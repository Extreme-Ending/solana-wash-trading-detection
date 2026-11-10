"""Synthetic tests for the Phase 1 read-only dataset audit."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import pytest

from solana_risk.data.audit import (
    REQUIRED_COLUMNS,
    AuditValidationError,
    audit_dataset,
    default_input_path,
    repository_root,
    write_reports,
)


def _row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "wallet": "11111111111111111111111111111111",
        "block_time": "2025-01-01T00:00:10Z",
        "block_slot": 100,
        "tx_hash": "transaction-one",
        "dex": "raydium",
        "token_pair": "SOL/USDC",
        "token_in": "So11111111111111111111111111111111111111112",
        "token_out": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "amount_in": 1.0,
        "amount_out": 100.0,
        "amount_usd": 100.0,
        "fee_usd": 0.1,
        "outer_instruction_index": 2,
        "inner_instruction_index": 1,
        "source": "dex_trade",
        "prev_event_time": "2025-01-01T00:00:00Z",
        "seconds_since_prev": 10.0,
        "source_week": "2025-W01",
    }
    row.update(overrides)
    return row


def _write_csv(path: Path, rows: list[dict[str, object]]) -> Path:
    pd.DataFrame(rows, columns=REQUIRED_COLUMNS).to_csv(path, index=False)
    return path


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_missing_input_file_fails_clearly(tmp_path: Path) -> None:
    with pytest.raises(AuditValidationError, match="does not exist"):
        audit_dataset(tmp_path / "missing.csv")


def test_directory_is_rejected_as_invalid_input(tmp_path: Path) -> None:
    with pytest.raises(AuditValidationError, match="not a regular file"):
        audit_dataset(tmp_path)


@pytest.mark.parametrize("header_only", [False, True])
def test_empty_dataset_is_rejected(tmp_path: Path, header_only: bool) -> None:
    path = tmp_path / "empty.csv"
    if header_only:
        pd.DataFrame(columns=REQUIRED_COLUMNS).to_csv(path, index=False)
    else:
        path.touch()
    with pytest.raises(AuditValidationError, match="empty|no data rows"):
        audit_dataset(path)


def test_missing_required_fields_are_reported(tmp_path: Path) -> None:
    path = tmp_path / "missing-fields.csv"
    pd.DataFrame([{"wallet": "abc", "block_time": "2025-01-01"}]).to_csv(path, index=False)
    with pytest.raises(AuditValidationError, match="missing required fields"):
        audit_dataset(path)


def test_malformed_csv_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "malformed.csv"
    path.write_text(",".join(REQUIRED_COLUMNS) + "\n" + '"unterminated\n', encoding="utf-8")
    with pytest.raises(AuditValidationError, match="Could not parse"):
        audit_dataset(path)


def test_timestamp_failure_duplicates_and_missingness_are_counted(tmp_path: Path) -> None:
    duplicate = _row(fee_usd=None, block_time="not-a-time")
    path = _write_csv(tmp_path / "audit.csv", [duplicate, duplicate, _row(tx_hash="transaction-two")])

    summary = audit_dataset(path)

    assert summary["timestamps"]["block_time"]["parse_failure_count"] == 2
    assert summary["duplicates"]["exact_duplicate_rows_beyond_first"] == 1
    assert summary["duplicates"]["rows_participating_in_duplicate_transaction_hashes"] == 2
    missing_fee = next(row for row in summary["missing_values"] if row["column"] == "fee_usd")
    assert missing_fee == {"column": "fee_usd", "count": 2, "percentage": pytest.approx(200 / 3)}


def test_single_wallet_edge_case_and_input_immutability(tmp_path: Path) -> None:
    path = _write_csv(
        tmp_path / "one-wallet.csv",
        [_row(), _row(tx_hash="transaction-two", block_time="2025-02-01T00:00:00Z")],
    )
    before = _digest(path)

    summary = audit_dataset(path)

    assert _digest(path) == before
    assert summary["wallet_activity"]["unique_wallet_count"] == 1
    assert summary["wallet_activity"]["maximum_events_for_one_wallet"] == 2
    assert summary["temporal_readiness"]["wallet_month_presence"]["wallets_in_multiple_months"] == 1


def test_outputs_are_deterministic_and_strict_json(tmp_path: Path) -> None:
    path = _write_csv(tmp_path / "stable.csv", [_row()])
    first = audit_dataset(path)
    first_paths = write_reports(first, tmp_path / "first")
    second = audit_dataset(path)
    second_paths = write_reports(second, tmp_path / "second")

    assert first == second
    assert first_paths[0].read_bytes() == second_paths[0].read_bytes()
    assert first_paths[1].read_bytes() == second_paths[1].read_bytes()


def test_default_dataset_path_is_repository_root_even_after_chdir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    expected_root = repository_root()
    monkeypatch.chdir(tmp_path)

    assert default_input_path() == expected_root / "nft.csv"
