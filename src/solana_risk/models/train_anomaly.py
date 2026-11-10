"""Fit and serialize provisional label-free wallet anomaly scorers.

The experiment is not an approved replacement for the submitted methodology.
Its outputs are anomaly scores and unverified review candidates, not fraud or
wash-trading labels, decisions, or probabilities.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn
from pandas.api.types import is_numeric_dtype
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.neighbors import LocalOutlierFactor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler

from solana_risk.data.audit import repository_root
from solana_risk.features.build import (
    FEATURE_RULES_VERSION,
    FORBIDDEN_TARGET_COLUMNS,
    METADATA_COLUMNS,
    MODEL_FEATURE_COLUMNS,
    feature_registry_sha256,
)
from solana_risk.models.baselines import RobustMADDetector

EXPERIMENT_STATUS = "EXPERIMENTAL UNSUPERVISED ANOMALY MODELLING"
EXPERIMENT_VERSION = "4B.1"
MODEL_NAMES: tuple[str, ...] = ("isolation_forest", "local_outlier_factor", "robust_mad")


class AnomalyValidationError(ValueError):
    """Raised when an input would make the experiment invalid or irreproducible."""


@dataclass(frozen=True)
class AnomalyConfig:
    """Explicit configuration for deterministic provisional scoring."""

    random_seed: int = 42
    isolation_n_estimators: int = 300
    isolation_max_samples: int = 256
    isolation_contamination: str = "auto"
    isolation_max_features: float = 1.0
    lof_n_neighbors: int = 35
    lof_metric: str = "minkowski"
    lof_p: int = 2
    robust_clip: float = 25.0
    robust_constant_penalty: float = 10.0

    def validate(self, train_size: int) -> None:
        if self.isolation_n_estimators < 1:
            raise AnomalyValidationError("isolation_n_estimators must be positive")
        if self.isolation_max_samples < 2:
            raise AnomalyValidationError("isolation_max_samples must be at least 2")
        if not 0 < self.isolation_max_features <= 1:
            raise AnomalyValidationError("isolation_max_features must be in (0, 1]")
        if not 1 < self.lof_n_neighbors < train_size:
            raise AnomalyValidationError(
                f"lof_n_neighbors must be between 2 and train_size - 1 ({train_size - 1})"
            )
        if self.robust_clip <= 0 or self.robust_constant_penalty <= 0:
            raise AnomalyValidationError("robust baseline parameters must be positive")


@dataclass(frozen=True)
class TemporalSplit:
    """Chronological split with explicit identity-overlap diagnostics."""

    train_cutoff: str
    validation_cutoff: str
    holdout_cutoff: str
    train_rows: int
    validation_rows: int
    holdout_rows: int
    train_validation_wallet_overlap: int
    train_holdout_wallet_overlap: int
    validation_holdout_wallet_overlap: int
    validation_new_wallets: int
    holdout_new_wallets: int


def default_input_path() -> Path:
    return repository_root() / "data" / "features" / "wallet_snapshots.csv"


def default_artifact_dir() -> Path:
    return repository_root() / "artifacts" / "experimental"


def sha256_file(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _strict_target_like_columns(columns: Sequence[str]) -> list[str]:
    forbidden = {name.casefold() for name in FORBIDDEN_TARGET_COLUMNS}
    tokens = ("label", "target", "fraud", "wash", "outcome", "probability")
    return sorted(
        name
        for name in columns
        if name.casefold() in forbidden or any(token in name.casefold() for token in tokens)
    )


def validate_snapshot_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate and type a snapshot table without fitting or repairing values."""

    if not isinstance(frame, pd.DataFrame):
        raise AnomalyValidationError("Snapshots must be provided as a pandas DataFrame")
    if frame.empty:
        raise AnomalyValidationError("Snapshot input contains no rows")
    if frame.columns.duplicated().any():
        raise AnomalyValidationError("Snapshot input contains duplicate column names")
    target_like = _strict_target_like_columns(frame.columns.tolist())
    if target_like:
        raise AnomalyValidationError(
            "Target-like columns are unsupported in the label-free experiment: "
            + ", ".join(target_like)
        )
    expected = (*METADATA_COLUMNS, *MODEL_FEATURE_COLUMNS)
    missing = sorted(set(expected).difference(frame.columns))
    unexpected = sorted(set(frame.columns).difference(expected))
    if missing or unexpected:
        details: list[str] = []
        if missing:
            details.append(f"missing columns: {missing}")
        if unexpected:
            details.append(f"unexpected columns: {unexpected}")
        raise AnomalyValidationError("Snapshot schema mismatch; " + "; ".join(details))
    typed = frame.loc[:, expected].copy()
    if typed["wallet"].isna().any() or typed["wallet"].astype("string").str.strip().eq("").any():
        raise AnomalyValidationError("wallet metadata contains missing or empty values")
    typed["wallet"] = typed["wallet"].astype("string")
    typed["as_of"] = pd.to_datetime(typed["as_of"], errors="coerce", utc=True)
    if typed["as_of"].isna().any():
        raise AnomalyValidationError("as_of contains invalid or timezone-free values")
    if typed[["wallet", "as_of"]].duplicated().any():
        raise AnomalyValidationError("wallet and as_of must be unique together")
    for column in MODEL_FEATURE_COLUMNS:
        if not is_numeric_dtype(typed[column].dtype):
            try:
                typed[column] = pd.to_numeric(typed[column], errors="raise")
            except (TypeError, ValueError) as exc:
                raise AnomalyValidationError(f"Feature {column!r} must be numeric") from exc
    values = typed.loc[:, MODEL_FEATURE_COLUMNS].to_numpy(dtype=float)
    if np.isinf(values).any():
        raise AnomalyValidationError("Snapshot features contain infinite values")
    cutoffs = sorted(typed["as_of"].unique())
    if len(cutoffs) != 3:
        raise AnomalyValidationError(
            f"Phase 4B requires exactly three chronological cutoffs; observed {len(cutoffs)}"
        )
    return typed.sort_values(["as_of", "wallet"], kind="stable", ignore_index=True)


