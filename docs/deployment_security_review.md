# Phase 12 deployment security review

## Decision

**NO-GO for deployment; PASS for local CI/CD implementation.** Billing is enabled and Firebase Hosting exists, but budget evidence, protected GitHub environments, branch protection, required APIs, WIF, deployment/runtime identities, Artifact Registry and a private Cloud Run service are missing. No live workflow has run.

## Trust boundaries

CI has `contents: read` only. It cannot request a GitHub OIDC token and receives no environment secret. Deployment credentials are available only inside manually dispatched jobs attached to named GitHub environments. Each deployment revalidates the exact repository, `main` ref, full SHA, successful matching CI and fixed project identity before WIF authentication.

The OIDC provider trusts one repository and `main`; service-account bindings additionally trust exact environment subjects. This prevents another repository or an unapproved branch from impersonating the deployers. The Cloud Run deployer, Hosting deployer and runtime identities are separate. No private key or Firebase refresh token is used.

## Supply-chain controls

- GitHub actions are pinned to immutable commit SHAs with reviewed release comments.
- Python and frontend project dependencies remain version/lockfile controlled.
- Firebase CLI is pinned to `15.33.0`; ADC/WIF support must be proven by the first preview. A failure stops deployment and does not authorize a token/key fallback.
- The Docker base image is digest-pinned. The production image is smoke-tested before upload, tagged with the full source SHA, resolved to a registry digest and deployed by digest.
- The image excludes datasets, tests, reports, notebooks, model packages/artifacts, private steering files and credentials.
- The frontend bundle is rebuilt from the selected SHA and scanned before publication.

## Runtime controls

The private pilot retains the Cloud Run Invoker IAM check. It uses request-based CPU, min 0/max 2, 1 CPU, 512 MiB, concurrency 20, 30-second timeout and non-root UID 10001. Production starts without scikit-learn/joblib or model files and explicitly disables experimental scoring. Firebase Admin uses ADC, checks revoked/disabled users and the server UID allowlist. Exact Hosting CORS origins, size/event limits and per-process rate limiting remain configured.

`/healthz` confirms process availability only. `/readyz` remains 503 `MODEL_NOT_APPROVED`. Successful infrastructure deployment does not approve the Isolation Forest, establish fraud detection or authorize production scoring.

## Browser-to-API limitation

Firebase Authentication and Cloud Run IAM authenticate different tokens. The static SPA can obtain a Firebase ID token but cannot safely mint a Google service identity token for an IAM-private service. Hosting rewrites do not create privileged identity. Therefore:

- a private pilot can be healthy and operator-callable while the hosted browser analysis remains unavailable;
- Hosting preview/live may show login and an accurate restricted/unavailable API state;
- a functional hosted analysis path still requires a separately approved BFF/proxy, or separate risk acceptance for public platform invocation with Firebase enforcement and stronger abuse controls; and
- Phase 12 contains no public-access workflow, `allUsers` grant or Invoker-check bypass.

## Cost and privacy

The proposed USD 10 monthly budget with alerts at 50%, 80% and 100% is a prerequisite attested by a fixed environment value only after human verification. Budget alerts do not stop spending. Cloud Run spend caps, where eligible, do not cap Firebase Hosting, Artifact Registry, Logging and all project costs. Max instances and cleanup decisions are additional controls, not guarantees.

Do not log bearer tokens, Firebase claims, raw event payloads, wallet histories or the UID allowlist. An account diagnostic emitted local Firebase CLI credential fields during read-only discovery; rotate that CLI session before any deployment and do not preserve the values. No credential value was written to a project file.

## Remaining acceptance gates

1. Rotate local Firebase CLI credentials.
2. Create and verify the budget/alerts and separately assess spend-cap availability.
3. Run and review the guarded bootstrap.
4. Configure protected GitHub environments/reviewers and `main` protection.
5. Run CI on the committed SHA and inspect every job.
6. Deploy the private pilot only; record image digest, revision and URL.
7. Complete two-token operator testing for protected routes and inspect logs.
8. Publish an expiring Hosting preview; verify sign-in domain, SPA refreshes and accurate API restriction.
9. Make a separate architecture/authorization decision before any fully accessible browser API.
10. Approve live Hosting separately; keep production scoring disabled.
