# Phase 10 research gap analysis

## Evidence-based gap

Existing research establishes general anomaly-detection methods, evaluation challenges, financial monitoring applications and DEX wash-trading analyses. It does not make an unlabelled wallet table a fraud dataset. The bounded applied gap addressed here is the absence of a transparent, leakage-safe and reproducible workflow for analysing this supplied Solana DEX sample while retaining strict claim boundaries.

The project combines five elements that are often evaluated separately:

1. deterministic audit and quarantine of messy swap-event data;
2. strict wallet-at-time features built only from prior events;
3. comparison of global, local and robust anomaly rankings without outcome claims;
4. explicit separation of repeated-wallet, later-entrant and observation-coverage effects; and
5. a bounded authenticated research interface that fails closed outside experimental local mode.

## What the gap is not

- It is not evidence that no prior Solana anomaly work exists.
- It is not a claim to have discovered a new anomaly algorithm.
- It is not a labelled fraud-detection benchmark.
- It is not a graph or coordination study because counterparty edges are absent.
- It is not an NFT wash-trading study.
- It is not an operational deployment evaluation.

## Relationship to literature

Isolation Forest, LOF and robust statistics supply contrasting notions of unusualness. Unsupervised-evaluation literature motivates sensitivity and agreement analysis but also shows why those diagnostics cannot replace ground truth. DEX wash-trading literature demonstrates the importance of self-trade/account structures; the current data cannot reproduce those structures. Concept-drift literature motivates chronological monitoring, while this study carefully reports observed covariate/coverage change rather than claiming drift in an unknown fraud target.

## Research contribution that can be defended

The contribution is an applied methodology and evidence system: a reproducible implementation showing how to construct, compare, deliver and constrain point-in-time wallet anomaly scores under missing labels and incomplete provenance. It provides negative knowledge as well—specifically, which fraud, NFT and coordination conclusions the available evidence cannot support.

## Gaps remaining after Phase 10

1. independent, timestamped outcomes for any supervised effectiveness study;
2. direct, semantically valid account/counterparty edges for coordination analysis;
3. lawful and repeatable dataset acquisition with known coverage;
4. evaluation across independent time periods and data sources;
5. expert review outcomes for operational usefulness and false-suspicion risk; and
6. prospective monitoring for changing feature distributions and review capacity.
