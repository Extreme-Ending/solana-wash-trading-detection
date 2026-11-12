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
- **Reason:** The Phase 1 audit of the root `nft.csv` confirms that none of its 18 columns is an explicit wash-trading target.
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
- **Reason:** Lab 2’s `GroupKFold` and the separate practical's random holdout answer different validation questions from future point-in-time wallet scoring.

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

## D012 — Audit one immutable root dataset

- **Date:** 2026-11-10
- **Status:** accepted for Phase 1
- **Decision:** Audit only `<repository-root>/nft.csv`; resolve that location with `pathlib`, accept an explicit CLI override, never read `nft_trades.csv`, and never modify or track the source file.
- **Reason:** The approved Phase 1 specification establishes a single research dataset and forbids substitution, movement, combination, or cleaning during inspection.
- **Evidence:** Local SHA-256 remained `8f387709c6742f2fc31c19fc32dac27474b6b27b9304786c367a8d8bece81271` before and after the audit. Generated reports are under the Git-ignored `reports/data_audit/` directory.

## D013 — Classify the records as DEX/swap evidence, not NFT sales

- **Date:** 2026-11-10
- **Status:** accepted evidence interpretation
- **Decision:** Describe the actual rows as DEX/swap events and treat NFT-sale semantics as unsupported.
- **Reason:** The schema contains DEX, token-in/out, amount-in/out, and swap-source fields, while no NFT, collection, buyer, or seller field exists. A filename cannot override the observed schema.
- **Consequence:** Proposal differences are disclosed. No NFT wash-trading relationship or behaviour is inferred.

## D014 — Preserve diagnostic distinctions during inspection

- **Date:** 2026-11-10
- **Status:** accepted for Phase 1
- **Decision:** Report exact rows, repeated transaction hashes, and complete instruction-key collisions separately; report IQR outliers and nonpositive amounts without deleting or correcting rows; convert the literal `<nil>` only for missingness measurement.
- **Reason:** One Solana transaction can contain multiple valid instructions, heavy-tailed financial values are not automatically errors, and Lab 2 requires inspection before treatment.
- **Consequence:** Phase 2 must define and test event-grain, missingness, validity, and categorical-normalization policies after student approval.

## D015 — Make audit artifacts deterministic and private by default

- **Date:** 2026-11-10
- **Status:** accepted
- **Decision:** Produce strict JSON and human-readable Markdown without generation timestamps or absolute source paths; redact wallet, transaction, and token samples; ignore generated reports in Git.
- **Reason:** Stable artifacts support reproducibility, while raw identifiers and machine-specific paths do not belong in tracked evidence.
- **Implementation:** `pandas==3.0.2` is the sole Phase 1 runtime dependency. Synthetic tests cover validation, audit calculations, determinism, path resolution, and input immutability.

## D016 — Quarantine invalid evidence instead of deleting it

- **Date:** 2026-11-10
- **Status:** accepted for Phase 2
- **Decision:** Exclude missing/malformed essential identifiers, invalid event timestamps, invalid slots/indices, invalid fees, and missing/nonfinite/nonpositive required amounts from the cleaned table, but retain every excluded row in quarantine with ordered reason codes. Permanently remove zero rows.
- **Reason:** Invalid essential values make an event unsafe for deterministic downstream processing, while academic traceability requires preserving the original evidence and row reconciliation.
- **Observed result:** 10,800 input = 10,798 retained + 2 quarantined + 0 removed. Both quarantined rows have zero `amount_in` and `amount_usd`.

## D017 — Preserve transaction evidence at conservative instruction grain

- **Date:** 2026-11-10
- **Status:** accepted for Phase 2
- **Decision:** Quarantine only later exact copies of all 18 raw fields. Retain repeated transaction hashes and distinct instruction rows. Flag, rather than discard, collisions on complete `(wallet, tx_hash, outer_instruction_index, inner_instruction_index)` keys.
- **Reason:** Transaction-hash repetition is expected for multi-instruction swaps and cannot establish duplicate events by itself.
- **Evidence correction:** Direct recomputation on the approved checksum finds zero complete-key collisions, not the older steering note’s 263. The discrepancy is documented in `docs/preprocessing_findings.md`.

## D018 — Keep missingness and extremes explicit

