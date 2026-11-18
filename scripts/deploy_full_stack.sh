#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${DEPLOY_ENV_FILE:-${ROOT_DIR}/.env}"
REPOSITORY="Extreme-Ending/solana-wash-trading-detection"
FIREBASE_WORKFLOW="deploy-firebase.yml"

usage() {
  cat <<'EOF'
Usage: ./scripts/deploy_full_stack.sh FULL_GIT_SHA preview|live --execute

Deploy one reviewed, pushed main-branch commit to both application tiers:
  1. build, smoke-test, publish, and deploy the private Cloud Run backend;
  2. build and publish the same commit through the guarded Firebase workflow.

Backend configuration is loaded by deploy_private_local.sh from the ignored
root .env by default. Public frontend build configuration is read from the
selected GitHub environment (hosting-preview or production), with repository
variables used as a fallback.

This script does not write to Git, change IAM, make Cloud Run public, bypass
CI, enable experimental scoring, or weaken Firebase/UID authorization. Because
Cloud Run remains IAM-private, a Firebase-hosted browser cannot call the API
until a separate access-architecture change is explicitly reviewed and approved.
EOF
}

fail() {
  printf 'full-stack-deploy: %s\n' "$1" >&2
  exit 1
}

on_error() {
  local exit_code=$?
  printf '\nfull-stack-deploy: stopped after a command failed (exit %s).\n' "$exit_code" >&2
  printf 'One tier may already be deployed. Inspect the output and cloud state before retrying.\n' >&2
  exit "$exit_code"
}
trap on_error ERR

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "$1 is required."
}

github_variable() {
  local name="$1"
  local value=""

  value="$(gh variable get "$name" --repo "$REPOSITORY" --env "$GITHUB_ENVIRONMENT" \
    --json value --jq .value 2>/dev/null || true)"
  if [[ -z "$value" ]]; then
    value="$(gh variable get "$name" --repo "$REPOSITORY" \
      --json value --jq .value 2>/dev/null || true)"
  fi
  [[ -n "$value" ]] || fail "GitHub variable ${name} is missing from ${GITHUB_ENVIRONMENT} and the repository."
  printf '%s' "$value"
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

REVISION="${1:-}"
RELEASE="${2:-}"
EXECUTE="${3:-}"

[[ "$REVISION" =~ ^[0-9a-f]{40}$ ]] || {
  usage >&2
  fail "FULL_GIT_SHA must contain exactly 40 lowercase hexadecimal characters."
}
[[ "$RELEASE" == "preview" || "$RELEASE" == "live" ]] || {
  usage >&2
  fail "release must be preview or live."
}
[[ "$EXECUTE" == "--execute" && $# -eq 3 ]] || {
  usage >&2
  fail "deployment requires the explicit --execute flag."
}

for command in curl gcloud gh git jq python3; do
  require_command "$command"
done

[[ -f "$ENV_FILE" ]] || fail "private environment file not found: ${ENV_FILE}."
git -C "$ROOT_DIR" check-ignore -q -- "$ENV_FILE" || \
  fail "the environment file must be ignored by Git: ${ENV_FILE}."
[[ -x "$ROOT_DIR/scripts/deploy_private_local.sh" ]] || \
  fail "scripts/deploy_private_local.sh is missing or not executable."

[[ "$(git -C "$ROOT_DIR" rev-parse --show-toplevel)" == "$ROOT_DIR" ]] || \
  fail "repository root could not be verified."
[[ "$(git -C "$ROOT_DIR" branch --show-current)" == "main" ]] || fail "current branch must be main."
[[ "$(git -C "$ROOT_DIR" rev-parse HEAD)" == "$REVISION" ]] || fail "FULL_GIT_SHA must equal local HEAD."
[[ "$(git -C "$ROOT_DIR" rev-parse origin/main)" == "$REVISION" ]] || \
  fail "FULL_GIT_SHA must equal locally known origin/main; fetch manually if needed."
[[ -z "$(git -C "$ROOT_DIR" status --porcelain)" ]] || fail "working tree must be clean."

origin_url="$(git -C "$ROOT_DIR" remote get-url origin)"
case "$origin_url" in
  https://github.com/Extreme-Ending/solana-wash-trading-detection.git|\
  git@github.com:Extreme-Ending/solana-wash-trading-detection.git)
    ;;
  *) fail "origin does not match the approved GitHub repository." ;;
