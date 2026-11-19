"""Process-health and prediction-readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

from solana_risk.api.errors import ApiError
from solana_risk.api.schemas import (
    ErrorResponse,
    ExperimentalReadinessResponse,
    HealthResponse,
)

router = APIRouter(tags=["service status"])


@router.get(
    "/healthz",
    response_model=HealthResponse,
    summary="Process health",
    description="Reports that the API process is running; it makes no model-readiness claim.",
)
@router.get(
    "/v1/health",
    response_model=HealthResponse,
    summary="Application health",
    description="Hosted-browser health alias; it makes no model-readiness claim.",
)
async def healthz(request: Request) -> HealthResponse:
    settings = request.app.state.settings
    return HealthResponse(status="ok", service=settings.service_name, version=settings.api_version)


@router.get(
    "/readyz",
    response_model=ExperimentalReadinessResponse,
    responses={503: {"model": ErrorResponse}},
    summary="Experimental scoring readiness",
    description=(
        "Reports whether checksum-verified experimental anomaly scoring is available. "
        "Availability does not imply a fraud prediction capability."
    ),
)
async def readyz(request: Request) -> ExperimentalReadinessResponse:
    settings = request.app.state.settings
    if request.app.state.experimental_scoring_available:
        return ExperimentalReadinessResponse(
            status="ready",
            available=True,
            capability="experimental_anomaly_scoring",
            methodology_status="experimental_unsupervised_research_only",
            is_probability=False,
            message="Experimental unsupervised anomaly scoring is available.",
        )
    if settings.experimental_scoring_allowed:
        raise ApiError(
            status_code=503,
            code="EXPERIMENTAL_MODEL_UNAVAILABLE",
            message="The experimental model is unavailable or failed integrity validation.",
            details={"experimental_scoring_available": False},
        )
    raise ApiError(
        status_code=503,
        code="MODEL_NOT_APPROVED",
        message="Prediction capability is unavailable.",
        details={"prediction_available": False},
    )
