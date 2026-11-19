# Phase 8D research evaluation evidence

## Claim boundary

The implemented system is an unsupervised wallet-anomaly research prototype over observed Solana DEX swap events. Its unit is `(wallet, as_of)`. A larger score means that the 29-feature snapshot is more unusual relative to the September 2025 training reference under one fitted Isolation Forest.

It does **not** demonstrate wash trading, fraud, intent, coordination, future offending, or a calibrated probability. There are no independently verified outcome labels. Therefore precision, recall, F1, false-positive rate, PR-AUC, MCC, confusion matrices and calibration are unavailable and must not be inferred.

## What the evidence supports

### 1. Software correctness

- Strict schema/order checks and target-like column rejection.
- Point-in-time features use `block_time < as_of`.
- Preprocessing, snapshot construction, training and scoring are deterministic in the audited environment.
- Imputation, LOF scaling, robust-MAD summaries and all feature-reference statistics are fitted on September training data only.
- The trusted loader validates bytes and metadata before deserialization.
- Single and batch Isolation Forest scores are exactly equal for the same histories/cutoff.
- Production refuses experimental scoring even if experimental paths are supplied.

### 2. Rank stability and anomaly sensitivity

The current evaluation rerun reports the following validation Spearman rank correlations against the primary Isolation Forest:

| Variation | Spearman correlation |
|---|---:|
| 100 trees | 0.994104 |
| 500 trees | 0.997970 |
| `max_samples=128` | 0.992826 |
| `max_samples=512` | 0.992334 |

LOF was less stable when its neighborhood changed: 15 neighbors produced 0.605186 and 70 produced 0.782718. On the December holdout, cross-model correlations were 0.048846 for Isolation Forest/LOF, 0.866200 for Isolation Forest/robust MAD and -0.018689 for LOF/robust MAD. At an arbitrary review budget of 10, the three pairwise top-list Jaccard values and three-way overlap were all zero.

This supports a narrow conclusion: the selected Isolation Forest ranking is stable to the tested internal tree/sample variations, while candidate lists are algorithm-dependent. It does not show which ranking is correct.

Controlled synthetic bursty/steady/sparse histories yield finite, deterministic values and correct rank mechanics. Those scenarios verify expected software sensitivity, not real-world wash-trading effectiveness.

### 3. Real-world effectiveness

Not established. No independent labels, adjudicated review outcomes, prospective intervention results or timestamped fraud evidence are available. Unusualness may reflect legitimate high volume, short observable history, new-wallet cohort shift, data quality or market regime.

## Temporal and leakage audit

| Risk | Finding |
|---|---|
| Future event leakage | Controlled: feature builder uses strict pre-cutoff events and tests exclude equal/post-cutoff events. |
| Preprocessing leakage | Controlled: model pipelines learn imputation and scaling on the earliest cutoff only. |
| Reference leakage | Controlled: `training_reference_v1` is built from the same 1,754 September snapshots only. |
| Synthetic/demo contamination | Controlled: demonstration events are request fixtures and are absent from the training snapshot. |
| Repeated-wallet leakage | Explicit limitation: all 1,754 training wallets recur at validation and holdout, so those full-period results are longitudinal rescoring diagnostics, not independent generalization. |
| Later-entrant shift | Explicit limitation: 176 October and 382 December entrants have shorter histories and different coverage. Wallet-disjoint does not make them exchangeable. |
| Threshold selection | No fraud threshold exists. Review budget is analyst capacity and changes only selected-for-review flags. |
| Feature/label circularity | No labels are fitted. Historical heuristic flags are not treated as ground truth. |

## Evaluation design and limitations

The fixed chronological partitions are:

- training: 1 September 2025, 1,754 wallets;
- exploratory validation: 1 October 2025, 1,930 wallets, including 176 later entrants;
- final temporal holdout: 1 December 2025, 2,312 wallets, including 382 later entrants relative to training.

The December holdout was used for the already-defined final descriptive report. Continued model/feature tuning against it would erode its holdout role. Future exploratory changes should introduce a new predeclared temporal evaluation plan or new data rather than repeatedly optimizing against December results.

The current model comparison is defensible as label-free descriptive evaluation because it reports distribution shift, coverage strata, rank correlations, top-K agreement, configuration sensitivity and controlled scenarios. It is insufficient for outcome effectiveness.

## Research readiness decision

**NO-GO for claims of wash-trading or fraud-detection effectiveness.**

**CONDITIONAL GO for a clearly labelled unsupervised anomaly-detection capstone demonstration**, subject to documenting extraction-time metadata and permitted use for confirmed Dune query 6561080, attaching primary proposal/rubric evidence, documenting the methodology authorization in a reviewable artifact, and restoring the required factual AI-use disclosure through a student-reviewed action.

The student has stated in conversation that the methodology was authorized, but no written approval artifact is present in this repository. This audit therefore records that repository evidence is unresolved; it does not contradict the student's statement or claim approval independently.
