# Model training and evaluation

## Objective

The models rank wallet snapshots by statistical unusualness relative to an earlier reference cohort. They do not classify fraud and do not output calibrated probabilities. No verified fraud outcome is present in the data.

## Chronological design

| Role | Cutoff | Wallets | Later entrants relative to training |
| --- | --- | ---: | ---: |
| Training reference | 2025-09-01 UTC | 1,754 | 0 |
| Exploratory validation | 2025-10-01 UTC | 1,930 | 176 |
| Descriptive holdout | 2025-12-01 UTC | 2,312 | 382 |

All 1,754 reference wallets occur in later cumulative snapshots. Full validation and holdout comparisons are therefore longitudinal, not identity-independent tests. Entrant-only analyses are wallet-disjoint but have shorter observed histories and different coverage.

The 29-feature order is fixed by `MODEL_FEATURE_COLUMNS`. Median imputation is learned only from training. LOF also uses a training-fitted `RobustScaler`. Identifiers and target-like fields are rejected.

## Algorithms

| Method | Primary configuration | Purpose |
| --- | --- | --- |
| Isolation Forest | 300 estimators, `max_samples=256`, `contamination="auto"`, `max_features=1.0`, seed 42 | Nonlinear ranking and served application model |
| Local Outlier Factor | 35 neighbors, Minkowski distance with `p=2`, novelty mode, `contamination="auto"` | Local-density comparison on later observations |
| Robust MAD | clipped deviations at 25, constant penalty 10, root-mean-square aggregation | Transparent robust statistical baseline |

The `contamination="auto"` setting is an algorithm configuration. It does not estimate fraud prevalence.

## Comparison results

### Holdout rank agreement

| Pair | Spearman correlation |
| --- | ---: |
| Isolation Forest and robust MAD | 0.8662 |
| Isolation Forest and LOF | 0.0488 |
| LOF and robust MAD | -0.0187 |

The corresponding correlations for the 382 later entrants were approximately `0.773`, `0.225`, and `0.279`. These values measure detector agreement under cohort shift, not outcome validity.

### Validation sensitivity

| Alternative | Correlation with primary validation ranking |
| --- | ---: |
| Isolation Forest, 100 trees | 0.9938 |
| Isolation Forest, 500 trees | 0.9980 |
| Isolation Forest, `max_samples=128` | 0.9929 |
| Isolation Forest, `max_samples=512` | 0.9923 |
| LOF, 15 neighbors | 0.6052 |
| LOF, 70 neighbors | 0.7827 |

The holdout was not used to tune these alternatives.

### Review-budget agreement

| Holdout budget | All-three intersection |
| ---: | ---: |
| 10 | 0 |
| 25 | 0 |
| 50 | 3 |
| 100 | 7 |

Candidate intersections are not evidence of wrongdoing.

## Selected model

Isolation Forest is the served ranker because it was stable under the tested validation variations and showed strong rank agreement with robust MAD. LOF remains useful as a disagreement diagnostic but was more sensitive to neighborhood size and produced weak cross-method agreement.

The selected artifact records:

- exact feature order and feature-registry fingerprint
- training cutoff and snapshot checksum
- estimator parameters and random seed
- fitted preprocessing and reference summaries
- Python and package versions
- artifact and manifest checksums

FastAPI verifies these fields before loading the artifact. A score is unitless and model-specific. Higher values mean more unusual relative to the training reference only.

## Evaluation boundary

Precision, recall, accuracy, PR-AUC, MCC, calibration, and fraud-detection claims are not available because no independently verified outcome exists. Score distributions, rank correlations, parameter sensitivity, review-budget overlap, drift, coverage, and deterministic reruns are valid unsupervised diagnostics.

The application result is best used to prioritize manual investigation of supplied histories. It should not be used as a fraud verdict or enforcement decision.
