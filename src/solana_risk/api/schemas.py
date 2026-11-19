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
    """One-wallet history for explicitly enabled experimental scoring."""


class BatchWalletHistory(ApiModel):
    """One explicitly separated wallet history within a batch request."""

    wallet: str
    events: list[EventInput] = Field(default_factory=list)

    @field_validator("wallet")
    @classmethod
    def validate_wallet(cls, value: str) -> str:
        return _safe_text(value, field_name="wallet", maximum=128)


class BatchScoreRequest(ApiModel):
    """Bounded multi-wallet histories sharing one explicit UTC decision time."""

    as_of: datetime
    wallet_histories: list[BatchWalletHistory] = Field(min_length=1)
    review_budget: int | None = Field(default=None, strict=True, ge=1)

    @field_validator("as_of", mode="before")
    @classmethod
    def validate_as_of(cls, value: Any) -> datetime:
        return _explicit_utc(value, field_name="as_of")

    @model_validator(mode="after")
    def validate_unique_wallet_groups(self) -> "BatchScoreRequest":
        wallets = [history.wallet for history in self.wallet_histories]
        if len(wallets) != len(set(wallets)):
            raise ValueError("wallet_histories must contain each wallet exactly once")
        return self


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


class ExperimentalScoreResponse(ApiModel):
    status: Literal["experimental_anomaly_score"]
    methodology_status: Literal["experimental_unsupervised_research_only"]
    source: Literal["user_supplied_unverified_events"]
    wallet: str
    as_of: datetime
    supplied_event_count: int
    included_historical_event_count: int
    excluded_at_or_after_cutoff_count: int
    model_id: Literal["isolation_forest"]
    model_version: str
    anomaly_score: float = Field(allow_inf_nan=False)
    score_direction: Literal["higher_means_more_anomalous_relative_to_training_reference"]
    score_units: Literal["model_specific_unitless_isolation_forest_score"]
    is_probability: Literal[False]
    training_cutoff: datetime
    feature_rules_version: str
    feature_registry_sha256: str
    observable_history_days: float = Field(ge=0, allow_inf_nan=False)
    warnings: list[str]
    interpretation: str


class FeatureReferenceStatistic(ApiModel):
    observed_count: int = Field(ge=1)
    missing_count: int = Field(ge=0)
    minimum: float = Field(allow_inf_nan=False)
    quartile_1: float = Field(allow_inf_nan=False)
    median: float = Field(allow_inf_nan=False)
    mean: float = Field(allow_inf_nan=False)
    quartile_3: float = Field(allow_inf_nan=False)
    maximum: float = Field(allow_inf_nan=False)
    is_binary: bool
    is_constant: bool


class FeatureTrainingReference(ApiModel):
    version: Literal["training_reference_v1"]
    source: Literal["phase_3_training_snapshots"]
    training_cutoff: datetime
    snapshot_sha256: str
    wallet_count: int = Field(ge=1)
    feature_registry_sha256: str
    feature_order: list[str]
    statistics: dict[str, FeatureReferenceStatistic]
    comparison_method: Literal[
        "robust_iqr_distance_for_nonbinary_nonconstant_features"
    ]


class BatchWalletScore(ApiModel):
    wallet: str
    anomaly_score: float = Field(allow_inf_nan=False)
    rank: int = Field(ge=1)
    selected_for_review: bool
    supplied_event_count: int = Field(ge=0)
    included_historical_event_count: int = Field(ge=1)
    excluded_at_or_after_cutoff_count: int = Field(ge=0)
    observable_history_days: float = Field(ge=0, allow_inf_nan=False)
    features: dict[str, FeatureValue]
    warnings: list[str]


class BatchWalletRejection(ApiModel):
    wallet: str
    code: Literal[
        "EMPTY_WALLET_HISTORY",
        "WALLET_EVENT_MISMATCH",
        "DUPLICATE_SOURCE_ROW",
        "DUPLICATE_EVENT_RECORD",
        "INSUFFICIENT_HISTORY",
        "FEATURE_INPUT_INVALID",
    ]
    message: str
    supplied_event_count: int = Field(ge=0)


class ExperimentalBatchScoreResponse(ApiModel):
    status: Literal["experimental_batch_anomaly_ranking"]
    methodology_status: Literal["experimental_unsupervised_research_only"]
    source: Literal["user_supplied_unverified_events"]
    model_id: Literal["isolation_forest"]
    model_version: str
    as_of: datetime
    training_cutoff: datetime
    score_direction: Literal["higher_means_more_anomalous_relative_to_training_reference"]
    score_units: Literal["model_specific_unitless_isolation_forest_score"]
    is_probability: Literal[False]
    feature_rules_version: str
    feature_registry_sha256: str
    feature_reference: FeatureTrainingReference
    wallets_submitted: int = Field(ge=1)
    wallets_scored: int = Field(ge=1)
    wallets_rejected: int = Field(ge=0)
    review_budget_requested: int | None = Field(default=None, ge=1)
    review_budget: int = Field(ge=0)
    review_candidates: list[str]
    ranked_wallets: list[BatchWalletScore]
    rejected_wallets: list[BatchWalletRejection]
    warnings: list[str]
    interpretation: Literal[
        "Experimental statistical anomalies requiring review; not confirmed wash trading or fraud."
    ]


class HealthResponse(ApiModel):
    status: Literal["ok"]
    service: str
    version: str


class ExperimentalReadinessResponse(ApiModel):
    status: Literal["ready"]
    available: Literal[True]
    capability: Literal["experimental_anomaly_scoring"]
    methodology_status: Literal["experimental_unsupervised_research_only"]
    is_probability: Literal[False]
    message: str


class ErrorDetail(ApiModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(ApiModel):
    error: ErrorDetail
