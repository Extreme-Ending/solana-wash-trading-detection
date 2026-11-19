# Reproducibility guide

## Requirements

- Python 3.11 to 3.13. Python 3.11 is used by CI and containers.
- Node.js 22.22.2 or compatible with `frontend/package.json`.
- The authorized private Dune export at repository-root `nft.csv`.
- Dependencies installed from `pyproject.toml` and `frontend/package-lock.json`.

Core pinned versions include pandas 3.0.2, NumPy 2.4.4, scikit-learn 1.8.0, joblib 1.5.3, FastAPI 0.139.0, React 19.3.1, TypeScript 7.0.2, and Vite 8.3.8.

## Verified fingerprints

| Asset | SHA-256 |
| --- | --- |
| Source CSV | `8f387709c6742f2fc31c19fc32dac27474b6b27b9304786c367a8d8bece81271` |
| Feature registry | `75be47d7f875e2a04848d8b8b7931d7f90d7bbf3c5aa2b3476a827e09e2d4e8a` |
| Wallet snapshots | `779b446b15cce9cdc630353c60ffad2bfae039b086a1e0daa8dd66d05aff3a60` |
| Model artifact | `3e35561b0bf5db42c5b7146e7ff568e313be1beb1be724997356af45f5533035` |
| Model manifest | `1551d55f469ac3abd7a985d98055c69375968a2d9e28151e153aea2b61061ad0` |

The model and manifest digests apply to the pinned local environment. Joblib bytes are not promised to match across different Python or dependency versions. The manifest remains the compatibility contract.

## Clean pipeline

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python -m solana_risk.data.audit
python -m solana_risk.data.preprocess
python -m solana_risk.features.build \
  --as-of 2025-09-01T00:00:00Z \
  --as-of 2025-10-01T00:00:00Z \
  --as-of 2025-12-01T00:00:00Z
python -m solana_risk.models.train_anomaly
python -m solana_risk.models.evaluate_anomaly
```

Expected reconciliation is 10,800 source rows, 10,798 retained events, 2 quarantined events, and 5,996 snapshots across the three cutoffs.

## Artifact verification

```bash
sha256sum artifacts/experimental/anomaly_models.joblib
sha256sum artifacts/experimental/anomaly_models_manifest.json
```

Two independent training runs in separate temporary directories produced byte-identical artifacts and manifests in the pinned environment. A different digest must be investigated rather than silently accepted.

## Local inference demonstration

```bash
python scripts/demonstrate_batch_scoring.py \
  --artifact artifacts/experimental/anomaly_models.joblib \
  --manifest artifacts/experimental/anomaly_models_manifest.json \
  --sha256 "$(sha256sum artifacts/experimental/anomaly_models.joblib | cut -d' ' -f1)"
```

This uses labelled-as-synthetic transaction histories to verify deterministic scoring, descending rank order, review-budget selection, and equality between single and batch scoring. It does not evaluate fraud detection.

## Validation commands

```bash
python -m pytest -q
npm --prefix frontend test -- --run
npm --prefix frontend run typecheck
npm --prefix frontend run build
docker compose config --quiet
python scripts/validate_workflows.py
```

Notebook execution requires isolated Jupyter and Matplotlib configuration directories. Container smoke tests require Docker and unused loopback ports.

## Reproducibility limits

The repository cannot reproduce the source acquisition from Dune because query and export metadata are absent. It can reproduce processing and modelling only when the verified private source is supplied. Raw data, generated reports, snapshots, and model artifacts are intentionally ignored and must not be uploaded without confirmed rights.
