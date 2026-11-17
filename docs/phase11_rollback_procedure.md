# Phase 11 rollback procedure

## Current state

There is no deployed revision to roll back and no prior service URL or image digest. Running a rollback now would fail and must not be represented as tested.

## Procedure for a future private pilot

Before changing traffic, record the project, region, service, new revision, prior healthy revision, immutable image URI and registry digest.

1. Inspect revisions and traffic without changing them:

   ```bash
   gcloud run revisions list \
     --project=solana-wallet-risk \
     --region=africa-south1 \
     --service=solana-wallet-risk-api
   ```

2. If the new revision fails health, authentication, model-gate or log review, set `ROLLBACK_REVISION` to the exact previously verified revision and review the dry-run plan.

3. The authorized operator may execute the guarded repository action interactively:

   ```bash
   PROJECT_ID=solana-wallet-risk \
   REGION=africa-south1 \
   ROLLBACK_REVISION=THE_REVIEWED_PRIOR_REVISION \
   ./scripts/deployment.sh rollback --execute
   ```

4. Verify traffic is 100% on the prior revision, then repeat private platform-authenticated `/healthz`, `/readyz`, missing/invalid application-token, approved-user preview and disabled-score tests.

5. Inspect logs and metrics after rollback. Preserve the failed revision and immutable image long enough for diagnosis; do not rewrite Git history or overwrite the image tag.

If there is no prior healthy revision, route no demonstration traffic and remove access through the approved Cloud Run operational process rather than weakening authentication. Any destructive service or repository deletion requires separate target verification and intent.

The repository rollback action changes Cloud Run traffic only. It does not reset source, amend a commit or perform any Git operation.