esac

gh auth status --hostname github.com >/dev/null
ci_success="$(gh run list --repo "$REPOSITORY" --workflow ci.yml --branch main \
  --limit 100 --json headSha,status,conclusion \
  | jq -r --arg sha "$REVISION" \
      'any(.[]; .headSha == $sha and .status == "completed" and .conclusion == "success")')"
[[ "$ci_success" == "true" ]] || fail "no successful completed CI run exists for the exact SHA."

if [[ "$RELEASE" == "live" ]]; then
  GITHUB_ENVIRONMENT="production"
  WORKFLOW_CONFIRMATION="HOSTING-LIVE"
else
  GITHUB_ENVIRONMENT="hosting-preview"
  WORKFLOW_CONFIRMATION="HOSTING-PREVIEW"
fi

GCP_PROJECT_ID="$(github_variable GCP_PROJECT_ID)"
GCP_PROJECT_NUMBER="$(github_variable GCP_PROJECT_NUMBER)"
GCP_WORKLOAD_IDENTITY_PROVIDER="$(github_variable GCP_WORKLOAD_IDENTITY_PROVIDER)"
FIREBASE_DEPLOY_SERVICE_ACCOUNT="$(github_variable FIREBASE_DEPLOY_SERVICE_ACCOUNT)"
FIREBASE_PROJECT_ID="$(github_variable FIREBASE_PROJECT_ID)"
VITE_FIREBASE_PROJECT_ID="$FIREBASE_PROJECT_ID"
FIREBASE_HOSTING_SITE="$(github_variable FIREBASE_HOSTING_SITE)"
VITE_API_BASE_URL="$(github_variable VITE_API_BASE_URL)"
VITE_FIREBASE_API_KEY="$(github_variable VITE_FIREBASE_API_KEY)"
VITE_FIREBASE_AUTH_DOMAIN="$(github_variable VITE_FIREBASE_AUTH_DOMAIN)"
VITE_FIREBASE_APP_ID="$(github_variable VITE_FIREBASE_APP_ID)"
COST_CONTROL_ATTESTATION="$(github_variable COST_CONTROL_ATTESTATION)"

GITHUB_REPOSITORY="$REPOSITORY" \
GITHUB_REF="refs/heads/main" \
GITHUB_SHA="$REVISION" \
GCP_PROJECT_ID="$GCP_PROJECT_ID" \
GCP_PROJECT_NUMBER="$GCP_PROJECT_NUMBER" \
GCP_WORKLOAD_IDENTITY_PROVIDER="$GCP_WORKLOAD_IDENTITY_PROVIDER" \
FIREBASE_DEPLOY_SERVICE_ACCOUNT="$FIREBASE_DEPLOY_SERVICE_ACCOUNT" \
FIREBASE_PROJECT_ID="$FIREBASE_PROJECT_ID" \
FIREBASE_HOSTING_SITE="$FIREBASE_HOSTING_SITE" \
VITE_API_BASE_URL="$VITE_API_BASE_URL" \
VITE_FIREBASE_API_KEY="$VITE_FIREBASE_API_KEY" \
VITE_FIREBASE_AUTH_DOMAIN="$VITE_FIREBASE_AUTH_DOMAIN" \
VITE_FIREBASE_PROJECT_ID="$VITE_FIREBASE_PROJECT_ID" \
VITE_FIREBASE_APP_ID="$VITE_FIREBASE_APP_ID" \
COST_CONTROL_ATTESTATION="$COST_CONTROL_ATTESTATION" \
python3 "$ROOT_DIR/scripts/validate_release_config.py" --mode "firebase-${RELEASE}"

