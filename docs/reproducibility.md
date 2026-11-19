# Reproducibility guide

## Requirements

- Python 3.11 to 3.13. Python 3.11 is used by CI and containers.
- Node.js 22.22.2 or compatible with `frontend/package.json`.
- The authorized private export from Dune query 6561080 at repository-root `nft.csv`.
- Dependencies installed from `pyproject.toml` and `frontend/package-lock.json`.

Core pinned versions include pandas 3.0.2, NumPy 2.4.4, scikit-learn 1.8.0, joblib 1.5.3, FastAPI 0.139.0, React 19.3.1, TypeScript 7.0.2, and Vite 8.3.8.

## Verified fingerprints

| Asset | SHA-256 |
| --- | --- |
| Source CSV | `8f387709c6742f2fc31c19fc32dac27474b6b27b9304786c367a8d8bece81271` |
| Feature registry | `75be47d7f875e2a04848d8b8b7931d7f90d7bbf3c5aa2b3476a827e09e2d4e8a` |
| Wallet snapshots | `779b446b15cce9cdc630353c60ffad2bfae039b086a1e0daa8dd66d05aff3a60` |
| Public selected-model artifact | `de349dd2284db122ef528c03f0c61e7ab75f92ad002489399d074f554a61ebe5` |
| Public selected-model manifest | `e7c6188b6983650c6fecc002033ca3c70de9ef6f77e0395c5c6dccb99415bc13` |
| Private full research artifact | `3e35561b0bf5db42c5b7146e7ff568e313be1beb1be724997356af45f5533035` |
| Private full research manifest | `1551d55f469ac3abd7a985d98055c69375968a2d9e28151e153aea2b61061ad0` |

The private research digests apply to two byte-identical training runs in the pinned local environment. The public artifact was extracted from that trusted bundle without retraining and is the canonical checksum-bound release. Joblib bytes are not promised to match after reserialization with different Python or dependency versions. The manifest remains the compatibility contract.

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

## Public artifact verification

```bash
(cd artifacts/release/4B.1 && sha256sum -c SHA256SUMS)
```

The public release contains only the fitted Isolation Forest, feature contract and aggregate reference statistics. It excludes raw events, wallet identifiers, wallet snapshots and novelty LOF's retained row-level matrix. A different digest must be investigated rather than silently accepted. Load joblib files only from a trusted source after checksum verification.

## Local inference demonstration

```bash
python scripts/demonstrate_batch_scoring.py \
  --artifact artifacts/release/4B.1/anomaly_models.joblib \
  --manifest artifacts/release/4B.1/anomaly_models_manifest.json \
  --sha256 de349dd2284db122ef528c03f0c61e7ab75f92ad002489399d074f554a61ebe5
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

## Source acquisition and limits

The dataset was extracted from Dune Analytics query 6561080 in multiple batches of approximately 1,000 rows. The query was executed again after the original extraction, so its currently visible SQL should not be treated as a preserved snapshot of the extraction-time query. Original batch files, exact historical SQL revision, execution identifiers, parameters, and extraction timestamps are unavailable. The repository therefore cannot independently reconstruct the historical acquisition sequence.

For a new acquisition, use Dune result pagination against one recorded execution ID, with `limit=1000` and the returned `next_offset` or `next_uri`. Confirm that the query SQL has no whole-result `LIMIT 1000`, record the query revision and page manifest, and audit the resulting file as a new dataset version. Result retrieval can consume Dune credits and a current execution may not match the historical checksum.

Processing and modelling remain exactly reproducible when the verified private source is supplied. The selected-model release supports clone-only numerical inference, but exact end-to-end retraining still requires the private CSV matching the documented checksum. Raw data, generated pipeline reports, snapshots and the full research artifact remain ignored and must not be uploaded without confirmed rights.
