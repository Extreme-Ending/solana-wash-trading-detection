"""Evaluate provisional anomaly scores without labels or outcome claims."""

from __future__ import annotations

import argparse
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from solana_risk.data.audit import repository_root
from solana_risk.features.build import MODEL_FEATURE_COLUMNS
from solana_risk.models.train_anomaly import (
    EXPERIMENT_STATUS,
    MODEL_NAMES,
    AnomalyConfig,
    AnomalyValidationError,
    build_models,
    chronological_partitions,
    feature_matrix,
    load_bundle,
    load_snapshots,
    score_model,
    sha256_file,
)


def default_report_dir() -> Path:
    return repository_root() / "reports" / "modelling"


def default_artifact_path() -> Path:
    return repository_root() / "artifacts" / "experimental" / "anomaly_models.joblib"


def _summary(values: np.ndarray) -> dict[str, float | int]:
    array = np.asarray(values, dtype=float)
    if not len(array):
        return {"count": 0}
    quantiles = np.quantile(array, [0.0, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99, 1.0])
    return {
        "count": int(len(array)),
        "mean": float(array.mean()),
        "std": float(array.std(ddof=0)),
        "min": float(quantiles[0]),
        "q25": float(quantiles[1]),
        "median": float(quantiles[2]),
        "q75": float(quantiles[3]),
        "q90": float(quantiles[4]),
        "q95": float(quantiles[5]),
        "q99": float(quantiles[6]),
        "max": float(quantiles[7]),
    }


def score_partition(bundle: Mapping[str, Any], frame: pd.DataFrame) -> pd.DataFrame:
    """Return metadata plus one consistently directed score per model."""

    scored = frame.loc[:, ["wallet", "as_of"]].reset_index(drop=True).copy()
    for name in MODEL_NAMES:
        scored[name] = score_model(name, bundle["models"][name], frame)
    return scored


def _rank_agreement(scored: pd.DataFrame) -> dict[str, float]:
    correlations = scored.loc[:, MODEL_NAMES].corr(method="spearman")
    result: dict[str, float] = {}
    for index, left in enumerate(MODEL_NAMES):
        for right in MODEL_NAMES[index + 1 :]:
            result[f"{left}__{right}"] = float(correlations.loc[left, right])
    return result


def _top_sets(scored: pd.DataFrame, budget: int) -> dict[str, set[int]]:
    capped = min(budget, len(scored))
    return {
        name: set(scored[name].nlargest(capped, keep="first").index.tolist())
        for name in MODEL_NAMES
    }


def _review_budget_agreement(scored: pd.DataFrame) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for budget in (10, 25, 50, 100):
        sets = _top_sets(scored, budget)
        pairwise: dict[str, float] = {}
        for index, left in enumerate(MODEL_NAMES):
            for right in MODEL_NAMES[index + 1 :]:
                union = sets[left] | sets[right]
                pairwise[f"{left}__{right}"] = (
                    float(len(sets[left] & sets[right]) / len(union)) if union else 1.0
                )
        all_three = set.intersection(*(sets[name] for name in MODEL_NAMES))
        result[str(budget)] = {
            "effective_budget": min(budget, len(scored)),
            "all_model_intersection_count": len(all_three),
            "pairwise_jaccard": pairwise,
            "interpretation": "Unverified review-candidate agreement only.",
        }
    return result


def _temporal_score_changes(
    earlier_scores: pd.DataFrame,
    later_scores: pd.DataFrame,
) -> dict[str, Any]:
    joined = earlier_scores.merge(later_scores, on="wallet", suffixes=("_earlier", "_later"))
    result: dict[str, Any] = {"repeated_wallet_count": len(joined)}
    for name in MODEL_NAMES:
        earlier = joined[f"{name}_earlier"].to_numpy()
        later = joined[f"{name}_later"].to_numpy()
        delta = later - earlier
        result[name] = {
            "delta": _summary(delta),
            "rank_correlation": float(pd.Series(earlier).corr(pd.Series(later), method="spearman")),
        }
    return result


def _cohort_summaries(frame: pd.DataFrame, scored: pd.DataFrame) -> dict[str, Any]:
    combined = frame.reset_index(drop=True).copy()
    for name in MODEL_NAMES:
        combined[name] = scored[name].to_numpy()
    groups = {
        "single_event_history": combined["single_event_history"].astype(bool),
        "insufficient_history_30d": combined["insufficient_history_30d"].astype(bool),
        "top_1pct_total_usd_volume": combined["total_usd_volume"].ge(
            combined["total_usd_volume"].quantile(0.99)
        ),
        "top_1pct_max_usd_volume": combined["max_usd_volume"].ge(
            combined["max_usd_volume"].quantile(0.99)
        ),
    }
    result: dict[str, Any] = {}
    for label, mask in groups.items():
        result[label] = {
            "selected_count": int(mask.sum()),
            "other_count": int((~mask).sum()),
            "selected_scores": {name: _summary(combined.loc[mask, name].to_numpy()) for name in MODEL_NAMES},
            "other_scores": {name: _summary(combined.loc[~mask, name].to_numpy()) for name in MODEL_NAMES},
        }
    return result


