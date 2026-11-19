# Model artifact handover

## Trusted artifact

| Property | Verified value |
| --- | --- |
| Experiment version | `4B.1` |
| Model served | Isolation Forest |
| Artifact | `anomaly_models.joblib` |
| Artifact SHA-256 | `3e35561b0bf5db42c5b7146e7ff568e313be1beb1be724997356af45f5533035` |
| Manifest SHA-256 | `1551d55f469ac3abd7a985d98055c69375968a2d9e28151e153aea2b61061ad0` |
| Canonical feature-registry SHA-256 | `75be47d7f875e2a04848d8b8b7931d7f90d7bbf3c5aa2b3476a827e09e2d4e8a` |
| Snapshot SHA-256 | `779b446b15cce9cdc630353c60ffad2bfae039b086a1e0daa8dd66d05aff3a60` |
| Training cutoff | `2025-09-01T00:00:00+00:00` |
| Training wallets | 1,754 |
| Python | 3.12.3 |
| pandas | 3.0.2 |
| NumPy | 2.4.4 |
| scikit-learn | 1.8.0 |
| joblib | 1.5.3 |

The registry value fingerprints the canonical registered-feature payload, not the Markdown bytes of `docs/feature_registry.md`. The joblib bundle contains fitted Isolation Forest, LOF and robust MAD pipelines plus training-reference metadata. FastAPI serves only the Isolation Forest after validating the artifact digest, manifest, feature order, registry, cutoff, experiment version and dependency versions.

## Build the reviewer package

The local artifact is ignored and must not be committed accidentally. Build a verified ZIP under ignored `dist/reviewer/`:

```bash
python scripts/package_model_artifact.py
```

The package contains the artifact, manifest, checksum list, source revision, expected synthetic inference result and a security/readme file. The script refuses a missing, symlinked, checksum-mismatched or incompatible bundle. It runs deterministic synthetic inference before packaging.

## Reviewer loading

Only load a package received through a trusted course or repository channel. Joblib uses pickle-compatible serialization and can execute code during deserialization.

```bash
python -m pip install -e '.[models]'
python -c "from solana_risk.models.train_anomaly import load_bundle; load_bundle('anomaly_models.joblib'); print('artifact contract valid')"
```

Application loading additionally requires the matching manifest and expected SHA-256 through the documented `SOLANA_RISK_EXPERIMENTAL_*` settings.

From the matching source revision, verify deterministic inference against the packaged result:

```bash
sha256sum -c SHA256SUMS
python scripts/demonstrate_batch_scoring.py \
  --artifact /path/to/anomaly_models.joblib \
  --manifest /path/to/anomaly_models_manifest.json \
  --sha256 3e35561b0bf5db42c5b7146e7ff568e313be1beb1be724997356af45f5533035 \
  > observed_synthetic_result.json
```

Compare `observed_synthetic_result.json` with `EXPECTED_SYNTHETIC_RESULT.json`. The input is synthetic and confirms deterministic inference behavior only. It is not model-effectiveness or fraud-detection evidence.

## Delivery decision

The repository requirements do not state whether an external binary attachment counts as being supplied through the repository. Confirm the accepted channel before publication.

| Delivery method | Advantage | Limitation |
| --- | --- | --- |
| Institution-controlled submission store | Restricted reviewer access and clear submission boundary | May not appear directly in the repository clone |
| GitHub release asset | Binds the ZIP to a reviewed repository revision | Public visibility follows repository/release access and may be unsuitable while rights are unresolved |
| Git LFS | Preserves a repository path and normal checkout workflow | Adds quota, client and binary-history requirements; does not solve permission concerns |

Until dataset-derived artifact rights are confirmed, the institution-controlled store is the safest default.

Recommended student action:

1. Confirm that the selected restricted attachment or repository mechanism satisfies the deliverable rule.
2. After committing the reviewed source, run `python scripts/package_model_artifact.py` locally from that exact revision.
3. Verify the displayed ZIP and file hashes.
4. Upload the ZIP personally to the approved channel, bound to the reviewed Git revision.
5. Provide the reviewer the ZIP SHA-256 and this document.

Do not include the raw Dune export in the package. Do not publish the model if the institution determines that its derived state is restricted by the unresolved source terms.