def load_snapshots(path: Path | str) -> pd.DataFrame:
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise AnomalyValidationError(
            f"Snapshot input is missing: {source}. Run Phase 3 feature generation first."
        )
    try:
        frame = pd.read_csv(source, low_memory=False)
    except (OSError, UnicodeDecodeError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        raise AnomalyValidationError(f"Could not load snapshot input {source}: {exc}") from exc
    return validate_snapshot_frame(frame)


def chronological_partitions(frame: pd.DataFrame) -> tuple[dict[str, pd.DataFrame], TemporalSplit]:
    """Create chronological partitions and quantify repeated-wallet overlap."""

    validated = validate_snapshot_frame(frame)
    cutoffs = sorted(validated["as_of"].unique())
    train = validated.loc[validated["as_of"].eq(cutoffs[0])].copy()
    validation = validated.loc[validated["as_of"].eq(cutoffs[1])].copy()
    holdout = validated.loc[validated["as_of"].eq(cutoffs[2])].copy()
    train_wallets = set(train["wallet"])
    validation_wallets = set(validation["wallet"])
    holdout_wallets = set(holdout["wallet"])
    validation_new = validation.loc[~validation["wallet"].isin(train_wallets)].copy()
    holdout_new = holdout.loc[~holdout["wallet"].isin(validation_wallets)].copy()
    split = TemporalSplit(
        train_cutoff=pd.Timestamp(cutoffs[0]).isoformat(),
        validation_cutoff=pd.Timestamp(cutoffs[1]).isoformat(),
        holdout_cutoff=pd.Timestamp(cutoffs[2]).isoformat(),
        train_rows=len(train),
        validation_rows=len(validation),
        holdout_rows=len(holdout),
        train_validation_wallet_overlap=len(train_wallets & validation_wallets),
        train_holdout_wallet_overlap=len(train_wallets & holdout_wallets),
        validation_holdout_wallet_overlap=len(validation_wallets & holdout_wallets),
        validation_new_wallets=len(validation_new),
        holdout_new_wallets=len(holdout_new),
    )
    return {
        "train": train,
        "validation": validation,
        "holdout": holdout,
        "validation_new_wallets": validation_new,
        "holdout_new_wallets": holdout_new,
    }, split


def feature_matrix(frame: pd.DataFrame) -> pd.DataFrame:
    """Return only registered features in their immutable registry order."""

    return frame.loc[:, MODEL_FEATURE_COLUMNS].astype(float)


def audit_feature_matrix(frame: pd.DataFrame) -> dict[str, Any]:
    """Return structural audit evidence without altering the snapshot data."""

    validated = validate_snapshot_frame(frame)
    partitions, split = chronological_partitions(validated)
    train_x = feature_matrix(partitions["train"])
    all_missing = train_x.columns[train_x.isna().all()].tolist()
    constant = train_x.columns[train_x.nunique(dropna=False).le(1)].tolist()
    correlations = train_x.corr(method="spearman", min_periods=10).abs()
    high_pairs: list[dict[str, Any]] = []
    for left_index, left in enumerate(MODEL_FEATURE_COLUMNS):
        for right in MODEL_FEATURE_COLUMNS[left_index + 1 :]:
            value = correlations.loc[left, right]
            if pd.notna(value) and value >= 0.95:
                high_pairs.append({"left": left, "right": right, "absolute_spearman": float(value)})
    return {
        "row_count": len(validated),
        "feature_count": len(MODEL_FEATURE_COLUMNS),
        "cutoff_counts": {
            pd.Timestamp(key).isoformat(): int(value)
            for key, value in validated["as_of"].value_counts().sort_index().items()
        },
        "missing_counts": {
            column: int(value)
            for column, value in validated.loc[:, MODEL_FEATURE_COLUMNS].isna().sum().items()
            if value
        },
        "nonfinite_infinite_count": int(
            np.isinf(validated.loc[:, MODEL_FEATURE_COLUMNS].to_numpy(dtype=float)).sum()
        ),
        "train_all_missing_features": all_missing,
        "train_constant_features": constant,
        "train_high_correlation_pairs": high_pairs,
        "single_event_snapshot_count": int(validated["single_event_history"].sum()),
        "insufficient_history_30d_count": int(validated["insufficient_history_30d"].sum()),
        "temporal_split": asdict(split),
    }


def build_models(config: AnomalyConfig, train_size: int) -> dict[str, Pipeline]:
    config.validate(train_size)
    median_imputer = lambda: SimpleImputer(strategy="median", keep_empty_features=True)
    return {
        "isolation_forest": Pipeline(
            [
                ("imputer", median_imputer()),
                (
                    "model",
                    IsolationForest(
                        n_estimators=config.isolation_n_estimators,
                        max_samples=min(config.isolation_max_samples, train_size),
                        contamination=config.isolation_contamination,
                        max_features=config.isolation_max_features,
                        bootstrap=False,
                        n_jobs=1,
                        random_state=config.random_seed,
                    ),
                ),
            ]
        ),
        "local_outlier_factor": Pipeline(
            [
                ("imputer", median_imputer()),
                ("scale", RobustScaler()),
                (
                    "model",
                    LocalOutlierFactor(
                        n_neighbors=config.lof_n_neighbors,
                        contamination="auto",
                        novelty=True,
                        metric=config.lof_metric,
                        p=config.lof_p,
                        n_jobs=1,
                    ),
                ),
            ]
        ),
        "robust_mad": Pipeline(
            [
                ("imputer", median_imputer()),
                (
                    "model",
                    RobustMADDetector(
                        clip=config.robust_clip,
                        constant_penalty=config.robust_constant_penalty,
                    ),
                ),
            ]
        ),
    }


def score_model(model_name: str, model: Pipeline, frame: pd.DataFrame) -> np.ndarray:
    """Return scores in the shared direction: larger means more unusual."""

    matrix = feature_matrix(frame)
    if model_name in {"isolation_forest", "local_outlier_factor"}:
        scores = -model.score_samples(matrix)
    elif model_name == "robust_mad":
        scores = model.score_samples(matrix)
    else:
        raise AnomalyValidationError(f"Unsupported model name: {model_name}")
    scores = np.asarray(scores, dtype=float)
    if scores.shape != (len(frame),) or not np.isfinite(scores).all():
        raise AnomalyValidationError(f"{model_name} produced invalid anomaly scores")
    return scores


def fit_experiment(
    frame: pd.DataFrame,
    *,
    config: AnomalyConfig | None = None,
    snapshot_sha256: str | None = None,
) -> dict[str, Any]:
    """Fit all scorers on the earliest cutoff only and return a serializable bundle."""

    validated = validate_snapshot_frame(frame)
    partitions, split = chronological_partitions(validated)
    train = partitions["train"]
    audit = audit_feature_matrix(validated)
    if audit["train_all_missing_features"]:
        raise AnomalyValidationError(
            "Training features cannot be entirely missing: "
            + ", ".join(audit["train_all_missing_features"])
        )
    selected = config or AnomalyConfig()
    models = build_models(selected, len(train))
    train_x = feature_matrix(train)
    for model in models.values():
        model.fit(train_x)
    intrinsic_lof = -models["local_outlier_factor"].named_steps["model"].negative_outlier_factor_
    metadata = {
        "experiment_status": EXPERIMENT_STATUS,
        "experiment_version": EXPERIMENT_VERSION,
        "experiment_scope": "academic_research",
        "labels_used": False,
        "score_semantics": "Higher means more unusual relative to the earliest-cutoff training reference.",
        "outcome_semantics": "Scores do not establish wash trading, fraud, intent, or misconduct.",
        "is_probability": False,
        "feature_rules_version": FEATURE_RULES_VERSION,
        "feature_registry_sha256": feature_registry_sha256(),
        "feature_order": list(MODEL_FEATURE_COLUMNS),
        "metadata_columns_excluded": list(METADATA_COLUMNS),
        "snapshot_sha256": snapshot_sha256,
        "temporal_split": asdict(split),
        "config": asdict(selected),
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
        },
        "preprocessing": {
            "fitted_on": "earliest cutoff only",
            "missing_values": "training median imputation inside each fitted pipeline",
            "local_outlier_factor_scaling": "training-fitted RobustScaler",
            "isolation_forest_scaling": "none; tree partitioning is applied after median imputation",
            "robust_baseline_scaling": "training median/MAD inside RobustMADDetector",
        },
        "lof_score_note": (
            "training_intrinsic_scores use fitted negative_outlier_factor_; score_model uses "
            "novelty-mode score_samples for any supplied rows. These are not interchangeable."
        ),
    }
    return {
        "metadata": metadata,
        "models": models,
        "training_reference": {
            "wallet_count": len(train),
            "local_outlier_factor_intrinsic_scores": intrinsic_lof,
        },
        "input_audit": audit,
    }


