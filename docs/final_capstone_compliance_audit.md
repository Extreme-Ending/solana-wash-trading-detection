# Final capstone compliance and end-to-end ML pipeline audit

**Audit date:** 19 November 2026

**Repository:** `Extreme-Ending/solana-wash-trading-detection`

**Audited branch/revision:** `main` at `d7363b2412439b0e3b15387e4407db0046f28b8d`

**Revision subject:** `feat(deploy): enable checksum-pinned experimental anomaly scoring`

**Audit mode:** evidence-only; no cloud, Firebase, IAM, model, source-code, Git-history or deployment mutation was performed

## Source-of-truth limitation

No `DSA8401 Capstone Project.pdf`, approved proposal PDF, marking-rubric PDF or `references/` directory was present in the repository or supplied attachment. The supplied attachment contained only the exact assignment requirements reproduced in the audit request. Those requirements are therefore the official-requirements source used here; this report does not invent additional requirements.

The lecturer repository was checked read-only. The recorded Lab 2 snapshot `1ad78cc1ccaa6aa92e081893e3ea0cd380a1f950` remains retrievable and contains the documented audit, parsing, strict scoring-time and fitted-pipeline patterns. On the audit date, official `master` resolved to `ce9eaf933e9d7fd8621a024852dd6aafb9bf6c7a`; its unsupervised, FastAPI and fraud-MLOps examples were inspected. The `6a0b7e92ab4ffb6f168c08295eb378c19a0109f7` value described as a current checkout in `docs/lab_traceability.md` was not resolvable as an object in the public repository and should be corrected or explained in a separate remediation.

## A. Executive assessment

### Overall decision: PARTIAL — NO-GO for final academic submission

The project is a substantial, tested end-to-end **unsupervised wallet anomaly-analysis system**. With the locally supplied private input, its scripted audit, preprocessing, point-in-time feature generation, three-detector training, evaluation and serialization path reproduced successfully. A checksum-pinned Isolation Forest is also running in Cloud Run behind Firebase application authentication, and the React client is live on Firebase Hosting.

It is not submission-ready against all mandatory requirements because:

1. the explicit `AI_USE.md` deliverable is absent;
2. the input's provider, acquisition procedure, licence and redistribution permission are unresolved, so a fresh reviewer cannot lawfully or deterministically obtain it;
3. the serialized artifact exists only as an ignored local file and inside a deployed container, with no documented reviewer acquisition route;
4. the README has no architecture diagram and materially misstates the current cloud/scoring state;
5. only dissertation working drafts exist and no final report or slide deck exists; and
6. the student reports that the DEX anomaly-method amendment was accepted, but no primary written approval/amendment record is in the repository and the repository's amendment still says `DRAFT — NOT APPROVED`.

The strongest defensible research conclusion is that the implementation can reproducibly rank wallet-time observations by statistical unusualness relative to a September 2025 reference. It does **not** demonstrate wash-trading or fraud detection effectiveness.

## B. Official deliverables matrix

