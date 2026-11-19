"""Phase 12 CI/CD contracts and fail-closed deployment-input tests."""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str) -> ModuleType:
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _common() -> dict[str, str]:
    return {
        "GITHUB_REPOSITORY": "Extreme-Ending/solana-wash-trading-detection",
        "GITHUB_REF": "refs/heads/main",
        "GITHUB_SHA": "a" * 40,
        "GCP_PROJECT_ID": "solana-wallet-risk",
        "GCP_PROJECT_NUMBER": "441056127470",
        "GCP_WORKLOAD_IDENTITY_PROVIDER": (
            "projects/441056127470/locations/global/workloadIdentityPools/"
            "github-actions/providers/github"
        ),
        "COST_CONTROL_ATTESTATION": "USD10-50-80-100-REVIEWED",
    }


def _cloud() -> dict[str, str]:
    return {
        **_common(),
        "GCP_REGION": "africa-south1",
        "ARTIFACT_REGISTRY_REPOSITORY": "solana-wallet-risk",
        "CLOUD_RUN_SERVICE": "solana-wallet-risk-api",
        "FIREBASE_PROJECT_ID": "solana-wallet-risk",
        "FIREBASE_HOSTING_SITE": "solana-wallet-risk",
        "GCP_RUNTIME_SERVICE_ACCOUNT": (
            "solana-wallet-risk-runtime@solana-wallet-risk.iam.gserviceaccount.com"
        ),
        "GCP_DEPLOY_SERVICE_ACCOUNT": (
            "github-cloud-run-deployer@solana-wallet-risk.iam.gserviceaccount.com"
        ),
        "SOLANA_RISK_ALLOWED_UIDS": "approved-user-uid",
        "SOLANA_RISK_ENABLE_EXPERIMENTAL_SCORING": "false",
        "MAX_INSTANCES": "2",
    }


def _firebase() -> dict[str, str]:
    return {
        **_common(),
        "FIREBASE_PROJECT_ID": "solana-wallet-risk",
        "FIREBASE_HOSTING_SITE": "solana-wallet-risk",
        "FIREBASE_DEPLOY_SERVICE_ACCOUNT": (
            "github-firebase-deployer@solana-wallet-risk.iam.gserviceaccount.com"
        ),
        "VITE_API_BASE_URL": "https://solana-wallet-risk-api-xyz.a.run.app",
        "VITE_FIREBASE_API_KEY": "AIza" + "A" * 35,
        "VITE_FIREBASE_AUTH_DOMAIN": "solana-wallet-risk.firebaseapp.com",
        "VITE_FIREBASE_PROJECT_ID": "solana-wallet-risk",
        "VITE_FIREBASE_APP_ID": "1:441056127470:web:b5b19864319734869ac6ff",
    }


def test_workflow_security_validator_passes() -> None:
    _load("validate_workflows.py").validate()


def test_workflows_use_the_node_version_required_by_locked_dependencies() -> None:
    package = json.loads((ROOT / "frontend" / "package.json").read_text(encoding="utf-8"))
    lock = json.loads((ROOT / "frontend" / "package-lock.json").read_text(encoding="utf-8"))
    expected_engine = ">=22.22.2"
    assert package["engines"]["node"] == expected_engine
    assert lock["packages"][""]["engines"]["node"] == expected_engine
    assert lock["packages"]["node_modules/undici"]["engines"]["node"] == ">=22.19.0"
    assert lock["packages"]["node_modules/jsdom"]["engines"]["node"] == (
        "^22.22.2 || ^24.15.0 || >=26.0.0"
    )
    for workflow in ("ci.yml", "deploy-firebase.yml"):
        text = (ROOT / ".github" / "workflows" / workflow).read_text(encoding="utf-8")
        assert "node-version: 22.22.2" in text


def test_cloud_workflow_accepts_omitted_false_for_enabled_runtime_account() -> None:
    workflow = (ROOT / ".github" / "workflows" / "deploy-cloud-run.yml").read_text(
        encoding="utf-8"
    )
    assert '[[ -z "$runtime_disabled" || "${runtime_disabled,,}" == "false" ]]' in workflow
    assert "deploy_disabled=" not in workflow
    assert "--format='value(disabled)' | grep -Fxq False" not in workflow


