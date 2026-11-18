# Phase 12 deployment acceptance results

Date: 2026-11-18 (Africa/Nairobi)

## Status

**Implementation: PASS locally. Infrastructure/deployment: NO-GO.** This document records observed discovery and local validation, not a live deployment.

## Read-only environment evidence

| Check | Observed result |
|---|---|
| Git | clean `main` at entry, SHA `16c6919c48eefa5f192aec8a5960486dc6071ac1` |
| GitHub | public repository; default `main`; no environments; no branch protection |
| Local tools | Python 3.12.3 (CI targets 3.11), Node 22.23.4, npm 10.9.9, Docker 29.10.0, Compose 5.7.1, gcloud 590.0.0, Firebase CLI 15.33.0 |
| Target project | active `solana-wallet-risk`, project number `441056127470` |
| Local gcloud default | `seotranslate-507816` — unrelated and never selected/mutated |
| Billing | enabled on `solana-wallet-risk` |
| Budget | not verifiable: Budget API/permission was unavailable; no budget claim made |
| Enabled relevant APIs | Firebase, Firebase Hosting, Identity Toolkit, Resource Manager, Service Usage |
| Missing required APIs | Cloud Run, Artifact Registry, IAM Credentials and STS were not observed enabled |
| Artifact Registry | repository not queryable because its API is disabled; no repository evidence |
| Service accounts | planned runtime/deploy accounts absent; Firebase-managed admin SDK identity exists |
| Workload Identity | no pools/providers observed |
| Cloud Run | API disabled; no service or URL verified |
| Firebase | project active; default site `solana-wallet-risk` exists |
| Hosting publish | no preview or live publication executed |

## Workflow acceptance

The tracked workflows were validated locally for immutable action pins, minimal permissions, manual-only deployment triggers, exact-SHA CI gating, protected environment names, concurrency, private Cloud Run flags, digest deployment, model-disable configuration, Firebase CLI pinning and Hosting-only publication. Pinned `actionlint` 1.7.7 and ShellCheck 0.10.0 passed locally. Real GitHub-hosted execution still requires the student to commit and push the workflows.

No GitHub Actions run URL exists yet. No Artifact Registry digest, Cloud Run revision/URL, Hosting preview URL or live release was created in Phase 12.

## Production and research boundary

The production Docker image contains no experimental artifact or modelling runtime and production configuration explicitly disables experimental scoring. `/readyz`, `/v1/score` and `/v1/score/batch` remain unavailable as designed. The unsupervised Isolation Forest is not a fraud probability and has not been promoted.

The Firebase site can eventually host the static interface, but the browser cannot invoke the IAM-private pilot with only its Firebase token. Frontend-to-backend integration therefore remains **not working in hosted production** until a separately approved access architecture exists.

## GO/NO-GO

- CI push after student commit: **GO**.
- Guarded WIF/bootstrap after credential rotation, budget review and command review: **student decision required**.
- Private Cloud Run workflow: **NO-GO** until APIs, repository, identities, WIF, budget attestation and protected GitHub environment exist.
- Hosting preview: **NO-GO** until WIF/Hosting deploy identity and `hosting-preview` environment exist.
- Live Hosting: **NO-GO** until preview acceptance and explicit `production` approval.
- Public Cloud Run or production model scoring: **not authorized and not implemented**.