- **Date:** 2026-11-10
- **Status:** accepted for Phase 2
- **Decision:** Retain missing fees, token-pair labels, and source-specific instruction indices with indicators. Do not zero-fill, statistically impute, cap, winsorize, or delete IQR outliers.
- **Reason:** Missing is not equivalent to zero; missingness mechanisms are unverified; and a heavy-tailed trade amount is not proof of an error.
- **Constraint:** The full-data IQR flag is review-only and prohibited as a model feature. Any later fitted transform belongs inside chronological training folds.

## D019 — Apply formatting-only DEX normalization

- **Date:** 2026-11-10
- **Status:** accepted for Phase 2
- **Decision:** Trim, case-fold, and normalize punctuation/whitespace in DEX strings while preserving raw values. Collapse only labels that become identical under that formatting rule; do not assign protocol families or merge differently named variants.
- **Observed result:** 48 raw spellings become 41 canonical formatting labels. Raydium AMM/CLMM/CP and comparable named variants remain distinct.

## D020 — Version the deterministic event contract

- **Date:** 2026-11-10
- **Status:** accepted
- **Decision:** Use preprocessing rules version `1.0.0`; preserve all original fields under `raw__*`; add source-row and content identities; normalize event time to UTC; and sort by `(block_time, block_slot, tx_hash, outer_instruction_index, inner_instruction_index, source_row_number)`.
- **Reason:** Stable ordering, immutable-source linkage, report/output hashes, and explicit rules make the cleaned event table reproducible without trusting supplied temporal-history features.
- **Leakage boundary:** Phase 2 creates no wallet features, labels, graph edges, fitted transforms, model artifacts, or evaluation results.

## D021 — Version a strict point-in-time feature contract

- **Date:** 2026-11-10
- **Status:** accepted for Phase 3
- **Decision:** Emit one row per observed `(wallet, as_of)` only after filtering validated events with `block_time < as_of`; use `as_of - window <= block_time < as_of` for lookbacks and reject timestamps without an explicit timezone.
- **Reason:** This implements the scoring-time boundary demonstrated by the lecturer's Lab 2 while making equality and multiple snapshot dates explicit for UTC Solana data.
- **Consequence:** A wallet without a strictly prior event has no row. Events exactly at the cutoff and all future events are excluded. The contract is tested independently of the real-data distribution.

## D022 — Register descriptive behavior and coverage, not labels

- **Date:** 2026-11-10
- **Status:** accepted for Phase 3
- **Decision:** Version 29 wallet activity, USD volume, temporal, token/DEX, fee, multi-instruction, and observable-history fields with definitions, calculations, units, missingness rules, and source lineage.
- **Reason:** Interpretable lineage is required before later model selection, and the present dataset supports behavior summaries but no verified outcome.
- **Boundary:** Wallet and cutoff are metadata; wallet/transaction/token strings are not direct predictors. No target, probability, verdict, counterparty edge, fitted transform, selection, resampling, model, or metric is created.

## D023 — Recompute event history and retain unavailable values

- **Date:** 2026-11-10
- **Status:** accepted for Phase 3
- **Decision:** Derive order, gaps, and lookback counts only from Phase 2 `block_time`. Do not use supplied `prev_event_time`, `seconds_since_prev`, or `source_week`. Leave inter-event statistics missing for a single observed event and distinguish missing fees from zero.
- **Reason:** Supplied temporal lineage is unverified, and filling unavailable history would create false evidence. Explicit coverage indicators make the observational boundary reviewable.
- **Observed result:** 3,316 of 5,996 generated snapshots have one observed event; 527 expose fewer than 30 days of history.

## D024 — Keep notebooks as executable explanations

- **Date:** 2026-11-10
- **Status:** accepted for Phase 3
- **Decision:** Track one EDA notebook and one feature-engineering notebook with cleared outputs, repository-relative paths, and imports from the reusable Phase 1–3 modules. Execute copies top-to-bottom in a temporary directory during verification.
- **Reason:** This follows the lecturer's notebook-based AML workflow without creating a second, divergent implementation or committing large generated plots and tables.
- **Consequence:** The generated snapshot/report artifacts and executed notebooks remain Git-ignored or outside the repository; source notebooks contain no exposed wallet, transaction, or token samples.

## D025 — Stop before supervised or application work

- **Date:** 2026-11-10
- **Status:** active gate
- **Decision:** End Phase 3 after descriptive point-in-time features and notebooks. Do not begin label creation, modelling, evaluation, API, frontend, container, or deployment work without explicit approval; supervised work additionally requires verified time-aware labels.
- **Reason:** Phase boundaries preserve academic review, and implementation progress cannot substitute for missing scientific evidence.

