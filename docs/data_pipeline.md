# Data pipeline and provenance

## Source

The dataset was obtained from Dune Analytics and exported as a private CSV. The repository does not record the exact Dune query URL or identifier, SQL, export method, extraction date, sampling procedure, licence, or redistribution permission. The source file therefore remains excluded from Git. Identifying Dune Analytics does not by itself establish reuse rights.

The verified local file is `nft.csv`, despite containing DEX swap fields rather than NFT marketplace events. Its SHA-256 is:

```text
8f387709c6742f2fc31c19fc32dac27474b6b27b9304786c367a8d8bece81271
```

## Audited data

| Property | Value |
| --- | ---: |
| Rows | 10,800 |
| Columns | 18 |
| Wallet identifiers | 2,312 |
| Transaction hashes | 9,221 |
| First event | 2025-01-01 00:42:47 UTC |
| Last event | 2025-11-30 23:16:57 UTC |

The schema contains wallet, block time, slot, transaction hash, DEX, token pair, token mints, input and output amounts, USD value, fee, instruction indices, source, and supplied history fields. Source values are `dex_trade` and `jupiter_swap`.

There are no verified fraud labels, NFT marketplace fields, buyer or seller fields, or direct counterparty-wallet edges.

## Audit

`solana_risk.data.audit` validates the explicit schema, UTC parsing, identifier contracts, missingness, duplicate structure, event grain, amounts, category consistency, and chronological coverage. It reads the source without modifying it and writes ignored reports under `reports/data_audit/`.

Important findings include:

- zero exact duplicate rows
- 1,579 repeated transaction-hash occurrences beyond the first, retained because a transaction can contain multiple instructions
- 7,303 missing fee values
- 2,322 missing supplied previous-event values and gaps
- 936 missing instruction-index pairs
- 39 missing token-pair display labels
- 1,099 high-USD IQR review flags, retained without capping

## Preprocessing

`solana_risk.data.preprocess` applies deterministic rules version `1.0.0`:

1. Require the audited 18-column schema and approved source checksum.
2. Preserve every original field under a `raw__` prefix and add stable source-row lineage.
3. Parse event times as UTC and sort stably by time, slot, transaction, instruction indices, and source row.
4. Validate required identifiers and positive finite amounts.
5. Keep missing fees missing and add explicit missingness indicators.
6. Normalize DEX formatting without merging differently named protocol variants.
7. Keep repeated transaction hashes and large-value review flags.
8. Quarantine unsupported records with reason codes rather than silently deleting them.

| Reconciliation | Rows |
| --- | ---: |
| Input | 10,800 |
| Retained | 10,798 |
| Quarantined | 2 |
| Permanently removed | 0 |

Both quarantined records have nonpositive required `amount_in` and `amount_usd` values. The pipeline does not infer why.

## Feature dataset

`solana_risk.features.build` creates cumulative wallet snapshots at three UTC cutoffs:

| Cutoff | Wallet snapshots |
| --- | ---: |
| 2025-09-01 | 1,754 |
| 2025-10-01 | 1,930 |
| 2025-12-01 | 2,312 |

Each row represents `(wallet, as_of)` and contains 29 registered features. Only events satisfying `block_time < as_of` contribute. The combined snapshot file has 5,996 rows. See the [feature registry](feature_registry.md).

## Generated outputs

The following outputs are local and Git-ignored:

- `reports/data_audit/audit.json`
- `reports/data_audit/audit.md`
- `data/processed/cleaned_events.csv`
- `data/processed/quarantined_events.csv`
- `reports/preprocessing/cleaning_report.json`
- `reports/preprocessing/preprocessing_summary.md`
- `data/features/wallet_snapshots.csv`
- feature-generation reports under `reports/`

## Provenance actions still required

The student should supply the Dune query URL or identifier, query SQL, export date and method, sampling rationale, licence, and written redistribution status if available. Until then, the file checksum proves local identity only, not origin completeness or public sharing permission.
