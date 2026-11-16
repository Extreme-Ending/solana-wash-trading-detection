"""Generate dissertation-ready figures from verified label-free experiment reports.

The script consumes reports produced by the importable pipeline. It does not fit a
model, assign labels, or infer fraud outcomes. Validation is intentionally strict so
that stale or incompatible inputs fail instead of producing persuasive-looking plots.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


EXPERIMENT_STATUS = "EXPERIMENTAL UNSUPERVISED ANOMALY MODELLING"
MODEL_LABELS = {
    "isolation_forest": "Isolation Forest",
    "local_outlier_factor": "Local Outlier Factor",
    "robust_mad": "Robust median/MAD",
}
COLORS = {"forest": "#164b3b", "gold": "#c38b2a", "blue": "#39708f", "cream": "#f4efe3"}


class EvidenceValidationError(ValueError):
    """Raised when report inputs cannot support the requested figures."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceValidationError(f"Could not read valid JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise EvidenceValidationError(f"Expected a JSON object in {path}.")
    return value


def _require(mapping: Mapping[str, Any], key: str, context: str) -> Any:
    if key not in mapping:
        raise EvidenceValidationError(f"Missing {context}.{key}.")
    return mapping[key]


def validate_evidence(
    evaluation: Mapping[str, Any],
    cleaning: Mapping[str, Any],
    features: Mapping[str, Any],
    model_manifest: Mapping[str, Any],
) -> None:
    if evaluation.get("experiment_status") != EXPERIMENT_STATUS:
        raise EvidenceValidationError("Evaluation is not the registered experimental unsupervised study.")
    if evaluation.get("labels_used") is not False:
        raise EvidenceValidationError("Phase 9 figures require an explicit labels_used=false contract.")
    if evaluation.get("confirmed_outcomes_reported") is not False:
        raise EvidenceValidationError("Confirmed outcomes must be explicitly disabled.")

    reconciliation = _require(cleaning, "row_reconciliation", "cleaning")
    if not isinstance(reconciliation, Mapping) or reconciliation.get("reconciles") is not True:
        raise EvidenceValidationError("Cleaning rows do not reconcile.")
    if reconciliation.get("input") != reconciliation.get("retained", 0) + reconciliation.get(
        "quarantined", 0
    ) + reconciliation.get("removed", 0):
        raise EvidenceValidationError("Cleaning row arithmetic is inconsistent.")

    feature_summary = _require(features, "features", "features")
    feature_output = _require(features, "output", "features")
    if not isinstance(feature_summary, Mapping) or feature_summary.get("count") != 29:
        raise EvidenceValidationError("Expected the registered 29-feature contract.")

    fingerprints = _require(evaluation, "fingerprints", "evaluation")
    if not isinstance(fingerprints, Mapping):
        raise EvidenceValidationError("Evaluation fingerprints must be an object.")
    if fingerprints.get("artifact_sha256") != model_manifest.get("artifact_sha256"):
        raise EvidenceValidationError("Evaluation and model artifact fingerprints differ.")
    snapshot_sha = feature_output.get("sha256") if isinstance(feature_output, Mapping) else None
    if fingerprints.get("snapshot_sha256") != snapshot_sha:
        raise EvidenceValidationError("Evaluation and feature snapshot fingerprints differ.")
    if model_manifest.get("snapshot_sha256") != snapshot_sha:
        raise EvidenceValidationError("Model and feature snapshot fingerprints differ.")
    if model_manifest.get("experiment_status") != EXPERIMENT_STATUS:
        raise EvidenceValidationError("Model manifest status is incompatible.")


def _style() -> None:
    plt.rcParams.update(
        {
            "axes.edgecolor": "#2a3c35",
            "axes.labelcolor": "#23352f",
            "axes.titleweight": "bold",
            "figure.facecolor": "white",
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "savefig.facecolor": "white",
            "svg.hashsalt": "solana-phase9-evidence",
            "text.color": "#23352f",
            "xtick.color": "#42554e",
            "ytick.color": "#42554e",
        }
    )


