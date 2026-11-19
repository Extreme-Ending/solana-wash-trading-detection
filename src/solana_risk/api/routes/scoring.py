"""Protected, explicitly gated experimental anomaly-scoring interface."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from solana_risk.api.auth import require_authorized_user
from solana_risk.api.errors import ApiError
from solana_risk.api.schemas import (
    BatchScoreRequest,
    ErrorResponse,
    ExperimentalBatchScoreResponse,
    ExperimentalScoreResponse,
    ScoreRequest,
)

router = APIRouter(prefix="/v1", tags=["scoring"])


def _experimental_scorer(request: Request):
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
            message="The experimental model is unavailable or failed validation.",
            details={"experimental_scoring_available": False},
        )
    return scorer


@router.post(
    "/score",
    response_model=ExperimentalScoreResponse,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
    summary="Experimental wallet anomaly scoring",
    description=(
        "Returns a model-specific, non-probabilistic anomaly score only when a checksum-pinned "
        "Phase 4B artifact is explicitly enabled and passes integrity validation. This is "
        "unsupervised research output, not a fraud prediction."
    ),
)
async def score(
    payload: ScoreRequest,
    request: Request,
    authorized_user: dict = Depends(require_authorized_user),
) -> ExperimentalScoreResponse:
    del authorized_user
    scorer = _experimental_scorer(request)
    try:
        return scorer.score(payload)
    except ApiError:
        raise
    except Exception as exc:
        raise ApiError(
            status_code=503,
            code="EXPERIMENTAL_SCORING_FAILED",
            message="The experimental scorer could not produce a valid result.",
            details={"experimental_scoring_available": False},
        ) from exc


@router.post(
    "/score/batch",
    response_model=ExperimentalBatchScoreResponse,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
    summary="Experimental multi-wallet anomaly ranking",
    description=(
        "Scores bounded, explicitly separated wallet histories with the already-loaded local "
        "Isolation Forest and ranks them within only the submitted batch. Rankings are not "
        "fraud probabilities or confirmed outcomes."
    ),
)
async def score_batch(
    payload: BatchScoreRequest,
    request: Request,
    authorized_user: dict = Depends(require_authorized_user),
) -> ExperimentalBatchScoreResponse:
    del authorized_user
    scorer = _experimental_scorer(request)
    settings = request.app.state.settings
    try:
        return scorer.score_batch(
            payload,
            max_wallets=settings.max_batch_wallets,
            max_events=settings.max_batch_events,
            max_events_per_wallet=settings.max_batch_events_per_wallet,
        )
    except ApiError:
        raise
    except Exception as exc:
        raise ApiError(
            status_code=503,
            code="EXPERIMENTAL_SCORING_FAILED",
            message="The experimental scorer could not produce a valid batch result.",
            details={"experimental_scoring_available": False},
        ) from exc
