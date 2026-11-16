# Phase 8D data provenance and limitations

## Verified local evidence

The research input is the Git-ignored root file `nft.csv`, not an NFT transaction table merely because of its name. Direct inspection shows 10,800 rows and 18 fields describing Solana DEX/swap observations, including wallet, block time/slot, transaction hash, DEX, token pair, token in/out, USD amounts/fees, instruction indices, source and prior-event timing.

Observed identifiers:

- 2,312 distinct wallet strings;
- source SHA-256 `8f387709c6742f2fc31c19fc32dac27474b6b27b9304786c367a8d8bece81271`;
- deterministic preprocessing retains 10,798 rows and quarantines 2 invalid rows;
- no explicit verified target or adjudicated wash-trading outcome exists in the 18 columns.

`data/raw/nft_trades_t_sample.json` is a bounded local API input sample. It is not the primary dataset and must not be counted as a second research source.

## Proposal/data mismatch

The original capstone framing concerns coordinated NFT wash trading. The supplied schema has DEX, token and swap semantics and lacks NFT asset/collection, marketplace sale, buyer/seller and verified self-trade/counterparty evidence. It cannot substantiate NFT-sale claims or direct wallet coordination.

The earlier reference to 249 flagged wallets is not a verified target in the supplied CSV. Local documents indicate historical flags were behavioral heuristics rather than independent adjudication; the flag file, exact evidence timestamps, matching wallet universe and independently reviewed outcomes are unavailable. Those flags are not reconstructed or used as labels.

## Provenance status

| Question | Status |
|---|---|
| Exact upstream provider/API | Unresolved; local `source` values describe events but do not prove the external provider. |
| Collector/query and collection date | Unresolved. |
| Chain/domain | Solana DEX/swap semantics are supported by the observed schema; NFT-sale semantics are unsupported. |
| Dataset ownership and licence | Unresolved; no licence or permission artifact is present. |
| Source integrity | Locally pinned by SHA-256 and row/schema checks. |
| Label provenance | No independently verified label dataset is present. |
| Direct counterparty edges | Not present; transaction/token co-occurrence is not converted to wallet edges. |
| Primary proposal and rubric | `references/` is absent; only steering summaries and derived documents are locally available. |

Local integrity does not prove lawful provenance or permitted publication. The source CSV, cleaned data, reports containing row-level evidence and model artifacts remain ignored/private.

## Data and inference limitations

- Observation begins within a bounded extract, so `observable_history_days` is coverage, not wallet age.
- Cumulative snapshots repeat wallets and share historical events across dates.
- Late entrants have systematically shorter observed histories; anomaly ranks can reflect coverage.
- USD values are heavy-tailed. Extremeness is not wrongdoing.
- Missing fee values are measured rather than silently imputed during feature construction; model-pipeline imputation is training-only.
- Multiple instruction records can share a transaction hash and are not automatically duplicates.
- The system accepts user-supplied histories and does not verify them against an RPC/provider.
- No outcomes exist for estimating false positives, precision, recall or demographic/market fairness.
- No causal, graph-collusion or future-behavior conclusion follows from the current features.

## Academic compliance audit

- Lab traceability is documented and distinguishes adapted principles from copied assets. The implementation follows inspect-before-transform, fitted-pipeline, held-out evaluation, typed API and reproducible-delivery fundamentals while replacing random row splits with chronology appropriate to repeated wallets.
- No lecturer datasets, labels, artifacts or source files are copied into this repository.
- The steering contract requires a tracked, factual `AI_USE.md`. That file is absent after deliberate student removal. Phase 8D records the compliance gap and does not silently recreate it. The student should confirm the institution's required disclosure wording and restore a factual, reviewed file if required.
- The approved proposal/rubric primary documents are absent. They should be added only if the student has permission to include them, or evaluated privately and cited accurately.
- Written evidence of the methodology decision is absent locally. The student reports authorization, but this repository audit cannot independently verify it.

## Required resolution before research submission

1. Obtain a citable provider/source statement, collector/query description, collection window and licence/permitted-use evidence.
2. Add or privately verify the approved proposal and course rubric; reconcile the title/objective with the actual DEX anomaly methodology in the final report.
3. Retain the explicit statement that anomaly candidates are not confirmed fraud.
4. Record the methodology authorization in a student-approved form suitable for assessment evidence.
5. Resolve the factual AI-use disclosure requirement without concealing assistance.
