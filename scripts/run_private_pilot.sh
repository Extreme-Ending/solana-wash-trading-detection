#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="solana-wallet-risk"
REGION="africa-south1"
SERVICE="solana-wallet-risk-api"
REPOSITORY="Extreme-Ending/solana-wash-trading-detection"
WORKFLOW="deploy-cloud-run.yml"
REQUIRED_API="iam.googleapis.com"

usage() {
  cat <<'EOF'
Usage: ./scripts/run_private_pilot.sh FULL_GIT_SHA --execute

Student-operated launcher for the guarded private Cloud Run pilot. It verifies
the reviewed main SHA and successful CI, enables only iam.googleapis.com when
missing, dispatches the existing private-pilot workflow, monitors the run, and
checks that the resulting Cloud Run service has no public IAM principal.

This script never changes Git history, makes Cloud Run public, deploys Firebase
Hosting, supplies a model artifact, bypasses hooks, or force-pushes anything.
EOF
}

fail() {
  printf 'private-pilot: %s\n' "$1" >&2
  exit 1
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

REVISION="${1:-}"
EXECUTE="${2:-}"
[[ "$REVISION" =~ ^[0-9a-f]{40}$ ]] || {
  usage >&2
  fail "FULL_GIT_SHA must contain exactly 40 lowercase hexadecimal characters."
}
[[ "$EXECUTE" == "--execute" && $# -eq 2 ]] || {
  usage >&2
  fail "deployment requires the explicit --execute flag."
}

for command in gh gcloud git jq; do
  command -v "$command" >/dev/null 2>&1 || fail "$command is required."
done

[[ "$(git rev-parse --show-toplevel)" == "$PWD" ]] || \
  fail "run this script from the repository root."
[[ "$(git branch --show-current)" == "main" ]] || fail "the current branch must be main."
[[ "$(git rev-parse HEAD)" == "$REVISION" ]] || fail "FULL_GIT_SHA must equal local HEAD."
[[ "$(git rev-parse origin/main)" == "$REVISION" ]] || \
  fail "FULL_GIT_SHA must equal the locally known origin/main. Fetch manually if needed."
[[ -z "$(git status --porcelain)" ]] || fail "the working tree must be clean."

origin_url="$(git remote get-url origin)"
case "$origin_url" in
  https://github.com/Extreme-Ending/solana-wash-trading-detection.git|\
  git@github.com:Extreme-Ending/solana-wash-trading-detection.git)
    ;;
  *) fail "origin does not match the approved GitHub repository." ;;
esac

gh auth status --hostname github.com >/dev/null
active_gcloud_account="$(gcloud auth list --filter=status:ACTIVE --limit=1 --format='value(account)')"
[[ -n "$active_gcloud_account" ]] || fail "no active gcloud account is available."

ci_success="$(gh run list --repo "$REPOSITORY" --workflow ci.yml --branch main \
  --limit 100 --json headSha,status,conclusion \
  | jq -r --arg sha "$REVISION" \
      'any(.[]; .headSha == $sha and .status == "completed" and .conclusion == "success")')"
[[ "$ci_success" == "true" ]] || fail "no successful completed CI run exists for the exact SHA."

printf 'Private Cloud Run pilot\n'
printf '  Project:    %s\n' "$PROJECT_ID"
printf '  Region:     %s\n' "$REGION"
printf '  Service:    %s\n' "$SERVICE"
printf '  Repository: %s\n' "$REPOSITORY"
printf '  Revision:   %s\n' "$REVISION"
printf '  Account:    %s\n' "$active_gcloud_account"
printf '\nThis may enable %s and will dispatch a private Cloud Run deployment.\n' "$REQUIRED_API"
printf 'It will not make the service public or enable experimental scoring.\n'
printf 'Type PRIVATE-PILOT/%s to continue: ' "$REVISION"
read -r confirmation
[[ "$confirmation" == "PRIVATE-PILOT/${REVISION}" ]] || fail "confirmation did not match; nothing was dispatched."