| # | Mandatory deliverable | Status | Evidence inspected | Finding and remaining action |
|---:|---|---|---|---|
| 1 | `README.md`: overview, setup, architecture diagram and reproduction instructions | **PARTIAL** | `README.md`; documented commands were checked | It has a detailed overview, dependencies and pipeline commands, but no architecture diagram. It still says no live deployment, production scoring is disabled, the artifact is not in Docker, and the project is at Phase 8C. Those statements contradict revision 7's live scoring container and Firebase release. It also cannot tell a fresh reviewer how to obtain the approved input/artifact. Update only in a separately authorized remediation. |
| 2 | `AI_USE.md` | **FAIL** | `git ls-files`; filesystem search; `docs/proposed_ai_use_disclosure.md` | `AI_USE.md` is absent. The proposed disclosure explicitly says it is not the required file. A truthful, student-reviewed disclosure of AI-assisted code, documentation, tests and troubleshooting is mandatory; this audit did not recreate it. |
| 3 | Scripted reproducible data pipeline | **PARTIAL** | `src/solana_risk/data/audit.py`, `data/preprocess.py`, `features/build.py`, `models/train_anomaly.py`, `models/evaluate_anomaly.py`; fresh `/tmp` run | The non-notebook pipeline runs end to end and is byte-deterministic with the private `nft.csv`. Fresh-clone reproduction is incomplete because the input is ignored, provenance/licensing is unresolved, and there is no acquisition mechanism. |
| 4 | Model training code and serialized model artifact | **PARTIAL** | `train_anomaly.py::fit_experiment`, `save_bundle`, `load_bundle`; local artifact and manifest | Training code and a valid 1,185,949-byte artifact exist. The artifact reproduced byte-for-byte, but `git ls-files` contains no artifact and no approved release/storage retrieval procedure exists. Publish only through a lecturer-approved mechanism with checksum/manifest and a trust warning for joblib/pickle; confirm whether an external release satisfies the repository-deliverable wording. |
| 5 | Dockerfile and Compose or equivalent | **PASS** | `Dockerfile`, `Dockerfile.scoring`, `.dockerignore`, `docker-compose.yml`, `scripts/container_smoke_test.py` | Both the model-free and checksum-pinned scoring images built and passed non-root, content, port, health, readiness and graceful-shutdown checks. Compose validated. |
| 6 | FastAPI model-serving API | **PASS** | `api/main.py::create_app`; `routes/scoring.py`; `experimental_scoring.py::TrustedExperimentalScorer`; API/auth tests; local Docker; live Cloud Run | The API loads only an explicitly enabled, checksum-verified Isolation Forest and returns typed non-probability single/batch anomaly scores. Live readiness is 200 and request logs contain an authenticated/protected batch POST returning 200. The live `/healthz` path nevertheless returns 404 while its `/v1/health` alias returns 200; fix and retest separately. |
| 7 | Final report or slide deck | **PARTIAL** | `docs/dissertation_draft/`; Phase 9 figures/tables; repository-wide PDF/PPT search | Five short working chapters and an evidence index cover most required topics, but they are explicitly non-final and contain student/document placeholders and stale no-deployment statements. No slide deck was found. Student authorship, final reconciliation, citation checking and institutional formatting remain required. |

**Count:** 2 PASS, 4 PARTIAL, 1 FAIL. No deliverable is marked `NOT APPLICABLE`.

## C. Rubric alignment

No numerical grade is assigned.

| Rubric component | Assessment | Evidence and limitation |
|---|---|---|
| Data pipeline — 10% | **PARTIAL** | Strong deterministic scripts, immutable input checks, quarantine reconciliation and point-in-time features. Independent acquisition and licensed fresh-clone reproduction are blocked. |
| Modelling and evaluation — 20% | **PARTIAL** | Three real detectors, chronological partitions, entrant/repeated-wallet separation, parameter sensitivity, rank correlation, top-budget overlap, shift and reproducibility are present. There is no detection-effectiveness evidence against independent outcomes, and incomplete-history/feature-configuration stress testing is not comprehensive. |
| Technique justification — 10% | **PASS** | Isolation Forest is justified by high validation rank stability in the tested range; novelty LOF and robust MAD are genuine comparators. Limitations and detector disagreement are reported honestly. The claim is anomaly ranking, not fraud prediction. |
| API and Docker deployment — 10% | **PARTIAL** | Local real-artifact inference, two Docker boundaries, production Cloud Run readiness and a successful live protected batch request are evidenced. The required live `/healthz` path is 404, authenticated response content was not independently captured during this audit, and artifact retrieval is undocumented. |
| Final report and presentation — 10% | **PARTIAL** | Traceable figures, tables, literature notes and chapter drafts exist. They are not a final student-authored report; no slides exist; several statements predate the live deployment. |

### Lecturer-lab alignment

The implementation preserves the lecturer's core fundamentals rather than copying the class task:

- inspect schema, missingness and duplicate grain before treatment;
- parse/validate timestamps and numeric values explicitly;
- use only events before a declared scoring time;
- aggregate to one row per entity/time observation;
- fit imputation/scaling inside training-fitted pipelines;
- compare methods and interpret anomalies cautiously;
- serialize feature order with the model;
- use typed FastAPI input and model-serving boundaries; and
- test a containerized runtime.

The capstone correctly departs from random row splitting and supervised class metrics because repeated wallets, chronological scoring and missing labels make those class-lab choices scientifically inappropriate here.

## D. ML pipeline audit

### D.1 End-to-end stage findings

