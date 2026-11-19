#!/usr/bin/env python3
"""Build the public, selected-model-only artifact from the trusted research bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import joblib
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline

from solana_risk.features.build import MODEL_FEATURE_COLUMNS, feature_registry_sha256
from solana_risk.models.train_anomaly import EXPERIMENT_VERSION, load_bundle, sha256_file


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ARTIFACT = ROOT / "artifacts" / "experimental" / "anomaly_models.joblib"
SOURCE_MANIFEST = ROOT / "artifacts" / "experimental" / "anomaly_models_manifest.json"
DEFAULT_OUTPUT = ROOT / "artifacts" / "release" / EXPERIMENT_VERSION
SOURCE_ARTIFACT_SHA256 = "3e35561b0bf5db42c5b7146e7ff568e313be1beb1be724997356af45f5533035"
SOURCE_MANIFEST_SHA256 = "1551d55f469ac3abd7a985d98055c69375968a2d9e28151e153aea2b61061ad0"
PUBLIC_PROFILE = "selected_isolation_forest_serving_only"


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _source_manifest() -> dict[str, Any]:
    if sha256_file(SOURCE_ARTIFACT) != SOURCE_ARTIFACT_SHA256:
        raise SystemExit("Trusted research artifact checksum does not match the release contract")
    if sha256_file(SOURCE_MANIFEST) != SOURCE_MANIFEST_SHA256:
        raise SystemExit("Trusted research manifest checksum does not match the release contract")
    try:
        manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SystemExit("Trusted research manifest is unreadable") from exc
    if manifest.get("artifact_sha256") != SOURCE_ARTIFACT_SHA256:
        raise SystemExit("Trusted research manifest does not identify the trusted artifact")
    return manifest


def _public_bundle() -> tuple[dict[str, Any], dict[str, Any]]:
    source_manifest = _source_manifest()
    source = load_bundle(SOURCE_ARTIFACT)
    selected = source["models"]["isolation_forest"]
    if not isinstance(selected, Pipeline) or not isinstance(
        selected.named_steps.get("model"), IsolationForest
    ):
        raise SystemExit("Trusted research bundle does not contain the selected Isolation Forest")

    metadata_fields = (
        "experiment_status",
        "experiment_version",
        "experiment_scope",
        "labels_used",
        "score_semantics",
        "outcome_semantics",
        "is_probability",
        "feature_rules_version",
        "feature_registry_sha256",
        "feature_order",
        "feature_reference_version",
        "metadata_columns_excluded",
        "snapshot_sha256",
        "temporal_split",
        "config",
        "versions",
        "preprocessing",
    )
    metadata = {name: source["metadata"][name] for name in metadata_fields}
    metadata["artifact_profile"] = PUBLIC_PROFILE
    metadata["source_research_artifact_sha256"] = SOURCE_ARTIFACT_SHA256

    reference = source["training_reference"]
    public_reference = {
        "version": reference["version"],
        "wallet_count": reference["wallet_count"],
        "feature_order": reference["feature_order"],
        "statistics": reference["statistics"],
    }
    bundle = {
        "metadata": metadata,
        "models": {"isolation_forest": selected},
        "training_reference": public_reference,
    }
    return bundle, source_manifest


def build_public_artifact(output_dir: Path) -> dict[str, Path | str]:
    bundle, source_manifest = _public_bundle()
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact = output_dir / "anomaly_models.joblib"
    manifest_path = output_dir / "anomaly_models_manifest.json"
    readme_path = output_dir / "README.md"
    checksums_path = output_dir / "SHA256SUMS"

    existing = [
        path
        for path in (artifact, manifest_path, readme_path, checksums_path)
        if path.exists()
    ]
    if existing:
        names = ", ".join(path.name for path in existing)
        raise SystemExit(
            "Refusing to overwrite an existing public release. "
            f"Choose an empty --output-dir after reviewing the source bundle: {names}"
        )

    joblib.dump(bundle, artifact, compress=3)
    artifact_sha256 = sha256_file(artifact)
    manifest = dict(source_manifest)
    manifest.update(
        {
            "artifact": artifact.name,
            "artifact_profile": PUBLIC_PROFILE,
            "artifact_sha256": artifact_sha256,
            "contains_training_rows": False,
            "models": ["isolation_forest"],
            "source_research_artifact_sha256": SOURCE_ARTIFACT_SHA256,
            "source_research_manifest_sha256": SOURCE_MANIFEST_SHA256,
        }
    )
    manifest_bytes = (
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode("utf-8")
    manifest_path.write_bytes(manifest_bytes)
    manifest_sha256 = _sha256_bytes(manifest_bytes)

    readme = f"""# Public Isolation Forest artifact

This directory contains the fitted Isolation Forest selected for Solana Wallet Risk
experiment `{EXPERIMENT_VERSION}`. It is extracted from the checksum-verified research
bundle without retraining. The public bundle excludes LOF, robust MAD, input-audit
objects, wallet identifiers, raw events, wallet-level snapshots, and fitted LOF rows.

The output is an unsupervised anomaly score. It is not a fraud probability, verified
wash-trading label, or automated enforcement decision.

## Verify and run

From the repository root in the documented Python environment:

```bash
(cd artifacts/release/{EXPERIMENT_VERSION} && sha256sum -c SHA256SUMS)
python -m pip install -e '.[api,models]'
python scripts/demonstrate_batch_scoring.py \\
  --artifact artifacts/release/{EXPERIMENT_VERSION}/anomaly_models.joblib \\
  --manifest artifacts/release/{EXPERIMENT_VERSION}/anomaly_models_manifest.json \\
  --sha256 {artifact_sha256}
```

The demonstration uses synthetic transaction histories and returns finite numerical
anomaly scores. It verifies inference behavior, not fraud-detection effectiveness.

## Security

Joblib uses pickle-compatible serialization and can execute code during loading. Load
this artifact only from this trusted repository after verifying `SHA256SUMS`. Never
deserialize an artifact from an untrusted source.

The full research bundle remains private because novelty LOF retains fitted row-level
feature arrays. This selected-model artifact contains the Isolation Forest pipeline and
aggregate training-reference statistics required by the API, not the source dataset.
"""
    readme_path.write_text(readme, encoding="utf-8")
    readme_sha256 = sha256_file(readme_path)
    checksums_path.write_text(
        f"{artifact_sha256}  anomaly_models.joblib\n"
        f"{manifest_sha256}  anomaly_models_manifest.json\n"
        f"{readme_sha256}  README.md\n",
        encoding="utf-8",
    )

    return {
        "artifact": artifact,
        "manifest": manifest_path,
        "readme": readme_path,
        "checksums": checksums_path,
        "artifact_sha256": artifact_sha256,
        "manifest_sha256": manifest_sha256,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = build_public_artifact(args.output_dir.resolve())
    print(f"Public artifact: {result['artifact']}")
    print(f"Artifact SHA-256: {result['artifact_sha256']}")
    print(f"Manifest SHA-256: {result['manifest_sha256']}")
    print("No raw data, wallet identifiers, or row-level training feature matrix was included.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
