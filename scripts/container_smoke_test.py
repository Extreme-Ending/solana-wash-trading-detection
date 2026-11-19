"""Build and exercise the Phase 5B image using only synthetic request data."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IMAGE = "solana-wallet-risk-api:phase7b"
EXPERIMENTAL_ARTIFACT_SHA256 = (
    "de349dd2284db122ef528c03f0c61e7ab75f92ad002489399d074f554a61ebe5"
)


def _run(*args: str, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=capture,
    )


def _docker_json(*args: str) -> Any:
    result = _run("docker", *args, capture=True)
    return json.loads(result.stdout)


def _request(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any]]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def _wait_for_health(base_url: str, timeout: float = 45.0) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            status, body = _request("GET", f"{base_url}/healthz")
            if status == 200 and body.get("status") == "ok":
                return
        except (OSError, ValueError) as exc:
            last_error = exc
        time.sleep(0.5)
    raise RuntimeError(f"container did not become healthy: {last_error}")


def _wait_for_container_health(name: str, timeout: float = 45.0) -> str:
    deadline = time.monotonic() + timeout
    state = "unknown"
    while time.monotonic() < deadline:
        state = _run(
            "docker",
            "inspect",
            "--format",
            "{{.State.Health.Status}}",
            name,
            capture=True,
        ).stdout.strip()
        if state == "healthy":
            return state
        if state == "unhealthy":
            break
        time.sleep(0.5)
    raise RuntimeError(f"Docker health check did not become healthy; last state: {state}")


def _synthetic_payload() -> dict[str, Any]:
    return {
        "as_of": "2025-02-01T00:00:00Z",
        "events": [
            {
                "source_row_number": 1,
                "wallet": "synthetic-wallet-001",
                "block_time": "2025-01-15T12:00:00Z",
                "block_slot": 1001,
                "tx_hash": "synthetic-transaction-001",
                "dex": "synthetic-dex",
                "token_pair": "TOKEN-A/TOKEN-B",
                "token_in": "synthetic-token-a",
                "token_out": "synthetic-token-b",
                "amount_usd": 125.5,
                "fee_usd": 0.25,
                "outer_instruction_index": 1,
                "inner_instruction_index": 0,
            }
        ],
    }


def _remove_container(name: str) -> None:
    exists = subprocess.run(
        ["docker", "container", "inspect", name],
        cwd=ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0
    if exists:
        subprocess.run(
            ["docker", "container", "rm", "--force", name],
            cwd=ROOT,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def _start_container(
    *,
    name: str,
    image: str,
    host_port: int,
    container_port: int,
    experimental_scoring: bool = False,
) -> None:
    command = [
        "docker",
        "run",
        "--detach",
        "--name",
        name,
        "--publish",
        f"127.0.0.1:{host_port}:{container_port}",
        "--env",
        f"PORT={container_port}",
        "--env",
        (
            "SOLANA_RISK_ENVIRONMENT=production"
            if experimental_scoring
            else "SOLANA_RISK_ENVIRONMENT=container-test"
        ),
        "--read-only",
        "--tmpfs",
        "/tmp:size=16m,mode=1777",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges:true",
    ]
    if experimental_scoring:
        command.extend(
            [
                "--env",
                "SOLANA_RISK_FIREBASE_PROJECT_ID=container-test-project",
                "--env",
                "SOLANA_RISK_ALLOWED_UIDS=container-test-uid",
                "--env",
                "SOLANA_RISK_ENABLE_EXPERIMENTAL_SCORING=true",
                "--env",
                "SOLANA_RISK_ALLOW_PRODUCTION_EXPERIMENTAL_SCORING=true",
                "--env",
                "SOLANA_RISK_EXPERIMENTAL_MODEL_ARTIFACT=/app/artifacts/experimental/anomaly_models.joblib",
                "--env",
                "SOLANA_RISK_EXPERIMENTAL_MODEL_MANIFEST=/app/artifacts/experimental/anomaly_models_manifest.json",
                "--env",
                f"SOLANA_RISK_EXPERIMENTAL_ARTIFACT_SHA256={EXPERIMENTAL_ARTIFACT_SHA256}",
            ]
        )
    command.append(image)
    _run(*command)


def validate_image(image: str, *, experimental_scoring: bool = False) -> dict[str, Any]:
    inspection = _docker_json("image", "inspect", image)[0]
    config = inspection["Config"]
    assert config["User"] == "10001:10001"
    assert config["Cmd"] == ["python", "-m", "solana_risk.api.run"]
    assert "/healthz" in " ".join(config["Healthcheck"]["Test"])

    if experimental_scoring:
        check_code = f"""
