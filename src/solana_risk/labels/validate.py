"""Validate externally supplied wallet labels without creating or repairing them.

The validator is deliberately narrower than a general data-cleaning utility. It
accepts only an explicit, independently verified binary-label contract and
rejects unsupported identities, domains, label types, provenance, or temporal
relationships. It does not derive labels from features and does not write a
labelled dataset.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

import pandas as pd
from pandas.api.types import is_bool_dtype, is_integer_dtype

LABEL_CONTRACT_VERSION = "1.0.0"
REQUIRED_LABEL_COLUMNS: tuple[str, ...] = (
    "wallet",
    "scoring_time",
    "label",
    "target_type",
    "label_definition",
    "domain",
    "outcome_window_start",
    "outcome_window_end",
    "evidence_time",
    "knowledge_time",
    "evidence_source",
    "evidence_reference",
    "verification_status",
    "review_method",
    "label_version",
)
TIMESTAMP_COLUMNS: tuple[str, ...] = (
    "scoring_time",
    "outcome_window_start",
    "outcome_window_end",
    "evidence_time",
    "knowledge_time",
)
TEXT_COLUMNS: tuple[str, ...] = (
    "wallet",
    "target_type",
    "label_definition",
    "domain",
    "evidence_source",
    "evidence_reference",
    "verification_status",
    "review_method",
    "label_version",
)
SUPPORTED_TARGET_TYPES = frozenset({"historical_status", "future_outcome"})
SUPPORTED_VERIFICATION_STATUS = "independently_verified"
_BASE58_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")


class LabelValidationError(ValueError):
    """Raised when proposed supervised labels fail the evidence contract."""


def _require_exact_schema(frame: pd.DataFrame) -> None:
    if frame.columns.duplicated().any():
        raise LabelValidationError("Label schema contains duplicate column names")
    missing = sorted(set(REQUIRED_LABEL_COLUMNS).difference(frame.columns))
    unexpected = sorted(set(frame.columns).difference(REQUIRED_LABEL_COLUMNS))
    if missing or unexpected:
        details: list[str] = []
        if missing:
            details.append(f"missing columns: {missing}")
        if unexpected:
            details.append(f"unexpected columns: {unexpected}")
        raise LabelValidationError("Label schema mismatch; " + "; ".join(details))


def _require_text_values(frame: pd.DataFrame) -> None:
    for column in TEXT_COLUMNS:
        invalid = frame[column].map(
            lambda value: not isinstance(value, str)
            or not value
            or value != value.strip()
        )
        if invalid.any():
            raise LabelValidationError(
                f"{column!r} must contain nonempty strings without surrounding whitespace"
            )


def _parse_timestamp_column(frame: pd.DataFrame, column: str) -> pd.Series:
    parsed: list[pd.Timestamp] = []
    for row_number, value in enumerate(frame[column], start=1):
        try:
            timestamp = pd.Timestamp(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise LabelValidationError(
                f"{column!r} row {row_number} is not a valid timestamp"
            ) from exc
        if pd.isna(timestamp):
            raise LabelValidationError(
                f"{column!r} row {row_number} is not a valid timestamp"
            )
        if timestamp.tzinfo is None:
            raise LabelValidationError(
                f"{column!r} row {row_number} must include an explicit timezone"
            )
        parsed.append(timestamp.tz_convert("UTC"))
    return pd.Series(parsed, index=frame.index, dtype="datetime64[ns, UTC]")


def _require_consistent_definition(frame: pd.DataFrame) -> None:
    for column in (
        "target_type",
        "label_definition",
        "domain",
        "verification_status",
        "label_version",
    ):
        if frame[column].nunique(dropna=False) != 1:
            raise LabelValidationError(
                f"{column!r} must have exactly one value within a label-table version"
            )


def _require_temporal_contract(frame: pd.DataFrame) -> None:
    if (frame["outcome_window_end"] < frame["outcome_window_start"]).any():
        raise LabelValidationError(
            "outcome_window_end must be on or after outcome_window_start"
        )
    if (
        (frame["evidence_time"] < frame["outcome_window_start"])
        | (frame["evidence_time"] > frame["outcome_window_end"])
    ).any():
        raise LabelValidationError(
            "evidence_time must fall inside the declared outcome window"
        )
    if (frame["knowledge_time"] < frame["outcome_window_end"]).any():
        raise LabelValidationError(
            "knowledge_time must be on or after the mature outcome-window end"
        )

    target_type = frame["target_type"].iat[0]
    if target_type == "future_outcome":
        if (frame["outcome_window_start"] < frame["scoring_time"]).any():
            raise LabelValidationError(
                "future_outcome windows must start on or after scoring_time"
            )
        if (frame["outcome_window_end"] <= frame["outcome_window_start"]).any():
            raise LabelValidationError(
                "future_outcome windows must have positive duration"
            )
    elif target_type == "historical_status":
        if (frame["outcome_window_end"] > frame["scoring_time"]).any():
            raise LabelValidationError(
                "historical_status evidence must end on or before scoring_time"
            )
        if (frame["knowledge_time"] > frame["scoring_time"]).any():
            raise LabelValidationError(
                "historical_status evidence must be known by scoring_time"
            )


def validate_label_table(
    frame: pd.DataFrame,
    *,
    known_wallets: Iterable[str],
    expected_domain: str,
) -> pd.DataFrame:
    """Return a validated copy of a model-ready external label table.

    Validation is fail-closed. The caller must provide the wallets observed in
    the approved event domain and the exact expected domain name. The function
    does not strip strings, coerce labels, infer timestamps, deduplicate rows,
    create missing values, or persist the returned frame.
    """

    if not isinstance(frame, pd.DataFrame):
        raise LabelValidationError("labels must be provided as a pandas DataFrame")
    if frame.empty:
        raise LabelValidationError("label table must not be empty")
    if not isinstance(expected_domain, str) or not expected_domain.strip():
        raise LabelValidationError("expected_domain must be a nonempty string")

    _require_exact_schema(frame)
    validated = frame.loc[:, REQUIRED_LABEL_COLUMNS].copy()
    _require_text_values(validated)

    malformed_wallets = ~validated["wallet"].str.fullmatch(_BASE58_RE)
    if malformed_wallets.any():
        raise LabelValidationError("wallet values must be 32-44 character Base58 strings")

    known_wallet_set = set(known_wallets)
    if not known_wallet_set:
        raise LabelValidationError("known_wallets must not be empty")
    unknown_wallets = set(validated["wallet"]).difference(known_wallet_set)
    if unknown_wallets:
        raise LabelValidationError(
            f"label table contains {len(unknown_wallets)} wallet(s) outside the approved domain"
        )

    if is_bool_dtype(validated["label"].dtype) or not is_integer_dtype(
        validated["label"].dtype
    ):
        raise LabelValidationError("label must use an integer dtype with exact values 0 and 1")
    if validated["label"].isna().any() or not validated["label"].isin([0, 1]).all():
        raise LabelValidationError("label must contain only exact integer values 0 and 1")
    if set(validated["label"].unique()) != {0, 1}:
        raise LabelValidationError("label table must contain independently verified examples of both classes")

    _require_consistent_definition(validated)
    target_type = validated["target_type"].iat[0]
    if target_type not in SUPPORTED_TARGET_TYPES:
        raise LabelValidationError(
            f"unsupported target_type {target_type!r}; expected one of {sorted(SUPPORTED_TARGET_TYPES)}"
        )
    if validated["domain"].iat[0] != expected_domain:
        raise LabelValidationError(
            f"label domain {validated['domain'].iat[0]!r} does not match {expected_domain!r}"
        )
    if validated["verification_status"].iat[0] != SUPPORTED_VERIFICATION_STATUS:
        raise LabelValidationError(
            "verification_status must be 'independently_verified'; heuristic flags are unsupported"
        )

    for column in TIMESTAMP_COLUMNS:
        validated[column] = _parse_timestamp_column(validated, column)
    if validated[["wallet", "scoring_time"]].duplicated().any():
        raise LabelValidationError("wallet and scoring_time must be unique together")
    _require_temporal_contract(validated)

    return validated
