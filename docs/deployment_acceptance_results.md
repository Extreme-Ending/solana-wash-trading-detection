# Phase 12 deployment acceptance results

Date: 2026-11-18 (Africa/Nairobi)

## Status

**Bootstrap: PASS. CI: FAIL pending a tested Node-version correction. Deployment: NO-GO.** No Cloud Run service or Firebase Hosting release has been deployed.

## Read-only environment evidence

| Check | Observed result |
|---|---|
| Git | remote `main` SHA `432c4c252ab1f91e2a1890c1f05e7ae71923b716`; local bootstrap and CI fixes remain uncommitted |
| GitHub | public repository; default `main`; no environments; no branch protection |
| Local tools | Python 3.12.3 (CI targets 3.11), Node 22.23.4, npm 10.9.9, Docker 29.10.0, Compose 5.7.1, gcloud 590.0.0, Firebase CLI 15.33.0 |
| Target project | active `solana-wallet-risk`, project number `441056127470` |
| Local gcloud default | `seotranslate-507816` — unrelated and never selected/mutated |
| Billing | enabled on `solana-wallet-risk` |
| Budget | not verifiable: Budget API/permission was unavailable; no budget claim made |
| Enabled relevant APIs | Cloud Run, Artifact Registry, IAM Credentials, STS, Firebase Hosting and previously enabled Firebase APIs |
| Artifact Registry | empty Docker repository `solana-wallet-risk` in `africa-south1` |
| Service accounts | separate enabled runtime, Cloud Run deployer and Hosting deployer; zero user-managed keys |
| Workload Identity | active `github-actions/github` provider restricted to the exact repository and `main`; exact environment-subject bindings verified |
| Cloud Run | API enabled; no service or URL exists |
| Firebase | project active; default site `solana-wallet-risk` exists |
| Hosting publish | no preview or live publication executed |

## Workflow acceptance

The tracked workflows were validated locally for immutable action pins, minimal permissions, manual-only deployment triggers, exact-SHA CI gating, protected environment names, concurrency, private Cloud Run flags, digest deployment, model-disable configuration, Firebase CLI pinning and Hosting-only publication. Pinned `actionlint` 1.7.7 and ShellCheck 0.10.0 passed locally.

The first hosted [CI run](https://github.com/Extreme-Ending/solana-wash-trading-detection/actions/runs/44274052898) completed with Python, container and workflow-security jobs passing. The frontend job failed before running tests because locked `undici 8.12.4` requires Node 22.19 or newer while CI used Node 22.12. The corrected workflows and project engine use Node 22.22.2, satisfying the stricter `jsdom 31.0.0` minimum as well; a new student-pushed SHA and successful hosted run are required. No registry image digest, Cloud Run revision/URL, Hosting preview URL or live release exists.

## Production and research boundary

The production Docker image contains no experimental artifact or modelling runtime and production configuration explicitly disables experimental scoring. `/readyz`, `/v1/score` and `/v1/score/batch` remain unavailable as designed. The unsupervised Isolation Forest is not a fraud probability and has not been promoted.

The Firebase site can eventually host the static interface, but the browser cannot invoke the IAM-private pilot with only its Firebase token. Frontend-to-backend integration therefore remains **not working in hosted production** until a separately approved access architecture exists.

## GO/NO-GO

- Corrected CI push after student review and commit: **GO**.
- Guarded WIF/bootstrap: **PASS**, independently verified after execution.
- Private Cloud Run workflow: **NO-GO** until corrected CI passes and the protected `private-pilot` environment, variables, UID secret and budget attestation exist.
- Hosting preview: **NO-GO** until corrected CI passes and the protected `hosting-preview` environment and Firebase web variables exist.
- Live Hosting: **NO-GO** until preview acceptance and explicit `production` approval.
- Public Cloud Run or production model scoring: **not authorized and not implemented**.
