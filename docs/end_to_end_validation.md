# Phase 8D end-to-end validation

## Audit scope and result

This is an independent local integration audit of the repository state on 16 November 2026. It covers the path from the immutable research CSV to the React presentation boundary. It does not establish fraud-detection effectiveness, perform a cloud deployment, or promote the experimental model.

The local pipeline is connected and deterministic. The API uses the actual Phase 4B.1 artifact and the same 29-feature builder used in training. The production configuration still refuses experimental scoring. The remaining end-to-end gap is a hosted, real-Firebase browser session: successful protected-route integration was exercised through the application's documented test-only verifier seam, not by weakening or replacing production Firebase verification.

## Traceability from input to presentation

| Stage | Implementation and control | Observed evidence |
|---|---|---|
| Source | Root `nft.csv`; `audit.py` reads the explicit input and does not mutate it | 10,800 rows, 18 columns; SHA-256 `8f387709c6742f2fc31c19fc32dac27474b6b27b9304786c367a8d8bece81271` |
| Audit | `python -m solana_risk.data.audit` validates schema, grain, times, missingness and identity patterns | Two clean reruns produced identical audit JSON SHA-256 `c32090b1df2bbaf36243b5031c2ae075ef0467daeae64a41d8350315e1739c36` |
| Preprocessing | Invalid essential evidence is quarantined with reason codes; valid rows are normalized and deterministically ordered | 10,800 input = 10,798 retained + 2 quarantined + 0 removed; both clean runs produced cleaned SHA `1889adf72a727544a8759203336ac257108d344e2ea71aaa118aa04f0aa50937` and quarantine SHA `5cab1d4860e5ab2345979085cada6e3a583933f132875209309cb1fe84e9eb38` |
| Features | `build_wallet_snapshots` selects only `block_time < as_of`; registry fixes definitions and order | 5,996 `(wallet, as_of)` snapshots at three cutoffs; both runs and the checked local snapshot have SHA `779b446b15cce9cdc630353c60ffad2bfae039b086a1e0daa8dd66d05aff3a60` |
| Training | Earliest cutoff only fits imputers, scaling where applicable, and three unsupervised comparators | 1,754 wallets at `2025-09-01T00:00:00+00:00`; seed 42; artifact version 4B.1 |
| Evaluation | October validation and December holdout are scored without refitting | Reports repeated-wallet overlap and later-entrant cohorts separately; no label metric or outcome claim is computed |
| Artifact | API loader checks regular files, configured SHA, manifest, runtime versions, registry/order, cutoff and reference statistics before deserializing | Current artifact SHA `3e35561b0bf5db42c5b7146e7ff568e313be1beb1be724997356af45f5533035`; incompatible or corrupt artifacts fail closed |
| FastAPI | Preview and scoring call the shared point-in-time feature service; protected routes require authentication and authorization | Actual-artifact audit returned health 200, readiness 503, preview 200, single score 200 and batch score 200; missing/invalid/expired credentials returned 401 |
| React | Typed response guards preserve score/rank values; filters and sorting operate on the response without recomputing scores | Vitest covers schema checks, unchanged original ranks, review selection, missing/constant/binary/reference cases and failure states |

## Train/serve parity

- `MODEL_FEATURE_COLUMNS` contains exactly 29 ordered features and is consumed by training, the trusted artifact loader, feature preview, single scoring and batch scoring.
- The registry SHA-256 is `75be47d7f875e2a04848d8b8b7931d7f90d7bbf3c5aa2b3476a827e09e2d4e8a` in the current code, manifest and response reference.
- The local integration auditor rejects a preview or training reference whose order or keys differ and established exact equality between every synthetic single-wallet score and its corresponding batch score.
- API `as_of` and event times require explicit UTC. Events at or after `as_of` are excluded, not silently treated as history.
- Frontend response guards reject nonfinite scores, inconsistent counts, rank/order changes, incompatible reference statistics and any schema drift. The dashboard does not transform a raw score into a percentage or class.

## API integration evidence

Run:

```bash
PYTHONPATH=src .venv/bin/python scripts/audit_local_integration.py
```

The script loads the real ignored artifact and manifest, then uses FastAPI's application factory and ASGI transport. Its injected verifier exists only inside the audit process; it does not alter Firebase code or the default/production app. Observed synthetic scores were `0.6509974555401139`, `0.5596084908291551`, and `0.4441462779258222`, ranked 1–3. These values prove deterministic wiring only. They are not probabilities, thresholds, labels or evidence of real-world fraud detection.

