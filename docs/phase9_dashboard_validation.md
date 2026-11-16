# Phase 9 dashboard validation

## Presentation assessment

The existing Phase 8C dashboard already provides the core academic walkthrough: feature preview, experimental single and batch scoring, score/rank charts, deterministic filters/sorts, full wallet detail, training-reference comparisons, rejected histories, warnings and explicit scientific boundaries.

Phase 9 made two minimal presentation corrections:

1. the overview no longer incorrectly says anomaly scoring is “not served”; it now states that checksum-pinned scoring exists only in the explicitly enabled authenticated local demonstration; and
2. a compact **Verified experimental snapshot** section separates actual observations, model outputs and synthetic examples.

No API contract, scoring calculation, rank, threshold, authentication rule or model artifact changed.

## Evidence displayed

The new panel records the fixed audited research snapshot:

- 10,800 source DEX/swap event rows;
- 10,798 retained and two quarantined rows;
- 2,312 wallet identifiers and 29 registered point-in-time features;
- 1,754 training-reference wallets at 1 September 2025;
- 2,312 holdout wallets, including 1,754 repeated and 382 later entrants;
- holdout Isolation Forest/LOF Spearman agreement `0.049`; and
- Isolation Forest/robust-MAD agreement `0.866`.

The panel calls these fixed local research values, not live blockchain statistics. If the research artifact or dataset changes, the panel and Phase 9 figure manifest must be reviewed together; it is not silently data-bound at runtime.

## Model-behaviour communication

| Dashboard element | Supported interpretation | Explicit exclusion |
|---|---|---|
| Ranked score bars | Relative order within the submitted scorable batch | Probability, severity or universal threshold |
| Score distribution | Shape/count of currently visible model outputs | Normal/fraud class distribution |
| Review budget | Analyst capacity applied to deterministic ranks | Learned decision threshold |
| Wallet detail | Actual feature values and history/coverage warnings | Confirmed case or wallet ownership |
| Median/IQR comparison | Descriptive distance from training aggregates | SHAP, feature contribution or causal explanation |
| Detector evidence panel | Rank agreement/disagreement on the fixed holdout | Which detector is correct |
| Synthetic examples | UI, schema and score-path demonstration | Independent validation or fraud evidence |

Isolation Forest has no faithful per-feature contribution in this implementation. Phase 9 therefore does not invent one. The dashboard retains the more limited, methodologically supported feature context and states that it is not attribution.

## Interaction and accessibility coverage

- Semantic headings, tables, status regions, labels and error messages remain accessible.
- Filters do not mutate original ranks or scores.
- Sorting remains deterministic with rank/wallet tie handling.
- Sparse/constant/binary/missing reference comparisons retain explicit states.
- Desktop/tablet/mobile layouts preserve one-column fallback and horizontal table scrolling.
- 401, 403, 413, 422, 429 and 503 paths remain represented through tested UI messaging.
- No event history or token is stored in browser persistence.

## Validation boundary

Vitest/jsdom validates DOM behavior, not pixel layout. The production build validates bundling. A headless local page can validate the unauthenticated shell and new evidence panel; it cannot validate an approved Google popup or protected request without real student-operated Firebase credentials. That live acceptance remains a presentation prerequisite, not a fabricated automated pass.
