# Research methodology alignment

## Assessment

The implemented pipeline is methodologically aligned with an **unsupervised, point-in-time wallet anomaly analysis of the supplied DEX event sample**. It is not aligned with supervised NFT wash-trading detection or with claims of confirmed fraud effectiveness.

| Research element | Implemented evidence | Alignment |
|---|---|---|
| Unit of analysis | Wallet snapshot as of a declared UTC scoring timestamp | Aligned for wallet anomaly ranking |
| Event domain | Solana DEX/swap events | Not aligned with an NFT-marketplace objective |
| Target | No outcome target; unitless unsupervised score | Aligned only with anomaly detection |
| Feature timing | Events must be strictly earlier than the scoring timestamp | Aligned with lecturer point-in-time fundamentals |
| Model family | Isolation Forest, novelty-enabled LOF, robust median/MAD comparator | Suitable for exploratory multivariate/outlier comparison; not a fraud classifier |
| Validation | September reference, October exploratory validation, December holdout | Chronological, but longitudinal dependence remains |
| Repeated wallets | All 1,754 reference wallets recur later | Explicitly audited; prevents claims of independent generalisation |
| New wallets | 176 in October and 382 in December relative to training | Useful cohort diagnostic, affected by shorter observed history |
| Ground truth | No independently verified label | Blocks precision, recall, F1, PR-AUC, calibration and fraud-effectiveness claims |

## Defensible research objective

> Develop and evaluate a reproducible point-in-time pipeline that ranks unusual wallet behaviour in a supplied sample of Solana DEX swap events, and study the stability, sensitivity and limitations of those rankings over time.

The output is an analyst-screening signal. A higher score means “more unusual under this fitted feature distribution,” not “more likely to be fraudulent.” The work can legitimately compare algorithms, rank agreement, temporal drift, coverage strata, engineering reproducibility and serving safeguards.

## Algorithm rationale and limits

- **Isolation Forest** is the served experimental detector because it handles multivariate outliers without labels and produces deterministic results under the pinned seed/configuration. Its transformed score is unitless and detector-specific.
- **Local Outlier Factor**, fitted with novelty scoring, supplies a different local-density view. Low agreement with Isolation Forest is substantive evidence that “anomaly” depends on detector geometry.
- **Robust median/MAD distance** is a transparent comparator, not a statistical probability or a ground-truth baseline.

No algorithm supplies causal attribution, collusion evidence or fraud status. The dashboard's feature reference is a descriptive training-distribution comparison, not SHAP or a causal explanation.

## Temporal design and leakage controls

The training reference is the wallet snapshot at 2025-09-01 UTC; October is exploratory validation and 2025-12-01 is the holdout snapshot. Each snapshot includes only events strictly before its timestamp. Preprocessing is fitted on the reference snapshot and reused later. The registered feature order and fingerprints bind training and serving.

This design prevents future events from entering an earlier feature vector, but it does not make repeated observations of a wallet independent. Full-period rank stability measures longitudinal consistency under more accumulated history. It is not an out-of-wallet performance estimate. New-wallet subsets are wallet-disjoint from training, but are systematically newer and have less observable history; they are not a random external population.

## Alignment with lecturer fundamentals

The implementation follows the verified AML lab sequence: inspect before cleaning; make parsing and quarantine explicit; set a scoring timestamp; aggregate entity features strictly before it; reason about leakage by field lineage; fit transformations inside an sklearn pipeline; keep validation and holdout roles distinct; serialize the complete fitted pipeline; and verify the serving contract. These are adaptations of the lecturer's official [course repository](https://github.com/NUELBUNDI/AML_Book-Data) and [Lab 2 solution](https://raw.githubusercontent.com/NUELBUNDI/AML_Book-Data/master/notebook/lab2_solution.ipynb), not copied results or data. Exact mappings are maintained in [`lab_traceability.md`](lab_traceability.md).

The labs' supervised metrics cannot be transplanted without outcomes. Replacing them with rank/sensitivity diagnostics is a methodological constraint, not a claim that anomaly evaluation is equivalent to classification evaluation.

## Formal-methodology status

The repository contains a draft research amendment and a methodology comparison. It does not contain the primary approved proposal, marking rubric or written approval evidence. Conversation statements are not converted here into documentary approval. The current implementation should therefore be described accurately as an experimental unsupervised route pending retention of the institutionally required record.

## Recommendation

Retain the current pipeline and frame the contribution around reproducibility, point-in-time anomaly ranking, temporal/sensitivity evidence and safe delivery. Do not add a supervised classifier, label high-ranked wallets, infer graph coordination, or change the formal title without documentary evidence and the student's authorized academic process.
