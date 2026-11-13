# Google Cloud deployment plan

## Phase 7B boundary

This document is a preparation record, not a deployment record. No Google Cloud/Firebase resource, billing setting, API, repository, service, IAM binding, Authentication provider, site, or public URL was created or changed in Phase 7B. The code now supports Google sign-in and application-layer Firebase token verification. `/v1/features/preview` and `/v1/score` require an approved Firebase UID, while `/readyz` and authorized `/v1/score` continue to return `MODEL_NOT_APPROVED`.

## Prepared architecture

```text
Firebase Hosting                            Google Cloud Run (private platform IAM)
React/Vite + Firebase Auth -- ID token --> FastAPI + Firebase Admin + UID allowlist
frontend/dist                               public: /healthz, /readyz
                                            protected: /v1/features/preview, /v1/score
                                                ^
                                                |
                                 Artifact Registry image tagged by Git SHA
```

- **Frontend:** a clean `npm ci` and Vite production build produces `frontend/dist`; Firebase Hosting serves only that static directory.
- **Backend:** the existing tested, non-root API image is reused. It trains nothing at startup and contains neither the raw CSV nor experimental model artifacts.
- **Registry:** the proposed image URI is `africa-south1-docker.pkg.dev/PROJECT_ID/solana-wallet-risk/solana-wallet-risk-api:GIT_SHA`.
- **Configuration:** exact origins, Firebase Web identifiers, backend project and UID allowlist are environment values. The Web API key is public configuration, not authorization. No ID token or Admin credential is a Vite variable or repository file.
- **Region:** `africa-south1` (Johannesburg) supports both Cloud Run and Artifact Registry and is the nearest listed Google Cloud region to the intended Nairobi use. It is currently in Cloud Run pricing Tier 1. Availability is documented by the [Cloud Run deployment regions](https://cloud.google.com/run/docs/deploying) and [Artifact Registry locations](https://cloud.google.com/artifact-registry/docs/repositories/repo-locations); pricing must be rechecked immediately before deployment.

## Routing decision

The production frontend is prepared to use the exact Cloud Run HTTPS origin in `VITE_API_BASE_URL`. The value must be an origin only, for example `https://SERVICE-HASH.africa-south1.run.app`, with no `/api` suffix. `ApiClient` appends the existing FastAPI paths exactly, so the resulting requests remain `/healthz`, `/readyz`, `/v1/features/preview`, and `/v1/score`.

The local Vite `/api` proxy remains unchanged. A Firebase Hosting rewrite was not adopted because Firebase forwards the original path: the browser's `/api/healthz` request would remain `/api/healthz`, while the API implements `/healthz`. A rewrite would therefore require an API-prefix change or another path adapter and would risk breaking the already-tested contract. See the [Firebase Hosting rewrite configuration](https://firebase.google.com/docs/hosting/full-config#rewrite).

## Public-access blocker

Cloud Run services are private by default. The prepared command explicitly uses `--no-allow-unauthenticated`. Firebase Authentication now supplies a signed end-user token that FastAPI validates, but that token does not grant Cloud Run IAM invocation. An authorized operator can smoke-test both layers by sending a Cloud Run identity token in `X-Serverless-Authorization` and a Firebase ID token in `Authorization`; a normal static browser has only the latter. CORS only tells a browser which origins may read a response; it is not platform IAM or rate limiting.

Consequently, the hosted browser-to-API path remains **blocked** until the student approves and documents an access design. Options for Phase 7C include an identity-aware intermediary that can satisfy private platform IAM, or separately risk-accepted public platform invocation while retaining Firebase verification, the UID allowlist and abuse controls. Phase 7B does not enable anonymous invocation. See [Cloud Run end-user authentication](https://cloud.google.com/run/docs/authenticating/end-users) and [Cloud Run authentication overview](https://cloud.google.com/run/docs/authenticating/overview).

## Student-operated sequence

1. Create/select one project and decide whether billing and the required APIs may be enabled. This is outside Phase 7A.
2. Create a user-managed runtime service account for ADC without a downloaded key; validate the minimum permissions needed for Firebase token verification.
3. Create the Docker-format Artifact Registry repository in `africa-south1` and apply the prepared cleanup policy.
4. Grant only the roles listed in `cloud_run_configuration.md` to the student/deployer identities.
5. Copy `deployment/deployment.env.example` to the Git-ignored `deployment/deployment.env.local`, replace every placeholder, and export it in the shell.
6. Run `./scripts/deployment.sh prerequisites` and `./scripts/deployment.sh plan`.
7. Use the individually confirmed build, tag, push, Cloud Run deploy, frontend build and Firebase deploy actions only after reviewing each displayed target and effect.
8. Keep Cloud Run private for a two-token authenticated operator smoke test. Do not claim browser integration until the access blocker is resolved.
9. Review cost/logging dashboards and use rollback or cleanup commands if needed.

The helper never creates a project, billing account, repository, service account or IAM binding. Its cloud-changing actions require both `--execute` and an interactive exact confirmation. Full commands and prerequisites are in the deployment documents. Phase 7B ran none of them.
