# Phase 12 deployment acceptance results

Date: 2026-11-18 (Africa/Nairobi)

## Status

**WIF bootstrap: PASS. CI: PASS. Deployment: NO-GO.** The third private-pilot attempt passed billing and registry checks, then stopped before image build because the IAM API required for the runtime identity check was not enabled.

## Read-only environment evidence

| Check | Observed result |
|---|---|
| Git | third private-pilot attempt targeted reviewed `main` SHA `e05dfc474698f3db67dac2e6c4c55db2762e5dd7`; IAM API correction remains uncommitted |
| GitHub | public repository; `private-pilot` environment restricted to `main`; repository branch protection remains unverified |
| Local tools | Python 3.12.3 (CI targets 3.11), Node 22.23.4, npm 10.9.9, Docker 29.10.0, Compose 5.7.1, gcloud 590.0.0, Firebase CLI 15.33.0 |
| Target project | active `solana-wallet-risk`, project number `441056127470` |
| Local gcloud default | `seotranslate-507816` — unrelated and never selected/mutated |
| Billing | enabled on `solana-wallet-risk` |
| Budget | not verifiable: Budget API/permission was unavailable; no budget claim made |
| Enabled relevant APIs | Cloud Run, Artifact Registry, Cloud Billing, IAM Credentials, STS, Firebase Hosting and previously enabled Firebase APIs; IAM API is the remaining requirement |
| Artifact Registry | empty Docker repository `solana-wallet-risk` in `africa-south1` |
| Service accounts | separate enabled runtime, Cloud Run deployer and Hosting deployer; zero user-managed keys |
| Workload Identity | immutable account/repository/environment subjects verified; provider remains restricted to the exact repository and `main`; hosted authentication passed |
| Cloud Run | API enabled; no service or URL exists |
| Firebase | project active; default site `solana-wallet-risk` exists |
| Hosting publish | no preview or live publication executed |

## Workflow acceptance

The tracked workflows were validated locally for immutable action pins, minimal permissions, manual-only deployment triggers, exact-SHA CI gating, protected environment names, concurrency, private Cloud Run flags, digest deployment, model-disable configuration, Firebase CLI pinning and Hosting-only publication. Pinned `actionlint` 1.7.7 and ShellCheck 0.10.0 passed locally.

The initial hosted [CI run](https://github.com/Extreme-Ending/solana-wash-trading-detection/actions/runs/44274052898) exposed the Node-version mismatch. The corrected exact-SHA [CI run](https://github.com/Extreme-Ending/solana-wash-trading-detection/actions/runs/44288003553) passed all jobs. The first authorized [private-pilot run](https://github.com/Extreme-Ending/solana-wash-trading-detection/actions/runs/44283829878) exposed the immutable-subject mismatch; the corrected bindings were then applied and verified. The second authorized [private-pilot run](https://github.com/Extreme-Ending/solana-wash-trading-detection/actions/runs/44287186402) stopped because `cloudbilling.googleapis.com` was disabled; that API was then explicitly enabled. The third authorized [private-pilot run](https://github.com/Extreme-Ending/solana-wash-trading-detection/actions/runs/44288998069) passed billing, API-list and registry checks, then stopped because `iam.googleapis.com` was disabled. No image was built or pushed and no Cloud Run revision, service URL or Hosting release was created. The deployer already has the necessary runtime-account read permission through the existing service-account-level binding, so no broader viewer role is added.

## Production and research boundary

The production Docker image contains no experimental artifact or modelling runtime and production configuration explicitly disables experimental scoring. `/readyz`, `/v1/score` and `/v1/score/batch` remain unavailable as designed. The unsupervised Isolation Forest is not a fraud probability and has not been promoted.

The Firebase site can eventually host the static interface, but the browser cannot invoke the IAM-private pilot with only its Firebase token. Frontend-to-backend integration therefore remains **not working in hosted production** until a separately approved access architecture exists.

## GO/NO-GO

- Corrected CI at SHA `e05dfc474698f3db67dac2e6c4c55db2762e5dd7`: **PASS**.
- Guarded WIF/bootstrap: **PASS**; immutable-subject impersonation succeeded in hosted Actions.
- Private Cloud Run workflow: **NO-GO** until the IAM API requirement is committed, passes CI, is explicitly enabled and the new SHA is re-authorized.
- Hosting preview: **NO-GO** until corrected CI passes and the protected `hosting-preview` environment and Firebase web variables exist.
- Live Hosting: **NO-GO** until preview acceptance and explicit `production` approval.
- Public Cloud Run or production model scoring: **not authorized and not implemented**.
