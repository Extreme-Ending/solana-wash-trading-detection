"""Thin serve-time adapter around the single Phase 3 feature implementation."""

from __future__ import annotations

from typing import Any

import pandas as pd

from solana_risk.api.errors import ApiError
from solana_risk.api.schemas import FeaturePreviewRequest, FeaturePreviewResponse
from solana_risk.features.build import (
    FEATURE_RULES_VERSION,
    MODEL_FEATURE_COLUMNS,
    FeatureValidationError,
    build_wallet_snapshots,
    feature_registry_sha256,
)


def _python_value(value: Any) -> int | float | bool | None:
    if value is None or value is pd.NA or pd.isna(value):
        return None
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, (bool, int, float)):
        return value
    raise ApiError(
        status_code=500,
        code="FEATURE_OUTPUT_INVALID",
        message="The shared feature builder returned an unsupported value.",
    )


def build_feature_preview(payload: FeaturePreviewRequest) -> FeaturePreviewResponse:
    """Build one descriptive snapshot without training or scoring any model."""

    event_records = [event.model_dump() for event in payload.events]
    historical_count = sum(event.block_time < payload.as_of for event in payload.events)
    if historical_count == 0:
        raise ApiError(
            status_code=422,
            code="INSUFFICIENT_HISTORY",
            message="At least one event must occur strictly before as_of.",
            details={"required_temporal_rule": "block_time < as_of"},
        )
    try:
        snapshots = build_wallet_snapshots(pd.DataFrame(event_records), [payload.as_of])
    except FeatureValidationError as exc:
        raise ApiError(
            status_code=422,
            code="FEATURE_INPUT_INVALID",
            message="Events are incompatible with the shared feature contract.",
            details={"reason": str(exc)},
        ) from exc
    if len(snapshots) != 1:
        raise ApiError(
            status_code=500,
            code="FEATURE_OUTPUT_INVALID",
            message="The shared feature builder did not return exactly one wallet snapshot.",
        )
    row = snapshots.iloc[0]
    features = {name: _python_value(row[name]) for name in MODEL_FEATURE_COLUMNS}
    return FeaturePreviewResponse(
        status="descriptive_features",
        source="user_supplied_unverified_events",
        interpretation=(
            "Descriptive point-in-time features only; they do not establish wash trading, "
            "fraud, intent or misconduct."
        ),
        wallet=str(row["wallet"]),
        as_of=payload.as_of,
        supplied_event_count=len(payload.events),
        included_historical_event_count=historical_count,
        excluded_at_or_after_cutoff_count=len(payload.events) - historical_count,
        feature_rules_version=FEATURE_RULES_VERSION,
        feature_registry_sha256=feature_registry_sha256(),
        feature_order=list(MODEL_FEATURE_COLUMNS),
        features=features,
    )
