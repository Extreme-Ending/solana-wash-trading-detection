# Phase 9 local demonstration

## Demonstration boundary

The complete demonstrable path is:

```text
nft.csv -> audit -> deterministic preprocessing -> point-in-time features
        -> offline experimental models -> checksum-pinned FastAPI
        -> authenticated React dashboard
```

The scoring portion is available only in explicitly configured `development` mode. Default and production processes return HTTP 503 `MODEL_NOT_APPROVED`. The demonstration consumes user-supplied event histories and does not retrieve a wallet's blockchain history.

## Prerequisites

- Linux/Bash; supported Python with the pinned `.venv` dependencies (Python 3.11 is the target container runtime).
- Node.js 22.22.2 or later and installed `frontend/node_modules`.
- Local ignored `nft.csv` with the expected SHA-256.
- Local ignored model artifact and manifest, or permission to regenerate them offline.
- For the interactive protected routes: the configured Firebase project, an approved Firebase UID, Google Application Default Credentials for the backend, and an approved Google sign-in account.
- Ports 8080 and 5173 available on loopback.
- Docker only for the separate production-container demonstration; the production image intentionally contains no experimental artifact.

Never paste ID tokens, service-account keys or private environment values into a terminal recording, screenshot, report or Git-tracked file.

## 1. Verify source and reproduce the pipeline

Use a fresh temporary directory so the checked local evidence is not overwritten:

```bash
phase9_run="$(mktemp -d /tmp/solana-phase9-XXXXXX)"
sha256sum nft.csv

PYTHONPATH=src .venv/bin/python -m solana_risk.data.audit \
  --input nft.csv --output-dir "$phase9_run/audit"

PYTHONPATH=src .venv/bin/python -m solana_risk.data.preprocess \
  --input nft.csv \
  --processed-dir "$phase9_run/processed" \
  --report-dir "$phase9_run/preprocessing"

PYTHONPATH=src .venv/bin/python -m solana_risk.features.build \
  --input "$phase9_run/processed/cleaned_events.csv" \
  --output "$phase9_run/wallet_snapshots.csv" \
  --report-dir "$phase9_run/features" \
  --as-of 2025-09-01T00:00:00Z \
  --as-of 2025-10-01T00:00:00Z \
  --as-of 2025-12-01T00:00:00Z

PYTHONPATH=src .venv/bin/python -m solana_risk.models.train_anomaly \
  --input "$phase9_run/wallet_snapshots.csv" \
  --artifact-dir "$phase9_run/artifacts"
```

Expected reconciliation and fingerprints:

| Output | Expected evidence |
|---|---|
| Input | 10,800 events |
| Preprocessing | 10,798 retained, 2 quarantined, 0 removed |
| Feature output | 5,996 snapshots and 29 registered features |
| Cleaned events SHA-256 | `1889adf72a727544a8759203336ac257108d344e2ea71aaa118aa04f0aa50937` |
| Quarantine SHA-256 | `5cab1d4860e5ab2345979085cada6e3a583933f132875209309cb1fe84e9eb38` |
| Snapshot SHA-256 | `779b446b15cce9cdc630353c60ffad2bfae039b086a1e0daa8dd66d05aff3a60` |
| Model SHA-256 | `3e35561b0bf5db42c5b7146e7ff568e313be1beb1be724997356af45f5533035` |
| Manifest SHA-256 | `1551d55f469ac3abd7a985d98055c69375968a2d9e28151e153aea2b61061ad0` |

Inspect the two quarantine reason records from the generated report; do not delete or repair them for presentation convenience.

## 2. Reproduce evaluation and figures

```bash
PYTHONPATH=src .venv/bin/python -m solana_risk.models.evaluate_anomaly \
  --input data/features/wallet_snapshots.csv \
  --artifact artifacts/experimental/anomaly_models.joblib \
  --report-dir reports/modelling

MPLCONFIGDIR=/tmp/solana-phase9-matplotlib \
  .venv/bin/python scripts/generate_phase9_figures.py \
  --output-dir reports/phase9
```

The generator rejects any report that says labels were used, reports confirmed outcomes, has a non-reconciling cleaning count, violates the 29-feature contract, or disagrees with the artifact/snapshot fingerprints.

## 3. Start the local experimental API

