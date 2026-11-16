"""Fail-closed loading and serving of the local Phase 4B Isolation Forest."""

from __future__ import annotations

import hashlib
import hmac
import io
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline

from solana_risk.api.errors import ApiError
from solana_risk.api.feature_service import build_feature_preview
from solana_risk.api.schemas import (
    BatchScoreRequest,
    BatchWalletRejection,
    BatchWalletScore,
    ExperimentalBatchScoreResponse,
    ExperimentalScoreResponse,
    FeaturePreviewResponse,
    ScoreRequest,
)
from solana_risk.features.build import (
    FEATURE_RULES_VERSION,
    MODEL_FEATURE_COLUMNS,
    feature_registry_sha256,
)
from solana_risk.models.train_anomaly import (
    EXPERIMENT_STATUS,
    EXPERIMENT_VERSION,
    MODEL_NAMES,
)


class ExperimentalArtifactError(ValueError):
    """Raised when an experimental artifact is missing, untrusted, or incompatible."""


def _mapping(value: Any, *, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ExperimentalArtifactError(f"{name} must be a mapping")
    return value


def _same(left: Any, right: Any, *, name: str) -> None:
    if left != right:
        raise ExperimentalArtifactError(f"{name} does not match the trusted contract")


def _regular_local_file(path: Path | None, *, name: str) -> Path:
    if path is None:
        raise ExperimentalArtifactError(f"{name} is not configured")
    candidate = path.expanduser()
    if candidate.is_symlink() or not candidate.is_file():
        raise ExperimentalArtifactError(f"{name} must be an existing regular non-symlink file")
    return candidate.resolve()


def _load_manifest(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExperimentalArtifactError("The experimental manifest is unreadable") from exc
    return _mapping(value, name="manifest")


def _validate_runtime_versions(manifest: Mapping[str, Any]) -> None:
    versions = _mapping(manifest.get("versions"), name="manifest versions")
    runtime = {
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scikit_learn": sklearn.__version__,
        "joblib": joblib.__version__,
    }
    for package, version in runtime.items():
        _same(versions.get(package), version, name=f"{package} version")


class TrustedExperimentalScorer:
    """A checksum-pinned, metadata-validated local Isolation Forest scorer."""

    def __init__(
        self,
        *,
        model: Pipeline,
        model_version: str,
        training_cutoff: datetime,
    ) -> None:
        self._model = model
        self._model_version = model_version
        self._training_cutoff = training_cutoff

    @classmethod
    def load(
        cls,
        *,
        artifact_path: Path | None,
        manifest_path: Path | None,
        expected_sha256: str | None,
    ) -> "TrustedExperimentalScorer":
        artifact = _regular_local_file(artifact_path, name="experimental artifact")
        manifest_file = _regular_local_file(manifest_path, name="experimental manifest")
        if expected_sha256 is None:
            raise ExperimentalArtifactError("The expected artifact SHA-256 is not configured")

        manifest = _load_manifest(manifest_file)
        _same(manifest.get("artifact"), artifact.name, name="artifact filename")
        _same(manifest.get("artifact_sha256"), expected_sha256, name="manifest checksum")
        try:
            artifact_bytes = artifact.read_bytes()
        except OSError as exc:
            raise ExperimentalArtifactError("The experimental artifact is unreadable") from exc
        observed_sha256 = hashlib.sha256(artifact_bytes).hexdigest()
        if not hmac.compare_digest(observed_sha256, expected_sha256):
            raise ExperimentalArtifactError("The experimental artifact checksum does not match")
        _same(manifest.get("experiment_status"), EXPERIMENT_STATUS, name="experiment status")
        _same(manifest.get("experiment_version"), EXPERIMENT_VERSION, name="model version")
        _same(
            manifest.get("feature_rules_version"),
            FEATURE_RULES_VERSION,
            name="feature rules version",
        )
        _same(
            manifest.get("feature_registry_sha256"),
            feature_registry_sha256(),
            name="feature registry fingerprint",
        )
        _same(manifest.get("feature_order"), list(MODEL_FEATURE_COLUMNS), name="feature order")
        _validate_runtime_versions(manifest)

        try:
            bundle = joblib.load(io.BytesIO(artifact_bytes))
        except Exception as exc:  # joblib wraps pickle, import, and IO failures
            raise ExperimentalArtifactError("The verified experimental artifact is unreadable") from exc
        bundle_map = _mapping(bundle, name="artifact bundle")
        metadata = _mapping(bundle_map.get("metadata"), name="artifact metadata")
        models = _mapping(bundle_map.get("models"), name="artifact models")
        if set(models) != set(MODEL_NAMES):
            raise ExperimentalArtifactError("The artifact model set is incompatible")

        for field in (
            "experiment_status",
            "experiment_version",
            "feature_rules_version",
            "feature_registry_sha256",
            "feature_order",
            "versions",
        ):
            _same(metadata.get(field), manifest.get(field), name=f"artifact {field}")
        _same(metadata.get("labels_used"), False, name="label-use declaration")
        _same(metadata.get("is_probability"), False, name="probability declaration")

        split = _mapping(metadata.get("temporal_split"), name="temporal split")
        _same(split.get("train_cutoff"), manifest.get("training_cutoff"), name="training cutoff")
        try:
            training_cutoff = datetime.fromisoformat(
                str(split["train_cutoff"]).replace("Z", "+00:00")
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ExperimentalArtifactError("The training cutoff is invalid") from exc
        if training_cutoff.tzinfo is None or training_cutoff.utcoffset() is None:
            raise ExperimentalArtifactError("The training cutoff must be timezone-aware")

        model = models.get("isolation_forest")
        if not isinstance(model, Pipeline):
            raise ExperimentalArtifactError("The selected model is not a fitted pipeline")
        if list(model.named_steps) != ["imputer", "model"] or not isinstance(
            model.named_steps["model"], IsolationForest
        ):
            raise ExperimentalArtifactError("The selected Isolation Forest pipeline is incompatible")
        if getattr(model, "n_features_in_", None) != len(MODEL_FEATURE_COLUMNS):
            raise ExperimentalArtifactError("The selected model feature count is incompatible")
        feature_names = getattr(model, "feature_names_in_", None)
        if feature_names is not None and list(feature_names) != list(MODEL_FEATURE_COLUMNS):
            raise ExperimentalArtifactError("The fitted model feature names are incompatible")

        return cls(
            model=model,
            model_version=str(metadata["experiment_version"]),
            training_cutoff=training_cutoff,
        )

    def _validate_scoring_time(self, as_of: datetime) -> None:
        if as_of < self._training_cutoff:
            raise ApiError(
                status_code=422,
                code="SCORING_TIME_PRECEDES_MODEL_REFERENCE",
                message="as_of must not precede the model training reference cutoff.",
                details={"training_cutoff": self._training_cutoff.isoformat()},
            )

    def _score_previews(self, previews: list[FeaturePreviewResponse]) -> np.ndarray:
        matrix = pd.DataFrame(
            [preview.features for preview in previews],
            columns=MODEL_FEATURE_COLUMNS,
        ).astype(float)
        scores = -np.asarray(self._model.score_samples(matrix), dtype=float)
        if scores.shape != (len(previews),) or not np.isfinite(scores).all():
            raise ExperimentalArtifactError("The selected model produced an invalid score")
        return scores

    @staticmethod
    def _history_warnings(preview: FeaturePreviewResponse) -> list[str]:
        warnings = [
            "The submitted event history is user-supplied and may be incomplete or unverified."
        ]
        if bool(preview.features["single_event_history"]):
            warnings.append("Only one pre-cutoff event is observable; gap features are unavailable.")
        if bool(preview.features["insufficient_history_7d"]):
            warnings.append("Less than seven days of observable history are available.")
        if bool(preview.features["insufficient_history_30d"]):
            warnings.append("Less than 30 days of observable history are available.")
        if preview.excluded_at_or_after_cutoff_count:
            warnings.append(
                "Events at or after as_of were excluded by the point-in-time leakage rule."
            )
        return warnings

    @staticmethod
    def _observable_history_days(preview: FeaturePreviewResponse) -> float:
        observable_days = preview.features["observable_history_days"]
        if not isinstance(observable_days, (int, float)) or isinstance(observable_days, bool):
            raise ExperimentalArtifactError("Observable history metadata is invalid")
        value = float(observable_days)
        if not math.isfinite(value) or value < 0:
            raise ExperimentalArtifactError("Observable history metadata is invalid")
        return value

    def score(self, payload: ScoreRequest) -> ExperimentalScoreResponse:
        self._validate_scoring_time(payload.as_of)
        preview = build_feature_preview(payload)
        score = float(self._score_previews([preview])[0])
        warnings = self._history_warnings(preview)
        observable_days = self._observable_history_days(preview)

        return ExperimentalScoreResponse(
            status="experimental_anomaly_score",
            methodology_status="experimental_unsupervised_research_only",
            source="user_supplied_unverified_events",
            wallet=preview.wallet,
            as_of=preview.as_of,
            supplied_event_count=preview.supplied_event_count,
            included_historical_event_count=preview.included_historical_event_count,
            excluded_at_or_after_cutoff_count=preview.excluded_at_or_after_cutoff_count,
            model_id="isolation_forest",
            model_version=self._model_version,
            anomaly_score=score,
            score_direction="higher_means_more_anomalous_relative_to_training_reference",
            score_units="model_specific_unitless_isolation_forest_score",
            is_probability=False,
            training_cutoff=self._training_cutoff,
            feature_rules_version=preview.feature_rules_version,
            feature_registry_sha256=preview.feature_registry_sha256,
            observable_history_days=observable_days,
            warnings=warnings,
            interpretation=(
                "Experimental unsupervised anomaly score relative to the Phase 4B training "
                "reference. It is not a probability, label, fraud determination, or evidence "
                "of wash trading, intent, or misconduct."
            ),
        )

    def score_batch(
        self,
        payload: BatchScoreRequest,
        *,
        max_wallets: int,
        max_events: int,
        max_events_per_wallet: int,
    ) -> ExperimentalBatchScoreResponse:
        """Score eligible wallet groups once and rank them deterministically."""

        self._validate_scoring_time(payload.as_of)
        wallet_count = len(payload.wallet_histories)
        total_events = sum(len(history.events) for history in payload.wallet_histories)
        if wallet_count > max_wallets:
            raise ApiError(
                status_code=413,
                code="BATCH_WALLET_LIMIT_EXCEEDED",
                message="Wallet count exceeds the configured batch limit.",
                details={"max_batch_wallets": max_wallets},
            )
        if total_events > max_events:
            raise ApiError(
                status_code=413,
                code="BATCH_EVENT_LIMIT_EXCEEDED",
                message="Event count exceeds the configured batch limit.",
                details={"max_batch_events": max_events},
            )
        oversized = sorted(
            history.wallet
            for history in payload.wallet_histories
            if len(history.events) > max_events_per_wallet
        )
        if oversized:
            raise ApiError(
                status_code=413,
                code="WALLET_EVENT_LIMIT_EXCEEDED",
                message="A wallet history exceeds the configured per-wallet event limit.",
                details={
                    "max_batch_events_per_wallet": max_events_per_wallet,
                    "wallets": oversized,
                },
            )
        if payload.review_budget is not None and payload.review_budget > max_wallets:
            raise ApiError(
                status_code=413,
                code="REVIEW_BUDGET_LIMIT_EXCEEDED",
                message="Review budget exceeds the configured batch wallet limit.",
                details={"max_review_budget": max_wallets},
            )

        previews: list[FeaturePreviewResponse] = []
        rejected: list[BatchWalletRejection] = []
        for history in payload.wallet_histories:
            event_count = len(history.events)
            rejection: BatchWalletRejection | None = None
            if event_count == 0:
                rejection = BatchWalletRejection(
                    wallet=history.wallet,
                    code="EMPTY_WALLET_HISTORY",
                    message="No events were supplied for this wallet.",
                    supplied_event_count=0,
                )
            elif any(event.wallet != history.wallet for event in history.events):
                rejection = BatchWalletRejection(
                    wallet=history.wallet,
                    code="WALLET_EVENT_MISMATCH",
                    message="An event wallet does not match its wallet-history group.",
                    supplied_event_count=event_count,
                )
            elif len({event.source_row_number for event in history.events}) != event_count:
                rejection = BatchWalletRejection(
                    wallet=history.wallet,
                    code="DUPLICATE_SOURCE_ROW",
                    message="source_row_number values must be unique within a wallet history.",
                    supplied_event_count=event_count,
                )
            else:
                event_fingerprints = [
                    event.model_dump_json(exclude={"source_row_number"})
                    for event in history.events
                ]
                if len(set(event_fingerprints)) != event_count:
                    rejection = BatchWalletRejection(
                        wallet=history.wallet,
                        code="DUPLICATE_EVENT_RECORD",
                        message=(
                            "An exact event record is repeated; repeated transaction hashes "
                            "with distinct instruction records remain permitted."
                        ),
                        supplied_event_count=event_count,
                    )
            if rejection is not None:
                rejected.append(rejection)
                continue

            try:
                preview = build_feature_preview(
                    ScoreRequest(
                        as_of=payload.as_of.isoformat().replace("+00:00", "Z"),
                        events=history.events,
                    )
                )
            except ApiError as exc:
                if exc.code not in {"INSUFFICIENT_HISTORY", "FEATURE_INPUT_INVALID"}:
                    raise
                rejected.append(
                    BatchWalletRejection(
                        wallet=history.wallet,
                        code=exc.code,
                        message=exc.message,
                        supplied_event_count=event_count,
                    )
                )
                continue
            previews.append(preview)

        rejected.sort(key=lambda item: item.wallet)
        if not previews:
            raise ApiError(
                status_code=422,
                code="NO_SCORABLE_WALLETS",
                message="No submitted wallet has eligible pre-cutoff history.",
                details={
                    "rejected_wallets": [
                        item.model_dump(mode="json") for item in rejected
                    ]
                },
            )

        scores = self._score_previews(previews)
        scored = sorted(
            zip(previews, scores, strict=True),
            key=lambda item: (-float(item[1]), item[0].wallet),
        )
        requested_budget = payload.review_budget
        applied_budget = min(requested_budget or 0, len(scored))
        ranked_wallets: list[BatchWalletScore] = []
        for rank, (preview, score) in enumerate(scored, start=1):
            ranked_wallets.append(
                BatchWalletScore(
                    wallet=preview.wallet,
                    anomaly_score=float(score),
                    rank=rank,
                    selected_for_review=rank <= applied_budget,
                    supplied_event_count=preview.supplied_event_count,
                    included_historical_event_count=(
                        preview.included_historical_event_count
                    ),
                    excluded_at_or_after_cutoff_count=(
                        preview.excluded_at_or_after_cutoff_count
                    ),
                    observable_history_days=self._observable_history_days(preview),
                    warnings=self._history_warnings(preview),
                )
            )

        batch_warnings = [
            "Ranks are relative only to the wallets scored in this submitted batch.",
            "The review budget represents analyst capacity, not a validated decision threshold.",
        ]
        if rejected:
            batch_warnings.append(
                "Rejected wallet histories were not used in any other wallet's features or rank."
            )
        if requested_budget is not None and requested_budget > len(scored):
            batch_warnings.append(
                "The requested review budget was reduced to the number of scored wallets."
            )
        review_candidates = [
            item.wallet for item in ranked_wallets if item.selected_for_review
        ]
        return ExperimentalBatchScoreResponse(
            status="experimental_batch_anomaly_ranking",
            methodology_status="experimental_unsupervised_research_only",
            source="user_supplied_unverified_events",
            model_id="isolation_forest",
            model_version=self._model_version,
            as_of=payload.as_of,
            training_cutoff=self._training_cutoff,
            score_direction="higher_means_more_anomalous_relative_to_training_reference",
            score_units="model_specific_unitless_isolation_forest_score",
            is_probability=False,
            feature_rules_version=FEATURE_RULES_VERSION,
            feature_registry_sha256=feature_registry_sha256(),
            wallets_submitted=wallet_count,
            wallets_scored=len(ranked_wallets),
            wallets_rejected=len(rejected),
            review_budget_requested=requested_budget,
            review_budget=applied_budget,
            review_candidates=review_candidates,
            ranked_wallets=ranked_wallets,
            rejected_wallets=rejected,
            warnings=batch_warnings,
            interpretation=(
                "Experimental statistical anomalies requiring review; not confirmed wash "
                "trading or fraud."
            ),
        )