def _save(figure: plt.Figure, path: Path) -> None:
    figure.savefig(
        path,
        format="svg",
        bbox_inches="tight",
        metadata={"Date": None, "Creator": "Phase 9 deterministic evidence generator"},
    )
    plt.close(figure)
    # Matplotlib writes path-command lines with terminal spaces. Normalize them so
    # repository whitespace checks pass and equivalent renders remain byte-stable.
    normalized = "\n".join(line.rstrip() for line in path.read_text(encoding="utf-8").splitlines())
    path.write_text(normalized + "\n", encoding="utf-8")


def _write_csv(path: Path, header: Sequence[str], rows: Sequence[Sequence[Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def _temporal_figure(evaluation: Mapping[str, Any], output: Path) -> None:
    split = evaluation["temporal_split"]
    labels = ["Training\n1 Sep", "Validation\n1 Oct", "Holdout\n1 Dec"]
    repeated = [split["train_rows"], split["train_validation_wallet_overlap"], split["train_holdout_wallet_overlap"]]
    new = [0, split["validation_new_wallets"], split["holdout_new_wallets"]]
    figure, axis = plt.subplots(figsize=(7.4, 4.6))
    positions = np.arange(3)
    axis.bar(positions, repeated, color=COLORS["forest"], label="Training-wallet cohort")
    axis.bar(positions, new, bottom=repeated, color=COLORS["gold"], label="New relative to training")
    for index, total in enumerate(np.add(repeated, new)):
        axis.text(index, total + 35, f"{int(total):,}", ha="center", fontweight="bold")
    axis.set_xticks(positions, labels)
    axis.set_ylabel("Wallet snapshots")
    axis.set_ylim(0, max(np.add(repeated, new)) * 1.14)
    axis.set_title("Chronological wallet cohorts are longitudinal")
    axis.legend(frameon=False, loc="upper left")
    axis.spines[["top", "right"]].set_visible(False)
    _save(figure, output)


def _score_summary_figure(evaluation: Mapping[str, Any], output: Path) -> None:
    distributions = evaluation["score_distributions"]
    keys = ["train", "validation", "holdout", "validation_new_wallets", "holdout_new_wallets"]
    labels = ["Train", "Validation", "Holdout", "Validation\nnew", "Holdout\nnew"]
    summaries = [distributions[key]["isolation_forest"] for key in keys]
    medians = np.array([item["median"] for item in summaries], dtype=float)
    lower = medians - np.array([item["q25"] for item in summaries], dtype=float)
    upper = np.array([item["q75"] for item in summaries], dtype=float) - medians
    figure, axis = plt.subplots(figsize=(7.8, 4.6))
    positions = np.arange(len(keys))
    axis.errorbar(
        positions,
        medians,
        yerr=np.vstack([lower, upper]),
        fmt="o",
        color=COLORS["forest"],
        ecolor=COLORS["blue"],
        capsize=7,
        linewidth=2,
    )
    for index, median in enumerate(medians):
        axis.text(index, median + 0.012, f"{median:.3f}", ha="center", fontsize=9)
    axis.set_xticks(positions, labels)
    axis.set_ylabel("Unitless Isolation Forest score")
    axis.set_title("Median and interquartile score summaries")
    axis.text(
        0.01,
        -0.25,
        "Descriptive distributions only; scores are not probabilities and cohorts differ in observed history.",
        transform=axis.transAxes,
        fontsize=8.5,
    )
    axis.spines[["top", "right"]].set_visible(False)
    _save(figure, output)


def _agreement_figure(evaluation: Mapping[str, Any], output: Path) -> None:
    order = list(MODEL_LABELS)
    matrix = np.eye(len(order))
    agreement = evaluation["rank_agreement"]["holdout"]
    for left_index, left in enumerate(order):
        for right_index, right in enumerate(order[left_index + 1 :], start=left_index + 1):
            value = agreement[f"{left}__{right}"]
            matrix[left_index, right_index] = matrix[right_index, left_index] = value
    figure, axis = plt.subplots(figsize=(7.2, 5.4))
    image = axis.imshow(matrix, cmap="RdYlGn", vmin=-1, vmax=1)
    short = ["Isolation Forest", "LOF", "Robust MAD"]
    axis.set_xticks(range(3), short, rotation=18, ha="right")
    axis.set_yticks(range(3), short)
    for row in range(3):
        for column in range(3):
            axis.text(column, row, f"{matrix[row, column]:.3f}", ha="center", va="center", fontweight="bold")
    axis.set_title("Holdout rank agreement (Spearman rho)")
    figure.colorbar(image, ax=axis, label="Rank correlation", shrink=0.78)
    _save(figure, output)


def _sensitivity_figure(evaluation: Mapping[str, Any], output: Path) -> None:
    sensitivity = evaluation["validation_parameter_sensitivity"]
    ordered = [
        "isolation_n_estimators_100",
        "isolation_n_estimators_500",
        "isolation_max_samples_128",
        "isolation_max_samples_512",
        "lof_n_neighbors_15",
        "lof_n_neighbors_70",
    ]
    labels = ["IF trees=100", "IF trees=500", "IF samples=128", "IF samples=512", "LOF neighbours=15", "LOF neighbours=70"]
    values = [sensitivity[key]["validation_rank_correlation_with_primary"] for key in ordered]
    figure, axis = plt.subplots(figsize=(8.0, 4.8))
    positions = np.arange(len(ordered))
    axis.barh(positions, values, color=[COLORS["forest"]] * 4 + [COLORS["gold"]] * 2)
    axis.set_yticks(positions, labels)
    axis.invert_yaxis()
    axis.set_xlim(0, 1.05)
    axis.set_xlabel("Validation rank correlation with registered configuration")
    axis.set_title("One-at-a-time parameter sensitivity")
    for index, value in enumerate(values):
        axis.text(value + 0.012, index, f"{value:.3f}", va="center")
    axis.text(0, -0.22, "Holdout was not used for this sensitivity study.", transform=axis.transAxes, fontsize=8.5)
    axis.spines[["top", "right"]].set_visible(False)
    _save(figure, output)


def _coverage_figure(evaluation: Mapping[str, Any], output: Path) -> None:
    cohorts = evaluation["holdout_cohort_diagnostics"]
    keys = [
        "single_event_history",
        "insufficient_history_30d",
        "top_1pct_total_usd_volume",
        "top_1pct_max_usd_volume",
    ]
    labels = ["Single-event\nhistory", "<30 days\nhistory", "Top 1% total\nUSD volume", "Top 1% max\nUSD volume"]
    selected = [cohorts[key]["selected_scores"]["isolation_forest"]["median"] for key in keys]
    other = [cohorts[key]["other_scores"]["isolation_forest"]["median"] for key in keys]
    positions = np.arange(len(keys))
    width = 0.36
    figure, axis = plt.subplots(figsize=(8.4, 4.8))
    axis.bar(positions - width / 2, selected, width, label="Selected stratum", color=COLORS["gold"])
    axis.bar(positions + width / 2, other, width, label="Other wallets", color=COLORS["forest"])
    axis.set_xticks(positions, labels)
    axis.set_ylabel("Median unitless Isolation Forest score")
    axis.set_title("Holdout score context varies by coverage and volume strata")
    axis.legend(frameon=False)
    axis.text(
        0,
        -0.25,
        "Associations are descriptive; they are not causal feature attribution or fraud evidence.",
        transform=axis.transAxes,
        fontsize=8.5,
    )
    axis.spines[["top", "right"]].set_visible(False)
    _save(figure, output)


def generate_package(
    *,
    evaluation_path: Path,
    cleaning_path: Path,
    features_path: Path,
    model_manifest_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    inputs = {
        "evaluation": evaluation_path,
        "cleaning": cleaning_path,
        "features": features_path,
        "model_manifest": model_manifest_path,
    }
    evidence = {name: load_json(path) for name, path in inputs.items()}
    validate_evidence(
        evidence["evaluation"], evidence["cleaning"], evidence["features"], evidence["model_manifest"]
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    _style()

    figures = {
        "figure_01_temporal_cohorts.svg": _temporal_figure,
        "figure_02_isolation_score_summaries.svg": _score_summary_figure,
        "figure_03_holdout_rank_agreement.svg": _agreement_figure,
        "figure_04_parameter_sensitivity.svg": _sensitivity_figure,
        "figure_05_coverage_score_context.svg": _coverage_figure,
    }
    for filename, plotter in figures.items():
        plotter(evidence["evaluation"], output_dir / filename)

    reconciliation = evidence["cleaning"]["row_reconciliation"]
    feature_output = evidence["features"]["output"]
    _write_csv(
        output_dir / "table_01_pipeline_summary.csv",
        ["stage", "records", "notes"],
        [
            ["source events", reconciliation["input"], "Supplied DEX/swap event rows"],
            ["retained events", reconciliation["retained"], "Validated events used for feature construction"],
            ["quarantined events", reconciliation["quarantined"], "Invalid essential evidence retained separately"],
            ["removed events", reconciliation["removed"], "No silently removed rows"],
            ["wallet snapshots", feature_output["row_count"], "Three point-in-time cutoffs"],
            ["registered features", evidence["features"]["features"]["count"], "Per wallet and scoring timestamp"],
        ],
    )
    split = evidence["evaluation"]["temporal_split"]
    _write_csv(
        output_dir / "table_02_temporal_evaluation.csv",
        ["role", "cutoff", "wallets", "training_wallet_overlap", "new_relative_to_training"],
        [
            ["training", split["train_cutoff"], split["train_rows"], split["train_rows"], 0],
            ["validation", split["validation_cutoff"], split["validation_rows"], split["train_validation_wallet_overlap"], split["validation_new_wallets"]],
            ["holdout", split["holdout_cutoff"], split["holdout_rows"], split["train_holdout_wallet_overlap"], split["holdout_new_wallets"]],
        ],
    )
    config = evidence["model_manifest"]["config"]
    agreement = evidence["evaluation"]["rank_agreement"]["holdout"]
    _write_csv(
        output_dir / "table_03_detector_evidence.csv",
        ["evidence", "value", "interpretation"],
        [
            ["Isolation Forest trees", config["isolation_n_estimators"], "Registered primary configuration"],
            ["Isolation Forest max samples", config["isolation_max_samples"], "Registered primary configuration"],
            ["Random seed", config["random_seed"], "Deterministic local experiment"],
            ["IF vs LOF holdout Spearman", agreement["isolation_forest__local_outlier_factor"], "Algorithm-dependent ranking"],
            ["IF vs robust MAD holdout Spearman", agreement["isolation_forest__robust_mad"], "Comparator agreement, not correctness"],
            ["LOF vs robust MAD holdout Spearman", agreement["local_outlier_factor__robust_mad"], "Algorithm-dependent ranking"],
            ["Verified labels used", False, "No fraud-effectiveness metric is available"],
        ],
    )

    output_paths = sorted(path for path in output_dir.iterdir() if path.name != "figure_manifest.json")
    manifest = {
        "contract": "phase9_label_free_research_evidence_v1",
        "experiment_status": EXPERIMENT_STATUS,
        "labels_used": False,
        "confirmed_outcomes_reported": False,
        "interpretation": "Figures describe anomaly-score stability, agreement, cohorts and coverage; not fraud effectiveness.",
        "inputs": {
            name: {"path": str(path), "sha256": sha256_file(path)} for name, path in inputs.items()
        },
        "outputs": {path.name: sha256_file(path) for path in output_paths},
    }
    (output_dir / "figure_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluation", type=Path, default=Path("reports/modelling/anomaly_evaluation.json"))
    parser.add_argument("--cleaning", type=Path, default=Path("reports/preprocessing/cleaning_report.json"))
    parser.add_argument("--features", type=Path, default=Path("reports/features/feature_report.json"))
    parser.add_argument(
        "--model-manifest",
        type=Path,
        default=Path("artifacts/experimental/anomaly_models_manifest.json"),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("reports/phase9"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = generate_package(
        evaluation_path=args.evaluation,
        cleaning_path=args.cleaning,
        features_path=args.features,
        model_manifest_path=args.model_manifest,
        output_dir=args.output_dir,
    )
    print(f"Phase 9 evidence package: {args.output_dir}")
    print(f"Generated outputs: {len(manifest['outputs'])}")
    print("Interpretation: label-free anomaly evidence only; no fraud-effectiveness claim.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
