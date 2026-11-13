"""Static Phase 5B packaging contracts that do not require a Docker daemon."""

from __future__ import annotations

import json
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

from solana_risk.api.run import port_from_env

ROOT = Path(__file__).resolve().parents[1]


def _dependency_names(items: list[str]) -> set[str]:
    return {item.split("==", maxsplit=1)[0] for item in items}


def test_runtime_dependency_extra_excludes_model_and_development_tools() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]
    assert project["dependencies"] == ["pandas==3.0.2"]
    api_names = _dependency_names(project["optional-dependencies"]["api"])
    assert api_names == {"fastapi", "firebase-admin", "pydantic", "uvicorn"}
    assert api_names.isdisjoint({"joblib", "scikit-learn", "pytest", "jupyter"})


def test_dockerfile_has_reproducible_non_root_runtime_contract() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "python:3.11.14-slim-bookworm@sha256:" in dockerfile
    assert '"solana-wallet-risk[api]==0.0.0"' in dockerfile
    assert "USER 10001:10001" in dockerfile
    assert "COPY ." not in dockerfile
    assert "nft.csv" not in dockerfile
    assert "artifacts/experimental" not in dockerfile
    assert "/healthz" in dockerfile
    assert 'CMD ["python", "-m", "solana_risk.api.run"]' in dockerfile
    assert "--reload" not in dockerfile


def test_dockerignore_excludes_private_and_generated_material() -> None:
    rules = {
        line.strip()
        for line in (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    required = {
        ".git/",
        ".agents/",
        "AGENTS.md",
        "CODEX_IMPLEMENTATION_PROMPT.md",
        ".env",
        ".venv/",
        "nft.csv",
        "nft_trades.csv",
        "data/",
        "reports/",
        "artifacts/",
        "models/",
        "notebooks/",
        ".ipynb_checkpoints/",
        "__pycache__/",
        ".pytest_cache/",
        "frontend/dist/",
    }
    assert required <= rules
    assert "src/" not in rules
    assert "pyproject.toml" not in rules


@pytest.mark.parametrize(
    ("environ", "expected"),
    [({}, 8080), ({"PORT": "9090"}, 9090), ({"PORT": "1"}, 1), ({"PORT": "65535"}, 65535)],
)
def test_container_port_configuration(environ: dict[str, str], expected: int) -> None:
    assert port_from_env(environ) == expected


@pytest.mark.parametrize("value", ["", "not-a-port", "0", "65536"])
def test_invalid_container_port_fails_closed(value: str) -> None:
    with pytest.raises(ValueError, match="PORT"):
        port_from_env({"PORT": value})


def test_compose_configuration_is_valid_when_docker_cli_is_available() -> None:
    if shutil.which("docker") is None:
        pytest.skip("Docker CLI is unavailable; static Compose validation skipped")
    result = subprocess.run(
        ["docker", "compose", "-f", str(ROOT / "docker-compose.yml"), "config", "--format", "json"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    config = json.loads(result.stdout)
    assert set(config["services"]) == {"api"}
    service = config["services"]["api"]
    assert service["read_only"] is True
    assert service["cap_drop"] == ["ALL"]
    assert service["security_opt"] == ["no-new-privileges:true"]
    assert service["ports"][0]["host_ip"] == "127.0.0.1"
    assert int(service["ports"][0]["published"]) == 8080
    assert int(service["ports"][0]["target"]) == 8080
    assert "/healthz" in " ".join(service["healthcheck"]["test"])
    assert "volumes" not in service
