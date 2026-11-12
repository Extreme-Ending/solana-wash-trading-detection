# Detecting Coordinated Wash Trading on Solana

This repository supports the DSA 8401 Applied Machine Learning capstone **“Detecting Coordinated Wash Trading on Solana: A Reproducible Wallet-Risk Scoring Service.”** The intended modelling unit is `(wallet, as_of)`: any future feature must use only events with `block_time < as_of`.

Phase 5B packages the Phase 5A FastAPI foundation in a locally validated, non-root Docker image and a locked-down one-service Compose configuration. The container does not include or load Phase 4B experimental artifacts and returns no anomaly, fraud, wash-trading, or probability output. React and live cloud resources remain outside this phase.

## Phase 4A evidence and blockers

The audited file contains 10,800 rows, 18 columns, and 2,312 unique wallets between 1 January and 30 November 2025 UTC. Its columns and source values support DEX/swap-event semantics, not verified NFT marketplace-sale semantics. Despite the filename, no NFT-specific column is present.

There is no verified wash-trading target and no buyer, seller, or wallet-counterparty field. Supervised wash-trading classification and graph-based coordination features therefore remain blocked. The data also has very limited longitudinal wallet coverage: 2,302 wallets occur in one calendar month and only 10 occur in two months. See [`docs/data_audit_findings.md`](docs/data_audit_findings.md) for the Phase 1 evidence and [`docs/preprocessing_findings.md`](docs/preprocessing_findings.md) for the Phase 2 rules and results.

Phase 2 retains 10,798 events and quarantines 2 records whose `amount_in` and `amount_usd` are both zero. It permanently removes zero records: quarantined source evidence remains in a separate output with explicit reason codes. The 7,303 missing fees remain missing with indicators rather than being replaced with zero. All 1,099 IQR review flags remain uncapped and retained. Formatting-only DEX normalization reduces 48 raw spellings to 41 canonical labels without merging differently named protocol variants.

Phase 3 produces 29 registered behavioral/data-quality fields for explicit `(wallet, as_of)` cutoffs. At `2025-09-01`, `2025-10-01`, and `2025-12-01` UTC it produces 1,754, 1,930, and 2,312 wallet rows respectively. Strict cutoff, window-boundary, missing-history, determinism, registry, and no-target tests are automated. See [`docs/feature_registry.md`](docs/feature_registry.md) and [`docs/feature_engineering_findings.md`](docs/feature_engineering_findings.md).

Phase 4A traces the historical “249 flagged wallets” to a weak-supervision notebook rule based on `burst_ratio`, `alternation_ratio`, and `mean_time_gap`. A separate four-condition heuristic produces 18 candidates in the saved notebook output, although an old roadmap incorrectly attributes 249 to it. Neither rule is independent evidence, both reuse candidate predictors to create the target, and no persisted wallet evidence register or timestamps exist. See [`docs/label_evidence_and_readiness.md`](docs/label_evidence_and_readiness.md) and [`docs/modelling_evaluation_plan.md`](docs/modelling_evaluation_plan.md).

Phase 4B fits Isolation Forest, novelty-enabled Local Outlier Factor, and a robust median/MAD baseline on the 1 September 2025 reference only. October is exploratory validation and December is final holdout. All 1,754 training wallets recur later, so full-period comparisons are longitudinal rather than independent; the 176 and 382 later entrants are wallet-disjoint diagnostics affected by shorter observed history. See [`docs/experimental_modelling_findings.md`](docs/experimental_modelling_findings.md) and [`docs/anomaly_model_comparison.md`](docs/anomaly_model_comparison.md).

The approved NFT proposal is not present under a local `references/` directory. A local DSA 8401 rubric was reviewed outside the repository, while other locally named proposal files concern a different cross-chain scam-token study. `AI_USE.md` is absent by student decision, although the rubric identifies an AI-use statement as required submission evidence. Provider/API, extraction query, collection method, licence, source snapshot, approved target wording, and independent label provenance remain unresolved.

## Install and run

Python 3.11 is the baseline. From the repository root:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
pytest -q
python -m solana_risk.data.audit
python -m solana_risk.data.preprocess
python -m solana_risk.features.build \
  --as-of 2025-09-01T00:00:00Z \
  --as-of 2025-10-01T00:00:00Z \
  --as-of 2025-12-01T00:00:00Z
