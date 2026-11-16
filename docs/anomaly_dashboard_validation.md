# Phase 8C anomaly dashboard validation

## Scope

Phase 8C turns the authenticated Phase 8B batch response into a local analyst-review interface. It does not fetch wallet history, retrain or promote a model, select a fraud threshold, create a wash-trading label, or deploy anything. Default and production scoring remain HTTP 503 `MODEL_NOT_APPROVED`.

## Evidence flow

1. The student supplies bounded, explicitly separated wallet histories and one UTC `as_of` timestamp.
2. FastAPI authenticates the request, applies the existing point-in-time feature builder independently to each eligible wallet, and produces the existing model-specific scores and deterministic ranks.
3. The successful response includes the exact 29 feature values for each scored wallet and a versioned aggregate reference fitted only from the earliest Phase 3 training cutoff.
4. React rejects incompatible response metadata before rendering. It then displays the returned counts, values, scores, ranks, selections, warnings and rejections without recomputing model outputs.
5. Client-side filters and sorts change only the visible ordering. Selecting a wallet opens manual-review context; changing the review budget requires a new authenticated request.

## Visual and interaction coverage

- Summary cards show submitted, scored, rejected, applied review capacity, selected count, model/version and scoring cutoff.
- Ranked bars retain actual six-decimal scores, original rank, review status and the full wallet identifier via the table/title.
- Fewer than five visible wallets use a dot view. Five or more use count-preserving histogram bins. Neither view implies a probability or normal class.
- Filters cover wallet substring, review selection, minimum events, minimum history, warnings and score range. Sorts cover score, original rank, event count, history duration and wallet identifier with deterministic original-rank/wallet tie handling.
- Wallet detail shows full identity, score/rank/review state, model/cutoffs, event and history metadata, warnings and all 29 registry-grouped features.
- Training comparison displays median and Q1–Q3. Robust IQR distance is shown only for finite, non-binary, non-constant values with non-zero IQR. Binary fields show training true share; unsupported comparisons say why they are unavailable.
- CSS layouts collapse at 900 px and 680 px, tables scroll horizontally, semantic labels/tables/status regions remain available, and reduced-motion preferences are respected.

## Reproducible local artifact evidence

The Phase 8C regeneration used `data/features/wallet_snapshots.csv` and produced an ignored local artifact with:

- artifact SHA-256: `3e35561b0bf5db42c5b7146e7ff568e313be1beb1be724997356af45f5533035`;
- snapshot SHA-256: `779b446b15cce9cdc630353c60ffad2bfae039b086a1e0daa8dd66d05aff3a60`;
- registry SHA-256: `75be47d7f875e2a04848d8b8b7931d7f90d7bbf3c5aa2b3476a827e09e2d4e8a`;
- reference version: `training_reference_v1`;
- training cutoff: `2025-09-01T00:00:00+00:00`; and
- training-reference wallets: 1,754.

The synthetic demonstration remained deterministic and preserved single/batch equality. It returned scores 0.7112287827056774 (bursty), 0.5244905161109438 (steady), and 0.45179068711851816 (sparse). These values demonstrate plumbing only, not fraud-detection performance.

## Scientific interpretation boundary

An anomaly score is a model-specific indicator of unusualness relative to the fitted reference. Rank depends on the other successfully scored wallets in the submitted batch. Review selection represents stated analyst capacity. Feature-reference differences are descriptive and do not reveal Isolation Forest feature attribution. None of these outputs is a probability, verified label, confirmed wash trading, fraud finding, intent assessment or causal explanation.

## Validation limitations

Automated DOM tests exercise desktop/mobile-compatible semantic structure, charts, filters, sorting, details, missing/constant/binary comparisons, rejections and budget-change behavior. The production build verifies compilation and bundling. No browser screenshot is claimed unless separately captured by the student; jsdom does not provide a real layout engine. The supplied DEX events and training snapshots still lack independently verified wash-trading outcomes, direct counterparty edges and resolved source/licensing provenance.

## Observed local validation

| Command | Result |
|---|---|
| `.venv/bin/pytest -q` | PASS — 201 tests |
| `cd frontend && npm test` | PASS — 71 tests in 10 files |
| `cd frontend && npm run typecheck` | PASS |
| `cd frontend && npm run build` | PASS — 47 modules transformed |
| `.venv/bin/python -m solana_risk.models.train_anomaly` | PASS — ignored artifact and manifest regenerated |
| `.venv/bin/python scripts/demonstrate_batch_scoring.py ...` | PASS — deterministic repeat and single/batch equivalence |
| `docker compose config --quiet` | PASS |
| `.venv/bin/python scripts/container_smoke_test.py --host-port 18080 --custom-host-port 18082` | PASS after one dependency-download timeout and retry — content exclusions, non-root UID 10001, health 200, readiness 503, unauthenticated protected routes 401, custom port 9090 and graceful exit 0 |
| `.venv/bin/python scripts/validate_deployment_bundle.py frontend/dist` | PASS — 3 generated files checked for excluded private content |
| `git diff --check` | PASS |
| `bash -n commit.sh` | PASS; the workflow was not executed |
