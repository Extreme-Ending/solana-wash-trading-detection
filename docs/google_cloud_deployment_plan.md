# Google Cloud deployment plan

## Phase 7A boundary

This document is a preparation record, not a deployment record. No Google Cloud project, billing account, API, repository, service, IAM binding, Firebase site, or public URL was created or changed in Phase 7A. The proposed academic demonstration uses one future Google Cloud project and preserves the current scoring gate: the deployed API would expose descriptive feature preview only, while `/readyz` and `/v1/score` continue to return `MODEL_NOT_APPROVED`.

## Prepared architecture

```text
Firebase Hosting                         Google Cloud Run (private by default)
React/Vite static SPA  -- HTTPS JSON --> FastAPI container
frontend/dist                            /healthz, /readyz,
                                           /v1/features/preview, /v1/score
                                                ^
                                                |
                                 Artifact Registry image tagged by Git SHA
```

- **Frontend:** a clean `npm ci` and Vite production build produces `frontend/dist`; Firebase Hosting serves only that static directory.
- **Backend:** the existing tested, non-root API image is reused. It trains nothing at startup and contains neither the raw CSV nor experimental model artifacts.
- **Registry:** the proposed image URI is `africa-south1-docker.pkg.dev/PROJECT_ID/solana-wallet-risk/solana-wallet-risk-api:GIT_SHA`.
- **Configuration:** identifiers and exact origins are environment values. No credential is a Vite variable or repository file.
- **Region:** `africa-south1` (Johannesburg) supports both Cloud Run and Artifact Registry and is the nearest listed Google Cloud region to the intended Nairobi use. It is currently in Cloud Run pricing Tier 1. Availability is documented by the [Cloud Run deployment regions](https://cloud.google.com/run/docs/deploying) and [Artifact Registry locations](https://cloud.google.com/artifact-registry/docs/repositories/repo-locations); pricing must be rechecked immediately before deployment.

## Routing decision

The production frontend is prepared to use the exact Cloud Run HTTPS origin in `VITE_API_BASE_URL`. The value must be an origin only, for example `https://SERVICE-HASH.africa-south1.run.app`, with no `/api` suffix. `ApiClient` appends the existing FastAPI paths exactly, so the resulting requests remain `/healthz`, `/readyz`, `/v1/features/preview`, and `/v1/score`.

The local Vite `/api` proxy remains unchanged. A Firebase Hosting rewrite was not adopted because Firebase forwards the original path: the browser's `/api/healthz` request would remain `/api/healthz`, while the API implements `/healthz`. A rewrite would therefore require an API-prefix change or another path adapter and would risk breaking the already-tested contract. See the [Firebase Hosting rewrite configuration](https://firebase.google.com/docs/hosting/full-config#rewrite).

## Public-access blocker

Cloud Run services are private by default. The prepared command explicitly uses `--no-allow-unauthenticated`. An authenticated student can invoke the service with a short-lived Google identity token and run the smoke test, but a static Firebase SPA cannot safely hold such a token or service credential. CORS only tells a browser which origins may read a response; it is not authentication or rate limiting.

Consequently, the hosted browser-to-API path is **blocked** until the student approves and documents an access design. Options for a later phase include end-user authentication with token verification and abuse controls, or a narrowly approved public descriptive API with explicit risk acceptance, rate limiting and monitoring. Phase 7A does not enable anonymous invocation. See [Cloud Run authentication](https://cloud.google.com/run/docs/authenticating/overview) and [public access controls](https://cloud.google.com/run/docs/authenticating/public).

## Student-operated sequence

1. Create/select one project and decide whether billing and the required APIs may be enabled. This is outside Phase 7A.
2. Create a user-managed runtime service account with no project roles; the current API calls no Google APIs.
3. Create the Docker-format Artifact Registry repository in `africa-south1` and apply the prepared cleanup policy.
4. Grant only the roles listed in `cloud_run_configuration.md` to the student/deployer identities.
5. Copy `deployment/deployment.env.example` to the Git-ignored `deployment/deployment.env.local`, replace every placeholder, and export it in the shell.
6. Run `./scripts/deployment.sh prerequisites` and `./scripts/deployment.sh plan`.
7. Use the individually confirmed build, tag, push, Cloud Run deploy, frontend build and Firebase deploy actions only after reviewing each displayed target and effect.
8. Keep Cloud Run private for an authenticated smoke test. Do not claim browser integration until the access blocker is resolved.
9. Review cost/logging dashboards and use rollback or cleanup commands if needed.

The helper never creates a project, billing account, repository, service account or IAM binding. Its cloud-changing actions require both `--execute` and an interactive exact confirmation. Full commands and prerequisites are in the other Phase 7A documents.