def _distribution_shift(train: pd.DataFrame, comparison: pd.DataFrame) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for column in MODEL_FEATURE_COLUMNS:
        train_values = train[column].astype(float)
        later_values = comparison[column].astype(float)
        train_median = float(train_values.median())
        later_median = float(later_values.median())
        q25, q75 = train_values.quantile([0.25, 0.75])
        iqr = float(q75 - q25)
        if iqr > 0:
            shift = abs(later_median - train_median) / iqr
        else:
            shift = 0.0 if math.isclose(later_median, train_median) else None
        result[column] = {
            "train_median": train_median,
            "comparison_median": later_median,
            "absolute_median_shift_in_train_iqr": shift,
            "train_missing_fraction": float(train_values.isna().mean()),
            "comparison_missing_fraction": float(later_values.isna().mean()),
        }
    return result


def _sensitivity(
    frame: pd.DataFrame,
    primary_scores: pd.DataFrame,
    base_config: AnomalyConfig,
) -> dict[str, Any]:
    """Fit alternatives on training only and compare ranks on validation only."""

    partitions, _ = chronological_partitions(frame)
    train = partitions["train"]
    validation = partitions["validation"]
    primary = primary_scores.set_index("wallet")
    variants: list[tuple[str, AnomalyConfig, str]] = []
    for estimators in (100, 500):
        variants.append(
            (
                f"isolation_n_estimators_{estimators}",
                replace(base_config, isolation_n_estimators=estimators),
                "isolation_forest",
            )
        )
    for max_samples in (128, 512):
        variants.append(
            (
                f"isolation_max_samples_{max_samples}",
                replace(base_config, isolation_max_samples=max_samples),
                "isolation_forest",
            )
        )
    for neighbors in (15, 70):
        variants.append(
            (
                f"lof_n_neighbors_{neighbors}",
                replace(base_config, lof_n_neighbors=neighbors),
                "local_outlier_factor",
            )
        )
    result: dict[str, Any] = {}
    for label, config, model_name in variants:
        model = build_models(config, len(train))[model_name]
        model.fit(feature_matrix(train))
        alternative = pd.Series(
            score_model(model_name, model, validation),
            index=validation["wallet"].astype(str),
        )
        reference = primary.loc[alternative.index, model_name]
        result[label] = {
            "model": model_name,
            "changed_parameter": {
                key: value
                for key, value in config.__dict__.items()
                if value != base_config.__dict__[key]
            },
            "validation_rank_correlation_with_primary": float(
                reference.corr(alternative, method="spearman")
            ),
            "evaluated_on_holdout": False,
        }
    return result


def evaluate_experiment(
    bundle: Mapping[str, Any],
    frame: pd.DataFrame,
    *,
    include_sensitivity: bool = True,
) -> tuple[dict[str, Any], dict[str, pd.DataFrame]]:
    """Evaluate stability, agreement, drift, and review-budget behavior."""

    partitions, split = chronological_partitions(frame)
    scores = {name: score_partition(bundle, partition) for name, partition in partitions.items()}
    config = AnomalyConfig(**bundle["metadata"]["config"])
    validation_sensitivity = (
        _sensitivity(frame, scores["validation"], config) if include_sensitivity else {}
    )
    score_distributions = {
        partition_name: {
            model_name: _summary(partition_scores[model_name].to_numpy())
            for model_name in MODEL_NAMES
        }
        for partition_name, partition_scores in scores.items()
    }
    report = {
        "experiment_status": EXPERIMENT_STATUS,
        "experiment_scope": "academic_research",
        "labels_used": False,
        "confirmed_outcomes_reported": False,
        "score_semantics": bundle["metadata"]["score_semantics"],
        "interpretation_boundary": bundle["metadata"]["outcome_semantics"],
        "temporal_split": split.__dict__,
        "score_distributions": score_distributions,
        "rank_agreement": {
            name: _rank_agreement(scores[name])
            for name in ("train", "validation", "holdout", "validation_new_wallets", "holdout_new_wallets")
        },
        "review_budget_sensitivity": {
            "validation": _review_budget_agreement(scores["validation"]),
            "holdout": _review_budget_agreement(scores["holdout"]),
            "holdout_new_wallets": _review_budget_agreement(scores["holdout_new_wallets"]),
        },
        "temporal_score_changes": {
            "train_to_validation": _temporal_score_changes(scores["train"], scores["validation"]),
            "train_to_holdout": _temporal_score_changes(scores["train"], scores["holdout"]),
        },
        "holdout_cohort_diagnostics": _cohort_summaries(partitions["holdout"], scores["holdout"]),
        "feature_shift": {
            "validation_vs_train": _distribution_shift(partitions["train"], partitions["validation"]),
            "holdout_vs_train": _distribution_shift(partitions["train"], partitions["holdout"]),
            "holdout_new_wallets_vs_train": _distribution_shift(
                partitions["train"], partitions["holdout_new_wallets"]
            ),
        },
        "validation_parameter_sensitivity": validation_sensitivity,
        "lof_score_contract": {
            "training_intrinsic_summary": _summary(
                np.asarray(
                    bundle["training_reference"]["local_outlier_factor_intrinsic_scores"],
                    dtype=float,
                )
            ),
            "novelty_scoring": (
                "Validation and holdout use novelty=True score_samples. Training intrinsic "
                "negative_outlier_factor_ is reported separately and is not treated as the same quantity."
            ),
        },
        "limitations": [
            "No verified outcome labels exist, so discrimination, recall, precision, calibration, and causal claims are unavailable.",
            "The full validation and holdout cutoffs repeat training wallets and are longitudinal diagnostics, not independent tests.",
            "Wallet-disjoint entrants are later acquisition cohorts with shorter observable histories and possible regime shift.",
            "Top-k lists are unverified review candidates selected by an arbitrary operational budget.",
            "Cumulative event histories make snapshot scores dependent across cutoffs.",
        ],
    }
    return report, scores


