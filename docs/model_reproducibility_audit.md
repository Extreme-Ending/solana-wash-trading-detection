# Phase 8D model reproducibility audit

## Current immutable observations

Hashes were recorded before any Phase 8D regeneration:

| Item | SHA-256 |
|---|---|
| Root `nft.csv` | `8f387709c6742f2fc31c19fc32dac27474b6b27b9304786c367a8d8bece81271` |
| `data/features/wallet_snapshots.csv` | `779b446b15cce9cdc630353c60ffad2bfae039b086a1e0daa8dd66d05aff3a60` |
| Current `anomaly_models.joblib` | `3e35561b0bf5db42c5b7146e7ff568e313be1beb1be724997356af45f5533035` |
| Current manifest | `1551d55f469ac3abd7a985d98055c69375968a2d9e28151e153aea2b61061ad0` |
| Feature registry | `75be47d7f875e2a04848d8b8b7931d7f90d7bbf3c5aa2b3476a827e09e2d4e8a` |

The manifest records experiment version `4B.1`, cutoff `2025-09-01T00:00:00+00:00`, 1,754 training wallets, reference version `training_reference_v1`, random seed 42 and exact package versions. The selected Isolation Forest uses 300 trees, `max_samples=256`, `contamination="auto"`, `max_features=1.0`, and `n_jobs=1`.

## Explanation of the Phase 8B/8C hash difference

Phase 8B reported artifact SHA-256 `737b1358a4907707f70f7c0cb34213902cd08f4685417c4da4ce8be716bf5af6`; Phase 8C/current reports `3e35561b0bf5db42c5b7146e7ff568e313be1beb1be724997356af45f5533035`.

The read-only source comparison from Phase 8B commit `0036a44` to Phase 8C commit `843e14b` shows that Phase 8C added `training_reference_v1` metadata and 29 training-only feature summaries to the serialized joblib bundle and corresponding manifest validation. It did not change the Isolation Forest constructor, fit input, feature order, random seed or training cutoff. Adding serialized fields changes the bytes and therefore the digest even when the fitted estimator is unchanged.

Supporting evidence:

- Phase 8C's synthetic demonstration scores remained exactly the earlier reported values (`0.7112287827056774`, `0.5244905161109438`, `0.45179068711851816`).
- Model parameters and the training snapshot fingerprint are unchanged.
- The current bundle contains additional reference/version/statistics data required by the advanced dashboard.
- The old artifact bytes were not retained, so a byte-level old/new object comparison is impossible. The conclusion is based on the versioned source diff, manifests, stable inputs/parameters and stable reported scores—not on an unavailable old binary.

An ignored Phase 8B-generated evaluation report can still contain the old digest. It is stale local output, not the current manifest. Regenerate ignored reports after artifact changes and use the sidecar manifest as the authoritative compatibility record.

## Clean rerun result

Two independent training runs in separate temporary directories produced:

- identical artifact SHA-256 `3e35561b0bf5db42c5b7146e7ff568e313be1beb1be724997356af45f5533035`;
- identical manifest SHA-256 `1551d55f469ac3abd7a985d98055c69375968a2d9e28151e153aea2b61061ad0`;
- byte-for-byte equal artifacts and manifests by `cmp`;
- byte-for-byte equality with the current local artifact and manifest.

This is strong reproducibility evidence for the pinned local environment. Joblib/pickle bytes are not promised to remain identical across different Python, NumPy, pandas, scikit-learn or joblib versions; the loader therefore rejects version mismatch.

## Reference statistics audit

The reference is computed only from the earliest-cutoff partition. It has the exact registry/order, cutoff, snapshot SHA and wallet count validated by the loader. For every feature it records observed/missing counts, minimum, quartiles, median, mean, maximum, binary status and constant status.

Automated tests establish:

- missing values are counted and all-missing training features are rejected;
- constant and zero-IQR cases remain valid metadata but the frontend suppresses an IQR-distance comparison;
- the three registered Boolean features are identified as binary and rendered as training true shares;
- an extreme right-skewed training value remains in maximum/mean without changing the robust median/quartiles;
- nonfinite values, unordered summaries, invalid counts and wrong binary/constant declarations are rejected;
- missing wallet histories are rejected or reported per batch rather than fabricated;
- extreme scored observations remain finite.

The dashboard comparison `(value - training median) / training IQR` is descriptive context only. It is not Isolation Forest feature attribution, SHAP, a causal contribution or an outcome explanation.

## Reproduction commands

```bash
mkdir -p /tmp/phase8d-repro-a /tmp/phase8d-repro-b
PYTHONPATH=src .venv/bin/python -m solana_risk.models.train_anomaly \
  --input data/features/wallet_snapshots.csv --artifact-dir /tmp/phase8d-repro-a
PYTHONPATH=src .venv/bin/python -m solana_risk.models.train_anomaly \
  --input data/features/wallet_snapshots.csv --artifact-dir /tmp/phase8d-repro-b
sha256sum /tmp/phase8d-repro-{a,b}/anomaly_models.joblib
sha256sum /tmp/phase8d-repro-{a,b}/anomaly_models_manifest.json
cmp /tmp/phase8d-repro-a/anomaly_models.joblib /tmp/phase8d-repro-b/anomaly_models.joblib
cmp artifacts/experimental/anomaly_models.joblib /tmp/phase8d-repro-a/anomaly_models.joblib
```

The `artifacts/` directory is ignored and remains local. Reproduction is not authorization to promote or commit the artifact.
