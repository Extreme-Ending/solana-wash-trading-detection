"""Static fail-closed security checks for the tracked GitHub Actions workflows."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
EXPECTED = {"ci.yml", "deploy-cloud-run.yml", "deploy-firebase.yml"}
PINNED_ACTION = re.compile(r"uses:\s+[^\s]+@[0-9a-f]{40}(?:\s+#.*)?$")


def validate() -> None:
    files = {path.name: path for path in WORKFLOWS.glob("*.yml")}
    if set(files) != EXPECTED:
        raise ValueError(f"expected exactly {sorted(EXPECTED)}, found {sorted(files)}")
    combined = "\n".join(path.read_text(encoding="utf-8") for path in files.values())
    lowered = combined.casefold()
    for forbidden in (
        "pull_request_target:",
        "--allow-unauthenticated",
        "--no-invoker-iam-check",
        "allusers",
        "firebase_token",
        "service-account-key",
        "latest",
        "solana_risk_enable_experimental_scoring=true",
    ):
        if forbidden in lowered:
            raise ValueError(f"forbidden workflow content: {forbidden}")
    for path in files.values():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.lstrip().startswith("uses:") and not PINNED_ACTION.search(line.strip()):
                raise ValueError(f"action is not pinned to an immutable SHA in {path.name}: {line}")

    ci = files["ci.yml"].read_text(encoding="utf-8")
    for required in (
        "pull_request:",
        "push:",
        "python -m pytest -q",
        "npm test -- --run",
        "npm run typecheck",
        "npm run build",
        "container_smoke_test.py",
        "validate_deployment_bundle.py",
        "rhysd/actionlint:1.7.7@sha256:887a259a5a534f3c4f36cb02dca341673c6089431057242cdc931e9f133147e9",
    ):
        if required not in ci:
            raise ValueError(f"CI requirement missing: {required}")
    if "id-token: write" in ci:
        raise ValueError("CI must not receive an OIDC token")

    for name in ("deploy-cloud-run.yml", "deploy-firebase.yml"):
        text = files[name].read_text(encoding="utf-8")
        event_block = text.split("permissions:", maxsplit=1)[0]
        if "workflow_dispatch:" not in event_block or "push:" in event_block or "pull_request:" in event_block:
            raise ValueError(f"{name} must be manual-only")
        for required in (
            "environment:",
            "id-token: write",
            "Require a successful CI run for the exact SHA",
            "refs/heads/main",
            "persist-credentials: false",
        ):
            if required not in text:
                raise ValueError(f"deployment gate missing from {name}: {required}")

    cloud = files["deploy-cloud-run.yml"].read_text(encoding="utf-8")
    for required in (
        "--no-allow-unauthenticated",
        "@${IMAGE_DIGEST}",
        "cloudbilling.googleapis.com",
        "--min 0 --max \"$MAX_INSTANCES\"",
        "SOLANA_RISK_ENABLE_EXPERIMENTAL_SCORING=false",
        "private-pilot",
    ):
        if required not in cloud:
            raise ValueError(f"Cloud Run control missing: {required}")

    firebase = files["deploy-firebase.yml"].read_text(encoding="utf-8")
    for required in (
        "firebase-tools@${FIREBASE_CLI_VERSION}",
        "hosting:channel:deploy",
        "--only hosting",
        "hosting-preview",
        "production",
    ):
        if required not in firebase:
            raise ValueError(f"Firebase control missing: {required}")


def main() -> int:
    try:
        validate()
    except ValueError as exc:
        print(f"Workflow validation failed: {exc}")
        return 2
    print("Workflow security validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
