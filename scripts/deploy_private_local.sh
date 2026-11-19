#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${DEPLOY_ENV_FILE:-${ROOT_DIR}/deployment/deployment.env.local}"

usage() {
  cat <<'EOF'
Usage: ./scripts/deploy_private_local.sh FULL_GIT_SHA --execute

Student-operated local deployment path for the private Cloud Run pilot. The
script validates the reviewed main commit and CI, builds and smoke-tests the
checksum-pinned experimental scoring image locally, publishes an immutable SHA
tag, resolves its digest, and deploys that exact digest.

Configuration is read from exported environment variables and, when present,
deployment/deployment.env.local (Git-ignored). Required private value:
  ALLOWED_USER_UIDS or SOLANA_RISK_ALLOWED_UIDS

This script does not change Git, IAM, billing, APIs, public access, Firebase
Hosting, or research claims. Scores remain experimental unsupervised outputs,
not fraud probabilities or confirmed wash-trading labels. Remote authenticated
HTTP acceptance is deliberately deferred.
EOF
}

fail() {
  printf 'local-private-deploy: %s\n' "$1" >&2
  exit 1
}

on_error() {
  local exit_code=$?
  printf '\nlocal-private-deploy: stopped after a command failed (exit %s).\n' "$exit_code" >&2
  printf 'An uploaded image or completed Cloud Run revision may remain; inspect the output and cloud state before retrying.\n' >&2
  exit "$exit_code"
}
trap on_error ERR

