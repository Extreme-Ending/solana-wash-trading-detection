# Deployment guide

## Current deployment

| Component | Current target |
| --- | --- |
| Frontend | Firebase Hosting at `https://solana-wallet-risk.web.app/` |
| Backend | Google Cloud Run service `solana-wallet-risk-api` |
| Region | `africa-south1` |
| Container registry | Google Artifact Registry |
| Authentication | Firebase Google sign-in plus FastAPI UID allowlist |

The backend uses the scoring image built from `Dockerfile.scoring`. The image includes the checksum-pinned experimental Isolation Forest bundle. The standard `Dockerfile` intentionally remains model-free.

## Release controls

GitHub Actions runs Python, frontend, workflow, and security checks. The Firebase workflow supports controlled hosting releases. Cloud authentication uses Workload Identity Federation with repository and immutable-subject restrictions. Images are tagged with a full Git commit SHA. Releases are manually authorized and do not use force pushes, stored service-account keys, or automatic model promotion.

The tracked Cloud Run workflow is intentionally a model-disabled, IAM-private pilot path. It is not the release path that produced the current browser-reachable scoring service. The current scoring release used the guarded local full-stack script. This distinction must remain visible until the workflow is redesigned and revalidated.

The repository also contains guarded local deployment scripts. They validate exact Git SHA, required tools, project and region configuration, model checksum, frontend API origin, and explicit confirmation before a mutation. Local and CI deployment paths must not be mixed without checking the current cloud state.

## Runtime configuration

The backend requires environment values for:

- environment mode and allowed CORS origins
- Firebase project ID and approved UID allowlist
- revoked-token checks
- event, batch, request-size, and rate limits
- experimental scoring enablement
- model artifact path, manifest path, and expected SHA-256

The frontend uses public Firebase Web configuration and the exact HTTPS backend origin. `VITE_*` values are browser-visible and must never contain credentials. The runtime service account uses Application Default Credentials. Do not download a private service-account key into the repository.

## Network and security model

The browser must be able to reach Cloud Run. Platform reachability does not authorize analysis. Protected routes still require a valid Firebase bearer token, verified Google email, correct Firebase project, and an approved UID. Public routes expose only health and readiness metadata.

The live alias `GET /v1/health` is the recommended browser health check. A prior live verification observed `GET /healthz` returning a Google-edge 404 even though the route works in source and local containers. This routing discrepancy remains an operational issue to investigate. It does not justify weakening authentication.

## Acceptance checks

After an authorized deployment, verify:

1. Firebase Hosting returns the intended release.
2. `/v1/health` returns HTTP 200.
3. `/readyz` reports experimental anomaly scoring as ready and `is_probability=false`.
4. Protected routes return HTTP 401 without a token.
5. A valid unapproved user receives HTTP 403.
6. An approved user can submit bounded feature, single-score, and batch-score requests.
7. The displayed artifact checksum and Git SHA match the authorized release.
8. Logs contain no tokens, raw request bodies, private identifiers, or secrets.

## Rollback

Cloud Run rollback selects a previously verified revision. Firebase Hosting rollback selects a previous release. Confirm the image digest, configuration, model checksum, and frontend API origin before restoring traffic. Rollback does not authorize replacing the research artifact or changing the scoring interpretation.

## Cost controls

The service uses request-based Cloud Run billing, scale-to-zero behavior, bounded maximum instances, and budget alerts. Budget alerts are notifications, not guaranteed spending caps. Artifact storage, logs, Firebase, network egress, and other Google Cloud charges must be reviewed separately.
