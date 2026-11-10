# Detecting Coordinated Wash Trading on Solana

This repository supports the DSA 8401 Applied Machine Learning capstone **“Detecting Coordinated Wash Trading on Solana: A Reproducible Wallet-Risk Scoring Service.”** The intended modelling unit is `(wallet, as_of)`: any future feature must use only events with `block_time < as_of`.

Phase 1 implements a deterministic, read-only inspection of the single root-level dataset, `nft.csv`. It does not clean or transform data, create features or labels, train a model, expose an API, create a frontend, build containers, or deploy cloud resources.

## Phase 1 evidence and blockers

The audited file contains 10,800 rows, 18 columns, and 2,312 unique wallets between 1 January and 30 November 2025 UTC. Its columns and source values support DEX/swap-event semantics, not verified NFT marketplace-sale semantics. Despite the filename, no NFT-specific column is present.

There is no verified wash-trading target and no buyer, seller, or wallet-counterparty field. Supervised wash-trading classification and graph-based coordination features therefore remain blocked. The data also has very limited longitudinal wallet coverage: 2,302 wallets occur in one calendar month and only 10 occur in two months. See [`docs/data_audit_findings.md`](docs/data_audit_findings.md) for the verified findings, assumptions, proposal differences, and Phase 2 prerequisites.

The primary proposal and capstone-rubric PDFs are not present under a local `references/` directory. The implementation therefore records proposal comparisons only where the local approved specification or steering evidence gives a concrete expectation. Provider/API, extraction query, collection method, licence, source snapshot, and independent provenance remain unresolved.

## Install and run

Python 3.11 is the baseline. From the repository root:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
pytest -q
python -m solana_risk.data.audit
```

The CLI resolves `<repository-root>/nft.csv` from the installed module location, so it does not depend on the terminal's current directory. An explicit path is supported for reproducibility and testing:

```bash
python -m solana_risk.data.audit --input /path/to/input.csv
```

It writes deterministic `audit.json` and `audit.md` files to `reports/data_audit/`. That directory and the root dataset are Git-ignored. Reports contain the source SHA-256 but no generation timestamp or absolute source path; wallet, transaction, and token samples are redacted where appropriate. The audit reads only `nft.csv`, never `nft_trades.csv`, and does not modify its input.

For a source checkout that has not yet been installed and a system that exposes only `python3`, the equivalent development invocation is:

```bash
PYTHONPATH=src python3 -m solana_risk.data.audit
```

## Scientific and leakage contract

- The raw file is immutable evidence. Missingness and anomalies are reported, not repaired in Phase 1.
- Repeated transaction hashes are not automatically duplicates: a transaction can contain multiple legitimate instructions.
- Wallets and transaction hashes are identifiers, not predictors.
- `prev_event_time`, `seconds_since_prev`, and `source_week` require lineage validation and must not be accepted as leakage-safe merely because they are supplied.
- Future preprocessing must fit transformations inside training folds and use chronological validation appropriate to the scoring question.
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
tests/                          Scaffold and synthetic audit tests
docs/data_audit_findings.md     Tracked findings from the immutable root dataset
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
2. **Phase 1 — data integrity:** audit the single root dataset, record checksum and provenance gaps, and enforce label/edge readiness gates. Implemented; scientific blockers remain documented.
3. **Phase 2 — preprocessing:** deterministic parsing, ordering, invalid-row handling, and event-grain policy. Not started.
4. **Phase 3 — features:** strict point-in-time wallet features. Not started.
5. **Phase 4 — supervised gate:** validate external labels; train and evaluate only if the gate passes. Not started.
6. **Phase 5 — local serving:** FastAPI, readiness semantics, Docker/Compose, and smoke tests. Not started.
7. **Phase 6 — submission evidence:** architecture, model/data cards, report or slides, limitations, and reproducibility evidence. Not started.

Each phase stops for student review and a student-authored commit before the next begins.

## Lecturer alignment

The audit follows the verified Lab 2 sequence for shape/schema inspection, missingness, duplicate review, validity checks, and leakage-by-lineage reasoning while adapting it to UTC Solana events and the `(wallet, as_of)` estimand. Exact repository commit, notebook paths, observed principles, adaptations, and test evidence are recorded in [`docs/lab_traceability.md`](docs/lab_traceability.md).

## Status

**Current phase:** Phase 1 — dataset inspection and data-quality audit.

**Implementation:** complete and tested for the approved Phase 1 scope.

**Model readiness:** blocked by absent verified wash-trading labels, absent wallet-counterparty edges, sparse cross-month wallet history, and unresolved provenance/licensing.

**Next action:** student review and explicit approval are required before Phase 2.
