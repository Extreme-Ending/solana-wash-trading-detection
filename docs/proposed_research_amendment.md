# DRAFT — NOT APPROVED

# Proposed research amendment: unsupervised Solana DEX wallet-anomaly detection

**Status:** DRAFT — NOT APPROVED

**Purpose:** Supervisor review only

**Implementation authority:** None; no methodology change takes effect until written approval is recorded

## Proposed change

Replace the currently unsupported supervised NFT wash-trading classification task with an unsupervised study of anomalous wallet behaviour in the available Solana DEX swap-event data.

### Proposed working title

**Unsupervised Detection of Anomalous Solana DEX Wallet Activity: A Reproducible Wallet-Risk Screening Service**

This proposed title must not replace the approved title unless the supervisor approves the amendment.

## Rationale

The available `nft.csv` contains DEX/swap events rather than identifiable NFT marketplace sales. It has no independently verified wash-trading target, negative class, evidence timestamps, or direct wallet-counterparty edges. The historical suspicious-wallet counts are produced by behavioural heuristics that overlap with proposed predictors and cannot support defensible supervised performance claims.

The existing project has nevertheless established a reproducible DEX event pipeline and 29 point-in-time wallet features. An unsupervised anomaly study can use this evidence without fabricating labels, provided that all outputs are described as relative anomalies rather than confirmed fraud.

## Revised problem statement

Solana DEX monitoring may involve large volumes of wallet activity without reliable adjudicated manipulation labels. The revised study would investigate whether leakage-safe, point-in-time wallet features can support reproducible identification and explanation of observations that are unusual relative to a historical reference cohort.

It would not attempt to prove that an anomalous wallet has conducted wash trading or fraud.

## Revised objective

Develop and evaluate a reproducible unsupervised wallet-anomaly screening pipeline for Solana DEX swap events using only information available before an explicit scoring time.

### Proposed research questions

1. Which point-in-time wallet activity, volume, timing, token/DEX concentration, and data-coverage patterns produce stable anomaly rankings across later scoring periods?
2. How sensitive are anomaly rankings to detector choice, preprocessing, sparse wallet histories, and temporal distribution shift?
3. Can anomaly scores be accompanied by transparent feature-level deviation summaries suitable for prioritizing human review without being represented as fraud probabilities?

## Unit of analysis and data boundary

- Unit: `(wallet, scoring_time)`.
- Feature boundary: only events with `block_time < scoring_time`.
- Domain: observed Solana DEX/swap events only.
- Current evidence: 10,798 validated events, 2,312 wallets, and 5,996 snapshots across three cutoffs.
- Exclusions: no NFT-sale, buyer/seller, direct counterparty, collusion, or verified fraud interpretation.

Eligibility and minimum-history rules would be declared before anomaly rankings are inspected. Single-event and incomplete-history observations would be excluded, stratified, or reported separately according to that predeclared rule—not silently imputed into equivalence with well-observed wallets.

## Proposed methods

1. Transparent robust-deviation baseline.
2. Isolation Forest for nonlinear anomaly ranking.
3. PCA reconstruction error as a contrasting linear baseline.

All imputers, scalers, PCA components, and detector parameters would be fitted on the historical training/reference period only. Wallet identifiers, transaction hashes, raw token identities, supplied `source_week`, heuristic flags, and post-cutoff information would not be predictors.

Deep autoencoders, One-Class SVM, DBSCAN/HDBSCAN, GNNs, and graph propagation are initially excluded because the current effective sample size, sparse histories, absent direct graph edges, or complexity do not justify them. This exclusion would be revisited only with evidence and approval.

## Proposed validation and evaluation

- Use chronological reference and later scoring periods; no random row-level split.
- Separate temporal-rescoring analysis from unseen-wallet generalisation.
- Fit all learned preprocessing within the historical reference period.
- Measure score/rank stability, method agreement, temporal drift, sensitivity to reasonable settings, and coverage-stratified behaviour.
- Provide feature-level explanations of why an observation is unusual.
- Permit blinded top-budget review only when independent case evidence is available and kept outside detector fitting.

Without verified labels, the study would not report fraud precision, recall, F1, PR-AUC, MCC, calibration, false-positive rate, or wash-trading accuracy. Detector agreement and a chosen contamination fraction would not be treated as ground truth.

## Revised claim boundary

Permitted conclusion:

> The method identified wallet observations that were unusual relative to the specified historical DEX reference distribution, with the reported stability and feature deviations.

Prohibited conclusions:

- the wallet is a wash trader or fraudster;
- the anomaly score is a wash-trading probability;
- the method detects coordinated wallets without direct edges;
- anomaly prevalence equals fraud prevalence;
- results generalise to NFT marketplaces or unobserved Solana activity.

## Pipeline and deployment implications

The existing audit, cleaning, point-in-time feature, and test modules would remain applicable. A later approved modelling phase would add reproducible anomaly-detector training, artifact metadata, temporal evaluation, and inference transformations.

A later API would return an anomaly score, relative rank/reference context, feature-deviation reasons, model/reference-period metadata, and an explicit non-fraud disclaimer. It would not return `wash_probability`, a confirmed-fraud label, or an arbitrary address score without authorized event history. FastAPI, Docker, React/Vite, Firebase, and Cloud Run remain outside this amendment phase and require their existing milestone approvals.

## Lecturer-lab and rubric alignment

- Retains the lecturer's audit-before-treatment, explicit timestamp parsing, point-in-time feature construction, leakage-by-lineage review, train-only fitted transformations, importable modules, and automated tests.
- Uses an unsupervised method explicitly allowed by the capstone rubric because it fits the observed no-label problem.
- Preserves the required scripted ingestion → preprocessing → training → prediction structure in a future approved implementation.
- Supports later API and Docker delivery without inventing supervised predictions.
- Provides explicit technique justification and exclusions, honest evaluation limitations, and real-world screening relevance.

The amendment changes the modelling/evaluation evidence available to the rubric: supervised classification metrics would be replaced with unsupervised stability, sensitivity, drift, interpretability, and review-process evidence. The supervisor should confirm that this revised evidence is acceptable for the assessed modelling component.

## Unresolved prerequisites

Before implementation, the student still needs:

1. written supervisor approval of the revised title, objective, research questions, claim boundary, and evaluation evidence;
2. confirmation of the data provider/API, extraction query, sampling method, snapshot dates, licence, and permitted use;
3. a decision on wallet-history eligibility and later scoring periods;
4. an approved operational meaning for a review budget and anomaly-ranking output; and
5. resolution of required submission documentation, including the rubric-required `AI_USE.md`.

## Approval record

**Decision:** Pending

**Supervisor:** ______________________________

**Date:** ______________________________

**Conditions or requested changes:**

______________________________________________________________________________

______________________________________________________________________________

This draft does not modify the approved research methodology until signed or otherwise formally approved.