def save_bundle(bundle: Mapping[str, Any], output_dir: Path | str) -> dict[str, Path]:
    destination = Path(output_dir).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    artifact_path = destination / "anomaly_models.joblib"
    joblib.dump(dict(bundle), artifact_path, compress=3)
    artifact_sha256 = sha256_file(artifact_path)
    manifest = {
        "experiment_status": EXPERIMENT_STATUS,
        "artifact": artifact_path.name,
        "artifact_sha256": artifact_sha256,
        "snapshot_sha256": bundle["metadata"]["snapshot_sha256"],
        "feature_registry_sha256": bundle["metadata"]["feature_registry_sha256"],
        "feature_order": bundle["metadata"]["feature_order"],
        "config": bundle["metadata"]["config"],
        "versions": bundle["metadata"]["versions"],
    }
    manifest_path = destination / "anomaly_models_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return {"artifact": artifact_path, "manifest": manifest_path}


def load_bundle(path: Path | str) -> dict[str, Any]:
    artifact = Path(path).expanduser().resolve()
    if not artifact.is_file():
        raise AnomalyValidationError(f"Model artifact is missing: {artifact}")
    try:
        bundle = joblib.load(artifact)
    except Exception as exc:  # joblib can wrap several pickle/IO failures
        raise AnomalyValidationError(f"Could not load model artifact {artifact}: {exc}") from exc
    if not isinstance(bundle, dict) or set(bundle.get("models", {})) != set(MODEL_NAMES):
        raise AnomalyValidationError("Model artifact does not match the Phase 4B bundle contract")
    metadata = bundle.get("metadata", {})
    if metadata.get("feature_order") != list(MODEL_FEATURE_COLUMNS):
        raise AnomalyValidationError("Model artifact feature order does not match the registry")
    if metadata.get("feature_registry_sha256") != feature_registry_sha256():
        raise AnomalyValidationError("Model artifact feature registry fingerprint is stale")
    return bundle


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=default_input_path())
    parser.add_argument("--artifact-dir", type=Path, default=default_artifact_dir())
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        snapshots = load_snapshots(args.input)
        bundle = fit_experiment(
            snapshots,
            snapshot_sha256=sha256_file(args.input),
        )
        paths = save_bundle(bundle, args.artifact_dir)
    except AnomalyValidationError as exc:
        print(f"Phase 4B training validation failed: {exc}")
        return 2
    print(EXPERIMENT_STATUS)
    print(f"Artifact: {paths['artifact']}")
    print(f"Manifest: {paths['manifest']}")
    print("Interpretation: anomaly scores only; no labels or confirmed outcomes were produced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