import hashlib
import importlib.util
from pathlib import Path
from solana_risk.api.experimental_scoring import TrustedExperimentalScorer
from solana_risk.api.schemas import ScoreRequest

artifact = Path('/app/artifacts/experimental/anomaly_models.joblib')
manifest = Path('/app/artifacts/experimental/anomaly_models_manifest.json')
expected = '{EXPERIMENTAL_ARTIFACT_SHA256}'
assert importlib.util.find_spec('joblib') is not None
assert importlib.util.find_spec('sklearn') is not None
assert artifact.is_file() and manifest.is_file()
assert hashlib.sha256(artifact.read_bytes()).hexdigest() == expected
scorer = TrustedExperimentalScorer.load(
    artifact_path=artifact,
    manifest_path=manifest,
    expected_sha256=expected,
)
result = scorer.score(ScoreRequest.model_validate({{
    'as_of': '2025-11-01T00:00:00Z',
    'events': [{{
        'source_row_number': 1,
        'wallet': 'synthetic-container-wallet',
        'block_time': '2025-10-15T12:00:00Z',
        'block_slot': 1001,
        'tx_hash': 'synthetic-container-transaction',
        'dex': 'synthetic-dex',
        'token_pair': 'TOKEN-A/TOKEN-B',
        'token_in': 'synthetic-token-a',
        'token_out': 'synthetic-token-b',
        'amount_usd': 125.5,
        'fee_usd': 0.25,
        'outer_instruction_index': 1,
        'inner_instruction_index': 0,
    }}],
}}))
assert result.status == 'experimental_anomaly_score'
assert result.methodology_status == 'experimental_unsupervised_research_only'
assert result.is_probability is False
assert isinstance(result.anomaly_score, float)
for forbidden in (
    '/app/nft.csv', '/app/nft_trades.csv', '/app/.env', '/app/.agents',
    '/app/AGENTS.md', '/app/data', '/app/reports', '/app/models',
    '/app/notebooks', '/app/tests',
):
    assert not Path(forbidden).exists(), forbidden
print('trusted experimental scoring image checks: PASS')
"""
    else:
        check_code = """
import importlib.util
from pathlib import Path
import solana_risk.api.main

assert importlib.util.find_spec('joblib') is None
assert importlib.util.find_spec('sklearn') is None
for forbidden in (
    '/app/nft.csv', '/app/nft_trades.csv', '/app/.env', '/app/.agents',
    '/app/AGENTS.md', '/app/data', '/app/reports', '/app/artifacts',
    '/app/models', '/app/notebooks', '/app/tests',
):
    assert not Path(forbidden).exists(), forbidden
