# Decision log

This log records decisions that constrain later implementation. It does not claim that later-phase components already exist.

## D001 — Stop at the Phase 0 foundation

- **Date:** 2026-11-07
- **Status:** accepted
- **Decision:** Create only documentation, ordinary ignore rules, minimal package metadata, an importable placeholder, and a scaffold test.
- **Reason:** The milestone protocol requires student review and a student-authored commit between phases.
- **Consequence:** No data, feature, training, evaluation, API, Docker, report, or slide implementation is included.

## D002 — Treat supervised modelling as blocked

- **Date:** 2026-11-07
- **Status:** active blocker
- **Decision:** Do not create labels, train a classifier, serialize a model, or report supervised metrics until an independently verifiable wallet-level label source passes provenance and as-of checks.
- **Reason:** The steering audit reports no explicit target in the earlier CSV uploads, and those raw files are absent from the current working tree.
- **Required evidence:** `wallet`, label definition, evidence/source, label or knowledge timestamp, label version, and review methodology.

## D003 — Disable graph claims without direct edges

- **Date:** 2026-11-07
- **Status:** active blocker
- **Decision:** Do not infer wallet-to-wallet coordination from shared tokens, pool/program identifiers, DEX names, or transaction hashes.
- **Reason:** Such fields do not establish a counterparty relationship. Graph features need verified, time-bounded wallet edges.

## D004 — Use point-in-time wallet observations

- **Date:** 2026-11-07
- **Status:** approved design constraint
- **Decision:** Define the future unit as `(wallet, as_of)` and allow only events with `block_time < as_of` into features.
- **Reason:** This matches the approved scoring question and prevents future-event leakage.
- **Consequence:** Split selection, feature lineage, labels, and serving inputs must all carry temporal meaning.

## D005 — Adapt, rather than copy, course validation

- **Date:** 2026-11-07
- **Status:** approved design constraint
- **Decision:** Preserve Lab 2’s fitted-pipeline and entity-separation principles but use time-ordered validation for the capstone, adding wallet/event overlap controls where the estimand requires them.
- **Reason:** Lab 2’s `GroupKFold` answers a different validation question. The separate end-to-end practical also fits preprocessing before splitting, which is unsuitable here.

## D006 — Keep the dependency baseline minimal

- **Date:** 2026-11-07
- **Status:** accepted for Phase 0
- **Decision:** Target Python 3.11+, pin only the scaffold test dependency, and defer data/ML/API packages until the phase that uses them.
- **Reason:** This makes current claims reproducible without implying unimplemented capabilities or adding unjustified tooling.

## D007 — Record missing primary documents and provenance

- **Date:** 2026-11-07
- **Status:** open
- **Decision:** Use the verified steering summaries temporarily and explicitly disclose that `references/` is absent.
- **Required follow-up:** Add and read the approved proposal and rubric when the student can lawfully include or provide them. Resolve the provider/API placeholder, collection method, chain, snapshot dates, licence, and checksums before making source claims.

## D008 — Preserve student Git ownership

- **Date:** 2026-11-07
- **Status:** permanent workflow rule
- **Decision:** Codex may edit approved working-tree files and run read-only Git inspection, but the student alone stages, commits, pushes, changes branches, tags, or modifies repository history.
- **Reason:** The capstone is an individual assessment and requires genuine student review and authorship checkpoints.

## D009 — Use one repository with separated application boundaries

- **Date:** 2026-11-08
- **Status:** user-approved architecture direction
- **Decision:** Keep offline Python ML, a future FastAPI backend, a future React/Vite frontend, tests, and academic documentation in one assessed repository while preserving independently understandable components.
- **Boundary:** `src/solana_risk/` owns data, feature, training, evaluation, serialization, and shared inference transformations; a future `api/` imports serving logic; a future `frontend/` communicates only through HTTPS/JSON. Training runs locally and never on API startup or prediction requests.
- **Phase 0 consequence:** Document the boundaries only. Do not create backend/frontend applications or cloud resources.

## D010 — Target Cloud Run and Firebase Hosting after local delivery

- **Date:** 2026-11-08
- **Status:** user-approved future direction
- **Decision:** Establish FastAPI with Docker/Compose locally before considering Google Cloud Run. Build the later React/Vite SPA as static assets for standard Firebase Hosting. Treat Azure Container Apps Consumption as an alternative only after a measured comparison or explicit student direction.
- **Portability and security:** Keep core Python provider-neutral, use environment variables, restrict CORS to the deployed frontend and localhost development origin, and never embed credentials or provider secrets in browser code.
- **Cost control:** Prefer request-based CPU, scale-to-zero, conservative instance limits, CPU-only serving, measured memory, bounded requests, and no always-on database or paid RPC by default. Verify current regional pricing and indirect costs before deployment.
- **Phase gate:** React/Vite, Firebase Hosting, Cloud Run, and live integration require separate approval after the academic Phase 0–6 milestones; no deployment is authorized now.

## D011 — Do not imply wallet-address-only inference without event access

- **Date:** 2026-11-08
- **Status:** approved integrity constraint
- **Decision:** A future address lookup requires an authorized, timestamped event source or precomputed snapshot/index. Until then, any valid inference interface must accept sufficiently validated event history or feature-compatible input with explicit `as_of` semantics.
- **Reason:** A public address alone does not supply historical events, feature lineage, or a valid scoring cutoff.
- **Consequence:** The future API must return explicit model/data-not-ready responses rather than mock probabilities.
