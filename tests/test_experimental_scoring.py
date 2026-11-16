"""Trusted-artifact and development-only anomaly-scoring contracts."""

from __future__ import annotations

import asyncio
import json
import math
import shutil
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import joblib
import numpy as np
import pandas as pd
import pytest

from solana_risk.api.auth import TokenInvalidError
from solana_risk.api.config import Settings
from solana_risk.api.experimental_scoring import (
    ExperimentalArtifactError,
    TrustedExperimentalScorer,
)
from solana_risk.api.main import create_app
from solana_risk.api.schemas import (
    BatchScoreRequest,
    FeatureReferenceStatistic,
    FeatureTrainingReference,
    ScoreRequest,
)
from solana_risk.features.build import (
    METADATA_COLUMNS,
    MODEL_FEATURE_COLUMNS,
    feature_registry_sha256,
)
from solana_risk.models.train_anomaly import (
    BINARY_FEATURE_COLUMNS,
    AnomalyConfig,
    fit_experiment,
    save_bundle,
    sha256_file,
)


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
    wallet: str = "synthetic-score-wallet",
) -> dict[str, Any]:
    return {
        "source_row_number": row,
        "wallet": wallet,
        "block_time": time,
        "block_slot": 10_000 + row,
        "tx_hash": f"{wallet}-synthetic-score-tx-{row}",
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


def _batch_payload(*, review_budget: int | None = 2) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "as_of": "2025-11-01T00:00:00Z",
        "wallet_histories": [
            {
                "wallet": "synthetic-batch-wallet-a",
                "events": [
                    _event(
                        1,
                        wallet="synthetic-batch-wallet-a",
                        time="2025-09-15T00:00:00Z",
                        amount=10.0,
                    ),
                    _event(
                        2,
                        wallet="synthetic-batch-wallet-a",
                        time="2025-10-31T00:00:00Z",
                        amount=25_000.0,
                    ),
                ],
            },
            {
                "wallet": "synthetic-batch-wallet-b",
                "events": [
                    _event(
                        1,
                        wallet="synthetic-batch-wallet-b",
                        time="2025-10-31T12:00:00Z",
                        amount=75.0,
                    )
                ],
            },
            {
                "wallet": "synthetic-batch-wallet-c",
                "events": [
                    _event(
                        1,
                        wallet="synthetic-batch-wallet-c",
                        time="2025-10-01T00:00:00Z",
                        amount=250.0,
                    ),
                    _event(
                        2,
                        wallet="synthetic-batch-wallet-c",
                        time="2025-10-10T00:00:00Z",
                        amount=275.0,
                    ),
                    _event(
                        3,
                        wallet="synthetic-batch-wallet-c",
                        time="2025-11-01T00:00:00Z",
                        amount=999_999.0,
                    ),
                ],
            },
        ],
    }
    if review_budget is not None:
        payload["review_budget"] = review_budget
    return payload


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


def _feature_reference() -> FeatureTrainingReference:
    statistics = {
        name: FeatureReferenceStatistic(
            observed_count=40,
            missing_count=0,
            minimum=0.0,
            quartile_1=1.0,
            median=2.0,
            mean=2.0,
            quartile_3=3.0,
            maximum=4.0,
            is_binary=name in BINARY_FEATURE_COLUMNS,
            is_constant=False,
        )
        for name in MODEL_FEATURE_COLUMNS
    }
    return FeatureTrainingReference(
        version="training_reference_v1",
        source="phase_3_training_snapshots",
        training_cutoff=datetime(2025, 9, 1, tzinfo=timezone.utc),
        snapshot_sha256="0" * 64,
        wallet_count=40,
        feature_registry_sha256=feature_registry_sha256(),
        feature_order=list(MODEL_FEATURE_COLUMNS),
        statistics=statistics,
        comparison_method="robust_iqr_distance_for_nonbinary_nonconstant_features",
    )


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


