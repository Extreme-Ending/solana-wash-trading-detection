# GitHub Actions deployment

## Separation of duties

Phase 12 defines three independent workflows. None commits source, changes Git history, or deploys from a pull request.

| Workflow | Trigger | Credentials | Effect |
|---|---|---|---|
| `ci.yml` | pull request to `main`; push to `main` | read-only `GITHUB_TOKEN`; no OIDC or cloud secret | Python, frontend, container, bundle, shell, whitespace and workflow validation |
| `deploy-cloud-run.yml` | manual `workflow_dispatch` on `main` | WIF only after the `private-pilot` environment gate | build, smoke, push SHA-tagged image, resolve digest, deploy exact digest privately |
| `deploy-firebase.yml` | manual `workflow_dispatch` on `main` | WIF only after `hosting-preview` or `production` environment gate | build/scan SPA, then publish an expiring preview or explicitly approved live Hosting release |

Each deployment requires the full 40-character SHA, an exact confirmation phrase, and a successful completed `CI` run for the same SHA. Deployment jobs use concurrency groups and do not cancel an in-progress release. Third-party actions are pinned to immutable reviewed commits. Checkout never persists a repository credential.

## CI coverage

The unprivileged workflow uses Python 3.11 and Node 22.22.2, matching `pyproject.toml`, `frontend/package.json` and the highest minimum required by the locked frontend dependencies. It runs:

```text
python -m pytest -q
npm ci
npm test -- --run
npm run typecheck
npm run build
python3 scripts/validate_deployment_bundle.py frontend/dist
docker compose config --quiet
python3 scripts/container_smoke_test.py ...
bash -n and shellcheck
python3 scripts/validate_workflows.py
actionlint v1.7.7
git diff/show --check
```

CI builds with synthetic, format-valid public Firebase configuration and an `.invalid` API origin. It never receives deploy credentials, the production UID allowlist, or a model artifact. A CI build is validation evidence, not a deployment.

## Cloud Run pilot

The protected job validates project `solana-wallet-risk`, project number `441056127470`, region `africa-south1`, billing, required APIs, the Docker repository and separate deployment/runtime identities. It builds and exercises the production Dockerfile before upload. The image is tagged with the full Git SHA, its registry digest is resolved and validated, and Cloud Run receives `IMAGE@sha256:...`, never `latest`.

The service remains IAM-private. The deploy command preserves the Invoker check, request-based CPU, min 0/max 2, 1 CPU, 512 MiB, concurrency 20, timeout 30 seconds, port 8080 and the user-managed runtime identity. Production explicitly sets `SOLANA_RISK_ENABLE_EXPERIMENTAL_SCORING=false`; no model path, manifest or digest is supplied. The workflow verifies digest identity, authorized `/healthz`, expected `/readyz` 503 `MODEL_NOT_APPROVED`, and anonymous platform rejection. A full protected application-route check still requires a short-lived approved-user Firebase token and remains a student-operated post-deploy test.

## Firebase Hosting

Preview and live publication share one workflow but use different protected environments and exact confirmations. Preview deploys a seven-day SHA channel. Live runs only with `release=live`, `HOSTING-LIVE`, and the `production` environment approval. The pinned Firebase CLI is `15.33.0` and authenticates through ADC created from WIF; neither `FIREBASE_TOKEN` nor a service-account key is accepted.

The workflow deploys only Hosting from the tracked `firebase.json`. It does not run `firebase init` or deploy Functions, Firestore, Storage or Authentication configuration. SPA rewrites and cache/security headers remain tracked. If ADC/WIF fails, the workflow stops; it must not fall back to a long-lived key or refresh token.

## Required GitHub controls

Create these environments in repository settings:

- `private-pilot`: restrict deployment to `main`; add a required reviewer if the repository plan supports it.
- `hosting-preview`: restrict to `main`; reviewer recommended.
- `production`: restrict to `main`; required reviewer strongly required.

At discovery on 2026-11-18, the public repository had no environments and no `main` branch protection. Until those controls are configured and verified, deployment is **NO-GO**. If the plan cannot enforce reviewers, retain manual-only workflows, require the student to review the exact SHA/CI run in the Actions UI, and never schedule or add push deployment triggers.

## Rollback

Cloud Run rollback is an explicit traffic reassignment to a named prior healthy revision:

```bash
gcloud run revisions list --service solana-wallet-risk-api \
  --project solana-wallet-risk --region africa-south1
ROLLBACK_REVISION='<reviewed-revision>' ./scripts/deployment.sh rollback --execute
```

Firebase Hosting retains release history. Inspect releases in the Firebase console and use the supported rollback action for the selected site/release; do not rebuild an old source tree under a new SHA and call that rollback. Record the restored release and verify routing, authentication UI and bundle privacy afterwards.