def test_cloud_workflow_mints_audience_bound_acceptance_token_with_wif() -> None:
    workflow = (ROOT / ".github" / "workflows" / "deploy-cloud-run.yml").read_text(
        encoding="utf-8"
    )
    assert "id: deploy" in workflow
    assert "service_url=%s" in workflow
    assert "id: acceptance-auth" in workflow
    assert "token_format: id_token" in workflow
    assert "id_token_audience: ${{ steps.deploy.outputs.service_url }}" in workflow
    assert "id_token_include_email: true" in workflow
    assert "CLOUD_RUN_ID_TOKEN: ${{ steps.acceptance-auth.outputs.id_token }}" in workflow
    assert "create_credentials_file: false" in workflow
    assert "export_environment_variables: false" in workflow
    assert "gcloud auth print-identity-token" not in workflow
    assert '"404"' in workflow


def test_release_contract_accepts_only_the_reviewed_targets() -> None:
    validator = _load("validate_release_config.py")
    validator.validate_cloud_run(_cloud())
    validator.validate_firebase(_firebase())
    validator.validate_digest("sha256:" + "b" * 64)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("GCP_PROJECT_ID", "seotranslate-507816"),
        ("GITHUB_REF", "refs/heads/feature"),
        ("GITHUB_SHA", "main"),
        ("MAX_INSTANCES", "20"),
        ("SOLANA_RISK_ENABLE_EXPERIMENTAL_SCORING", "true"),
        ("SOLANA_RISK_ALLOWED_UIDS", "uid one"),
        ("COST_CONTROL_ATTESTATION", "not-reviewed"),
    ),
)
def test_cloud_release_rejects_unsafe_or_missing_configuration(field: str, value: str) -> None:
    validator = _load("validate_release_config.py")
    values = _cloud()
    values[field] = value
    with pytest.raises(validator.ReleaseConfigurationError):
        validator.validate_cloud_run(values)


def test_cloud_release_rejects_runtime_identity_as_deployer() -> None:
    validator = _load("validate_release_config.py")
    values = _cloud()
    values["GCP_DEPLOY_SERVICE_ACCOUNT"] = values["GCP_RUNTIME_SERVICE_ACCOUNT"]
    with pytest.raises(validator.ReleaseConfigurationError, match="GCP_DEPLOY_SERVICE_ACCOUNT"):
        validator.validate_cloud_run(values)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("VITE_API_BASE_URL", "http://insecure.example.com"),
        ("VITE_API_BASE_URL", "https://example.com/path"),
        ("VITE_FIREBASE_API_KEY", "YOUR_FIREBASE_WEB_API_KEY"),
        ("VITE_FIREBASE_PROJECT_ID", "other-project"),
        ("VITE_FIREBASE_AUTH_DOMAIN", "attacker.example.com"),
        ("FIREBASE_DEPLOY_SERVICE_ACCOUNT", ""),
    ),
)
def test_firebase_release_rejects_invalid_build_or_identity_values(field: str, value: str) -> None:
    validator = _load("validate_release_config.py")
    values = _firebase()
    values[field] = value
    with pytest.raises(validator.ReleaseConfigurationError):
        validator.validate_firebase(values)


@pytest.mark.parametrize("digest", ("", "latest", "sha256:abc", "b" * 64))
def test_image_digest_must_be_an_immutable_sha256(digest: str) -> None:
    validator = _load("validate_release_config.py")
    with pytest.raises(validator.ReleaseConfigurationError):
        validator.validate_digest(digest)


def test_bootstrap_is_plan_only_by_default_and_has_no_key_or_public_access_path() -> None:
    script = (ROOT / "scripts" / "bootstrap_github_wif.sh").read_text(encoding="utf-8")
    assert script.startswith("#!/usr/bin/env bash\nset -euo pipefail\n")
    assert 'MODE="${1:-plan}"' in script
    assert "apply requires --execute" in script
    assert "service-account keys create" not in script
    assert "--allow-unauthenticated" not in script
    assert "--no-invoker-iam-check" not in script
    assert "allUsers" not in script
    assert "roles/run.invoker" not in script
    assert "roles/serviceusage.apiKeysViewer" in script
    assert "roles/apikeys.viewer" not in script
    assert "cloudbilling.googleapis.com" in script
    assert "iam.googleapis.com" in script
    cloud_workflow = (ROOT / ".github" / "workflows" / "deploy-cloud-run.yml").read_text(
        encoding="utf-8"
    )
    assert "cloudbilling.googleapis.com" in cloud_workflow
    assert "iam.googleapis.com" in cloud_workflow
    assert '[[ -z "$disabled" || "${disabled,,}" == "false" ]]' in script
    assert (
        'GITHUB_SUBJECT_PREFIX="repo:Extreme-Ending@296935112/'
        'solana-wash-trading-detection@1452262108"' in script
    )
    assert "subject/${GITHUB_SUBJECT_PREFIX}:environment:" in script
    assert "principalSet://" not in script
    assert "remove_service_account_binding_if_present" in script
    assert "Editor" not in script and "Owner" not in script
    display_name = re.search(r'^PROVIDER_DISPLAY_NAME="([^"]+)"$', script, re.MULTILINE)
    assert display_name is not None
    assert len(display_name.group(1)) <= 32


