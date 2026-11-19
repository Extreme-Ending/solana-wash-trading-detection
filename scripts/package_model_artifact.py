#!/usr/bin/env python3
"""Create a deterministic, integrity-checked reviewer model package."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

from solana_risk.features.build import feature_registry_sha256
from solana_risk.models.train_anomaly import load_bundle


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts" / "experimental" / "anomaly_models.joblib"
MANIFEST = ROOT / "artifacts" / "experimental" / "anomaly_models_manifest.json"
OUTPUT = ROOT / "dist" / "reviewer" / "solana-wallet-risk-model-4B.1.zip"
DEMONSTRATION = ROOT / "scripts" / "demonstrate_batch_scoring.py"
FIXED_ZIP_TIME = (2026, 11, 19, 0, 0, 0)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def add_bytes(archive: zipfile.ZipFile, name: str, content: bytes) -> None:
    info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, content)


def expected_synthetic_result(artifact_digest: str) -> bytes:
    completed = subprocess.run(
        [
            sys.executable,
            str(DEMONSTRATION),
            "--artifact",
            str(ARTIFACT),
            "--manifest",
            str(MANIFEST),
            "--sha256",
            artifact_digest,
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(completed.stdout)
    if (
        result.get("deterministic_repeat") is not True
        or result.get("single_endpoint_equivalence") is not True
        or result.get("is_probability") is not False
        or result.get("model_version") != "4B.1"
    ):
        raise SystemExit("Synthetic inference evidence does not satisfy the package contract")
    return (json.dumps(result, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> int:
    for path in (ARTIFACT, MANIFEST):
        if path.is_symlink() or not path.is_file():
            raise SystemExit(f"Required trusted local file is unavailable: {path}")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    artifact_digest = sha256(ARTIFACT)
    manifest_digest = sha256(MANIFEST)
    if artifact_digest != manifest.get("artifact_sha256"):
        raise SystemExit("Artifact digest does not match its manifest")
    if manifest.get("feature_registry_sha256") != feature_registry_sha256():
        raise SystemExit("Manifest feature-registry digest is stale")
    load_bundle(ARTIFACT)
    expected_result = expected_synthetic_result(artifact_digest)
    expected_result_digest = hashlib.sha256(expected_result).hexdigest()
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    readme = f"""Solana Wallet Risk model reviewer package

Experiment version: {manifest['experiment_version']}
Source revision: {revision}
Training cutoff: {manifest['training_cutoff']}
Feature registry SHA-256: {manifest['feature_registry_sha256']}
Snapshot SHA-256: {manifest['snapshot_sha256']}

The package contains unsupervised anomaly models, not a supervised fraud classifier.
Isolation Forest scores are model-specific and are not probabilities or confirmed outcomes.

SECURITY WARNING
Joblib is pickle-compatible and can execute code during loading. Load this file only
after verifying SHA256SUMS and only when the package came through the trusted course
or repository channel.

Install the pinned project model dependencies, then load with:
  python -c "from solana_risk.models.train_anomaly import load_bundle; load_bundle('anomaly_models.joblib'); print('artifact contract valid')"

From the matching source revision, reproduce the packaged synthetic result with:
  python scripts/demonstrate_batch_scoring.py --artifact /path/to/anomaly_models.joblib --manifest /path/to/anomaly_models_manifest.json --sha256 {artifact_digest}

Compare the JSON output with EXPECTED_SYNTHETIC_RESULT.json. The demonstration uses
bounded synthetic histories and verifies deterministic software inference only. It is
not research evaluation or evidence of fraud detection.
"""
    checksums = (
        f"{artifact_digest}  anomaly_models.joblib\n"
        f"{manifest_digest}  anomaly_models_manifest.json\n"
        f"{expected_result_digest}  EXPECTED_SYNTHETIC_RESULT.json\n"
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w") as archive:
        add_bytes(archive, "README.txt", readme.encode("utf-8"))
        add_bytes(archive, "SOURCE_REVISION.txt", (revision + "\n").encode("utf-8"))
        add_bytes(archive, "SHA256SUMS", checksums.encode("utf-8"))
        add_bytes(archive, "EXPECTED_SYNTHETIC_RESULT.json", expected_result)
        add_bytes(archive, "anomaly_models_manifest.json", MANIFEST.read_bytes())
        add_bytes(archive, "anomaly_models.joblib", ARTIFACT.read_bytes())
    with zipfile.ZipFile(OUTPUT) as archive:
        if archive.testzip() is not None:
            raise SystemExit("Reviewer ZIP integrity validation failed")
    print(f"Reviewer package: {OUTPUT}")
    print(f"Package SHA-256: {sha256(OUTPUT)}")
    print(f"Artifact SHA-256: {artifact_digest}")
    print(f"Manifest SHA-256: {manifest_digest}")
    print("No data file was included. Nothing was uploaded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
