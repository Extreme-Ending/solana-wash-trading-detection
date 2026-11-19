# DRAFT FOR FORMAL RECORD — STUDENT REVIEW REQUIRED

# Proposed methodology amendment

## Administrative note

The student previously communicated that the unsupervised direction was accepted. The repository does not contain the signed proposal or a written approval/amendment record that an examiner can verify. This document therefore supplies precise amendment wording for reconciliation; it does not impersonate or replace an institutional approval record.

## Original-to-implemented change

| Element | Original proposal summary | Evidence-aligned amendment |
|---|---|---|
| Title/domain | Coordinated wash trading, led by NFT trades | Unsupervised wallet anomaly analysis in Solana DEX swaps |
| Learning task | Supervised binary risk/probability | Label-free anomaly score and relative rank |
| Unit | Wallet at scoring time | `(wallet, as_of)` |
| Ground truth | Proposed flagged wallets | No verified outcomes used |
| Relational evidence | Proposed co-trading graph | Disabled: no direct counterparty edges |
| Evaluation | PR-AUC, MCC, recall, calibration | Stability, agreement, sensitivity, drift and coverage diagnostics |
| Service output | Fraud/wash-trading risk | Experimental unitless unusualness score and review rank |

## Proposed amended title

**Unsupervised Wallet Anomaly Detection in Solana DEX Trading: A Reproducible Risk Monitoring Service**

## Proposed objective and questions

Adopt the general objective, six specific objectives and five questions in [`phase10_research_alignment.md`](phase10_research_alignment.md). The change is necessary because the actual file is a DEX/swap table with no independent fraud target, while the historical flagged-wallet counts derive from overlapping behavioural heuristics.

## Proposed claim boundary

“Anomaly” means an observation that differs from the fitted historical reference in the registered feature space. It does not mean fraud, wash trading, coordination, intent or illegality. The system is decision support for research review only and must not issue a binary wallet flag or calibrated probability.

## Proposed validation

Use chronological reference, exploratory validation and descriptive holdout cutoffs. Keep repeated-wallet longitudinal evidence distinct from later-entrant evidence. Fit imputers, scaling and detectors only on the reference cohort. Report rank stability, cross-method agreement, review-budget overlap, parameter sensitivity, distribution shift and coverage-stratified behaviour. Do not use outcome metrics without independent labels.

## Records needed before final submission

- primary approved proposal and marking rubric;
- written amendment/approval record, date and approved wording;
- confirmation of whether the recommended title is formally adopted;
- extraction-time metadata and permitted-use evidence for confirmed Dune query 6561080; and
- institutionally compliant AI-assistance disclosure.

## Student confirmation fields

- Official amended title: **[STUDENT TO CONFIRM]**
- Approval record/date: **[STUDENT TO ATTACH OR CITE]**
- Supervisor/department wording constraints: **[STUDENT TO COMPLETE]**
- Dataset-use authority: **[STUDENT TO COMPLETE]**
