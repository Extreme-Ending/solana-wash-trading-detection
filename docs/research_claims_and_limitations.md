# Research claims and limitations

## Permitted claims

Subject to the unresolved source/licence qualification, the repository evidence supports these claims:

- the supplied local file contains 10,800 wallet-attributed Solana DEX/swap-event records for 2,312 wallet identifiers over the observed 2025 interval;
- the deterministic cleaner retained 10,798 records and quarantined two under documented rules;
- 29 registered wallet features are constructed using only events before an explicit scoring timestamp;
- the fitted Isolation Forest, LOF and robust comparator produce reproducible experimental anomaly rankings under pinned local inputs and dependencies;
- detector agreement, parameter sensitivity, longitudinal stability and cohort/coverage associations were measured without labels;
- the API and dashboard explicitly present anomaly scores and review candidates rather than probabilities or fraud decisions; and
- production configuration fails closed and does not load the experimental artifact.

## Prohibited or unsupported claims

The evidence does **not** support statements that:

- a wallet committed fraud, wash trading, market manipulation or misconduct;
- a score is a fraud probability, calibrated risk, severity, monetary loss or confidence level;
- the system detects NFT wash trading or coordinated wallet networks;
- “249 flagged wallets” are verified positives;
- the detector has measured accuracy, precision, recall, F1, PR-AUC, ROC-AUC, MCC or calibration;
- top-ranked cases are true positives, model errors or representative of the wider Solana population;
- feature associations explain why a wallet is anomalous or caused its score;
- longitudinal stability is independent test performance;
- synthetic demonstration cases validate real-world effectiveness; or
- the system, artifact, deployment or methodology is production-approved merely because software tests pass.

## Principal limitations

1. **No independent outcomes.** There is no timestamped, independently reviewed wash-trading label register. Effectiveness against fraud cannot be measured.
2. **Domain mismatch.** The observed schema is DEX swap-oriented, not an NFT marketplace schema. Buyer/seller and NFT fields are absent.
3. **Unresolved provenance/licence.** The provider, acquisition query, sampling frame, completeness and reuse rights are unknown.
4. **No counterparty graph.** A shared transaction or token is not direct evidence of a wallet-to-wallet transfer or collusion link.
5. **Longitudinal dependence.** Every training wallet appears in later full snapshots. Later ranks partly reflect accumulated history for the same entities.
6. **Cohort/history confounding.** New entrants and limited-history wallets have shorter observable histories. Differences may reflect coverage rather than behavioural risk.
7. **Detector dependence.** Rank agreement varies substantially across algorithms and settings. There is no label-based basis to select the detector that is “most accurate.”
8. **Arbitrary review budgets.** Top-*k* membership is a workload convention, not a learned or validated fraud threshold.
9. **Feature sensitivity is descriptive.** Score associations with feature/coverage strata are not causal explanations and do not isolate individual feature effects.
10. **Synthetic demonstrations are contract tests.** They validate request handling and rendering only; they are not empirical research cases.
11. **Local-only acceptance.** Hosted Firebase identity, private-service routing, distributed abuse protection and operational monitoring have not been accepted live.

## Required language in reports and interfaces

Use: “experimental anomaly score,” “unusual relative to the fitted reference,” “review candidate,” “supplied DEX swap-event sample,” and “no verified fraud label.”

Avoid: “fraud probability,” “wash trader,” “confirmed suspicious wallet,” “accuracy,” “prediction confidence,” “ground truth,” and “production ready” unless future evidence specifically warrants the term.

## What would permit stronger conclusions

Stronger fraud-detection claims require an independently sourced label schema with wallet identity, transaction domain, evidence timestamp, outcome/decision timestamp, evidence provenance, label definition, reviewer/audit information and explicit unknown/negative handling. Labels must predate or be separated appropriately from scoring, match the same population, and not be derived from the evaluated features. A chronological, wallet-aware protocol with enough positives in each split would then be required. Dataset provenance and use rights must also be resolved.
