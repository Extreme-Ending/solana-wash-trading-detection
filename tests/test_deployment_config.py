"""Phase 7A deployment contracts using only local files and synthetic fixtures."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
from pathlib import Path
from types import ModuleType

import pytest

from solana_risk.api.config import ConfigurationError, Settings

ROOT = Path(__file__).resolve().parents[1]


def _load_bundle_validator() -> ModuleType:
    path = ROOT / "scripts" / "validate_deployment_bundle.py"
    spec = importlib.util.spec_from_file_location("validate_deployment_bundle", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_firebase_hosts_actual_vite_spa_with_cache_and_security_headers() -> None:
    config = json.loads((ROOT / "firebase.json").read_text(encoding="utf-8"))
    assert set(config) == {"hosting"}
    hosting = config["hosting"]
    assert hosting["public"] == "frontend/dist"
    assert hosting["rewrites"] == [{"source": "**", "destination": "/index.html"}]
    assert hosting["trailingSlash"] is False
    headers = {entry["source"]: entry["headers"] for entry in hosting["headers"]}
    assert {item["key"]: item["value"] for item in headers["/index.html"]}["Cache-Control"] == "no-cache, no-store, must-revalidate"
    assert {item["key"]: item["value"] for item in headers["/assets/**"]}["Cache-Control"] == "public, max-age=31536000, immutable"
    security = {item["key"]: item["value"] for item in headers["**"]}
    assert security["X-Content-Type-Options"] == "nosniff"
    assert security["X-Frame-Options"] == "DENY"
    assert security["Referrer-Policy"] == "strict-origin-when-cross-origin"
    serialized = json.dumps(config).casefold()
    assert all(term not in serialized for term in ('"run"', "firestore", "authentication", "functions"))


def test_project_and_production_environment_examples_are_placeholders_only() -> None:
    firebase_example = json.loads((ROOT / ".firebaserc.example").read_text(encoding="utf-8"))
    assert firebase_example == {"projects": {"default": "YOUR_GCP_PROJECT_ID"}}
    frontend_example = (ROOT / "frontend" / ".env.production.example").read_text(encoding="utf-8")
    assignments = [
        line for line in frontend_example.splitlines() if line and not line.startswith("#")
    ]
    assert assignments == [
        "VITE_API_BASE_URL=https://YOUR_CLOUD_RUN_SERVICE_HOST",
        "VITE_FIREBASE_API_KEY=YOUR_FIREBASE_WEB_API_KEY",
        "VITE_FIREBASE_AUTH_DOMAIN=YOUR_GCP_PROJECT_ID.firebaseapp.com",
        "VITE_FIREBASE_PROJECT_ID=YOUR_GCP_PROJECT_ID",
        "VITE_FIREBASE_APP_ID=YOUR_FIREBASE_WEB_APP_ID",
    ]
    assert all(term not in frontend_example.casefold() for term in ("private_key", "password"))
    ignore_rules = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "/deployment/deployment.env.local" in ignore_rules


def test_cloud_defaults_are_private_bounded_and_exact_origin_only() -> None:
    values: dict[str, str] = {}
    for line in (ROOT / "deployment" / "deployment.env.example").read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            key, value = line.split("=", maxsplit=1)
            values[key] = value
    assert values["REGION"] == "africa-south1"
    assert values["MAX_INSTANCES"] == "2"
    assert values["CPU"] == "1"
    assert values["MEMORY"] == "512Mi"
    assert values["CONCURRENCY"] == "20"
    assert values["TIMEOUT"] == "30s"
    assert values["FIREBASE_ORIGINS"] == "https://YOUR_GCP_PROJECT_ID.web.app,https://YOUR_GCP_PROJECT_ID.firebaseapp.com"
    assert "YOUR_GCP_PROJECT_ID" in values["PROJECT_ID"]
    assert values["FIREBASE_PROJECT_ID"] == "YOUR_GCP_PROJECT_ID"
    assert values["ALLOWED_USER_UIDS"] == "YOUR_APPROVED_FIREBASE_UIDS"


def test_api_accepts_exact_firebase_origins_and_rejects_wildcard() -> None:
    settings = Settings.from_env(
        {
            "SOLANA_RISK_CORS_ORIGINS": (
                "https://project-id.web.app,https://project-id.firebaseapp.com"
            )
        }
    )
    assert settings.cors_origins == (
        "https://project-id.web.app",
        "https://project-id.firebaseapp.com",
    )
    with pytest.raises(ConfigurationError, match="Wildcard"):
        Settings.from_env({"SOLANA_RISK_CORS_ORIGINS": "*"})


def test_deployment_script_is_dry_run_by_default_and_never_enables_public_access() -> None:
    script_path = ROOT / "scripts" / "deployment.sh"
    script = script_path.read_text(encoding="utf-8")
    assert script.startswith("#!/usr/bin/env bash\nset -euo pipefail\n")
    assert "ACTION=\"${1:-plan}\"" in script
    assert "--no-allow-unauthenticated" in script
    assert not re.search(r"(?<!no-)--allow-unauthenticated", script)
    for control in (
        "--cpu-throttling",
        "--min 0",
        "--max \"$MAX_INSTANCES\"",
        "--port 8080",
        "SOLANA_RISK_MAX_EVENTS=100",
        "SOLANA_RISK_MAX_REQUEST_BYTES=262144",
        "SOLANA_RISK_FIREBASE_PROJECT_ID=",
        "SOLANA_RISK_ALLOWED_UIDS=",
    ):
        assert control in script
    assert "Live actions require an interactive terminal" in script
    assert "Type exactly" in script
    assert all(command not in script for command in ("git add", "git commit", "git push", "git reset", "git rebase"))

    env = {**os.environ, "PROJECT_ID": "YOUR_GCP_PROJECT_ID"}
    result = subprocess.run(
        ["bash", str(script_path), "plan"],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "commands are not executed" in result.stdout
    assert "--no-allow-unauthenticated" in result.stdout


def test_live_action_with_placeholder_stops_before_any_command() -> None:
    result = subprocess.run(
        ["bash", str(ROOT / "scripts" / "deployment.sh"), "push-image", "--execute"],
        cwd=ROOT,
        env={**os.environ, "PROJECT_ID": "YOUR_GCP_PROJECT_ID"},
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "placeholder" in result.stderr


def test_mutating_action_without_execute_only_prints_dry_run() -> None:
    env = {key: value for key, value in os.environ.items() if key not in {
        "RUNTIME_SERVICE_ACCOUNT",
        "FIREBASE_ORIGINS",
    }}
    env["PROJECT_ID"] = "example-project-123"
    env.update({
        "FIREBASE_PROJECT_ID": "example-project-123",
        "ALLOWED_USER_UIDS": "approved-user-uid",
        "FIREBASE_WEB_API_KEY": "public-web-api-key",
        "FIREBASE_AUTH_DOMAIN": "example-project-123.firebaseapp.com",
        "FIREBASE_APP_ID": "1:123:web:abc",
    })
    result = subprocess.run(
        ["bash", str(ROOT / "scripts" / "deployment.sh"), "deploy-cloud-run"],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "DRY RUN ONLY" in result.stdout
    assert "Re-run with --execute" in result.stdout


def test_artifact_cleanup_policy_bounds_stale_storage() -> None:
    policies = json.loads(
        (ROOT / "deployment" / "artifact_cleanup_policy.json").read_text(encoding="utf-8")
    )
    assert policies[0]["action"] == {"type": "Delete"}
    assert policies[0]["condition"]["olderThan"] == "30d"
    assert policies[1]["action"] == {"type": "Keep"}
    assert policies[1]["mostRecentVersions"]["keepCount"] == 3


def test_bundle_validator_accepts_static_files_and_rejects_private_content(tmp_path: Path) -> None:
    validator = _load_bundle_validator()
    bundle = tmp_path / "dist"
    bundle.mkdir()
    (bundle / "index.html").write_text("<html><script src='/assets/app.js'></script></html>", encoding="utf-8")
    assets = bundle / "assets"
    assets.mkdir()
    (assets / "app.js").write_text("console.log('safe synthetic bundle')", encoding="utf-8")
    assert len(validator.validate_bundle(bundle)) == 2

    (assets / "app.js").write_text(
        "const firebaseConfig={apiKey:'AIza" + "A" * 35 + "'};",
        encoding="utf-8",
    )
    assert len(validator.validate_bundle(bundle)) == 2
    (assets / "app.js").write_text(
        '{"private_key_id":"not-a-real-service-credential"}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="service-account"):
        validator.validate_bundle(bundle)
    (assets / "app.js").write_text("console.log('safe synthetic bundle')", encoding="utf-8")

    (bundle / "nft.csv").write_text("wallet,amount\nnot-real,1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="forbidden bundle file"):
        validator.validate_bundle(bundle)
    (bundle / "nft.csv").unlink()

    outside = tmp_path / "outside.txt"
    outside.write_text("not part of the bundle", encoding="utf-8")
    (bundle / "linked.txt").symlink_to(outside)
    with pytest.raises(ValueError, match="symbolic links"):
        validator.validate_bundle(bundle)


def test_deployment_files_are_excluded_from_api_image_context() -> None:
    rules = {
        line.strip()
        for line in (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    assert {"deployment/", "firebase.json", ".firebaserc*"} <= rules
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "COPY ." not in dockerfile


def test_firebase_sdk_has_no_telemetry_or_automatic_cloud_publish() -> None:
    package = json.loads((ROOT / "frontend" / "package.json").read_text(encoding="utf-8"))
    assert set(package["dependencies"]) == {"firebase", "react", "react-dom"}
    dependency_names = set(package["dependencies"]) | set(package["devDependencies"])
    assert dependency_names.isdisjoint({"@sentry/react", "@vercel/analytics", "posthog-js"})

    workflows = ROOT / ".github" / "workflows"
    if workflows.is_dir():
        text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in workflows.rglob("*")
            if path.is_file()
        ).casefold()
        assert "firebase deploy" not in text
        assert "gcloud run deploy" not in text
        assert "docker push" not in text


def test_required_deployment_runbooks_exist_and_do_not_claim_a_live_deployment() -> None:
    required = (
        "google_cloud_deployment_plan.md",
        "firebase_hosting_configuration.md",
        "cloud_run_configuration.md",
        "cloud_cost_and_security_controls.md",
        "deployment_readiness_checklist.md",
    )
    for name in required:
        text = (ROOT / "docs" / name).read_text(encoding="utf-8")
        assert len(text.strip()) > 500
        assert any(phase in text.casefold() for phase in ("phase 7a", "phase 7b"))
    combined = "\n".join((ROOT / "docs" / name).read_text(encoding="utf-8") for name in required)
    assert "No Google Cloud/Firebase resource" in combined
    assert "hosted browser" in combined
    assert "not a deployment record" in combined.casefold()
