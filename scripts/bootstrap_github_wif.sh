#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-plan}"
EXECUTE="${2:-}"
PROJECT_ID="solana-wallet-risk"
PROJECT_NUMBER="441056127470"
REGION="africa-south1"
GITHUB_REPOSITORY="Extreme-Ending/solana-wash-trading-detection"
# GitHub has immutable OIDC subjects enabled for this repository. The account
# and repository numeric IDs keep this trust stable across future renames.
GITHUB_SUBJECT_PREFIX="repo:Extreme-Ending@296935112/solana-wash-trading-detection@1452262108"
POOL_ID="github-actions"
PROVIDER_ID="github"
PROVIDER_DISPLAY_NAME="GitHub main deployments"
ARTIFACT_REPOSITORY="solana-wallet-risk"
RUNTIME_ACCOUNT="solana-wallet-risk-runtime"
RUN_DEPLOY_ACCOUNT="github-cloud-run-deployer"
HOSTING_DEPLOY_ACCOUNT="github-firebase-deployer"

usage() {
  cat <<'EOF'
Usage: ./scripts/bootstrap_github_wif.sh [plan | apply --execute]

plan is read-only and prints the exact intended resources and role boundaries.
apply requires --execute, an interactive terminal, and an exact confirmation.
It is idempotent and targets only project solana-wallet-risk.

The script does not attach billing, create a budget, deploy Cloud Run, publish
Firebase Hosting, change public invocation, create keys, or change Git state.
EOF
}

run_or_print() {
  if [[ "$MODE" == "plan" ]]; then
    printf '  '
    printf '%q ' "$@"
    printf '\n'
  else
    "$@"
  fi
}

service_account_email() {
  printf '%s@%s.iam.gserviceaccount.com' "$1" "$PROJECT_ID"
}

service_account_exists() {
  gcloud iam service-accounts describe "$(service_account_email "$1")" \
    --project "$PROJECT_ID" --format='value(email)' >/dev/null 2>&1
}

ensure_service_account() {
  local account_id="$1" display_name="$2"
  if [[ "$MODE" == "apply" ]] && service_account_exists "$account_id"; then
    local disabled
    disabled="$(gcloud iam service-accounts describe "$(service_account_email "$account_id")" \
      --project "$PROJECT_ID" --format='value(disabled)')"
    # The API commonly omits the field when the account is enabled, so gcloud
    # returns an empty value rather than the literal "False".
    [[ -z "$disabled" || "${disabled,,}" == "false" ]] || {
      printf 'Existing service account is disabled: %s\n' "$(service_account_email "$account_id")" >&2
      exit 1
    }
    printf 'Service account already exists: %s\n' "$(service_account_email "$account_id")"
  else
    run_or_print gcloud iam service-accounts create "$account_id" \
      --project "$PROJECT_ID" --display-name "$display_name"
  fi
}

project_binding() {
  run_or_print gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member "$1" --role "$2" --condition=None --quiet
}

service_account_binding() {
  run_or_print gcloud iam service-accounts add-iam-policy-binding "$1" \
    --project "$PROJECT_ID" --member "$2" --role "$3" --condition=None --quiet
}

remove_service_account_binding_if_present() {
  local service_account="$1" member="$2" role="$3"
  if [[ "$MODE" == "plan" ]]; then
    run_or_print gcloud iam service-accounts remove-iam-policy-binding "$service_account" \
      --project "$PROJECT_ID" --member "$member" --role "$role" --condition=None --quiet
    return
  fi

  local policy_json
  policy_json="$(gcloud iam service-accounts get-iam-policy "$service_account" \
    --project "$PROJECT_ID" --format=json)"
  if jq -e --arg member "$member" --arg role "$role" \
    '.bindings[]? | select(.role == $role) | .members[]? | select(. == $member)' \
    <<<"$policy_json" >/dev/null; then
    gcloud iam service-accounts remove-iam-policy-binding "$service_account" \
      --project "$PROJECT_ID" --member "$member" --role "$role" --condition=None --quiet
  else
    printf 'Legacy WIF binding already absent: %s\n' "$service_account"
  fi
}

if [[ "$MODE" == "help" || "$MODE" == "-h" || "$MODE" == "--help" ]]; then
  usage
  exit 0
fi
if [[ "$MODE" != "plan" && "$MODE" != "apply" ]]; then
  usage >&2
  exit 2