| Stage | Status | Evidence/functions | Audit finding |
|---|---|---|---|
| Raw ingestion | **PARTIAL** | `audit.py::_load_input`, `audit_dataset`; local `nft.csv` SHA-256 `8f387709c6742f2fc31c19fc32dac27474b6b27b9304786c367a8d8bece81271` | Deterministic local reading and schema checks pass. The filename is misleading; the 18 fields describe DEX swaps. Provider, query, sampling and licence are absent. |
| Audit | **PASS locally** | `audit_dataset`, `write_reports` | Reproduced 10,800 rows, 18 columns, 2,312 wallets and 9,221 transaction hashes. No labels or direct counterparty fields were found. |
| Preprocessing | **PASS locally** | `preprocess.py::preprocess_dataset`, `write_outputs` | Reproduced 10,798 retained plus two quarantined records, zero silent removal, UTC normalization, deterministic ordering and preserved raw lineage. Repeated transaction hashes are not blindly deduplicated. |
| Feature engineering | **PASS locally** | `build.py::validate_events`, `_wallet_snapshot`, `build_wallet_snapshots` | Exactly 29 ordered features; `block_time < as_of`; closed-open windows; supplied previous-event fields excluded; wallet/cutoff retained only as metadata. |
| Training split | **PASS for stated estimand** | `chronological_partitions` | September reference: 1,754; October validation: 1,930; December holdout: 2,312. All 1,754 training wallets recur later; 176 and 382 later entrants are separately reported. These are not independent random test rows. |
| Fitted preprocessing | **PASS** | `build_models`, `RobustMADDetector.fit` | Median imputation is fitted on September only. LOF additionally uses training-fitted `RobustScaler`; Isolation Forest is unscaled; MAD learns training medians/MADs. |
| Model training | **PASS locally** | `fit_experiment` | Isolation Forest, novelty LOF and robust MAD are all genuinely fitted. Fixed configuration and version metadata are persisted. |
| Serialization/integrity | **PARTIAL** | `save_bundle`, `load_bundle`, `TrustedExperimentalScorer.load` | Reproduced artifact and manifest are byte-identical and registry-checked. Distribution to a reviewer is absent. Joblib must be treated as trusted-code serialization. |
| Local inference | **PASS** | `score_model`; `TrustedExperimentalScorer.score` and `.score_batch` | Unit/integration tests and the scoring-image embedded check generate finite real model scores and preserve exact feature order. |
| API | **PASS with live defect** | `create_app`; scoring/health routes | Authenticated typed scoring is implemented and live readiness confirms artifact load. `/healthz` is 404 live; `/v1/health` is 200. |
| Frontend | **PASS for deployed client wiring** | `frontend/src/api/client.ts`, auth context, analysis pages/components | Live Hosting returns 200. Its deployed application chunk targets the audited Cloud Run origin and the four intended `/v1` routes. A genuine interactive sign-in was not performed by this auditor. |

### D.2 Reproduced data and feature facts

The audit run in a new `/tmp/solana-final-audit.*` directory observed:

- raw events: **10,800**;
- retained: **10,798**;
- quarantined: **2**;
- silently removed: **0**;
- distinct wallets: **2,312**;
- snapshots: **5,996**;
- registered features: **29**;
- cutoff wallet counts: **1,754 / 1,930 / 2,312** at 1 September, 1 October and 1 December 2025 UTC;
- feature snapshot SHA-256: `779b446b15cce9cdc630353c60ffad2bfae039b086a1e0daa8dd66d05aff3a60`;
- feature-registry SHA-256: `75be47d7f875e2a04848d8b8b7931d7f90d7bbf3c5aa2b3476a827e09e2d4e8a`.

There are 3,316 single-event snapshots. Each has missing inter-event mean, median and standard deviation by design. There are no infinite values, train-all-missing features or train-constant features. Twelve feature pairs have absolute training Spearman correlation at least 0.95, including several volume, history-coverage and diversity/concentration pairs. The detector may therefore give correlated constructs repeated influence; the current report acknowledges this for the MAD comparator but should discuss it clearly for all models.

Extreme USD events were retained rather than winsorized. This is transparent, but high-volume strata receive materially higher Isolation Forest/MAD scores, so extremeness must not be equated with misconduct. The service uses the same registry and `build_wallet_snapshots` feature path as training, and tests verify training/serving order and values.

### D.3 Fresh-reviewer reproducibility

