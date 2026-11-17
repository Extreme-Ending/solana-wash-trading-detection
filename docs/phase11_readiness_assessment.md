# Phase 11 readiness assessment

## Decision

**FAIL.** The production-shaped application passed local acceptance, but the required deployment and live cloud acceptance did not occur because billing is disabled and required cloud services/resources are unavailable. A local pass cannot substitute for Artifact Registry, Cloud Run, live IAM, HTTPS or logging evidence.

## Acceptance matrix

| Area | Required result | Phase 11 result |
|---|---|---|
| Docker image | Successful build | **PASS locally** |
| Artifact Registry | Image pushed and digest recorded | **FAIL / not attempted** — billing and API blocker |
| Cloud Run | Service deployed | **FAIL / not attempted** — billing and API blocker |
| Container startup | Successful | **PASS locally only** |
| Health endpoint | HTTP 200 | **PASS locally; untested in cloud** |
| Authentication | Negative cases rejected | **PASS locally; untested in cloud** |
| Model restrictions | Preserved | **PASS locally; no cloud revision** |
| API requests | Correct responses | **PASS locally; untested in cloud** |
| Frontend connection | Passed or documented blocker | **BLOCKED and documented** |
| Cloud logs | Reviewed | **Unavailable** |
| Security | No unauthorized access | **Local controls pass; live IAM unverified** |
| Cost controls | Verified | **FAIL** — billing owner/budget/spend cap unavailable |
| Rollback | Procedure documented | **PASS as procedure; not executable/tested yet** |

## Evidence-backed findings

- Project identity is consistent between repository Firebase configuration and the readable Google Cloud project: `solana-wallet-risk`.
- The local release artifact is reproducible, non-root, bounded and fail-closed.
- The deployment defaults now enforce min 0/max 1.
- Firebase application authentication is implemented, but it does not replace Cloud Run invoker IAM.
- The current frontend cannot directly invoke an IAM-private Cloud Run core without an additional trusted identity layer.
- Production scoring remains disabled; `/readyz` and an authorized score request intentionally return 503 `MODEL_NOT_APPROVED`.
- No verified wash-trading labels, fraud-performance metrics or public deployment claim has been introduced.

## Blocking prerequisites

1. Student-owned billing decision and attached billing account.
2. Budget alerts and separate spend-cap review.
3. Required APIs enabled after cost/permission review.
4. Dedicated runtime identity created with least-privilege Firebase user-read access.
5. Regional Artifact Registry repository and cleanup policy.
6. Verified deployer permissions and runtime service-account impersonation.
7. Ignored live deployment environment assembled and reviewed without exposing the UID allowlist.
8. Private image push/deploy followed by actual two-token HTTPS tests and log review.
9. Separate architecture decision before any browser-reachable/public platform endpoint.

## Recommended next action

Resolve billing and identity prerequisites outside the repository, then rerun **Phase 11 deployment execution** from the preflight gate. Do not begin another modelling or academic phase, and do not make the core public merely to unblock the browser.