Use private shell/environment configuration. The application does not automatically read `.env`:

```bash
export SOLANA_RISK_ENVIRONMENT=development
export SOLANA_RISK_CORS_ORIGINS=http://localhost:5173
export SOLANA_RISK_FIREBASE_PROJECT_ID='<your Firebase project ID>'
export SOLANA_RISK_ALLOWED_UIDS='<your approved Firebase UID>'
export SOLANA_RISK_CHECK_REVOKED_TOKENS=true
export SOLANA_RISK_ENABLE_EXPERIMENTAL_SCORING=true
export SOLANA_RISK_EXPERIMENTAL_MODEL_ARTIFACT=artifacts/experimental/anomaly_models.joblib
export SOLANA_RISK_EXPERIMENTAL_MODEL_MANIFEST=artifacts/experimental/anomaly_models_manifest.json
export SOLANA_RISK_EXPERIMENTAL_ARTIFACT_SHA256='3e35561b0bf5db42c5b7146e7ff568e313be1beb1be724997356af45f5533035'

PYTHONPATH=src .venv/bin/uvicorn solana_risk.api.main:app \
  --host 127.0.0.1 --port 8080
```

Expected checks in another terminal:

```bash
curl --fail http://127.0.0.1:8080/healthz
curl --include http://127.0.0.1:8080/readyz
```

`/healthz` returns 200. `/readyz` deliberately returns 503 because experimental local scoring is not production readiness.

## 4. Start and walk through React

Keep the public Firebase web identifiers in the ignored local frontend environment. Do not place a server credential in any `VITE_*` variable.

```bash
cd frontend
npm run dev
```

Open `http://localhost:5173`, then:

1. explain the audited dataset/evaluation panel and the observation/model/synthetic boundaries;
2. sign in with the approved Google account;
3. load the clearly labelled synthetic single-wallet example and generate its 29-feature preview;
4. inspect feature charts and the strict UTC cutoff behavior;
5. request the experimental single-wallet score and explain its unit and training cutoff;
6. load the synthetic batch, submit a review budget of two, and inspect ranked scores;
7. filter by wallet, event count, history, warnings and score; change deterministic sort order;
8. open wallet detail and explain median/IQR context as descriptive—not model attribution;
9. show rejected histories or validation errors without changing another wallet's features; and
10. finish at the methodology limitations and state that no verified fraud outcome exists.

## 5. Automated fallback evidence

If interactive Firebase credentials or a popup are unavailable, do not disable authentication. Demonstrate the software contract with:

```bash
PYTHONPATH=src .venv/bin/python scripts/audit_local_integration.py

PYTHONPATH=src .venv/bin/python scripts/demonstrate_batch_scoring.py \
  --artifact artifacts/experimental/anomaly_models.joblib \
  --manifest artifacts/experimental/anomaly_models_manifest.json \
  --sha256 "$(sha256sum artifacts/experimental/anomaly_models.joblib | cut -d' ' -f1)"
```

The integration auditor uses a verifier injected only into its process, exactly like a test dependency. It is not a runtime authentication bypass and does not contact Firebase. The synthetic results prove deterministic plumbing only.

## Recovery checklist

| Symptom | Safe recovery |
|---|---|
| `AUTH_VERIFICATION_UNAVAILABLE` | Verify ADC and Firebase project configuration; never add a service key to the repository |
| 401 | Sign in again; confirm a current Firebase ID token is being sent |
| 403 | Confirm verified Google email and server-side UID allowlist |
| 503 `MODEL_NOT_APPROVED` | Confirm development mode and explicit experimental gate; do not change production mode |
| 503 artifact error | Compare artifact, manifest and configured SHA; regenerate locally instead of bypassing validation |
| 422 insufficient history | Ensure at least one valid event is strictly before the UTC cutoff |
| Port already used | stop the unrelated local process or choose a documented alternate; keep origins/proxy aligned |
| Frontend configuration alert | restore the ignored local public Firebase configuration; do not hard-code secrets |

## Known limitations

The interactive Firebase/browser path still requires a student-operated accepted account and local credentials. Automated tests do not establish real popup usability. Synthetic examples are not empirical cases. Dune query 6561080 is the confirmed data source, but extraction metadata and permitted sharing remain incomplete. The Docker production image intentionally cannot serve experimental scores.