python -m solana_risk.models.train_anomaly
python -m solana_risk.models.evaluate_anomaly
```

Start the local API after installation:

```bash
uvicorn solana_risk.api.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for generated OpenAPI documentation. Optional non-secret configuration is shown in `.env.example`; export values into the process environment before starting Uvicorn.

## Phase 5A API foundation

| Endpoint | Current behavior |
|---|---|
| `GET /healthz` | HTTP 200 when the process is responsive; no model-readiness claim |
| `GET /readyz` | HTTP 503 `MODEL_NOT_APPROVED` while prediction is unavailable |
| `POST /v1/features/preview` | Descriptive 29-feature snapshot from one wallet's validated user-supplied events using `block_time < as_of` |
| `POST /v1/score` | HTTP 503 `MODEL_NOT_APPROVED`; no artifact load or fabricated score |

Feature preview uses the same `build_wallet_snapshots` implementation as offline Phase 3. Wallet identifiers remain metadata, at-cutoff and future events are excluded, and unavailable single-event gap features remain null. The endpoint does not verify that submitted events are authentic or complete and does not fetch blockchain history from a wallet address. See [`docs/api_contract.md`](docs/api_contract.md) and [`docs/api_implementation_findings.md`](docs/api_implementation_findings.md).

## Phase 5B local container

Docker Engine with Compose is required. Build and wait for the single API service:

```bash
docker compose config --quiet
docker compose up --detach --build --wait
docker compose ps
```

The API is available only on `http://127.0.0.1:8080`. `/healthz` must return 200, while `/readyz` and `/v1/score` intentionally return 503 `MODEL_NOT_APPROVED`. View logs and stop the temporary resources with:

```bash
docker compose logs --follow api
docker compose down
```

Run the complete direct-image smoke suite when port 8080 is free:

```bash
python3 scripts/container_smoke_test.py
```

The image uses the official digest-pinned Python 3.11 slim base, installs the `api` dependency extra from `pyproject.toml`, runs as UID/GID 10001, honors `PORT`, and contains no research dataset or experimental artifact. See [`docs/containerization_and_local_deployment.md`](docs/containerization_and_local_deployment.md) and [`docs/container_validation_results.md`](docs/container_validation_results.md).

The CLI resolves `<repository-root>/nft.csv` from the installed module location, so it does not depend on the terminal's current directory. An explicit path is supported for reproducibility and testing:

```bash
python -m solana_risk.data.audit --input /path/to/input.csv
```

It writes deterministic `audit.json` and `audit.md` files to `reports/data_audit/`. That directory and the root dataset are Git-ignored. Reports contain the source SHA-256 but no generation timestamp or absolute source path; wallet, transaction, and token samples are redacted where appropriate. The audit reads only `nft.csv`, never `nft_trades.csv`, and does not modify its input.

The preprocessing CLI writes:

- `data/processed/cleaned_events.csv` — retained, typed, UTC-normalized and deterministically sorted events;
- `data/processed/quarantined_events.csv` — excluded rows with reason codes;
- `reports/preprocessing/cleaning_report.json` — structured rules, counts, mappings and output hashes; and
- `reports/preprocessing/preprocessing_summary.md` — concise human-readable evidence.

Both output directories are Git-ignored. Every original source field is retained under a `raw__` prefix, along with its one-based source row and content hash. The default CLI verifies the approved root-file SHA-256 before preprocessing.

The feature CLI verifies the cleaned CSV against the Phase 2 report hash and writes Git-ignored `data/features/wallet_snapshots.csv`, `reports/features/feature_report.json`, and `reports/features/feature_summary.md`. Repeat `--as-of` for multiple timezone-aware cutoffs. Optional `--input`, `--output`, and `--report-dir` paths support controlled tests without weakening the validation contract.

The notebooks are tracked without outputs. Run them from the repository root after installing development dependencies and generating the Phase 2 files:

```bash
jupyter nbconvert --to notebook --execute notebooks/01_exploratory_data_analysis.ipynb \
  --output 01_exploratory_data_analysis.executed.ipynb --output-dir /tmp/solana-risk-notebooks
jupyter nbconvert --to notebook --execute notebooks/02_feature_engineering.ipynb \
  --output 02_feature_engineering.executed.ipynb --output-dir /tmp/solana-risk-notebooks
jupyter nbconvert --to notebook --execute notebooks/03_unsupervised_anomaly_modelling.ipynb \
  --output 03_unsupervised_anomaly_modelling.executed.ipynb --output-dir /tmp/solana-risk-notebooks
```

Using a temporary output directory keeps generated plots and tables out of the assessed source notebook files.

