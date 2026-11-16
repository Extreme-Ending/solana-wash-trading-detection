# Dissertation evidence mapping

## Use of this map

Every material dissertation statement should point to code, generated evidence and a limitation. “Incomplete” entries require student research or institutional/provider evidence; they must not be filled with invented references.

## Chapter 1 — Introduction

| Proposed claim/topic | Supporting evidence | Status/qualification |
|---|---|---|
| Automated review can help prioritize unusual high-volume wallet activity | Anomaly-ranking interface and [`research_methodology_alignment.md`](research_methodology_alignment.md) | Motivate as review support, not confirmed fraud detection |
| The implemented domain is Solana DEX swaps | Schema audit and [`dataset_provenance_resolution.md`](dataset_provenance_resolution.md) | Verified from fields; origin remains unknown |
| Research objective is reproducible point-in-time anomaly ranking | Feature contract, evaluator, API and [`phase9_research_results.md`](phase9_research_results.md) | Supported for the implemented system |
| Original NFT/supervised framing differs from available evidence | Proposal summary in steering plus Phase 4A/8E documents | Primary proposal absent; formal reconciliation evidence incomplete |
| Research contribution | Deterministic pipeline, comparison diagnostics, secure local demonstration | Limit contribution to methodology/engineering and label-free findings |

## Chapter 2 — Literature review

| Proposed claim/topic | Supporting evidence | Status/qualification |
|---|---|---|
| AML course foundations for auditing and leakage-safe features | [`lab_traceability.md`](lab_traceability.md), official lecturer repository/Lab 2 | Present as course-method alignment |
| Isolation Forest, LOF and robust anomaly detection literature | Existing technical implementation and model comparison | **Incomplete:** student must add and verify primary scholarly references |
| Blockchain/DEX wash-trading research context | Existing proposal summaries only | **Incomplete:** do not invent a bibliography or transfer NFT findings to DEX data |
| Gap: verified on-chain labels and temporal evaluation | Phase 4A and [`research_claims_and_limitations.md`](research_claims_and_limitations.md) | Supported as this project's evidence gap; broader literature claim needs citations |

## Chapter 3 — Methodology

| Proposed claim/topic | Supporting code/evidence | Status/qualification |
|---|---|---|
| Dataset contains 10,800 events and 2,312 wallets | `audit.py`, audit JSON, Phase 9 table 01 | Source/licence unresolved |
| Two rows quarantined under explicit rules | `preprocess.py`, cleaning report, preprocessing tests | Supported; report reason codes |
| Unit is `(wallet, as_of)` with strict `block_time < as_of` | `features/build.py`, feature registry/tests | Supported |
| 29 registered features | feature registry, snapshot/manifest hashes | Supported; document categories and lineage |
| Chronological train/validation/holdout | `train_anomaly.py`, Phase 9 figure 01/table 02 | Supported; not wallet-independent |
| Algorithms/configuration | artifact manifest and model comparison | Supported as label-free experiment |
| Evaluation uses rank stability, agreement, drift and coverage | `evaluate_anomaly.py`, figures 02–05 | Supported; no outcome metrics |
| Ethical controls | no labels/edges invented, bounded API, explicit interpretations | Supported; source permission remains unresolved |
| AI-use disclosure | None locally | **Incomplete/blocking:** Phase 9 is not authorized to recreate it |

## Chapter 4 — Implementation and results

| Proposed claim/topic | Supporting code/result/figure | Status/qualification |
|---|---|---|
| End-to-end deterministic processing | data/feature/model CLIs and [`phase9_reproducibility.md`](phase9_reproducibility.md) | Supported in pinned local environment |
| Isolation Forest sensitivity `0.9923–0.9980` | Figure 04 and evaluation JSON | Validation rank stability only |
| Holdout detector correlations `0.0488`, `0.8662`, `-0.0187` | Figure 03/table 03 | Agreement, not correctness |
| Later entrants have higher median scores | Figure 02 and evaluation JSON | Confounded by shorter history/cohort shift |
| Coverage/volume strata differ | Figure 05 | Association, not attribution |
| Local API and dashboard function | integration auditor, frontend tests/build, demonstration guide | Real Firebase browser acceptance requires student-operated session |
| Production fails closed | API tests, actual-artifact audit, container smoke | Supported locally; no live deployment claim |
| Synthetic bursty/steady/sparse walkthrough | demo script and API integration | Software example only; exclude from empirical effectiveness |

## Chapter 5 — Discussion and conclusions

| Proposed claim/topic | Supporting evidence | Status/qualification |
|---|---|---|
| Rankings depend on algorithm and review budget | Figure 03 and top-k evaluation | Supported |
| Repeated wallets prevent independent temporal generalisation claims | Figure 01 and longitudinal diagnostics | Supported |
| Data coverage affects interpretation | Figures 02 and 05 | Supported descriptively |
| System demonstrates anomaly-analysis methodology | Full local pipeline and validation | Supported conditionally |
| System detects wash trading/fraud effectively | No supporting evidence | **Prohibited claim** |
| Future supervised work | Label contract and modelling plan | Conditional on independent timestamped labels and lawful source data |
| Future deployment | Secure deployment architecture | Proposal only; no resource/deployment claim |

## Submission evidence gaps

The primary proposal, marking rubric, written methodology authorization, dataset source/licence, consolidated scholarly bibliography, final report/slides and required AI disclosure are not present locally. This map organizes available evidence but cannot close those external or student-authored obligations.