**Local computational reproducibility: PASS with the supplied private file.**

**Clone-only/acquisition reproducibility: FAIL.**

The README's default pipeline works after installation only if `nft.csv` has been supplied separately. Neither the raw input nor the artifact is tracked. The repository gives no lawful acquisition URL/query, licence or approved checksum-based retrieval step. On this host, the literal first command `python3.11 -m venv .venv` also fails because `python3.11` is unavailable; the existing Python 3.12 environment is compatible with `pyproject.toml` and passed all tests. This is an environment-specific documentation portability issue, not a package incompatibility.

An acceptable closure is a provider-approved acquisition procedure or restricted reviewer handover with a source manifest, terms/permission, immutable checksum and data dictionary. A fabricated substitute must not be presented as equivalent reproduction.

## E. Modelling and evaluation

### E.1 Models genuinely trained

| Model | Reproduced configuration | Role |
|---|---|---|
| Isolation Forest | 300 estimators; `max_samples=256`; `contamination="auto"`; `max_features=1.0`; no bootstrap; `n_jobs=1`; seed 42 | Selected experimental ranker because its validation ranks were stable across tested tree/sample settings. `contamination="auto"` is not fraud prevalence. |
| Local Outlier Factor | 35 neighbours; Minkowski p=2; novelty mode; robust scaling; `contamination="auto"`; `n_jobs=1` | Local-density comparator. Material neighbourhood and temporal instability prevents its selection as the served ranker. |
| Robust MAD | clip 25; constant penalty 10; root-mean-square clipped marginal deviations | Transparent baseline. Correlated variables may be counted repeatedly. |

The artifact was trained only on 1 September 2025 snapshots. It records Python/library versions, exact feature order, cutoff, feature reference, source snapshot hash and configuration. A fresh retraining produced the exact local artifact SHA-256 `3e35561b0bf5db42c5b7146e7ff568e313be1beb1be724997356af45f5533035` and manifest SHA-256 `1551d55f469ac3abd7a985d98055c69375968a2d9e28151e153aea2b61061ad0`.

### E.2 Evaluation tiers

#### A. Software correctness — strong

Deterministic runs, schema failure, strict cutoff boundaries, no target-like columns, training-only transforms, exact feature parity, artifact integrity, local real-artifact scoring, single/batch equality, ranking order, API errors, authentication branches and container boundaries are extensively tested.

One stale audit utility was discovered: `python scripts/audit_local_integration.py` expected development `/readyz` to be 503, but current enabled scoring correctly returned 200. The actual preview and batch calls in that run returned 200; the script still exited failure before reporting success. This should be corrected in a separate task.

#### B. Unsupervised ranking quality/stability — useful but incomplete

Reproduced evidence includes:

- Isolation Forest validation sensitivity correlations of **0.9923–0.9980** for the four tested tree/sample alternatives;
- LOF sensitivity correlations of **0.6052** and **0.7827** for 15/70 neighbours;
- holdout rank correlations: IF/LOF **0.0488**, IF/MAD **0.8662**, LOF/MAD **-0.0187**;
- zero all-three overlap at top 10, and seven all-three observations at top 100;
- training-to-holdout repeated-wallet correlations: IF **0.7502**, LOF **0.2207**, MAD **0.9635**;
- score, feature-shift, coverage, high-volume and later-entrant diagnostics; and
- controlled synthetic histories that test expected software sensitivity, not empirical detection.

These results support narrow claims about reproducibility, local parameter stability, algorithm disagreement and coverage dependence. They do not establish that the Isolation Forest ranking is correct. The zero top-10 three-way overlap is particularly important: review candidates are detector- and budget-dependent.

Additional high-value evaluation, without inventing labels, should include predeclared event-history truncation experiments; feature-family ablations and redundant-feature sensitivity; multiple random seeds; bootstrap rank/top-K uncertainty; rolling-origin reference windows; stability by activity/coverage strata; and an independent later/source cohort if lawful data becomes available. The December descriptive holdout should not be repeatedly tuned against.

#### C. Detection effectiveness — unavailable

There are no independently verified fraud or wash-trading outcomes. Precision, recall, F1, ROC-AUC, PR-AUC, false-positive rate, calibration, confusion matrices and claims of fraud detection effectiveness are therefore unavailable and must not be reported. Current experiments answer, “Is this ranking reproducible and how does it change across methods/time/coverage?” They cannot answer, “Does it detect wash trading?”