## D026 — Reject historical heuristic flags as supervised ground truth

- **Date:** 2026-11-10
- **Status:** active blocker
- **Decision:** Do not use the historical 249-candidate, 18-candidate, or nine-candidate heuristic results as verified binary targets or evidence of predictive performance.
- **Reason:** Static inspection traces the 249 count to a three-feature weak-supervision rule. A separate four-condition rule produces 18 positives in saved notebook output, despite a roadmap attributing 249 to that rule. Neither has independent adjudication, evidence timestamps, a persisted evidence register, or verified negatives.
- **Leakage consequence:** The heuristic rules use the same behavioral variables later offered as predictors, making supervised evaluation circular.

## D027 — Enforce a versioned external-label contract

- **Date:** 2026-11-10
- **Status:** accepted for Phase 4A
- **Decision:** Require exact binary values, a matching Base58 wallet and event domain, explicit scoring/outcome/evidence/knowledge times, independent verification, source and case references, review method, one target definition, and one label version. Reject unsupported values rather than repairing them.
- **Reason:** A reproducible schema can prevent accidental ingestion of heuristic flags, domain-mismatched evidence, immature outcomes, identity errors, and temporal leakage.
- **Implementation boundary:** `validate_label_table` validates synthetic fixtures and any future external input; it does not create, infer, store, or download research labels.

## D028 — Require approval for the NFT-to-DEX methodological mismatch

- **Date:** 2026-11-10
- **Status:** revision required
- **Decision:** Do not represent the current DEX swap-event file as NFT marketplace sale data. Do not change the title, target, or methodology to generic DEX manipulation, anomaly detection, positive-unlabelled learning, or weak supervision without student and supervisor approval.
- **Reason:** The current schema lacks NFT mints/collections, marketplace sales, buyer/seller roles, ownership transfers, and direct counterparties required to support the stated NFT wash-trading interpretation.
- **Consequence:** The overall readiness decision is **REVISION REQUIRED**; the supervised gate independently remains **BLOCKED** pending verified evidence.

## D029 — Make future evaluation chronological and wallet-aware

- **Date:** 2026-11-10
- **Status:** approved conditional plan
- **Decision:** If the label gate later passes, use a chronological, wallet-disjoint primary split with mature nonoverlapping outcome windows, purging/embargo as required, fold-contained fitted transformations, validation-only selection, and a final untouched holdout. Do not randomly split cumulative wallet snapshots.
- **Reason:** Phase 3 repeats 1,754 wallets across all three cutoffs and 1,930 across the October/December cutoffs. Random rows would share wallet identity and overlapping event history between partitions.
- **Metric gate:** PR-AUC, MCC, recall at a predeclared review budget, and calibration are reported only when verified per-split class support makes them estimable.

## D030 — Stop after Phase 4A

- **Date:** 2026-11-10
- **Status:** active gate
- **Decision:** End Phase 4A after the provenance audit, target/evaluation plan, and label-validator tests. Do not begin classifier training, model interpretation, API, container, frontend, or cloud work without explicit student approval and a passed evidence gate.
- **Reason:** A documented plan and validation contract do not substitute for the missing labelled evidence.

## D031 — Recommend an unsupervised DEX amendment for supervisor review

- **Date:** 2026-11-10
- **Status:** proposed — not approved
- **Decision:** Recommend, but do not implement, a revised unsupervised study of anomalous `(wallet, scoring_time)` observations in the existing DEX data because it is the only option currently supportable without manufactured labels.
- **Claim boundary:** Any future output would be a relative anomaly score/rank, not a wash-trading classification, fraud probability, or evidence of guilt.
- **Alternative paths:** Preserve the original supervised NFT study if authentic NFT events and independently verified labels are supplied; consider supervised DEX detection only if matching independently verified timestamped labels become available.
- **Gate:** No supervised or unsupervised model implementation begins until the student records supervisor direction and explicitly approves the next milestone.

## D032 — Authorize a provisional unsupervised experiment without changing methodology status

