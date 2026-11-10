# Supervisor methodology decision package

## Decision requested

This document requests supervisor direction on the research methodology. It does not record approval and does not authorize model training.

The approved project summary describes supervised, point-in-time wallet-risk scoring for coordinated Solana wash trading, led by an NFT trade cohort and supported by a DEX validation cohort. Phase 4A established that the available file is instead an unlabelled DEX swap-event table. The historical counts of 249, 18, and nine suspicious wallets are heuristic candidates, not independently verified outcomes.

## Evidence common to all options

- The available root dataset contains 10,800 DEX/swap events, 2,312 wallets, and no verified target, NFT sale fields, or direct wallet-counterparty edges.
- Phase 2 retains 10,798 valid events. Phase 3 supplies 29 point-in-time descriptive features for 5,996 `(wallet, as_of)` snapshots.
- Feature history is sparse: 55.30% of snapshots contain one event; 2,302 of 2,312 wallets occur in only one event month.
- Cumulative cutoffs repeat wallets and event history. Random row-level splitting is invalid.
- The source provider, extraction query, licence, approved proposal PDF, and independently verified evidence register remain unavailable.
- An unusual wallet is not necessarily a wash trader. An anomaly score is not a fraud probability or ground-truth classification.

## Option comparison

| Criterion | 1. Preserve supervised NFT approach | 2. Revise to supervised DEX detection | 3. Revise to unsupervised DEX anomaly detection |
|---|---|---|---|
| Scientific fit | Best fit to the approved NFT proposal, if authentic evidence is obtained. | Valid supervised study of a different transaction domain, conditional on verified labels. | Valid exploratory screening study using current data, but not fraud detection. |
| Readiness now | Blocked: NFT events and verified labels are absent. | Blocked: DEX events exist, but verified labels are absent. | Conditionally feasible after supervisor approval; no label fabrication is required. |
| Proposal change | None if supplied data and labels exactly support the approved objective; data-source details still need correction. | Substantial domain, title, objective, feature, and validation amendment. | Substantial objective, title, claims, metrics, service-output, and validation amendment. |
| Legitimate output | Estimated NFT wash-trading risk under the verified label definition and sampling assumptions. | Estimated DEX wash-trading risk under the verified label definition and sampling assumptions. | Relative anomaly score/rank and reasons within the observed DEX cohort—not a fraud verdict. |

## Option 1 — Preserve supervised NFT wash-trading detection

### Objective and unit

Estimate, for one `(wallet, scoring_time)` observation, whether independently verified NFT wash-trading evidence occurs in a prespecified outcome window. If the approved objective is retrospective instead, evidence and label knowledge must be available by the scoring time; the two targets cannot be mixed.

### Data and missing evidence

This option requires authentic NFT marketplace sales or ownership-transfer events with NFT mint/collection, marketplace, buyer, seller, price, event time, and transaction identity. A versioned independent label register must include wallet identity, binary outcome definition, evidence/source reference, evidence and knowledge timestamps, review method, and outcome window. Neither the NFT events nor this register is currently available.

The present DEX file cannot be renamed or interpreted as NFT sales. Its existing activity, timing, volume, token/DEX, and coverage features may provide engineering patterns, but NFT-specific features would require a new audited registry.

### Algorithms and rationale

- Prevalence/dummy comparator for context.
- Class-weighted logistic regression as an interpretable baseline.
- Random Forest for nonlinear interactions and robust tabular comparison.
- LightGBM only if effective sample size and verified positive counts justify the dependency and tuning complexity.

Graph features remain disabled unless direct, time-bounded buyer/seller or transfer edges exist. GNNs, synthetic labels, and full-data SMOTE are not justified.

### Training and evaluation

Use chronological, wallet-aware train/validation/final-holdout partitions with mature outcome windows. Fit all transformations inside training folds. Select hyperparameters and operating thresholds on validation only. Subject to class support, report prevalence, PR-AUC versus prevalence, MCC, recall at a predeclared review budget, confusion matrices, calibration, and wallet-aware uncertainty intervals.

