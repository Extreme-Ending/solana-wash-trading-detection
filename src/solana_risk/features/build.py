"""Build deterministic wallet snapshots from validated events strictly before cutoffs.

Each output row represents ``(wallet, as_of)``. Wallet and cutoff are metadata; the
registered feature columns describe only events with ``block_time < as_of``. This
module creates no targets, counterparty edges, fitted transforms, or model results.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from solana_risk.data.audit import repository_root

LOGGER = logging.getLogger(__name__)

FEATURE_RULES_VERSION = "1.0.0"
METADATA_COLUMNS: tuple[str, ...] = ("wallet", "as_of")
REQUIRED_EVENT_COLUMNS: tuple[str, ...] = (
    "source_row_number",
    "wallet",
    "block_time",
    "block_slot",
    "tx_hash",
    "dex",
    "token_pair",
    "token_in",
    "token_out",
    "amount_usd",
    "fee_usd",
    "outer_instruction_index",
    "inner_instruction_index",
)
FORBIDDEN_TARGET_COLUMNS = frozenset(
    {
        "label",
        "target",
        "is_wash_trade",
        "wash_trade",
        "is_fraud",
        "fraud_label",
        "risk_label",
        "wash_probability",
        "risk_score",
    }
)


class FeatureValidationError(ValueError):
    """Raised when cleaned events or a scoring cutoff violate the feature contract."""


@dataclass(frozen=True)
class FeatureDefinition:
    """Machine-readable definition and lineage for one model-candidate feature."""

    name: str
    category: str
    definition: str
    calculation: str
    units: str
    dtype: str
    missingness_policy: str
    lineage: tuple[str, ...]


FEATURE_REGISTRY: tuple[FeatureDefinition, ...] = (
    FeatureDefinition(
        "historical_event_count",
        "wallet_activity",
        "Number of retained wallet events observed before the cutoff.",
        "count(events where block_time < as_of)",
        "events",
        "integer",
        "Always present for emitted wallets; wallets with no observed event have no row.",
        ("wallet", "block_time"),
    ),
    FeatureDefinition(
        "unique_transaction_count",
        "wallet_activity",
        "Distinct transaction hashes observed before the cutoff.",
        "nunique(tx_hash)",
        "transactions",
        "integer",
        "Always present because validated events require a transaction hash.",
        ("wallet", "block_time", "tx_hash"),
    ),
    FeatureDefinition(
        "active_day_count",
        "wallet_activity",
        "Distinct UTC calendar days with at least one event.",
        "nunique(floor_utc_day(block_time))",
        "days",
        "integer",
        "Always at least one for emitted wallets.",
        ("wallet", "block_time"),
    ),
    FeatureDefinition(
        "events_per_active_day",
        "wallet_activity",
        "Average event count over observed active UTC days.",
        "historical_event_count / active_day_count",
        "events/day",
        "float",
        "Always present because active_day_count is positive.",
        ("wallet", "block_time"),
    ),
    FeatureDefinition(
        "observed_activity_duration_days",
        "wallet_activity",
        "Elapsed time between first and last observed event.",
        "(max(block_time) - min(block_time)) / 1 day",
        "days",
        "float",
        "Zero for a single-event wallet.",
        ("wallet", "block_time"),
    ),
    FeatureDefinition(
        "total_usd_volume",
        "trading_volume",
        "Sum of validated positive USD event amounts.",
        "sum(amount_usd)",
        "USD",
        "float",
        "Always present; Phase 2 quarantines missing or invalid required amounts.",
        ("wallet", "block_time", "amount_usd"),
    ),
    FeatureDefinition(
        "mean_usd_volume",
        "trading_volume",
        "Mean validated USD amount per event.",
        "mean(amount_usd)",
        "USD/event",
        "float",
        "Always present for emitted wallets.",
        ("wallet", "block_time", "amount_usd"),
    ),
    FeatureDefinition(
        "median_usd_volume",
        "trading_volume",
        "Median validated USD amount per event.",
        "median(amount_usd)",
        "USD/event",
        "float",
        "Always present for emitted wallets.",
        ("wallet", "block_time", "amount_usd"),
    ),
    FeatureDefinition(
        "max_usd_volume",
        "trading_volume",
        "Largest validated USD event amount.",
        "max(amount_usd)",
        "USD",
        "float",
        "Always present for emitted wallets; large values are not capped.",
        ("wallet", "block_time", "amount_usd"),
    ),
    FeatureDefinition(
        "std_usd_volume",
        "trading_volume",
        "Population standard deviation of validated USD event amounts.",
        "std(amount_usd, ddof=0)",
        "USD",
        "float",
        "Zero for a single event; no fitted scaling or imputation is applied.",
        ("wallet", "block_time", "amount_usd"),
    ),
    FeatureDefinition(
        "time_since_last_event_hours",
        "temporal_patterns",
        "Elapsed time from the latest strictly prior event to the cutoff.",
        "(as_of - max(block_time)) / 1 hour",
        "hours",
        "float",
        "Always positive for emitted wallets because cutoff equality is excluded.",
        ("wallet", "block_time", "as_of"),
    ),
    FeatureDefinition(
        "inter_event_mean_seconds",
        "temporal_patterns",
        "Mean gap between consecutive pre-cutoff wallet events.",
        "mean(diff(sorted block_time))",
        "seconds",
        "float",
        "Missing for a single-event wallet; not imputed.",
        ("wallet", "block_time"),
    ),
    FeatureDefinition(
        "inter_event_median_seconds",
        "temporal_patterns",
        "Median gap between consecutive pre-cutoff wallet events.",
        "median(diff(sorted block_time))",
        "seconds",
        "float",
        "Missing for a single-event wallet; not imputed.",
        ("wallet", "block_time"),
    ),
    FeatureDefinition(
        "inter_event_std_seconds",
        "temporal_patterns",
        "Population standard deviation of consecutive event gaps.",
        "std(diff(sorted block_time), ddof=0)",
        "seconds",
        "float",
        "Missing for a single-event wallet; zero when exactly one gap exists.",
        ("wallet", "block_time"),
    ),
    FeatureDefinition(
        "events_last_24h",
        "temporal_patterns",
        "Events in the closed-open 24-hour lookback window.",
        "count(as_of - 24h <= block_time < as_of)",
        "events",
        "integer",
        "Zero means no observed event in the available window, not guaranteed inactivity.",
        ("wallet", "block_time", "as_of"),
    ),
    FeatureDefinition(
        "events_last_7d",
        "temporal_patterns",
        "Events in the closed-open seven-day lookback window.",
        "count(as_of - 7d <= block_time < as_of)",
        "events",
        "integer",
        "Zero means no observed event in the available window, not guaranteed inactivity.",
        ("wallet", "block_time", "as_of"),
    ),
    FeatureDefinition(
        "events_last_30d",
        "temporal_patterns",
        "Events in the closed-open 30-day lookback window.",
        "count(as_of - 30d <= block_time < as_of)",
        "events",
        "integer",
        "Zero means no observed event in the available window, not guaranteed inactivity.",
        ("wallet", "block_time", "as_of"),
    ),
    FeatureDefinition(
        "unique_token_count",
        "token_and_dex",
        "Distinct validated token mints observed on either side of swaps.",
        "nunique(concat(token_in, token_out))",
        "tokens",
        "integer",
        "Always present because Phase 2 validates both token identifiers.",
        ("wallet", "block_time", "token_in", "token_out"),
    ),
    FeatureDefinition(
        "unique_token_pair_count",
        "token_and_dex",
        "Distinct nonmissing directional token-pair display labels.",
        "nunique(token_pair, drop missing)",
        "pairs",
        "integer",
        "Zero when all pair labels are unavailable; token mints remain authoritative.",
        ("wallet", "block_time", "token_pair"),
    ),
    FeatureDefinition(
        "unique_dex_count",
        "token_and_dex",
        "Distinct formatting-normalized DEX labels observed.",
        "nunique(dex)",
        "DEX labels",
        "integer",
        "Always present because Phase 2 requires a DEX value.",
        ("wallet", "block_time", "dex"),
    ),
    FeatureDefinition(
        "token_concentration",
        "token_and_dex",
        "Share of all token-side appearances belonging to the most frequent token.",
        "max(value_counts(token_in + token_out)) / (2 * historical_event_count)",
        "proportion [0,1]",
        "float",
        "Always present; token identities remain identifiers, not direct predictors.",
        ("wallet", "block_time", "token_in", "token_out"),
    ),
    FeatureDefinition(
        "dex_concentration",
        "token_and_dex",
        "Share of events routed through the most frequently observed DEX label.",
        "max(value_counts(dex)) / historical_event_count",
        "proportion [0,1]",
        "float",
        "Always present for emitted wallets.",
        ("wallet", "block_time", "dex"),
    ),
    FeatureDefinition(
        "missing_fee_proportion",
        "data_quality_and_history",
        "Fraction of historical events whose USD fee is unavailable.",
        "mean(is_missing(fee_usd))",
        "proportion [0,1]",
        "float",
        "Missing remains distinct from a valid zero fee.",
        ("wallet", "block_time", "fee_usd"),
    ),
    FeatureDefinition(
        "multi_instruction_transaction_count",
        "data_quality_and_history",
        "Distinct transaction hashes represented by more than one historical event.",
        "count(group_size(tx_hash) > 1)",
        "transactions",
        "integer",
        "Zero is valid; repeated hashes are not discarded as duplicate swaps.",
        ("wallet", "block_time", "tx_hash"),
    ),
    FeatureDefinition(
        "single_event_history",
        "data_quality_and_history",
        "Whether only one wallet event is observable before the cutoff.",
        "historical_event_count == 1",
        "indicator",
        "boolean",
        "Always present and explains unavailable inter-event statistics.",
        ("wallet", "block_time"),
    ),
    FeatureDefinition(
        "insufficient_history_7d",
        "data_quality_and_history",
        "Whether fewer than seven days separate first observation and cutoff.",
        "observable_history_days < 7",
        "indicator",
        "boolean",
        "Signals incomplete observable coverage; it does not prove wallet age.",
        ("wallet", "block_time", "as_of"),
    ),
    FeatureDefinition(
        "insufficient_history_30d",
        "data_quality_and_history",
        "Whether fewer than 30 days separate first observation and cutoff.",
        "observable_history_days < 30",
        "indicator",
        "boolean",
        "Signals incomplete observable coverage; it does not prove wallet age.",
        ("wallet", "block_time", "as_of"),
    ),
    FeatureDefinition(
        "observable_history_days",
        "data_quality_and_history",
        "Elapsed time from first observed event to cutoff.",
        "(as_of - min(block_time)) / 1 day",
        "days",
        "float",
        "A lower bound on observed history, not wallet lifetime or continuous coverage.",
        ("wallet", "block_time", "as_of"),
    ),
    FeatureDefinition(
        "history_coverage_30d_fraction",
        "data_quality_and_history",
        "Available observed-history fraction of a 30-day lookback.",
        "min(observable_history_days / 30, 1)",
        "proportion [0,1]",
        "float",
        "Distinguishes a fully observable 30-day window from a shorter observed span.",
        ("wallet", "block_time", "as_of"),
    ),
)

MODEL_FEATURE_COLUMNS: tuple[str, ...] = tuple(item.name for item in FEATURE_REGISTRY)


def default_input_path() -> Path:
    """Return the Phase 2 cleaned-event path."""

    return repository_root() / "data" / "processed" / "cleaned_events.csv"


def default_output_path() -> Path:
    """Return the Git-ignored wallet snapshot path."""

    return repository_root() / "data" / "features" / "wallet_snapshots.csv"


def default_report_path() -> Path:
    """Return the Git-ignored feature report directory."""

    return repository_root() / "reports" / "features"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def parse_as_of(value: str | pd.Timestamp) -> pd.Timestamp:
    """Parse a timezone-aware scoring timestamp and normalize it to UTC."""

    try:
        timestamp = pd.Timestamp(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise FeatureValidationError(f"Invalid scoring timestamp: {value!r}") from exc
    if pd.isna(timestamp):
        raise FeatureValidationError(f"Invalid scoring timestamp: {value!r}")
    if timestamp.tzinfo is None:
        raise FeatureValidationError(
            f"Scoring timestamp must include a timezone or Z suffix: {value!r}"
        )
    return timestamp.tz_convert("UTC")


def _canonical_cutoff(timestamp: pd.Timestamp) -> str:
    return timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def validate_events(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate the Phase 2 cleaned-event contract and return a typed copy."""

    forbidden = sorted(column for column in frame.columns if column.casefold() in FORBIDDEN_TARGET_COLUMNS)
    if forbidden:
        raise FeatureValidationError(
            "Cleaned events contain forbidden target-like columns: " + ", ".join(forbidden)
        )
    missing = [column for column in REQUIRED_EVENT_COLUMNS if column not in frame.columns]
    if missing:
        raise FeatureValidationError("Cleaned events are missing required fields: " + ", ".join(missing))
    events = frame.loc[:, REQUIRED_EVENT_COLUMNS].copy()
    if events.empty:
        raise FeatureValidationError("Cleaned event input contains no rows.")

    events["block_time"] = pd.to_datetime(events["block_time"], errors="coerce", utc=True)
    if events["block_time"].isna().any():
        raise FeatureValidationError("Cleaned events contain invalid block_time values.")
    for column in ("source_row_number", "block_slot", "outer_instruction_index", "inner_instruction_index"):
        events[column] = pd.to_numeric(events[column], errors="coerce").astype("Int64")
    if events["source_row_number"].isna().any() or events["block_slot"].isna().any():
        raise FeatureValidationError("Cleaned events contain invalid source-row or block-slot values.")
    events["amount_usd"] = pd.to_numeric(events["amount_usd"], errors="coerce")
    if events["amount_usd"].isna().any() or (~events["amount_usd"].map(math.isfinite)).any():
        raise FeatureValidationError("Cleaned events contain missing or nonfinite amount_usd values.")
    if events["amount_usd"].le(0).any():
        raise FeatureValidationError("Cleaned events contain nonpositive amount_usd values.")
    events["fee_usd"] = pd.to_numeric(events["fee_usd"], errors="coerce")
    for column in ("wallet", "tx_hash", "dex", "token_in", "token_out"):
        events[column] = events[column].astype("string").str.strip()
        if events[column].isna().any() or events[column].eq("").any():
            raise FeatureValidationError(f"Cleaned events contain missing {column} values.")
    events["token_pair"] = events["token_pair"].astype("string")
    return events.sort_values(
        [
            "block_time",
            "block_slot",
            "tx_hash",
            "outer_instruction_index",
            "inner_instruction_index",
            "source_row_number",
        ],
        kind="stable",
        na_position="last",
        ignore_index=True,
    )


