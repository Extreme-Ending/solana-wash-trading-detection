# Conditional modelling and evaluation plan

## Scope and gate

This plan defines what Phase 4B could do only after the Phase 4A evidence gate passes. No classifier, fitted preprocessing, resampling, threshold selection, probability, fraud verdict, SHAP explanation, or predictive performance result is produced in Phase 4A.

Current status is **REVISION REQUIRED**, with supervised learning **BLOCKED** by absent independently verified labels and the NFT-versus-DEX domain mismatch.

## Existing evidence available to a future model

Phase 3 contains 5,996 rows representing 2,312 unique wallets at three cumulative UTC cutoffs:

| Scoring cutoff | Snapshot rows | Wallet overlap with later cutoffs |
|---|---:|---|
| 2025-09-01 | 1,754 | all 1,754 reappear at both later cutoffs |
| 2025-10-01 | 1,930 | all 1,930 reappear at 2025-12-01 |
| 2025-12-01 | 2,312 | final descriptive cutoff; no later events exist in the file |

Across the three tables, 1,754 wallets have three snapshots, 176 have two, and 382 have one. Treating these 5,996 rows as independent observations would leak wallet identity and overlapping event history across folds.

The validated event history runs from `2025-01-01T00:42:47Z` to `2025-11-30T23:16:57Z`. Of 2,312 wallets, 2,302 occur in only one calendar month and 10 in two months. This is weak longitudinal coverage for learning within-wallet behavioural change. A December cutoff has no observable future outcome window in the current file.

## Estimand and temporal alignment

### Preferred early-warning estimand

Subject to confirmation against the approved proposal, the operational question would be:

> For a wallet observed before `scoring_time`, what is the risk of independently verified wash trading in a fixed future outcome window?

The observation is `(wallet, scoring_time)`. All feature events satisfy `block_time < scoring_time`. The target window begins at or after `scoring_time`; label evidence is not used as a feature. Labels become eligible for training only after the full outcome window matures at `knowledge_time`.

The horizon, population eligibility rule, data-coverage requirement, and independent evidence definition must be fixed before inspecting model results. A wallet with no recorded future event is not automatically a negative because missing source coverage and inactivity are indistinguishable without additional evidence.

### Historical-status estimand

If approval confirms retrospective detection, evidence and label knowledge must predate or equal `scoring_time`. Results must be described as recognition of previously demonstrated status, not future prediction. The two estimands require different label timing and cannot be pooled.

## Conditional split design

Random row-level splitting is prohibited. A future split manifest must be created before training and must record wallet identities, feature cutoffs, outcome windows, label knowledge times, and exclusion reasons.

The primary design should be chronological and wallet-disjoint:

1. Define nonoverlapping training, validation, and final holdout scoring periods with outcome windows fully observed by the data/evidence cutoff.
2. Assign every wallet identity to only one partition. Later snapshots of a wallet assigned to training cannot enter validation or holdout.
3. Purge observations whose feature-history or outcome intervals overlap a later partition's outcome interval; apply an embargo matching the selected horizon where needed.
4. Fit imputers, scalers, encoders, feature selection, resampling, and calibration inside training only. Validation selects model/hyperparameters/thresholds; the holdout is opened once for final evaluation.
5. Freeze the label version, feature-rule version, split manifest, random seeds, and review budget with the artifact.

The existing cutoffs are useful for measuring overlap but are not an approved split. A possible future-window study could use earlier feature cutoffs for training, `2025-09-01` for validation, and `2025-10-01` for holdout with outcomes ending by 30 November. This is only a candidate boundary: new snapshots would be needed, and it is infeasible unless verified positive and negative counts are adequate in every partition. `2025-12-01` cannot test a future outcome using the current event history.

If the intended deployment explicitly rescored known wallets, a secondary repeated-wallet analysis may be justified, but it must remain strictly chronological, use nonoverlapping outcome windows, account for within-wallet dependence, and be reported separately from new-wallet generalisation. It cannot replace the wallet-disjoint primary analysis without an approved estimand change.

