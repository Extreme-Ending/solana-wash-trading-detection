"""Process-health and prediction-readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

from solana_risk.api.errors import ApiError
from solana_risk.api.schemas import ErrorResponse, HealthResponse

router = APIRouter(tags=["service status"])


@router.get(
    "/healthz",
    response_model=HealthResponse,
    summary="Process health",
    description="Reports that the API process is running; it makes no model-readiness claim.",
)
async def healthz(request: Request) -> HealthResponse:
    settings = request.app.state.settings
    return HealthResponse(status="ok", service=settings.service_name, version=settings.api_version)


@router.get(
    "/readyz",
    response_model=None,
    responses={503: {"model": ErrorResponse}},
    summary="Prediction readiness",
    description="Returns 503 while an approved prediction capability is unavailable.",
)
async def readyz() -> None:
    raise ApiError(
        status_code=503,
        code="MODEL_NOT_APPROVED",
        message="Prediction capability is unavailable.",
        details={"prediction_available": False},
    )