def load_cleaned_events(
    input_path: Path | str,
    *,
    expected_sha256: str | None = None,
) -> pd.DataFrame:
    """Load and validate a Phase 2 cleaned-event CSV."""

    path = Path(input_path).expanduser().resolve()
    if not path.exists():
        raise FeatureValidationError(
            f"Cleaned event input does not exist: {path}. Run Phase 2 preprocessing first."
        )
    if not path.is_file():
        raise FeatureValidationError(f"Cleaned event input is not a regular file: {path}")
    observed_hash = _sha256(path)
    if expected_sha256 is not None and observed_hash != expected_sha256:
        raise FeatureValidationError(
            f"Cleaned event checksum mismatch: expected {expected_sha256}, observed {observed_hash}"
        )
    try:
        header = pd.read_csv(path, nrows=0).columns.tolist()
        forbidden = sorted(column for column in header if column.casefold() in FORBIDDEN_TARGET_COLUMNS)
        if forbidden:
            raise FeatureValidationError(
                "Cleaned event file contains forbidden target-like columns: " + ", ".join(forbidden)
            )
        frame = pd.read_csv(path, usecols=list(REQUIRED_EVENT_COLUMNS), low_memory=False)
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError, OSError, ValueError) as exc:
        if isinstance(exc, FeatureValidationError):
            raise
        raise FeatureValidationError(f"Could not load cleaned event CSV {path}: {exc}") from exc
    return validate_events(frame)


