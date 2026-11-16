# Chapter 1 — Introduction (working draft)

## 1.1 Background

Public blockchains expose timestamped transaction evidence that can support market monitoring, but transparency does not automatically identify the entities controlling addresses or the intent behind a trade. Wash trading is a particularly demanding target because defensible identification may require self-trade, account-control, counterparty or adjudicated evidence. Victor and Weintraud (2021), for example, analysed relational trading structures on specific Ethereum DEX designs; those structures cannot be assumed from any generic swap table.

The supplied project file contains Solana DEX swap-event fields rather than NFT marketplace-sale fields. It records 10,800 events for 2,312 wallet identifiers over January–November 2025, but it contains no independently verified wash-trading outcome and no direct counterparty-wallet edge. A supervised fraud classifier would therefore learn no defensible target. The implemented research instead studies wallet observations that are statistically unusual relative to a historical reference cohort.

## 1.2 Problem statement

Solana DEX monitoring data can be large, temporally dependent, sparse and incompletely labelled. Simple whole-dataset aggregation risks using future events, while heuristic flags derived from the same behaviour features create circular evaluation. The research problem is to determine whether a reproducible point-in-time pipeline can rank and contextualise unusual wallet observations without converting those rankings into unsupported fraud claims.

## 1.3 Motivation

The study is motivated by three needs. First, applied machine learning requires data-quality and leakage controls before model fitting. Second, an unlabelled environment needs evaluation based on stability, agreement, sensitivity and distributional context rather than invented classification accuracy. Third, any reviewer-facing service must communicate uncertainty and fail safely when an experimental model is not authorised.

## 1.4 General objective

To design, implement and evaluate a reproducible point-in-time unsupervised anomaly-analysis service for wallet activity in a supplied Solana DEX swap-event sample.

## 1.5 Specific objectives

1. Audit and deterministically clean the event sample while documenting provenance limitations.
2. Construct leakage-safe wallet features using only events before explicit UTC scoring times.
3. Compare Isolation Forest, LOF and robust MAD rankings through chronological label-free diagnostics.
4. Examine repeated-wallet dependence, later entrants and observable-history coverage.
5. Deliver bounded local feature-preview and anomaly-review workflows with explicit non-fraud semantics.
6. establish computational reproducibility through versioned contracts, fingerprints and automated tests.

## 1.6 Research questions

1. How can the DEX events be transformed into reproducible point-in-time wallet snapshots without future information?
2. How stable are anomaly rankings across chronological periods and reasonable settings?
3. How strongly do the three contrasting detectors agree on later wallet rankings?
4. How do coverage and cohort differences constrain score interpretation?
5. Can the research workflow be delivered locally while preserving security and scientific claim boundaries?

## 1.7 Scope

The unit is `(wallet, as_of)`. The study covers the supplied events, 29 registered features, three fixed scoring cutoffs, three unsupervised detectors, deterministic local training/evaluation, FastAPI, a React dashboard and container validation. It excludes NFT-sale analysis, direct coordination graphs, supervised fraud metrics, production deployment and automated adverse decisions.

## 1.8 Contribution

The contribution is an integrated applied methodology: audit, transparent quarantine, strict pre-cutoff features, contrasting anomaly rankings, temporal/coverage diagnostics, checksum-bound evidence and a fail-closed review interface. It also documents negative findings—what the evidence cannot support—rather than hiding absent labels or provenance.

## 1.9 Required student reconciliation

**[DOCUMENT REQUIRED]** Insert the official proposal title, approved amendment wording and approval date from primary records. **[STUDENT INPUT REQUIRED]** Add the student's personal motivation and contextual rationale in their own words. Dataset origin/licence must be resolved or retained as a major limitation.