## F. Deployment

### F.1 Verified live state

| Item | Status | Read-only evidence |
|---|---|---|
| Frontend deployed | **PASS** | `https://solana-wallet-risk.web.app/` returned 200. GitHub Actions run `44473720937` successfully performed a **live** Firebase Hosting release from audited SHA `d7363b2…`; deployed version identifier `124f2b594b47aabf`. |
| Frontend API wiring | **PASS** | Public deployed application bundle contains the Cloud Run origin and `/v1/health`, `/v1/features/preview`, `/v1/score`, `/v1/score/batch`. |
| Backend deployed | **PASS** | Cloud Run service `solana-wallet-risk-api`, region `africa-south1`, latest ready revision `solana-wallet-risk-api-00007-4mh`, labelled `git-sha=d7363b2…` and `managed-by=local-script`. |
| Container/image | **PASS** | Service spec is digest-pinned; the revision is ready/container-healthy. It runs with the dedicated runtime service account, 1 CPU, 512 MiB, max scale 2 and port 8080. |
| Platform reachability | **PASS by explicit design** | Cloud Run's Invoker IAM check is disabled and ingress is all; FastAPI Firebase authentication protects research routes. This is public platform reachability, not public application authorization. |
| `/healthz` | **FAIL live** | Both reported service URLs returned Google-edge HTML 404. The source route exists and works in local containers. |
| `/v1/health` | **PASS live** | Returned 200 JSON; this is the hosted-browser health alias. |
| `/readyz` | **PASS live** | Returned 200 with `experimental_anomaly_scoring`, `experimental_unsupervised_research_only`, and `is_probability=false`. This also demonstrates that the configured artifact passed startup checksum/manifest/registry/version validation. |
| Protected endpoints without token | **PASS** | Preview, single score and batch score each returned 401 `AUTHENTICATION_REQUIRED`, before body validation. |
| CORS | **PASS for tested origin** | Preflight from the exact Firebase Hosting origin returned 200 and allowed only configured methods/headers including `Authorization`. |
| Authentication working | **PARTIAL/indirectly verified** | Production verifies Firebase signature/project/revocation plus audience, issuer, expiry, subject/UID, verified email, Google provider and allowlist. Cloud Run logs show a protected batch POST returned 200. This auditor did not perform a real Google popup or use/capture a user's ID token. |
| Actual deployed model response | **PARTIAL/strong indirect evidence** | Readiness was 200 and request metadata records `POST /v1/score/batch` HTTP 200 at 2026-11-19T06:42:17Z on revision 7. The response body was not logged or independently captured, so its numeric content remains unobserved by this audit. Local real-artifact tests do capture actual scores. |
| Reviewer reproduction | **PARTIAL** | Code, CI and containers work; raw data/artifact acquisition and authorized-account access are not reviewer-ready. |

The service configuration contains the exact artifact digest, production scoring opt-in, revocation checks, bounded payloads/batches, exact Firebase origins, a non-empty UID allowlist and per-instance rate limiting. No secret or user token is reproduced in this report. The per-instance limiter is not a distributed abuse-control system, and App Check is not enabled.

GitHub CI run `44471672509` passed for the exact SHA. The current Cloud Run scoring revision was deployed by the guarded local script, not by the repository's Cloud Run workflow; that workflow still describes a model-disabled private pilot. Deployment documentation and automation therefore do not yet fully describe the live state.

## G. Research-methodology alignment

### G.1 NFT proposal versus DEX evidence

The supplied file cannot support the original coordinated NFT wash-trading claim:

- it contains DEX/token/swap and instruction fields, not marketplace, NFT mint/collection, sale, buyer or seller fields;
- it contains no verified wash-trading target;
- the historic “249” and “18” wallet sets came from behavioral heuristics, not independent adjudication;
- those heuristics overlap with candidate behavioural features, making supervised reuse circular;
- it has no direct wallet-counterparty or validated common-ownership edges; and
- transaction/token co-occurrence cannot establish self-trading, circular trading, coordination or intent.

The implemented project is therefore **unsupervised wallet-time anomaly analysis in a supplied Solana DEX swap-event sample**. A high score means unusual relative to the September reference; it is not confirmed fraud or wash trading.

### G.2 Approval status