fi
if [[ "$MODE" == "apply" ]]; then
  if [[ "$EXECUTE" != "--execute" ]]; then
    printf 'Refusing mutation: apply requires --execute.\n' >&2
    exit 2
  fi
  if [[ ! -t 0 || ! -t 1 ]]; then
    printf 'Bootstrap apply requires an interactive terminal.\n' >&2
    exit 2
  fi
  printf 'This will create narrowly scoped CI identities, WIF trust, required APIs, and one Docker repository.\n'
  printf 'It will not deploy or make Cloud Run public. Type solana-wallet-risk/phase12/bootstrap: '
  read -r confirmation
  if [[ "$confirmation" != "solana-wallet-risk/phase12/bootstrap" ]]; then
    printf 'Confirmation did not match; nothing was changed.\n' >&2
    exit 2
  fi
fi

command -v gcloud >/dev/null 2>&1 || { printf 'gcloud is required.\n' >&2; exit 1; }
if [[ "$MODE" == "apply" ]]; then
  command -v jq >/dev/null 2>&1 || { printf 'jq is required for existing-resource verification.\n' >&2; exit 1; }
fi
actual_number="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
[[ "$actual_number" == "$PROJECT_NUMBER" ]] || {
  printf 'Target project number mismatch; refusing to continue.\n' >&2
  exit 1
}
billing_enabled="$(gcloud billing projects describe "$PROJECT_ID" --format='value(billingEnabled)')"
[[ "$billing_enabled" == "True" ]] || {
  printf 'Billing is not enabled for %s; no bootstrap action is permitted.\n' "$PROJECT_ID" >&2
  exit 1
}

printf 'Phase 12 bootstrap %s\nProject: %s (%s)\nRepository: %s\n' \
  "$MODE" "$PROJECT_ID" "$PROJECT_NUMBER" "$GITHUB_REPOSITORY"

run_or_print gcloud services enable \
  artifactregistry.googleapis.com cloudbilling.googleapis.com firebasehosting.googleapis.com \
  iamcredentials.googleapis.com run.googleapis.com sts.googleapis.com \
  --project "$PROJECT_ID" --quiet

ensure_service_account "$RUNTIME_ACCOUNT" "Solana wallet risk Cloud Run runtime"
ensure_service_account "$RUN_DEPLOY_ACCOUNT" "GitHub private Cloud Run deployer"
ensure_service_account "$HOSTING_DEPLOY_ACCOUNT" "GitHub Firebase Hosting deployer"

if [[ "$MODE" == "apply" ]] && gcloud artifacts repositories describe "$ARTIFACT_REPOSITORY" \
  --project "$PROJECT_ID" --location "$REGION" >/dev/null 2>&1; then
  repository_format="$(gcloud artifacts repositories describe "$ARTIFACT_REPOSITORY" \
    --project "$PROJECT_ID" --location "$REGION" --format='value(format)')"
  [[ "$repository_format" == "DOCKER" ]] || {
    printf 'Existing Artifact Registry repository is not Docker format.\n' >&2
    exit 1
  }
  printf 'Artifact Registry repository already exists: %s\n' "$ARTIFACT_REPOSITORY"
else
  run_or_print gcloud artifacts repositories create "$ARTIFACT_REPOSITORY" \
    --project "$PROJECT_ID" --location "$REGION" --repository-format=docker \
    --description="Academic capstone API images" --quiet
fi

if [[ "$MODE" == "apply" ]] && gcloud iam workload-identity-pools describe "$POOL_ID" \
  --project "$PROJECT_ID" --location=global >/dev/null 2>&1; then
  pool_state="$(gcloud iam workload-identity-pools describe "$POOL_ID" \
    --project "$PROJECT_ID" --location=global --format='value(state)')"
  [[ "$pool_state" == "ACTIVE" ]] || {
    printf 'Existing Workload Identity Pool is not active.\n' >&2
    exit 1
  }
  printf 'Workload Identity Pool already exists: %s\n' "$POOL_ID"
else
  run_or_print gcloud iam workload-identity-pools create "$POOL_ID" \
    --project "$PROJECT_ID" --location=global \
    --display-name="GitHub Actions" --description="Repository-scoped deployment federation"
fi

