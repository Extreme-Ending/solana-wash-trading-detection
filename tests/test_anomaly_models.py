"""Contract, leakage, persistence, and reproducibility tests for Phase 4B."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest

from solana_risk.features.build import MODEL_FEATURE_COLUMNS, feature_registry_sha256
from solana_risk.models.baselines import RobustMADDetector
from solana_risk.models.evaluate_anomaly import evaluate_experiment, score_partition
from solana_risk.models.train_anomaly import (
    EXPERIMENT_STATUS,
    MODEL_NAMES,
    AnomalyConfig,
    AnomalyValidationError,
    audit_feature_matrix,
    chronological_partitions,
    feature_matrix,
    fit_experiment,
    load_bundle,
    load_snapshots,
    save_bundle,
    score_model,
    validate_snapshot_frame,
)


def _snapshots(*, rows_per_cutoff: int = 90) -> pd.DataFrame:
    rng = np.random.default_rng(19)
    cutoffs = [
        "2025-09-01T00:00:00.000000Z",
        "2025-10-01T00:00:00.000000Z",
        "2025-12-01T00:00:00.000000Z",
    ]
    rows: list[dict[str, object]] = []
    for cutoff_index, cutoff in enumerate(cutoffs):
        existing = rows_per_cutoff
        start = 0 if cutoff_index == 0 else cutoff_index * 5
        for wallet_index in range(start, start + existing):
            event_count = int(rng.integers(1, 40))
            row: dict[str, object] = {
                "wallet": f"wallet-{wallet_index:04d}",
                "as_of": cutoff,
                "historical_event_count": event_count + cutoff_index,
                "unique_transaction_count": max(1, event_count - 1),
                "active_day_count": max(1, min(event_count, 20)),
                "events_per_active_day": event_count / max(1, min(event_count, 20)),
                "observed_activity_duration_days": float(rng.uniform(0, 150)),
                "total_usd_volume": float(rng.lognormal(8, 1.5)),
                "mean_usd_volume": float(rng.lognormal(5, 1.0)),
                "median_usd_volume": float(rng.lognormal(4.8, 0.9)),
                "max_usd_volume": float(rng.lognormal(6.5, 1.2)),
                "std_usd_volume": float(rng.lognormal(4, 1.0)) if event_count > 1 else 0.0,
                "time_since_last_event_hours": float(rng.uniform(1, 1000)),
                "inter_event_mean_seconds": float(rng.uniform(60, 90000)) if event_count > 1 else np.nan,
                "inter_event_median_seconds": float(rng.uniform(60, 70000)) if event_count > 1 else np.nan,
                "inter_event_std_seconds": float(rng.uniform(0, 50000)) if event_count > 1 else np.nan,
                "events_last_24h": int(rng.integers(0, 5)),
                "events_last_7d": int(rng.integers(0, 15)),
                "events_last_30d": int(rng.integers(0, 30)),
                "unique_token_count": int(rng.integers(2, 15)),
                "unique_token_pair_count": int(rng.integers(1, 12)),
                "unique_dex_count": int(rng.integers(1, 7)),
                "token_concentration": float(rng.uniform(0.1, 1)),
                "dex_concentration": float(rng.uniform(0.2, 1)),
                "missing_fee_proportion": float(rng.uniform(0, 1)),
                "multi_instruction_transaction_count": int(rng.integers(0, 5)),
                "single_event_history": event_count == 1,
                "insufficient_history_7d": bool(rng.integers(0, 2)),
                "insufficient_history_30d": bool(rng.integers(0, 2)),
                "observable_history_days": float(rng.uniform(1, 250)),
                "history_coverage_30d_fraction": float(rng.uniform(0.03, 1)),
            }
            rows.append(row)
    return pd.DataFrame(rows, columns=["wallet", "as_of", *MODEL_FEATURE_COLUMNS])


def test_snapshot_schema_and_registry_order_are_enforced() -> None:
    frame = _snapshots()
    validated = validate_snapshot_frame(frame)
    assert list(feature_matrix(validated).columns) == list(MODEL_FEATURE_COLUMNS)
    with pytest.raises(AnomalyValidationError, match="missing columns"):
        validate_snapshot_frame(frame.drop(columns=[MODEL_FEATURE_COLUMNS[0]]))
    with pytest.raises(AnomalyValidationError, match="unexpected columns"):
        validate_snapshot_frame(frame.assign(extra=1))


@pytest.mark.parametrize("column", ["target", "is_fraud", "wash_probability", "outcome_flag"])
def test_target_or_outcome_columns_are_rejected(column: str) -> None:
    with pytest.raises(AnomalyValidationError, match="Target-like"):
        validate_snapshot_frame(_snapshots().assign(**{column: 0}))


def test_missing_invalid_and_nonfinite_inputs_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(AnomalyValidationError, match="missing"):
        load_snapshots(tmp_path / "absent.csv")
    invalid = _snapshots()
    invalid.loc[0, "total_usd_volume"] = np.inf
    with pytest.raises(AnomalyValidationError, match="infinite"):
        validate_snapshot_frame(invalid)
    invalid = _snapshots()
    invalid["mean_usd_volume"] = invalid["mean_usd_volume"].astype(object)
    invalid.loc[0, "mean_usd_volume"] = "not-numeric"
    with pytest.raises(AnomalyValidationError, match="numeric"):
        validate_snapshot_frame(invalid)


def test_all_missing_train_feature_is_rejected_but_expected_missing_values_are_imputed() -> None:
    frame = _snapshots()
    first = sorted(frame["as_of"].unique())[0]
    frame.loc[frame["as_of"].eq(first), "inter_event_mean_seconds"] = np.nan
    with pytest.raises(AnomalyValidationError, match="entirely missing"):
        fit_experiment(frame)
    ordinary = fit_experiment(_snapshots())
    assert np.isfinite(
        score_model("isolation_forest", ordinary["models"]["isolation_forest"], _snapshots())
    ).all()


def test_constant_features_are_safe_for_robust_baseline() -> None:
    detector = RobustMADDetector().fit(np.ones((20, 3)))
    unchanged = detector.score_samples(np.ones((2, 3)))
    changed = detector.score_samples(np.array([[2.0, 1.0, 1.0]]))
    assert np.allclose(unchanged, 0.0)
    assert changed[0] > 0


def test_chronological_split_preserves_order_and_reports_identity_overlap() -> None:
    partitions, split = chronological_partitions(_snapshots())
    assert split.train_cutoff < split.validation_cutoff < split.holdout_cutoff
    assert split.train_validation_wallet_overlap == 85
    assert split.validation_new_wallets == 5
    assert split.holdout_new_wallets == 5
    assert set(partitions["validation_new_wallets"]["wallet"]).isdisjoint(
        set(partitions["train"]["wallet"])
    )


def test_metadata_never_enters_feature_matrix() -> None:
    matrix = feature_matrix(_snapshots())
    assert "wallet" not in matrix
    assert "as_of" not in matrix
    assert matrix.shape[1] == 29


def test_preprocessing_is_fitted_on_train_only() -> None:
    frame = _snapshots()
    partitions, _ = chronological_partitions(frame)
    train_median = partitions["train"]["total_usd_volume"].median()
    bundle = fit_experiment(frame)
    for model in bundle["models"].values():
        statistics = model.named_steps["imputer"].statistics_
        feature_index = list(MODEL_FEATURE_COLUMNS).index("total_usd_volume")
        assert statistics[feature_index] == pytest.approx(train_median)


def test_models_are_deterministic_and_scores_share_direction() -> None:
    frame = _snapshots()
    first = fit_experiment(frame)
    second = fit_experiment(frame)
    extreme = frame.iloc[[0]].copy()
    for column in MODEL_FEATURE_COLUMNS:
        if column not in {"single_event_history", "insufficient_history_7d", "insufficient_history_30d"}:
            extreme[column] = pd.to_numeric(extreme[column]) * 1000 + 1000
    for name in MODEL_NAMES:
        first_scores = score_model(name, first["models"][name], frame)
        second_scores = score_model(name, second["models"][name], frame)
        extreme_score = score_model(name, first["models"][name], extreme)[0]
        assert np.allclose(first_scores, second_scores)
        assert first["metadata"]["score_semantics"].startswith("Higher means more unusual")
        assert not first["metadata"]["is_probability"]
        assert np.isfinite(extreme_score)
        assert extreme_score > np.median(first_scores)


def test_lof_novelty_and_training_score_contract_are_explicit() -> None:
    frame = _snapshots()
    bundle = fit_experiment(frame)
    model = bundle["models"]["local_outlier_factor"]
    assert model.named_steps["model"].novelty is True
    assert len(bundle["training_reference"]["local_outlier_factor_intrinsic_scores"]) == 90
    partitions, _ = chronological_partitions(frame)
    novelty_scores = score_model("local_outlier_factor", model, partitions["validation_new_wallets"])
    assert novelty_scores.shape == (5,)
    assert "not interchangeable" in bundle["metadata"]["lof_score_note"]


def test_serialization_reload_preserves_scores_and_contract(tmp_path: Path) -> None:
    frame = _snapshots()
    bundle = fit_experiment(frame, snapshot_sha256="synthetic-snapshot")
    paths = save_bundle(bundle, tmp_path)
    reloaded = load_bundle(paths["artifact"])
    manifest = json.loads(paths["manifest"].read_text())
    assert manifest["feature_registry_sha256"] == feature_registry_sha256()
    assert manifest["artifact_sha256"]
    for name in MODEL_NAMES:
        before = score_model(name, bundle["models"][name], frame)
        after = score_model(name, reloaded["models"][name], frame)
        assert np.allclose(before, after)


def test_configuration_validation_rejects_invalid_neighbors() -> None:
    with pytest.raises(AnomalyValidationError, match="lof_n_neighbors"):
        fit_experiment(_snapshots(), config=AnomalyConfig(lof_n_neighbors=1000))
    valid = replace(AnomalyConfig(), lof_n_neighbors=20)
    bundle = fit_experiment(_snapshots(), config=valid)
    assert bundle["metadata"]["config"]["lof_n_neighbors"] == 20


def test_evaluation_uses_no_label_metrics_or_probability_terminology() -> None:
    frame = _snapshots()
    bundle = fit_experiment(frame)
    report, scores = evaluate_experiment(bundle, frame, include_sensitivity=False)
    assert "supervised_metrics" not in report
    for partition in report["score_distributions"].values():
        assert all(set(summary).issubset({"count", "mean", "std", "min", "q25", "median", "q75", "q90", "q95", "q99", "max"}) for summary in partition.values())
    assert "not establish" in report["interpretation_boundary"]
    assert set(scores) == {
        "train",
        "validation",
        "holdout",
        "validation_new_wallets",
        "holdout_new_wallets",
    }


def test_feature_audit_records_missingness_correlation_and_history() -> None:
    audit = audit_feature_matrix(_snapshots())
    assert audit["feature_count"] == 29
    assert "inter_event_mean_seconds" in audit["missing_counts"]
    assert audit["nonfinite_infinite_count"] == 0
    assert audit["single_event_snapshot_count"] >= 0
    assert isinstance(audit["train_high_correlation_pairs"], list)


def test_cli_training_fails_cleanly_for_missing_input(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    import os

    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(project_root / "src")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "solana_risk.models.train_anomaly",
            "--input",
            str(tmp_path / "missing.csv"),
            "--artifact-dir",
            str(tmp_path / "artifacts"),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    assert completed.returncode == 2
    assert "validation failed" in completed.stdout
    assert not (tmp_path / "artifacts").exists()


def test_artifact_metadata_records_reproducibility_and_provisional_status() -> None:
    bundle = fit_experiment(_snapshots(), snapshot_sha256="abc")
    metadata = bundle["metadata"]
    assert metadata["experiment_status"] == EXPERIMENT_STATUS
    assert metadata["experiment_scope"] == "academic_research"
    assert metadata["labels_used"] is False
    assert metadata["snapshot_sha256"] == "abc"
    assert metadata["feature_registry_sha256"] == feature_registry_sha256()
    assert metadata["feature_order"] == list(MODEL_FEATURE_COLUMNS)
    assert metadata["config"]["random_seed"] == 42
    assert set(metadata["versions"]) == {"python", "numpy", "pandas", "scikit_learn", "joblib"}
    assert metadata["preprocessing"]["fitted_on"] == "earliest cutoff only"
