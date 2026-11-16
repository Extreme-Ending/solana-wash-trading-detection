# Phase 8E research evaluation

## Reproduction context

Phase 8E reran the registered evaluator against `data/features/wallet_snapshots.csv` and the current local experimental artifact. The artifact SHA-256 was `3e35561b0bf5db42c5b7146e7ff568e313be1beb1be724997356af45f5533035`; the manifest, snapshot and feature-registry fingerprints were also accepted by the evaluator. The training reference used 1,754 wallets at 2025-09-01 UTC with seed 42.

Reproduction command:

```bash
PYTHONPATH=src .venv/bin/python -m solana_risk.models.evaluate_anomaly \
  --input data/features/wallet_snapshots.csv \
  --artifact artifacts/experimental/anomaly_models.joblib \
  --report-dir /tmp/phase8e-evaluation
```

This is label-free evidence. No row was assigned a fraud outcome and no classification metric was calculated.

## Chronological cohorts

| Snapshot | Wallets | Training-wallet overlap | New relative to training |
|---|---:|---:|---:|
| 2025-09-01 reference | 1,754 | 1,754 | 0 |
| 2025-10-01 validation | 1,930 | 1,754 | 176 |
| 2025-12-01 holdout | 2,312 | 1,754 | 382 |

The full later snapshots are longitudinal. The new-wallet subsets are disjoint from training but have structurally shorter observed histories.

## Parameter sensitivity

Spearman correlation between validation rankings from the registered model and one-at-a-time alternatives was:

| Alternative | Spearman rho |
|---|---:|
| Isolation Forest, 100 trees | 0.9941 |
| Isolation Forest, 500 trees | 0.9980 |
| Isolation Forest, max samples 128 | 0.9928 |
| Isolation Forest, max samples 512 | 0.9923 |
| LOF, 15 neighbours | 0.6052 |
| LOF, 70 neighbours | 0.7827 |

Isolation Forest rankings were stable under these limited parameter changes. LOF neighbourhood changes were materially less stable. This is a bounded sensitivity study, not proof of optimal hyperparameters.

## Cross-detector agreement

Holdout rank correlations were 0.0488 for Isolation Forest versus LOF, 0.8662 for Isolation Forest versus robust MAD, and -0.0187 for LOF versus robust MAD. Within the 382 new-wallet subset they were 0.2251, 0.7729 and 0.2789 respectively.

The three detectors shared no wallet in all three holdout top-10 lists. At top 100, seven wallets were shared by all three; pairwise Jaccard values were 0.0417, 0.1976 and 0.0870. Consequently, a review candidate is strongly dependent on detector and budget. Agreement is not a proxy for correctness.

## Longitudinal rank stability

For the 1,754 repeated training wallets, Spearman correlation between reference and holdout ranks was 0.7502 for Isolation Forest, 0.2207 for LOF and 0.9635 for robust MAD. These values describe persistence while additional events accumulate; they are not independent generalisation metrics.

## Distribution and coverage sensitivity

Median Isolation Forest scores were 0.3517 on the reference snapshot, 0.3556 on validation and 0.3618 on holdout. New-wallet medians were higher: 0.4606 in validation and 0.4494 in holdout. Two new-wallet features exceeded the registered distribution-shift diagnostic threshold: `observable_history_days` at 1.152 training IQR and `time_since_last_event_hours` at 1.180 training IQR.

Descriptive holdout strata further show why coverage must accompany a score:

- 238 wallets with insufficient 30-day history had median Isolation Forest score 0.4818, versus 0.3560 for the other 2,074;
- 1,278 single-event wallets had median 0.3438, versus 0.4165 for the 1,034 multi-event wallets;
- the top 1% by total volume (24 wallets) had median 0.6474, versus 0.3617 elsewhere; and
- the top 1% by maximum single-event volume (24 wallets) had median 0.6245, versus 0.3617 elsewhere.

These are score/stratum associations. They are neither feature attributions nor evidence that volume or limited history causes anomalous behaviour.

## Synthetic demonstration validity

Synthetic and manually imported JSON cases are suitable for deterministic API, validation, authentication and UI tests. They can demonstrate how event histories become features and how experimental rankings are displayed. Because they are constructed and have no independent outcome, they must not appear in an empirical result table, confusion matrix or case-study claim about real wash trading.

## Evaluation conclusion

The evidence supports reproducibility, point-in-time construction, limited Isolation Forest parameter stability, and transparent detector/cohort sensitivity. It also demonstrates substantial algorithm dependence and coverage effects. Missing ground truth prevents model selection by effectiveness and prevents every classification or fraud claim. The experiment remains suitable for a local academic demonstration of anomaly-analysis methodology only.
