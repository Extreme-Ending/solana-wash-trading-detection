"""Typed request and response contracts for the Phase 5A API."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SYNTHETIC_EVENT_EXAMPLE = {
    "source_row_number": 1,
    "wallet": "synthetic-wallet-001",
    "block_time": "2025-01-15T12:00:00Z",
    "block_slot": 1001,
    "tx_hash": "synthetic-transaction-001",
    "dex": "synthetic-dex",
    "token_pair": "TOKEN-A/TOKEN-B",
    "token_in": "synthetic-token-a",
    "token_out": "synthetic-token-b",
    "amount_usd": 125.5,
    "fee_usd": 0.25,
    "outer_instruction_index": 1,
    "inner_instruction_index": 0,
}


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _safe_text(value: str, *, field_name: str, maximum: int) -> str:
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be nonempty without surrounding whitespace")
    if len(value) > maximum:
        raise ValueError(f"{field_name} must contain at most {maximum} characters")
    if not value.isprintable():
        raise ValueError(f"{field_name} must not contain control characters")
    return value


def _explicit_utc(value: Any, *, field_name: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be an explicit ISO-8601 UTC string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} must include an explicit UTC offset")
    if parsed.utcoffset() != timedelta(0):
        raise ValueError(f"{field_name} must use UTC (Z or +00:00)")
    return parsed.astimezone(timezone.utc)


class EventInput(ApiModel):
    """One user-supplied, unverified event compatible with the Phase 3 builder."""

    source_row_number: int = Field(strict=True, ge=1)
    wallet: str
    block_time: datetime
    block_slot: int = Field(strict=True, ge=0)
    tx_hash: str
    dex: str
    token_pair: str | None
    token_in: str
    token_out: str
    amount_usd: float = Field(strict=True, gt=0, allow_inf_nan=False)
    fee_usd: float | None = Field(default=None, strict=True, ge=0, allow_inf_nan=False)
    outer_instruction_index: int | None = Field(default=None, strict=True, ge=0)
    inner_instruction_index: int | None = Field(default=None, strict=True, ge=0)

    @field_validator("block_time", mode="before")
    @classmethod
    def validate_block_time(cls, value: Any) -> datetime:
        return _explicit_utc(value, field_name="block_time")

    @field_validator("wallet")
    @classmethod
    def validate_wallet(cls, value: str) -> str:
        return _safe_text(value, field_name="wallet", maximum=128)

    @field_validator("tx_hash")
    @classmethod
    def validate_tx_hash(cls, value: str) -> str:
        return _safe_text(value, field_name="tx_hash", maximum=256)

    @field_validator("dex", "token_in", "token_out")
    @classmethod
    def validate_short_identifier(cls, value: str, info: Any) -> str:
        return _safe_text(value, field_name=info.field_name, maximum=128)

    @field_validator("token_pair")
    @classmethod
    def validate_token_pair(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _safe_text(value, field_name="token_pair", maximum=256)


class FeaturePreviewRequest(ApiModel):
    """User-supplied history for one wallet at one explicit UTC cutoff."""

    as_of: datetime
    events: list[EventInput] = Field(min_length=1)

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "as_of": "2025-02-01T00:00:00Z",
                "events": [SYNTHETIC_EVENT_EXAMPLE],
            }
        },
    )

    @field_validator("as_of", mode="before")
    @classmethod
    def validate_as_of(cls, value: Any) -> datetime:
        return _explicit_utc(value, field_name="as_of")

    @model_validator(mode="after")
    def validate_request_identity(self) -> "FeaturePreviewRequest":
        wallets = {event.wallet for event in self.events}
        if len(wallets) != 1:
            raise ValueError("events must describe exactly one wallet per request")
        row_numbers = [event.source_row_number for event in self.events]
        if len(row_numbers) != len(set(row_numbers)):
            raise ValueError("source_row_number values must be unique within a request")
        return self


class ScoreRequest(FeaturePreviewRequest):
    """Reserved future scoring input; Phase 5A never produces a score."""


FeatureValue = int | float | bool | None


class FeaturePreviewResponse(ApiModel):
    status: Literal["descriptive_features"]
    source: Literal["user_supplied_unverified_events"]
    interpretation: str
    wallet: str
    as_of: datetime
    supplied_event_count: int
    included_historical_event_count: int
    excluded_at_or_after_cutoff_count: int
    feature_rules_version: str
    feature_registry_sha256: str
    feature_order: list[str]
    features: dict[str, FeatureValue]


class HealthResponse(ApiModel):
    status: Literal["ok"]
    service: str
    version: str


class ErrorDetail(ApiModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(ApiModel):
    error: ErrorDetail