### Leakage and validity risks

- Labels created from the same behavioural predictors would make evaluation circular.
- Post-outcome trades, ownership changes, graph structure, or review decisions must not enter features.
- Repeated wallets and overlapping history must not cross independent partitions.
- “Not flagged” is not a verified negative.

### Defensible conclusions

With valid evidence, results could support discrimination of the specified, evidenced NFT outcome within the observed population and time period. They would not prove criminal intent, universal marketplace generalisation, or guilt for an individual wallet.

### Proposal and implementation implications

The original research direction can be retained only if the authentic data matches it. The proposal's provider/API placeholder, sample construction, licence, target timing, and negative-class definition still need formal resolution. The current DEX-specific feature pipeline would need an NFT event adapter and NFT feature registry. A later API could return an estimated labelled-task risk with provenance and model metadata; address-only lookup would still require an authorized event source.

### Lab and rubric alignment

This option most directly supports the rubric's supervised modelling/evaluation requirement while retaining the lecturer's audit, point-in-time features, fitted pipeline, validation/test separation, and honest metric interpretation. It is not feasible merely to improve rubric coverage when its evidence prerequisites are absent.

## Option 2 — Revise to supervised DEX wash-trading detection

### Objective and unit

Estimate, for `(wallet, scoring_time)`, whether independently verified wash-trading activity in the same DEX swap domain occurs in a declared future window—or recognize evidenced historical status if that distinct target is approved.

### Data and missing evidence

The current DEX event data and 29 registered features provide a reproducible starting point. However, there are zero verified positive or negative labels, no evidence/knowledge timestamps, no direct counterparties, and no defensible class balance. The 249, 18, and nine heuristic counts cannot be used.

### Algorithms and rationale

Use the same conservative supervised comparison as Option 1: dummy/prevalence reference, class-weighted logistic regression, Random Forest, and conditional LightGBM. These suit the existing tabular features and preserve interpretability. Graph methods remain unsupported without verified edges.

### Training and evaluation

Apply the Phase 4A label contract, then create a chronological, wallet-disjoint primary split. Use an expanding-window or rolling historical validation design only if each period contains adequate independent positives and negatives. Preprocessing, optional resampling, model selection, calibration, and threshold selection remain inside training/validation. The final holdout is opened once.

### Leakage and validity risks

- The current heuristic rules directly reuse candidate model features and are prohibited as targets.
- The existing snapshots repeat 1,754 wallets across all three cutoffs and 1,930 across October/December.
- A December scoring cutoff has no future events in the present file.
- Sparse event histories may cause the model to learn data coverage rather than behaviour.
- Shared tokens, DEX programs, or transaction hashes do not establish coordinated wallets.

### Defensible conclusions

If independent DEX labels become available, results could describe performance for that defined DEX outcome and observed sampling process. They could not be presented as NFT marketplace results or proof of fraud beyond the label definition.

### Proposal and implementation implications

Supervisor approval would be required to change the domain, title, problem statement, target evidence, literature framing, feature interpretation, and generalisation claim from NFT trading to DEX swaps. Much of the existing audit, preprocessing, feature, and label-validation code could be reused. A later service could expose an estimated DEX outcome risk only after valid training and evaluation.

### Lab and rubric alignment

The path preserves the lecturer's supervised pipeline fundamentals and can eventually support the rubric's modelling, evaluation, API, and Docker deliverables. Until labels exist, it cannot satisfy the supervised performance claim or justify a prediction service.

## Option 3 — Revise to unsupervised DEX wallet-anomaly detection

### Objective and unit

Identify `(wallet, scoring_time)` observations whose pre-cutoff behaviour is unusual relative to a historical DEX reference population. The output is a relative anomaly score, rank, and feature-level deviation summary.

This option does **not** classify confirmed wash trading. A high score may reflect unusual legitimate strategy, high volume, new-wallet sparsity, source coverage, data quality, market regime, or manipulation. It must never be named `wash_probability` or treated as ground-truth fraud evidence.

