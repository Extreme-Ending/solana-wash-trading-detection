# Experimental anomaly-modelling findings

> **PROVISIONAL — METHODOLOGY NOT YET SUPERVISOR-APPROVED**

## Scope and claim boundary

Phase 4B is a label-free experiment on the available Solana DEX swap-event data. It does not change the approved capstone title or the pending status of the proposed amendment. The fitted systems assign relative anomaly scores to `(wallet, as_of)` observations. They do not classify wash trading, estimate fraud likelihood, establish intent, identify coordination, or validate the historical heuristic flags.

## Reproducible input evidence

- Snapshot file: `data/features/wallet_snapshots.csv`
- Snapshot SHA-256: `779b446b15cce9cdc630353c60ffad2bfae039b086a1e0daa8dd66d05aff3a60`
- Feature-registry SHA-256: `75be47d7f875e2a04848d8b8b7931d7f90d7bbf3c5aa2b3476a827e09e2d4e8a`
- Shape: 5,996 rows and 29 registered model features plus `wallet` and `as_of` metadata
- Cutoffs: 1,754 rows at 1 September, 1,930 at 1 October, and 2,312 at 1 December 2025 UTC
- Missingness: 3,316 missing values in each inter-event statistic, explained by the same 3,316 single-event snapshots
- Nonfinite infinite values: zero
- Train-constant and train-all-missing features: zero
- Incomplete coverage: 527 snapshots expose fewer than 30 observed history days

The source snapshot and its 29 feature definitions were not changed. Wallet and cutoff metadata are excluded from the modelling matrix, and target-like fields are rejected before fitting.

The earliest-cutoff audit found 12 feature pairs with absolute Spearman correlation at least 0.95. These include related USD summaries, event count versus the single-event indicator, recency versus observable history, 30-day activity versus coverage indicators, token versus token-pair diversity, and DEX diversity versus concentration. The experiment retains the registered set so that model sensitivity to its documented redundancy remains visible; it does not imply that each field contributes independent evidence.

## Temporal design

The fixed design is:

| Role | Cutoff | Rows | Identity interpretation |
|---|---:|---:|---|
| Training reference | 2025-09-01 UTC | 1,754 | Fit all imputers, scaling and detectors here only |
| Exploratory validation | 2025-10-01 UTC | 1,930 | 1,754 repeated wallets plus 176 later entrants |
| Final holdout | 2025-12-01 UTC | 2,312 | 1,930 October wallets plus 382 later entrants |

The full validation and holdout sets are longitudinal rescoring diagnostics, not independent tests: all 1,754 training wallets recur at both dates and their cumulative histories overlap. The 176 and 382 later entrants are wallet-disjoint identity diagnostics, but they are not exchangeable with the training population. Their observable histories are shorter and their coverage regime differs. In the 382-wallet holdout entrant cohort, the median observable history is 25.98 days versus 160.07 days in training; the median `insufficient_history_30d` changes from false to true. This is cohort and coverage shift, not model performance evidence.

## Pipeline controls

Each model contains median imputation fitted only on the training reference. LOF additionally contains a train-fitted `RobustScaler`. Isolation Forest receives unscaled imputed values. The robust baseline learns its medians and MAD values from training after imputation. The code rejects all-missing training features, infinities, schema/order changes, extra target-like fields, duplicate snapshot keys and an incompatible artifact registry fingerprint.

The artifact bundle records the feature order, registry and snapshot hashes, cutoffs and overlap, parameters, random seed, preprocessing, Python/library versions and a sidecar artifact checksum. The generated bundle is local and Git-ignored. Its current checksum is `2d6f4ee9ed05f83588bd26019cd103d0d754cc878888a171a0d1505f974774a1`; regenerating the artifact may change serialized bytes across environments even when scores remain reproducible, so reload consistency is tested directly.

## Exploratory findings

### Score distributions and drift

All outputs use the same direction: larger means more unusual relative to the September reference. Scores are not comparable in magnitude across algorithms.

- Isolation Forest median score moves from 0.352 in training to 0.356 in validation and 0.362 in holdout.
- Robust MAD median score moves from 4.248 to 4.565 and 4.583.
- LOF novelty-mode median score moves from 1.104 to 1.135 and 1.261, but its extreme tail is very large and unstable; its holdout maximum is 11,259 while its median is 1.261.
- For repeated wallets from training to holdout, rank stability is 0.750 for Isolation Forest, 0.963 for robust MAD and 0.221 for LOF.

The holdout's overall median feature shifts are modest except for elapsed-time fields, which naturally advance in a cumulative history. The wallet-disjoint holdout entrants instead show substantial coverage shifts: absolute median shifts are 1.18 training IQRs for time since last event and 1.15 for observable history, while three coverage fields move away from train-constant medians. Consequently, higher entrant scores may reflect late observation and sparse evidence.

### Sparse histories and extreme amounts

The models react differently to limited history. On the holdout, single-event snapshots have lower median Isolation Forest and robust-MAD scores than multi-event histories, while LOF's distribution and extreme tail behave differently. Observations with fewer than 30 history days have materially higher median Isolation Forest and robust-MAD scores than better-covered observations. Coverage stratification is therefore mandatory; one combined anomaly rank would mix behaviour with observability.

The top 1% by total or maximum USD volume receives high Isolation Forest and robust-MAD scores. That is expected because the methods rank statistical extremeness. It is not evidence that high-volume trading is improper.

### Stability and review budgets

Isolation Forest is stable across the predeclared validation-only alternatives: rank correlations with the primary configuration are 0.992–0.998 when changing tree count or maximum sample size. LOF is more sensitive: changing 35 neighbors to 15 or 70 gives rank correlations of 0.605 and 0.783.

At a holdout review budget of 10, no observation appears in all three model lists and every pairwise Jaccard overlap is zero. At budget 100, only seven observations occur in all three lists; pairwise Jaccard overlap ranges from 0.042 to 0.198. These are unverified candidate-list comparisons. Agreement would not establish correctness, and disagreement shows that the operational review list depends strongly on detector choice.

## Scientific conclusion

The experiment demonstrates a reproducible way to rank unusual wallet snapshots relative to a historical reference and to audit sensitivity, drift and coverage. It does not demonstrate wash-trading detection. Isolation Forest and the robust baseline show comparatively stable and concordant ranks, while LOF is locally sensitive and has an unstable extreme tail on this feature space. No method is selected for production or promoted as the approved capstone methodology.

Stronger conclusions require written supervisor approval of the revised question and claim boundary, verified dataset provenance/licensing, predeclared wallet-history eligibility, an approved review-budget meaning, and—if outcome performance is to be claimed—independent timestamped outcome evidence kept outside feature construction and model selection.

Generated detailed evidence is written locally to `reports/modelling/anomaly_evaluation.json` and `reports/modelling/anomaly_evaluation.md`; both are Git-ignored.