enabled_api="$(gcloud services list --enabled --project "$PROJECT_ID" \
  --filter="config.name=${REQUIRED_API}" --format='value(config.name)')"
if [[ "$enabled_api" != "$REQUIRED_API" ]]; then
  printf 'Enabling required API: %s\n' "$REQUIRED_API"
  gcloud services enable "$REQUIRED_API" --project "$PROJECT_ID" --quiet
fi
[[ "$(gcloud services list --enabled --project "$PROJECT_ID" \
  --filter="config.name=${REQUIRED_API}" --format='value(config.name)')" == "$REQUIRED_API" ]] || \
  fail "$REQUIRED_API is not enabled."

dispatch_started="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
gh workflow run "$WORKFLOW" --repo "$REPOSITORY" --ref main \
  -f "revision=${REVISION}" -f confirmation=PRIVATE-PILOT

run_id=""
for _attempt in {1..15}; do
  run_id="$(gh run list --repo "$REPOSITORY" --workflow "$WORKFLOW" --event workflow_dispatch \
    --branch main --limit 20 --json databaseId,headSha,createdAt \
    | jq -r --arg sha "$REVISION" --arg started "$dispatch_started" \
        '[.[] | select(.headSha == $sha and .createdAt >= $started)]
         | sort_by(.createdAt) | last | .databaseId // empty')"
  [[ -n "$run_id" ]] && break
  sleep 2
done
[[ -n "$run_id" ]] || fail "workflow was dispatched but its run ID was not found; inspect GitHub Actions."

run_url="https://github.com/${REPOSITORY}/actions/runs/${run_id}"
printf 'Monitoring workflow: %s\n' "$run_url"
if ! gh run watch "$run_id" --repo "$REPOSITORY" --exit-status; then
  printf '\nDeployment failed. Failed-step log follows; the GitHub secret value remains masked.\n' >&2
  gh run view "$run_id" --repo "$REPOSITORY" --log-failed >&2 || true
  fail "workflow failed; the run remains available at ${run_url}."
fi

service_json="$(gcloud run services describe "$SERVICE" --project "$PROJECT_ID" \
  --region "$REGION" --format=json)"
service_url="$(jq -r '.status.url // empty' <<<"$service_json")"
service_account="$(jq -r '.spec.template.spec.serviceAccountName // empty' <<<"$service_json")"
image="$(jq -r '.spec.template.spec.containers[0].image // empty' <<<"$service_json")"
scoring_enabled="$(jq -r \
  '[.spec.template.spec.containers[0].env[]? | select(.name == "SOLANA_RISK_ENABLE_EXPERIMENTAL_SCORING") | .value][0] // empty' \
  <<<"$service_json")"

[[ "$service_url" == https://* ]] || fail "the deployed service has no HTTPS URL."
[[ "$service_account" == "solana-wallet-risk-runtime@solana-wallet-risk.iam.gserviceaccount.com" ]] || \
  fail "the deployed service does not use the approved runtime identity."
[[ "$image" == *@sha256:* ]] || fail "the deployed image is not pinned by digest."
[[ "$scoring_enabled" == "false" ]] || fail "experimental scoring is not explicitly disabled."

policy_json="$(gcloud run services get-iam-policy "$SERVICE" --project "$PROJECT_ID" \
  --region "$REGION" --format=json)"
public_member="$(jq -r \
  '[.bindings[]?.members[]? | select(. == "allUsers" or . == "allAuthenticatedUsers")] | first // empty' \
  <<<"$policy_json")"
[[ -z "$public_member" ]] || fail "public Cloud Run principal detected: ${public_member}."

printf '\nPrivate pilot deployment verified.\n'
printf '  Workflow: %s\n' "$run_url"
printf '  Service:  %s\n' "$service_url"
printf '  Image:    %s\n' "$image"
printf '  Access:   private; no allUsers or allAuthenticatedUsers binding\n'
printf '  Scoring:  experimental model disabled\n'
