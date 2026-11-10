# Phase 3 feature engineering findings

## Reproducible input and output

Phase 3 consumes only the checksum-verified Phase 2 table, `data/processed/cleaned_events.csv`. Its SHA-256 remains `1889adf72a727544a8759203336ac257108d344e2ea71aaa118aa04f0aa50937`; the immutable root `nft.csv` remains `8f387709c6742f2fc31c19fc32dac27474b6b27b9304786c367a8d8bece81271`.

The feature CLI used three explicit UTC scoring cutoffs and created 5,996 `(wallet, as_of)` rows with 29 registered features plus the two metadata fields. Generated CSV/JSON/Markdown artifacts are local and Git-ignored.

| Cutoff | Strictly prior events | Events excluded at/after cutoff | Wallet snapshots |
| --- | ---: | ---: | ---: |
| `2025-09-01T00:00:00Z` | 7,798 | 3,000 | 1,754 |
| `2025-10-01T00:00:00Z` | 8,798 | 2,000 | 1,930 |
| `2025-12-01T00:00:00Z` | 10,798 | 0 | 2,312 |

The generated snapshot SHA-256 is `779b446b15cce9cdc630353c60ffad2bfae039b086a1e0daa8dd66d05aff3a60`. The CLI report records the input/output hashes, rule and registry versions, cutoff reconciliation, and integrity gates without generation timestamps or absolute paths.

## Descriptive observations

- The median snapshot contains one historical event; the 90th percentile contains seven and the maximum contains 509. This is sparse, uneven behavioral evidence.
- 3,316 of 5,996 snapshots (55.30%) have only one observable event. Their three inter-event gap statistics correctly remain missing rather than being imputed.
- 103 snapshots (1.72%) expose fewer than seven days of observed history and 527 (8.79%) expose fewer than 30 days. These flags describe coverage, not wallet age.
- Median accumulated USD volume is approximately 21.96, the 90th percentile approximately 870.68, and the maximum approximately 606,984.60. Extreme values remain uncapped and are not treated as misconduct.
- Median token diversity is two and median DEX diversity is one. Concentration values are descriptive routing/composition summaries, not coordination evidence.
- Median 30-day event count is zero at the chosen cutoffs. This is consistent with the Phase 1 finding that 2,302 of 2,312 wallets appear in only one calendar month; it limits longitudinal inference.
- Median missing-fee proportion is one. Missing fees remain unavailable rather than being converted to zero.

These summaries pool multiple cutoff snapshots for descriptive inspection only. They are not an independent sample, training set, validation set, or performance claim.

## Leakage controls and tests

The module validates and sorts cleaned events, rejects target-like input columns, normalizes timezone-aware cutoffs to UTC, and filters with `block_time < as_of` before grouping. Window boundaries are closed-open. Tests cover an event exactly equal to a cutoff, future-event exclusion, multiple cutoffs, a single-event wallet, missing versus zero fees, incomplete history, repeated transaction hashes, window-boundary equality, invalid/naive cutoffs, registry completeness, deterministic bytes, CLI execution outside the repository, and the absence of target attributes.

Both notebooks were executed top-to-bottom with Jupyter in a clean temporary output location. The tracked notebooks contain no execution outputs or direct wallet, transaction, or token samples. `01_exploratory_data_analysis.ipynb` uses the Phase 1/2 modules; `02_feature_engineering.ipynb` imports the reusable Phase 3 module and demonstrates that building from all events is identical to building from an explicitly prefiltered historical table.

## Scientific blockers

- No independently verified wash-trading label, label definition, evidence source, knowledge timestamp, version, or review methodology is available.
- No buyer/seller or wallet-counterparty edge is present, so graph or coordinated-wallet claims remain blocked.
- Provider/API, extraction method, licence, source snapshot, and independent provenance remain unresolved.
- The filename does not establish NFT-sale semantics; the observed records remain DEX/swap events.
- The approved proposal and capstone-rubric PDFs are still absent from `references/`.
- `AI_USE.md` is absent by the student's explicit repository decision, despite the steering rubric identifying an AI-use statement as required submission evidence. This remains an academic documentation blocker until the student decides how to reconcile it.

Phase 3 creates no labels, target-dependent preprocessing, feature selection, model, metric, risk score, API, frontend, container, or cloud resource. Phase 4 remains gated on explicit student approval and verified labels.