load_env_file() {
  local key line line_number=0 value
  [[ -f "$ENV_FILE" ]] || return 0
  while IFS= read -r line || [[ -n "$line" ]]; do
    line_number=$((line_number + 1))
    line="${line%$'\r'}"
    [[ -z "$line" || "$line" == \#* ]] && continue
    [[ "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*=.*$ ]] || \
      fail "invalid environment entry at ${ENV_FILE}:${line_number}."
    key="${line%%=*}"
    value="${line#*=}"
    printf -v "$key" '%s' "$value"
    export "${key?}"
  done < "$ENV_FILE"
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "$1 is required."
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

load_env_file

PROJECT_ID="${PROJECT_ID:-solana-wallet-risk}"
PROJECT_NUMBER="${PROJECT_NUMBER:-441056127470}"
REGION="${REGION:-africa-south1}"
ARTIFACT_REPOSITORY="${ARTIFACT_REPOSITORY:-solana-wallet-risk}"
IMAGE_NAME="${IMAGE_NAME:-solana-wallet-risk-api}"
CLOUD_RUN_SERVICE="${CLOUD_RUN_SERVICE:-solana-wallet-risk-api}"
RUNTIME_SERVICE_ACCOUNT="${RUNTIME_SERVICE_ACCOUNT:-solana-wallet-risk-runtime@solana-wallet-risk.iam.gserviceaccount.com}"
FIREBASE_PROJECT_ID="${FIREBASE_PROJECT_ID:-solana-wallet-risk}"
FIREBASE_ORIGINS="${FIREBASE_ORIGINS:-https://solana-wallet-risk.web.app,https://solana-wallet-risk.firebaseapp.com}"
ALLOWED_USER_UIDS="${ALLOWED_USER_UIDS:-${SOLANA_RISK_ALLOWED_UIDS:-}}"
MODEL_ARTIFACT="${ROOT_DIR}/artifacts/experimental/anomaly_models.joblib"
MODEL_MANIFEST="${ROOT_DIR}/artifacts/experimental/anomaly_models_manifest.json"
MODEL_ARTIFACT_SHA256="3e35561b0bf5db42c5b7146e7ff568e313be1beb1be724997356af45f5533035"
CONTAINER_MODEL_ARTIFACT="/app/artifacts/experimental/anomaly_models.joblib"
CONTAINER_MODEL_MANIFEST="/app/artifacts/experimental/anomaly_models_manifest.json"

[[ "$PROJECT_ID" == "solana-wallet-risk" ]] || fail "PROJECT_ID must equal solana-wallet-risk."
[[ "$PROJECT_NUMBER" == "441056127470" ]] || fail "PROJECT_NUMBER must equal 441056127470."
[[ "$REGION" == "africa-south1" ]] || fail "REGION must equal africa-south1."
[[ "$ARTIFACT_REPOSITORY" == "solana-wallet-risk" ]] || fail "unexpected Artifact Registry repository."
[[ "$IMAGE_NAME" == "solana-wallet-risk-api" ]] || fail "unexpected image name."
[[ "$CLOUD_RUN_SERVICE" == "solana-wallet-risk-api" ]] || fail "unexpected Cloud Run service."
[[ "$RUNTIME_SERVICE_ACCOUNT" == "solana-wallet-risk-runtime@solana-wallet-risk.iam.gserviceaccount.com" ]] || \
  fail "unexpected runtime service account."
[[ "$FIREBASE_PROJECT_ID" == "$PROJECT_ID" ]] || fail "Firebase and Google Cloud projects must match."
[[ "$FIREBASE_ORIGINS" == "https://solana-wallet-risk.web.app,https://solana-wallet-risk.firebaseapp.com" ]] || \
  fail "FIREBASE_ORIGINS must contain only the reviewed Hosting origins."
[[ "$ALLOWED_USER_UIDS" =~ ^[^,[:space:]]+(,[^,[:space:]]+)*$ ]] || \
  fail "set ALLOWED_USER_UIDS to the reviewed comma-separated Firebase UID allowlist."
for command in awk docker gcloud gh git jq python3 sha256sum; do
  require_command "$command"
done

[[ -f "$MODEL_ARTIFACT" && ! -L "$MODEL_ARTIFACT" ]] || \
  fail "trusted experimental model artifact is missing or is a symbolic link."
[[ -f "$MODEL_MANIFEST" && ! -L "$MODEL_MANIFEST" ]] || \
  fail "trusted experimental model manifest is missing or is a symbolic link."
actual_model_sha256="$(sha256sum "$MODEL_ARTIFACT" | awk '{print $1}')"
[[ "$actual_model_sha256" == "$MODEL_ARTIFACT_SHA256" ]] || \
  fail "experimental model checksum does not match the reviewed release artifact."
[[ "$(jq -r '.artifact_sha256 // empty' "$MODEL_MANIFEST")" == "$MODEL_ARTIFACT_SHA256" ]] || \
  fail "experimental model manifest checksum does not match the reviewed release artifact."

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

ci_success="$(gh run list --repo Extreme-Ending/solana-wash-trading-detection \
  --workflow ci.yml --branch main --limit 100 --json headSha,status,conclusion \
  | jq -r --arg sha "$REVISION" \
      'any(.[]; .headSha == $sha and .status == "completed" and .conclusion == "success")')"
[[ "$ci_success" == "true" ]] || fail "no successful completed CI run exists for the exact SHA."

active_account="$(gcloud auth list --filter=status:ACTIVE --limit=1 --format='value(account)')"
[[ -n "$active_account" ]] || fail "no active gcloud account is available."
[[ "$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')" == "$PROJECT_NUMBER" ]] || \
  fail "Google Cloud project number does not match."
[[ "$(gcloud billing projects describe "$PROJECT_ID" --format='value(billingEnabled)')" == "True" ]] || \
  fail "billing is not enabled for the selected project."

enabled_apis="$(gcloud services list --enabled --project "$PROJECT_ID" --format='value(config.name)')"
for api in artifactregistry.googleapis.com cloudbilling.googleapis.com iam.googleapis.com iamcredentials.googleapis.com run.googleapis.com sts.googleapis.com; do
  grep -Fxq "$api" <<< "$enabled_apis" || fail "required API is not enabled: ${api}."
done
[[ "$(gcloud artifacts repositories describe "$ARTIFACT_REPOSITORY" --project "$PROJECT_ID" \
  --location "$REGION" --format='value(format)')" == "DOCKER" ]] || fail "reviewed Docker repository is unavailable."
runtime_disabled="$(gcloud iam service-accounts describe "$RUNTIME_SERVICE_ACCOUNT" \
  --project "$PROJECT_ID" --format='value(disabled)')"
[[ -z "$runtime_disabled" || "${runtime_disabled,,}" == "false" ]] || fail "runtime service account is disabled."

image_root="${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPOSITORY}/${IMAGE_NAME}"
image_tag="${image_root}:${REVISION}"

printf 'Local private Cloud Run deployment\n'
printf '  Project:    %s (%s)\n' "$PROJECT_ID" "$PROJECT_NUMBER"
printf '  Region:     %s\n' "$REGION"
printf '  Service:    %s\n' "$CLOUD_RUN_SERVICE"
printf '  Revision:   %s\n' "$REVISION"
printf '  Image tag:  %s\n' "$image_tag"
printf '  Account:    %s\n' "$active_account"
printf '  Access:     private; Invoker IAM check retained\n'
printf '  Scoring:    checksum-pinned experimental Isolation Forest\n'
printf '  Claim:      anomaly score only; not a probability or fraud determination\n\n'
printf 'This builds, uploads and deploys. It does not run the currently blocked remote HTTP acceptance check.\n'
printf 'Type LOCAL-PRIVATE-DEPLOY/%s to continue: ' "$REVISION"
read -r confirmation
[[ "$confirmation" == "LOCAL-PRIVATE-DEPLOY/${REVISION}" ]] || fail "confirmation did not match; nothing was built or deployed."

printf '\n[1/5] Building and smoke-testing the production container...\n'
(cd "$ROOT_DIR" && python3 scripts/container_smoke_test.py \
  --dockerfile Dockerfile.scoring --expect-experimental-scoring \
  --image "${IMAGE_NAME}:${REVISION}" --host-port 18082 --custom-host-port 18083)

printf '\n[2/5] Publishing the immutable commit tag...\n'
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
docker tag "${IMAGE_NAME}:${REVISION}" "$image_tag"
docker push "$image_tag"

printf '\n[3/5] Resolving and validating the registry digest...\n'
digest="$(gcloud artifacts docker images describe "$image_tag" --format='value(image_summary.digest)')"
python3 "$ROOT_DIR/scripts/validate_release_config.py" --mode image-digest --image-digest "$digest"

printf '\n[4/5] Deploying the exact digest privately...\n'
gcloud run deploy "$CLOUD_RUN_SERVICE" \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --image "${image_root}@${digest}" \
  --platform managed \
  --no-allow-unauthenticated \
  --cpu-throttling \
  --min 0 --max 2 \
  --cpu 1 --memory 512Mi --concurrency 20 --timeout 30s --port 8080 \
  --service-account "$RUNTIME_SERVICE_ACCOUNT" \
  --labels "managed-by=local-script,git-sha=${REVISION}" \
  --set-env-vars "^@^SOLANA_RISK_ENVIRONMENT=production@SOLANA_RISK_ENABLE_EXPERIMENTAL_SCORING=true@SOLANA_RISK_ALLOW_PRODUCTION_EXPERIMENTAL_SCORING=true@SOLANA_RISK_EXPERIMENTAL_MODEL_ARTIFACT=${CONTAINER_MODEL_ARTIFACT}@SOLANA_RISK_EXPERIMENTAL_MODEL_MANIFEST=${CONTAINER_MODEL_MANIFEST}@SOLANA_RISK_EXPERIMENTAL_ARTIFACT_SHA256=${MODEL_ARTIFACT_SHA256}@SOLANA_RISK_CORS_ORIGINS=${FIREBASE_ORIGINS}@SOLANA_RISK_MAX_EVENTS=100@SOLANA_RISK_MAX_BATCH_WALLETS=20@SOLANA_RISK_MAX_BATCH_EVENTS=100@SOLANA_RISK_MAX_BATCH_EVENTS_PER_WALLET=50@SOLANA_RISK_MAX_REQUEST_BYTES=262144@SOLANA_RISK_FIREBASE_PROJECT_ID=${FIREBASE_PROJECT_ID}@SOLANA_RISK_ALLOWED_UIDS=${ALLOWED_USER_UIDS}@SOLANA_RISK_CHECK_REVOKED_TOKENS=true@SOLANA_RISK_RATE_LIMIT_REQUESTS=30@SOLANA_RISK_RATE_LIMIT_WINDOW_SECONDS=60"

printf '\n[5/5] Verifying control-plane state and private IAM...\n'
service_json="$(gcloud run services describe "$CLOUD_RUN_SERVICE" --project "$PROJECT_ID" \
  --region "$REGION" --format=json)"
deployed_image="$(jq -r '.spec.template.spec.containers[0].image // empty' <<< "$service_json")"
latest_revision="$(jq -r '.status.latestReadyRevisionName // empty' <<< "$service_json")"
service_url="$(jq -r '.status.url // empty' <<< "$service_json")"
ready_status="$(jq -r '[.status.conditions[]? | select(.type == "Ready") | .status][0] // empty' <<< "$service_json")"
runtime_identity="$(jq -r '.spec.template.spec.serviceAccountName // empty' <<< "$service_json")"
scoring_enabled="$(jq -r '[.spec.template.spec.containers[0].env[]? | select(.name == "SOLANA_RISK_ENABLE_EXPERIMENTAL_SCORING") | .value][0] // empty' <<< "$service_json")"
production_scoring_allowed="$(jq -r '[.spec.template.spec.containers[0].env[]? | select(.name == "SOLANA_RISK_ALLOW_PRODUCTION_EXPERIMENTAL_SCORING") | .value][0] // empty' <<< "$service_json")"
deployed_model_sha256="$(jq -r '[.spec.template.spec.containers[0].env[]? | select(.name == "SOLANA_RISK_EXPERIMENTAL_ARTIFACT_SHA256") | .value][0] // empty' <<< "$service_json")"
[[ "$deployed_image" == "${image_root}@${digest}" ]] || fail "deployed image does not match the resolved digest."
[[ "$ready_status" == "True" ]] || fail "Cloud Run does not report the service Ready."
[[ -n "$latest_revision" ]] || fail "Cloud Run did not report a ready revision."
[[ "$service_url" == https://*.run.app ]] || fail "Cloud Run did not report a service URL."
[[ "$runtime_identity" == "$RUNTIME_SERVICE_ACCOUNT" ]] || fail "runtime identity does not match."
[[ "$scoring_enabled" == "true" ]] || fail "experimental scoring is not enabled."
[[ "$production_scoring_allowed" == "true" ]] || fail "production experimental scoring opt-in is missing."
[[ "$deployed_model_sha256" == "$MODEL_ARTIFACT_SHA256" ]] || fail "deployed model checksum does not match."

service_policy="$(gcloud run services get-iam-policy "$CLOUD_RUN_SERVICE" --project "$PROJECT_ID" \
  --region "$REGION" --format=json)"
public_service_member="$(jq -r '[.bindings[]?.members[]? | select(. == "allUsers" or . == "allAuthenticatedUsers")] | first // empty' <<< "$service_policy")"
[[ -z "$public_service_member" ]] || fail "public service IAM member detected: ${public_service_member}."
project_policy="$(gcloud projects get-iam-policy "$PROJECT_ID" --format=json)"
public_project_invoker="$(jq -r '[.bindings[]? | select(.role == "roles/run.invoker") | .members[]? | select(. == "allUsers" or . == "allAuthenticatedUsers")] | first // empty' <<< "$project_policy")"
[[ -z "$public_project_invoker" ]] || fail "public project-level Cloud Run invoker detected: ${public_project_invoker}."

printf '\nPrivate Cloud Run deployment completed.\n'
printf '  Service URL: %s\n' "$service_url"
printf '  Revision:    %s\n' "$latest_revision"
printf '  Image:       %s@%s\n' "$image_root" "$digest"
printf '  Access:      private; no public Invoker binding detected\n'
printf '  Scoring:     checksum-pinned experimental anomaly scoring enabled\n'
printf '  HTTP check:  deferred; debug the existing run.app routing separately\n'
