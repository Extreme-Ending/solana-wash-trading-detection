"""Trusted-artifact and development-only anomaly-scoring contracts."""

from __future__ import annotations

import asyncio
import json
import math
import shutil
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import httpx
import pandas as pd
import pytest

from solana_risk.api.auth import TokenInvalidError
from solana_risk.api.config import Settings
from solana_risk.api.experimental_scoring import (
    ExperimentalArtifactError,
    TrustedExperimentalScorer,
)
from solana_risk.api.main import create_app
from solana_risk.api.schemas import ScoreRequest
from solana_risk.features.build import METADATA_COLUMNS, MODEL_FEATURE_COLUMNS
from solana_risk.models.train_anomaly import AnomalyConfig, fit_experiment, save_bundle, sha256_file


class _Verifier:
    def verify(self, token: str) -> Mapping[str, Any]:
        if token != "test-token":
            raise TokenInvalidError
        return {
            "aud": "test-project-123",
            "iss": "https://securetoken.google.com/test-project-123",
            "sub": "approved-test-uid",
            "uid": "approved-test-uid",
            "exp": 4_102_444_800,
            "email": "approved@example.test",
            "email_verified": True,
            "firebase": {"sign_in_provider": "google.com"},
        }


def _event(
    row: int,
    *,
    time: str,
    amount: float = 100.0,
) -> dict[str, Any]:
    return {
        "source_row_number": row,
        "wallet": "synthetic-score-wallet",
        "block_time": time,
        "block_slot": 10_000 + row,
        "tx_hash": f"synthetic-score-tx-{row}",
        "dex": "synthetic-dex",
        "token_pair": "TOKEN-A/TOKEN-B",
        "token_in": "synthetic-token-a",
        "token_out": "synthetic-token-b",
        "amount_usd": amount,
        "fee_usd": 0.1,
        "outer_instruction_index": 1,
        "inner_instruction_index": row,
    }


def _payload() -> dict[str, Any]:
    return {
        "as_of": "2025-11-01T00:00:00Z",
        "events": [
            _event(1, time="2025-10-01T00:00:00Z", amount=10.0),
            _event(2, time="2025-10-31T00:00:00Z", amount=30.0),
            _event(3, time="2025-11-01T00:00:00Z", amount=9_999.0),
        ],
    }


def _request(app: Any, path: str, payload: dict[str, Any]) -> httpx.Response:
    async def run() -> httpx.Response:
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=True)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post(
                path,
                json=payload,
                headers={"Authorization": "Bearer test-token"},
            )

    return asyncio.run(run())


def _snapshot_frame() -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    cutoffs = ("2025-09-01T00:00:00Z", "2025-10-01T00:00:00Z", "2025-12-01T00:00:00Z")
    for cutoff_index, cutoff in enumerate(cutoffs):
        for wallet_index in range(40):
            record: dict[str, Any] = {
                METADATA_COLUMNS[0]: f"synthetic-training-wallet-{wallet_index:03d}",
                METADATA_COLUMNS[1]: cutoff,
            }
            for feature_index, name in enumerate(MODEL_FEATURE_COLUMNS):
                record[name] = float(
                    1 + wallet_index + cutoff_index * 0.25 + feature_index * 0.01
                )
            record["single_event_history"] = float(wallet_index % 2 == 0)
            record["insufficient_history_7d"] = float(wallet_index % 3 == 0)
            record["insufficient_history_30d"] = float(wallet_index % 5 == 0)
            records.append(record)
    return pd.DataFrame(records, columns=(*METADATA_COLUMNS, *MODEL_FEATURE_COLUMNS))


@pytest.fixture(scope="module")
def trusted_files(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path, str]:
    directory = tmp_path_factory.mktemp("experimental-artifact")
    bundle = fit_experiment(
        _snapshot_frame(),
        config=AnomalyConfig(
            isolation_n_estimators=20,
            isolation_max_samples=32,
            lof_n_neighbors=5,
        ),
        snapshot_sha256="0" * 64,
    )
    paths = save_bundle(bundle, directory)
    return paths["artifact"], paths["manifest"], sha256_file(paths["artifact"])