## Feasibility checks before any training

| Check | Current finding | Gate to proceed |
|---|---|---|
| Usable labelled wallets | Zero verified labels available. | Exact-schema label register passes automated and human evidence review. |
| Class imbalance | Unknown. Counts of 249, 18, and 9 in old material are heuristic, not ground truth. | Report verified prevalence overall and per split, with source/coverage caveats. |
| Wallet/domain overlap | Root file and old notebook input match, but no evidence register exists. NFT evidence would not automatically match DEX swaps. | Every label wallet joins exactly to an approved event identity and domain. |
| Positive support per split | Unknown. | Each train/validation/holdout partition contains enough independent positives and negatives to compute stable planned metrics; otherwise redesign before training. |
| Outcome maturity | No evidence/knowledge times exist. | Every observation's full outcome window has matured before label use. |
| Repeated-wallet leakage | Certain under naive row splitting: cumulative snapshots repeat 1,930 wallets. | Wallet-disjoint primary manifest or separately approved repeated-wallet estimand with dependence controls. |
| Event-history adequacy | Eleven months overall; nearly all wallets appear in one event month. | Eligibility/history coverage fixed in advance; limitations retained in interpretation. |
| Label-feature circularity | Certain for the 249 and 18 heuristic targets. | Label evidence is independent of engineered predictor rules. |

## Metrics and decision policy

Metrics are feasible only after the split audit confirms both classes in each evaluated partition.

- **PR-AUC / average precision:** primary ranking summary for imbalance, always reported with the holdout prevalence and uncertainty. It is not meaningful as evidence of fraud detection when the target is feature-derived.
- **MCC:** thresholded summary using all four confusion-matrix cells. Report the complete confusion matrix; do not hide a degenerate all-negative or all-positive prediction behind one scalar.
- **Recall at a fixed review budget:** rank holdout wallets and measure positives captured in the top `K` or top declared percentage. `K` must come from a documented operational review capacity and be frozen before holdout access.
- **Calibration:** evaluate Brier score, calibration intercept/slope, and a reliability display only if independent positive support is adequate. Fit any calibration method on training/validation data, never the holdout. Avoid many fixed bins when positives are sparse.
- **Supporting measures:** precision, recall, specificity, and false-positive count at the frozen operating point, with wallet-level confidence intervals where defensible.

Accuracy and ROC-AUC may be supporting diagnostics but cannot be the primary evidence under severe imbalance. Thresholds must be selected on validation data against the declared review policy, not optimized on the final holdout.

No universal minimum positive count is asserted here. Before Phase 4B, the observed per-split counts must be reviewed for statistical precision and reported honestly. If a metric cannot be estimated credibly, it must be marked infeasible rather than omitted or replaced with a more flattering measure.

## Lecturer-lab alignment

The plan retains the lecturer's demonstrated separation of features/target, fitted transformations inside a pipeline, explicit validation versus test roles, probability-based evaluation, PR-AUC, and recorded feature order. It adapts the examples because their random or group-only partitions do not answer this point-in-time wallet question. The capstone therefore adds chronological outcome maturity, wallet-disjoint primary evaluation, interval purging/embargo, and a label-provenance gate before any pipeline is fitted.

## Phase 4B entry criteria

Phase 4B may begin only after explicit student approval and all of the following are available:

1. the approved proposal/target wording or documented supervisor approval for the chosen domain and estimand;
2. a lawful, versioned independent evidence register that passes `validate_label_table`;
3. documented source independence, identity matching, negative-class logic, coverage, and adjudication;
4. a frozen temporal split manifest with adequate verified class support in every partition; and
5. explicit confirmation that label-generation fields are not reused as circular predictors.

If these conditions cannot be met, the next milestone is supervisor review of a methodological revision—not model training.
