# Lecturer lab traceability

## Reference snapshot

- Repository: `https://github.com/NUELBUNDI/AML_Book-Data`
- Branch inspected: `master`
- Exact commit: `1ad78cc1ccaa6aa92e081893e3ea0cd380a1f950`
- Commit timestamp: `2026-11-02T20:35:51+03:00`
- Inspected on: `2026-11-07`
- Snapshot rechecked locally on: `2026-11-08`
- Method: temporary read-only clone under `/tmp`; no course files were copied into or used as a scaffold for this repository.

The paths and observations below were verified from actual files at that commit. They are not inferred solely from directory names.

## Files actually consulted

| Lecturer repository path | Directly observed concept | Capstone use or adaptation |
|---|---|---|
| `README.md` | Lab 2 overview: raw audit, mixed-format cleaning, entity resolution, scoring-time features, lineage-based leak review, and a `ColumnTransformer`/`Pipeline`. It also warns that the notebook has a Windows absolute data path. | Retain the scientific sequence, use repository-relative inputs, and avoid claiming the class dataset or result applies to Solana. |
| `notebook/lab2_solution.ipynb` | Measures missingness and duplicate rows; discusses MCAR/MAR/MNAR; parses amounts/times; resolves an entity; filters strictly before `SCORING_TS`; builds RFM, ratio, and cyclical features; identifies post-outcome fields by lineage; fits imputers, transforms, encoders, and logistic regression in one pipeline; uses `GroupKFold`. | Primary conceptual reference. Future implementation will use `(wallet, as_of)`, UTC timestamps, `block_time < as_of`, wallet-safe identity, and fitted transforms inside folds. The approved chronological evaluation replaces blind use of group-only CV, with wallet/event overlap guards where needed. Correlation is only a screen, never the leakage decision. |
| `notebook/End_to_End_ML_ProcessClass Pratical.ipynb` | Separates target/features, constructs numeric/categorical transforms, compares baseline and ensemble classifiers, reports probability-based metrics, and explores cost-sensitive thresholds. The notebook fits `preprocessor` on all `X` before `train_test_split`. | Model comparison, PR-AUC, and business-cost ideas may inform later labelled work. The demonstrated pre-split fit and random holdout are **not** adopted because they leak fitted preprocessing and conflict with the capstone’s time-based estimand. |
| `lab10_fastapi/train_model.py` | Trains a class-weighted random forest, records feature order, and serializes a model bundle. | Later artifacts must preserve feature schema, but training is forbidden until labels pass provenance checks. Random splitting is not suitable here. |
| `lab10_fastapi/train_mlflow.py` | Uses separate train/validation/test partitions, optimizes PR-AUC on validation, selects a threshold on validation, reports on test, logs metadata, and exports an artifact. | Later labelled work should preserve validation-versus-holdout roles and feature metadata. It must use chronological splitting and a predeclared review-budget policy; MLflow and Optuna are not Phase 0 requirements. |
| `lab10_fastapi/api/main.py` | Loads a model once, uses a Pydantic request schema, enforces training feature order, and exposes health/prediction routes. | Later API code should retain typed validation and train/serve schema parity. Unlike this example, it must distinguish liveness from readiness and return a clear non-success response when no verified model exists. |
| `fraud_mlops/README.md` and `fraud_mlops/train.py` | Organizes training, experiment metadata, a quality gate, artifact export, and deployment as separate layers. | The layering is useful, but an F1 gate cannot replace the missing-label gate and the class example’s holdout-driven model choice is not copied. No MLflow component is justified yet. |
| `fraud_mlops/api/main.py` and `fraud_mlops/tests/test_api.py` | Serves model metadata, validates complete inputs, tests health/model/prediction paths, and expects malformed requests to return HTTP 422. | Future service tests should cover health, readiness, metadata, malformed events, and fail-closed prediction. Phase 0 adopts only the principle that runnable interfaces need automated tests. |
| `fraud_mlops/Dockerfile` and `.github/workflows/fraud-mlops.yml` | Separates serving dependencies, builds an image, tests endpoints, and smoke-tests the container after training. | Docker and CI are deferred to Phase 5. A future image must not require or fabricate a model when supervised readiness is blocked. Codex will not configure automated commits or pushes. |
| `mlflow_simple/README.md`, `mlflow_simple/train.py`, `mlflow_simple/predict.py`, and `mlflow_simple/test_model.py` | Demonstrates experiment tracking, a model-quality gate, registry lookup, prediction, and automated artifact behaviour checks. | Useful lifecycle separation, but breast-cancer accuracy thresholds and registry choices do not transfer to this task. Tracking infrastructure remains out of scope unless later justified. |

## Implemented-component mapping