- **Date:** 2026-11-10
- **Status:** accepted for Phase 4B experiment only — methodology not approved
- **Decision:** Following explicit student authorization, implement Isolation Forest, novelty-enabled LOF, and robust MAD scoring on the existing DEX snapshots as a provisional experiment. Keep the approved title and the proposed amendment's `DRAFT — NOT APPROVED` status unchanged.
- **Temporal boundary:** Fit all learned preprocessing and detectors on the 1 September reference, use October for exploratory sensitivity, and preserve December for final aggregate diagnostics. Report repeated-wallet longitudinal evidence separately from later wallet entrants; do not use a random row split.
- **Claim boundary:** Scores and top-budget ranks are unverified anomaly-screening candidates, not labels, probabilities, wash-trading detections, or evidence of guilt. Detector agreement is not ground truth.
- **Observed limitation:** All 1,754 training wallets recur in validation and holdout. Later entrants are wallet-disjoint but have shorter observable histories and material coverage shift. No independent outcome performance can be estimated.
- **Next gate:** Stop after Phase 4B. No model promotion, API, frontend, container, cloud deployment, title change, or methodology-approval claim without a later explicit instruction and the required supervisor decision.

## D033 — Separate descriptive feature serving from unavailable prediction

- **Date:** 2026-11-10
- **Status:** accepted for Phase 5A
- **Decision:** Expose process health, prediction readiness, and shared-code descriptive feature preview as separate contracts. Keep `/v1/score` at HTTP 503 `MODEL_NOT_APPROVED`; do not deserialize or serve the Phase 4B experimental artifacts.
- **Feature boundary:** Require complete user-supplied event records for one wallet and an explicit UTC `as_of`; call the existing Phase 3 builder and retain the strict `block_time < as_of` rule. Reject requests with no prior event rather than generating history.
- **Security boundary:** Use typed closed schemas, bounded event/body sizes, exact configurable CORS origins, non-secret environment configuration, sanitized errors, and no client-supplied file path, external lookup, credential or raw-payload logging.
- **Reason:** A healthy API and reproducible feature preview are valid engineering deliverables, while neither establishes model readiness or verified fraud detection.
- **Next gate:** Stop after the local service foundation. Docker/Compose, React, Firebase, Cloud Run, artifact promotion and live integration require later explicit approval.

## D034 — Package only the descriptive API and preserve the readiness gate

- **Date:** 2026-11-12
- **Status:** accepted for Phase 5B
- **Decision:** Build a digest-pinned, multi-stage Python 3.11 slim image from the `pyproject.toml` `api` extra, run it as UID/GID 10001, and expose `/healthz` as container health while leaving `/readyz` and `/v1/score` at HTTP 503 `MODEL_NOT_APPROVED`.
- **Content boundary:** Use explicit Docker copies and a deny-oriented `.dockerignore`. Do not include raw/processed data, reports, notebooks, private steering, secrets, tests, joblib/scikit-learn, or experimental model artifacts. Compose mounts no data, artifact, host path, or Docker socket.
- **Runtime boundary:** Bind to `0.0.0.0`, validate the platform `PORT` with default 8080, disable reload, log to stdout/stderr, retain API request/CORS limits, use a read-only Compose filesystem and drop all capabilities.
- **Observed evidence:** The final local image is 345,274,935 bytes uncompressed. Direct-image and Compose tests returned 200/503/200/503/200 for health, readiness, feature preview, score, and OpenAPI; custom port, non-root execution, content exclusions, Docker health, and graceful exit code 0 passed.
- **Next gate:** Stop after local container validation. React, Firebase, live Google Cloud resources, automated deployment, authentication, and model-artifact promotion require separate explicit approval.

## D035 — Keep the browser descriptive, typed, and ephemeral

- **Date:** 2026-11-12
- **Status:** accepted for Phase 6
- **Decision:** Implement a React, TypeScript, and Vite research dashboard that accepts bounded user-supplied event history, calls the Phase 5A API, and displays all 29 descriptive features. Keep readiness and scoring unavailable; reject schema drift and any unexpected successful scoring response.
- **Data boundary:** Apply one wallet identifier to each event, require explicit UTC timestamps, enforce the API's 100-event and 256 KiB limits, and hold values only in React memory. A local JSON import is read only after the user selects it and is not submitted until an explicit form action.
- **Presentation boundary:** Distinguish null from zero, derive accessible charts only from returned feature values, disclose the DEX-versus-NFT mismatch and unverified-event limitation, and never turn unusual activity into a fraud or wash-trading claim.
- **Runtime boundary:** Default to a same-origin `/api` path with a loopback Vite proxy for local Docker integration. Add no credentials, persistence, telemetry, external runtime dependency, Firebase resource, Cloud Run resource, wallet provider, or model artifact.
- **Next gate:** Stop after local Phase 6 validation. Cloud hosting, authentication, provider-backed data retrieval, scoring enablement, and model promotion require a separately approved implementation milestone.
