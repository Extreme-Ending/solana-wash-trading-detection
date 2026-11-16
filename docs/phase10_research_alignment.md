# Phase 10 research alignment

## Status of this recommendation

This document recommends wording consistent with the implemented evidence. It does not replace the title or objectives in an approved institutional record. The repository lacks the primary proposal and a written amendment/approval record; these must be reconciled by the student before submission.

## Recommended working title

**Unsupervised Wallet Anomaly Detection in Solana DEX Trading: A Reproducible Risk Monitoring Service**

This title accurately names the domain, learning paradigm, unit and engineering contribution. “Risk monitoring” must be defined as review prioritisation, not an estimate of fraud probability.

## Problem statement

Solana DEX activity produces time-dependent wallet behaviour, but the supplied research sample contains no independently verified wash-trading outcomes and no direct counterparty graph. A supervised fraud classifier or coordination detector cannot therefore be evaluated honestly. The supportable problem is to determine whether reproducible, leakage-safe wallet snapshots can identify and contextualise observations that are unusual relative to a historical reference distribution while preserving uncertainty, temporal dependence and data-coverage limitations.

## General objective

To design, implement and evaluate a reproducible point-in-time unsupervised anomaly-analysis service for wallet activity in a supplied Solana DEX swap-event sample.

## Specific measurable objectives

1. Audit and deterministically clean the supplied event data while preserving rejected evidence and documenting provenance limitations.
2. construct 29 registered wallet features using only events strictly before each UTC scoring time;
3. compare Isolation Forest, Local Outlier Factor and a robust MAD baseline through chronological rank stability, cross-detector agreement, sensitivity and coverage diagnostics;
4. provide bounded single-wallet and batch review interfaces that preserve feature parity and non-probabilistic interpretation;
5. reproduce pipeline, artifact and research outputs through content fingerprints and automated tests; and
6. document scientific, ethical, security and external-validity limitations.

## Research questions

1. How can Solana DEX swap events be transformed into reproducible point-in-time wallet snapshots without using future information?
2. How stable are anomaly rankings across chronological scoring periods and reasonable detector settings?
3. To what extent do Isolation Forest, LOF and robust MAD agree when ranking later wallet snapshots?
4. How do observable-history coverage and later-entry cohorts constrain interpretation of anomaly scores?
5. Can the experimental outputs be delivered through a secure, reproducible local service without presenting anomaly as confirmed fraud?

## Methodology

- **Design:** quantitative, observational, label-free anomaly-analysis study plus reproducible systems implementation.
- **Data:** privately supplied Solana DEX/swap-event sample; origin/licence unresolved and disclosed.
- **Unit:** `(wallet, as_of)`.
- **Temporal rule:** only `block_time < as_of`; fixed cutoffs at 1 September, 1 October and 1 December 2025 UTC.
- **Preparation:** deterministic validation, quarantine and feature lineage. No dataset-wide fitted transform is learned before the reference split.
- **Methods:** training-reference-fitted preprocessing with Isolation Forest; novelty-enabled LOF and robust MAD as contrasting offline comparators.
- **Evaluation without labels:** rank correlation, top-budget overlap, configuration sensitivity, feature-distribution shift, repeated-wallet longitudinal analysis, later-entrant analysis and coverage-stratified score summaries.
- **Delivery:** local FastAPI and React application with Firebase identity boundaries, bounded payloads, exact feature parity and fail-closed production configuration.
- **Reproducibility:** immutable hashes, fixed seeds, versioned feature registry, deterministic scripts and automated regression tests.

## Evaluation criteria

Appropriate evidence includes deterministic reproduction, Spearman rank stability, cross-detector rank correlation, top-k overlap, chronological cohort accounting, distribution/coverage diagnostics, feature parity, API contract tests and security failure paths. Precision, recall, F1, ROC-AUC, PR-AUC, MCC and calibration are not estimable for fraud because verified outcomes are absent.

## Legitimate conclusions

The study may conclude that particular wallet-time observations were ranked as more unusual under a specified model/reference cohort; that rankings were stable or unstable under declared tests; and that the local pipeline is reproducible under the pinned environment. It may not conclude that a wallet committed wash trading, that the score is a probability, that the approach predicts crime, or that detector agreement constitutes ground truth.

## Limitations and ethics

- unknown sample construction, licence and completeness;
- DEX rather than NFT marketplace domain;
- no independent outcome or direct wallet-counterparty evidence;
- pseudonymous addresses remain potentially sensitive behavioural identifiers;
- repeated-wallet dependence and later-entrant coverage shift;
- arbitrary review budgets and method-dependent rankings;
- potential false suspicion if results are communicated as guilt; and
- no operational deployment or autonomous adverse decision is justified.

Human review, purpose limitation, data minimisation, access control and explicit uncertainty are mandatory. No wallet should be sanctioned or publicly identified from these experimental scores.
