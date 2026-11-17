# Phase 11 cloud deployment record

## Outcome

**FAIL — no cloud deployment was made.** Local release acceptance passed, but the confirmed Google Cloud project has billing disabled. The Phase 11 instructions require cloud mutations to stop when billing is unresolved. Required service APIs and deployment resources are also missing or unavailable.

This failure is an operational deployment result, not a modelling result. Production anomaly scoring remains unavailable and no fraud or wash-trading prediction was exposed.

## Confirmed target

| Field | Verified value or state |
|---|---|
| Google Cloud project | `solana-wallet-risk` (`441056127470`) |
| Project lifecycle | Active |
| Firebase selected project | `solana-wallet-risk` |
| Preferred region | `africa-south1` |
| Planned Cloud Run service | `solana-wallet-risk-api` |
| Planned Artifact Registry repository | `solana-wallet-risk` |
| Planned image | `africa-south1-docker.pkg.dev/solana-wallet-risk/solana-wallet-risk/solana-wallet-risk-api:a9a4bcbd347ed87332abbd9bb84e2cd0a7e068e3` |
| Local image ID | `sha256:75df3c3731267e4b0692bb4f52b0a572d3588c2528f266a251cf2d081dad0a7a` |
| Registry digest | Not available; image was not pushed |
| Service URL | Not created or verified |
| Active revision | Not created or verified |
| Runtime identity | Planned `solana-wallet-risk-runtime@solana-wallet-risk.iam.gserviceaccount.com`; API returned `NOT_FOUND` |

The active `gcloud` account was `shakurshakurr7@gmail.com`. Its configured default project was `seotranslate-507816`, so every discovery command for this phase used an explicit `--project=solana-wallet-risk`; the default configuration was not changed.

## Preflight evidence

- Cloud Billing reported `billingEnabled: false` and no attached billing account.
- Firebase and Identity Toolkit APIs were enabled.
- Cloud Run, Artifact Registry, Cloud Build and IAM Credentials APIs were not in the enabled-service list.
- Artifact Registry and Cloud Run discovery returned service-disabled errors. Their live resource state therefore could not be verified.
- The dedicated runtime service account does not exist.
- The ignored root `.env` contains the required backend Firebase project, UID allowlist and revocation-check keys. Their values were not printed or copied into source.
- `deployment/deployment.env.local` is absent, so no reviewed live deployment environment has been assembled.

When the CLI offered to enable an API during discovery, the default `N` response was retained. No project, API, repository, service account, IAM binding, image, Cloud Run revision, budget or frontend hosting release was created or changed.

## Local release artifact

The production Docker build completed from the pinned Python 3.11.14 base. The image runs as `10001:10001`, starts with `python -m solana_risk.api.run`, listens on the environment-provided `PORT`, and contains only the API package and production dependencies selected by the Dockerfile. The build context excludes raw data, reports, notebooks, model artifacts, tests, local configuration and private steering files.

The local image is not a registry artifact. Its local ID must not be described as an Artifact Registry digest.

## Planned private deployment configuration

- invoker IAM check retained; no `allUsers` binding;
- minimum instances `0`, maximum instances `1`;
- `1` CPU, `512Mi` memory, concurrency `20`, timeout `30s`;
- request-based CPU throttling, no GPU and port `8080`;
- exact Firebase Hosting origins only;
- Firebase project identity, server-side approved-UID allowlist and token-revocation checks;
- request limits of 100 events and 262,144 bytes; and
- production model restriction preserved.

The deployment script and example were updated from maximum 2 to maximum 1 to match Phase 11. No live action in that script was executed.

## Required operator actions before retry

1. Attach an approved billing account to `solana-wallet-risk` and record who owns cost monitoring.
2. Configure a low budget/alerts and separately check spend-cap eligibility; ordinary alerts are not hard caps.
3. Enable only the required APIs after reviewing charges and permissions.
4. Create the named runtime service account and grant only the Firebase user-read permission needed for revoked/disabled-user checks.
5. Create the regional Docker repository and preview its cleanup policy.
6. Verify the deployer can push images, deploy Cloud Run, use the runtime identity and manage only the required service resources.
7. Assemble the ignored deployment environment, rerun local acceptance, then repeat read-only preflight before any push.

Google documents that a private Cloud Run caller must present a Google-signed ID token and that `X-Serverless-Authorization` can carry it when the application already uses `Authorization` ([Cloud Run service-to-service authentication](https://docs.cloud.google.com/run/docs/authenticating/service-to-service)).
