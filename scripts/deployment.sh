#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ACTION="${1:-plan}"
EXECUTE=false

if [[ "${2:-}" == "--execute" ]]; then
  EXECUTE=true
elif [[ $# -gt 1 ]]; then
  printf 'Unknown argument: %s\n' "$2" >&2
  exit 2
fi

PROJECT_ID="${PROJECT_ID:-YOUR_GCP_PROJECT_ID}"
REGION="${REGION:-africa-south1}"
ARTIFACT_REPOSITORY="${ARTIFACT_REPOSITORY:-solana-wallet-risk}"
IMAGE_NAME="${IMAGE_NAME:-solana-wallet-risk-api}"
CLOUD_RUN_SERVICE="${CLOUD_RUN_SERVICE:-solana-wallet-risk-api}"
RUNTIME_SERVICE_ACCOUNT="${RUNTIME_SERVICE_ACCOUNT:-solana-wallet-risk-runtime@${PROJECT_ID}.iam.gserviceaccount.com}"
FIREBASE_ORIGINS="${FIREBASE_ORIGINS:-https://${PROJECT_ID}.web.app,https://${PROJECT_ID}.firebaseapp.com}"
CLOUD_RUN_URL="${CLOUD_RUN_URL:-}"
MAX_INSTANCES="${MAX_INSTANCES:-2}"
CPU="${CPU:-1}"
MEMORY="${MEMORY:-512Mi}"
CONCURRENCY="${CONCURRENCY:-20}"
TIMEOUT="${TIMEOUT:-30s}"
SMOKE_HOST_PORT="${SMOKE_HOST_PORT:-8080}"
SMOKE_CUSTOM_HOST_PORT="${SMOKE_CUSTOM_HOST_PORT:-18081}"
ROLLBACK_REVISION="${ROLLBACK_REVISION:-}"

usage() {
  cat <<'EOF'
Usage: ./scripts/deployment.sh ACTION [--execute]

Safe/read-only actions:
  plan              Print the selected configuration and future commands (default).
  prerequisites     Check required local tools and authenticated account state.
  verify-local      Run local Python/frontend/configuration checks.
  smoke             Test an existing private HTTPS service using an ID token from stdin.

Student-confirmed actions (require --execute and an interactive exact confirmation):
  build-image       Build and validate a commit-SHA-tagged image locally.
  tag-image         Tag an existing local image for Artifact Registry.
  push-image        Configure Docker authentication and publish the tagged image.
  deploy-cloud-run Deploy a private Cloud Run revision with conservative limits.
  build-frontend    Build and inspect the production Firebase bundle.
  deploy-firebase   Publish the already-built frontend bundle to Firebase Hosting.
  rollback          Route Cloud Run traffic to ROLLBACK_REVISION.
  cleanup           Delete the Cloud Run service/repository and disable Hosting.

Copy deployment/deployment.env.example to deployment/deployment.env.local, replace
every placeholder, then export its values before using a live action. The local file
is Git-ignored. This script never
creates a project, billing account, Artifact Registry repository, service account,
or IAM binding. It never enables unauthenticated Cloud Run invocation.
EOF
}

git_sha() {
  git -C "$ROOT_DIR" rev-parse --verify HEAD
}

image_uri() {
  printf '%s-docker.pkg.dev/%s/%s/%s:%s' \
    "$REGION" "$PROJECT_ID" "$ARTIFACT_REPOSITORY" "$IMAGE_NAME" "$(git_sha)"
}

print_command() {
  printf '  '
  printf '%q ' "$@"
  printf '\n'
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || {
    printf 'Missing required command: %s\n' "$1" >&2
    exit 1
  }
}

require_live_config() {
  local web_origin firebaseapp_origin extra_origin site_id
  if [[ "$PROJECT_ID" == "YOUR_GCP_PROJECT_ID" || "$PROJECT_ID" == *YOUR_* ]]; then
    printf 'PROJECT_ID still contains a placeholder; refusing a live action.\n' >&2
    exit 1
  fi
  if [[ ! "$PROJECT_ID" =~ ^[a-z][a-z0-9-]{4,28}[a-z0-9]$ ]]; then
    printf 'PROJECT_ID does not match the Google Cloud project-ID format.\n' >&2
    exit 1
  fi
  if [[ "$REGION" != "africa-south1" ]]; then
    printf 'REGION differs from the reviewed Phase 7A region (africa-south1).\n' >&2
    exit 1
  fi
  if [[ "$MAX_INSTANCES" != "2" || "$CPU" != "1" || "$MEMORY" != "512Mi" || "$CONCURRENCY" != "20" || "$TIMEOUT" != "30s" ]]; then
    printf 'Resource controls differ from the reviewed Phase 7A defaults; update the documented review before deployment.\n' >&2
    exit 1
  fi
  IFS=',' read -r web_origin firebaseapp_origin extra_origin <<< "$FIREBASE_ORIGINS"
  if [[ -n "$extra_origin" || ! "$web_origin" =~ ^https://([a-z0-9-]+)\.web\.app$ ]]; then
    printf 'FIREBASE_ORIGINS must begin with one exact HTTPS web.app origin.\n' >&2
    exit 1
  fi
  site_id="${BASH_REMATCH[1]}"
  if [[ "$firebaseapp_origin" != "https://${site_id}.firebaseapp.com" ]]; then
    printf 'FIREBASE_ORIGINS must contain matching web.app and firebaseapp.com site origins only.\n' >&2
    exit 1
  fi
  if [[ "$RUNTIME_SERVICE_ACCOUNT" != "solana-wallet-risk-runtime@${PROJECT_ID}.iam.gserviceaccount.com" ]]; then
    printf 'RUNTIME_SERVICE_ACCOUNT must be the reviewed user-managed identity in PROJECT_ID.\n' >&2
    exit 1
  fi
}

confirm_live() {
  local effect="$1"
  local expected="${PROJECT_ID}/${REGION}/${ACTION}"
  require_live_config
  if [[ "$EXECUTE" != true ]]; then
    printf 'DRY RUN ONLY: %s\n' "$effect"
    printf 'Re-run with --execute only after reviewing the command and documentation.\n'
    exit 0
  fi
  if [[ ! -t 0 || ! -t 1 ]]; then
    printf 'Live actions require an interactive terminal; refusing non-interactive execution.\n' >&2
    exit 1
  fi
  printf 'Project: %s\nRegion:  %s\nEffect:  %s\n' "$PROJECT_ID" "$REGION" "$effect"
  printf 'Type exactly %s to continue: ' "$expected"
  read -r confirmation
  if [[ "$confirmation" != "$expected" ]]; then
    printf 'Confirmation did not match. No live action was executed.\n' >&2
    exit 1
  fi
}

plan() {
  local sha uri
  sha="$(git_sha)"
  uri="$(image_uri)"
  printf 'Phase 7A deployment plan (commands are not executed)\n'
  printf 'Project:           %s\n' "$PROJECT_ID"
  printf 'Region:            %s\n' "$REGION"
  printf 'Commit SHA:        %s\n' "$sha"
  printf 'Image:             %s\n' "$uri"
  printf 'Cloud Run service: %s (private; min 0, max %s)\n' "$CLOUD_RUN_SERVICE" "$MAX_INSTANCES"
  printf 'Firebase output:   frontend/dist\n\n'
  printf 'Future image build:\n'
  print_command docker build --tag "${IMAGE_NAME}:${sha}" "$ROOT_DIR"
  printf 'Future registry tag/push:\n'
  print_command docker tag "${IMAGE_NAME}:${sha}" "$uri"
  print_command docker push "$uri"
  printf 'Future private Cloud Run deployment:\n'
  print_command gcloud run deploy "$CLOUD_RUN_SERVICE" --project "$PROJECT_ID" --region "$REGION" --image "$uri" --platform managed --no-allow-unauthenticated --cpu-throttling --min 0 --max "$MAX_INSTANCES" --cpu "$CPU" --memory "$MEMORY" --concurrency "$CONCURRENCY" --timeout "$TIMEOUT" --port 8080 --service-account "$RUNTIME_SERVICE_ACCOUNT" --set-env-vars "^@^SOLANA_RISK_ENVIRONMENT=production@SOLANA_RISK_CORS_ORIGINS=${FIREBASE_ORIGINS}@SOLANA_RISK_MAX_EVENTS=100@SOLANA_RISK_MAX_REQUEST_BYTES=262144"
  printf 'Future frontend build/deploy (CLOUD_RUN_URL must be the exact HTTPS service origin):\n'
  print_command env "VITE_API_BASE_URL=${CLOUD_RUN_URL:-https://YOUR_CLOUD_RUN_SERVICE_HOST}" npm --prefix frontend run build
  print_command firebase deploy --only hosting --project "$PROJECT_ID"
}

case "$ACTION" in
  help|-h|--help)
    usage
    ;;
  plan)
    plan
    ;;
  prerequisites)
    prerequisite_failed=false
    for command_name in git docker python3 npm gcloud firebase; do
      if command -v "$command_name" >/dev/null 2>&1; then
        printf '%-10s %s\n' "$command_name" "$(command -v "$command_name")"
      else
        printf '%-10s MISSING\n' "$command_name"
        prerequisite_failed=true
      fi
    done
    printf '\nDocker daemon check:\n'
    if command -v docker >/dev/null 2>&1; then
      if docker info >/dev/null 2>&1; then
        printf 'Docker daemon is reachable.\n'
      else
        printf 'Docker CLI is installed but the daemon is not reachable.\n' >&2
        prerequisite_failed=true
      fi
    fi
    printf '\nAuthenticated Google Cloud accounts (read-only check):\n'
    if command -v gcloud >/dev/null 2>&1; then
      if ! active_accounts="$(gcloud auth list --filter=status:ACTIVE --format='value(account)')"; then
        printf 'gcloud is installed but unusable; repair it before any cloud action.\n' >&2
        prerequisite_failed=true
      elif [[ -z "$active_accounts" ]]; then
        printf 'No active gcloud account is configured.\n' >&2
        prerequisite_failed=true
      else
        printf '%s\n' "$active_accounts"
      fi
    fi
    printf '\nAuthenticated Firebase accounts (read-only check):\n'
    if command -v firebase >/dev/null 2>&1; then
      if ! firebase login:list; then
        printf 'Firebase CLI is installed but no usable login could be verified.\n' >&2
        prerequisite_failed=true
      fi
    fi
    printf 'No cloud resources were created or changed.\n'
    if [[ "$prerequisite_failed" == true ]]; then
      exit 1
    fi
    ;;
  verify-local)
    require_command python3
    require_command npm
    require_command docker
    (cd "$ROOT_DIR" && python3 -m pytest -q)
    npm --prefix "$ROOT_DIR/frontend" ci
    npm --prefix "$ROOT_DIR/frontend" run typecheck
    npm --prefix "$ROOT_DIR/frontend" test -- --run
    (cd "$ROOT_DIR" && docker compose config --quiet)
    ;;
  build-image)
    confirm_live "build a local Docker image and run the existing container smoke suite; no cloud upload"
    require_command docker
    (cd "$ROOT_DIR" && python3 scripts/container_smoke_test.py \
      --image "${IMAGE_NAME}:$(git_sha)" \
      --host-port "$SMOKE_HOST_PORT" \
      --custom-host-port "$SMOKE_CUSTOM_HOST_PORT")
    ;;
  tag-image)
    confirm_live "add the Artifact Registry tag to the existing local commit-SHA image; no upload"
    require_command docker
    docker tag "${IMAGE_NAME}:$(git_sha)" "$(image_uri)"
    ;;
  push-image)
    confirm_live "configure Docker for ${REGION}-docker.pkg.dev and upload image $(image_uri); registry storage may incur charges"
    require_command gcloud
    require_command docker
    gcloud auth configure-docker "${REGION}-docker.pkg.dev"
    docker push "$(image_uri)"
    ;;
  deploy-cloud-run)
    confirm_live "create or update a private Cloud Run service revision; usage may incur charges"
    require_command gcloud
    gcloud run deploy "$CLOUD_RUN_SERVICE" \
      --project "$PROJECT_ID" \
      --region "$REGION" \
      --image "$(image_uri)" \
      --platform managed \
      --no-allow-unauthenticated \
      --cpu-throttling \
      --min 0 \
      --max "$MAX_INSTANCES" \
      --cpu "$CPU" \
      --memory "$MEMORY" \
      --concurrency "$CONCURRENCY" \
      --timeout "$TIMEOUT" \
      --port 8080 \
      --service-account "$RUNTIME_SERVICE_ACCOUNT" \
      --set-env-vars "^@^SOLANA_RISK_ENVIRONMENT=production@SOLANA_RISK_CORS_ORIGINS=${FIREBASE_ORIGINS}@SOLANA_RISK_MAX_EVENTS=100@SOLANA_RISK_MAX_REQUEST_BYTES=262144"
    ;;
  build-frontend)
    confirm_live "perform a clean production frontend build against CLOUD_RUN_URL and scan the static bundle; no upload"
    require_command npm
    require_command python3
    if [[ ! "$CLOUD_RUN_URL" =~ ^https://[a-z0-9][a-z0-9.-]*[a-z0-9]/?$ ]]; then
      printf 'CLOUD_RUN_URL must be an HTTPS origin with no path.\n' >&2
      exit 1
    fi
    npm --prefix "$ROOT_DIR/frontend" ci
    VITE_API_BASE_URL="${CLOUD_RUN_URL%/}" npm --prefix "$ROOT_DIR/frontend" run build
    python3 "$ROOT_DIR/scripts/validate_deployment_bundle.py" "$ROOT_DIR/frontend/dist"
    ;;
  deploy-firebase)
    confirm_live "publish the existing frontend/dist bundle to Firebase Hosting; hosting usage may incur charges"
    require_command firebase
    python3 "$ROOT_DIR/scripts/validate_deployment_bundle.py" "$ROOT_DIR/frontend/dist"
    (cd "$ROOT_DIR" && firebase deploy --only hosting --project "$PROJECT_ID")
    ;;
  smoke)
    require_command python3
    if [[ ! "$CLOUD_RUN_URL" =~ ^https://[a-z0-9][a-z0-9.-]*[a-z0-9]/?$ ]]; then
      printf 'Set CLOUD_RUN_URL to the exact HTTPS Cloud Run origin.\n' >&2
      exit 1
    fi
    printf 'Paste a short-lived Cloud Run identity token, then press Enter. It will not be displayed or stored.\n' >&2
    python3 "$ROOT_DIR/scripts/deployment_smoke_test.py" --base-url "${CLOUD_RUN_URL%/}" --token-stdin
    ;;
  rollback)
    confirm_live "route 100% of service traffic to the named prior revision; no history is rewritten"
    require_command gcloud
    if [[ -z "$ROLLBACK_REVISION" || ! "$ROLLBACK_REVISION" =~ ^[a-z0-9-]+$ ]]; then
      printf 'Set ROLLBACK_REVISION to a reviewed Cloud Run revision name.\n' >&2
      exit 1
    fi
    gcloud run services update-traffic "$CLOUD_RUN_SERVICE" --project "$PROJECT_ID" --region "$REGION" --to-revisions "${ROLLBACK_REVISION}=100"
    ;;
  cleanup)
    confirm_live "delete the Cloud Run service and Artifact Registry repository, then disable Firebase Hosting; these resources are not automatically recoverable"
    require_command gcloud
    require_command firebase
    gcloud run services delete "$CLOUD_RUN_SERVICE" --project "$PROJECT_ID" --region "$REGION"
    gcloud artifacts repositories delete "$ARTIFACT_REPOSITORY" --project "$PROJECT_ID" --location "$REGION"
    firebase hosting:disable --project "$PROJECT_ID"
    ;;
  *)
    printf 'Unknown action: %s\n\n' "$ACTION" >&2
    usage >&2
    exit 2
    ;;
esac
