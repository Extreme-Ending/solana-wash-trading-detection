# Data pipeline and provenance

## Source

The dataset was extracted from [Dune Analytics query 6561080](https://dune.com/queries/6561080) in multiple batches of approximately 1,000 rows. The query was executed again after the original extraction, so its currently visible SQL should not be treated as a preserved snapshot of the extraction-time query.

| Provenance item | Verified evidence |
| --- | --- |
| Source | Dune Analytics query `6561080` |
| Extraction method | Multiple downloads of approximately 1,000 rows, combined as `nft.csv` |
| Preserved result | 10,800 records covering January through November 2025 |
| Local identity | Filename, byte size, schema, row counts, observation window, and SHA-256 are verified |
| Not archived | Exact historical SQL revision, execution identifiers, parameters, extraction timestamps, and original batch files |

No original batch CSV or JSON files remain in the repository. The final file provides evidence of 11 contiguous month-labelled blocks: January to March and May to November contain 1,000 rows each, while April contains 800. This does not establish the exact pagination, parameter, or execution sequence used during extraction.

The source file remains excluded from Git because public redistribution permission has not been established.

The verified local file is named `nft.csv` and contains DEX swap fields. Its SHA-256 is:

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
| File size | 4,195,387 bytes |

The schema contains wallet, block time, slot, transaction hash, DEX, token pair, token mints, input and output amounts, USD value, fee, instruction indices, source, and supplied history fields. Source values are `dex_trade` and `jupiter_swap`.

There are no verified fraud labels, buyer or seller fields, or direct counterparty-wallet edges.

## Batch and event-grain evidence

The stored row order has 11 contiguous `source_week` runs that correspond to calendar months, despite the field name. Ten runs contain 1,000 rows and April contains 800. The rows inside each run are not timestamp-sorted, and the original batch files are unavailable. Consequently, schema consistency and overlap at the original batch boundaries cannot be independently rechecked.

The combined file has zero exact duplicate rows. It has 1,579 repeated transaction-hash occurrences beyond the first and 263 repeated `(wallet, tx_hash, outer_instruction_index, inner_instruction_index)` occurrences. The 179 ambiguous instruction-key groups all contain different amounts, and 173 contain different token legs. Adding source, token mints, and input, output, and USD amounts distinguishes every row. The appropriate research grain is therefore the full observed swap leg, not transaction hash alone. Repeated hashes must not be deleted automatically.

The combined order is reproducible from the preserved CSV, but deterministic reconstruction of the original concatenation cannot be claimed without the batch files or their execution metadata. If the month batches came from separate executions, their source state may also have differed between requests.

## Reacquiring a result safely

[Dune result pagination](https://docs.dune.com/api-reference/executions/pagination) supports `limit` and `offset`, but a reproducible download should page one completed execution rather than repeatedly request whichever execution is currently latest. A reviewer with an authorized Dune account should:

1. Open query 6561080 and record its current full SQL, parameters, version, ordering, and latest completed execution ID.
2. Confirm that the SQL itself does not truncate the whole result with `LIMIT 1000`.
3. Retrieve the first page with `limit=1000`, record its `execution_id`, and follow `next_uri` or `next_offset` for that same execution until no next page remains.
4. Preserve the returned column order, concatenate pages in API order, and record page counts, row counts, UTC retrieval time, execution ID, and query revision.
5. Run the repository audit against the new file. Treat it as a new source version unless it matches the reference SHA-256 exactly.

Fetching result pages can consume Dune credits. Do not rerun the query or export pages solely to reproduce the historical checksum without the student's authorization. A current execution can legitimately differ as source tables and query revisions change.

The [query metadata endpoint](https://docs.dune.com/api-reference/queries/endpoint/read) does not execute the query. An authorized Analyst-plan account can retrieve the current title, owner, SQL, parameters, and version without printing the API key:

```bash
read -rsp "Dune API key: " DUNE_API_KEY
echo
curl --fail --silent --show-error \
  --header "X-DUNE-API-KEY: ${DUNE_API_KEY}" \
  https://api.dune.com/api/v1/query/6561080 \
  --output /tmp/dune-query-6561080.json
unset DUNE_API_KEY
jq '{query_id, name, owner, version, parameters, query_sql}' \
  /tmp/dune-query-6561080.json
```

Do not commit the API key. Review the returned SQL and Dune version history before treating current metadata as the extraction-time revision.

## Publication decision

The reference CSV is 4,195,387 bytes, below [GitHub's 100 MiB per-file enforcement limit](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github). Size is therefore not the blocker. [Dune's terms](https://dune.com/terms) do not by themselves establish that this exported result, including data supplied through curated or third-party tables, may be republished as a repository dataset.

Keep `nft.csv` ignored and use the restricted-reviewer handover until the student reviews applicable source-table terms and obtains a clear institutional or rights-holder decision permitting public redistribution. Citing the public query is appropriate; publishing the CSV is a separate decision.

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

If historical records are available, archive the exact SQL revision used for the 2025 extraction, source tables, parameters, ordering, any SQL `LIMIT`, execution identifiers, extraction timestamps, and batch procedure. The query's current SQL is not evidence of that historical state. The student should also confirm the applicable Dune terms, any source-table restrictions, and written redistribution status if available.

Until those items are recorded, the source identity is established but the historical extraction cannot be reconstructed exactly. The file checksum proves local identity, and the block analysis supports the reported batch pattern, but neither grants public redistribution permission.
