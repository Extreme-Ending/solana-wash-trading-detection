# Detecting Coordinated Wash Trading on Solana

This repository supports the DSA 8401 Applied Machine Learning capstone **“Detecting Coordinated Wash Trading on Solana: A Reproducible Wallet-Risk Scoring Service.”** The intended modelling unit is `(wallet, as_of)`: any future feature must use only events with `block_time < as_of`.

Phase 3 adds deterministic point-in-time wallet feature snapshots and two reproducible Jupyter notebooks on top of the Phase 2 validated events. It does not create labels, fit statistical transforms, train a model, infer graph edges, expose an API, create a frontend, build containers, or deploy cloud resources.

## Phase 3 evidence and blockers

The audited file contains 10,800 rows, 18 columns, and 2,312 unique wallets between 1 January and 30 November 2025 UTC. Its columns and source values support DEX/swap-event semantics, not verified NFT marketplace-sale semantics. Despite the filename, no NFT-specific column is present.

There is no verified wash-trading target and no buyer, seller, or wallet-counterparty field. Supervised wash-trading classification and graph-based coordination features therefore remain blocked. The data also has very limited longitudinal wallet coverage: 2,302 wallets occur in one calendar month and only 10 occur in two months. See [`docs/data_audit_findings.md`](docs/data_audit_findings.md) for the Phase 1 evidence and [`docs/preprocessing_findings.md`](docs/preprocessing_findings.md) for the Phase 2 rules and results.

Phase 2 retains 10,798 events and quarantines 2 records whose `amount_in` and `amount_usd` are both zero. It permanently removes zero records: quarantined source evidence remains in a separate output with explicit reason codes. The 7,303 missing fees remain missing with indicators rather than being replaced with zero. All 1,099 IQR review flags remain uncapped and retained. Formatting-only DEX normalization reduces 48 raw spellings to 41 canonical labels without merging differently named protocol variants.

Phase 3 produces 29 registered behavioral/data-quality fields for explicit `(wallet, as_of)` cutoffs. At `2025-09-01`, `2025-10-01`, and `2025-12-01` UTC it produces 1,754, 1,930, and 2,312 wallet rows respectively. Strict cutoff, window-boundary, missing-history, determinism, registry, and no-target tests are automated. See [`docs/feature_registry.md`](docs/feature_registry.md) and [`docs/feature_engineering_findings.md`](docs/feature_engineering_findings.md).

The primary proposal and capstone-rubric PDFs are not present under a local `references/` directory. `AI_USE.md` is also absent by student decision, although the steering rubric identifies an AI-use statement as required submission evidence. Provider/API, extraction query, collection method, licence, source snapshot, and independent provenance remain unresolved.

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
```

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
- No label, counterparty edge, fraudulent behaviour, probability, metric, or model result is fabricated.

## Approved architecture (future milestones)

All assessed components remain in one repository with clear boundaries:

- Local Python ingestion, audit, point-in-time features, training, evaluation, serialization, and shared inference transformations live in `src/solana_risk/`.
- A future lightweight FastAPI backend will load an already-created artifact and eventually run in Docker on Google Cloud Run. It will never train at startup or during prediction.
- A future React + Vite static frontend will communicate with the API over HTTPS/JSON and eventually use Firebase Hosting.
- Core Python stays provider-neutral. Configuration uses environment variables; frontend code contains no credentials; CORS is restricted to approved deployed and local origins.

These are architecture decisions, not deployment claims. API, frontend, Docker, Google Cloud Run, and Firebase work require later explicit approval.

## Repository layout

```text
README.md                       Scope, setup, constraints, and phase status
pyproject.toml                  Python package and test dependencies
src/solana_risk/data/audit.py  Deterministic Phase 1 audit and CLI
src/solana_risk/data/preprocess.py  Deterministic Phase 2 cleaning and CLI
src/solana_risk/features/build.py  Point-in-time feature registry, builder, reports, and CLI
notebooks/01_exploratory_data_analysis.ipynb  Reproducible descriptive EDA
notebooks/02_feature_engineering.ipynb  Reusable-module feature analysis and leakage check
tests/                          Scaffold, audit, preprocessing, and feature tests
docs/data_audit_findings.md     Tracked findings from the immutable root dataset
docs/preprocessing_findings.md  Versioned Phase 2 rules, counts, and limitations
docs/feature_registry.md        Versioned feature definitions, units, missingness, and lineage
docs/feature_engineering_findings.md  Phase 3 results, controls, and blockers
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
5. **Phase 4 — supervised gate:** validate external labels; train and evaluate only if the gate passes. Not started.
6. **Phase 5 — local serving:** FastAPI, readiness semantics, Docker/Compose, and smoke tests. Not started.
7. **Phase 6 — submission evidence:** architecture, model/data cards, report or slides, limitations, and reproducibility evidence. Not started.

Each phase stops for student review and a student-authored commit before the next begins.

## Lecturer alignment

The audit, preprocessing, EDA, and feature implementation follow the verified Lab 2 sequence for inspection before treatment, exact-duplicate review, explicit parsing, strict `SCORING_TS` filtering, point-in-time entity aggregation, and leakage-by-lineage reasoning. They adapt the lab to UTC Solana events, conservative instruction grain, immutable source evidence, multiple `(wallet, as_of)` observations, and chronological validation requirements. Exact repository commit, notebook cells, adaptations, and test evidence are recorded in [`docs/lab_traceability.md`](docs/lab_traceability.md).

## Status

**Current phase:** Phase 3 — point-in-time wallet features and notebooks.

**Implementation:** complete and tested for the approved Phase 3 scope.

**Model readiness:** blocked by absent verified wash-trading labels, absent wallet-counterparty edges, sparse cross-month wallet history, and unresolved provenance/licensing.

**Next action:** student review and explicit approval are required before Phase 4. Supervised work cannot proceed unless the verified-label gate also passes.