**Audit status: UNVERIFIED documentary approval.** The student has stated that the unsupervised direction was approved. The repository contains no primary written approval or signed amendment, and `docs/proposed_research_amendment.md` still says `DRAFT — NOT APPROVED`. The original proposal is also absent. This report does not deny the student's account, but an independent examiner cannot verify it from the available records.

Submission evidence should include an authorized written record reconciling title, objective, DEX domain, anomaly-score interpretation and permitted evaluation. If that record cannot be placed in a public repository, retain a redacted reference in the repository and provide the full record privately to the examiner.

## H. Dataset provenance

| Provenance question | Status |
|---|---|
| Exact provider/indexer/API | **UNRESOLVED** |
| Collector, query, sampling frame and collection date | **UNRESOLVED** |
| Dataset version/snapshot | Local filename/size/SHA known; upstream version **UNRESOLVED** |
| Domain | **VERIFIED locally as Solana DEX/swap semantics**, not NFT marketplace sales |
| Licence and academic-use permission | **UNRESOLVED — BLOCKER** |
| Redistribution of raw/derived wallet data | **NOT EVIDENCED; do not publish** |
| Exact reviewer reacquisition | **UNAVAILABLE** |
| Label provenance | **No independently verified labels present** |
| Direct counterparty evidence | **Absent** |

One historical on-chain record was previously corroborated against Solana RPC, but that does not identify the table's provider, selection, enrichment, completeness or licence. Local SHA-256 proves file integrity only.

## I. Academic submission readiness

### I.1 README

**PARTIAL.** It needs a current architecture diagram and a single fresh-reviewer path covering lawful data acquisition, the standard versus scoring image, artifact acquisition/retraining, API authentication, an actual inference example, evaluation reproduction and current live state. Stale no-deployment/production-disabled claims must be reconciled, not merely appended to.

### I.2 AI disclosure

**FAIL.** `AI_USE.md` is an explicit deliverable and is absent. `docs/proposed_ai_use_disclosure.md` is a useful factual draft but expressly not the required submission file. The final wording must truthfully disclose assistance with source code, documentation, test design, troubleshooting and draft academic material, while identifying the student's decisions, validation and authorship.

### I.3 Artifact

**PARTIAL.** The valid local artifact is ignored. Recommended delivery is a versioned, access-controlled or lecturer-approved repository release/artifact store containing only the trusted artifact and manifest, bound to Git SHA, dependencies, feature registry and SHA-256. Provide a retraining route and warn reviewers never to load untrusted joblib/pickle files. Obtain lecturer confirmation if an external release does not clearly satisfy “repository contains the deliverables.” Do not publish the raw dataset without rights.

### I.4 Final report and presentation

**PARTIAL.** The chapter drafts cover framing, literature, data, preprocessing, feature engineering, model choice, evaluation, architecture, limitations, ethics and future work, but they total only working-draft material, include explicit placeholders, and say the application is not deployed. No slide deck exists.

Proposed final report structure:

1. abstract and declaration/disclosure;
2. introduction, problem, objectives and approved scope change;
3. literature review and research gap;
4. data provenance, ethics and limitations;
5. reproducible methodology: audit, preprocessing, point-in-time features, models and temporal design;
6. implementation architecture: training, artifact, API, Docker, authentication, frontend and deployment;
7. results separated into software correctness, ranking/stability and unavailable effectiveness;
8. discussion, validity threats and detector disagreement;
9. conclusion and future independent validation; and
10. verified references and appendices containing commands, schemas, manifests and rubric crosswalk.

Proposed presentation outline:

1. problem and why it matters;
2. proposal-to-data mismatch and approved scope;
3. actual DEX dataset/provenance limits;
4. end-to-end architecture;
5. cleaning and leakage-safe temporal features;
6. IF/LOF/MAD rationale;
7. chronological cohorts and repeated-wallet constraint;
8. strongest stability/agreement results;
9. what the evaluation cannot establish;
10. live authenticated demonstration and score interpretation;
11. ethics, limitations and reproducibility blockers; and
12. conclusion and future validation.

## J. Priority remediation plan

