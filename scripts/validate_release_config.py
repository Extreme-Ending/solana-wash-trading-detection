"""Fail-closed validation for manually dispatched CI/CD release inputs."""

from __future__ import annotations

import argparse
import os
import re
from collections.abc import Mapping
from urllib.parse import urlparse

PROJECT_ID = "solana-wallet-risk"
PROJECT_NUMBER = "441056127470"
REGION = "africa-south1"
REPOSITORY = "Extreme-Ending/solana-wash-trading-detection"
ARTIFACT_REPOSITORY = "solana-wallet-risk"
CLOUD_RUN_SERVICE = "solana-wallet-risk-api"
HOSTING_SITE = "solana-wallet-risk"
RUNTIME_SERVICE_ACCOUNT = (
    "solana-wallet-risk-runtime@solana-wallet-risk.iam.gserviceaccount.com"
)
RUN_DEPLOY_SERVICE_ACCOUNT = (
    "github-cloud-run-deployer@solana-wallet-risk.iam.gserviceaccount.com"
)
FIREBASE_DEPLOY_SERVICE_ACCOUNT = (
    "github-firebase-deployer@solana-wallet-risk.iam.gserviceaccount.com"
)
EXPECTED_WIF_PROVIDER = (
    f"projects/{PROJECT_NUMBER}/locations/global/workloadIdentityPools/"
    "github-actions/providers/github"
)
PLACEHOLDER = re.compile(r"(?:your|replace|example|changeme|placeholder)", re.I)
SHA = re.compile(r"[0-9a-f]{40}")
DIGEST = re.compile(r"sha256:[0-9a-f]{64}")


class ReleaseConfigurationError(ValueError):
    """Raised when a deployment input is missing, ambiguous, or unsupported."""


def _required(values: Mapping[str, str], name: str) -> str:
    value = values.get(name, "").strip()
    if not value or PLACEHOLDER.search(value):
        raise ReleaseConfigurationError(f"{name} is missing or contains a placeholder")
    if "\n" in value or "\r" in value:
        raise ReleaseConfigurationError(f"{name} must be a single line")
    return value


def _exact(values: Mapping[str, str], name: str, expected: str) -> None:
    if _required(values, name) != expected:
        raise ReleaseConfigurationError(f"{name} must equal {expected}")


def _https_origin(values: Mapping[str, str], name: str) -> str:
    value = _required(values, name)
    parsed = urlparse(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.path not in ("", "/")
        or parsed.params
        or parsed.query
        or parsed.fragment
    ):
        raise ReleaseConfigurationError(f"{name} must be an HTTPS origin without a path")
    return value.rstrip("/")


def validate_common(values: Mapping[str, str]) -> None:
    _exact(values, "GITHUB_REPOSITORY", REPOSITORY)
    _exact(values, "GITHUB_REF", "refs/heads/main")
    revision = _required(values, "GITHUB_SHA")
    if not SHA.fullmatch(revision):
        raise ReleaseConfigurationError("GITHUB_SHA must be a full lowercase Git SHA")
    _exact(values, "GCP_PROJECT_ID", PROJECT_ID)
    _exact(values, "GCP_PROJECT_NUMBER", PROJECT_NUMBER)
    _exact(values, "COST_CONTROL_ATTESTATION", "USD10-50-80-100-REVIEWED")
    _exact(values, "GCP_WORKLOAD_IDENTITY_PROVIDER", EXPECTED_WIF_PROVIDER)


def validate_cloud_run(values: Mapping[str, str]) -> None:
    validate_common(values)
    _exact(values, "GCP_REGION", REGION)
    _exact(values, "ARTIFACT_REGISTRY_REPOSITORY", ARTIFACT_REPOSITORY)
    _exact(values, "CLOUD_RUN_SERVICE", CLOUD_RUN_SERVICE)
    _exact(values, "FIREBASE_PROJECT_ID", PROJECT_ID)
    _exact(values, "FIREBASE_HOSTING_SITE", HOSTING_SITE)
    _exact(values, "GCP_RUNTIME_SERVICE_ACCOUNT", RUNTIME_SERVICE_ACCOUNT)
    _exact(values, "SOLANA_RISK_ENABLE_EXPERIMENTAL_SCORING", "false")
    _exact(values, "MAX_INSTANCES", "2")
    _exact(values, "GCP_DEPLOY_SERVICE_ACCOUNT", RUN_DEPLOY_SERVICE_ACCOUNT)
    allowlist = _required(values, "SOLANA_RISK_ALLOWED_UIDS")
    if not re.fullmatch(r"[^,\s]+(?:,[^,\s]+)*", allowlist):
        raise ReleaseConfigurationError("SOLANA_RISK_ALLOWED_UIDS is malformed")


def validate_firebase(values: Mapping[str, str]) -> None:
    validate_common(values)
    _exact(values, "FIREBASE_PROJECT_ID", PROJECT_ID)
    _exact(values, "FIREBASE_HOSTING_SITE", HOSTING_SITE)
    _exact(values, "VITE_FIREBASE_PROJECT_ID", PROJECT_ID)
    _exact(
        values,
        "VITE_FIREBASE_AUTH_DOMAIN",
        f"{PROJECT_ID}.firebaseapp.com",
    )
    _https_origin(values, "VITE_API_BASE_URL")
    api_key = _required(values, "VITE_FIREBASE_API_KEY")
    if not re.fullmatch(r"AIza[0-9A-Za-z_-]{30,}", api_key):
        raise ReleaseConfigurationError("VITE_FIREBASE_API_KEY is malformed")
    app_id = _required(values, "VITE_FIREBASE_APP_ID")
    if not re.fullmatch(r"1:\d+:web:[0-9a-f]+", app_id, re.I):
        raise ReleaseConfigurationError("VITE_FIREBASE_APP_ID is malformed")
    _exact(
        values,
        "FIREBASE_DEPLOY_SERVICE_ACCOUNT",
        FIREBASE_DEPLOY_SERVICE_ACCOUNT,
    )


def validate_digest(value: str) -> None:
    if not DIGEST.fullmatch(value.strip()):
        raise ReleaseConfigurationError("image digest must be sha256 followed by 64 hex digits")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        required=True,
        choices=("cloud-run", "firebase-preview", "firebase-live", "image-digest"),
    )
    parser.add_argument("--image-digest")
    args = parser.parse_args()
    try:
        if args.mode == "cloud-run":
            validate_cloud_run(os.environ)
        elif args.mode.startswith("firebase-"):
            validate_firebase(os.environ)
        else:
            validate_digest(args.image_digest or "")
    except ReleaseConfigurationError as exc:
        print(f"Release configuration rejected: {exc}")
        return 2
    print(f"Release configuration validation: PASS ({args.mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
