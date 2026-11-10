# Provisional anomaly-model comparison

> **PROVISIONAL — METHODOLOGY NOT YET SUPERVISOR-APPROVED**

All three methods are fitted on the 1 September 2025 reference only. Higher scores mean more unusual relative to that reference. The magnitudes have method-specific scales and are not probabilities.

| Method | Exact primary configuration | Preprocessing | Useful property | Main limitation observed |
|---|---|---|---|---|
| Isolation Forest | `n_estimators=300`, `max_samples=256`, `contamination="auto"`, `max_features=1.0`, `bootstrap=False`, `n_jobs=1`, `random_state=42` | Train-median imputation | Nonlinear tabular ranking; validation ranks were stable under tree/sample alternatives | Rankings can be driven by coverage and amount extremes; `contamination="auto"` is algorithmic and says nothing about prevalence |
| Local Outlier Factor | `n_neighbors=35`, `metric="minkowski"`, `p=2`, `contamination="auto"`, `novelty=True`, `n_jobs=1` | Train-median imputation and train-fitted `RobustScaler` | Contrasting local-density view and valid scoring of later observations | Strong neighbor sensitivity, weak cross-model/temporal rank agreement, and a very heavy score tail |
| Robust MAD baseline | `clip=25.0`, `constant_penalty=10.0`; root-mean-square of clipped feature deviations | Train-median imputation; train medians/MADs learned by detector | Transparent reference and safe zero-dispersion handling | Correlated features can be counted repeatedly; a single combined distance obscures feature-specific context |

## Comparative evidence

### Holdout rank agreement

| Pair | Spearman rank correlation |
|---|---:|
| Isolation Forest vs robust MAD | 0.866 |
| Isolation Forest vs LOF | 0.049 |
| LOF vs robust MAD | -0.019 |

For the 382 wallet-disjoint holdout entrants, the corresponding correlations are 0.773, 0.225 and 0.279. Entrants have materially shorter observed histories than the training population, so these numbers describe detector agreement under cohort shift rather than independent outcome validity.

### Validation-only parameter sensitivity

| Alternative | Rank correlation with primary validation score |
|---|---:|
| Isolation Forest, 100 trees | 0.994 |
| Isolation Forest, 500 trees | 0.998 |
| Isolation Forest, `max_samples=128` | 0.993 |
| Isolation Forest, `max_samples=512` | 0.992 |
| LOF, 15 neighbors | 0.605 |
| LOF, 70 neighbors | 0.783 |

The holdout was not used to choose these settings. The primary settings were declared in code, and the alternatives quantify sensitivity rather than optimize against an outcome.

### Review-budget agreement

| Holdout budget | All-three intersection | Isolation/LOF Jaccard | Isolation/MAD Jaccard | LOF/MAD Jaccard |
|---:|---:|---:|---:|---:|
| 10 | 0 | 0.000 | 0.000 | 0.000 |
| 25 | 0 | 0.042 | 0.087 | 0.000 |
| 50 | 3 | 0.053 | 0.149 | 0.064 |
| 100 | 7 | 0.042 | 0.198 | 0.087 |

These lists are unverified candidates for investigation. Neither intersection nor consensus is evidence of wash trading.

## LOF score distinction

With `novelty=True`, the fitted estimator exposes `negative_outlier_factor_` for the training observations and `score_samples` for unseen observations. The pipeline stores and reports the training intrinsic distribution separately. Validation and holdout use novelty scoring. The two quantities are not treated as interchangeable, and comparisons across time use the same novelty-mode scoring function.

## Provisional assessment

Isolation Forest is the most stable nonlinear experimental ranker in the tested range, and robust MAD is a valuable transparent comparator. Their agreement is descriptive only. LOF contributes a useful disagreement diagnostic but is not stable enough here to support a single operational ranking without further predeclared eligibility, dimensionality/redundancy treatment and supervisor-approved evaluation. No model is approved for deployment.
