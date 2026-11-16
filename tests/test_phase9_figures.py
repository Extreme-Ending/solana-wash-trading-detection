from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from scripts.generate_phase9_figures import EvidenceValidationError, generate_package


def _write(path: Path, value: dict) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


@pytest.fixture()
def evidence_paths(tmp_path: Path) -> dict[str, Path]:
    artifact_sha = "a" * 64
    snapshot_sha = "b" * 64
    score = lambda median: {"count": 10, "q25": median - 0.02, "median": median, "q75": median + 0.02}
    models = {name: score(0.4) for name in ("isolation_forest", "local_outlier_factor", "robust_mad")}
    evaluation = {
        "experiment_status": "EXPERIMENTAL UNSUPERVISED ANOMALY MODELLING",
        "labels_used": False,
        "confirmed_outcomes_reported": False,
        "fingerprints": {"artifact_sha256": artifact_sha, "snapshot_sha256": snapshot_sha},
        "temporal_split": {
            "train_cutoff": "2025-09-01T00:00:00+00:00",
            "validation_cutoff": "2025-10-01T00:00:00+00:00",
            "holdout_cutoff": "2025-12-01T00:00:00+00:00",
            "train_rows": 8,
            "validation_rows": 9,
            "holdout_rows": 10,
            "train_validation_wallet_overlap": 8,
            "train_holdout_wallet_overlap": 8,
            "validation_new_wallets": 1,
            "holdout_new_wallets": 2,
        },
        "score_distributions": {
            "train": deepcopy(models),
            "validation": deepcopy(models),
            "holdout": deepcopy(models),
            "validation_new_wallets": deepcopy(models),
            "holdout_new_wallets": deepcopy(models),
        },
        "rank_agreement": {
            "holdout": {
                "isolation_forest__local_outlier_factor": 0.1,
                "isolation_forest__robust_mad": 0.8,
                "local_outlier_factor__robust_mad": 0.0,
            }
        },
        "validation_parameter_sensitivity": {
            key: {"validation_rank_correlation_with_primary": value}
            for key, value in {
                "isolation_n_estimators_100": 0.99,
                "isolation_n_estimators_500": 1.0,
                "isolation_max_samples_128": 0.98,
                "isolation_max_samples_512": 0.97,
                "lof_n_neighbors_15": 0.6,
                "lof_n_neighbors_70": 0.7,
            }.items()
        },
        "holdout_cohort_diagnostics": {
            key: {
                "selected_scores": {"isolation_forest": score(0.5)},
                "other_scores": {"isolation_forest": score(0.4)},
            }
            for key in (
                "single_event_history",
                "insufficient_history_30d",
                "top_1pct_total_usd_volume",
                "top_1pct_max_usd_volume",
            )
        },
    }
    cleaning = {
        "row_reconciliation": {"input": 10, "retained": 8, "quarantined": 2, "removed": 0, "reconciles": True}
    }
    features = {"features": {"count": 29}, "output": {"row_count": 27, "sha256": snapshot_sha}}
    manifest = {
        "artifact_sha256": artifact_sha,
        "snapshot_sha256": snapshot_sha,
        "experiment_status": "EXPERIMENTAL UNSUPERVISED ANOMALY MODELLING",
        "config": {"isolation_n_estimators": 300, "isolation_max_samples": 256, "random_seed": 42},
    }
    return {
        "evaluation_path": _write(tmp_path / "evaluation.json", evaluation),
        "cleaning_path": _write(tmp_path / "cleaning.json", cleaning),
        "features_path": _write(tmp_path / "features.json", features),
        "model_manifest_path": _write(tmp_path / "model_manifest.json", manifest),
    }


def test_generates_label_free_deterministic_package(tmp_path: Path, evidence_paths: dict[str, Path]) -> None:
    first = generate_package(**evidence_paths, output_dir=tmp_path / "first")
    second = generate_package(**evidence_paths, output_dir=tmp_path / "second")

    assert first["labels_used"] is False
    assert first["confirmed_outcomes_reported"] is False
    assert first["outputs"] == second["outputs"]
    assert len(first["outputs"]) == 8
    assert (tmp_path / "first" / "figure_03_holdout_rank_agreement.svg").is_file()
    assert (tmp_path / "first" / "table_01_pipeline_summary.csv").is_file()


def test_rejects_any_report_that_claims_labels(tmp_path: Path, evidence_paths: dict[str, Path]) -> None:
    evaluation = json.loads(evidence_paths["evaluation_path"].read_text())
    evaluation["labels_used"] = True
    evidence_paths["evaluation_path"].write_text(json.dumps(evaluation))

    with pytest.raises(EvidenceValidationError, match="labels_used=false"):
        generate_package(**evidence_paths, output_dir=tmp_path / "rejected")


def test_rejects_stale_artifact_fingerprint(tmp_path: Path, evidence_paths: dict[str, Path]) -> None:
    evaluation = json.loads(evidence_paths["evaluation_path"].read_text())
    evaluation["fingerprints"]["artifact_sha256"] = "c" * 64
    evidence_paths["evaluation_path"].write_text(json.dumps(evaluation))

    with pytest.raises(EvidenceValidationError, match="artifact fingerprints differ"):
        generate_package(**evidence_paths, output_dir=tmp_path / "rejected")
