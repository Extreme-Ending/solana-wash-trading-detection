# Model artifact handover

## Public selected-model release

| Property | Verified value |
| --- | --- |
| Experiment version | `4B.1` |
| Model served | Isolation Forest |
| Repository path | `artifacts/release/4B.1/anomaly_models.joblib` |
| Artifact SHA-256 | `de349dd2284db122ef528c03f0c61e7ab75f92ad002489399d074f554a61ebe5` |
| Manifest SHA-256 | `e7c6188b6983650c6fecc002033ca3c70de9ef6f77e0395c5c6dccb99415bc13` |
| Artifact profile | `selected_isolation_forest_serving_only` |
| Training cutoff | `2025-09-01T00:00:00+00:00` |
| Reference wallets | 1,754 |
| Registered features | 29 |
| Contains row-level training arrays | No |

The public artifact was extracted from the checksum-verified research bundle without retraining. It contains the fitted selected Isolation Forest pipeline, its 29-feature contract and aggregate training-reference statistics. It excludes the raw CSV, wallet identifiers, wallet snapshots, input-audit objects, the robust MAD comparison model and Local Outlier Factor. LOF is excluded because fitted novelty LOF retains row-level feature arrays.

The artifact produces a relative unsupervised anomaly score. It is not a fraud probability, verified wash-trading label or automated decision.

## Verify and score

From the repository root in the documented Python environment:

```bash
(cd artifacts/release/4B.1 && sha256sum -c SHA256SUMS)
python -m pip install -e '.[api,models]'
python scripts/demonstrate_batch_scoring.py \
  --artifact artifacts/release/4B.1/anomaly_models.joblib \
  --manifest artifacts/release/4B.1/anomaly_models_manifest.json \
  --sha256 de349dd2284db122ef528c03f0c61e7ab75f92ad002489399d074f554a61ebe5
```

The demonstration submits clearly synthetic transaction histories through the production inference contract and returns finite numerical scores. It verifies compatibility and deterministic inference behavior, not fraud-detection effectiveness.

Joblib uses pickle-compatible serialization and may execute code during deserialization. Load this artifact only from the trusted repository after verifying `SHA256SUMS`. Never load an arbitrary model file received from an untrusted source.

## Private research bundle

The full local research bundle remains ignored and is not the public serving deliverable.

| Property | Verified value |
| --- | --- |
| Local path | `artifacts/experimental/anomaly_models.joblib` |
| Artifact SHA-256 | `3e35561b0bf5db42c5b7146e7ff568e313be1beb1be724997356af45f5533035` |
| Manifest SHA-256 | `1551d55f469ac3abd7a985d98055c69375968a2d9e28151e153aea2b61061ad0` |
| Models | Isolation Forest, novelty LOF and robust MAD |
| Reason kept private | Novelty LOF retains fitted row-level feature arrays |

The public release records both private-source hashes in its manifest, preserving lineage to the evaluated research bundle. Synthetic scoring with the public artifact was compared with scoring from the full bundle and produced the same selected-model response. The public file is the checksum-bound release artifact; do not overwrite it by rebuilding into the same version directory.

## Rebuilding a new release candidate

`scripts/build_public_model_artifact.py` validates the trusted research hashes and writes only to an empty output directory. Use a new candidate directory, review its contents and assign a new version before replacing a published release. Joblib serialization is environment-dependent, so a newly serialized candidate is not expected to reproduce the existing release bytes outside the pinned environment.

The older ZIP builder under `scripts/package_model_artifact.py` packages the full research bundle for restricted review. Its ignored output under `dist/reviewer/` does not satisfy the public GitHub artifact requirement and should not be published because it includes the fitted LOF row arrays.

## Publication state

The selected-model files are present locally and are not ignored. They become publicly accessible only after the student reviews, stages, commits and pushes them. The raw dataset and full research bundle must remain excluded. No public redistribution permission for the raw Dune result has been established, and no legal determination about derived-model distribution is claimed here; the release is technically minimized to exclude observed row-level records and identifiers.