print('installed API import and image-content checks: PASS')
"""
    _run(
        "docker", "run", "--rm", "--entrypoint", "python",
        "--env", "SOLANA_RISK_ENVIRONMENT=container-test",
        image, "-c", check_code,
    )
    return {
        "image_id": inspection["Id"],
        "size_bytes": inspection["Size"],
        "configured_user": config["User"],
    }


def validate_default_runtime(
    image: str,
    name: str,
    *,
    host_port: int = 8080,
    experimental_scoring: bool = False,
) -> dict[str, Any]:
    base_url = f"http://127.0.0.1:{host_port}"
    _start_container(
        name=name,
        image=image,
        host_port=host_port,
        container_port=8080,
        experimental_scoring=experimental_scoring,
    )
    _wait_for_health(base_url)

    status, health = _request("GET", f"{base_url}/healthz")
    assert status == 200 and health["status"] == "ok"
    status, readiness = _request("GET", f"{base_url}/readyz")
    if experimental_scoring:
        assert status == 200
        assert readiness == {
            "status": "ready",
            "available": True,
            "capability": "experimental_anomaly_scoring",
            "methodology_status": "experimental_unsupervised_research_only",
            "is_probability": False,
            "message": "Experimental unsupervised anomaly scoring is available.",
        }
    else:
        assert status == 503 and readiness["error"]["code"] == "MODEL_NOT_APPROVED"
    status, preview = _request("POST", f"{base_url}/v1/features/preview", _synthetic_payload())
    assert status == 401 and preview["error"]["code"] == "AUTHENTICATION_REQUIRED"
    status, scoring = _request("POST", f"{base_url}/v1/score", _synthetic_payload())
    assert status == 401 and scoring["error"]["code"] == "AUTHENTICATION_REQUIRED"
    status, openapi = _request("GET", f"{base_url}/openapi.json")
    if experimental_scoring:
        assert status == 404
    else:
        assert status == 200 and "/healthz" in openapi["paths"]

    runtime_uid = _run("docker", "exec", name, "id", "-u", capture=True).stdout.strip()
    assert runtime_uid == "10001"
    health_state = _wait_for_container_health(name)
    assert health_state == "healthy"

    _run("docker", "stop", "--timeout", "10", name)
    exit_code = int(
        _run("docker", "inspect", "--format", "{{.State.ExitCode}}", name, capture=True)
        .stdout.strip()
    )
    assert exit_code == 0
    logs = _run("docker", "logs", name, capture=True)
    combined_logs = logs.stdout + logs.stderr
    assert "Application shutdown complete" in combined_logs
    return {
        "healthz": 200,
        "readyz": 200 if experimental_scoring else 503,
        "feature_preview": 401,
        "score": 401,
        "openapi": 404 if experimental_scoring else 200,
        "runtime_uid": int(runtime_uid),
        "graceful_exit_code": exit_code,
    }


def validate_custom_port(
    image: str,
    name: str,
    *,
    host_port: int = 18081,
    experimental_scoring: bool = False,
) -> dict[str, int]:
    base_url = f"http://127.0.0.1:{host_port}"
    _start_container(
        name=name,
        image=image,
        host_port=host_port,
        container_port=9090,
        experimental_scoring=experimental_scoring,
    )
    _wait_for_health(base_url)
    status, _ = _request("GET", f"{base_url}/healthz")
    assert status == 200
    _run("docker", "stop", "--timeout", "10", name)
    return {"configured_container_port": 9090, "healthz": status}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--dockerfile", default="Dockerfile")
    parser.add_argument("--expect-experimental-scoring", action="store_true")
    parser.add_argument("--host-port", type=int, default=8080)
    parser.add_argument("--custom-host-port", type=int, default=18081)
    args = parser.parse_args()
    port_arguments = (
        ("--host-port", args.host_port),
        ("--custom-host-port", args.custom_host_port),
    )
    for name, value in port_arguments:
        if not 1 <= value <= 65535:
            parser.error(f"{name} must be between 1 and 65535")
    if args.host_port == args.custom_host_port:
        parser.error("--host-port and --custom-host-port must differ")

    suffix = uuid.uuid4().hex[:10]
    default_name = f"solana-risk-smoke-{suffix}"
    custom_name = f"solana-risk-port-{suffix}"
    results: dict[str, Any] = {}
    try:
        if not args.skip_build:
            _run("docker", "build", "--file", args.dockerfile, "--tag", args.image, ".")
        results["image"] = validate_image(
            args.image,
            experimental_scoring=args.expect_experimental_scoring,
        )
        results["default_runtime"] = validate_default_runtime(
            args.image,
            default_name,
            host_port=args.host_port,
            experimental_scoring=args.expect_experimental_scoring,
        )
        results["custom_port"] = validate_custom_port(
            args.image,
            custom_name,
            host_port=args.custom_host_port,
            experimental_scoring=args.expect_experimental_scoring,
        )
    finally:
        _remove_container(default_name)
        _remove_container(custom_name)

    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
