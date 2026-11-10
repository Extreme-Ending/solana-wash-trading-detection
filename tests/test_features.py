"""Synthetic leakage and contract tests for Phase 3 wallet snapshots."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from solana_risk.features.build import (
    FEATURE_REGISTRY,
    FORBIDDEN_TARGET_COLUMNS,
    METADATA_COLUMNS,
    MODEL_FEATURE_COLUMNS,
    FeatureValidationError,
    build_wallet_snapshots,
    feature_registry_records,
    parse_as_of,
    write_outputs,
)

WALLET_A = "1" * 32
WALLET_B = "2" * 32
TOKEN_A = "3" * 32
TOKEN_B = "4" * 32
TOKEN_C = "5" * 32


def _event(
    row_number: int,
    *,
    wallet: str = WALLET_A,
    block_time: str = "2025-01-01T00:00:00Z",
    tx_hash: str | None = None,
    amount_usd: float = 10.0,
    fee_usd: float | None = 0.1,
    dex: str = "raydium",
    token_in: str = TOKEN_A,
    token_out: str = TOKEN_B,
    token_pair: str | None = "A-B",
    outer_instruction_index: int | None = 1,
    inner_instruction_index: int | None = 0,
) -> dict[str, object]:
    return {
        "source_row_number": row_number,
        "wallet": wallet,
        "block_time": block_time,
        "block_slot": 100 + row_number,
        "tx_hash": tx_hash or str((row_number % 7) + 3) * 86,
        "dex": dex,
        "token_pair": token_pair,
        "token_in": token_in,
        "token_out": token_out,
        "amount_usd": amount_usd,
        "fee_usd": fee_usd,
        "outer_instruction_index": outer_instruction_index,
        "inner_instruction_index": inner_instruction_index,
    }


def _frame(*rows: dict[str, object]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def test_strict_cutoff_excludes_events_at_and_after_cutoff() -> None:
    events = _frame(
        _event(1, block_time="2025-01-01T23:59:59Z"),
        _event(2, block_time="2025-01-02T00:00:00Z"),
        _event(3, block_time="2025-01-03T00:00:00Z"),
    )

    snapshots = build_wallet_snapshots(events, ["2025-01-02T00:00:00Z"])

    assert len(snapshots) == 1
    assert snapshots.loc[0, "historical_event_count"] == 1
    assert snapshots.loc[0, "max_usd_volume"] == 10.0


def test_future_event_cannot_change_earlier_snapshot() -> None:
    historical = _frame(
        _event(1, block_time="2025-01-01T00:00:00Z", amount_usd=10),
        _event(2, block_time="2025-01-02T00:00:00Z", amount_usd=20),
    )
    with_future = pd.concat(
        [historical, _frame(_event(3, block_time="2025-12-01T00:00:00Z", amount_usd=999999))],
        ignore_index=True,
    )

    expected = build_wallet_snapshots(historical, ["2025-02-01T00:00:00Z"])
    observed = build_wallet_snapshots(with_future, ["2025-02-01T00:00:00Z"])

    pd.testing.assert_frame_equal(expected, observed)


def test_multiple_wallets_and_cutoffs_produce_distinct_snapshots() -> None:
    events = _frame(
        _event(1, wallet=WALLET_A, block_time="2025-01-01T00:00:00Z"),
        _event(2, wallet=WALLET_B, block_time="2025-02-01T00:00:00Z"),
    )

    snapshots = build_wallet_snapshots(
        events,
        ["2025-01-15T00:00:00Z", "2025-03-01T00:00:00Z"],
    )

    assert len(snapshots) == 3
    assert snapshots.groupby("as_of")["wallet"].nunique().tolist() == [1, 2]


def test_single_event_wallet_preserves_unavailable_inter_event_statistics() -> None:
    snapshots = build_wallet_snapshots(
        _frame(_event(1)),
        ["2025-01-02T00:00:00Z"],
    )

    row = snapshots.iloc[0]
    assert bool(row["single_event_history"])
    assert pd.isna(row["inter_event_mean_seconds"])
    assert pd.isna(row["inter_event_median_seconds"])
    assert pd.isna(row["inter_event_std_seconds"])
    assert row["observed_activity_duration_days"] == 0.0


def test_missing_fee_is_measured_not_imputed() -> None:
    snapshots = build_wallet_snapshots(
        _frame(_event(1, fee_usd=None), _event(2, fee_usd=0.0)),
        ["2025-01-02T00:00:00Z"],
    )

    assert snapshots.loc[0, "missing_fee_proportion"] == 0.5


def test_incomplete_observed_history_is_explicit() -> None:
    snapshots = build_wallet_snapshots(
        _frame(_event(1, block_time="2025-01-29T00:00:00Z")),
        ["2025-02-01T00:00:00Z"],
    )

    row = snapshots.iloc[0]
    assert row["observable_history_days"] == 3.0
    assert bool(row["insufficient_history_7d"])
    assert bool(row["insufficient_history_30d"])
    assert row["history_coverage_30d_fraction"] == 0.1


def test_repeated_transaction_hash_counts_multi_instruction_transaction() -> None:
    repeated_hash = "6" * 86
    events = _frame(
        _event(1, tx_hash=repeated_hash, inner_instruction_index=0),
        _event(2, tx_hash=repeated_hash, inner_instruction_index=1),
        _event(3, tx_hash="7" * 86, inner_instruction_index=0),
    )

    snapshots = build_wallet_snapshots(events, ["2025-01-02T00:00:00Z"])

    assert snapshots.loc[0, "historical_event_count"] == 3
    assert snapshots.loc[0, "unique_transaction_count"] == 2
    assert snapshots.loc[0, "multi_instruction_transaction_count"] == 1


def test_window_lower_boundaries_are_inclusive_and_cutoff_is_exclusive() -> None:
    cutoff = "2025-01-31T00:00:00Z"
    events = _frame(
        _event(1, block_time="2025-01-01T00:00:00Z"),
        _event(2, block_time="2025-01-24T00:00:00Z"),
        _event(3, block_time="2025-01-30T00:00:00Z"),
        _event(4, block_time=cutoff),
    )

    row = build_wallet_snapshots(events, [cutoff]).iloc[0]

    assert row["events_last_24h"] == 1
    assert row["events_last_7d"] == 2
    assert row["events_last_30d"] == 3
    assert row["historical_event_count"] == 3


@pytest.mark.parametrize("value", ["not-a-time", "2025-01-01T00:00:00", "NaT"])
def test_invalid_or_naive_scoring_timestamp_is_rejected(value: str) -> None:
    with pytest.raises(FeatureValidationError, match="timestamp|timezone"):
        parse_as_of(value)


def test_feature_registry_matches_output_and_contains_complete_lineage() -> None:
    snapshots = build_wallet_snapshots(_frame(_event(1)), ["2025-01-02T00:00:00Z"])
    records = feature_registry_records()

    assert len(FEATURE_REGISTRY) == 29
    assert tuple(snapshots.columns) == (*METADATA_COLUMNS, *MODEL_FEATURE_COLUMNS)
    assert [record["name"] for record in records] == list(MODEL_FEATURE_COLUMNS)
    assert all(record["definition"] and record["calculation"] for record in records)
    assert all(record["units"] and record["missingness_policy"] for record in records)
    assert all(record["lineage"] for record in records)


def test_feature_generation_and_written_outputs_are_deterministic(tmp_path: Path) -> None:
    events = _frame(
        _event(2, block_time="2025-01-02T00:00:00Z", amount_usd=20),
        _event(1, block_time="2025-01-01T00:00:00Z", amount_usd=10),
    )
    input_path = tmp_path / "cleaned.csv"
    events.to_csv(input_path, index=False)
    cutoff = [parse_as_of("2025-02-01T00:00:00Z")]
    first = build_wallet_snapshots(events, cutoff)
    second = build_wallet_snapshots(events.sample(frac=1, random_state=7), cutoff)
    first_paths = write_outputs(
        first,
        events,
        cutoff,
        input_path,
        tmp_path / "first" / "wallet_snapshots.csv",
        tmp_path / "first-report",
    )
    second_paths = write_outputs(
        second,
        events,
        cutoff,
        input_path,
        tmp_path / "second" / "wallet_snapshots.csv",
        tmp_path / "second-report",
    )

    pd.testing.assert_frame_equal(first, second)
    assert first_paths["snapshots"].read_bytes() == second_paths["snapshots"].read_bytes()
    assert first_paths["json"].read_bytes() == second_paths["json"].read_bytes()
    assert first_paths["markdown"].read_bytes() == second_paths["markdown"].read_bytes()


def test_target_columns_are_rejected_and_never_registered() -> None:
    events = _frame(_event(1))
    events["is_fraud"] = 1

    with pytest.raises(FeatureValidationError, match="forbidden target"):
        build_wallet_snapshots(events, ["2025-01-02T00:00:00Z"])
    assert not (set(MODEL_FEATURE_COLUMNS) & FORBIDDEN_TARGET_COLUMNS)
    assert "wallet" not in MODEL_FEATURE_COLUMNS
    assert "as_of" not in MODEL_FEATURE_COLUMNS


def test_cli_runs_outside_repository_root(tmp_path: Path) -> None:
    input_path = tmp_path / "cleaned.csv"
    _frame(_event(1)).to_csv(input_path, index=False)
    project_root = Path(__file__).resolve().parents[1]
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(project_root / "src")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "solana_risk.features.build",
            "--as-of",
            "2025-02-01T00:00:00Z",
            "--input",
            str(input_path),
            "--output",
            str(tmp_path / "output" / "snapshots.csv"),
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
    assert (tmp_path / "output" / "snapshots.csv").is_file()
    assert (tmp_path / "reports" / "feature_report.json").is_file()
