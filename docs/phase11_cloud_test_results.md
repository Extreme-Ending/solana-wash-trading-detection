# Phase 11 test results

## Scope distinction

All HTTP results below are local unless explicitly labelled cloud. **No live Cloud Run HTTP test was executed** because no service was deployed. Local results are not presented as cloud evidence.

## Local acceptance results

| Command or check | Observed result |
|---|---|
| `.venv/bin/python -m pytest` | 205 passed in 14.55 s |
| `npm test -- --run` in `frontend/` | 10 files and 72 tests passed in 2.69 s |
| `npm run typecheck` in `frontend/` | Passed |
| `npm run build` in `frontend/` | Passed; 49 modules transformed |
| `bash -n scripts/deployment.sh` | Passed |
| Focused deployment/container pytest set | 25 passed in 0.21 s |
| Production Docker build | Passed |
| `scripts/container_smoke_test.py` | Passed |
| `scripts/audit_local_integration.py` | Passed against the registered experimental artifact through in-process ASGI transport |
| `scripts/validate_deployment_bundle.py frontend/dist` | Passed; 4 files checked |
| `git diff --check` before documentation | Passed |

## Local container observations

| Check | Result |
|---|---|
| Runtime user | UID/GID `10001:10001` |
| Entrypoint | `python -m solana_risk.api.run` |
| Default health | `/healthz` returned 200 |
| Intentional readiness | `/readyz` returned 503 `MODEL_NOT_APPROVED` |
| Missing auth, feature preview | 401 |
| Missing auth, score | 401 |
| Custom container port | `PORT=9090` returned health 200 |
| Graceful stop | Exit code 0 |
| Image-content/import checks | Passed |

The integration audit additionally observed missing, malformed and expired application credentials returning 401; an injected test-only authorized identity could preview features; and production scoring returned 503. The injected verifier did not contact Firebase and is software evidence only.

## Cloud discovery checks

| Check | Observed result |
|---|---|
| Active account | Present |
| Target project | Active and readable |
| Billing | Disabled |
| Required APIs | Cloud Run, Artifact Registry, Cloud Build and IAM Credentials not enabled |
| Runtime service account | `NOT_FOUND` |
| Registry discovery | Blocked by disabled Artifact Registry API |
| Cloud Run discovery | Blocked by disabled Cloud Run Admin API |

## Live acceptance tests

| Required live test | Status |
|---|---|
| Revision active and container startup | Not run; no revision |
| Cloud URL `/healthz` 200 | Not run; no service URL |
| Cloud URL `/readyz` 503 | Not run; no service URL |
| Missing/invalid/expired token rejection | Not run in cloud |
| Unauthorized UID rejection | Not run in cloud |
| Authorized feature preview | Not run in cloud |
| Authorized score returns 503 | Not run in cloud |
| Cloud logs reviewed | Not available |
| Runtime IAM verified | Not available |

Unavailable tests are intentionally not marked as passed.
