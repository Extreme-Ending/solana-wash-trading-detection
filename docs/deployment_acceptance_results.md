# Phase 12 deployment acceptance results

Date: 2026-11-18 (Africa/Nairobi)

## Status

**WIF bootstrap: PASS. CI: PASS. Private service deployed; acceptance: NO-GO pending corrected workflow.** The `8b5e81644e01afe76f19903c75917f9957132534` pilot built, pushed and deployed the private service, then failed only when the final check tried to mint an audience-bound token with an unsupported `gcloud` external-account path. The service exists, but the pilot is not accepted until the corrected workflow passes for a separately reviewed SHA.

## Read-only environment evidence

| Check | Observed result |
|---|---|
| Git | current deployed source is reviewed `main` SHA `8b5e81644e01afe76f19903c75917f9957132534`; the acceptance-token correction is an uncommitted working-tree change |
| GitHub | public repository; `private-pilot` environment restricted to `main`; repository branch protection remains unverified |
| Local tools | Python 3.12.3 (CI targets 3.11), Node 22.23.4, npm 10.9.9, Docker 29.10.0, Compose 5.7.1, gcloud 590.0.0, Firebase CLI 15.33.0 |
| Target project | active `solana-wallet-risk`, project number `441056127470` |
| Local gcloud default | `seotranslate-507816` — unrelated and never selected/mutated |
| Billing | enabled on `solana-wallet-risk` |
| Budget | not verifiable: Budget API/permission was unavailable; no budget claim made |
| Enabled relevant APIs | Cloud Run, Artifact Registry, Cloud Billing, IAM, IAM Credentials, STS, Firebase Hosting and previously enabled Firebase APIs |
| Artifact Registry | immutable image digest `sha256:61b05787f0080fbc12848596ebfbbd674cc35e29632a3de13b577a507d0deb3b` exists in `solana-wallet-risk` in `africa-south1` |
| Service accounts | separate enabled runtime, Cloud Run deployer and Hosting deployer; zero user-managed keys |
| Workload Identity | immutable account/repository/environment subjects verified; provider remains restricted to the exact repository and `main`; hosted authentication passed |
| Cloud Run | `solana-wallet-risk-api` revision `solana-wallet-risk-api-8b5e81644e01` is Ready with 100% traffic at its private `run.app` URL; exact registry digest, 1 CPU, 512 MiB, approved runtime identity, production environment and experimental scoring `false` were verified read-only |
| Firebase | project active; default site `solana-wallet-risk` exists |
| Hosting publish | no preview or live publication executed |

## Workflow acceptance

The tracked workflows were validated locally for immutable action pins, minimal permissions, manual-only deployment triggers, exact-SHA CI gating, protected environment names, concurrency, private Cloud Run flags, digest deployment, model-disable configuration, Firebase CLI pinning and Hosting-only publication. Pinned `actionlint` 1.7.7 and ShellCheck 0.10.0 passed locally.

The initial hosted [CI run](https://github.com/Extreme-Ending/solana-wash-trading-detection/actions/runs/44274052898) exposed the Node-version mismatch. The corrected exact-SHA [CI run](https://github.com/Extreme-Ending/solana-wash-trading-detection/actions/runs/44288003553) passed all jobs. The first authorized [private-pilot run](https://github.com/Extreme-Ending/solana-wash-trading-detection/actions/runs/44283829878) exposed the immutable-subject mismatch; the corrected bindings were then applied and verified. The second authorized [private-pilot run](https://github.com/Extreme-Ending/solana-wash-trading-detection/actions/runs/44287186402) stopped because `cloudbilling.googleapis.com` was disabled; that API was then explicitly enabled. The third authorized [private-pilot run](https://github.com/Extreme-Ending/solana-wash-trading-detection/actions/runs/44288998069) stopped because `iam.googleapis.com` was disabled.

The subsequent [private-pilot run for `8b5e816`](https://github.com/Extreme-Ending/solana-wash-trading-detection/actions/runs/44297199630) passed the exact-SHA gate, preflight, production-image smoke test, registry push and digest deployment. It failed in the final acceptance step because `gcloud auth print-identity-token --audiences=...` does not support the WIF external-account credential type. Read-only follow-up verified the Ready revision, exact digest, private service and project IAM (no `allUsers` or `allAuthenticatedUsers` bindings), and experimental scoring disabled. An anonymous `/healthz` request returned `404`; because the authorized request was never reached in that run, end-to-end acceptance remains incomplete. The correction uses the pinned authentication action's audience-bound, short-lived ID-token output and requires no new IAM grant or long-lived key.

## Production and research boundary

The production Docker image contains no experimental artifact or modelling runtime and production configuration explicitly disables experimental scoring. `/readyz`, `/v1/score` and `/v1/score/batch` remain unavailable as designed. The unsupervised Isolation Forest is not a fraud probability and has not been promoted.

The Firebase site can eventually host the static interface, but the browser cannot invoke the IAM-private pilot with only its Firebase token. Frontend-to-backend integration therefore remains **not working in hosted production** until a separately approved access architecture exists.

## GO/NO-GO

- CI at deployed SHA `8b5e81644e01afe76f19903c75917f9957132534`: **PASS**.
- Guarded WIF/bootstrap: **PASS**; immutable-subject impersonation succeeded in hosted Actions.
- Private Cloud Run resource: **DEPLOYED and read-only controls verified**, but the pilot acceptance is **NO-GO** until the corrected token flow is committed by the student, passes CI and is explicitly re-authorized for the new SHA.
- Hosting preview: **NO-GO** until corrected CI passes and the protected `hosting-preview` environment and Firebase web variables exist.
- Live Hosting: **NO-GO** until preview acceptance and explicit `production` approval.
- Public Cloud Run or production model scoring: **not authorized and not implemented**.
