# Google Cloud and Firebase setup for keyless deployment

## Initial discovery snapshot

| Item | Value / observed state on 2026-11-18 |
|---|---|
| Project | `solana-wallet-risk` (`441056127470`), active |
| Region | `africa-south1` |
| Billing | linked and enabled; budget could not be read with the available permission/API |
| Firebase | active project and default Hosting site `solana-wallet-risk` |
| Hosting URL | `https://solana-wallet-risk.web.app`; existence verified, publication not performed |
| Cloud Run API | disabled |
| Artifact Registry API | disabled |
| IAM Credentials / STS APIs | not observed enabled |
| Artifact repository | not available; API disabled |
| Runtime/deployment identities | not created |
| WIF pools/providers | none observed |
| Cloud Run service | no verified service; API disabled |
| Local default gcloud project | unrelated `seotranslate-507816`; never use implicitly |

No resource above was created or changed during the initial discovery.

## Post-bootstrap verification

On 2026-11-18 the guarded bootstrap completed. Cloud Run, Artifact Registry, IAM Credentials, STS and Firebase Hosting APIs are enabled. The empty `solana-wallet-risk` Docker repository, three enabled user-managed service accounts, active `github-actions/github` provider, repository/main condition, exact environment-subject impersonation grants and intended project/repository roles were verified. All three accounts have zero user-managed keys. No Cloud Run service, container digest or Hosting release was created.

## Bootstrap order

1. Rotate the local Firebase CLI session before further work because a diagnostic command emitted credential material. Sign out and sign in again in the student's terminal; never copy its JSON credential output into an issue, report or repository.
2. In Cloud Billing, create a project-scoped USD 10 monthly budget with 50%, 80% and 100% alerts. Confirm notification recipients. Alerts are delayed notifications, not a universal hard cap. Separately check current Cloud Run spend-cap eligibility and scope.
3. Review the plan:

   ```bash
   ./scripts/bootstrap_github_wif.sh plan
   ```

4. Only after reviewing every target, run the idempotent bootstrap personally:

   ```bash
   ./scripts/bootstrap_github_wif.sh apply --execute
   ```

The bootstrap targets only `solana-wallet-risk`; checks project number and billing; enables the required APIs; creates one Docker repository, three user-managed service accounts, a repository/main-restricted OIDC provider and exact environment-subject WIF bindings. It creates no key, deployment, budget, public principal or Git change. It does not configure the existing cleanup policy because Phase 12 requires no automatic deletion without a separate retention decision.

## Identities and roles

| Identity | Binding scope | Role | Purpose |
|---|---|---|---|
| `github-cloud-run-deployer@...` | project | `roles/run.developer` | create/update private revisions and perform the authenticated pilot check (`run.routes.invoke` is already included) |
| same | project | `roles/serviceusage.serviceUsageConsumer` | consume enabled APIs |
| same | one Artifact Registry repository | `roles/artifactregistry.writer` | publish immutable images |
| same | runtime service account | `roles/iam.serviceAccountUser` | attach only the reviewed runtime identity |
| `github-firebase-deployer@...` | project | `roles/firebasehosting.admin` | Hosting releases only |
| same | project | `roles/serviceusage.apiKeysViewer` | Firebase CLI project/web configuration lookup required by Firebase deployments |
| same | project | `roles/serviceusage.serviceUsageConsumer` | consume Firebase APIs |
| `solana-wallet-risk-runtime@...` | project | `roles/firebaseauth.viewer` | revoked/disabled-user lookup used by Firebase Admin verification |

No identity receives Owner, Editor, service-account-key creation, IAM administration, billing mutation or model-storage access. The Cloud Run runtime receives no deployment role. If testing proves a narrower custom runtime permission set supports revocation checks, replace `firebaseauth.viewer` after documenting the result.

## Workload Identity Federation contract

The pool/provider are `github-actions/github`. Map `google.subject=assertion.sub`, `attribute.repository=assertion.repository` and `attribute.ref=assertion.ref`. The provider condition must require both:

```text
assertion.repository == 'Extreme-Ending/solana-wash-trading-detection'
assertion.ref == 'refs/heads/main'
```

Service-account impersonation uses exact OIDC subjects, not organization-wide trust:

```text
repo:Extreme-Ending/solana-wash-trading-detection:environment:private-pilot
repo:Extreme-Ending/solana-wash-trading-detection:environment:hosting-preview
repo:Extreme-Ending/solana-wash-trading-detection:environment:production
```

## GitHub environment configuration

Set these environment variables with the exact names shown. Public Firebase Web values are variables, not secrets.

| Environment variable | Environments | Required value |
|---|---|---|
| `GCP_PROJECT_ID` | all | `solana-wallet-risk` |
| `GCP_PROJECT_NUMBER` | all | `441056127470` |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | all | full provider resource name |
| `COST_CONTROL_ATTESTATION` | all | `USD10-50-80-100-REVIEWED` only after budget review |
| `GCP_REGION` | private pilot | `africa-south1` |
| `GCP_DEPLOY_SERVICE_ACCOUNT` | private pilot | Cloud Run deployer email |
| `GCP_RUNTIME_SERVICE_ACCOUNT` | private pilot | runtime email |
| `ARTIFACT_REGISTRY_REPOSITORY` | private pilot | `solana-wallet-risk` |
| `CLOUD_RUN_SERVICE` | private pilot | `solana-wallet-risk-api` |
| `FIREBASE_PROJECT_ID` | all | `solana-wallet-risk` |
| `FIREBASE_HOSTING_SITE` | all | `solana-wallet-risk` |
| `FIREBASE_DEPLOY_SERVICE_ACCOUNT` | Hosting | Hosting deployer email |
| `VITE_API_BASE_URL` | Hosting | exact HTTPS API origin; private pilot remains unavailable to browsers |
| `VITE_FIREBASE_API_KEY` | Hosting | actual public web API key |
| `VITE_FIREBASE_AUTH_DOMAIN` | Hosting | `solana-wallet-risk.firebaseapp.com` |
| `VITE_FIREBASE_APP_ID` | Hosting | actual public web app ID |

The `private-pilot` environment also needs one encrypted secret: `SOLANA_RISK_ALLOWED_UIDS`. It is a comma-separated server-side UID allowlist. Never place it in a `VITE_` variable or print it.

## Student-operated verification

After bootstrap, rerun read-only checks with explicit project flags. Do not run `gcloud config set project`:

```bash
gcloud billing projects describe solana-wallet-risk
gcloud services list --enabled --project solana-wallet-risk
gcloud artifacts repositories describe solana-wallet-risk \
  --project solana-wallet-risk --location africa-south1
gcloud iam workload-identity-pools providers describe github \
  --workload-identity-pool github-actions --project solana-wallet-risk --location global
firebase hosting:sites:list --project solana-wallet-risk
```

Then create the three GitHub environments and protection rules in the GitHub UI. Push the reviewed Phase 12 commit personally, wait for the exact SHA's CI run to pass, and only then manually dispatch the desired deployment workflow.
