"""Synthetic tests for the Phase 4A label-evidence contract."""

from __future__ import annotations

import pandas as pd
import pytest

from solana_risk.labels import (
    REQUIRED_LABEL_COLUMNS,
    LabelValidationError,
    validate_label_table,
)

WALLET_A = "1" * 32
WALLET_B = "2" * 32


def _labels(**overrides: object) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for wallet, label in ((WALLET_A, 0), (WALLET_B, 1)):
        row: dict[str, object] = {
            "wallet": wallet,
            "scoring_time": "2025-09-01T00:00:00Z",
            "label": label,
            "target_type": "future_outcome",
            "label_definition": "Independently adjudicated wash trading in the next 30 days",
            "domain": "dex_swap",
            "outcome_window_start": "2025-09-01T00:00:00Z",
            "outcome_window_end": "2025-10-01T00:00:00Z",
            "evidence_time": "2025-09-15T00:00:00Z",
            "knowledge_time": "2025-10-02T00:00:00Z",
            "evidence_source": "independent-review-board",
            "evidence_reference": f"case-{label + 1}",
            "verification_status": "independently_verified",
            "review_method": "documented dual review",
            "label_version": "labels-1.0.0",
        }
        row.update(overrides)
        rows.append(row)
    return pd.DataFrame(rows, columns=REQUIRED_LABEL_COLUMNS)


def _validate(frame: pd.DataFrame) -> pd.DataFrame:
    return validate_label_table(
        frame,
        known_wallets={WALLET_A, WALLET_B},
        expected_domain="dex_swap",
    )


def test_valid_future_outcome_contract_is_accepted_and_normalized_to_utc() -> None:
    labels = _labels()
    labels.loc[0, "scoring_time"] = "2025-09-01T03:00:00+03:00"

    validated = _validate(labels)

    assert tuple(validated.columns) == REQUIRED_LABEL_COLUMNS
    assert str(validated["scoring_time"].dtype) == "datetime64[ns, UTC]"
    assert validated.loc[0, "scoring_time"] == pd.Timestamp("2025-09-01T00:00:00Z")
    assert labels.loc[0, "scoring_time"] == "2025-09-01T03:00:00+03:00"


@pytest.mark.parametrize("column", REQUIRED_LABEL_COLUMNS)
def test_every_contract_column_is_required(column: str) -> None:
    with pytest.raises(LabelValidationError, match="missing columns"):
        _validate(_labels().drop(columns=column))


def test_unexpected_columns_are_rejected() -> None:
    labels = _labels()
    labels["model_score"] = 0.9

    with pytest.raises(LabelValidationError, match="unexpected columns"):
        _validate(labels)


@pytest.mark.parametrize("label_values", [[0.0, 1.0], [False, True], [0, 2]])
def test_nonbinary_or_noninteger_labels_are_rejected(label_values: list[object]) -> None:
    labels = _labels()
    labels["label"] = label_values

    with pytest.raises(LabelValidationError, match="label"):
        _validate(labels)


def test_single_class_table_is_rejected() -> None:
    with pytest.raises(LabelValidationError, match="both classes"):
        _validate(_labels(label=0))


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("wallet", "not-a-wallet", "Base58"),
        ("domain", "nft_marketplace", "does not match"),
        ("verification_status", "heuristic_unverified", "independently_verified"),
        ("target_type", "retrospective_guess", "unsupported target_type"),
        ("evidence_source", " ", "nonempty strings"),
    ],
)
def test_unsupported_identity_provenance_or_target_is_rejected(
    column: str, value: object, message: str
) -> None:
    with pytest.raises(LabelValidationError, match=message):
        _validate(_labels(**{column: value}))


def test_unknown_wallet_is_rejected() -> None:
    labels = _labels()
    labels.loc[1, "wallet"] = "3" * 32

    with pytest.raises(LabelValidationError, match="outside the approved domain"):
        _validate(labels)


def test_duplicate_wallet_scoring_observation_is_rejected() -> None:
    labels = _labels()
    labels.loc[1, "wallet"] = WALLET_A

    with pytest.raises(LabelValidationError, match="unique together"):
        _validate(labels)


def test_equivalent_timezone_scoring_observations_are_duplicates() -> None:
    labels = _labels()
    labels.loc[1, "wallet"] = WALLET_A
    labels.loc[1, "scoring_time"] = "2025-09-01T03:00:00+03:00"

    with pytest.raises(LabelValidationError, match="unique together"):
        _validate(labels)


@pytest.mark.parametrize("value", ["not-a-time", "2025-09-01T00:00:00", pd.NaT])
def test_invalid_or_naive_evidence_timestamp_is_rejected(value: object) -> None:
    with pytest.raises(LabelValidationError, match="timestamp|timezone"):
        _validate(_labels(evidence_time=value))


def test_future_outcome_cannot_start_before_scoring_time() -> None:
    with pytest.raises(LabelValidationError, match="start on or after scoring_time"):
        _validate(_labels(outcome_window_start="2025-08-31T23:59:59Z"))


def test_evidence_must_fall_inside_outcome_window() -> None:
    with pytest.raises(LabelValidationError, match="inside the declared outcome window"):
        _validate(_labels(evidence_time="2025-10-02T00:00:00Z"))


def test_knowledge_time_cannot_precede_mature_outcome_window() -> None:
    with pytest.raises(LabelValidationError, match="mature outcome-window end"):
        _validate(_labels(knowledge_time="2025-09-30T00:00:00Z"))


def test_valid_historical_status_must_be_known_by_scoring_time() -> None:
    labels = _labels(
        target_type="historical_status",
        label_definition="Independently demonstrated historical wash-trading status",
        outcome_window_start="2025-01-01T00:00:00Z",
        outcome_window_end="2025-08-01T00:00:00Z",
        evidence_time="2025-07-15T00:00:00Z",
        knowledge_time="2025-08-15T00:00:00Z",
    )

    validated = _validate(labels)

    assert validated["target_type"].iat[0] == "historical_status"


def test_historical_status_known_after_scoring_time_is_rejected() -> None:
    labels = _labels(
        target_type="historical_status",
        label_definition="Independently demonstrated historical wash-trading status",
        outcome_window_start="2025-01-01T00:00:00Z",
        outcome_window_end="2025-08-01T00:00:00Z",
        evidence_time="2025-07-15T00:00:00Z",
        knowledge_time="2025-10-01T00:00:00Z",
    )

    with pytest.raises(LabelValidationError, match="known by scoring_time"):
        _validate(labels)
