# Academic demonstration script

## Before the presentation

- Run the complete Phase 9 validation and retain terminal output privately.
- Confirm `nft.csv`, snapshot, artifact and manifest hashes.
- Start the authenticated development API and Vite frontend using ignored local configuration.
- Sign in once with the approved Google account; do not expose tokens or UID values.
- Keep `reports/phase9/` and this script open as offline fallbacks.
- Close unrelated terminals, cloud consoles and secret-bearing files.
- State at the beginning that the source is DEX data and that no verified fraud labels exist.

## Concise 10-minute demonstration

### 0:00–1:00 — Problem and evidence boundary

Talking points:

- The original topic concerns wash-trading risk, but the supplied schema contains DEX swap events rather than verified NFT sales.
- No independent fraud target is available, so the implemented objective is point-in-time anomaly ranking.
- Anomaly means statistically unusual relative to a fitted reference, not fraudulent.

Screen: dashboard overview and **Verified experimental snapshot** panel.

### 1:00–2:15 — Data and preprocessing

Command/screen:

```bash
sha256sum nft.csv
sed -n '1,100p' reports/preprocessing/preprocessing_summary.md
```

Talking points: 10,800 input, 10,798 retained, two quarantined, no silent removal; query 6561080 confirmed; extraction metadata and data-sharing permission incomplete. FastAPI is the primary API-first scoring service, while React is a JSON demonstration client rather than a complete commercial SaaS platform.

### 2:15–3:15 — Features and leakage

Screen: feature registry/Phase 9 cohort figure.

Talking points: wallet-at-UTC-cutoff unit, 29 registered features, strict `block_time < as_of`, no label or wallet identifier in model features, all 1,754 training wallets recur later.

### 3:15–4:30 — Model methodology

Screen: figures 03 and 04.

Talking points: Isolation Forest selected for bounded parameter stability; LOF and robust MAD are comparisons; weak LOF agreement shows detector dependence; no accuracy metric is possible.

### 4:30–6:00 — Feature preview and single score

Screen: load synthetic single-wallet example, preview 29 features, request local experimental score.

Talking points: user-supplied history, explicit UTC cutoff, same feature builder as training, score is unitless and checksum-pinned.

### 6:00–8:00 — Batch dashboard

Screen: load synthetic batch, request budget two, filter/sort, open wallet detail.

Talking points: rank is relative to the submitted batch; review capacity is not a threshold; median/IQR context is not SHAP or causal explanation; synthetic wallets test plumbing only.

### 8:00–9:00 — Evaluation

Screen: figures 01, 02 and 05.

Talking points: longitudinal dependence, new-wallet history shift, coverage/volume associations, detector disagreement.

### 9:00–10:00 — Conclusion

Talking points:

- Contribution: reproducible leakage-aware anomaly workflow plus secure local delivery.
- Not demonstrated: fraud effectiveness, NFT wash trading or coordination.
- Critical next evidence: extraction-time metadata, data-sharing permission and independent timestamped labels if supervised claims are desired.

## Detailed 20-minute technical demonstration

### 0:00–2:00 — Research framing

Use the entry assessment. Explain the DEX/NFT mismatch, lack of labels and the authorized anomaly framing. Avoid saying “detected wallets.” Say “ranked review candidates.”

### 2:00–4:00 — Reproducible audit

Run or show the fresh `/tmp` audit command. Explain raw checksum, missingness, repeated hashes versus instruction-grain events, two nonpositive amount records and quarantine preservation.

Expected: 10,800 rows and no mutation of `nft.csv`.

### 4:00–6:00 — Preprocessing and feature engineering

Show the cleaning reconciliation and feature report. Explain UTC parsing, deterministic ordering, canonical DEX mapping, recomputed prior-event gaps and strict pre-cutoff construction.

Expected: 10,798 clean records, 5,996 snapshots, 29 features.

### 6:00–8:30 — Experimental models

Open the model manifest. Explain training-only imputation/scaling, Isolation Forest configuration, novelty-enabled LOF and robust MAD. Emphasize that different model score magnitudes are not comparable.

### 8:30–11:00 — Evaluation evidence

Use the five Phase 9 figures:

1. repeated/new cohorts;
2. score summary shifts;
3. detector disagreement;
4. validation parameter sensitivity; and
5. coverage/volume context.

State the exact limitation beside every result. Do not show a confusion matrix or AUC slide.

### 11:00–13:00 — API and security

```bash
curl --fail http://127.0.0.1:8080/healthz
curl --include http://127.0.0.1:8080/readyz
```

Explain public health, protected preview/score routes, verified Firebase identity/UID, request bounds, checksum validation and production 503. Do not display an ID token.

### 13:00–17:00 — React walkthrough

- single-wallet feature preview and feature charts;
- experimental score with cutoff/history metadata;
- batch ranking, score distribution and review capacity;
- filters, deterministic sorts and full identifier detail;
- warning/rejection handling; and
- training median/IQR descriptive context.

Explicitly identify synthetic examples before loading them.

### 17:00–18:30 — Reproducibility and Docker

Show the Phase 9 manifest and test summary. Explain that the production Docker image excludes experimental artifact/model dependencies and deliberately reports scoring unavailable.

### 18:30–20:00 — Limitations and questions

End with missing extraction metadata and data-sharing permission, no labels/edges, repeated-wallet dependence, coverage shift, real Firebase acceptance and academic documentation gaps. Present the future label contract and secure deployment architecture as proposals, not completed work.

## Fallbacks

| Failure | Fallback that preserves integrity |
|---|---|
| Firebase popup/account unavailable | Show unauthenticated shell, then run `scripts/audit_local_integration.py`; disclose test-only verifier |
| Experimental artifact rejected | Show manifest/hash mismatch and regenerate offline; never bypass loader checks |
| API port unavailable | Use a documented alternate port and update Vite proxy/origin consistently, or use in-process integration audit |
| Frontend cannot start | Use production build/test results and Phase 9 figure SVGs; do not claim a live browser pass |
| Docker daemon unavailable | Show prior command/result as historical evidence only and say it was not rerun in the session |
| Internet unavailable | Use the already installed local app; do not attempt Google sign-in, and disclose that protected browser routes were not live-tested |
| Question asks whether a wallet is fraudulent | Answer that the system has no verified outcome and returns only a model-specific anomaly ranking |

## Phrases to use

- “supplied DEX swap-event sample”
- “experimental unitless anomaly score”
- “review candidate under the stated analyst budget”
- “descriptive feature context, not model attribution”
- “longitudinal diagnostic, not independent generalisation”

Avoid “fraud probability,” “confirmed wash trader,” “accuracy,” “prediction confidence,” or “production ready.”