def load_default_cleaned_events() -> pd.DataFrame:
    """Load the default cleaned CSV and verify it against the Phase 2 report hash."""

    report_path = repository_root() / "reports" / "preprocessing" / "cleaning_report.json"
    if not report_path.is_file():
        raise FeatureValidationError(
            f"Phase 2 cleaning report is missing: {report_path}. Run preprocessing first."
        )
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        expected_hash = report["outputs"]["cleaned_sha256"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise FeatureValidationError(f"Invalid Phase 2 cleaning report: {report_path}") from exc
    return load_cleaned_events(default_input_path(), expected_sha256=expected_hash)


def _wallet_snapshot(group: pd.DataFrame, as_of: pd.Timestamp) -> dict[str, Any]:
    times = group["block_time"].sort_values(kind="stable")
    event_count = len(group)
    first_time = times.iloc[0]
    last_time = times.iloc[-1]
    gaps = times.diff().dropna().dt.total_seconds()
    active_days = int(times.dt.normalize().nunique())
    token_sides = pd.concat([group["token_in"], group["token_out"]], ignore_index=True)
    token_counts = token_sides.value_counts(dropna=True)
    dex_counts = group["dex"].value_counts(dropna=True)
    transaction_sizes = group.groupby("tx_hash", sort=False).size()
    observable_history_days = (as_of - first_time).total_seconds() / 86400.0
    return {
        "wallet": str(group["wallet"].iloc[0]),
        "as_of": _canonical_cutoff(as_of),
        "historical_event_count": event_count,
        "unique_transaction_count": int(group["tx_hash"].nunique()),
        "active_day_count": active_days,
        "events_per_active_day": event_count / active_days,
        "observed_activity_duration_days": (last_time - first_time).total_seconds() / 86400.0,
        "total_usd_volume": float(group["amount_usd"].sum()),
        "mean_usd_volume": float(group["amount_usd"].mean()),
        "median_usd_volume": float(group["amount_usd"].median()),
        "max_usd_volume": float(group["amount_usd"].max()),
        "std_usd_volume": float(group["amount_usd"].std(ddof=0)),
        "time_since_last_event_hours": (as_of - last_time).total_seconds() / 3600.0,
        "inter_event_mean_seconds": float(gaps.mean()) if not gaps.empty else None,
        "inter_event_median_seconds": float(gaps.median()) if not gaps.empty else None,
        "inter_event_std_seconds": float(gaps.std(ddof=0)) if not gaps.empty else None,
        "events_last_24h": int(times.ge(as_of - pd.Timedelta(hours=24)).sum()),
        "events_last_7d": int(times.ge(as_of - pd.Timedelta(days=7)).sum()),
        "events_last_30d": int(times.ge(as_of - pd.Timedelta(days=30)).sum()),
        "unique_token_count": int(token_sides.nunique()),
        "unique_token_pair_count": int(group["token_pair"].nunique(dropna=True)),
        "unique_dex_count": int(group["dex"].nunique()),
        "token_concentration": float(token_counts.iloc[0] / (2 * event_count)),
        "dex_concentration": float(dex_counts.iloc[0] / event_count),
        "missing_fee_proportion": float(group["fee_usd"].isna().mean()),
        "multi_instruction_transaction_count": int(transaction_sizes.gt(1).sum()),
        "single_event_history": event_count == 1,
        "insufficient_history_7d": observable_history_days < 7.0,
        "insufficient_history_30d": observable_history_days < 30.0,
        "observable_history_days": observable_history_days,
        "history_coverage_30d_fraction": min(observable_history_days / 30.0, 1.0),
    }


def build_wallet_snapshots(
    events: pd.DataFrame,
    as_of_values: Sequence[str | pd.Timestamp],
) -> pd.DataFrame:
    """Build one leakage-safe row per observed ``(wallet, as_of)``."""

    if not as_of_values:
        raise FeatureValidationError("At least one scoring timestamp is required.")
    validated = validate_events(events)
    cutoffs = sorted({parse_as_of(value) for value in as_of_values})
    rows: list[dict[str, Any]] = []
    for cutoff in cutoffs:
        history = validated.loc[validated["block_time"].lt(cutoff)]
        for _, group in history.groupby("wallet", sort=True, dropna=False):
            rows.append(_wallet_snapshot(group, cutoff))
    columns = [*METADATA_COLUMNS, *MODEL_FEATURE_COLUMNS]
    snapshots = pd.DataFrame(rows, columns=columns)
    if snapshots.empty:
        return snapshots
    return snapshots.sort_values(["as_of", "wallet"], kind="stable", ignore_index=True)


def feature_registry_records() -> list[dict[str, Any]]:
    """Return the registry as deterministic JSON-ready records."""

    return [_json_value(asdict(item)) for item in FEATURE_REGISTRY]


def feature_registry_sha256() -> str:
    payload = json.dumps(feature_registry_records(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _build_report(
    events: pd.DataFrame,
    snapshots: pd.DataFrame,
    cutoffs: Sequence[pd.Timestamp],
    input_path: Path,
) -> dict[str, Any]:
    cutoff_rows = []
    for cutoff in cutoffs:
        cutoff_text = _canonical_cutoff(cutoff)
        before = events["block_time"].lt(cutoff)
        cutoff_rows.append(
            {
                "as_of": cutoff_text,
                "historical_event_count": int(before.sum()),
                "excluded_event_at_or_after_count": int((~before).sum()),
                "wallet_snapshot_count": int(snapshots["as_of"].eq(cutoff_text).sum()),
            }
        )
    return {
        "rules_version": FEATURE_RULES_VERSION,
        "input": {
            "filename": input_path.name,
            "sha256": _sha256(input_path),
            "event_count": len(events),
            "wallet_count": int(events["wallet"].nunique()),
            "minimum_block_time_utc": events["block_time"].min().isoformat(),
            "maximum_block_time_utc": events["block_time"].max().isoformat(),
        },
        "temporal_contract": {
            "condition": "block_time < as_of",
            "window_condition": "as_of - window <= block_time < as_of",
            "wallet_without_prior_event": "No snapshot row is emitted; this is unavailable history, not observed inactivity.",
            "supplied_history_fields_used": False,
        },
        "cutoffs": cutoff_rows,
        "features": {
            "count": len(MODEL_FEATURE_COLUMNS),
            "names": list(MODEL_FEATURE_COLUMNS),
            "registry_sha256": feature_registry_sha256(),
            "metadata_columns": list(METADATA_COLUMNS),
        },
        "integrity": {
            "labels_created": False,
            "target_columns_in_features": False,
            "counterparty_edges_created": False,
            "dataset_wide_fitted_transforms": False,
            "wallet_identifiers_are_metadata": True,
            "supervised_status": "BLOCKED_NO_VERIFIED_WASH_TRADING_LABEL",
            "graph_status": "BLOCKED_NO_WALLET_COUNTERPARTY_EDGES",
        },
    }


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False, lineterminator="\n", float_format="%.17g")


def _markdown_table(rows: Sequence[Sequence[Any]], headers: Sequence[str]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        values = [str(value).replace("|", "\\|").replace("\n", " ") for value in row]
        lines.append("| " + " | ".join(values) + " |")
    return lines


def render_markdown(report: Mapping[str, Any]) -> str:
    """Render a concise deterministic feature summary."""

    lines = [
        "# Wallet feature summary",
        "",
        "> Behavioral descriptions only. No feature independently proves wash trading.",
        "",
        f"- Rules version: `{report['rules_version']}`",
        f"- Validated input events: {report['input']['event_count']}",
        f"- Input wallets: {report['input']['wallet_count']}",
        f"- Engineered features: {report['features']['count']}",
        f"- Temporal rule: `{report['temporal_contract']['condition']}`",
        "",
        "## Cutoff reconciliation",
        "",
    ]
    lines.extend(
        _markdown_table(
            [
                [
                    row["as_of"],
                    row["historical_event_count"],
                    row["excluded_event_at_or_after_count"],
                    row["wallet_snapshot_count"],
                ]
                for row in report["cutoffs"]
            ],
            ("As of", "Prior events", "Excluded events", "Wallet snapshots"),
        )
    )
    lines.extend(
        [
            "",
            "## Integrity gates",
            "",
            f"- Supervised modelling: **{report['integrity']['supervised_status']}**.",
            f"- Graph features: **{report['integrity']['graph_status']}**.",
            "- Wallet identifiers and scoring timestamps are metadata, not model features.",
            "- Supplied previous-event, gap, and source-week fields are not used.",
            "- No scaling, encoding, imputation, selection, resampling, label, or model is fitted.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(
    snapshots: pd.DataFrame,
    events: pd.DataFrame,
    cutoffs: Sequence[pd.Timestamp],
    input_path: Path | str,
    output_path: Path | str,
    report_dir: Path | str,
) -> dict[str, Path]:
    """Write deterministic feature CSV, JSON report, and Markdown summary."""

    source = Path(input_path).expanduser().resolve()
    output = Path(output_path).expanduser().resolve()
    reports = Path(report_dir).expanduser().resolve()
    if output == source:
        raise FeatureValidationError("Feature output cannot overwrite cleaned event input.")
    validated_events = validate_events(events)
    output.parent.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    _write_csv(snapshots, output)
    report = _build_report(validated_events, snapshots, cutoffs, source)
    report["output"] = {
        "filename": output.name,
        "sha256": _sha256(output),
        "row_count": len(snapshots),
    }
    json_path = reports / "feature_report.json"
    markdown_path = reports / "feature_summary.md"
    json_path.write_text(
        json.dumps(_json_value(report), indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    return {"snapshots": output, "json": json_path, "markdown": markdown_path}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--as-of",
        action="append",
        required=True,
        dest="as_of_values",
        help="Timezone-aware scoring cutoff; repeat for multiple snapshots",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=default_input_path(),
        help="Validated Phase 2 cleaned events CSV",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output_path(),
        help="Wallet snapshot CSV",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=default_report_path(),
        help="Directory for feature_report.json and feature_summary.md",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = build_parser().parse_args(argv)
    input_path = args.input.expanduser().resolve()
    try:
        cutoffs = sorted({parse_as_of(value) for value in args.as_of_values})
        events = (
            load_default_cleaned_events()
            if input_path == default_input_path().resolve()
            else load_cleaned_events(input_path)
        )
        snapshots = build_wallet_snapshots(events, cutoffs)
        paths = write_outputs(
            snapshots,
            events,
            cutoffs,
            input_path,
            args.output,
            args.report_dir,
        )
    except (FeatureValidationError, OSError) as exc:
        LOGGER.error("%s", exc)
        return 2
    LOGGER.info("Built %s wallet snapshots across %s cutoff(s)", len(snapshots), len(cutoffs))
    for name, path in paths.items():
        LOGGER.info("Wrote %s: %s", name, path)
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised by CLI tests
    raise SystemExit(main())
