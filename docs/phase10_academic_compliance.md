# Phase 10 academic compliance assessment

## Evidence basis

The primary proposal, full capstone rubric, written methodology record and authoritative institutional AI policy are absent from `references/`. This assessment uses only the verified rubric/proposal summary in local steering and observed repository contents. It cannot certify institutional compliance.

## Compliance matrix

| Requirement/evidence area | Status | Evidence or action required |
|---|---|---|
| One individual Git repository | Verified locally | Existing repository and incremental history; student owns Git writes |
| README and reproducible setup | Verified | `README.md`, scripts and tests |
| Scripted audit/preprocess/features/training/evaluation | Verified locally | importable package/CLIs and manifests |
| Valid modelling claim | Partial | unsupervised anomaly experiment is defensible; fraud effectiveness remains blocked |
| API, container and frontend | Verified locally | regression and container evidence; not deployed |
| Report/presentation evidence | Partial | chapter drafts and demo script exist; student-authored final report/slides absent |
| Proposal/method alignment | Partial | evidence-aligned recommendation exists; primary formal record absent |
| Dataset provenance/permission | Blocked | provider, query, licence and redistribution permission required |
| Labels/coordination evidence | Blocked for fraud claim | independent outcomes/direct edges absent |
| Scholarly references | Verified working set | 13 audited sources; student/library style review still required |
| AI assistance disclosure | Blocked/incomplete | `AI_USE.md` absent; steering summary says disclosure is required |
| Academic authorship | Requires student review | drafts are working material, not submission text |

## Lecturer-lab fidelity

The implementation follows the observed Lab 2 fundamentals: audit first, preserve missingness meaning, normalise with traceability, resolve the correct entity, construct scoring-time features, audit leakage by lineage and fit transformations on the historical reference. The supervised lab metric pathway is intentionally not copied because no verified target exists. End-to-end layering, FastAPI separation and testable delivery are mapped in `docs/lab_traceability.md`.

## AI-use requirement

The verified local rubric summary states that an `AI_USE.md` disclosure is required, while the current phase explicitly prohibits creating or modifying that file without authorization. Phase 10 therefore leaves it absent and creates `docs/proposed_ai_use_disclosure.md` as a factual review draft. The student must compare it with the actual institutional policy, correct it in their own words and explicitly authorize any final tracked disclosure.

## Academic integrity controls preserved

- no fabricated labels, metrics, experiments, approvals, sources or deployment;
- no classifier trained against heuristic flags;
- no graph constructed from unsupported co-occurrence;
- no raw dataset redistribution;
- no anomaly-to-fraud relabelling;
- clear distinction between synthetic software fixtures and empirical observations;
- formal document gaps retained as gaps; and
- all Git staging/commit/push reserved for the student.

## Submission actions for the student

1. Supply and reconcile the official proposal, rubric and amendment/approval record.
2. Resolve dataset-use authority or obtain written guidance on restricted private use.
3. Review, personalize and approve the AI disclosure under the actual policy.
4. Rewrite the dissertation drafts in the student's own voice and verify every citation.
5. Prepare the final slides/report and rubric crosswalk.
6. Retain terminal/test evidence without presenting previous runs as live if not rerun.

## Assessment

Academic evidence is substantially improved but compliance is **conditional**, not certified. Dataset rights, formal governance records, AI disclosure and student-authored submission artifacts remain mandatory external/student actions.
