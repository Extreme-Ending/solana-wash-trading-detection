# Chapter 4 — Implementation and results (working draft)

## 4.1 Architecture

The repository separates the Python research package, tests, FastAPI service, React/Vite frontend and documentation. Training is local and offline. The API reuses the same feature registry and builder used by research scripts; it does not train on request. The production-shaped container deliberately omits experimental model artifacts and modelling dependencies.

## 4.2 Data pipeline results

The deterministic audit found 10,800 source events and 2,312 wallet identifiers. Cleaning retained 10,798 events and quarantined two, with zero silent removal. Three cutoffs generated 5,996 wallet snapshots with 29 features. Figure 1 in the Phase 9 package shows that all 1,754 reference wallets recur in later periods, while 176 wallets first appear by October and another 382 by December.

## 4.3 Anomaly results

Isolation Forest validation rankings were highly stable across the tested estimator/sample-size alternatives: Spearman correlations ranged from `0.9923` to `0.9980` against the declared configuration. This supports configuration stability within the tested range only; it does not establish optimality or fraud effectiveness.

On the December holdout, rank correlations were:

- Isolation Forest versus LOF: `0.0488`;
- Isolation Forest versus robust MAD: `0.8662`; and
- LOF versus robust MAD: `-0.0187`.

No wallet was shared by all three top-10 lists; seven were shared by all three top-100 lists. The ranking is therefore materially detector- and budget-dependent.

## 4.4 Longitudinal and coverage results

For repeated wallets, reference-to-holdout rank correlations were `0.7502` for Isolation Forest, `0.2207` for LOF and `0.9635` for robust MAD. These are longitudinal persistence diagnostics as wallet histories accumulate, not out-of-wallet validation.

Later entrants have shorter observable histories and different score distributions. Holdout median Isolation Forest scores also differed by incomplete-history and high-volume strata. These associations show why coverage context matters; they are not causal feature contributions or evidence of manipulation.

## 4.5 Reproducibility results

Two independent full runs produced byte-identical audit JSON, cleaned events, quarantine, snapshots, experimental artifact and manifest. A second generation of all five SVG figures, three CSV tables and the figure manifest was byte-identical. The manifest records `labels_used=false` and rejects mismatched input fingerprints.

## 4.6 Service and dashboard results

Local integration tests verified health, fail-closed readiness, authentication failures, exact 29-feature parity, single/batch score equality, deterministic ranking and production scoring refusal. Synthetic bursty, steady and sparse histories validate software paths only. They are not empirical wallet case studies.

The dashboard presents anomaly values without percent formatting, retains full identifiers for review, distinguishes reference statistics from model explanations and displays methodological limits. The application has not been deployed.

## 4.7 Figure references

Use the tracked figures with the captions and interpretations in [`../phase10_results_interpretation.md`](../phase10_results_interpretation.md). Do not introduce a confusion matrix, ROC curve or classification metric because no verified outcome exists.

## 4.8 Student work required

**[STUDENT INPUT REQUIRED]** Select which figures appear in the final chapter, write transitions in the student's voice and check all numbering against the final dissertation template. Do not present synthetic scores as research results.