| Priority | Gap | Required remediation |
|---|---|---|
| **BLOCKER** | Missing `AI_USE.md` | Student verifies institutional wording and authorizes a truthful tracked disclosure. |
| **BLOCKER** | No source/licence/acquisition evidence | Obtain provider, extraction/sampling procedure, data dictionary, licence/permission and immutable source manifest; otherwise seek written academic direction on use. |
| **BLOCKER** | Methodology/title approval not independently documented | Supply a primary amendment/approval record or examiner-verifiable private record, and reconcile title/objective/claim boundary. |
| **BLOCKER** | No reviewer artifact delivery and no clone-only pipeline reproduction | Establish approved artifact delivery with checksums/trust warning and a lawful data handover/acquisition path. |
| **BLOCKER** | No final student-authored report/slide deck | Rewrite/complete the drafts, update deployment evidence, verify citations, prepare slides and perform rubric crosswalk. |
| **HIGH** | Evaluation breadth | Add predeclared history truncation, feature-family ablation/redundancy, multi-seed/uncertainty and rolling-origin/independent-cohort diagnostics without reusing holdout for tuning. |
| **HIGH** | README materially stale | Replace phase chronology with current reviewer workflow and an architecture diagram; document both Docker modes and actual deployment. |
| **HIGH** | Live `/healthz` returns 404 | Diagnose Cloud Run routing/health alias behavior and retest the assignment-specified endpoint without weakening auth. |
| **HIGH** | Stale local integration expectation | Update `audit_local_integration.py` to the current readiness contract and rerun; do not alter results retroactively. |
| **MEDIUM** | Lab traceability current commit is not publicly resolvable | Refresh the reference to the official current commit or document why the old checkout was private/unpublished. |
| **MEDIUM** | Cloud workflow differs from live scoring deployment | Reconcile the GitHub Cloud Run workflow, guarded local script and live architecture; preserve manual approval and checksums. |
| **MEDIUM** | Real-user acceptance evidence is incomplete | Student performs a controlled sign-in, authorized score/batch request and logout/error rehearsal without recording tokens or sensitive wallet data. |
| **OPTIONAL** | Independently verified outcomes | If lawfully obtained later, conduct a separately approved effectiveness study. Do not block the explicitly permitted unsupervised submission merely to manufacture classification metrics. |

Recommended order: governance/disclosure → provenance/data rights → artifact/data reviewer handover → final report/README/slides → live health/integration corrections → evaluation extensions → controlled final rehearsal.

## K. Evidence register

### K.1 Key paths and functions

- Data: `src/solana_risk/data/audit.py::audit_dataset`; `data/preprocess.py::preprocess_dataset`.
- Features: `src/solana_risk/features/build.py::build_wallet_snapshots`; `MODEL_FEATURE_COLUMNS`; `docs/feature_registry.md`.
- Training: `models/train_anomaly.py::chronological_partitions`, `build_models`, `fit_experiment`, `save_bundle`, `load_bundle`.
- Baseline/evaluation: `models/baselines.py::RobustMADDetector`; `models/evaluate_anomaly.py::evaluate_experiment`.
- Serving: `api/experimental_scoring.py::TrustedExperimentalScorer`; `api/main.py::create_app`; scoring and health routers.
- Authentication: `api/auth.py::FirebaseTokenVerifier`, `authenticate_authorization_header`; `api/config.py::Settings`.
- Frontend: `frontend/src/auth/`, `frontend/src/api/client.ts`, analysis/dashboard components and tests.
- Delivery: `Dockerfile`, `Dockerfile.scoring`, `.dockerignore`, `docker-compose.yml`, `.github/workflows/`, deployment scripts.
- Research evidence: `docs/data_audit_findings.md`, `preprocessing_findings.md`, `experimental_modelling_findings.md`, `anomaly_model_comparison.md`, `research_evaluation_evidence.md`, Phase 9 tables/figures and dissertation drafts.

### K.2 Commands and observed results

