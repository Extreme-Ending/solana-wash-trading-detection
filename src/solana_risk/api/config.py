"""Environment-backed, non-secret configuration for the API foundation."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import urlsplit


class ConfigurationError(ValueError):
    """Raised when service configuration is unsafe or malformed."""


def _parse_positive_int(
    value: str,
    *,
    name: str,
    maximum: int,
) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be a positive integer") from exc
    if not 1 <= parsed <= maximum:
        raise ConfigurationError(f"{name} must be between 1 and {maximum}")
    return parsed


def _validate_origin(origin: str) -> str:
    if origin == "*":
        raise ConfigurationError("Wildcard CORS origins are not permitted")
    parsed = urlsplit(origin)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ConfigurationError(f"Invalid CORS origin: {origin!r}")
    if (
        parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise ConfigurationError(
            f"CORS origins must contain only scheme, host and optional port: {origin!r}"
        )
    return f"{parsed.scheme}://{parsed.netloc}"


@dataclass(frozen=True)
class Settings:
    """Validated service settings with conservative local defaults."""

    service_name: str = "Solana Wallet Feature Service"
    api_version: str = "0.1.0"
    environment: str = "development"
    cors_origins: tuple[str, ...] = ("http://localhost:5173",)
    max_events: int = 100
    max_request_bytes: int = 262_144

    def __post_init__(self) -> None:
        if not self.service_name.strip() or not self.api_version.strip():
            raise ConfigurationError("service_name and api_version must be nonempty")
        if not self.environment.strip():
            raise ConfigurationError("environment must be nonempty")
        if not 1 <= self.max_events <= 10_000:
            raise ConfigurationError("max_events must be between 1 and 10000")
        if not 1 <= self.max_request_bytes <= 10_485_760:
            raise ConfigurationError("max_request_bytes must be between 1 and 10485760")
        if not self.cors_origins:
            raise ConfigurationError("At least one explicit CORS origin is required")
        normalized = tuple(_validate_origin(origin) for origin in self.cors_origins)
        if len(set(normalized)) != len(normalized):
            raise ConfigurationError("CORS origins must be unique")
        object.__setattr__(self, "cors_origins", normalized)

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "Settings":
        """Load validated settings from a supplied mapping or process environment."""

        values = os.environ if environ is None else environ
        origins_text = values.get("SOLANA_RISK_CORS_ORIGINS", "http://localhost:5173")
        origins = tuple(item.strip() for item in origins_text.split(",") if item.strip())
        return cls(
            environment=values.get("SOLANA_RISK_ENVIRONMENT", "development"),
            cors_origins=origins,
            max_events=_parse_positive_int(
                values.get("SOLANA_RISK_MAX_EVENTS", "100"),
                name="SOLANA_RISK_MAX_EVENTS",
                maximum=10_000,
            ),
            max_request_bytes=_parse_positive_int(
                values.get("SOLANA_RISK_MAX_REQUEST_BYTES", "262144"),
                name="SOLANA_RISK_MAX_REQUEST_BYTES",
                maximum=10_485_760,
            ),
        )