def test_private_pilot_operator_script_is_guarded_and_private() -> None:
    script = (ROOT / "scripts" / "run_private_pilot.sh").read_text(encoding="utf-8")
    assert script.startswith("#!/usr/bin/env bash\nset -euo pipefail\n")
    assert '[[ "$EXECUTE" == "--execute"' in script
    assert "FULL_GIT_SHA must equal local HEAD" in script
    assert "no successful completed CI run exists for the exact SHA" in script
    assert "confirmation=PRIVATE-PILOT" in script
    assert "gh run watch" in script
    assert "allUsers" in script and "allAuthenticatedUsers" in script
    assert "SOLANA_RISK_ENABLE_EXPERIMENTAL_SCORING" in script
    assert "--allow-unauthenticated" not in script
    assert "--no-invoker-iam-check" not in script
    for forbidden in (
        "git add",
        "git commit",
        "git push",
        "git reset",
        "git rebase",
        "git checkout",
        "git switch",
    ):
        assert forbidden not in script


def test_local_private_deployment_is_guarded_digest_pinned_and_defers_http() -> None:
    script = (ROOT / "scripts" / "deploy_private_local.sh").read_text(encoding="utf-8")
    assert script.startswith("#!/usr/bin/env bash\nset -euo pipefail\n")
    assert '[[ "$EXECUTE" == "--execute"' in script
    assert "FULL_GIT_SHA must equal local HEAD" in script
    assert "no successful completed CI run exists for the exact SHA" in script
    assert "LOCAL-PRIVATE-DEPLOY/${REVISION}" in script
    assert 'python3 scripts/container_smoke_test.py' in script
    assert "--dockerfile Dockerfile.scoring --expect-experimental-scoring" in script
    assert 'python3 "$ROOT_DIR/scripts/validate_release_config.py" --mode image-digest' in script
    assert '--image "${image_root}@${digest}"' in script
    assert "--no-allow-unauthenticated" in script
    assert "--no-invoker-iam-check" not in script
    assert "allUsers" in script and "allAuthenticatedUsers" in script
    assert "SOLANA_RISK_ENABLE_EXPERIMENTAL_SCORING=true" in script
    assert "SOLANA_RISK_ALLOW_PRODUCTION_EXPERIMENTAL_SCORING=true" in script
    assert "SOLANA_RISK_EXPERIMENTAL_ARTIFACT_SHA256" in script
    assert "3e35561b0bf5db42c5b7146e7ff568e313be1beb1be724997356af45f5533035" in script
    assert "HTTP check:  deferred" in script
    assert "curl " not in script
    for forbidden in (
        "git add",
        "git commit",
        "git push",
        "git reset",
        "git rebase",
        "git checkout",
        "git switch",
    ):
        assert forbidden not in script


def test_full_stack_deployment_preserves_app_auth_with_public_platform_access() -> None:
    script = (ROOT / "scripts" / "deploy_full_stack.sh").read_text(encoding="utf-8")
    assert script.startswith("#!/usr/bin/env bash\nset -euo pipefail\n")
    assert '[[ "$EXECUTE" == "--execute"' in script
    assert "FULL_GIT_SHA must equal local HEAD" in script
    assert "no successful completed CI run exists for the exact SHA" in script
    assert 'ENV_FILE="${DEPLOY_ENV_FILE:-${ROOT_DIR}/.env}"' in script
    assert "check-ignore" in script
    assert '"$ROOT_DIR/scripts/deploy_private_local.sh" "$REVISION" --execute' in script
    assert 'python3 "$ROOT_DIR/scripts/validate_release_config.py"' in script
    assert 'gh workflow run "$FIREBASE_WORKFLOW"' in script
    assert "HOSTING-PREVIEW" in script and "HOSTING-LIVE" in script
    assert "gh run watch" in script
    assert "VITE_API_BASE_URL does not match" in script
    assert "PUBLIC-PLATFORM/${REVISION}" in script
    assert '"${service_url}/readyz"' in script
    assert 'methodology_status == "experimental_unsupervised_research_only"' in script
    assert "--expect-experimental-scoring" in script
    assert "an unauthenticated protected request returned HTTP" in script
    assert "--allow-unauthenticated" not in script
    assert "--no-invoker-iam-check" in script
    assert "allUsers" not in script
    for forbidden in (
        "git add",
        "git commit",
        "git push",
        "git reset",
        "git rebase",
        "git checkout",
        "git switch",
    ):
        assert forbidden not in script
