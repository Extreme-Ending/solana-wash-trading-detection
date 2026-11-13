# Cloud cost and security controls

## Cost posture

The intended workload is a low-traffic academic demonstration, not a production fraud-monitoring service. No Phase 7A action created a billable resource, and no future no-cost result is guaranteed.

| Area | Prepared control | Residual risk / student check |
|---|---|---|
| Cloud Run compute | request-based billing, min 0, max 2, 1 CPU, 512 MiB, concurrency 20, 30-second timeout | max instances bounds scale but is not a spending cap; recheck [Cloud Run pricing](https://cloud.google.com/run/pricing) |
| Artifact Registry | one repository, SHA tags, delete images older than 30 days while keeping three recent versions | storage and network transfer can be charged; review [Artifact Registry pricing](https://cloud.google.com/artifact-registry/pricing) and cleanup dry-run results |
| Firebase Hosting | static hashed assets with long caching and non-cached HTML | transfer/storage beyond allowances can be charged; review [Hosting usage](https://firebase.google.com/docs/hosting/usage-quotas-pricing) |
| Cloud Logging | no application telemetry or verbose payload logging added; bounded API traffic | default `_Default` retention is currently 30 days, but volume can still cost; verify exclusions/retention in [Logging quotas and limits](https://cloud.google.com/logging/quotas) |
| Budget monitoring | configure low threshold alerts before deployment | [budget alerts](https://cloud.google.com/billing/docs/how-to/budgets) notify; they do **not** automatically stop usage or charges and can be delayed |

Before deployment, the student should inspect current prices for `africa-south1`, create a small monthly budget with several percentage/forecast thresholds, nominate a monitored email, and verify that billing export or paid monitoring is not being enabled unintentionally. A budget alert is evidence of monitoring, not a hard cap.

## Security controls

- Cloud Run remains private with `--no-allow-unauthenticated`; only the service-specific Invoker role permits calls.
- The runtime uses a dedicated service account with no project role because this API consumes no Google API.
- The browser CORS allowlist is exactly the two project Hosting origins. Wildcards, credentialed origins and path-bearing origins fail validation.
- The frontend configuration accepts only an HTTPS origin in production. It forbids embedded credentials and path suffixes, including `/api`.
- Vite variables contain no secrets. Static browser code cannot protect a credential.
- API request-size and event-count limits remain 262,144 bytes and 100 events. Cloud Run also has max instances, concurrency and timeout bounds.
- Docker and Firebase bundle checks exclude research CSVs, models, reports, notebooks, private steering files and common secret signatures.
- No database, authentication provider, third-party telemetry, automatic deployment workflow, model artifact or training job is introduced.
- Health remains process health. Readiness and scoring remain unavailable; deployment does not imply scientific model approval.

The unresolved public-browser issue is security-critical: Firebase Hosting cannot make an IAM-private service callable from arbitrary browsers without an authentication design. CORS is not access control. Do not weaken this by putting a service token in JavaScript or enabling anonymous invocation merely for convenience.

## Logging and privacy

Do not log submitted wallet/event payloads, authorization headers, identity tokens or entire validation bodies. Use aggregate request status, latency and instance metrics only. Inspect Cloud Run request logs after a synthetic smoke test for accidental payload/header exposure. If application logs are later added, define redaction and retention before deployment.

## Cleanup

First list exact targets with read-only commands:

```bash
gcloud run services describe solana-wallet-risk-api \
  --project YOUR_GCP_PROJECT_ID --region africa-south1
gcloud artifacts repositories describe solana-wallet-risk \
  --project YOUR_GCP_PROJECT_ID --location africa-south1
firebase hosting:sites:list --project YOUR_GCP_PROJECT_ID
```

After reviewing those targets and confirming that destruction is intended:

```bash
./scripts/deployment.sh cleanup --execute
```

The guarded action deletes the named Cloud Run service and Artifact Registry repository and disables Hosting. These operations may not be recoverable. It does not delete the project, billing account, source files or Git history. IAM bindings, service accounts, enabled APIs, budgets and retained logs must be reviewed separately because the helper intentionally does not guess which shared project resources are safe to remove.
## Phase 7C.0 hardening and cost update

Production now requires revoked/disabled Firebase-token checking, rejects protected requests at the authentication boundary before parsing, disables `/docs`, `/redoc` and `/openapi.json`, and limits each approved UID to 30 protected requests per 60 seconds in each process. The limiter is not shared across instances, resets on restart and cannot protect token verification from invalid-token traffic. Safe errors do not echo token, body or submitted values; logs must remain free of authorization headers, Firebase claims, wallet event bodies and feature payloads.

The future Firebase-hosted browser path recommends platform-public Cloud Run with application-layer Firebase/UID protection. It is not enabled. Public reachability can generate Cloud Run, Firebase verification and logging usage even when FastAPI returns 401. App Check can reduce abuse but is not identity, is not a cost cap and is deferred pending provider/domain setup, quota/cost acceptance and monitored rollout.

The proposed academic budget is USD 10/month with 50%, 80% and 100% alerts. Those alerts do not stop spending. A USD 15 enforced ceiling may be considered only if the actual project is eligible for Google Cloud's spend-cap budget and it demonstrably covers every selected service; otherwise it must not be claimed as a cap. No budget or billing setting was changed. Preserve min 0/max 2, request-based CPU, 1 CPU, 512 MiB, concurrency 20 and timeout 30 seconds; monitor Firebase Hosting transfer, Artifact Registry retention/scanning, Cloud Run requests and Logging ingestion. Full sources and actions are in [`phase_7c_deployment_security_review.md`](phase_7c_deployment_security_review.md).
