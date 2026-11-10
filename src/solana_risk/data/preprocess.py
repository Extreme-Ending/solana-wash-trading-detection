"""Deterministic Phase 2 validation and event-level preprocessing.

The source CSV is immutable. Invalid essential records and later exact copies are
written to quarantine with reasons; no evidence is silently discarded. This module
does not create labels, wallet-level features, fitted transforms, or graph edges.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .audit import AuditValidationError, REQUIRED_COLUMNS, default_input_path, repository_root

LOGGER = logging.getLogger(__name__)

PREPROCESSING_RULES_VERSION = "1.0.0"
EXPECTED_ROOT_SHA256 = "8f387709c6742f2fc31c19fc32dac27474b6b27b9304786c367a8d8bece81271"
MISSING_LITERALS = frozenset({"", "<nil>"})
BASE58_PATTERN = r"[1-9A-HJ-NP-Za-km-z]+"

REQUIRED_POSITIVE_NUMERIC_COLUMNS: tuple[str, ...] = (
    "amount_in",
    "amount_out",
    "amount_usd",
)
OPTIONAL_INDEX_COLUMNS: tuple[str, ...] = (
    "outer_instruction_index",
    "inner_instruction_index",
)


@dataclass(frozen=True)
class PreprocessingResult:
    """In-memory cleaned/quarantine tables and their deterministic report."""

    cleaned: pd.DataFrame
    quarantine: pd.DataFrame
    report: dict[str, Any]
    source_path: Path


def default_processed_path() -> Path:
    """Return the Git-ignored processed-data directory."""

    return repository_root() / "data" / "processed"


def default_report_path() -> Path:
    """Return the Git-ignored preprocessing-report directory."""

    return repository_root() / "reports" / "preprocessing"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _missing(series: pd.Series) -> pd.Series:
    text = series.astype("string")
    return text.isna() | text.str.strip().isin(MISSING_LITERALS)


def _clean_text(series: pd.Series) -> pd.Series:
    text = series.astype("string").str.strip()
    return text.mask(_missing(series), pd.NA)


def _json_value(value: Any) -> Any:
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


def _canonical_dex(value: Any) -> Any:
    if pd.isna(value):
        return pd.NA
    canonical = re.sub(r"[^a-z0-9]+", "_", str(value).strip().casefold()).strip("_")
    return canonical or pd.NA


def _canonical_timestamp(series: pd.Series) -> tuple[pd.Series, pd.Series]:
    parsed = pd.to_datetime(_clean_text(series), errors="coerce", utc=True, format="mixed")
    formatted = parsed.dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ").astype("string")
    return formatted.mask(parsed.isna(), pd.NA), parsed


def _content_hash(row: pd.Series) -> str:
    values = [str(row[column]) for column in REQUIRED_COLUMNS]
    payload = json.dumps(values, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _event_key_hash(row: pd.Series) -> str:
    if pd.notna(row["outer_instruction_index"]) and pd.notna(row["inner_instruction_index"]):
        identity = (
            f"instruction|{row['wallet']}|{row['tx_hash']}|{int(row['outer_instruction_index'])}|"
            f"{int(row['inner_instruction_index'])}"
        )
    else:
        identity = f"source-row|{row['source_record_hash']}|{int(row['source_row_number'])}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _load_source(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise AuditValidationError(f"Input does not exist: {path}")
    if not path.is_file():
        raise AuditValidationError(f"Input is not a regular file: {path}")
    if path.stat().st_size == 0:
        raise AuditValidationError(f"Input CSV is empty: {path}")
    try:
        frame = pd.read_csv(
            path,
            dtype="string",
            keep_default_na=False,
            na_filter=False,
            on_bad_lines="error",
        )
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError, OSError) as exc:
        raise AuditValidationError(f"Could not parse input CSV {path}: {exc}") from exc
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    unexpected = [column for column in frame.columns if column not in REQUIRED_COLUMNS]
    if missing or unexpected:
        details = []
        if missing:
            details.append("missing required fields: " + ", ".join(missing))
        if unexpected:
            details.append("unexpected fields: " + ", ".join(unexpected))
        raise AuditValidationError("Input schema mismatch; " + "; ".join(details))
    if frame.empty:
        raise AuditValidationError(f"Input CSV contains a header but no data rows: {path}")
    return frame.loc[:, REQUIRED_COLUMNS].copy()


def _add_reason(reasons: list[list[str]], mask: pd.Series, code: str) -> None:
    for position in mask[mask].index:
        reasons[int(position)].append(code)


def _numeric_column(
    raw: pd.Series,
    reasons: list[list[str]],
    name: str,
    *,
    missing_allowed: bool,
    positive: bool = False,
    nonnegative: bool = False,
    integral: bool = False,
) -> pd.Series:
    missing = _missing(raw)
    supplied = ~missing
    numeric = pd.to_numeric(_clean_text(raw), errors="coerce")
    finite = numeric.notna() & ~numeric.isin([float("inf"), float("-inf")])
    invalid = supplied & ~finite
    if not missing_allowed:
        _add_reason(reasons, missing, f"MISSING_{name.upper()}")
    _add_reason(reasons, invalid, f"INVALID_{name.upper()}")
    if integral:
        nonintegral = finite & numeric.mod(1).ne(0)
        _add_reason(reasons, nonintegral, f"NONINTEGER_{name.upper()}")
        invalid |= nonintegral
    if positive:
        nonpositive = finite & numeric.le(0)
        _add_reason(reasons, nonpositive, f"NONPOSITIVE_{name.upper()}")
    if nonnegative:
        negative = finite & numeric.lt(0)
        _add_reason(reasons, negative, f"NEGATIVE_{name.upper()}")
    numeric = numeric.mask(~finite | invalid, pd.NA)
    return numeric.astype("Int64" if integral else "Float64")


def _validate_identifier(
    series: pd.Series,
    reasons: list[list[str]],
    name: str,
    *,
    minimum_length: int,
    maximum_length: int,
) -> pd.Series:
    cleaned = _clean_text(series)
    missing = cleaned.isna()
    valid = cleaned.str.fullmatch(BASE58_PATTERN, na=False) & cleaned.str.len().between(
        minimum_length, maximum_length
    )
    _add_reason(reasons, missing, f"MISSING_{name.upper()}")
    _add_reason(reasons, ~missing & ~valid, f"INVALID_{name.upper()}")
    return cleaned


def _reason_counts(reasons: list[list[str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row_reasons in reasons:
        for reason in row_reasons:
            counts[reason] = counts.get(reason, 0) + 1
    return dict(sorted(counts.items()))


def preprocess_dataset(
    input_path: Path | str,
    *,
    expected_sha256: str | None = None,
) -> PreprocessingResult:
    """Validate, normalize, sort, and quarantine one event CSV deterministically."""

    path = Path(input_path).expanduser().resolve()
    source_hash = _sha256(path) if path.is_file() else None
    if expected_sha256 is not None and source_hash != expected_sha256:
        raise AuditValidationError(
            f"Input checksum mismatch: expected {expected_sha256}, observed {source_hash}"
        )
    raw = _load_source(path)
    row_count = len(raw)
    reasons: list[list[str]] = [[] for _ in range(row_count)]

    clean = pd.DataFrame(index=raw.index)
    clean["source_row_number"] = pd.Series(range(1, row_count + 1), dtype="Int64")
    clean["source_record_hash"] = raw.apply(_content_hash, axis=1).astype("string")
    for column in REQUIRED_COLUMNS:
        clean[f"raw__{column}"] = raw[column].astype("string")

    clean["wallet"] = _validate_identifier(
        raw["wallet"], reasons, "wallet", minimum_length=32, maximum_length=44
    )
    clean["tx_hash"] = _validate_identifier(
        raw["tx_hash"], reasons, "tx_hash", minimum_length=64, maximum_length=100
    )
    clean["token_in"] = _validate_identifier(
        raw["token_in"], reasons, "token_in", minimum_length=32, maximum_length=44
    )
    clean["token_out"] = _validate_identifier(
        raw["token_out"], reasons, "token_out", minimum_length=32, maximum_length=44
    )

    block_time_missing = _missing(raw["block_time"])
    clean["block_time"], parsed_block_time = _canonical_timestamp(raw["block_time"])
    _add_reason(reasons, block_time_missing, "MISSING_BLOCK_TIME")
    _add_reason(
        reasons,
        ~block_time_missing & parsed_block_time.isna(),
        "INVALID_BLOCK_TIME",
    )

    clean["block_slot"] = _numeric_column(
        raw["block_slot"], reasons, "block_slot", missing_allowed=False, nonnegative=True, integral=True
    )
    for column in REQUIRED_POSITIVE_NUMERIC_COLUMNS:
        clean[column] = _numeric_column(
            raw[column], reasons, column, missing_allowed=False, positive=True
        )
    clean["fee_usd"] = _numeric_column(
        raw["fee_usd"], reasons, "fee_usd", missing_allowed=True, nonnegative=True
    )
    for column in OPTIONAL_INDEX_COLUMNS:
        clean[column] = _numeric_column(
            raw[column], reasons, column, missing_allowed=True, nonnegative=True, integral=True
        )

    clean["dex"] = _clean_text(raw["dex"]).map(_canonical_dex).astype("string")
    clean["source"] = _clean_text(raw["source"]).str.casefold().astype("string")
    clean["token_pair"] = _clean_text(raw["token_pair"])
    for column in ("dex", "source"):
        missing = clean[column].isna()
        _add_reason(reasons, missing, f"MISSING_{column.upper()}")

    clean["prev_event_time"], parsed_previous_time = _canonical_timestamp(raw["prev_event_time"])
    supplied_seconds = ~_missing(raw["seconds_since_prev"])
    parsed_seconds = pd.to_numeric(_clean_text(raw["seconds_since_prev"]), errors="coerce")
    finite_seconds = parsed_seconds.notna() & ~parsed_seconds.isin([float("inf"), float("-inf")])
    clean["seconds_since_prev"] = parsed_seconds.mask(~finite_seconds, pd.NA).astype("Float64")
    clean["source_week"] = _clean_text(raw["source_week"])

    supplied_previous = ~_missing(raw["prev_event_time"])
    clean["provided_prev_event_time_invalid"] = supplied_previous & parsed_previous_time.isna()
    clean["provided_prev_event_time_after_event"] = (
        parsed_previous_time.notna()
        & parsed_block_time.notna()
        & parsed_previous_time.gt(parsed_block_time)
    )
    clean["provided_seconds_since_prev_invalid"] = supplied_seconds & ~finite_seconds
    clean["provided_seconds_since_prev_negative"] = clean["seconds_since_prev"].lt(0).fillna(False)
    clean["provided_history_fields_untrusted"] = True

    clean["fee_usd_missing"] = _missing(raw["fee_usd"])
    clean["token_pair_missing"] = _missing(raw["token_pair"])
    clean["instruction_index_missing"] = raw.loc[:, OPTIONAL_INDEX_COLUMNS].apply(_missing).any(axis=1)

    exact_duplicate = raw.duplicated(keep="first")
    _add_reason(reasons, exact_duplicate, "EXACT_DUPLICATE_AFTER_FIRST")
    clean["exact_duplicate_after_first"] = exact_duplicate

    reason_text = pd.Series(
        ["|".join(row_reasons) for row_reasons in reasons], index=raw.index, dtype="string"
    )
    quarantined_mask = reason_text.str.len().gt(0)
    retained_mask = ~quarantined_mask

    retained_tx = clean.loc[retained_mask, "tx_hash"]
    repeated_transactions = retained_tx.duplicated(keep=False) & retained_tx.notna()
    clean["repeated_transaction_hash"] = False
    clean.loc[repeated_transactions.index, "repeated_transaction_hash"] = repeated_transactions

    key_columns = ["wallet", "tx_hash", "outer_instruction_index", "inner_instruction_index"]
    complete_key = clean.loc[retained_mask, key_columns].notna().all(axis=1)
    complete_keys = clean.loc[retained_mask].loc[complete_key, key_columns]
    ambiguous_keys = complete_keys.duplicated(keep=False)
    clean["ambiguous_complete_instruction_key"] = False
    clean.loc[ambiguous_keys.index, "ambiguous_complete_instruction_key"] = ambiguous_keys

    valid_amounts = clean.loc[retained_mask, "amount_usd"].dropna()
    if valid_amounts.empty:
        lower_fence = upper_fence = None
        outlier_mask = pd.Series(False, index=clean.index)
    else:
        q1 = float(valid_amounts.quantile(0.25))
        q3 = float(valid_amounts.quantile(0.75))
        iqr = q3 - q1
        lower_fence = q1 - 1.5 * iqr
        upper_fence = q3 + 1.5 * iqr
        outlier_mask = clean["amount_usd"].lt(lower_fence) | clean["amount_usd"].gt(upper_fence)
        outlier_mask = outlier_mask.fillna(False) & retained_mask
    clean["review_amount_usd_iqr_outlier"] = outlier_mask
    clean["event_key_hash"] = clean.apply(_event_key_hash, axis=1).astype("string")
    clean["quarantine_reasons"] = reason_text

    sort_columns = [
        "block_time",
        "block_slot",
        "tx_hash",
        "outer_instruction_index",
        "inner_instruction_index",
        "source_row_number",
    ]
    cleaned = clean.loc[retained_mask].sort_values(
        sort_columns, kind="stable", na_position="last", ignore_index=True
    )
    quarantine = clean.loc[quarantined_mask].sort_values(
        ["source_row_number"], kind="stable", ignore_index=True
    )

    dex_mapping = (
        pd.DataFrame(
            {
                "raw": _clean_text(raw["dex"]),
                "canonical": clean["dex"],
            }
        )
        .drop_duplicates()
        .sort_values(["canonical", "raw"], kind="stable", na_position="last")
    )
    dex_mapping_records = [
        {"raw": _json_value(row.raw), "canonical": _json_value(row.canonical)}
        for row in dex_mapping.itertuples(index=False)
    ]

    warning_counts = {
        "fee_usd_missing": int(clean.loc[retained_mask, "fee_usd_missing"].sum()),
        "token_pair_missing": int(clean.loc[retained_mask, "token_pair_missing"].sum()),
        "instruction_index_missing": int(clean.loc[retained_mask, "instruction_index_missing"].sum()),
        "provided_prev_event_time_invalid": int(
            clean.loc[retained_mask, "provided_prev_event_time_invalid"].sum()
        ),
        "provided_prev_event_time_after_event": int(
            clean.loc[retained_mask, "provided_prev_event_time_after_event"].sum()
        ),
        "provided_seconds_since_prev_invalid": int(
            clean.loc[retained_mask, "provided_seconds_since_prev_invalid"].sum()
        ),
        "provided_seconds_since_prev_negative": int(
            clean.loc[retained_mask, "provided_seconds_since_prev_negative"].sum()
        ),
        "amount_usd_iqr_review_flags": int(outlier_mask.sum()),
    }
    report: dict[str, Any] = {
        "rules_version": PREPROCESSING_RULES_VERSION,
        "source": {
            "filename": path.name,
            "sha256": source_hash,
            "expected_sha256": expected_sha256,
            "checksum_verified": expected_sha256 is None or source_hash == expected_sha256,
        },
        "schema_validation": {
            "expected_columns": list(REQUIRED_COLUMNS),
            "observed_columns": list(raw.columns),
            "status": "PASS",
        },
        "row_reconciliation": {
            "input": row_count,
            "retained": int(retained_mask.sum()),
            "quarantined": int(quarantined_mask.sum()),
            "removed": 0,
            "reconciles": row_count
            == int(retained_mask.sum()) + int(quarantined_mask.sum()),
        },
        "quarantine_reason_counts": _reason_counts(reasons),
        "warning_counts_retained": warning_counts,
        "duplicates": {
            "exact_duplicate_rows_after_first": int(exact_duplicate.sum()),
            "rows_with_repeated_transaction_hashes_retained": int(
                clean.loc[retained_mask, "repeated_transaction_hash"].sum()
            ),
            "ambiguous_complete_instruction_key_rows_retained": int(
                clean.loc[retained_mask, "ambiguous_complete_instruction_key"].sum()
            ),
            "policy": (
                "Quarantine only later exact copies. Retain repeated transaction hashes and distinct "
                "instruction rows; flag complete-key collisions for review."
            ),
        },
        "missing_value_policy": {
            "fee_usd": (
                "Retain missing values as unavailable and add fee_usd_missing; no zero fill or "
                "statistical imputation."
            ),
            "token_pair": "Retain missing display labels and add token_pair_missing.",
            "instruction_indices": (
                "Retain missing indices and add instruction_index_missing; source-row identity is the "
                "event fallback."
            ),
            "essential_fields": "Quarantine missing or invalid essential identifiers, times, and amounts.",
        },
        "normalization": {
            "timestamps": "Parse with UTC and serialize as YYYY-MM-DDTHH:MM:SS.ffffffZ.",
            "dex_rule": (
                "Trim, case-fold, and replace formatting punctuation/whitespace with underscores; "
                "do not merge different resulting protocol names."
            ),
            "semantic_classification": (
                "Not performed; canonical labels standardize formatting only, and unfamiliar raw "
                "labels remain visible rather than being assigned to invented protocol families."
            ),
            "dex_mapping": dex_mapping_records,
            "tokens": "Trim and validate base58 identifiers; preserve case and never merge token identities.",
            "token_pair": "Trim only; preserve pair direction and raw value.",
        },
        "numeric_policy": {
            "amounts": "Quarantine nonnumeric, nonfinite, missing, or nonpositive required amounts.",
            "fee_usd": "Retain missing and zero fees; quarantine nonnumeric, nonfinite, or negative fees.",
            "amount_usd_iqr_review": {
                "lower_fence": lower_fence,
                "upper_fence": upper_fence,
                "retained_flag_count": int(outlier_mask.sum()),
                "action": "Retain unchanged; review-only flag is prohibited as a fitted model feature.",
            },
        },
        "ordering": {
            "columns": sort_columns,
            "tie_breaker": "source_row_number",
            "missing_instruction_indices": "sort last",
        },
        "traceability": {
            "source_row_number": "One-based data-row position in the source CSV.",
            "source_record_hash": "SHA-256 of the ordered original cell values.",
            "raw_columns_prefix": "raw__",
            "removed_rows_preserved": "All excluded rows are written to quarantine; removed is always zero.",
        },
        "modelling_integrity": {
            "labels_created": False,
            "counterparty_edges_created": False,
            "wallet_features_created": False,
            "fitted_imputation_scaling_or_encoding": False,
            "supplied_history_fields_trusted": False,
            "supervised_status": "BLOCKED_NO_VERIFIED_WASH_TRADING_LABEL",
            "graph_status": "BLOCKED_NO_WALLET_COUNTERPARTY_EDGES",
        },
    }
    return PreprocessingResult(
        cleaned=cleaned,
        quarantine=quarantine,
        report=_json_value(report),
        source_path=path,
    )


def _markdown_table(rows: Sequence[Sequence[Any]], headers: Sequence[str]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        values = [str(value).replace("|", "\\|").replace("\n", " ") for value in row]
        lines.append("| " + " | ".join(values) + " |")
    return lines


def render_markdown(report: Mapping[str, Any]) -> str:
    """Render a deterministic human-readable preprocessing summary."""

    rows = report["row_reconciliation"]
    lines = [
        "# Preprocessing summary",
        "",
        "> Phase 2 deterministic event cleaning only; no labels, features, models, or edges are created.",
        "",
        "## Source and reconciliation",
        "",
        f"- File: `{report['source']['filename']}`",
        f"- SHA-256: `{report['source']['sha256']}`",
        f"- Rules version: `{report['rules_version']}`",
        "",
    ]
    lines.extend(
        _markdown_table(
            [(rows["input"], rows["retained"], rows["quarantined"], rows["removed"], rows["reconciles"])],
            ("Input", "Retained", "Quarantined", "Removed", "Reconciles"),
        )
    )
    lines.extend(["", "## Quarantine reasons", ""])
    reason_rows = [[name, count] for name, count in report["quarantine_reason_counts"].items()]
    lines.extend(_markdown_table(reason_rows or [["None", 0]], ("Reason", "Rows")))
    lines.extend(["", "## Retained-row warnings", ""])
    warning_rows = [[name, count] for name, count in report["warning_counts_retained"].items()]
    lines.extend(_markdown_table(warning_rows, ("Warning", "Rows")))
    lines.extend(
        [
            "",
            "## Policies",
            "",
            f"- Duplicates: {report['duplicates']['policy']}",
            f"- Missing fees: {report['missing_value_policy']['fee_usd']}",
            f"- DEX normalization: {report['normalization']['dex_rule']}",
            f"- Amounts: {report['numeric_policy']['amounts']}",
            f"- Ordering: `{', '.join(report['ordering']['columns'])}`; final tie-breaker is source row.",
            "- Supplied previous-event, gap, and source-week fields remain untrusted and are not recomputed into features.",
            "- Every source field is retained under the `raw__` prefix.",
            "",
            "## Readiness",
            "",
            f"- Supervised modelling: **{report['modelling_integrity']['supervised_status']}**.",
            f"- Graph features: **{report['modelling_integrity']['graph_status']}**.",
        ]
    )
    return "\n".join(lines) + "\n"


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False, lineterminator="\n", float_format="%.17g")


def write_outputs(
    result: PreprocessingResult,
    processed_dir: Path | str,
    report_dir: Path | str,
) -> dict[str, Path]:
    """Write cleaned, quarantine, JSON, and Markdown artifacts deterministically."""

    processed = Path(processed_dir).expanduser().resolve()
    reports = Path(report_dir).expanduser().resolve()
    processed.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    paths = {
        "cleaned": processed / "cleaned_events.csv",
        "quarantine": processed / "quarantined_events.csv",
        "json": reports / "cleaning_report.json",
        "markdown": reports / "preprocessing_summary.md",
    }
    if result.source_path in paths.values():
        raise AuditValidationError("An output path would overwrite the immutable source CSV.")
    _write_csv(result.cleaned, paths["cleaned"])
    _write_csv(result.quarantine, paths["quarantine"])
    report = dict(result.report)
    report["outputs"] = {
        "cleaned_filename": paths["cleaned"].name,
        "cleaned_sha256": _sha256(paths["cleaned"]),
        "quarantine_filename": paths["quarantine"].name,
        "quarantine_sha256": _sha256(paths["quarantine"]),
    }
    paths["json"].write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    paths["markdown"].write_text(render_markdown(report), encoding="utf-8")
    return paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=default_input_path(),
        help="CSV to preprocess (default: repository-root nft.csv)",
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=default_processed_path(),
        help="Directory for cleaned and quarantined event CSVs",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=default_report_path(),
        help="Directory for JSON and Markdown preprocessing reports",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = build_parser().parse_args(argv)
    input_path = args.input.expanduser().resolve()
    expected_hash = EXPECTED_ROOT_SHA256 if input_path == default_input_path().resolve() else None
    try:
        LOGGER.info("Preprocessing %s", input_path)
        result = preprocess_dataset(input_path, expected_sha256=expected_hash)
        paths = write_outputs(result, args.processed_dir, args.report_dir)
    except (AuditValidationError, OSError) as exc:
        LOGGER.error("%s", exc)
        return 2
    rows = result.report["row_reconciliation"]
    LOGGER.info(
        "Rows: input=%s retained=%s quarantined=%s removed=%s",
        rows["input"],
        rows["retained"],
        rows["quarantined"],
        rows["removed"],
    )
    for name, path in paths.items():
        LOGGER.info("Wrote %s: %s", name, path)
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised by CLI tests
    raise SystemExit(main())
