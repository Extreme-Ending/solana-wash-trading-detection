# Phase 9 reproducibility

## Reproduction contract

The evidence chain is bound by content fingerprints rather than filenames alone:

| Evidence | SHA-256 |
|---|---|
| Supplied `nft.csv` | `8f387709c6742f2fc31c19fc32dac27474b6b27b9304786c367a8d8bece81271` |
| Cleaned events | `1889adf72a727544a8759203336ac257108d344e2ea71aaa118aa04f0aa50937` |
| Quarantine | `5cab1d4860e5ab2345979085cada6e3a583933f132875209309cb1fe84e9eb38` |
| Wallet snapshots | `779b446b15cce9cdc630353c60ffad2bfae039b086a1e0daa8dd66d05aff3a60` |
| Feature registry | `75be47d7f875e2a04848d8b8b7931d7f90d7bbf3c5aa2b3476a827e09e2d4e8a` |
| Experimental artifact | `3e35561b0bf5db42c5b7146e7ff568e313be1beb1be724997356af45f5533035` |
| Artifact manifest | `1551d55f469ac3abd7a985d98055c69375968a2d9e28151e153aea2b61061ad0` |
| Current evaluation JSON | `d37426a7bc8ab478b165af7c84263283c91e46a2148bc82b146245b87383b145` |

The generated evaluation report is ignored because it is reproducible. The Phase 9 figure package is tracked and records the exact evaluation, preprocessing, feature and model-manifest input hashes in [`figure_manifest.json`](../reports/phase9/figure_manifest.json).

## Deterministic commands

The full pipeline commands are listed in [`phase9_local_demonstration.md`](phase9_local_demonstration.md). For an independent comparison, run twice in two fresh temporary roots, then compare:

```bash
sha256sum <run-a>/audit/audit.json <run-b>/audit/audit.json
sha256sum <run-a>/processed/cleaned_events.csv <run-b>/processed/cleaned_events.csv
sha256sum <run-a>/processed/quarantined_events.csv <run-b>/processed/quarantined_events.csv
sha256sum <run-a>/wallet_snapshots.csv <run-b>/wallet_snapshots.csv
sha256sum <run-a>/artifacts/anomaly_models.joblib <run-b>/artifacts/anomaly_models.joblib
cmp <run-a>/artifacts/anomaly_models.joblib <run-b>/artifacts/anomaly_models.joblib
```

Generate figures twice and compare every output:

```bash
MPLCONFIGDIR=/tmp/mpl-a .venv/bin/python scripts/generate_phase9_figures.py \
  --output-dir /tmp/phase9-figures-a
MPLCONFIGDIR=/tmp/mpl-b .venv/bin/python scripts/generate_phase9_figures.py \
  --output-dir /tmp/phase9-figures-b
cmp /tmp/phase9-figures-a/figure_03_holdout_rank_agreement.svg \
    /tmp/phase9-figures-b/figure_03_holdout_rank_agreement.svg
```

The generator removes volatile SVG date metadata, pins the SVG hash salt, uses a headless backend, orders outputs and writes sorted JSON. It fails closed for labels, claimed outcomes, row mismatch, wrong feature count or fingerprint disagreement.

## Environment limits

The artifact manifest records Python, pandas, NumPy, scikit-learn and joblib versions. Byte-identical joblib output is established only in the pinned local environment; pickle/joblib bytes are not portable guarantees across library versions. The trusted loader rejects incompatible runtime metadata rather than silently accepting it.

The raw input and experimental artifact are Git-ignored. An examiner cannot reproduce the project from a clone alone until a lawful source/distribution procedure is established. This is an unresolved reproducibility blocker, not something checksums can solve.

## Train/serve parity

- One ordered `MODEL_FEATURE_COLUMNS` registry is used by feature building, training, artifact loading, preview, single scoring and batch scoring.
- The API rejects incompatible feature-reference fingerprints/order.
- Events at or after `as_of` are excluded.
- Single and batch scores are exactly equal for the same history and cutoff.
- The production image omits model dependencies/artifacts and returns 503 for scoring.

## Lecturer-lab alignment

The official AML Lab 2 sequence—audit, clean/aggregate, leakage-by-lineage analysis, and a fitted pipeline—is adapted to the wallet/time setting. Its `SCORING_TS` rule is implemented as strict pre-cutoff snapshots. Its supervised metrics are not copied because this dataset has no verified target. See [`lab_traceability.md`](lab_traceability.md) for exact references and tests.

## Reproducibility conclusion

Local engineering and label-free results are reproducible under the pinned environment. Repository-only reproduction and lawful evidence redistribution remain blocked by unresolved dataset provenance/licence and ignored binary inputs.
