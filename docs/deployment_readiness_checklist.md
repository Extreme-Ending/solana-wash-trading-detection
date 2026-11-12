# Deployment readiness checklist

## Phase 7A result

Repository preparation is locally testable and non-destructive. A live deployment is not authorized or claimed. The static frontend can be hosted, and the container can be deployed privately, but the end-to-end hosted browser experience remains blocked until an API access strategy is approved and implemented.

## Before creating resources

- [ ] Student selects one real Google Cloud/Firebase project ID and confirms project ownership.
- [ ] Student reviews billing implications and explicitly decides whether to attach/retain billing.
- [ ] Current `africa-south1` product availability and pricing are rechecked.
- [ ] Cloud Run, Artifact Registry and Firebase Hosting prerequisites/APIs are reviewed.
- [ ] A low budget and several alerts are configured, acknowledging that alerts do not cap charges.
- [ ] Student/deployer roles are task-scoped; the runtime identity has no project roles.
- [ ] Artifact Registry cleanup policy is reviewed in dry-run mode.
- [ ] The private-service limitation for a Firebase SPA is accepted as a blocker; anonymous access is not silently enabled.

## Local release gate

- [ ] `./scripts/deployment.sh prerequisites` reports all required tools.
- [ ] `./scripts/deployment.sh plan` shows the intended project, Johannesburg region, SHA image and private deployment command.
- [ ] `python3 -m pytest -q` passes.
- [ ] `npm --prefix frontend ci` completes from the lockfile.
- [ ] frontend typecheck, tests and a production build pass.
- [ ] `python3 scripts/validate_deployment_bundle.py frontend/dist` passes.
- [ ] `docker compose config --quiet` passes.
- [ ] `python3 scripts/container_smoke_test.py` passes with health 200, readiness 503, preview 200 and score 503.
- [ ] If port 8080 is already in use, preserve the existing service and rerun the smoke script with reviewed unused `--host-port` and `--custom-host-port` values.
- [ ] `git diff --check` passes; the student reviews all changes without staging them automatically.

## Future controlled rollout

- [ ] Copy the deployment example to a local ignored file; replace every placeholder and export it.
- [ ] Build and inspect the commit-SHA image locally.
- [ ] Confirm image contents: non-root, no datasets/artifacts/private files, no model libraries.
- [ ] Tag and push only that exact SHA image.
- [ ] Deploy Cloud Run privately with min 0/max 2 and the reviewed runtime identity.
- [ ] Verify the deployed service with a short-lived identity token and synthetic request only.
- [ ] Build the frontend using the exact HTTPS Cloud Run origin and rescan `frontend/dist`.
- [ ] Deploy Hosting only after checking the selected project/site.
- [ ] Do not describe the hosted SPA as functional end-to-end while the API is private.
- [ ] Inspect error rates, latency, logs, instance count and billing after the synthetic smoke test.

## Access-decision gate

Before any public browser demo, document and approve one of these paths:

1. end-user authentication with server-side token verification plus abuse/rate controls; or
2. explicitly risk-accepted public access limited to the descriptive API, with rate limiting, monitoring, privacy review and a defined shutdown procedure.

Do not put Google identity tokens or service-account keys in Vite/Firebase files. Do not treat exact CORS as authentication. Model readiness and public access are separate decisions.

## Rollback

- [ ] Record the new and prior revision names and SHA tags before traffic changes.
- [ ] If the new revision fails, list revisions and set `ROLLBACK_REVISION` to the reviewed prior name.
- [ ] Run `./scripts/deployment.sh rollback --execute` and confirm the exact project/region/action.
- [ ] Repeat the authenticated synthetic smoke test.
- [ ] Preserve the failed image/revision long enough for diagnosis; do not rewrite Git history.

## Cleanup

- [ ] Describe/list the exact Cloud Run service, repository and Hosting site first.
- [ ] Confirm no shared workload depends on the single repository or Hosting site.
- [ ] Run `./scripts/deployment.sh cleanup --execute` only when deletion is intended.
- [ ] Review leftover IAM bindings, runtime service account, enabled APIs, budgets and logs separately.
- [ ] Verify billing/resource dashboards after cleanup; deletion does not guarantee that all charges stop instantly.

## Current blockers and prerequisites

- No real project ID, Firebase site, deployment URL, repository, service account, IAM binding or cloud authentication state is recorded in source.
- In the managed validation environment, the installed `gcloud` Snap reports that `snap-confine` is unconfined/elevated and asks for the `snapd.apparmor` service. The Firebase CLI credential check also could not complete its remote/config check. Rerun `./scripts/deployment.sh prerequisites` in the student's ordinary terminal; if repeated, repair the Google Cloud CLI/AppArmor installation and Firebase CLI access before any cloud action. Phase 7A did not verify cloud authentication.
- No permission/billing decision has been made in this phase.
- The safe default Cloud Run service is private, so a static browser cannot invoke it directly.
- No authentication or distributed rate limiting exists; public unauthenticated API access is therefore not approved by this preparation.
- The API intentionally has no available model and makes no fraud/wash-trading prediction.
