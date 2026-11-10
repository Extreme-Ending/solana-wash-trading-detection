# Phase 1 data-audit findings

## Audit boundary

This is a tracked summary of the deterministic audit of the single repository-root file `nft.csv`. The generated JSON and Markdown reports are local, Git-ignored artifacts under `reports/data_audit/`. The audit did not read or combine `nft_trades.csv`, alter the input, clean values, engineer features, or infer labels or relationships.

The source file was verified before and after the audit with SHA-256:

`8f387709c6742f2fc31c19fc32dac27474b6b27b9304786c367a8d8bece81271`

## Verified observations

### Shape, event meaning, and identifiers

- The file has **10,800 rows and 18 columns** representing **2,312 unique wallets** and **9,221 unique transaction hashes**.
- The time range is **2025-01-01 00:42:47 UTC** through **2025-11-30 23:16:57 UTC**. All 10,800 `block_time` values parse successfully as UTC.
- The schema contains `dex`, `token_in`, `token_out`, `amount_in`, `amount_out`, `amount_usd`, and `source`. Source values are `dex_trade` (9,864 rows) and `jupiter_swap` (936 rows). These are direct indicators of DEX/swap events.
- No NFT, collection, marketplace buyer, or marketplace seller column exists. The filename is therefore not sufficient evidence that the observations are NFT sales.
- Wallet, transaction, and token identifiers have no missing, blank, or surrounding-whitespace values. All wallet values satisfy the audited Solana base58 length/character pattern.

### Missingness and duplicates

| Field | Missing | Percentage |
| --- | ---: | ---: |
| `fee_usd` | 7,303 | 67.620370% |
| `prev_event_time` | 2,322 | 21.500000% |
| `seconds_since_prev` | 2,322 | 21.500000% |
| `outer_instruction_index` | 936 | 8.666667% |
| `inner_instruction_index` | 936 | 8.666667% |
| `token_pair` | 39 | 0.361111% |

All other fields have zero parsed missing values. Missingness has not been classified as MCAR, MAR, or MNAR because that requires evidence about the data-generating and extraction processes; it must not be filled automatically.

There are **zero exact duplicate rows**. There are **1,579 repeated transaction-hash occurrences beyond the first**, involving 2,543 rows. Among the 9,864 rows with a complete `(tx_hash, outer_instruction_index, inner_instruction_index)` key, none shares that complete key. This supports treating repeated transaction hashes as possible multi-instruction swaps, not automatically deleting them as duplicate observations.

### Activity, time, and chronological readiness

Events per wallet are strongly concentrated: the median is 1, the 95th percentile is 14, the maximum is 509, and 1,277 wallets have one event.

| Month | Events | Active wallets |
| --- | ---: | ---: |
| 2025-01 | 1,000 | 294 |
| 2025-02 | 1,000 | 321 |
| 2025-03 | 1,000 | 320 |
| 2025-04 | 800 | 204 |
| 2025-05 | 1,000 | 128 |
| 2025-06 | 1,000 | 169 |
| 2025-07 | 1,000 | 205 |
| 2025-08 | 1,000 | 113 |
| 2025-09 | 1,000 | 176 |
| 2025-10 | 1,000 | 154 |
| 2025-11 | 1,000 | 238 |

Only **10 wallets occur in two calendar months**; **2,302 occur in exactly one**, and no wallet occurs in more than two. Consecutive-month overlap is zero for every adjacent pair. Before the October cohort, 10 active wallets have any prior-month history; every other monthly cohort has zero wallets with earlier history in this file. A chronological event split is mechanically possible, but the available data provides almost no repeated-wallet history across cutoffs and cannot currently evaluate the proposed labelled wallet-risk task.

### Amounts and category consistency

`amount_usd` has a minimum of 0, median of 16.025543, 95th percentile of 517.183399, 99th percentile of 2,008.098943, and maximum of 312,846.087263. The 1.5-IQR diagnostic flags 1,099 values; this is evidence of a heavy-tailed distribution, not proof that the values are errors. Two `amount_usd` values and two `amount_in` values are nonpositive. These rows require a Phase 2 policy supported by domain and extraction evidence rather than silent deletion.

DEX labels are not normalized: examples include `raydium` and `Raydium amm`, `meteora` and `Meteora`, and multiple named protocol variants. This is a categorical consistency issue to resolve explicitly in Phase 2, without merging genuinely different protocols merely because their names look similar.

The supplied `prev_event_time` never occurs after its current event for 8,478 comparable rows, and its recorded seconds gap matches the recomputed difference. All `source_week` values differ from an ISO year-week encoding, but the supplied format resembles a separate source convention and its lineage is undocumented. The ISO comparison is a diagnostic only, not evidence that the values are wrong.

## Label, graph, and leakage assessment

- No wash-trading label or target column exists. There is no verified positive/negative definition, evidence source, review procedure, version, or knowledge timestamp.
- No buyer/seller, sender/receiver, or wallet-counterparty column exists. Shared tokens, DEX labels, or transaction hashes do not establish wallet-to-wallet edges.
- `wallet` and `tx_hash` are identifiers, not candidate predictors.
- `prev_event_time`, `seconds_since_prev`, and `source_week` are precomputed fields whose construction must be documented and recomputed or validated using only information before `as_of`.
- Any future fitted imputer, scaler, encoder, selector, or resampler must be learned inside the training fold. Correlation alone cannot establish absence of leakage.

**Readiness conclusion:** supervised wash-trading classification is blocked. Graph-based coordination features are also blocked. No target, fraud status, graph edge, score, probability, metric, or claimed malicious wallet is created by this phase.

## Provenance and proposal differences

The local file checksum makes repeated local audits comparable, but it does not establish origin or lawful reuse. The on-chain provider/API, extraction query, collection method, creator, licence, permitted reuse, independent snapshot/version, and source-issued checksum remain undocumented.

Compared with the approved description available to the project:

- the actual row count is 10,800 rather than approximately 9,000;
- the wallet count matches the expected 2,312;
- the actual schema is DEX/swap-like rather than verified NFT marketplace trades;
- the proposed wash-trading flags are absent; and
- counterparty relationships needed for coordination graphs are absent.

These are dataset-to-proposal differences, not evidence that any row is fraudulent.

## Requirements before Phase 2

1. Preserve `nft.csv` unchanged and confirm its provider/API, extraction query, licence, collection method, snapshot/version, and chain context.
2. Define the event grain and decide how transaction/instruction identifiers determine distinct rows; do not drop repeated hashes by default.
3. Establish explicit, tested policies for timestamp parsing, missingness, nonpositive values, amount outliers, token-pair gaps, DEX naming, and source-specific instruction gaps.
4. Recompute or validate temporal lineage from sorted events and enforce `block_time < as_of` in all later features.
5. Obtain and validate independently sourced wallet-level labels with evidence and knowledge timestamps before any supervised training.
6. Obtain direct, time-bounded wallet-to-wallet edges before any graph or coordination claim.

Phase 2 has not begun. Every item above requires student review and explicit Phase 2 approval.
