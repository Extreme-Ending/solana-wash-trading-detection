"""Deterministic, read-only data-quality audit for the capstone event dataset.

The module deliberately audits evidence without cleaning rows, manufacturing labels,
or inferring wallet-to-wallet relationships. Generated reports are local artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import re
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

import pandas as pd

LOGGER = logging.getLogger(__name__)

REQUIRED_COLUMNS: tuple[str, ...] = (
    "wallet",
    "block_time",
    "block_slot",
    "tx_hash",
    "dex",
    "token_pair",
    "token_in",
    "token_out",
    "amount_in",
    "amount_out",
    "amount_usd",
    "fee_usd",
    "outer_instruction_index",
    "inner_instruction_index",
    "source",
    "prev_event_time",
    "seconds_since_prev",
    "source_week",
)
TIMESTAMP_COLUMNS: tuple[str, ...] = ("block_time", "prev_event_time")
NUMERIC_AUDIT_COLUMNS: tuple[str, ...] = (
    "amount_in",
    "amount_out",
    "amount_usd",
    "fee_usd",
)
SENSITIVE_COLUMNS = frozenset({"wallet", "tx_hash", "token_in", "token_out"})
KNOWN_LABEL_NAMES = frozenset(
    {
        "label",
        "target",
        "is_wash_trade",
        "wash_trade",
        "is_fraud",
        "fraud_label",
        "risk_label",
    }
)
KNOWN_COUNTERPARTY_NAMES = frozenset(
    {
        "buyer",
        "seller",
        "buyer_wallet",
        "seller_wallet",
        "counterparty",
        "counterparty_wallet",
        "from_wallet",
        "to_wallet",
    }
)


class AuditError(RuntimeError):
    """Base exception for a user-actionable audit failure."""


class AuditValidationError(AuditError):
    """Raised when an input is present but unsuitable for this audit."""


def repository_root(start: Path | None = None) -> Path:
    """Return the project root by finding ``pyproject.toml`` from this module.

    Supplying ``start`` exists for focused tests; normal execution is independent of
    the caller's current working directory.
    """

    candidate = (start or Path(__file__)).resolve()
    if candidate.is_file():
        candidate = candidate.parent
    for directory in (candidate, *candidate.parents):
        if (directory / "pyproject.toml").is_file():
            return directory
    raise AuditValidationError("Could not locate repository root (pyproject.toml).")


def default_input_path() -> Path:
    """Return the mandated root-level dataset path."""

    return repository_root() / "nft.csv"


def default_output_path() -> Path:
    """Return the Git-ignored local report directory."""

    return repository_root() / "reports" / "data_audit"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _redact(value: Any) -> str:
    text = str(value)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    return f"sha256:{digest}"


def _json_value(value: Any) -> Any:
    """Convert pandas/numpy scalars into strict JSON-compatible values."""

    if value is None or value is pd.NA:
        return None
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _sample_values(series: pd.Series, *, redact: bool) -> list[Any]:
    values = series.dropna().drop_duplicates().head(3).tolist()
    return [_redact(value) if redact else _json_value(value) for value in values]


def _counts(series: pd.Series, *, redact: bool = False, limit: int = 20) -> list[dict[str, Any]]:
    materialized = series.dropna().astype("string")
    if materialized.empty:
        return []
    counts = materialized.value_counts(dropna=True).rename_axis("value").reset_index(name="count")
    counts["sort_value"] = counts["value"].astype(str)
    counts = counts.sort_values(["count", "sort_value"], ascending=[False, True], kind="stable")
    result: list[dict[str, Any]] = []
    for row in counts.head(limit).itertuples(index=False):
        label = _redact(row.value) if redact else str(row.value)
        result.append({"value": label, "count": int(row.count)})
    return result


def _numeric_summary(series: pd.Series) -> dict[str, Any]:
    numeric = pd.to_numeric(series, errors="coerce")
    supplied = series.notna()
    nonnumeric = int((supplied & numeric.isna()).sum())
    valid = numeric.dropna()
    base: dict[str, Any] = {
        "count": int(valid.size),
        "missing_count": int(series.isna().sum()),
        "nonnumeric_count": nonnumeric,
    }
    if valid.empty:
        return {**base, "statistics": None, "iqr_outliers": None}
    quantiles = valid.quantile([0.01, 0.05, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99])
    q1, q3 = float(quantiles.loc[0.25]), float(quantiles.loc[0.75])
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return {
        **base,
        "statistics": {
            "minimum": float(valid.min()),
            "p01": float(quantiles.loc[0.01]),
            "p05": float(quantiles.loc[0.05]),
            "p25": q1,
            "median": float(quantiles.loc[0.50]),
            "p75": q3,
            "p90": float(quantiles.loc[0.90]),
            "p95": float(quantiles.loc[0.95]),
            "p99": float(quantiles.loc[0.99]),
            "maximum": float(valid.max()),
            "mean": float(valid.mean()),
            "standard_deviation": float(valid.std()),
            "nonpositive_count": int((valid <= 0).sum()),
        },
        "iqr_outliers": {
            "lower_fence": lower,
            "upper_fence": upper,
            "count": int(((valid < lower) | (valid > upper)).sum()),
        },
    }


def _timestamp_format(value: Any) -> str:
    text = str(value).strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z", text):
        return "ISO-8601 UTC (Z)"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)? UTC", text):
        return "date time with UTC suffix"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?[+-]\d{2}:?\d{2}", text):
        return "ISO-8601 with offset"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?", text):
        return "ISO-like without timezone"
    return "other"


def _timestamp_summary(series: pd.Series) -> tuple[dict[str, Any], pd.Series]:
    nonmissing = series.dropna()
    parsed = pd.to_datetime(series, errors="coerce", utc=True, format="mixed")
    failures = int((series.notna() & parsed.isna()).sum())
    valid = parsed.dropna()
    formats = _counts(nonmissing.map(_timestamp_format), limit=20)
    return (
        {
            "supplied_count": int(nonmissing.size),
            "missing_count": int(series.isna().sum()),
            "parse_failure_count": failures,
            "observed_format_classes": formats,
            "minimum_utc": valid.min().isoformat() if not valid.empty else None,
            "maximum_utc": valid.max().isoformat() if not valid.empty else None,
        },
        parsed,
    )


def _identifier_quality(frame: pd.DataFrame, column: str) -> dict[str, Any]:
    series = frame[column]
    text = series.dropna().astype("string")
    result: dict[str, Any] = {
        "missing_count": int(series.isna().sum()),
        "blank_count": int(text.str.strip().eq("").sum()),
        "surrounding_whitespace_count": int(text.ne(text.str.strip()).sum()),
        "unique_nonmissing_count": int(text.nunique()),
    }
    if column == "wallet":
        valid_base58 = text.str.fullmatch(r"[1-9A-HJ-NP-Za-km-z]{32,44}", na=False)
        result["invalid_solana_base58_length_or_charset_count"] = int((~valid_base58).sum())
    return result


def _temporal_readiness(frame: pd.DataFrame, parsed_time: pd.Series) -> dict[str, Any]:
    valid = frame.loc[parsed_time.notna(), ["wallet"]].copy()
    valid["month"] = parsed_time.loc[parsed_time.notna()].dt.strftime("%Y-%m").values
    valid = valid.loc[valid["wallet"].notna()]
    months = sorted(valid["month"].unique().tolist())
    wallet_sets = {
        month: set(valid.loc[valid["month"] == month, "wallet"].astype(str)) for month in months
    }
    coverage = [
        {
            "month": month,
            "event_count": int((valid["month"] == month).sum()),
            "active_wallet_count": len(wallet_sets[month]),
        }
        for month in months
    ]
    consecutive = []
    for prior, current in zip(months, months[1:]):
        overlap = wallet_sets[prior] & wallet_sets[current]
        consecutive.append(
            {
                "prior_month": prior,
                "current_month": current,
                "wallet_overlap_count": len(overlap),
            }
        )
    cutoffs = []
    historical: set[str] = set()
    for month in months:
        active = wallet_sets[month]
        with_history = active & historical
        cutoffs.append(
            {
                "month": month,
                "active_wallet_count": len(active),
                "wallets_with_prior_history": len(with_history),
                "new_wallets_without_prior_history": len(active - historical),
                "prior_history_percentage": (100.0 * len(with_history) / len(active)) if active else 0.0,
            }
        )
        historical |= active
    wallet_months = valid.groupby("wallet", dropna=True)["month"].nunique()
    return {
        "calendar_month_coverage": coverage,
        "consecutive_month_wallet_overlap": consecutive,
        "wallet_month_presence": {
            "wallets_in_one_month_only": int((wallet_months == 1).sum()),
            "wallets_in_multiple_months": int((wallet_months > 1).sum()),
            "maximum_months_for_one_wallet": int(wallet_months.max()) if not wallet_months.empty else 0,
        },
        "history_before_monthly_cutoff": cutoffs,
    }


def _load_input(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise AuditValidationError(f"Input does not exist: {path}")
    if not path.is_file():
        raise AuditValidationError(f"Input is not a regular file: {path}")
    if path.stat().st_size == 0:
        raise AuditValidationError(f"Input CSV is empty: {path}")
    try:
        frame = pd.read_csv(
            path,
            na_values=["<nil>"],
            keep_default_na=True,
            low_memory=False,
            on_bad_lines="error",
        )
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError, OSError) as exc:
        raise AuditValidationError(f"Could not parse input CSV {path}: {exc}") from exc
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise AuditValidationError("Input is missing required fields: " + ", ".join(missing))
    if frame.empty:
        raise AuditValidationError(f"Input CSV contains a header but no data rows: {path}")
    return frame


def audit_dataset(input_path: Path | str) -> dict[str, Any]:
    """Audit one CSV without changing it and return a deterministic summary."""

    path = Path(input_path).expanduser().resolve()
    frame = _load_input(path)
    row_count = len(frame)

    timestamp_summaries: dict[str, Any] = {}
    parsed_times: dict[str, pd.Series] = {}
    for column in TIMESTAMP_COLUMNS:
        timestamp_summaries[column], parsed_times[column] = _timestamp_summary(frame[column])

    wallet_counts = frame["wallet"].value_counts(dropna=True)
    transaction_duplicates = frame["tx_hash"].duplicated(keep=False) & frame["tx_hash"].notna()
    instruction_columns = ["tx_hash", "outer_instruction_index", "inner_instruction_index"]
    complete_instruction_key = frame[instruction_columns].notna().all(axis=1)
    instruction_duplicates = frame.loc[complete_instruction_key, instruction_columns].duplicated(keep=False)

    schema = [
        {
            "name": column,
            "inferred_dtype": str(frame[column].dtype),
            "sample_values": _sample_values(frame[column], redact=column in SENSITIVE_COLUMNS),
        }
        for column in frame.columns
    ]
    missing_values = [
        {
            "column": column,
            "count": int(frame[column].isna().sum()),
            "percentage": 100.0 * float(frame[column].isna().sum()) / row_count,
        }
        for column in frame.columns
    ]

    source_week_expected = parsed_times["block_time"].dt.strftime("%G-W%V")
    source_week_comparable = frame["source_week"].notna() & source_week_expected.notna()
    source_week_mismatches = int(
        (frame.loc[source_week_comparable, "source_week"].astype(str) != source_week_expected[source_week_comparable]).sum()
    )
    prev_comparable = parsed_times["prev_event_time"].notna() & parsed_times["block_time"].notna()
    prev_after_current = int(
        (parsed_times["prev_event_time"][prev_comparable] > parsed_times["block_time"][prev_comparable]).sum()
    )
    computed_seconds = (
        parsed_times["block_time"] - parsed_times["prev_event_time"]
    ).dt.total_seconds()
    recorded_seconds = pd.to_numeric(frame["seconds_since_prev"], errors="coerce")
    gap_comparable = computed_seconds.notna() & recorded_seconds.notna()
    gap_mismatches = int(
        ((computed_seconds[gap_comparable] - recorded_seconds[gap_comparable]).abs() > 1e-6).sum()
    )

    label_columns = sorted(column for column in frame.columns if column.lower() in KNOWN_LABEL_NAMES)
    counterparty_columns = sorted(
        column for column in frame.columns if column.lower() in KNOWN_COUNTERPARTY_NAMES
    )
    likely_nft_columns = sorted(
        column for column in frame.columns if any(term in column.lower() for term in ("nft", "mint", "collection"))
    )

    summary: dict[str, Any] = {
        "audit_contract": {
            "phase": "Phase 1: inspection and data-quality audit only",
            "input_modified": False,
            "verified_observations_are_separate_from_interpretations": True,
        },
        "source": {
            "filename": path.name,
            "byte_size": path.stat().st_size,
            "sha256": _sha256(path),
        },
        "shape": {"rows": row_count, "columns": len(frame.columns)},
        "schema": schema,
        "missing_values": missing_values,
        "duplicates": {
            "exact_duplicate_rows_beyond_first": int(frame.duplicated().sum()),
            "exact_duplicate_rows_participating": int(frame.duplicated(keep=False).sum()),
            "duplicate_transaction_hash_occurrences_beyond_first": int(
                frame.loc[frame["tx_hash"].notna(), "tx_hash"].duplicated().sum()
            ),
            "rows_participating_in_duplicate_transaction_hashes": int(transaction_duplicates.sum()),
            "complete_instruction_key_rows": int(complete_instruction_key.sum()),
            "rows_participating_in_duplicate_instruction_keys": int(instruction_duplicates.sum()),
            "interpretation": (
                "Repeated transaction hashes or instruction keys are audited, not automatically removed; "
                "one transaction can legitimately contain multiple swap instructions."
            ),
        },
        "wallet_activity": {
            "unique_wallet_count": int(frame["wallet"].nunique(dropna=True)),
            "events_per_wallet": _numeric_summary(wallet_counts),
            "wallets_with_one_event": int((wallet_counts == 1).sum()),
            "maximum_events_for_one_wallet": int(wallet_counts.max()) if not wallet_counts.empty else 0,
            "wallet_identifiers_in_rankings": "redacted; aggregate statistics only",
        },
        "timestamps": timestamp_summaries,
        "temporal_readiness": _temporal_readiness(frame, parsed_times["block_time"]),
        "numeric_distributions": {
            column: _numeric_summary(frame[column]) for column in NUMERIC_AUDIT_COLUMNS
        },
        "categorical_distributions": {
            "dex": _counts(frame["dex"], limit=50),
            "source": _counts(frame["source"], limit=20),
            "token_pair": _counts(frame["token_pair"], limit=20),
            "token_in_redacted": _counts(frame["token_in"], redact=True, limit=20),
            "token_out_redacted": _counts(frame["token_out"], redact=True, limit=20),
        },
        "identifier_quality": {
            column: _identifier_quality(frame, column)
            for column in ("wallet", "tx_hash", "token_in", "token_out")
        },
        "derived_field_consistency": {
            "source_week_iso_week_comparable_rows": int(source_week_comparable.sum()),
            "source_week_does_not_match_iso_week_count": source_week_mismatches,
            "source_week_caution": (
                "The field's lineage and intended week convention are undocumented; an ISO-week comparison "
                "is a diagnostic, not proof that the supplied value is wrong."
            ),
            "previous_event_comparable_rows": int(prev_comparable.sum()),
            "previous_event_after_current_count": prev_after_current,
            "seconds_since_prev_comparable_rows": int(gap_comparable.sum()),
            "seconds_since_prev_mismatch_count": gap_mismatches,
        },
        "event_semantics": {
            "verified_columns_support": "DEX/swap event records",
            "evidence": [
                "dex, token_in, token_out, amount_in, amount_out, and source columns are present",
                "source values are audited as categorical evidence",
            ],
            "nft_specific_columns_found": likely_nft_columns,
            "interpretation": (
                "The filename alone is not evidence of NFT marketplace sales. "
                "No NFT-specific sale semantics are assumed."
            ),
        },
        "modelling_readiness": {
            "wash_trading_label_columns_found": label_columns,
            "counterparty_columns_found": counterparty_columns,
            "supervised_status": (
                "READY_FOR_LABEL_VALIDATION" if label_columns else "BLOCKED_NO_VERIFIED_WASH_TRADING_LABEL"
            ),
            "graph_feature_status": (
                "REQUIRES_EDGE_VALIDATION" if counterparty_columns else "BLOCKED_NO_WALLET_COUNTERPARTY_EDGES"
            ),
            "chronological_split_status": (
                "Event timestamps permit ordering, but sparse cross-month wallet history and absent labels "
                "prevent the proposed supervised evaluation."
            ),
            "prohibition": "No target, fraud behaviour, relationship, or probability is manufactured.",
        },
        "leakage_review": {
            "identifier_columns_not_features": ["wallet", "tx_hash"],
            "precomputed_temporal_columns_requiring_lineage_validation": [
                "prev_event_time",
                "seconds_since_prev",
                "source_week",
            ],
            "future_information_rule": "Future features must use only rows with block_time < as_of.",
            "warning": (
                "Precomputed temporal values cannot be trusted as point-in-time features until their "
                "construction and consistency are verified; fitted transforms must stay inside training folds."
            ),
        },
        "provenance_and_reproducibility_gaps": [
            "On-chain provider/API and exact extraction query are not documented.",
            "Collection method, creator, licence, and permitted reuse are not documented.",
            "Snapshot/version identifier and independent source checksum are not documented.",
            "Label definition, evidence source, review method, version, and knowledge timestamp are absent.",
        ],
        "proposal_comparison": {
            "verified_actual_row_count": row_count,
            "proposal_expected_approximate_row_count": 9000,
            "verified_actual_wallet_count": int(frame["wallet"].nunique(dropna=True)),
            "proposal_expected_wallet_count": 2312,
            "differences": [
                "The actual schema supports DEX/swap events rather than verified NFT marketplace sales.",
                "The actual row count differs from the proposal's approximate count.",
                "No proposed wash-trading flags/labels are present.",
                "No buyer/seller or wallet-counterparty relationship is present.",
            ],
        },
    }
    return _json_value(summary)


def _markdown_table(rows: Iterable[Sequence[Any]], headers: Sequence[str]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        safe = [str(value).replace("|", "\\|").replace("\n", " ") for value in row]
        lines.append("| " + " | ".join(safe) + " |")
    return lines


def render_markdown(summary: Mapping[str, Any]) -> str:
    """Render the deterministic JSON summary as a concise human report."""

    shape = summary["shape"]
    source = summary["source"]
    model = summary["modelling_readiness"]
    lines = [
        "# Dataset audit",
        "",
        "> Phase 1 inspection only. This report does not clean data, create labels, or confirm wash trading.",
        "",
        "## Input evidence",
        "",
        f"- File: `{source['filename']}`",
        f"- SHA-256: `{source['sha256']}`",
        f"- Size: {source['byte_size']} bytes",
        f"- Shape: {shape['rows']} rows × {shape['columns']} columns",
        "",
        "## Missingness",
        "",
    ]
    lines.extend(
        _markdown_table(
            ((row["column"], row["count"], f"{row['percentage']:.6f}%") for row in summary["missing_values"]),
            ("Column", "Missing", "Percentage"),
        )
    )
    lines.extend(["", "## Duplicate evidence", ""])
    duplicate_rows = [
        (key.replace("_", " "), value)
        for key, value in summary["duplicates"].items()
        if isinstance(value, int)
    ]
    lines.extend(_markdown_table(duplicate_rows, ("Measure", "Count")))
    lines.extend(["", "## Temporal coverage", ""])
    lines.extend(
        _markdown_table(
            (
                (row["month"], row["event_count"], row["active_wallet_count"])
                for row in summary["temporal_readiness"]["calendar_month_coverage"]
            ),
            ("Month", "Events", "Active wallets"),
        )
    )
    lines.extend(["", "## Volume distributions", ""])
    numeric_rows = []
    for column, details in summary["numeric_distributions"].items():
        stats = details["statistics"] or {}
        numeric_rows.append(
            (
                column,
                details["count"],
                stats.get("minimum"),
                stats.get("median"),
                stats.get("p95"),
                stats.get("maximum"),
                (details["iqr_outliers"] or {}).get("count"),
            )
        )
    lines.extend(
        _markdown_table(
            numeric_rows,
            ("Column", "Count", "Min", "Median", "P95", "Max", "IQR outliers"),
        )
    )
    lines.extend(
        [
            "",
            "## Semantics and readiness",
            "",
            f"- Verified event interpretation: **{summary['event_semantics']['verified_columns_support']}**.",
            f"- Unique wallets: {summary['wallet_activity']['unique_wallet_count']}.",
            f"- Supervised modelling: **{model['supervised_status']}**.",
            f"- Graph features: **{model['graph_feature_status']}**.",
            f"- Chronological readiness: {model['chronological_split_status']}",
            "- Wallet, transaction, and token samples/rankings are redacted where appropriate.",
            "",
            "## Provenance gaps",
            "",
        ]
    )
    lines.extend(f"- {gap}" for gap in summary["provenance_and_reproducibility_gaps"])
    lines.extend(["", "## Proposal differences", ""])
    lines.extend(f"- {difference}" for difference in summary["proposal_comparison"]["differences"])
    return "\n".join(lines) + "\n"


def write_reports(summary: Mapping[str, Any], output_dir: Path | str) -> tuple[Path, Path]:
    """Write deterministic JSON and Markdown reports outside the source dataset."""

    destination = Path(output_dir).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    json_path = destination / "audit.json"
    markdown_path = destination / "audit.md"
    json_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(summary), encoding="utf-8")
    return json_path, markdown_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=default_input_path(),
        help="CSV to audit (default: repository-root nft.csv)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_output_path(),
        help="Local directory for audit.json and audit.md",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = build_parser().parse_args(argv)
    try:
        LOGGER.info("Auditing %s", args.input)
        summary = audit_dataset(args.input)
        json_path, markdown_path = write_reports(summary, args.output_dir)
    except AuditError as exc:
        LOGGER.error("%s", exc)
        return 2
    except OSError as exc:
        LOGGER.error("Could not write audit reports: %s", exc)
        return 2
    LOGGER.info("Wrote %s", json_path)
    LOGGER.info("Wrote %s", markdown_path)
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through the CLI
    raise SystemExit(main())
