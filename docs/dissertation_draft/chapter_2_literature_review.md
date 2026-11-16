# Chapter 2 — Literature review (working draft)

## 2.1 Anomaly detection foundations

Anomaly detection covers methods that identify departures from an expected pattern, with technique-specific assumptions about global, local, statistical or structural unusualness (Chandola et al., 2009). In settings with limited abnormal examples, novelty and one-class approaches model a reference distribution rather than a conventional two-class target (Pimentel et al., 2014). The current study is more cautious still: its historical cohort is a fitted reference, not a verified anomaly-free class.

Isolation Forest isolates observations through random recursive partitions (Liu et al., 2008). LOF compares an observation's local density with neighbouring densities (Breunig et al., 2000). Robust median-based deviations provide a transparent comparator resistant to extreme observations (Rousseeuw & Croux, 1993). These algorithms operationalise different anomaly concepts, so disagreement is scientifically informative.

## 2.2 Evaluation without ground truth

Unsupervised detector evaluation is sensitive to datasets, parameters, anomaly definitions and evaluation construction (Campos et al., 2016). Comparative work also distinguishes local from global anomaly behaviour and warns against assuming one detector dominates across tasks (Goldstein & Uchida, 2016). In the absence of verified labels, this study uses rank stability, cross-detector correlation, top-budget overlap, sensitivity and cohort diagnostics. These evaluate consistency, not fraud correctness.

## 2.3 Financial anomaly monitoring

Financial anomaly research applies statistical and machine-learning methods to rare, evolving and operationally costly behaviours (Hilal et al., 2022). Yet unusual financial activity can be legitimate. This motivates review prioritisation and human judgement instead of autonomous accusation. It also requires scores, thresholds and explanations to be described according to what they actually measure.

## 2.4 Blockchain and DEX evidence

Victor and Weintraud (2021) identify wash-trading structures using account and trade relationships on particular Ethereum limit-order-book DEXs. Their design illustrates the importance of market mechanism, self-trades and multi-account patterns. The current Solana file lacks the counterparty/ownership structure necessary to reproduce those criteria. Similarly, address clustering relies on explicit chain-specific heuristics and validation (Victor, 2020); shared tokens or transactions do not prove common control.

## 2.5 Temporal validation and distribution change

Behavioural data change over time, creating evaluation and adaptation problems (Gama et al., 2014). The current study observes feature/coverage differences across cutoffs and later entrants, but without a target it cannot establish change in a fraud concept. Chronological cohorts and repeated-wallet analysis are therefore reported separately, and random row-level splitting is rejected.

## 2.6 Reproducibility and responsible AI

Reproducibility practices strengthen the reliability of machine-learning evidence through transparent code, environments and reporting (Pineau et al., 2021). This project binds source, cleaned data, snapshots, models and figures with hashes. It also follows the high-stakes caution expressed by Rudin (2019): descriptive feature comparisons are not presented as causal black-box explanations, and no anomaly rank triggers an automated adverse action.

## 2.7 Research gap

The project addresses a bounded applied gap: how to integrate leakage-safe temporal wallet representation, multi-detector label-free diagnostics, reproducible evidence and secure review delivery for this supplied Solana DEX sample. It does not claim algorithmic novelty or universal Solana fraud detection. The full verified bibliography and transfer limitations are in [`../phase10_literature_review.md`](../phase10_literature_review.md) and [`../phase10_reference_audit.md`](../phase10_reference_audit.md).

## 2.8 Student work required

**[STUDENT INPUT REQUIRED]** Expand thematic synthesis in the student's voice, add any institution-mandated recent sources, verify all references through the university library and connect each theme to the final research questions. Do not introduce NFT or labelled-performance literature as if it validated the present DEX sample.
