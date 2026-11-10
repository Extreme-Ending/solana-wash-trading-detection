"""Synthetic contract tests for deterministic Phase 2 preprocessing."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from solana_risk.data.audit import REQUIRED_COLUMNS, AuditValidationError
from solana_risk.data.preprocess import preprocess_dataset, write_outputs

WALLET = "1" * 32
TX_ONE = "2" * 86
TX_TWO = "3" * 86
TOKEN_IN = "4" * 32
TOKEN_OUT = "5" * 32


def _row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "wallet": WALLET,
        "block_time": "2025-01-01 03:00:10+03:00",
        "block_slot": "100",
        "tx_hash": TX_ONE,
        "dex": "Raydium amm",
        "token_pair": "SOL-USDC",
        "token_in": TOKEN_IN,
        "token_out": TOKEN_OUT,
        "amount_in": "1.0",
        "amount_out": "100.0",
        "amount_usd": "100.0",
        "fee_usd": "0.1",
        "outer_instruction_index": "2",
        "inner_instruction_index": "1",
        "source": "DEX_TRADE",
        "prev_event_time": "2025-01-01 02:59:10+03:00",
        "seconds_since_prev": "60",
        "source_week": "2025-01-W1",
    }
    row.update(overrides)
    return row


def _write(path: Path, rows: list[dict[str, object]]) -> Path:
    pd.DataFrame(rows, columns=REQUIRED_COLUMNS).to_csv(path, index=False)
    return path


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_valid_schema_and_utc_timestamp_normalization(tmp_path: Path) -> None:
    result = preprocess_dataset(_write(tmp_path / "valid.csv", [_row()]))

    assert result.report["schema_validation"]["status"] == "PASS"
    assert result.cleaned.loc[0, "block_time"] == "2025-01-01T00:00:10.000000Z"
    assert result.cleaned.loc[0, "raw__block_time"] == "2025-01-01 03:00:10+03:00"


def test_invalid_schema_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "invalid-schema.csv"
    pd.DataFrame([{"wallet": WALLET, "unexpected": "value"}]).to_csv(path, index=False)

    with pytest.raises(AuditValidationError, match="schema mismatch"):
        preprocess_dataset(path)


def test_missing_identifiers_are_quarantined(tmp_path: Path) -> None:
    result = preprocess_dataset(
        _write(tmp_path / "missing-id.csv", [_row(wallet="<nil>"), _row(tx_hash="")])
    )

    assert result.cleaned.empty
    assert len(result.quarantine) == 2
    assert "MISSING_WALLET" in result.quarantine.loc[0, "quarantine_reasons"]
    assert "MISSING_TX_HASH" in result.quarantine.loc[1, "quarantine_reasons"]


def test_missing_fee_is_retained_without_zero_imputation(tmp_path: Path) -> None:
    result = preprocess_dataset(_write(tmp_path / "missing-fee.csv", [_row(fee_usd="<nil>")]))

    assert len(result.cleaned) == 1
    assert pd.isna(result.cleaned.loc[0, "fee_usd"])
    assert bool(result.cleaned.loc[0, "fee_usd_missing"])
    assert result.report["warning_counts_retained"]["fee_usd_missing"] == 1


def test_dex_format_normalization_preserves_raw_values(tmp_path: Path) -> None:
    result = preprocess_dataset(
        _write(
            tmp_path / "dex.csv",
            [
                _row(dex="  Meteora  "),
                _row(tx_hash=TX_TWO, dex="Raydium CLMM", inner_instruction_index="2"),
            ],
        )
    )

    assert result.cleaned["dex"].tolist() == ["meteora", "raydium_clmm"]
    assert result.cleaned["raw__dex"].tolist() == ["  Meteora  ", "Raydium CLMM"]


def test_repeated_transaction_distinct_instructions_are_retained(tmp_path: Path) -> None:
    result = preprocess_dataset(
        _write(
            tmp_path / "multi-event.csv",
            [_row(inner_instruction_index="1"), _row(inner_instruction_index="2", amount_usd="90")],
        )
    )

    assert len(result.cleaned) == 2
    assert result.cleaned["repeated_transaction_hash"].all()
    assert not result.cleaned["ambiguous_complete_instruction_key"].any()
    assert result.cleaned["event_key_hash"].nunique() == 2


def test_exact_duplicate_after_first_is_preserved_in_quarantine(tmp_path: Path) -> None:
    duplicate = _row()
    result = preprocess_dataset(_write(tmp_path / "duplicate.csv", [duplicate, duplicate]))

    assert len(result.cleaned) == 1
    assert len(result.quarantine) == 1
    assert result.quarantine.loc[0, "quarantine_reasons"] == "EXACT_DUPLICATE_AFTER_FIRST"
    assert result.report["row_reconciliation"] == {
        "input": 2,
        "retained": 1,
        "quarantined": 1,
        "removed": 0,
        "reconciles": True,
    }


def test_invalid_and_nonpositive_amounts_are_quarantined(tmp_path: Path) -> None:
    result = preprocess_dataset(
        _write(
            tmp_path / "amounts.csv",
            [
                _row(amount_usd="not-a-number"),
                _row(tx_hash=TX_TWO, amount_in="0", amount_usd="0"),
            ],
        )
    )

    assert result.cleaned.empty
    reasons = "|".join(result.quarantine["quarantine_reasons"].tolist())
    assert "INVALID_AMOUNT_USD" in reasons
    assert "NONPOSITIVE_AMOUNT_IN" in reasons
    assert "NONPOSITIVE_AMOUNT_USD" in reasons


def test_outlier_is_preserved_and_flagged_for_review(tmp_path: Path) -> None:
    rows = [
        _row(tx_hash=str(number) * 86, inner_instruction_index=str(number), amount_usd=value)
        for number, value in zip((2, 3, 4, 5, 6), ("10", "11", "12", "13", "1000"))
    ]
    result = preprocess_dataset(_write(tmp_path / "outlier.csv", rows))

    flagged = result.cleaned.loc[result.cleaned["review_amount_usd_iqr_outlier"]]
    assert len(result.cleaned) == 5
    assert flagged["amount_usd"].tolist() == [1000.0]
    assert result.report["numeric_policy"]["amount_usd_iqr_review"]["action"].startswith(
        "Retain unchanged"
    )


def test_input_immutable_sort_deterministic_and_outputs_reproducible(tmp_path: Path) -> None:
    path = _write(
        tmp_path / "stable.csv",
        [
            _row(block_time="2025-01-02T00:00:00Z", tx_hash=TX_TWO),
            _row(block_time="2025-01-01T00:00:00Z", tx_hash=TX_ONE),
        ],
    )
    before = _digest(path)
    first = preprocess_dataset(path)
    first_paths = write_outputs(first, tmp_path / "first-data", tmp_path / "first-report")
    second = preprocess_dataset(path)
    second_paths = write_outputs(second, tmp_path / "second-data", tmp_path / "second-report")

    assert _digest(path) == before
    assert first.cleaned["tx_hash"].tolist() == [TX_ONE, TX_TWO]
    for name in first_paths:
        assert first_paths[name].read_bytes() == second_paths[name].read_bytes()


def test_cli_runs_outside_repository_and_reconciles_rows(tmp_path: Path) -> None:
    input_path = _write(tmp_path / "cli.csv", [_row(), _row(tx_hash=TX_TWO, amount_usd="0")])
    project_root = Path(__file__).resolve().parents[1]
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(project_root / "src")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "solana_risk.data.preprocess",
            "--input",
            str(input_path),
            "--processed-dir",
            str(tmp_path / "processed"),
            "--report-dir",
            str(tmp_path / "reports"),
        ],
        cwd=tmp_path,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    report = pd.read_json(tmp_path / "reports" / "cleaning_report.json", typ="series")
    assert report["row_reconciliation"] == {
        "input": 2,
        "quarantined": 1,
        "reconciles": True,
        "removed": 0,
        "retained": 1,
    }