if [[ "$MODE" == "apply" ]] && gcloud iam workload-identity-pools providers describe "$PROVIDER_ID" \
  --workload-identity-pool "$POOL_ID" --project "$PROJECT_ID" --location=global >/dev/null 2>&1; then
  provider_json="$(gcloud iam workload-identity-pools providers describe "$PROVIDER_ID" \
    --workload-identity-pool "$POOL_ID" --project "$PROJECT_ID" --location=global --format=json)"
  expected_condition="assertion.repository=='${GITHUB_REPOSITORY}' && assertion.ref=='refs/heads/main'"
  [[ "$(jq -r '.state' <<<"$provider_json")" == "ACTIVE" \
    && "$(jq -r '.oidc.issuerUri' <<<"$provider_json")" == "https://token.actions.githubusercontent.com" \
    && "$(jq -r '.attributeCondition' <<<"$provider_json")" == "$expected_condition" \
    && "$(jq -r '.attributeMapping["google.subject"]' <<<"$provider_json")" == "assertion.sub" \
    && "$(jq -r '.attributeMapping["attribute.repository"]' <<<"$provider_json")" == "assertion.repository" \
    && "$(jq -r '.attributeMapping["attribute.ref"]' <<<"$provider_json")" == "assertion.ref" ]] || {
    printf 'Existing OIDC provider does not match the exact reviewed trust contract.\n' >&2
    exit 1
  }
  printf 'OIDC provider already exists: %s\n' "$PROVIDER_ID"
else
  run_or_print gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_ID" \
    --workload-identity-pool "$POOL_ID" --project "$PROJECT_ID" --location=global \
    --display-name="$PROVIDER_DISPLAY_NAME" \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref" \
    --attribute-condition="assertion.repository=='${GITHUB_REPOSITORY}' && assertion.ref=='refs/heads/main'"
fi

run_deployer="serviceAccount:$(service_account_email "$RUN_DEPLOY_ACCOUNT")"
hosting_deployer="serviceAccount:$(service_account_email "$HOSTING_DEPLOY_ACCOUNT")"
runtime_email="$(service_account_email "$RUNTIME_ACCOUNT")"

project_binding "$run_deployer" roles/run.developer
project_binding "$run_deployer" roles/serviceusage.serviceUsageConsumer
project_binding "$hosting_deployer" roles/firebasehosting.admin
project_binding "$hosting_deployer" roles/serviceusage.apiKeysViewer
project_binding "$hosting_deployer" roles/serviceusage.serviceUsageConsumer
project_binding "serviceAccount:${runtime_email}" roles/firebaseauth.viewer

run_or_print gcloud artifacts repositories add-iam-policy-binding "$ARTIFACT_REPOSITORY" \
  --project "$PROJECT_ID" --location "$REGION" --member "$run_deployer" \
  --role roles/artifactregistry.writer --condition=None --quiet
service_account_binding "$runtime_email" "$run_deployer" roles/iam.serviceAccountUser

principal_prefix="principal://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/subject/${GITHUB_SUBJECT_PREFIX}:environment:"
service_account_binding "$(service_account_email "$RUN_DEPLOY_ACCOUNT")" \
  "${principal_prefix}private-pilot" roles/iam.workloadIdentityUser
service_account_binding "$(service_account_email "$HOSTING_DEPLOY_ACCOUNT")" \
  "${principal_prefix}hosting-preview" roles/iam.workloadIdentityUser
service_account_binding "$(service_account_email "$HOSTING_DEPLOY_ACCOUNT")" \
  "${principal_prefix}production" roles/iam.workloadIdentityUser

# Remove the name-only subjects used before immutable GitHub OIDC subjects were
# discovered. They cannot authenticate this repository and should not remain as
# misleading trust entries after the corrected bindings are installed.
legacy_principal_prefix="principal://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/subject/repo:${GITHUB_REPOSITORY}:environment:"
remove_service_account_binding_if_present "$(service_account_email "$RUN_DEPLOY_ACCOUNT")" \
  "${legacy_principal_prefix}private-pilot" roles/iam.workloadIdentityUser
remove_service_account_binding_if_present "$(service_account_email "$HOSTING_DEPLOY_ACCOUNT")" \
  "${legacy_principal_prefix}hosting-preview" roles/iam.workloadIdentityUser
remove_service_account_binding_if_present "$(service_account_email "$HOSTING_DEPLOY_ACCOUNT")" \
  "${legacy_principal_prefix}production" roles/iam.workloadIdentityUser

printf '\nNo service-account key is created. No Cloud Run or Firebase deployment is performed.\n'
printf 'Create and verify the USD 10 budget separately before setting COST_CONTROL_ATTESTATION.\n'