def _json_value(value: Any) -> Any:
    if value is None or value is pd.NA:
        return None
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [_json_value(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def render_summary(report: Mapping[str, Any]) -> str:
    split = report["temporal_split"]
    holdout_agreement = report["rank_agreement"]["holdout"]
    sensitivity = report["validation_parameter_sensitivity"]
    lines = [
        "# Provisional anomaly-modelling evaluation",
        "",
        f"> **{EXPERIMENT_STATUS}**",
        "",
        "These are label-free anomaly scores. They do not confirm wash trading, fraud, intent, or misconduct.",
        "",
        "## Temporal design",
        "",
        f"- Training cutoff: `{split['train_cutoff']}` ({split['train_rows']} wallets).",
        f"- Validation cutoff: `{split['validation_cutoff']}` ({split['validation_rows']} wallets; {split['validation_new_wallets']} new identities).",
        f"- Holdout cutoff: `{split['holdout_cutoff']}` ({split['holdout_rows']} wallets; {split['holdout_new_wallets']} new identities).",
        f"- Training wallets repeated in validation: {split['train_validation_wallet_overlap']}; repeated in holdout: {split['train_holdout_wallet_overlap']}.",
        "",
        "## Holdout rank agreement",
        "",
    ]
    for pair, value in holdout_agreement.items():
        lines.append(f"- `{pair}` Spearman correlation: {value:.3f}.")
    lines.extend(["", "## Validation-only sensitivity", ""])
    for label, evidence in sensitivity.items():
        lines.append(
            f"- `{label}` rank correlation with the primary configuration: "
            f"{evidence['validation_rank_correlation_with_primary']:.3f}; holdout not used."
        )
    lines.extend(
        [
            "",
            "## Interpretation limits",
            "",
            *[f"- {item}" for item in report["limitations"]],
        ]
    )
    return "\n".join(lines) + "\n"


def write_reports(
    report: Mapping[str, Any],
    report_dir: Path | str,
    *,
    artifact_path: Path | str,
    snapshot_path: Path | str,
) -> dict[str, Path]:
    destination = Path(report_dir).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    payload = dict(report)
    payload["fingerprints"] = {
        "artifact_sha256": sha256_file(artifact_path),
        "snapshot_sha256": sha256_file(snapshot_path),
    }
    json_path = destination / "anomaly_evaluation.json"
    markdown_path = destination / "anomaly_evaluation.md"
    json_path.write_text(
        json.dumps(_json_value(payload), indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_summary(payload), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=repository_root() / "data" / "features" / "wallet_snapshots.csv",
    )
    parser.add_argument("--artifact", type=Path, default=default_artifact_path())
    parser.add_argument("--report-dir", type=Path, default=default_report_dir())
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        frame = load_snapshots(args.input)
        bundle = load_bundle(args.artifact)
        expected_snapshot = bundle["metadata"].get("snapshot_sha256")
        observed_snapshot = sha256_file(args.input)
        if expected_snapshot and observed_snapshot != expected_snapshot:
            raise AnomalyValidationError(
                "Snapshot checksum differs from the data used to fit the artifact"
            )
        report, _ = evaluate_experiment(bundle, frame)
        paths = write_reports(
            report,
            args.report_dir,
            artifact_path=args.artifact,
            snapshot_path=args.input,
        )
    except AnomalyValidationError as exc:
        print(f"Phase 4B evaluation validation failed: {exc}")
        return 2
    print(EXPERIMENT_STATUS)
    print(f"JSON report: {paths['json']}")
    print(f"Markdown report: {paths['markdown']}")
    print("Interpretation: top-ranked wallets are unverified review candidates only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
