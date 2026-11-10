"""Phase 5A API contracts, feature parity, limits, and not-ready tests."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping
from typing import Any

import httpx
import joblib
import pandas as pd
import pytest
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor

from solana_risk.api.config import ConfigurationError, Settings
from solana_risk.api.main import create_app
from solana_risk.features.build import (
    FEATURE_RULES_VERSION,
    MODEL_FEATURE_COLUMNS,
    build_wallet_snapshots,
    feature_registry_sha256,
)
from solana_risk.models.baselines import RobustMADDetector


def _event(
    row_number: int,
    *,
    wallet: str = "synthetic-wallet-001",
    block_time: str = "2025-01-15T12:00:00Z",
    amount_usd: float = 125.5,
) -> dict[str, Any]:
    return {
        "source_row_number": row_number,
        "wallet": wallet,
        "block_time": block_time,
        "block_slot": 1000 + row_number,
        "tx_hash": f"synthetic-transaction-{row_number:03d}",
        "dex": "synthetic-dex",
        "token_pair": "TOKEN-A/TOKEN-B",
        "token_in": "synthetic-token-a",
        "token_out": "synthetic-token-b",
        "amount_usd": amount_usd,
        "fee_usd": 0.25,
        "outer_instruction_index": 1,
        "inner_instruction_index": row_number - 1,
    }


def _payload(*events: Mapping[str, Any], as_of: str = "2025-02-01T00:00:00Z") -> dict[str, Any]:
    return {"as_of": as_of, "events": [dict(event) for event in events]}


def _request(
    app: Any,
    method: str,
    path: str,
    **kwargs: Any,
) -> httpx.Response:
    async def run() -> httpx.Response:
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=True)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(run())


@pytest.fixture
def app() -> Any:
    return create_app(
        Settings(
            cors_origins=("http://localhost:5173",),
            max_events=10,
            max_request_bytes=100_000,
        )
    )


def test_health_is_independent_of_prediction_readiness(app: Any) -> None:
    response = _request(app, "GET", "/healthz")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Solana Wallet Feature Service",
        "version": "0.1.0",
    }


def test_readiness_returns_structured_model_not_approved(app: Any) -> None:
    response = _request(app, "GET", "/readyz")
    assert response.status_code == 503
    assert response.json() == {
        "error": {
            "code": "MODEL_NOT_APPROVED",
            "message": "Prediction capability is unavailable.",
            "details": {"prediction_available": False},
        }
    }


def test_scoring_interface_returns_503_without_score_fields(app: Any) -> None:
    response = _request(app, "POST", "/v1/score", json=_payload(_event(1)))
    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "MODEL_NOT_APPROVED"
    serialized = json.dumps(body).casefold()
    assert "anomaly_score" not in serialized
    assert "fraud_probability" not in serialized
    assert "wash_probability" not in serialized


def test_valid_feature_preview_is_descriptive_and_registry_ordered(app: Any) -> None:
    response = _request(app, "POST", "/v1/features/preview", json=_payload(_event(1)))
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "descriptive_features"
    assert body["source"] == "user_supplied_unverified_events"
    assert body["wallet"] == "synthetic-wallet-001"
    assert body["feature_rules_version"] == FEATURE_RULES_VERSION
    assert body["feature_registry_sha256"] == feature_registry_sha256()
    assert body["feature_order"] == list(MODEL_FEATURE_COLUMNS)
    assert list(body["features"]) == list(MODEL_FEATURE_COLUMNS)
    assert body["features"]["historical_event_count"] == 1
    assert body["features"]["inter_event_mean_seconds"] is None
    assert "do not establish" in body["interpretation"]


def test_api_feature_values_match_shared_python_builder(app: Any) -> None:
    events = [
        _event(1, block_time="2025-01-10T00:00:00Z", amount_usd=10.0),
        _event(2, block_time="2025-01-20T00:00:00Z", amount_usd=30.0),
        _event(3, block_time="2025-03-01T00:00:00Z", amount_usd=999.0),
    ]
    response = _request(app, "POST", "/v1/features/preview", json=_payload(*events))
    assert response.status_code == 200, response.text
    body = response.json()
    expected = build_wallet_snapshots(pd.DataFrame(events), ["2025-02-01T00:00:00Z"]).iloc[0]
    assert body["included_historical_event_count"] == 2
    assert body["excluded_at_or_after_cutoff_count"] == 1
    for feature in MODEL_FEATURE_COLUMNS:
        observed = body["features"][feature]
        expected_value = expected[feature]
        if pd.isna(expected_value):
            assert observed is None
        elif isinstance(expected_value, (float, int)) and not isinstance(expected_value, bool):
            assert observed == pytest.approx(expected_value)
        else:
            assert observed == expected_value


def test_events_at_and_after_cutoff_are_excluded(app: Any) -> None:
    events = [
        _event(1, block_time="2025-01-31T23:59:59Z"),
        _event(2, block_time="2025-02-01T00:00:00Z"),
        _event(3, block_time="2025-02-02T00:00:00Z"),
    ]
    response = _request(app, "POST", "/v1/features/preview", json=_payload(*events))
    assert response.status_code == 200
    body = response.json()
    assert body["features"]["historical_event_count"] == 1
    assert body["included_historical_event_count"] == 1
    assert body["excluded_at_or_after_cutoff_count"] == 2


def test_no_prior_event_returns_structured_insufficient_history(app: Any) -> None:
    response = _request(
        app,
        "POST",
        "/v1/features/preview",
        json=_payload(_event(1, block_time="2025-02-01T00:00:00Z")),
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INSUFFICIENT_HISTORY"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("wallet", " "),
        ("wallet", "wallet\ncontrol"),
        ("amount_usd", -1.0),
        ("amount_usd", "125.5"),
        ("fee_usd", -0.1),
        ("tx_hash", ""),
    ],
)
def test_invalid_event_values_return_sanitized_422(
    app: Any,
    field: str,
    value: Any,
) -> None:
    event = _event(1)
    event[field] = value
    response = _request(app, "POST", "/v1/features/preview", json=_payload(event))
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "REQUEST_VALIDATION_ERROR"
    assert body["error"]["details"]["issues"]
    assert "input" not in json.dumps(body["error"]["details"])


@pytest.mark.parametrize(
    "as_of",
    ["not-a-time", "2025-02-01T00:00:00", "2025-02-01T03:00:00+03:00"],
)
def test_invalid_or_non_utc_cutoff_is_rejected(app: Any, as_of: str) -> None:
    response = _request(app, "POST", "/v1/features/preview", json=_payload(_event(1), as_of=as_of))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "REQUEST_VALIDATION_ERROR"


def test_non_utc_event_timestamp_is_rejected(app: Any) -> None:
    event = _event(1, block_time="2025-01-15T15:00:00+03:00")
    response = _request(app, "POST", "/v1/features/preview", json=_payload(event))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "REQUEST_VALIDATION_ERROR"


def test_nonfinite_amount_is_rejected_by_http_contract(app: Any) -> None:
    event = _event(1)
    event["amount_usd"] = float("inf")
    raw_body = json.dumps(_payload(event), allow_nan=True)
    response = _request(
        app,
        "POST",
        "/v1/features/preview",
        content=raw_body,
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "REQUEST_VALIDATION_ERROR"


def test_multiple_wallets_and_duplicate_source_rows_are_rejected(app: Any) -> None:
    other_wallet = _event(2, wallet="synthetic-wallet-002")
    response = _request(
        app,
        "POST",
        "/v1/features/preview",
        json=_payload(_event(1), other_wallet),
    )
    assert response.status_code == 422
    duplicate_row = _event(1, block_time="2025-01-16T00:00:00Z")
    response = _request(
        app,
        "POST",
        "/v1/features/preview",
        json=_payload(_event(1), duplicate_row),
    )
    assert response.status_code == 422


def test_missing_required_field_and_extra_field_are_rejected(app: Any) -> None:
    missing = _event(1)
    missing.pop("amount_usd")
    response = _request(app, "POST", "/v1/features/preview", json=_payload(missing))
    assert response.status_code == 422
    extra = _event(1)
    extra["server_file_path"] = "/tmp/model.joblib"
    response = _request(app, "POST", "/v1/features/preview", json=_payload(extra))
    assert response.status_code == 422


def test_event_count_limit_is_configurable() -> None:
    limited_app = create_app(Settings(max_events=2, max_request_bytes=100_000))
    response = _request(
        limited_app,
        "POST",
        "/v1/features/preview",
        json=_payload(_event(1), _event(2), _event(3)),
    )
    assert response.status_code == 413
    assert response.json()["error"] == {
        "code": "EVENT_LIMIT_EXCEEDED",
        "message": "Event count exceeds the configured request limit.",
        "details": {"max_events": 2},
    }


def test_raw_request_byte_limit_is_enforced_before_validation() -> None:
    limited_app = create_app(Settings(max_events=10, max_request_bytes=100))
    response = _request(
        limited_app,
        "POST",
        "/v1/features/preview",
        json=_payload(_event(1)),
    )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "REQUEST_TOO_LARGE"
    assert response.json()["error"]["details"] == {"max_request_bytes": 100}


def test_cors_allows_only_configured_origin(app: Any) -> None:
    allowed = _request(
        app,
        "OPTIONS",
        "/v1/features/preview",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    denied = _request(
        app,
        "OPTIONS",
        "/v1/features/preview",
        headers={
            "Origin": "https://unapproved.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-origin" not in denied.headers


def test_environment_configuration_and_unsafe_cors_rejection() -> None:
    settings = Settings.from_env(
        {
            "SOLANA_RISK_ENVIRONMENT": "test",
            "SOLANA_RISK_CORS_ORIGINS": "https://example.test,http://localhost:5173",
            "SOLANA_RISK_MAX_EVENTS": "25",
            "SOLANA_RISK_MAX_REQUEST_BYTES": "4096",
        }
    )
    assert settings.environment == "test"
    assert settings.cors_origins == ("https://example.test", "http://localhost:5173")
    assert settings.max_events == 25
    assert settings.max_request_bytes == 4096
    with pytest.raises(ConfigurationError, match="Wildcard"):
        Settings(cors_origins=("*",))


def test_startup_and_requests_never_load_or_fit_models(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*_: Any, **__: Any) -> None:
        raise AssertionError("Model loading or fitting must not occur in Phase 5A")

    monkeypatch.setattr(joblib, "load", forbidden)
    monkeypatch.setattr(IsolationForest, "fit", forbidden)
    monkeypatch.setattr(LocalOutlierFactor, "fit", forbidden)
    monkeypatch.setattr(RobustMADDetector, "fit", forbidden)
    guarded_app = create_app(Settings())
    assert _request(guarded_app, "GET", "/healthz").status_code == 200
    assert _request(guarded_app, "GET", "/readyz").status_code == 503
    assert _request(
        guarded_app,
        "POST",
        "/v1/features/preview",
        json=_payload(_event(1)),
    ).status_code == 200


def test_openapi_documents_health_features_and_unavailable_scoring(app: Any) -> None:
    response = _request(app, "GET", "/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert {"/healthz", "/readyz", "/v1/features/preview", "/v1/score"}.issubset(
        schema["paths"]
    )
    assert "model scoring is unavailable" in schema["info"]["description"].casefold()
