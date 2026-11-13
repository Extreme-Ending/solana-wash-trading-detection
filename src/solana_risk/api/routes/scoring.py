"""Stable unavailable-scoring interface; no model loading occurs here."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from solana_risk.api.auth import require_authorized_user
from solana_risk.api.errors import ApiError
from solana_risk.api.schemas import ErrorResponse, ScoreRequest

router = APIRouter(prefix="/v1", tags=["scoring"])


@router.post(
    "/score",
    response_model=None,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
    summary="Unavailable wallet scoring",
    description=(
        "Reserved future interface. Phase 5A does not load experimental artifacts or return "
        "anomaly, fraud or wash-trading scores."
    ),
)
async def score(
    payload: ScoreRequest,
    authorized_user: dict = Depends(require_authorized_user),
) -> None:
    del payload, authorized_user
    raise ApiError(
        status_code=503,
        code="MODEL_NOT_APPROVED",
        message="Prediction capability is unavailable.",
        details={"prediction_available": False},
    )
