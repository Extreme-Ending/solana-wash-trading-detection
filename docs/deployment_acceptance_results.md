# Phase 12 deployment acceptance results

Date: 2026-11-18 (Africa/Nairobi)

## Status

**Bootstrap: correction required. CI: PASS. Deployment: NO-GO.** The first private-pilot attempt stopped before image build or deployment because its WIF service-account binding used GitHub's legacy name-only subject rather than the repository's enabled immutable subject.

## Read-only environment evidence

| Check | Observed result |
|---|---|
| Git | private-pilot attempt targeted reviewed `main` SHA `942ac5786ec72571e485d45af6b7f256d9682f66`; immutable-subject correction remains uncommitted |
| GitHub | public repository; `private-pilot` environment restricted to `main`; repository branch protection remains unverified |
| Local tools | Python 3.12.3 (CI targets 3.11), Node 22.23.4, npm 10.9.9, Docker 29.10.0, Compose 5.7.1, gcloud 590.0.0, Firebase CLI 15.33.0 |
| Target project | active `solana-wallet-risk`, project number `441056127470` |
| Local gcloud default | `seotranslate-507816` — unrelated and never selected/mutated |
| Billing | enabled on `solana-wallet-risk` |
| Budget | not verifiable: Budget API/permission was unavailable; no budget claim made |
| Enabled relevant APIs | Cloud Run, Artifact Registry, IAM Credentials, STS, Firebase Hosting and previously enabled Firebase APIs |
| Artifact Registry | empty Docker repository `solana-wallet-risk` in `africa-south1` |
| Service accounts | separate enabled runtime, Cloud Run deployer and Hosting deployer; zero user-managed keys |
| Workload Identity | provider condition is restricted to the exact repository and `main`; name-only service-account subjects do not match the repository's enabled immutable OIDC subjects |
| Cloud Run | API enabled; no service or URL exists |
| Firebase | project active; default site `solana-wallet-risk` exists |
| Hosting publish | no preview or live publication executed |

## Workflow acceptance

The tracked workflows were validated locally for immutable action pins, minimal permissions, manual-only deployment triggers, exact-SHA CI gating, protected environment names, concurrency, private Cloud Run flags, digest deployment, model-disable configuration, Firebase CLI pinning and Hosting-only publication. Pinned `actionlint` 1.7.7 and ShellCheck 0.10.0 passed locally.

The initial hosted [CI run](https://github.com/Extreme-Ending/solana-wash-trading-detection/actions/runs/44274052898) exposed the Node-version mismatch. The corrected exact-SHA [CI run](https://github.com/Extreme-Ending/solana-wash-trading-detection/actions/runs/44282545410) passed Python, frontend, container and workflow-security jobs. The authorized [private-pilot run](https://github.com/Extreme-Ending/solana-wash-trading-detection/actions/runs/44283829878) then failed while obtaining service-account credentials: GitHub immutable OIDC subjects were enabled, but the bootstrap had granted `roles/iam.workloadIdentityUser` to the older name-only subject. No image was built or pushed and no Cloud Run revision, service URL or Hosting release was created. The correction retains exact environment trust using immutable account and repository IDs; it does not broaden access.

## Production and research boundary

The production Docker image contains no experimental artifact or modelling runtime and production configuration explicitly disables experimental scoring. `/readyz`, `/v1/score` and `/v1/score/batch` remain unavailable as designed. The unsupervised Isolation Forest is not a fraud probability and has not been promoted.

The Firebase site can eventually host the static interface, but the browser cannot invoke the IAM-private pilot with only its Firebase token. Frontend-to-backend integration therefore remains **not working in hosted production** until a separately approved access architecture exists.

## GO/NO-GO

- Corrected CI at SHA `942ac5786ec72571e485d45af6b7f256d9682f66`: **PASS**.
- Guarded WIF/bootstrap: **NO-GO** until immutable-subject bindings replace the obsolete name-only bindings and are independently verified.
- Private Cloud Run workflow: **NO-GO** until the WIF correction is committed, passes CI, is explicitly applied and the new SHA is re-authorized.
- Hosting preview: **NO-GO** until corrected CI passes and the protected `hosting-preview` environment and Firebase web variables exist.
- Live Hosting: **NO-GO** until preview acceptance and explicit `production` approval.
- Public Cloud Run or production model scoring: **not authorized and not implemented**.