| Component | Lecturer principle | Student repository equivalent | Why adapted | Test or reproducibility evidence |
|---|---|---|---|---|
| Importable package scaffold | Runnable logic should live outside exploratory notebooks; examples separate executable Python from explanatory material. | `src/solana_risk/__init__.py` | Phase 0 exposes metadata only so later phases can add importable modules without prematurely implementing the pipeline. | `tests/test_scaffold.py::test_package_exposes_initial_version` |
| Automated scaffold check | `fraud_mlops/tests/test_api.py` and `mlflow_simple/test_model.py` make runnable claims testable. | `tests/test_scaffold.py` | There is no model or API to test yet; the test asserts only the claim Phase 0 actually makes. | `pytest -q` |
| Architecture and scientific constraints | Lab 2 orders audit, cleaning, point-in-time features, leak review, and fitted pipelines. | `README.md` target architecture and `docs/decision_log.md` | Adds an explicit label-provenance gate and chronological validation required by the approved Solana question. | Human review plus exact reference commit recorded above. |
| Serving/deployment boundary plan | `lab10_fastapi/api/main.py`, `fraud_mlops/api/main.py`, `fraud_mlops/Dockerfile`, and `.github/workflows/fraud-mlops.yml` separate inference code, serving dependencies, tests, and container smoke checks. | Documented future `src/`, `api/`, and `frontend/` boundaries in `README.md`; only `src/` exists in Phase 0. | Training remains local and outside the future serving container. Cloud Run and Firebase Hosting are user-approved targets, not claims derived from the lecturer examples and not implemented in this phase. | Human review of `README.md`; absence of `api/`, `frontend/`, Docker, and cloud configuration confirmed by repository inspection. |
| Package/test configuration | Course examples list reproducible dependencies and runnable commands. | `pyproject.toml` | Only the currently needed test dependency is pinned; data/ML/API dependencies are deferred until their implementation phase. | Parse `pyproject.toml` with Python `tomllib`; run `pytest -q`. |
| Shape, schema, sample, and type inspection | `notebook/lab2_solution.ipynb` begins its raw audit by inspecting dimensions, columns/types, and representative values before transformation. | `src/solana_risk/data/audit.py` schema and redacted sample summary | The capstone uses the one immutable root CSV and redacts wallet, transaction, and token identifiers. It records evidence without cleaning. | `tests/test_data_audit.py`; generated `reports/data_audit/audit.json`; tracked `docs/data_audit_findings.md`. |
| Missingness and duplicate review | Lab 2 calculates null counts and duplicate rows and discusses MCAR, MAR, and MNAR before choosing treatment. | Per-column missing counts/percentages; exact-row, transaction-hash, and instruction-key duplicate measures | Missingness mechanisms are not asserted without extraction evidence. Repeated transaction hashes are separated from exact duplicates because multi-instruction swaps can be valid. | Synthetic missing/duplicate test plus verified counts in `docs/data_audit_findings.md`. |
| Parsing and validity checks | Lab 2 validates and parses mixed time/amount fields before downstream use. | UTC timestamp format/parse audit, numeric percentiles, nonpositive counts, IQR diagnostic, identifier checks, and derived-time consistency checks | Phase 1 reports anomalies but performs no repair. IQR flags are diagnostics, not automatic deletion rules. | Timestamp-failure, malformed-input, empty-input, and required-field tests. |
| Point-in-time and leakage review | Lab 2 filters strictly before `SCORING_TS` and reviews leakage by field lineage, not correlation alone. | Temporal coverage/history audit and explicit warnings for identifiers and supplied `prev_event_time`, `seconds_since_prev`, and `source_week` | The future unit is `(wallet, as_of)` with `block_time < as_of`. Sparse cross-month overlap and absent labels are reported as readiness blockers. | Deterministic temporal summaries and `docs/data_audit_findings.md`. |
| Reproducible executable audit | Course examples put repeatable logic into runnable notebooks/scripts and test runnable claims. | `python -m solana_risk.data.audit`, explicit `--input`, stable JSON/Markdown, source SHA-256, Git-ignored generated output | No generation timestamp or absolute path enters the report, so identical input/code yields identical output. The module resolves the root independently of CWD and never writes the input. | Determinism, input-immutability, and root-path tests; pre/post root-file checksum comparison. |

## Future mappings (not implemented in Phase 1)

| Future component | Lecturer source concept | Required Solana adaptation |
|---|---|---|
| Entity and temporal features | Lab 2 entity resolution, strict `SCORING_TS`, RFM/ratio/cyclical features | Wallet is already the entity; never merge wallets via display labels or token sharing. Recompute temporal history from validated events and enforce `block_time < as_of`. |
| Leakage-safe modelling | Lab 2 pipeline and grouped CV | Keep transforms inside folds, exclude identifiers/post-outcome fields, and use chronological validation plus overlap/embargo controls appropriate to `(wallet, as_of)`. Training stays blocked without independently verified labels. |
| Serving | `lab10_fastapi/api/main.py` and `fraud_mlops/api/main.py` | Add separate health/readiness semantics, explicit label/model-not-ready errors, bounded validated event input, UTC cutoffs, and exact train/serve feature parity. |
| Delivery | `fraud_mlops/Dockerfile` and workflow | Build and smoke-test locally only in Phase 5; never use container or cloud success as evidence that the supervised scientific claim is valid. React/Vite, Firebase Hosting, Cloud Run, and live integration are separate later approvals. |

## Deliberate non-copying

- The Lab 2 notebook’s absolute Windows path is not reused.
- The end-to-end practical’s pre-split `fit_transform` is not reused.
- Random or group-only splitting is not assumed suitable for temporal wallet scoring.
- The lecturer datasets, labels, metrics, thresholds, and model artifacts are not transferred to this capstone.
- The FastAPI examples’ eager assumption of an available fitted model is not reused for the no-label state.
- No course notebook outputs or source files are copied into the student repository.
