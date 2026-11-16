"""Protected, development-gated experimental anomaly-scoring interface."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from solana_risk.api.auth import require_authorized_user
from solana_risk.api.errors import ApiError
from solana_risk.api.schemas import ErrorResponse, ExperimentalScoreResponse, ScoreRequest

router = APIRouter(prefix="/v1", tags=["scoring"])


@router.post(
    "/score",
    response_model=ExperimentalScoreResponse,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
    summary="Development-gated experimental wallet anomaly scoring",
    description=(
        "Returns a model-specific, non-probabilistic anomaly score only when a checksum-pinned "
        "Phase 4B artifact is explicitly enabled in local development. Production remains "
        "unavailable."
    ),
)
async def score(
    payload: ScoreRequest,
    request: Request,
    authorized_user: dict = Depends(require_authorized_user),
) -> ExperimentalScoreResponse:
    del authorized_user
    settings = request.app.state.settings
    if not settings.experimental_scoring_allowed:
        raise ApiError(
            status_code=503,
            code="MODEL_NOT_APPROVED",
            message="Prediction capability is unavailable.",
            details={"prediction_available": False},
        )
    scorer = request.app.state.experimental_scorer
    if scorer is None:
        raise ApiError(
            status_code=503,
            code="EXPERIMENTAL_MODEL_UNAVAILABLE",
            message="The local experimental model is unavailable or failed validation.",
            details={"experimental_scoring_available": False},
        )
    try:
        return scorer.score(payload)
    except ApiError:
        raise
    except Exception as exc:
        raise ApiError(
            status_code=503,
            code="EXPERIMENTAL_SCORING_FAILED",
            message="The local experimental scorer could not produce a valid result.",
            details={"experimental_scoring_available": False},
        ) from exc