### Data and missing evidence

The existing DEX events, deterministic cleaning, coverage indicators, and point-in-time feature registry are usable without labels. Missing provenance/licence and sparse histories still require resolution. Direct coordination or NFT claims remain impossible. Eligibility rules may need to exclude or separately analyse observations with insufficient history, but must be fixed before inspecting anomaly rankings.

### Algorithms and rationale

- Robust univariate/multivariate deviation baseline for transparent feature-level context.
- Isolation Forest as the primary nonlinear tabular anomaly-ranking candidate.
- PCA reconstruction error as a contrasting linear/global-structure baseline after training-only imputation and scaling.

One-Class SVM, DBSCAN/HDBSCAN, deep autoencoders, GNNs, and graph propagation should initially be excluded because of scaling sensitivity, sparse histories, limited effective sample size, unavailable graph edges, or unjustified complexity. Technique exclusions should be reported as required by the rubric.

### Training and evaluation

Fit reference transformations and detectors on an earlier chronological period and score later observations. Do not randomly pool repeated snapshots. Report separately:

- score distribution and drift across time;
- sensitivity to reasonable preprocessing and model settings;
- rank stability across candidate methods and cutoffs;
- feature-level reasons for high scores;
- coverage-stratified results, including single-event and short-history observations;
- blinded top-budget case review if independent evidence can later be obtained.

Without verified labels, PR-AUC, MCC, recall, calibration, fraud accuracy, and false-positive rates are not estimable. Agreement between detectors is not ground truth. Any contamination parameter controls ranking behaviour; it does not establish a fraud prevalence.

### Leakage and validity risks

- Fitting scaling, imputation, PCA, or detector parameters on the evaluation period would leak future distribution information.
- Repeated wallets/event histories can overstate temporal stability.
- Data sparsity and missing-fee patterns may dominate scores.
- Tuning to the historical heuristic flags would silently reintroduce pseudo-supervision.
- Reviewing and then repeatedly tuning against the same top-ranked wallets creates confirmation bias.

### Defensible conclusions

The study could identify reproducible patterns that are unusual relative to the observed DEX reference cohort and assess the temporal stability and interpretability of anomaly rankings. It could not conclude that detected wallets engaged in wash trading, fraud, collusion, or illegal activity.

### Proposal and implementation implications

This is a material change requiring written supervisor approval. The title, objective, research questions, literature framing, outcome terminology, metrics, limitations, and future API contract must change. Existing audit, preprocessing, and feature modules can largely be reused. A later service would return an anomaly score/rank and explicit disclaimer, not a wash-trading probability; model readiness and event-history requirements would still apply.

### Lab and rubric alignment

The rubric explicitly permits unsupervised learning and values techniques that genuinely fit the problem. This option retains the lecturer's raw audit, deterministic cleaning, scoring-time boundaries, train-only fitted transformations, reproducible modules, and honest evaluation. It can support a scripted training/prediction pipeline and later API/Docker deliverables, but the report must explain why label-based metrics are impossible and why anomaly detection is not fraud classification.

## Recommendation

**Recommend Option 3 for supervisor consideration because it is the most feasible scientifically defensible method with the data currently available.** It uses the existing DEX pipeline without manufacturing outcomes and can produce a valid anomaly-screening study.

This is not approval to proceed. The recommended scope must be formally amended before model implementation. If the supervisor requires the original supervised wash-trading objective, select Option 1 and pause implementation until authentic NFT events and independently verified, timestamped labels are supplied. Option 2 is a valid intermediate direction only if independently verified DEX labels can be obtained; none currently exist.

## Supervisor decision requested

- [ ] Approve Option 1 and require authentic NFT events plus verified labels before modelling.
- [ ] Approve Option 2 as a DEX supervised amendment, conditional on verified timestamped labels.
- [ ] Approve Option 3 as an unsupervised DEX anomaly-detection amendment.
- [ ] Request a different revision.

Until a choice is documented, supervised modelling remains blocked and unsupervised model implementation is also paused.
