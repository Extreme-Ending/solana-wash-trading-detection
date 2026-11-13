"""Descriptive point-in-time feature preview endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from solana_risk.api.auth import require_authorized_user
from solana_risk.api.errors import ApiError
from solana_risk.api.feature_service import build_feature_preview
from solana_risk.api.schemas import (
    ErrorResponse,
    FeaturePreviewRequest,
    FeaturePreviewResponse,
)

router = APIRouter(prefix="/v1/features", tags=["descriptive features"])


@router.post(
    "/preview",
    response_model=FeaturePreviewResponse,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
    summary="Preview descriptive wallet features",
    description=(
        "Builds the registered wallet snapshot from user-supplied, unverified events using "
        "only block_time < as_of. No model is loaded or trained."
    ),
)
async def preview_features(
    payload: FeaturePreviewRequest,
    request: Request,
    authorized_user: dict = Depends(require_authorized_user),
) -> FeaturePreviewResponse:
    del authorized_user
    settings = request.app.state.settings
    if len(payload.events) > settings.max_events:
        raise ApiError(
            status_code=413,
            code="EVENT_LIMIT_EXCEEDED",
            message="Event count exceeds the configured request limit.",
            details={"max_events": settings.max_events},
        )
    return build_feature_preview(payload)
