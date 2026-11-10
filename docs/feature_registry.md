# Point-in-time wallet feature registry

## Contract

Each output row is one `(wallet, as_of)` observation. `wallet` and `as_of` are metadata, not model features. A wallet is emitted only when at least one validated event satisfies the strict historical condition:

```text
block_time < as_of
```

Window counts use `as_of - window <= block_time < as_of`. All timestamps are UTC. The implementation recomputes history from validated `block_time`; supplied `prev_event_time`, `seconds_since_prev`, and `source_week` fields are not used. The registry is versioned as `1.0.0` in `src/solana_risk/features/build.py` and its generated SHA-256 is `75be47d7f875e2a04848d8b8b7931d7f90d7bbf3c5aa2b3476a827e09e2d4e8a`.

The 29 fields below describe observed behavior and data coverage. No field is a wash-trading label, probability, rule-based verdict, or proof of misconduct.

## Registered features

| Feature | Category | Definition | Calculation | Units | Missingness/coverage policy | Source lineage |
| --- | --- | --- | --- | --- | --- | --- |
| `historical_event_count` | wallet activity | Number of retained wallet events observed before the cutoff. | `count(events where block_time < as_of)` | events | Always present for emitted wallets; wallets with no observed event have no row. | `wallet, block_time` |
| `unique_transaction_count` | wallet activity | Distinct transaction hashes observed before the cutoff. | `nunique(tx_hash)` | transactions | Always present because validated events require a transaction hash. | `wallet, block_time, tx_hash` |
| `active_day_count` | wallet activity | Distinct UTC calendar days with at least one event. | `nunique(floor_utc_day(block_time))` | days | Always at least one for emitted wallets. | `wallet, block_time` |
| `events_per_active_day` | wallet activity | Average event count over observed active UTC days. | `historical_event_count / active_day_count` | events/day | Always present because `active_day_count` is positive. | `wallet, block_time` |
| `observed_activity_duration_days` | wallet activity | Elapsed time between first and last observed event. | `(max(block_time) - min(block_time)) / 1 day` | days | Zero for a single-event wallet. | `wallet, block_time` |
| `total_usd_volume` | trading volume | Sum of validated positive USD event amounts. | `sum(amount_usd)` | USD | Always present; Phase 2 quarantines missing or invalid required amounts. | `wallet, block_time, amount_usd` |
| `mean_usd_volume` | trading volume | Mean validated USD amount per event. | `mean(amount_usd)` | USD/event | Always present for emitted wallets. | `wallet, block_time, amount_usd` |
| `median_usd_volume` | trading volume | Median validated USD amount per event. | `median(amount_usd)` | USD/event | Always present for emitted wallets. | `wallet, block_time, amount_usd` |
| `max_usd_volume` | trading volume | Largest validated USD event amount. | `max(amount_usd)` | USD | Always present; large values are not capped. | `wallet, block_time, amount_usd` |
| `std_usd_volume` | trading volume | Population standard deviation of validated USD event amounts. | `std(amount_usd, ddof=0)` | USD | Zero for one event; no fitted scaling or imputation is applied. | `wallet, block_time, amount_usd` |
| `time_since_last_event_hours` | temporal patterns | Elapsed time from the latest strictly prior event to the cutoff. | `(as_of - max(block_time)) / 1 hour` | hours | Always positive because cutoff equality is excluded. | `wallet, block_time, as_of` |
| `inter_event_mean_seconds` | temporal patterns | Mean gap between consecutive pre-cutoff wallet events. | `mean(diff(sorted block_time))` | seconds | Missing for a single-event wallet; not imputed. | `wallet, block_time` |
| `inter_event_median_seconds` | temporal patterns | Median gap between consecutive pre-cutoff wallet events. | `median(diff(sorted block_time))` | seconds | Missing for a single-event wallet; not imputed. | `wallet, block_time` |
| `inter_event_std_seconds` | temporal patterns | Population standard deviation of consecutive event gaps. | `std(diff(sorted block_time), ddof=0)` | seconds | Missing for one event; zero when exactly one gap exists. | `wallet, block_time` |
| `events_last_24h` | temporal patterns | Events in the closed-open 24-hour lookback window. | `count(as_of - 24h <= block_time < as_of)` | events | Zero means no observed event in the available window, not guaranteed inactivity. | `wallet, block_time, as_of` |
| `events_last_7d` | temporal patterns | Events in the closed-open seven-day lookback window. | `count(as_of - 7d <= block_time < as_of)` | events | Zero means no observed event in the available window, not guaranteed inactivity. | `wallet, block_time, as_of` |
| `events_last_30d` | temporal patterns | Events in the closed-open 30-day lookback window. | `count(as_of - 30d <= block_time < as_of)` | events | Zero means no observed event in the available window, not guaranteed inactivity. | `wallet, block_time, as_of` |
| `unique_token_count` | token and DEX | Distinct validated token mints observed on either side of swaps. | `nunique(concat(token_in, token_out))` | tokens | Always present because Phase 2 validates both token identifiers. | `wallet, block_time, token_in, token_out` |
| `unique_token_pair_count` | token and DEX | Distinct nonmissing directional token-pair display labels. | `nunique(token_pair, drop missing)` | pairs | Zero when all pair labels are unavailable; token mints remain authoritative. | `wallet, block_time, token_pair` |
| `unique_dex_count` | token and DEX | Distinct formatting-normalized DEX labels observed. | `nunique(dex)` | DEX labels | Always present because Phase 2 requires a DEX value. | `wallet, block_time, dex` |
| `token_concentration` | token and DEX | Share of all token-side appearances belonging to the most frequent token. | `max(value_counts(token_in + token_out)) / (2 * historical_event_count)` | proportion [0,1] | Always present; token identities remain identifiers, not direct predictors. | `wallet, block_time, token_in, token_out` |
| `dex_concentration` | token and DEX | Share of events routed through the most frequent DEX label. | `max(value_counts(dex)) / historical_event_count` | proportion [0,1] | Always present for emitted wallets. | `wallet, block_time, dex` |
| `missing_fee_proportion` | data quality/history | Fraction of historical events whose USD fee is unavailable. | `mean(is_missing(fee_usd))` | proportion [0,1] | Missing remains distinct from a valid zero fee. | `wallet, block_time, fee_usd` |
| `multi_instruction_transaction_count` | data quality/history | Distinct transaction hashes represented by more than one historical event. | `count(group_size(tx_hash) > 1)` | transactions | Zero is valid; repeated hashes are not discarded as duplicate swaps. | `wallet, block_time, tx_hash` |
| `single_event_history` | data quality/history | Whether only one wallet event is observable before the cutoff. | `historical_event_count == 1` | indicator | Always present and explains unavailable inter-event statistics. | `wallet, block_time` |
| `insufficient_history_7d` | data quality/history | Whether fewer than seven days separate first observation and cutoff. | `observable_history_days < 7` | indicator | Signals incomplete observable coverage; it does not prove wallet age. | `wallet, block_time, as_of` |
| `insufficient_history_30d` | data quality/history | Whether fewer than 30 days separate first observation and cutoff. | `observable_history_days < 30` | indicator | Signals incomplete observable coverage; it does not prove wallet age. | `wallet, block_time, as_of` |
| `observable_history_days` | data quality/history | Elapsed time from first observed event to cutoff. | `(as_of - min(block_time)) / 1 day` | days | A lower bound on observed history, not wallet lifetime or continuous coverage. | `wallet, block_time, as_of` |
| `history_coverage_30d_fraction` | data quality/history | Available observed-history fraction of a 30-day lookback. | `min(observable_history_days / 30, 1)` | proportion [0,1] | Distinguishes a fully observable 30-day window from a shorter observed span. | `wallet, block_time, as_of` |

## Explicit exclusions

- Wallet, transaction, and token strings are not direct model features.
- No supplied history field, target, label, probability, graph edge, or counterparty inference is created.
- No imputation, scaling, encoding, resampling, selection, or model fitting occurs in Phase 3.
- Large values remain observable; any later learned transform must be fitted inside chronological training folds.
