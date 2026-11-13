"""Firebase authentication and server-side authorization contracts."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Mapping
from typing import Any

import httpx
import pytest
from firebase_admin import auth as firebase_auth

from solana_risk.api.auth import (
    FirebaseTokenVerifier,
    TokenExpiredError,
    TokenInvalidError,
    TokenVerificationUnavailableError,
)
from solana_risk.api.config import ConfigurationError, Settings
from solana_risk.api.main import create_app

PROJECT_ID = "test-project-123"
APPROVED_UID = "approved-test-uid"


def _claims(**overrides: Any) -> dict[str, Any]:
    claims: dict[str, Any] = {
        "aud": PROJECT_ID,
        "iss": f"https://securetoken.google.com/{PROJECT_ID}",
        "sub": APPROVED_UID,
        "uid": APPROVED_UID,
        "exp": time.time() + 3_600,
        "email": "approved@example.test",
        "email_verified": True,
        "firebase": {"sign_in_provider": "google.com"},
    }
    claims.update(overrides)
    return claims


class _Verifier:
    def __init__(self, outcome: Mapping[str, Any] | Exception) -> None:
        self.outcome = outcome

    def verify(self, _: str) -> Mapping[str, Any]:
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


def _app(outcome: Mapping[str, Any] | Exception, **settings: Any) -> Any:
    values = {
        "firebase_project_id": PROJECT_ID,
        "allowed_user_uids": frozenset({APPROVED_UID}),
    }
    values.update(settings)
    return create_app(Settings(**values), token_verifier=_Verifier(outcome))


def _request(app: Any, path: str, token: str | None = "submitted-token") -> httpx.Response:
    async def run() -> httpx.Response:
        headers = {"Authorization": f"Bearer {token}"} if token is not None else {}
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=True)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post(path, headers=headers, json={
                "as_of": "2025-02-01T00:00:00Z",
                "events": [{
                    "source_row_number": 1,
                    "wallet": "synthetic-wallet",
                    "block_time": "2025-01-01T00:00:00Z",
                    "block_slot": 1,
                    "tx_hash": "synthetic-transaction",
                    "dex": "synthetic-dex",
                    "token_pair": "A/B",
                    "token_in": "A",
                    "token_out": "B",
                    "amount_usd": 1.0,
                    "fee_usd": None,
                    "outer_instruction_index": 0,
                    "inner_instruction_index": 0,
                }],
            })

    return asyncio.run(run())


@pytest.mark.parametrize(
    ("outcome", "expected_code"),
    [
        (TokenInvalidError(), "INVALID_TOKEN"),
        (TokenExpiredError(), "TOKEN_EXPIRED"),
        (_claims(aud="different-project"), "INVALID_TOKEN"),
        (_claims(iss="https://securetoken.google.com/different-project"), "INVALID_TOKEN"),
        (_claims(exp=1), "INVALID_TOKEN"),
    ],
)
def test_invalid_expired_and_wrong_project_tokens_return_401(
    outcome: Mapping[str, Any] | Exception,
    expected_code: str,
) -> None:
    response = _request(_app(outcome), "/v1/features/preview")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == expected_code
    assert response.headers["www-authenticate"] == "Bearer"


def test_missing_token_returns_401_without_invoking_protected_logic() -> None:
    response = _request(_app(_claims()), "/v1/features/preview", token=None)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.parametrize(
    ("claims", "expected_code"),
    [
        (_claims(email_verified=False), "VERIFIED_EMAIL_REQUIRED"),
        (_claims(firebase={"sign_in_provider": "password"}), "GOOGLE_SIGN_IN_REQUIRED"),
        (
            _claims(uid="unapproved-uid", sub="unapproved-uid"),
            "USER_NOT_ALLOWED",
        ),
    ],
)
def test_authenticated_but_unauthorized_users_return_403(
    claims: Mapping[str, Any],
    expected_code: str,
) -> None:
    response = _request(_app(claims), "/v1/features/preview")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == expected_code


def test_valid_authorized_user_can_preview_features() -> None:
    response = _request(_app(_claims()), "/v1/features/preview")
    assert response.status_code == 200
    assert response.json()["status"] == "descriptive_features"


def test_authorized_scoring_still_returns_model_not_approved() -> None:
    response = _request(_app(_claims()), "/v1/score")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "MODEL_NOT_APPROVED"


def test_verification_infrastructure_failure_returns_safe_503() -> None:
    response = _request(
        _app(TokenVerificationUnavailableError()),
        "/v1/features/preview",
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "AUTH_VERIFICATION_UNAVAILABLE"


def test_unconfigured_development_service_fails_closed_on_protected_endpoint() -> None:
    response = _request(create_app(Settings()), "/v1/features/preview")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "AUTH_CONFIGURATION_UNAVAILABLE"


def test_production_requires_project_and_uid_allowlist() -> None:
    with pytest.raises(ConfigurationError, match="FIREBASE_PROJECT_ID"):
        Settings(environment="production")
    with pytest.raises(ConfigurationError, match="ALLOWED_UIDS"):
        Settings(environment="production", firebase_project_id=PROJECT_ID)


def test_health_and_readiness_remain_public() -> None:
    app = create_app(Settings())
    async def run() -> tuple[httpx.Response, httpx.Response]:
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=True)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/healthz"), await client.get("/readyz")
    health, readiness = asyncio.run(run())
    assert health.status_code == 200
    assert readiness.status_code == 503
    assert readiness.json()["error"]["code"] == "MODEL_NOT_APPROVED"


def test_firebase_verifier_delegates_signature_and_claim_checks_to_admin_sdk(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    verifier = FirebaseTokenVerifier.__new__(FirebaseTokenVerifier)
    verifier._app = object()  # type: ignore[attr-defined]
    monkeypatch.setattr(
        firebase_auth,
        "verify_id_token",
        lambda token, *, app, check_revoked: {
            "token": token,
            "same_app": app is verifier._app,  # type: ignore[attr-defined]
            "check_revoked": check_revoked,
        },
    )
    assert verifier.verify("signed-token") == {
        "token": "signed-token",
        "same_app": True,
        "check_revoked": False,
    }