def test_batch_scores_match_single_scores_and_rank_descending(
    trusted_files: tuple[Path, Path, str],
) -> None:
    artifact, manifest, digest = trusted_files
    app = create_app(_settings(artifact, manifest, digest), token_verifier=_Verifier())
    payload = _batch_payload()
    response = _request(app, "/v1/score/batch", payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "experimental_batch_anomaly_ranking"
    assert body["methodology_status"] == "experimental_unsupervised_research_only"
    assert body["wallets_submitted"] == 3
    assert body["wallets_scored"] == 3
    assert body["wallets_rejected"] == 0
    assert body["review_budget"] == 2
    assert len(body["review_candidates"]) == 2
    scores = [item["anomaly_score"] for item in body["ranked_wallets"]]
    assert scores == sorted(scores, reverse=True)
    assert [item["rank"] for item in body["ranked_wallets"]] == [1, 2, 3]
    assert [item["selected_for_review"] for item in body["ranked_wallets"]] == [
        True,
        True,
        False,
    ]
    assert body["feature_reference"]["source"] == "phase_3_training_snapshots"
    assert body["feature_reference"]["training_cutoff"] == body["training_cutoff"]
    assert body["feature_reference"]["feature_order"] == list(MODEL_FEATURE_COLUMNS)
    assert set(body["feature_reference"]["statistics"]) == set(MODEL_FEATURE_COLUMNS)
    assert all(list(item["features"]) == list(MODEL_FEATURE_COLUMNS) for item in body["ranked_wallets"])
    for history in payload["wallet_histories"]:
        single = _request(
            app,
            "/v1/score",
            {"as_of": payload["as_of"], "events": history["events"]},
        )
        assert single.status_code == 200
        batch_item = next(
            item for item in body["ranked_wallets"] if item["wallet"] == history["wallet"]
        )
        assert batch_item["anomaly_score"] == single.json()["anomaly_score"]
    serialized = json.dumps(body).casefold()
    assert "fraud_probability" not in serialized
    assert "risk_class" not in serialized


def test_batch_requests_reuse_one_loaded_artifact(
    trusted_files: tuple[Path, Path, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact, manifest, digest = trusted_files
    original_load = joblib.load
    load_calls = 0

    def counting_load(*args: Any, **kwargs: Any) -> Any:
        nonlocal load_calls
        load_calls += 1
        return original_load(*args, **kwargs)

    monkeypatch.setattr("solana_risk.api.experimental_scoring.joblib.load", counting_load)
    app = create_app(_settings(artifact, manifest, digest), token_verifier=_Verifier())
    assert _request(app, "/v1/score/batch", _batch_payload()).status_code == 200
    assert _request(app, "/v1/score/batch", _batch_payload()).status_code == 200
    assert load_calls == 1


def test_batch_results_are_reproducible_and_input_order_independent(
    trusted_files: tuple[Path, Path, str],
) -> None:
    artifact, manifest, digest = trusted_files
    app = create_app(_settings(artifact, manifest, digest), token_verifier=_Verifier())
    original = _batch_payload()
    reordered = _batch_payload()
    reordered["wallet_histories"].reverse()
    for history in reordered["wallet_histories"]:
        history["events"].reverse()
    first = _request(app, "/v1/score/batch", original)
    second = _request(app, "/v1/score/batch", reordered)
    third = _request(app, "/v1/score/batch", original)
    assert first.status_code == second.status_code == third.status_code == 200
    assert first.json() == second.json() == third.json()


def test_batch_ties_use_wallet_identifier_as_stable_secondary_key() -> None:
    class _ConstantModel:
        calls = 0

        def score_samples(self, matrix: pd.DataFrame) -> np.ndarray:
            self.calls += 1
            return np.full(len(matrix), -0.5, dtype=float)

    model = _ConstantModel()
    scorer = TrustedExperimentalScorer(
        model=model,  # type: ignore[arg-type]
        model_version="synthetic-test-version",
        training_cutoff=datetime(2025, 9, 1, tzinfo=timezone.utc),
        feature_reference=_feature_reference(),
    )
    payload = BatchScoreRequest.model_validate(_batch_payload(review_budget=1))
    response = scorer.score_batch(
        payload,
        max_wallets=20,
        max_events=100,
        max_events_per_wallet=50,
    )
    assert [item.anomaly_score for item in response.ranked_wallets] == [0.5, 0.5, 0.5]
    assert [item.wallet for item in response.ranked_wallets] == sorted(
        item.wallet for item in response.ranked_wallets
    )
    assert response.review_candidates == [response.ranked_wallets[0].wallet]
    assert model.calls == 1


def test_batch_partial_failure_is_explicit_and_feature_isolated(
    trusted_files: tuple[Path, Path, str],
) -> None:
    artifact, manifest, digest = trusted_files
    app = create_app(_settings(artifact, manifest, digest), token_verifier=_Verifier())
    baseline_payload = _batch_payload(review_budget=1)
    baseline_payload["wallet_histories"] = [baseline_payload["wallet_histories"][0]]
    baseline = _request(app, "/v1/score/batch", baseline_payload)
    assert baseline.status_code == 200
    baseline_score = baseline.json()["ranked_wallets"][0]["anomaly_score"]

    mixed = _batch_payload(review_budget=10)
    mixed["wallet_histories"] = [
        mixed["wallet_histories"][0],
        {"wallet": "synthetic-empty-wallet", "events": []},
        {
            "wallet": "synthetic-future-wallet",
            "events": [
                _event(
                    1,
                    wallet="synthetic-future-wallet",
                    time="2025-11-01T00:00:00Z",
                )
            ],
        },
        {
            "wallet": "synthetic-group-wallet",
            "events": [
                _event(
                    1,
                    wallet="different-event-wallet",
                    time="2025-10-01T00:00:00Z",
                )
            ],
        },
    ]
    response = _request(app, "/v1/score/batch", mixed)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["wallets_scored"] == 1
    assert body["wallets_rejected"] == 3
    assert body["review_budget_requested"] == 10
    assert body["review_budget"] == 1
    assert body["ranked_wallets"][0]["anomaly_score"] == baseline_score
    assert {item["code"] for item in body["rejected_wallets"]} == {
        "EMPTY_WALLET_HISTORY",
        "INSUFFICIENT_HISTORY",
        "WALLET_EVENT_MISMATCH",
    }


def test_batch_duplicate_record_is_rejected_without_silent_deduplication(
    trusted_files: tuple[Path, Path, str],
) -> None:
    artifact, manifest, digest = trusted_files
    app = create_app(_settings(artifact, manifest, digest), token_verifier=_Verifier())
    payload = _batch_payload(review_budget=1)
    duplicate = dict(payload["wallet_histories"][0]["events"][0])
    duplicate["source_row_number"] = 99
    payload["wallet_histories"][0]["events"].append(duplicate)
    response = _request(app, "/v1/score/batch", payload)
    assert response.status_code == 200
    rejected = response.json()["rejected_wallets"]
    assert any(item["code"] == "DUPLICATE_EVENT_RECORD" for item in rejected)


def test_batch_allows_repeated_transaction_hash_for_distinct_instructions(
    trusted_files: tuple[Path, Path, str],
) -> None:
    artifact, manifest, digest = trusted_files
    app = create_app(_settings(artifact, manifest, digest), token_verifier=_Verifier())
    payload = _batch_payload(review_budget=1)
    first = payload["wallet_histories"][0]["events"][0]
    second = payload["wallet_histories"][0]["events"][1]
    second["tx_hash"] = first["tx_hash"]
    second["outer_instruction_index"] = 2
    response = _request(app, "/v1/score/batch", payload)
    assert response.status_code == 200, response.text
    assert response.json()["wallets_scored"] == 3


@pytest.mark.parametrize(
    ("settings_overrides", "mutator", "expected_code"),
    [
        (
            {"max_batch_wallets": 2},
            lambda payload: payload,
            "BATCH_WALLET_LIMIT_EXCEEDED",
        ),
        (
            {"max_batch_events": 3},
            lambda payload: payload,
            "BATCH_EVENT_LIMIT_EXCEEDED",
        ),
        (
            {"max_batch_events_per_wallet": 1},
            lambda payload: payload,
            "WALLET_EVENT_LIMIT_EXCEEDED",
        ),
        (
            {"max_batch_wallets": 2},
            lambda payload: {**payload, "review_budget": 3},
            "BATCH_WALLET_LIMIT_EXCEEDED",
        ),
    ],
)
def test_batch_resource_limits_fail_closed(
    trusted_files: tuple[Path, Path, str],
    settings_overrides: dict[str, int],
    mutator: Any,
    expected_code: str,
) -> None:
    artifact, manifest, digest = trusted_files
    app = create_app(
        _settings(artifact, manifest, digest, **settings_overrides),
        token_verifier=_Verifier(),
    )
    response = _request(app, "/v1/score/batch", mutator(_batch_payload()))
    assert response.status_code == 413
    assert response.json()["error"]["code"] == expected_code


def test_batch_review_budget_limit_is_enforced(
    trusted_files: tuple[Path, Path, str],
) -> None:
    artifact, manifest, digest = trusted_files
    app = create_app(_settings(artifact, manifest, digest), token_verifier=_Verifier())
    response = _request(
        app,
        "/v1/score/batch",
        _batch_payload(review_budget=21),
    )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "REVIEW_BUDGET_LIMIT_EXCEEDED"


def test_batch_structural_validation_and_all_rejected_behavior(
    trusted_files: tuple[Path, Path, str],
) -> None:
    artifact, manifest, digest = trusted_files
    app = create_app(_settings(artifact, manifest, digest), token_verifier=_Verifier())
    malformed = _batch_payload()
    malformed["wallet_histories"][0]["events"][0]["amount_usd"] = "not-numeric"
    response = _request(app, "/v1/score/batch", malformed)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "REQUEST_VALIDATION_ERROR"

    invalid_timestamp = _batch_payload()
    invalid_timestamp["wallet_histories"][0]["events"][0]["block_time"] = (
        "2025-09-15T03:00:00+03:00"
    )
    response = _request(app, "/v1/score/batch", invalid_timestamp)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "REQUEST_VALIDATION_ERROR"

    all_empty = {
        "as_of": "2025-11-01T00:00:00Z",
        "wallet_histories": [{"wallet": "synthetic-empty-wallet", "events": []}],
    }
    response = _request(app, "/v1/score/batch", all_empty)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "NO_SCORABLE_WALLETS"


def test_batch_scoring_time_and_security_gates(
    trusted_files: tuple[Path, Path, str],
) -> None:
    artifact, manifest, digest = trusted_files
    enabled = create_app(_settings(artifact, manifest, digest), token_verifier=_Verifier())
    too_early = _batch_payload()
    too_early["as_of"] = "2025-08-01T00:00:00Z"
    response = _request(enabled, "/v1/score/batch", too_early)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "SCORING_TIME_PRECEDES_MODEL_REFERENCE"

    disabled = create_app(
        Settings(
            firebase_project_id="test-project-123",
            allowed_user_uids=frozenset({"approved-test-uid"}),
        ),
        token_verifier=_Verifier(),
    )
    response = _request(disabled, "/v1/score/batch", _batch_payload())
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "MODEL_NOT_APPROVED"

    production = create_app(
        _settings(
            artifact,
            manifest,
            digest,
            environment="production",
            check_revoked_tokens=True,
        ),
        token_verifier=_Verifier(),
    )
    response = _request(production, "/v1/score/batch", _batch_payload())
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "MODEL_NOT_APPROVED"


def test_batch_uid_allowlist_is_enforced(
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
    response = _request(app, "/v1/score/batch", _batch_payload())
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "USER_NOT_ALLOWED"


def test_missing_artifact_fails_closed_at_endpoint(tmp_path: Path) -> None:
    missing = tmp_path / "missing.joblib"
    app = create_app(
        _settings(missing, tmp_path / "missing.json", "0" * 64),
        token_verifier=_Verifier(),
    )
    response = _request(app, "/v1/score", _payload())
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "EXPERIMENTAL_MODEL_UNAVAILABLE"
    batch_response = _request(app, "/v1/score/batch", _batch_payload())
    assert batch_response.status_code == 503
    assert batch_response.json()["error"]["code"] == "EXPERIMENTAL_MODEL_UNAVAILABLE"


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
        ("feature_reference_version", "unsupported", "artifact feature_reference_version"),
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


def test_incompatible_training_reference_is_rejected_after_checksum_verification(
    trusted_files: tuple[Path, Path, str],
    tmp_path: Path,
) -> None:
    artifact, manifest, _ = _copy_trusted_files(trusted_files, tmp_path)
    bundle = joblib.load(artifact)
    del bundle["training_reference"]["statistics"][MODEL_FEATURE_COLUMNS[0]]
    joblib.dump(bundle, artifact, compress=3)
    digest = sha256_file(artifact)
    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    manifest_data["artifact_sha256"] = digest
    manifest.write_text(json.dumps(manifest_data), encoding="utf-8")

    with pytest.raises(ExperimentalArtifactError, match="feature set is incompatible"):
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
