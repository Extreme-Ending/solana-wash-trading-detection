# Phase 7C.0 production security and deployment-readiness review

## Status and decision

**Readiness decision: NO-GO for live deployment and NO-GO for public Cloud Run invocation.**

The repository is hardened and locally testable, but no Google Cloud or Firebase project configuration has been verified, no runtime identity or budget has been created, no hosted Firebase-to-Cloud-Run acceptance test has run, and the student has not accepted the cost and abuse risks of platform-public invocation. This document is a readiness review, not a deployment record. Phase 7C.0 created or changed no cloud, Firebase, billing or IAM resource.

The recommended future browser architecture is:

```text
Firebase Hosting (React SPA)
  -> Google sign-in / short-lived Firebase ID token
  -> HTTPS Cloud Run URL (platform invocation publicly reachable)
  -> FastAPI boundary authentication
       -> Firebase signature/project/expiry/revocation checks
       -> verified Google email
       -> explicit server-side UID allowlist
       -> per-instance authorized-user request limit
  -> descriptive feature preview only
```

Cloud Run is private by default and checks IAM before a request reaches the container. A static browser cannot safely hold a Cloud Run invoker credential, so a direct Firebase Hosting SPA needs the Cloud Run platform invocation check relaxed in a later, separately approved action. Public platform reachability does **not** make protected routes anonymous: FastAPI must still return 401/403 unless the Firebase and UID policies pass. It does expose the container, public health routes and authentication boundary to untrusted traffic, which can consume instances, token-verification work and logging quota. Google currently recommends disabling the Invoker IAM check when making a service public; an `allUsers` binding is an alternative. Neither mechanism appears in the deployment script and neither was executed. See the official [Cloud Run public-access guidance](https://docs.cloud.google.com/run/docs/authenticating/public) and [authentication overview](https://docs.cloud.google.com/run/docs/authenticating/overview).

## Controls implemented and locally verified

| Boundary | Phase 7C.0 control |
|---|---|
| Authentication | Protected paths are intercepted before request-body/schema processing. Missing, duplicate, malformed, expired, wrong-project and otherwise invalid Bearer credentials fail with 401. Verification infrastructure failure fails closed with 503. |
| Revocation | Production requires `SOLANA_RISK_CHECK_REVOKED_TOKENS=true`; Firebase Admin checks revoked and disabled-user state as well as signature and standard token claims. This can add a remote lookup, latency and dependency on Firebase availability. |
| Authorization | A verified email, `google.com` provider and exact Firebase UID membership are required. The allowlist stays server-side. |
| Public endpoints | `/healthz` and `/readyz` remain application-public. Readiness still returns 503 `MODEL_NOT_APPROVED`. They disclose only service/version and model-unavailable state. |
| Protected endpoints | `/v1/features/preview` remains descriptive. `/v1/score` returns 503 `MODEL_NOT_APPROVED` after successful authorization. No experimental artifact is loaded. |
| API discovery | `/docs`, `/redoc` and `/openapi.json` are disabled when `SOLANA_RISK_ENVIRONMENT=production`; they remain available in development. |
| Browser boundary | CORS accepts only configured exact origins, methods and headers. Wildcards and origins containing paths, credentials, queries or fragments are rejected. CORS is not treated as authentication. |
| Input bounds | Authentication precedes protected body parsing; authorized requests remain limited to 256 KiB and 100 events by default. UTC and feature-parity validation are unchanged. |
| Rate control | Each process admits 30 protected requests per approved UID per 60 seconds, then returns 429 with `Retry-After`. This is intentionally labelled **per instance**, resets on restart/cold start and is neither global nor an unauthenticated-traffic control. With two instances an effective user allowance can exceed 30/minute. |
| Logging | Application errors never echo tokens or submitted values. No request body or authorization header is logged. Standard access/request logs may still contain method, route, status, latency and network metadata; do not add headers, bodies, wallet data or Firebase claims to logs. |
| Resource bounds | Planned Cloud Run settings remain request-based CPU throttling, min 0, max 2, 1 CPU, 512 MiB, concurrency 20 and timeout 30 seconds in `africa-south1`. The region is currently listed by Google Cloud and remains the reviewed default. |
| Release integrity | Planned images use the full Git commit SHA. The container is non-root, read-only in Compose, includes no research dataset/model, and never trains or loads a model at startup. |

## App Check evaluation — evaluated, not enabled

Firebase App Check can add app-attestation evidence to custom-backend requests through `X-Firebase-AppCheck`. For web, the supported built-in provider is reCAPTCHA Enterprise. It reduces casual scripted abuse but does not establish user identity, replace the Firebase ID token, guarantee abuse elimination, or create a spend cap. The official guidance states that App Check for custom backends requires both client token attachment and server verification; the web default one-hour TTL refreshes at roughly half the TTL. The current no-cost allowance is 10,000 reCAPTCHA Enterprise assessments per month, with charges beyond that, and shorter TTLs increase assessment frequency. See [App Check custom-backend integration](https://firebase.google.com/docs/app-check/web/custom-resource), [reCAPTCHA Enterprise provider guidance](https://firebase.google.com/docs/app-check/web/recaptcha-enterprise-provider), and [Firebase App Check limits](https://firebase.google.com/docs/app-check).

**Decision:** do not enable App Check in Phase 7C.0. Enabling it requires project/API/key configuration, production-domain registration, cost acceptance, local/CI debug-token handling, frontend/backend code, and observe-before-enforce testing. Replay protection is beta and the official custom-backend guidance currently limits Admin SDK token consumption to Node.js, while this backend is Python. Before public invocation, the student must choose one of these explicitly:

1. implement and monitor App Check for the production web app before enforcement; or
2. accept in writing that the small academic demo relies on Firebase user authentication, max instances, per-instance authorized-user limiting and budget controls, and remains exposed to unauthenticated request cost/availability risk.

## Rate limiting and excessive-request risk

The local limiter protects a single approved UID from accidental bursts within one running container. It cannot coordinate Cloud Run instances, survive restarts, stop invalid-token traffic before Firebase verification, or guarantee an account/project-wide quota. It is therefore not described as production-grade distributed rate limiting.

A stronger edge/global control would require an additional managed architecture (for example an external Application Load Balancer and Cloud Armor) or a shared durable counter. Either changes cost, IAM, latency and operational scope and must be priced and approved before implementation. Phase 7C.0 adds no paid dependency or infrastructure. Maximum instances of two bounds concurrency growth but is not a monetary guarantee.

## Deployment-script safety assessment

- `plan` remains the default and executes no cloud change.
- Every existing mutating action requires `--execute`, an interactive terminal and exact `project/region/action` confirmation.
- Live configuration rejects placeholders, a region other than `africa-south1`, altered resource bounds, mismatched Firebase project/origins, missing UID allowlist, disabled revocation checks or altered rate defaults.
- The Cloud Run command remains `--no-allow-unauthenticated`; the script contains neither `--no-invoker-iam-check` nor an `allUsers` binding.
- There is no public-access mutation action. Public invocation requires a separate future code review, explicit risk acceptance and explicit student execution.
- The script never creates a project, billing account, repository, service account, Firebase site or IAM binding. Resource creation must be performed as separately approved student actions.
- Image references are full-commit-SHA tags. Rollback routes traffic to an explicitly named prior revision. Cleanup is a separate destructive action with exact confirmation and is not automatic.
- The private smoke mode uses separate Cloud Run and Firebase tokens. `smoke-public-candidate` is prepared for a later already-public endpoint and accepts only a Firebase token; it does not alter IAM. Neither live mode was executed in this phase.

## Cost plan and limits

The proposed small academic-demo budget is **USD 10 per month**, with informational alerts at 50%, 80% and 100%, sent to the student. This amount is a review proposal, not a configured budget and not permission to incur charges. Standard Cloud Billing budget alerts do not stop usage. Google now documents spend-cap budgets for eligible projects/services; eligibility, included services and enforcement behavior must be verified in the actual account before relying on one. If an enforced spend cap is available and covers Cloud Run, Artifact Registry, Logging, Firebase Hosting and reCAPTCHA Enterprise, propose a separate **USD 15 hard-cap ceiling** after supervisor/student review. Otherwise, retain alerts and treat max instances/quotas as partial controls, not a hard cap. See [Cloud Billing budgets](https://docs.cloud.google.com/billing/docs/how-to/budgets) and [spend-cap budgets](https://docs.cloud.google.com/billing/docs/how-to/budgets-spend-caps).

Cost review before deployment:

- Cloud Run: min 0, max 2, request-based CPU throttling, conservative memory/concurrency/timeout; public abuse can still generate cost.
- Firebase Hosting: monitor project-level stored data and CDN transfer; the current no-cost transfer allowance is documented as 10 GB/month. See [Hosting usage and pricing](https://firebase.google.com/docs/hosting/usage-quotas-pricing).
- Artifact Registry: keep the runtime and registry co-located, retain three recent versions and delete versions older than 30 days only after previewing the cleanup policy. Storage above the current account-level free allowance and vulnerability scanning can cost money. See [Artifact Registry pricing](https://cloud.google.com/artifact-registry/pricing) and [cleanup policies](https://docs.cloud.google.com/artifact-registry/docs/repositories/cleanup-policy).
- Logging: monitor ingestion and retention; keep safe operational logs, avoid payload/claim logging, and review exclusions only after confirming they do not remove security/audit evidence.
- App Check: do not enable until assessment quota, domain/key setup, billing impact and enforcement rollout are accepted.

## Exact student actions required before GO

1. Select the exact Google Cloud/Firebase project and verify its project ID, billing status, account ownership and `africa-south1` availability.
2. Create/verify the Firebase web app, Google sign-in provider, authorized Hosting domains and the exact approved Firebase UID list. Do not download a service-account key.
3. Create/verify a dedicated runtime service account with only the permissions Firebase Admin verification actually requires, using Cloud Run ADC.
4. Create/verify the `africa-south1` Artifact Registry repository and preview its cleanup policy before enabling deletion.
5. Configure the USD 10 monthly alerts; separately determine whether an eligible spend-cap budget covers every service. Do not represent alerts as a cap.
6. Decide App Check monitoring/enforcement and distributed abuse protection, or explicitly accept their absence and associated public cost/availability risk for the academic demo.
7. Fill an ignored `deployment/deployment.env.local`; compare every project, region, origin, UID and resource value with this review.
8. Run all local tests and build/inspect the image and static bundle. Review dependencies and the bundle scan; do not upload a dirty or unreviewed build.
9. Deploy the backend **privately first**, inspect the revision/service account/environment/resource bounds, and run the two-token private smoke test.
10. Obtain separate student approval for platform-public invocation. Only then introduce and review a narrowly scoped public-access action; never combine this with deployment/resource creation.
11. Run the one-token Firebase-to-Cloud-Run acceptance smoke from the hosted origin: health 200, readiness 503, missing/invalid token 401, disallowed UID 403, approved preview 200/29 features, approved score 503, exact CORS, production docs 404 and no score fields.
12. Deploy Firebase Hosting only after the API origin and CORS are exact. Re-run browser accessibility/auth/error tests, watch costs/logs, and record revision/image/Hosting release identifiers.

## Rollback and cleanup

For an application regression, route 100% traffic to a reviewed prior Cloud Run revision and roll back Firebase Hosting to its prior release; then repeat health/auth checks. If public exposure causes abuse, restore the Cloud Run Invoker check before diagnosing further. Revoke affected Firebase sessions, remove UIDs, or disable users where appropriate. Cleanup of Cloud Run, Artifact Registry or Hosting is destructive and must remain a separate student-confirmed action. Preserve needed logs and assessed evidence before deletion; never delete source data or Git history.

## Remaining blockers

- Exact project, site, service URL, runtime identity, Firebase app ID/API key and approved UIDs are placeholders.
- Billing/budget/spend-cap eligibility has not been inspected or configured.
- App Check and a distributed unauthenticated-traffic control are not implemented.
- Public-invocation risk has not been accepted and no public-IAM action exists.
- No live private deployment, hosted browser test, token-revocation integration test or cost/log observation has occurred.
- The model remains unapproved and absent; `/v1/score` must remain unavailable.

Phase 7C deployment may proceed only after these blockers are resolved and the student gives explicit approval for the relevant live action. Phase 7C.0 stops here.