def _settings(
    artifact: Path,
    manifest: Path,
    digest: str,
    **overrides: Any,
) -> Settings:
    values: dict[str, Any] = {
        "environment": "development",
        "firebase_project_id": "test-project-123",
        "allowed_user_uids": frozenset({"approved-test-uid"}),
        "experimental_scoring_enabled": True,
        "experimental_model_artifact": artifact,
        "experimental_model_manifest": manifest,
        "experimental_artifact_sha256": digest,
    }
    values.update(overrides)
    return Settings(**values)


def _copy_trusted_files(
    trusted_files: tuple[Path, Path, str],
    destination: Path,
) -> tuple[Path, Path, str]:
    artifact_source, manifest_source, digest = trusted_files
    artifact = destination / artifact_source.name
    manifest = destination / manifest_source.name
    shutil.copy2(artifact_source, artifact)
    shutil.copy2(manifest_source, manifest)
    return artifact, manifest, digest


def test_trusted_local_artifact_scores_with_point_in_time_exclusion(
    trusted_files: tuple[Path, Path, str],
) -> None:
    artifact, manifest, digest = trusted_files
    app = create_app(_settings(artifact, manifest, digest), token_verifier=_Verifier())
    response = _request(app, "/v1/score", _payload())
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "experimental_anomaly_score"
    assert body["methodology_status"] == "experimental_unsupervised_research_only"
    assert body["model_id"] == "isolation_forest"
    assert body["model_version"] == "4B.1"
    assert body["is_probability"] is False
    assert body["score_direction"] == "higher_means_more_anomalous_relative_to_training_reference"
    assert math.isfinite(body["anomaly_score"])
    assert body["included_historical_event_count"] == 2
    assert body["excluded_at_or_after_cutoff_count"] == 1
    assert body["training_cutoff"] == "2025-09-01T00:00:00Z"
    assert any("at or after as_of" in warning for warning in body["warnings"])
    serialized = json.dumps(body).casefold()
    assert "fraud_probability" not in serialized
    assert "wash_probability" not in serialized


def test_scoring_is_deterministic_after_trusted_reload(
    trusted_files: tuple[Path, Path, str],
) -> None:
    artifact, manifest, digest = trusted_files
    payload = ScoreRequest.model_validate(_payload())
    first = TrustedExperimentalScorer.load(
        artifact_path=artifact,
        manifest_path=manifest,
        expected_sha256=digest,
    ).score(payload)
    second = TrustedExperimentalScorer.load(
        artifact_path=artifact,
        manifest_path=manifest,
        expected_sha256=digest,
    ).score(payload)
    assert first.anomaly_score == second.anomaly_score
    assert first.model_dump(mode="json") == second.model_dump(mode="json")


def test_single_event_history_returns_explicit_warnings(
    trusted_files: tuple[Path, Path, str],
) -> None:
    artifact, manifest, digest = trusted_files
    app = create_app(_settings(artifact, manifest, digest), token_verifier=_Verifier())
    payload = _payload()
    payload["events"] = [_event(1, time="2025-10-31T00:00:00Z")]
    response = _request(app, "/v1/score", payload)
    assert response.status_code == 200
    warnings = response.json()["warnings"]
    assert any("Only one pre-cutoff event" in warning for warning in warnings)
    assert any("Less than seven days" in warning for warning in warnings)


def test_missing_artifact_fails_closed_at_endpoint(tmp_path: Path) -> None:
    missing = tmp_path / "missing.joblib"
    app = create_app(
        _settings(missing, tmp_path / "missing.json", "0" * 64),
        token_verifier=_Verifier(),
    )
    response = _request(app, "/v1/score", _payload())
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "EXPERIMENTAL_MODEL_UNAVAILABLE"


