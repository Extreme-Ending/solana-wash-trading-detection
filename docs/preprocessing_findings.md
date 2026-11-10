# Phase 2 preprocessing findings

## Boundary and reproducibility contract

Phase 2 applies deterministic event-level validation and cleaning to the one repository-root file `nft.csv`. Rules version `1.0.0` is implemented in `src/solana_risk/data/preprocess.py`. It reads no other research dataset and creates no wallet aggregate, label, graph edge, fitted statistical transform, model, API, or deployment asset.

The source SHA-256 was verified before and after preprocessing:

`8f387709c6742f2fc31c19fc32dac27474b6b27b9304786c367a8d8bece81271`

The default CLI fails if that root-file checksum differs. Every original cell value is preserved under a `raw__` column in generated local outputs. `source_row_number` records the one-based data-row position, and `source_record_hash` identifies the ordered original cell content.

## Row reconciliation

| Measure | Rows |
| --- | ---: |
| Input | 10,800 |
| Retained in cleaned events | 10,798 |
| Preserved in quarantine | 2 |
| Permanently removed | 0 |

The two quarantined rows are source rows 2,328 and 3,548. Both have `amount_in = 0` and `amount_usd = 0` while `amount_out = 0.000001`. They receive both `NONPOSITIVE_AMOUNT_IN` and `NONPOSITIVE_AMOUNT_USD`. The pipeline does not silently discard them or assert why the values are zero.

## Transformation rules and justification

### Schema, identity, and data types

- The input must contain exactly the 18 audited fields. Missing or unexpected fields cause a clear schema error rather than being guessed or silently passed into later phases.
- Wallets, transaction signatures, and token mints are stripped only at their boundaries and validated against conservative Solana base58 character/length contracts. Missing or malformed essential identifiers are quarantined; none is invented.
- `block_slot` and instruction indices are parsed as nullable integers. Amount and fee fields are parsed as nullable numeric values. Their original strings remain available under `raw__*`.
- Token identifiers retain case because base58 identity is case-sensitive. `token_pair` is trimmed only; pair direction is never reordered and missing display labels remain missing.

### UTC time and deterministic order

- `block_time` is parsed with explicit UTC semantics and serialized as `YYYY-MM-DDTHH:MM:SS.ffffffZ`. Missing or invalid event time is an essential-record quarantine reason.
- Retained events are sorted stably by `(block_time, block_slot, tx_hash, outer_instruction_index, inner_instruction_index, source_row_number)`, with missing instruction indices last. The final source-row key makes ties deterministic.
- Supplied `prev_event_time`, `seconds_since_prev`, and `source_week` remain traceable but are marked untrusted. Invalid, negative, or future-inconsistent supplied history is flagged rather than used to produce features.
- No wall-clock-dependent “future” rule is used. Temporal inconsistency means a supplied previous timestamp occurs after its own event. Future feature cutoffs remain a Phase 3 responsibility with the strict rule `block_time < as_of`.

### Missing values

- All **7,303** missing `fee_usd` values remain unavailable and receive `fee_usd_missing = True`. They are not replaced with zero because a missing fee and a valid zero fee have different meanings.
- All **39** missing `token_pair` display labels are retained with `token_pair_missing = True` because token mint identifiers are present.
- All **936** rows missing instruction indices are retained with `instruction_index_missing = True`; these are the `jupiter_swap` source rows. Source-row identity is used as the conservative fallback event identity.
- No statistical imputer, scaler, encoder, selector, or resampler is fitted in Phase 2. Such transforms must later be fitted inside training folds only.

Missingness-mechanism labels remain hypotheses, not facts. Fee absence plausibly depends on source/extraction coverage, but provider and extraction documentation are still missing, so MCAR, MAR, or MNAR is not asserted.

### Duplicate and transaction grain

- Later exact copies of all 18 raw source fields are quarantined as `EXACT_DUPLICATE_AFTER_FIRST`; the first copy remains in the cleaned events. The current root file has zero such rows.
- Repeated transaction hashes are not treated as duplicate events. After the two invalid rows are quarantined, **2,539 retained rows** participate in repeated transaction hashes.
- Complete `(wallet, tx_hash, outer_instruction_index, inner_instruction_index)` collisions are flagged for review and retained rather than silently deduplicated. The current root file has zero collisions among complete keys.
- Distinct instructions in the same transaction receive different event-key hashes and remain separate events.