For a source checkout that has not yet been installed and a system that exposes only `python3`, the equivalent development invocation is:

```bash
PYTHONPATH=src python3 -m solana_risk.data.audit
PYTHONPATH=src python3 -m solana_risk.data.preprocess
PYTHONPATH=src python3 -m solana_risk.features.build --as-of 2025-12-01T00:00:00Z
```

## Scientific and leakage contract

- The raw file is immutable evidence. Missingness and anomalies are reported, not repaired in Phase 1.
- Repeated transaction hashes are not automatically duplicates: a transaction can contain multiple legitimate instructions.
- Wallets and transaction hashes are identifiers, not predictors.
- `prev_event_time`, `seconds_since_prev`, and `source_week` require lineage validation and must not be accepted as leakage-safe merely because they are supplied.
- Future preprocessing must fit transformations inside training folds and use chronological validation appropriate to the scoring question.
- Phase 2 performs no fitted imputation, scaling, encoding, resampling, or feature selection. Missing fees remain unavailable, and the IQR flag is review-only rather than a model input.
- Phase 3 filters strictly before every scoring cutoff and uses closed-open lookback windows. A wallet with no prior event gets no snapshot row; single-event gap values remain missing.
- Phase 3 recomputes temporal history from validated event time and does not use supplied `prev_event_time`, `seconds_since_prev`, or `source_week`.
- Phase 4A accepts only externally supplied, independently verified binary labels with matching wallets/domain, explicit scoring/evidence/knowledge times, a mature outcome window, a stable evidence reference, and a versioned definition.
- The historical 249 and 18 heuristic candidates are not ground truth and must not be used for supervised evaluation.
- Random row-level splitting of repeated wallet snapshots is prohibited; a future primary evaluation must be chronological and wallet-disjoint unless a different estimand is explicitly approved.
- No label, counterparty edge, fraudulent behaviour, probability, metric, or model result is fabricated.
- Phase 4B fits every imputer, scaler and detector on the earliest cutoff only. Later full-cutoff scores are dependent longitudinal diagnostics, and wallet-disjoint entrant cohorts are reported separately.
- Phase 4B model scores and top-budget lists are unverified anomaly-screening outputs, never confirmed fraud, wash-trading outcomes or calibrated probabilities.

## Approved architecture

All assessed components remain in one repository with clear boundaries:

- Local Python ingestion, audit, point-in-time features, training, evaluation, serialization, and shared inference transformations live in `src/solana_risk/`.
- The Phase 5A FastAPI foundation imports the shared feature builder and loads no model artifact. Phase 5B packages it for local Docker/Compose use. A later, explicitly approved scoring extension may load an already-created artifact; it will never train at startup or during prediction.
- A future React + Vite static frontend will communicate with the API over HTTPS/JSON and eventually use Firebase Hosting.
- Core Python stays provider-neutral. Configuration uses environment variables; frontend code contains no credentials; CORS is restricted to approved deployed and local origins.

Local Docker/Compose validation is complete. Frontend, Google Cloud Run, Firebase, and promotion of predictive scoring require later explicit approval and are not deployment claims.

## Repository layout

```text
README.md                       Scope, setup, constraints, and phase status
pyproject.toml                  Python package and test dependencies
src/solana_risk/data/audit.py  Deterministic Phase 1 audit and CLI
src/solana_risk/data/preprocess.py  Deterministic Phase 2 cleaning and CLI
src/solana_risk/features/build.py  Point-in-time feature registry, builder, reports, and CLI
src/solana_risk/labels/validate.py  Fail-closed external-label evidence contract
src/solana_risk/models/          Provisional anomaly training, evaluation, and robust baseline
src/solana_risk/api/             FastAPI schemas, configuration, feature adapter, routes, and app factory
Dockerfile                       Multi-stage non-root API image
docker-compose.yml               One-service local deployment with health and security controls
.dockerignore                    Private/generated build-context exclusions
scripts/container_smoke_test.py  Synthetic image/runtime/endpoint validation
notebooks/01_exploratory_data_analysis.ipynb  Reproducible descriptive EDA
notebooks/02_feature_engineering.ipynb  Reusable-module feature analysis and leakage check
notebooks/03_unsupervised_anomaly_modelling.ipynb  Provisional anomaly experiment
tests/                          Scaffold, audit, preprocessing, feature, and label-contract tests
docs/data_audit_findings.md     Tracked findings from the immutable root dataset
docs/preprocessing_findings.md  Versioned Phase 2 rules, counts, and limitations
docs/feature_registry.md        Versioned feature definitions, units, missingness, and lineage
docs/feature_engineering_findings.md  Phase 3 results, controls, and blockers
docs/label_evidence_and_readiness.md  Phase 4A provenance findings and readiness decision
docs/modelling_evaluation_plan.md  Conditional target, split, and metric plan
docs/experimental_modelling_findings.md  Phase 4B evidence and limitations
docs/anomaly_model_comparison.md  Detector configuration and stability comparison
docs/api_contract.md              Phase 5A endpoints, validation, examples, and errors
docs/api_implementation_findings.md  Feature parity, security decisions, and limitations
docs/containerization_and_local_deployment.md  Build, Compose, and future Cloud Run compatibility
docs/container_validation_results.md  Observed local image and endpoint evidence
docs/lab_traceability.md        Verified lecturer-example mapping
docs/decision_log.md            Decisions and unresolved evidence requirements
reports/data_audit/             Generated local reports (Git-ignored)
```

