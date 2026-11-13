"""Firebase ID-token verification and server-side authorization policy."""

from __future__ import annotations

import time
from collections.abc import Mapping
from typing import Any, Protocol

import firebase_admin
from fastapi import Request
from fastapi.security import HTTPBearer
from firebase_admin import auth, credentials, exceptions

from solana_risk.api.errors import ApiError


class TokenVerifier(Protocol):
    """Narrow verifier interface used by the API and deterministic unit tests."""

    def verify(self, token: str) -> Mapping[str, Any]: ...


class TokenInvalidError(Exception):
    """Raised when a submitted credential cannot be authenticated."""


class TokenExpiredError(TokenInvalidError):
    """Raised when a submitted credential has expired."""


class TokenVerificationUnavailableError(Exception):
    """Raised when trusted verification infrastructure is unavailable."""


class FirebaseTokenVerifier:
    """Verify Firebase ID tokens with ADC and a fixed Firebase project identity."""

    def __init__(self, project_id: str) -> None:
        app_name = f"solana-risk-{project_id}"
        try:
            self._app = firebase_admin.get_app(app_name)
        except ValueError:
            self._app = firebase_admin.initialize_app(
                credentials.ApplicationDefault(),
                {"projectId": project_id},
                name=app_name,
            )

    def verify(self, token: str) -> Mapping[str, Any]:
        try:
            return auth.verify_id_token(token, app=self._app, check_revoked=False)
        except auth.ExpiredIdTokenError as exc:
            raise TokenExpiredError from exc
        except (
            auth.InvalidIdTokenError,
            auth.RevokedIdTokenError,
            auth.UserDisabledError,
        ) as exc:
            raise TokenInvalidError from exc
        except (auth.CertificateFetchError, exceptions.FirebaseError, ValueError) as exc:
            raise TokenVerificationUnavailableError from exc


_bearer = HTTPBearer(auto_error=False)


def _unauthenticated(code: str, message: str) -> ApiError:
    return ApiError(
        status_code=401,
        code=code,
        message=message,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def require_authorized_user(
    request: Request,
) -> Mapping[str, Any]:
    """Authenticate a Firebase user, then enforce the email and UID policies."""

    credential = await _bearer(request)
    if credential is None or credential.scheme.lower() != "bearer":
        raise _unauthenticated(
            "AUTHENTICATION_REQUIRED",
            "A Firebase Bearer token is required.",
        )
    if not credential.credentials.strip():
        raise _unauthenticated("INVALID_TOKEN", "The authentication token is invalid.")

    settings = request.app.state.settings
    verifier: TokenVerifier | None = request.app.state.token_verifier
    if not settings.authentication_configured or verifier is None:
        raise ApiError(
            status_code=503,
            code="AUTH_CONFIGURATION_UNAVAILABLE",
            message="Authentication is not configured for this service.",
        )

    try:
        claims = verifier.verify(credential.credentials)
    except TokenExpiredError:
        raise _unauthenticated("TOKEN_EXPIRED", "The authentication token has expired.")
    except TokenInvalidError:
        raise _unauthenticated("INVALID_TOKEN", "The authentication token is invalid.")
    except TokenVerificationUnavailableError:
        raise ApiError(
            status_code=503,
            code="AUTH_VERIFICATION_UNAVAILABLE",
            message="Authentication verification is temporarily unavailable.",
        )

    project_id = settings.firebase_project_id
    expected_issuer = f"https://securetoken.google.com/{project_id}"
    uid = claims.get("uid")
    subject = claims.get("sub")
    expiration = claims.get("exp")
    if (
        claims.get("aud") != project_id
        or claims.get("iss") != expected_issuer
        or not isinstance(uid, str)
        or not uid
        or subject != uid
        or not isinstance(expiration, (int, float))
        or expiration <= time.time()
    ):
        raise _unauthenticated("INVALID_TOKEN", "The authentication token is invalid.")

    email = claims.get("email")
    if not isinstance(email, str) or not email or claims.get("email_verified") is not True:
        raise ApiError(
            status_code=403,
            code="VERIFIED_EMAIL_REQUIRED",
            message="A verified Google account email is required.",
        )
    firebase_claims = claims.get("firebase")
    provider = (
        firebase_claims.get("sign_in_provider")
        if isinstance(firebase_claims, Mapping)
        else None
    )
    if provider != "google.com":
        raise ApiError(
            status_code=403,
            code="GOOGLE_SIGN_IN_REQUIRED",
            message="Google sign-in is required.",
        )
    if uid not in settings.allowed_user_uids:
        raise ApiError(
            status_code=403,
            code="USER_NOT_ALLOWED",
            message="This account is not authorized to use the protected API.",
        )
    return claims