def test_experimental_scoring_preserves_uid_allowlist_authorization(
    trusted_files: tuple[Path, Path, str],
) -> None:
    artifact, manifest, digest = trusted_files
    app = create_app(
        _settings(
            artifact,
            manifest,
            digest,
            allowed_user_uids=frozenset({"different-approved-uid"}),
        ),
        token_verifier=_Verifier(),
    )
    response = _request(app, "/v1/score", _payload())
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "USER_NOT_ALLOWED"


def test_scoring_time_before_training_reference_is_rejected(
    trusted_files: tuple[Path, Path, str],
) -> None:
    artifact, manifest, digest = trusted_files
    app = create_app(_settings(artifact, manifest, digest), token_verifier=_Verifier())
    payload = _payload()
    payload["as_of"] = "2025-08-31T23:59:59Z"
    payload["events"] = [_event(1, time="2025-08-01T00:00:00Z")]
    response = _request(app, "/v1/score", payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "SCORING_TIME_PRECEDES_MODEL_REFERENCE"


def test_checksum_mismatch_is_rejected_before_deserialization(
    trusted_files: tuple[Path, Path, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact, manifest, _ = trusted_files
    loaded = False

    def forbidden(_: Path) -> None:
        nonlocal loaded
        loaded = True
        raise AssertionError("joblib.load must not run for an untrusted checksum")

    monkeypatch.setattr("solana_risk.api.experimental_scoring.joblib.load", forbidden)
    with pytest.raises(ExperimentalArtifactError, match="manifest checksum"):
        TrustedExperimentalScorer.load(
            artifact_path=artifact,
            manifest_path=manifest,
            expected_sha256="f" * 64,
        )
    assert loaded is False


@pytest.mark.parametrize(
    ("field", "bad_value", "message"),
    [
        ("experiment_version", "unsupported", "model version"),
        ("training_cutoff", "2024-01-01T00:00:00+00:00", "training cutoff"),
        ("feature_order", ["wrong"], "feature order"),
        ("feature_registry_sha256", "0" * 64, "feature registry fingerprint"),
        ("versions", {"numpy": "0"}, "numpy version"),
    ],
)
def test_incompatible_manifest_metadata_is_rejected(
    trusted_files: tuple[Path, Path, str],
    tmp_path: Path,
    field: str,
    bad_value: Any,
    message: str,
) -> None:
    artifact, manifest, digest = _copy_trusted_files(trusted_files, tmp_path)
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data[field] = bad_value
    manifest.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ExperimentalArtifactError, match=message):
        TrustedExperimentalScorer.load(
            artifact_path=artifact,
            manifest_path=manifest,
            expected_sha256=digest,
        )


def test_production_refuses_scoring_even_when_local_flags_are_set(
    trusted_files: tuple[Path, Path, str],
) -> None:
    artifact, manifest, digest = trusted_files

    class _ForbiddenScorer:
        def score(self, _: Any) -> Any:
            raise AssertionError("Production must not use an injected experimental scorer")

    app = create_app(
        _settings(
            artifact,
            manifest,
            digest,
            environment="production",
            check_revoked_tokens=True,
        ),
        token_verifier=_Verifier(),
        experimental_scorer=_ForbiddenScorer(),
    )
    response = _request(app, "/v1/score", _payload())
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "MODEL_NOT_APPROVED"
    assert app.state.experimental_scorer is None


def test_default_configuration_never_loads_experimental_module(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*_: Any, **__: Any) -> None:
        raise AssertionError("Disabled scoring must not load an artifact")

    monkeypatch.setattr("joblib.load", forbidden)
    settings = Settings(
        firebase_project_id="test-project-123",
        allowed_user_uids=frozenset({"approved-test-uid"}),
    )
    app = create_app(settings, token_verifier=_Verifier())
    response = _request(app, "/v1/score", _payload())
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "MODEL_NOT_APPROVED"