## Student-operated Git helper

The executable `commit.sh` lets the student review, stage, commit, and push one genuine milestone interactively:

```bash
./commit.sh
```

The student must run it personally. The helper checks the local Git identity, displays pending and staged files, blocks private instructions, secrets, raw datasets, and generated artifacts, and pushes without force. It does not amend, reset, rebase, bypass hooks, rewrite history, delete files, or store credentials.

## Gated milestones

1. **Phase 0 — foundation:** documentation, package scaffold, lab mapping, and test runner. Complete.
2. **Phase 1 — data integrity:** audit the single root dataset, record checksum and provenance gaps, and enforce label/edge readiness gates. Complete.
3. **Phase 2 — preprocessing:** deterministic parsing, ordering, invalid-row handling, and event-grain policy. Implemented; scientific blockers remain documented.
4. **Phase 3 — features:** strict point-in-time wallet features and reproducible notebooks. Complete.
5. **Phase 4A — label evidence/readiness:** trace candidate-label provenance, define the target/evaluation contract, and validate external evidence fail-closed. Complete; decision is **REVISION REQUIRED** and supervised training remains **BLOCKED**.
6. **Phase 4B — provisional unsupervised experiment:** reproducible label-free detectors, chronological diagnostics, sensitivity, drift, and notebook. Implemented experimentally; methodology remains **NOT SUPERVISOR-APPROVED** and no model is production-approved.
7. **Phase 5A — service foundation:** FastAPI health/readiness gates, descriptive shared-code feature preview, bounded validation, OpenAPI, and HTTP tests. Complete; prediction remains unavailable and no model artifact is loaded.
8. **Phase 5B — container delivery:** non-root Docker image, restricted Compose service, content checks, endpoint smoke tests, configurable port, and graceful shutdown. Complete locally; no cloud deployment was performed.
9. **Phase 6 — submission evidence:** architecture, model/data cards, report or slides, limitations, and reproducibility evidence. Not started.

Each phase stops for student review and a student-authored commit before the next begins.

## Lecturer alignment

The audit, preprocessing, EDA, feature implementation, Phase 4A gate, Phase 4B experiment, API, and local container follow the verified lab sequence for inspection before treatment, explicit parsing, strict `SCORING_TS` filtering, point-in-time entity aggregation, leakage-by-lineage reasoning, fitted transformations inside pipelines, validation/test separation, typed serving, runtime-only packaging, endpoint smoke testing, and cautious anomaly-score interpretation. They adapt the labs to UTC Solana events, immutable source evidence, label-provenance gating, repeated wallet observations, chronological evaluation, and an explicit no-model readiness gate. Exact repository commits, notebook cells, adaptations, and test evidence are recorded in [`docs/lab_traceability.md`](docs/lab_traceability.md).

## Status

**Current phase:** Phase 5B — Docker containerization and local deployment.

**Implementation:** the modular API is installed from packaged source in a digest-pinned Python 3.11 slim image, runs non-root, supports environment-based port/configuration, and is validated directly and through restricted Docker Compose. No model artifact is copied or loaded.

**Model readiness:** **REVISION REQUIRED** overall and **BLOCKED** for supervised learning by absent verified wash-trading labels, NFT-versus-DEX domain mismatch, absent wallet-counterparty edges, sparse cross-month wallet history, and unresolved provenance/licensing.

**Next action:** review and test Phase 5B locally. Do not begin React, Firebase, Google Cloud Run, CI/CD deployment, authentication, or model promotion without explicit approval.