The comprehensive API suites additionally cover wrong-project claims, an unapproved UID, verified-email/provider requirements, request bytes and event limits, invalid timestamps, empty histories, mixed-wallet groups, batch limits, rate limiting, artifact corruption, disabled scoring and production fail-closed behavior.

## Realistic workflow boundary

The production frontend build was served locally and opened with installed headless Google Chrome at desktop (1440×1000), tablet (768×1024) and mobile (390×844) dimensions. The visible shell, typography, evidence card and responsive stacking rendered without horizontal clipping in the inspected initial view. This verifies that the unauthenticated shell can load in a real browser and that its initial sign-in boundary renders. It does not verify Google popup usability, keyboard operation of authenticated dashboard controls, a successful Firebase session, protected scoring through the Vite proxy or authenticated charts/tables. Those require an interactive approved account, the exact Firebase project configuration and a non-secret ID token; no token was requested, captured or logged during this audit.

## Confirmed defects and disconnected components

- Phase 8C intentionally changed the artifact bundle, but an older ignored generated evaluation report still cites the Phase 8B digest. Regenerating the ignored evaluation report against the current artifact resolves that local evidence mismatch; tracked source and model parameters are not inconsistent.
- A production build without `VITE_API_BASE_URL` correctly rejected its unsafe default but originally failed before React mounted, producing a blank page. Phase 8D changed startup to render a safe accessible `role="alert"` configuration error. Headless Chrome verified the fail-closed message, and a rebuild with an explicit non-secret HTTPS audit origin rendered normally.
- The runtime Docker image intentionally contains no experimental artifact or modelling dependencies. It validates production fail-closed serving, not local experimental scoring.
- The frontend has no wallet-history provider. Users supply bounded event histories; entering a wallet address alone cannot fetch evidence.
- No direct wallet-counterparty edges exist, so coordination graphs remain unsupported.
- No verified labels exist, so the system cannot validate fraud classifications.

No scoring defect requiring a model or API change was found. Phase 8D added a reproducible actual-artifact integration auditor and edge-case regression tests.

## Automated validation observed

| Command | Result |
|---|---|
| `.venv/bin/python -m pytest -q` | 202 passed in 10.76 s |
| `npm test -- --run` | 10 files, 72 tests passed |
| `npm run typecheck` | passed |
| `VITE_API_BASE_URL=https://api.example.invalid npm run build` | passed; 48 modules transformed |
| `.venv/bin/python scripts/validate_deployment_bundle.py frontend/dist` | PASS; 4 files checked |
| `docker compose config --quiet` | passed |
| `.venv/bin/python scripts/container_smoke_test.py --image solana-wallet-risk-api:phase8d --skip-build --host-port 18082 --custom-host-port 18083` | passed: content/import checks, health 200, readiness 503, protected routes 401, UID 10001, custom port 9090, graceful exit 0 |
| `PYTHONPATH=src .venv/bin/python scripts/audit_local_integration.py` | passed with actual artifact and exact single/batch score equality |
| `bash -n scripts/deployment.sh commit.sh` | passed |
| `.venv/bin/python -m py_compile scripts/audit_local_integration.py` | passed |
| `git diff --check` | passed |

The initial Docker smoke attempt built the image and passed content checks but could not bind host port 8080 because another local process already owned it. Rerunning the same image on unused loopback ports 18082/18083 passed. This was an environment port collision, not an application failure.

## Reproduction commands

```bash
PYTHONPATH=src .venv/bin/python -m solana_risk.data.audit --input nft.csv --output-dir /tmp/phase8d/audit
PYTHONPATH=src .venv/bin/python -m solana_risk.data.preprocess --input nft.csv --processed-dir /tmp/phase8d/processed --report-dir /tmp/phase8d/preprocess-report
PYTHONPATH=src .venv/bin/python -m solana_risk.features.build \
  --input /tmp/phase8d/processed/nft_events_clean.csv \
  --output /tmp/phase8d/wallet_snapshots.csv \
  --report-dir /tmp/phase8d/feature-report \
  --as-of 2025-09-01T00:00:00Z \
  --as-of 2025-10-01T00:00:00Z \
  --as-of 2025-12-01T00:00:00Z
PYTHONPATH=src .venv/bin/python -m solana_risk.models.train_anomaly \
  --input /tmp/phase8d/wallet_snapshots.csv --artifact-dir /tmp/phase8d/artifacts
PYTHONPATH=src .venv/bin/python scripts/audit_local_integration.py
```

Use new temporary directories for a second run, then compare `sha256sum` output and `cmp` results. Do not overwrite the checked local artifact merely to perform the comparison.
