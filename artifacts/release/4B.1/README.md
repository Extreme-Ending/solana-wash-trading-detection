# Public Isolation Forest artifact

This directory contains the fitted Isolation Forest selected for Solana Wallet Risk
experiment `4B.1`. It is extracted from the checksum-verified research
bundle without retraining. The public bundle excludes LOF, robust MAD, input-audit
objects, wallet identifiers, raw events, wallet-level snapshots, and fitted LOF rows.

The output is an unsupervised anomaly score. It is not a fraud probability, verified
wash-trading label, or automated enforcement decision.

## Verify and run

From the repository root in the documented Python environment:

```bash
(cd artifacts/release/4B.1 && sha256sum -c SHA256SUMS)
python -m pip install -e '.[api,models]'
python scripts/demonstrate_batch_scoring.py \
  --artifact artifacts/release/4B.1/anomaly_models.joblib \
  --manifest artifacts/release/4B.1/anomaly_models_manifest.json \
  --sha256 de349dd2284db122ef528c03f0c61e7ab75f92ad002489399d074f554a61ebe5
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