printf 'Full-stack deployment plan\n'
printf '  Repository:  %s\n' "$REPOSITORY"
printf '  Revision:    %s\n' "$REVISION"
printf '  Backend:     private Cloud Run\n'
printf '  Frontend:    Firebase Hosting (%s)\n' "$RELEASE"
printf '  Environment: %s\n' "$GITHUB_ENVIRONMENT"
printf '  Site:        https://%s.web.app\n' "$FIREBASE_HOSTING_SITE"
printf '  Scoring:     experimental model disabled\n'
printf '  Browser API: blocked while Cloud Run remains IAM-private\n\n'

printf '[1/3] Starting the guarded private backend deployment.\n'
printf 'The backend script will request its own exact confirmation.\n\n'
DEPLOY_ENV_FILE="$ENV_FILE" "$ROOT_DIR/scripts/deploy_private_local.sh" "$REVISION" --execute

service_url="$(gcloud run services describe solana-wallet-risk-api \
  --project "$GCP_PROJECT_ID" --region africa-south1 --format='value(status.url)')"
[[ "$service_url" == https://*.run.app ]] || fail "deployed Cloud Run service URL is unavailable."
[[ "${VITE_API_BASE_URL%/}" == "${service_url%/}" ]] || \
  fail "GitHub VITE_API_BASE_URL does not match the deployed Cloud Run service URL. Update the variable before publishing Hosting."

printf '\n[2/3] Backend verified. Firebase Hosting is the next live mutation.\n'
printf 'Type FULL-STACK-%s/%s to publish Hosting: ' "${RELEASE^^}" "$REVISION"
read -r hosting_confirmation
[[ "$hosting_confirmation" == "FULL-STACK-${RELEASE^^}/${REVISION}" ]] || \
  fail "Hosting confirmation did not match; the backend remains deployed and Hosting was not dispatched."

dispatch_started="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
gh workflow run "$FIREBASE_WORKFLOW" --repo "$REPOSITORY" --ref main \
  -f "revision=${REVISION}" -f "release=${RELEASE}" -f "confirmation=${WORKFLOW_CONFIRMATION}"

run_id=""
for _attempt in {1..20}; do
  run_id="$(gh run list --repo "$REPOSITORY" --workflow "$FIREBASE_WORKFLOW" \
    --event workflow_dispatch --branch main --limit 30 --json databaseId,headSha,createdAt \
    | jq -r --arg sha "$REVISION" --arg started "$dispatch_started" \
        '[.[] | select(.headSha == $sha and .createdAt >= $started)]
         | sort_by(.createdAt) | last | .databaseId // empty')"
  [[ -n "$run_id" ]] && break
  sleep 3
done
[[ -n "$run_id" ]] || fail "Firebase workflow was dispatched but its run ID was not found; inspect GitHub Actions."

run_url="https://github.com/${REPOSITORY}/actions/runs/${run_id}"
printf 'Monitoring Firebase workflow: %s\n' "$run_url"
if ! gh run watch "$run_id" --repo "$REPOSITORY" --exit-status; then
  printf '\nFirebase deployment failed. Failed-step log follows.\n' >&2
  gh run view "$run_id" --repo "$REPOSITORY" --log-failed >&2 || true
  fail "Firebase workflow failed; the private backend remains deployed."
fi

printf '\n[3/3] Verifying deployment outcome...\n'
hosting_url="https://${FIREBASE_HOSTING_SITE}.web.app"
if [[ "$RELEASE" == "live" ]]; then
  http_status="$(curl --silent --show-error --location --output /dev/null \
    --write-out '%{http_code}' --max-time 30 "$hosting_url")"
  [[ "$http_status" =~ ^2[0-9][0-9]$ ]] || \
    fail "live Firebase Hosting returned HTTP ${http_status}; inspect ${run_url}."
  printf 'Live Hosting HTTP status: %s\n' "$http_status"
else
  printf 'Preview channel published; obtain its expiring URL from the workflow output.\n'
fi

printf '\nFull-stack deployment completed for the same reviewed Git SHA.\n'
printf '  Revision: %s\n' "$REVISION"
printf '  Backend:  %s (IAM-private)\n' "$service_url"
printf '  Frontend: %s\n' "$hosting_url"
printf '  Workflow: %s\n' "$run_url"
printf '  Scoring:  experimental model disabled\n'
printf '  Warning:  the hosted browser cannot invoke the IAM-private backend.\n'
