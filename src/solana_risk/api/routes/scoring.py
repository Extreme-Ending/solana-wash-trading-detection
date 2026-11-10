"""Stable unavailable-scoring interface; no model loading occurs here."""

from __future__ import annotations

from fastapi import APIRouter

from solana_risk.api.errors import ApiError
from solana_risk.api.schemas import ErrorResponse, ScoreRequest

router = APIRouter(prefix="/v1", tags=["scoring"])


@router.post(
    "/score",
    response_model=None,
    responses={503: {"model": ErrorResponse}},
    summary="Unavailable wallet scoring",
    description=(
        "Reserved future interface. Phase 5A does not load experimental artifacts or return "
        "anomaly, fraud or wash-trading scores."
    ),
)
async def score(_: ScoreRequest) -> None:
    raise ApiError(
        status_code=503,
        code="MODEL_NOT_APPROVED",
        message="Prediction capability is unavailable.",
        details={"prediction_available": False},
    )