The older local steering audit reported 263 repeated complete instruction keys, but direct recomputation on the approved 10,800-row file and checksum finds zero. The reproducible result from the current file takes precedence; the discrepancy is documented rather than hidden.

### DEX normalization

DEX labels are trimmed, case-folded, and have formatting punctuation or whitespace replaced by underscores. All raw strings remain available. This reduces 48 raw spellings to 41 formatting-normalized labels.

Only case variants collapse:

- `GoonFi` / `goonfi` → `goonfi`
- `HumidiFi` / `humidifi` → `humidifi`
- `Meteora` / `meteora` → `meteora`
- `PancakeSwap` / `pancakeswap` → `pancakeswap`
- `Phoenix` / `phoenix` → `phoenix`
- `SolFi` / `solfi` → `solfi`
- `ZeroFi` / `zerofi` → `zerofi`

Differently named variants remain distinct: for example, `raydium`, `raydium_amm`, `raydium_clmm`, and `raydium_cp` are not merged. Phase 2 does not assign unfamiliar names to invented protocol families.

### Numerical policy and review flags

- Required `amount_in`, `amount_out`, and `amount_usd` values must be present, finite, numeric, and strictly positive. Failures are quarantined with specific reasons.
- `fee_usd` may be missing or zero. A supplied fee must be finite, numeric, and nonnegative.
- The Phase 1 1.5-IQR diagnostic is reproduced as a review-only flag. **1,099 retained `amount_usd` values** exceed the upper diagnostic fence. They remain unchanged: no large trade is deleted, winsorized, capped, or declared erroneous.
- The IQR flag is calculated over the full descriptive dataset solely for review and is explicitly prohibited as a fitted model feature. Phase 3 must not use it to leak full-period distribution information.

## Generated local artifacts

- `data/processed/cleaned_events.csv`
- `data/processed/quarantined_events.csv`
- `reports/preprocessing/cleaning_report.json`
- `reports/preprocessing/preprocessing_summary.md`

Both directories are Git-ignored. The machine report records the source checksum, row reconciliation, validation reason counts, formatting mappings, rule version, ordering contract, modelling stop gates, and output checksums. It contains no generation timestamp or machine-specific absolute path, so reruns are byte-reproducible.

## Leakage and modelling integrity

- Raw wallet, transaction, token, source-record, and event-key identifiers are audit/join keys, not candidate predictors.
- Supplied history fields are not trusted, and no future-looking or wallet-level feature is created.
- The IQR review flag is descriptive quality-control evidence, not a model input.
- No wash-trading label, heuristic ground truth, counterparty relationship, fraud claim, score, probability, model result, or graph feature is created.

Supervised status remains `BLOCKED_NO_VERIFIED_WASH_TRADING_LABEL`. Graph status remains `BLOCKED_NO_WALLET_COUNTERPARTY_EDGES`.

## Alignment with the lecturer’s Lab 2

The implementation adapts the verified `notebook/lab2_solution.ipynb` at commit `1ad78cc1ccaa6aa92e081893e3ea0cd380a1f950`:

- cells 12–14 inspect missingness, duplicates, parsing, and validity before treatment;
- cell 22 removes exact copies, adapted here to quarantine later copies so source evidence remains inspectable;
- cells 24–26 parse amounts explicitly and report failures;
- cells 29–32 parse timestamps explicitly and check temporal validity;
- cell 36 preserves entity meaning during canonicalization; and
- cells 44–45 place fitted imputation/scaling/encoding inside later model folds, so Phase 2 does not fit them globally.

Unlike the lab’s synthetic labelled data, this source has no target. Unlike its exact-copy transaction IDs, repeated Solana transaction hashes can contain multiple legitimate instructions. Those differences require conservative retention and continued supervised blocking.

## Remaining problems before Phase 3

1. Provider/API, extraction query, collection method, licence, source snapshot, and independent provenance remain unresolved.
2. Verified wash-trading labels and their as-of knowledge timestamps remain absent.
3. Direct wallet-to-wallet counterparty edges remain absent.
4. The intended Phase 3 scoring cutoffs and observation windows require student approval and must account for almost nonexistent cross-month wallet overlap.
5. Phase 3 must recompute prior-event and gap features exclusively from cleaned events strictly before each `as_of`; supplied history fields and `source_week` must not be used as authoritative features.
6. Any future imputation, scaling, encoding, feature selection, or resampling must be fitted inside chronological training folds.

Phase 3 has not begun.
