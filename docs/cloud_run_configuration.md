# Cloud Run and Artifact Registry configuration

## Image contract

The existing root `Dockerfile` remains the only production image definition. It uses a digest-pinned Python 3.11 base, installs only the API dependency group, starts with the configurable `PORT`, runs as UID/GID 10001, and copies no dataset, report, notebook, test or experimental model artifact. Phase 7A additionally excludes Firebase/deployment files from the Docker context.

Every proposed image is tagged with the full Git commit SHA:

```text
africa-south1-docker.pkg.dev/PROJECT_ID/solana-wallet-risk/solana-wallet-risk-api:GIT_SHA
```

The SHA is read with `git rev-parse --verify HEAD`; the deployment helper performs no Git write operation.

## Resource and runtime settings

| Setting | Prepared value | Reason |
|---|---:|---|
| Region | `africa-south1` | Cloud Run and Artifact Registry support, regional proximity to Nairobi, current Tier 1 pricing |
| Billing mode | request-based (`--cpu-throttling`) | CPU is allocated for request handling rather than instance-based idle work |
| Minimum instances | `0` | scale to zero during academic inactivity |
| Maximum instances | `2` | bound accidental fan-out and cost; not a hard spending cap |
| CPU / memory | `1` / `512Mi` | conservative initial API allocation, to be adjusted only from observed evidence |
| Concurrency | `20` | modest bounded concurrency for a CPU/dataframe endpoint |
| Timeout | `30s` | bounds individual requests |
| Port | `8080` | matches the tested image default; Cloud Run still supplies `PORT` |
| Service identity | `solana-wallet-risk-runtime@PROJECT_ID.iam.gserviceaccount.com` | user-managed, no project roles for the current API |
| Invocation | private | anonymous access is not enabled by default |

Google documents [request-based billing](https://cloud.google.com/run/docs/configuring/billing-settings), [minimum instances](https://cloud.google.com/run/docs/configuring/min-instances), and the [`gcloud run deploy` flags](https://cloud.google.com/sdk/gcloud/reference/run/deploy). The settings must be revalidated against current product limits immediately before deployment.

## Least-privilege setup

Separate the human/deployer, Cloud Run service agent and runtime identity. The current application calls no Google Cloud APIs, so its runtime service account requires no project role. Do not attach Owner, Editor, Artifact Registry writer or Firebase roles to it.

Minimum task-scoped roles for future setup are:

- repository creator/admin: `roles/artifactregistry.admin` only while creating/configuring the repository and cleanup policy;
- image publisher: `roles/artifactregistry.writer` on the single repository;
- Cloud Run deployer: `roles/run.developer` on the project/service, `roles/artifactregistry.reader` on the repository, and `roles/iam.serviceAccountUser` on the selected runtime service account;
- authenticated smoke-test caller: `roles/run.invoker` on the single Cloud Run service; and
- Firebase deployer: `roles/firebasehosting.admin` for the hosting task.

Google recommends a user-managed [Cloud Run service identity](https://cloud.google.com/run/docs/securing/service-identity). Role requirements should be confirmed in the current [Cloud Run deployment permissions](https://cloud.google.com/run/docs/deploying#required_roles) and [Artifact Registry access-control](https://cloud.google.com/artifact-registry/docs/access-control) documentation. Remove temporary administrative grants after setup.

## Future setup commands

The following are student-reviewed examples only; none ran in Phase 7A:

```bash
gcloud config set project YOUR_GCP_PROJECT_ID
gcloud services enable run.googleapis.com artifactregistry.googleapis.com
gcloud iam service-accounts create solana-wallet-risk-runtime \
  --project YOUR_GCP_PROJECT_ID \
  --display-name 'Solana wallet risk Cloud Run runtime'
gcloud artifacts repositories create solana-wallet-risk \
  --project YOUR_GCP_PROJECT_ID \
  --location africa-south1 \
  --repository-format docker \
  --description 'Academic capstone API images'
gcloud artifacts repositories set-cleanup-policies solana-wallet-risk \
  --project YOUR_GCP_PROJECT_ID \
  --location africa-south1 \
  --policy deployment/artifact_cleanup_policy.json \
  --dry-run
```

Enabling APIs, creating identities/repositories and assigning roles may require billing or elevated permission and must be a deliberate student action. After verifying the cleanup dry run, the student may rerun the last command without `--dry-run`.

## Build, publish and deploy sequence

Create and review a private local configuration, then export it into the current shell:

```bash
cp deployment/deployment.env.example deployment/deployment.env.local
chmod 600 deployment/deployment.env.local
# Edit deployment/deployment.env.local and replace every placeholder.
set -a
source deployment/deployment.env.local
set +a
```

The local file is Git-ignored and must not contain credentials; it holds identifiers, origins and resource limits only. Then inspect the plan and run each separately confirmed step:

```bash
./scripts/deployment.sh plan
./scripts/deployment.sh build-image --execute
./scripts/deployment.sh tag-image --execute
./scripts/deployment.sh push-image --execute
./scripts/deployment.sh deploy-cloud-run --execute
```

Each action prints the target and effect, and requires the exact interactive phrase `PROJECT_ID/africa-south1/ACTION`. The deployment uses `--no-allow-unauthenticated`, request-based billing, min 0/max 2, the controlled identity and the actual Hosting site's matching `web.app`/`firebaseapp.com` CORS origins. It sets existing request/event limits explicitly and does not load or promote a model.

## Authenticated verification and rollback

An authorized student can obtain a short-lived identity token and pipe it without placing it in the process arguments:

```bash
gcloud auth print-identity-token | \
  CLOUD_RUN_URL=https://YOUR_CLOUD_RUN_SERVICE_HOST ./scripts/deployment.sh smoke
```

The test expects health 200, readiness 503, synthetic feature preview 200 with 29 fields, and score 503. It never prints the token. For a faulty new revision, inspect available revisions, export a reviewed `ROLLBACK_REVISION`, then run:

```bash
gcloud run revisions list --service solana-wallet-risk-api \
  --project YOUR_GCP_PROJECT_ID --region africa-south1
./scripts/deployment.sh rollback --execute
```

Rollback changes traffic only; it does not rewrite Git history. A hosted browser remains blocked while the service is private.