| Command/check | Result |
|---|---|
| `git status --short --branch`; `git rev-parse HEAD` | Clean `main...origin/main` before this report; SHA `d7363b2…`. |
| Full audit → preprocess → three-cutoff features → train → evaluate using explicit `/tmp` paths | **PASS**; counts and checksums reproduced; no repository output overwritten. |
| `cmp` fresh artifact/manifest against local artifact/manifest | **Identical** for both. |
| `.venv/bin/python -m pytest -q` | **235 passed in 14.80s**. Tests are predominantly unit/in-process HTTP tests; Firebase verifier branches are mocked/injected unless explicitly stated. |
| `npm test -- --run` | **13 files, 92 tests passed**. |
| `npm run typecheck` | **PASS**. |
| `npm run build` | **PASS**; 45 modules transformed, four output files. |
| `python3 scripts/validate_workflows.py` | **PASS**. |
| `python3 scripts/validate_deployment_bundle.py frontend/dist` | **PASS**, four files checked. |
| `bash -n commit.sh scripts/*.sh` | **PASS**. |
| `docker compose config --quiet` | **PASS**. |
| `git diff --check` before report | **PASS**. |
| Execute all three notebooks to `/tmp` | Initial sandbox attempt could not open kernel sockets; approved local rerun **PASS** for all three. Generated notebook copies remained in `/tmp`. |
| Standard `Dockerfile` smoke suite | **PASS**: non-root UID 10001; health 200; readiness 503; protected endpoints 401; OpenAPI 200; custom port and graceful stop pass. This image intentionally has no model. |
| `Dockerfile.scoring` smoke suite | **PASS**: embedded trusted-artifact real score check; readiness 200; protected endpoints 401; production OpenAPI 404; custom port and graceful stop pass. |
| `python scripts/audit_local_integration.py` | **FAIL** due stale expected readiness 503 versus observed 200; health 200, preview 200, batch 200 and auth-error checks had otherwise matched. |
| Local pinned ShellCheck/actionlint Docker invocation | **NOT EXECUTED**: safely rejected because mounting this working tree would expose ignored private files to third-party images; local binaries were absent. Exact-SHA GitHub CI nevertheless completed successfully and includes these checks on a clean checkout. |
| GitHub Actions read-only inspection | CI run `44471672509` **success**; live Firebase run `44473720937` **success**, both for exact audited SHA. |
| Read-only Cloud Run service/revision inspection | Revision 7 ready/container-healthy; exact Git-SHA label, scoring flags, checksum, resource limits, Firebase project, revocation, CORS and allowlist presence verified without disclosing identities. |
| Live HTTPS checks | Frontend 200; `/v1/health` 200; `/readyz` 200; protected endpoints 401 without token; CORS preflight 200; `/healthz` 404. |
| Read-only Cloud request metadata | Protected `POST /v1/score/batch` returned 200 on revision 7; no token, UID or response body was read. |

### K.3 Integrity identifiers

- raw input: `8f387709c6742f2fc31c19fc32dac27474b6b27b9304786c367a8d8bece81271`;
- cleaned events: `1889adf72a727544a8759203336ac257108d344e2ea71aaa118aa04f0aa50937`;
- wallet snapshots: `779b446b15cce9cdc630353c60ffad2bfae039b086a1e0daa8dd66d05aff3a60`;
- feature registry: `75be47d7f875e2a04848d8b8b7931d7f90d7bbf3c5aa2b3476a827e09e2d4e8a`;
- model artifact: `3e35561b0bf5db42c5b7146e7ff568e313be1beb1be724997356af45f5533035`;
- model manifest: `1551d55f469ac3abd7a985d98055c69375968a2d9e28151e153aea2b61061ad0`;
- live Cloud Run revision: `solana-wallet-risk-api-00007-4mh`;
- live Git SHA label: `d7363b2412439b0e3b15387e4407db0046f28b8d`;
- service image reference: digest-pinned Artifact Registry image; the service reports index digest `8477ca8f…68ca4` and the imported revision reports runtime manifest digest `2221b7ce…307df`;
- live frontend: `https://solana-wallet-risk.web.app/#home`;
- backend origin: `https://solana-wallet-risk-api-jm24jzeesq-bq.a.run.app`.

## L. Final GO/NO-GO

### NO-GO for final submission

The implementation is technically credible and unusually careful about leakage and unsupported fraud claims. It has a real reproducible local anomaly pipeline, a serialized model, a tested model-serving container and a live authenticated deployment. Those strengths do not close explicit academic deliverables or governance evidence.

Submission should wait until the required AI disclosure, data provenance/licensing decision, methodology approval record, reviewer artifact/data route, current README and final student-authored report/presentation are complete. The live `/healthz` defect and stale integration utility should also be resolved and retested in a separately authorized remediation. No model promotion, label fabrication or conversion of anomaly ranks into fraud flags is warranted.
