# Phase 8D deployment-readiness assessment

## Decision summary

| Area | Decision | Basis |
|---|---|---|
| Engineering readiness | **CONDITIONAL GO** for a local academic demonstration | Deterministic pipeline, actual-artifact API audit, full automated tests, typed frontend, checksum-pinned loader and production fail-closed controls pass. Real hosted Firebase/browser protected-route acceptance remains unverified. |
| Research readiness | **NO-GO** for fraud/wash-trading effectiveness claims; **CONDITIONAL GO** for anomaly research | No verified outcomes, incomplete extraction metadata and data-sharing permission, primary proposal/rubric absent, written methodology evidence absent locally and AI disclosure gap. |
| Cloud readiness | **NO-GO** for live deployment | No Phase 8D cloud mutation or acceptance test occurred; project, billing, IAM/runtime identity, public/private browser access choice, production data source and production artifact policy are unresolved. |

Private infrastructure deployment can be considered separately from enabling scoring. The current container deliberately excludes the experimental artifact and must continue returning `MODEL_NOT_APPROVED` in production.

## Engineering evidence

- FastAPI validates explicit UTC, bounded request sizes/event counts, identity grouping and exact schemas.
- Firebase Admin verification checks signature through the SDK, configured project, issuer/audience, expiry, revoked/disabled status, verified email, Google provider and server-side UID allowlist. Failures map to 401/403/503 without echoing credentials.
- The local experimental loader verifies file type, SHA-256, manifest, runtime versions, feature registry/order, cutoff, snapshot and training reference before joblib deserialization.
- The experimental gate is development-only. Production does not load the injected or configured scorer.
- React carries Firebase ID tokens in Bearer headers, validates responses and presents errors/disabled states without fabricating scores.
- The production Docker image runs non-root and intentionally contains no data, reports, experimental artifacts, modelling packages, private steering files or credentials.
- CORS is explicit; the local limiter is per instance and is not represented as distributed abuse protection.

## Authentication and browser status

The API's real-artifact success path was tested with the application factory's test-only verifier seam. Missing, invalid and expired credentials were rejected, and production scoring failed closed. The full auth tests cover wrong project, unapproved UID, wrong provider, unverified email and verifier unavailability.

No real Firebase token was acquired or printed. No interactive Google popup or hosted approved-account session was completed. A real installed headless Chrome loaded the locally served unauthenticated frontend at desktop, tablet and mobile sizes, but that is visual shell evidence only. Production acceptance still needs an approved account, registered domain, exact Firebase web configuration and real Admin/ADC verification.

The browser audit found and fixed one startup defect: missing production API configuration previously caused a blank page during fail-closed module initialization. It now renders a generic accessible configuration alert without displaying environment values. A build with an explicit HTTPS API origin still renders the normal shell.

## Cloud blockers and required student-operated actions

1. Verify the dedicated Google Cloud/Firebase project, ownership, billing and `africa-south1` availability; create nothing as part of this audit.
2. Verify Firebase web app, Google provider, authorized domains/site and the exact UID allowlist. Never place a service-account key in the frontend or repository.
3. Verify a dedicated Cloud Run runtime service account and the least privileges needed for Firebase user/revocation checks. Use ADC; do not download a private key.
4. Configure Artifact Registry and immutable full-Git-SHA tagging. Keep datasets and the experimental artifact out of the production image unless a separately approved artifact policy exists.
5. Configure the Phase 12 private-pilot resource bounds (min 0, max 2, 1 CPU, 512 MiB, concurrency 20, timeout 30 s) and exact frontend CORS origin.
6. Configure and test budget alerts; separately determine whether a spend-cap budget is eligible and covers each service. Alerts are not a hard cap.
7. Deploy privately first and preserve the Invoker IAM check. A static SPA cannot directly satisfy private Cloud Run IAM; select and review an identity-aware proxy/backend-for-frontend or explicitly approve the public-platform risk in a later phase. No public-access mutation is currently authorized.
8. Run the private two-token smoke, inspect revision identity/config/image, then complete hosted Firebase-to-API acceptance before publishing the frontend.
9. Keep production scoring disabled until research and artifact-approval gates are explicitly satisfied.

## Rollback and operational boundary

Use an explicitly named prior Cloud Run revision and prior Firebase Hosting release for rollback. Restore the Invoker check first if public exposure causes abuse. Artifact cleanup, resource deletion, IAM changes and billing changes remain separate student-confirmed operations. Preserve research evidence and logs before any deletion.

## Acceptance checklist

- [ ] Full local Python/frontend/type/build/container/privacy checks pass from a reviewed tree.
- [ ] Exact project/site/region/account/resource identities are verified read-only.
- [ ] Billing, alerts and spend-cap eligibility are reviewed separately.
- [ ] Runtime service account and Firebase revocation permissions are verified.
- [ ] Immutable image digest/tag and rollback revision are recorded.
- [ ] Private Cloud Run deploy passes health, readiness, auth and content inspection.
- [ ] Browser access architecture is explicitly approved without embedding a credential.
- [ ] Hosted real-Firebase checks cover 401, 403, approved preview, CORS and token revocation.
- [ ] Static bundle contains no secrets/private files.
- [ ] Production still refuses experimental scoring.
- [ ] Dataset extraction metadata/data-sharing permission, methodology evidence and disclosure gaps are resolved before research claims.

Passing local checks is necessary but not sufficient for live cloud deployment or research approval.
