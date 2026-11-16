# Chapter 3 — Methodology (working draft)

## 3.1 Research design

The study uses a quantitative observational design with unsupervised anomaly analysis and reproducible software validation. Its unit is a wallet observed at a declared UTC scoring time. It does not infer fraud outcomes or causal effects.

## 3.2 Data

The private input is a 10,800-row, 18-column Solana DEX/swap-event CSV covering 2,312 wallet identifiers from January through November 2025. Its checksum is fixed in the audit. The provider, query, sample selection, enrichment process and licence remain unknown. A Phase 10 public-chain check corroborated selected first-row transaction fields but did not establish collection provenance or reuse rights.

## 3.3 Audit and preprocessing

The audit measures schema, literal missing values, timestamps, amounts, category consistency and transaction/instruction grain. Cleaning is deterministic: 10,798 rows are retained and two rows with nonpositive required amounts are quarantined; no row is silently deleted. Raw fields, source-row identity and reason codes are preserved. Missing fees remain missing, extreme USD values are retained, DEX names receive formatting-only normalisation and supplied prior-event/week fields are not trusted for modelling.

## 3.4 Point-in-time features

For every cutoff, the feature builder first filters `block_time < as_of`. It produces 29 registered features spanning event frequency, value, recency/inter-event timing, recent windows, token/DEX diversity, concentration, fee missingness, instruction context and observable-history coverage. Wallet and cutoff are metadata, not predictors. Single-event histories preserve unavailable inter-event statistics as missing.

The fixed cutoffs are:

- reference/training: 1 September 2025 UTC, 1,754 wallets;
- exploratory validation: 1 October 2025 UTC, 1,930 wallets; and
- descriptive holdout: 1 December 2025 UTC, 2,312 wallets.

## 3.5 Models

Isolation Forest is the provisional ranking detector. Its fitted pipeline includes training-reference preprocessing and a fixed seed. Novelty-enabled LOF provides a local-density comparison and robust MAD provides a transparent marginal-deviation baseline. All learned transforms are fitted only on the September reference. The artifact manifest stores configuration, feature order, cutoff, dependency versions and fingerprints.

## 3.6 Evaluation

No fraud label is available, so classification metrics are prohibited. Evaluation comprises:

- validation parameter sensitivity via Spearman rank correlation;
- detector rank agreement on the untouched descriptive holdout;
- top-10 and top-100 overlap;
- reference-to-later score distributions;
- repeated-wallet longitudinal rank persistence;
- later-entrant feature/coverage shift; and
- coverage- and volume-stratified score summaries.

The December report is descriptive and should not be repeatedly used for tuning. All 1,754 reference wallets recur later, so repeated-wallet results are not independent wallet generalisation.

## 3.7 Application and security validation

FastAPI exposes public health/readiness and authenticated feature/scoring routes. Firebase ID tokens, verified Google email and an explicit UID allowlist protect research requests. Payload size, event count, UTC and schema contracts are bounded. Local development may load only a checksum-pinned experimental artifact. Production configuration excludes it and returns `MODEL_NOT_APPROVED`. The React dashboard distinguishes observations, model outputs and synthetic examples.

## 3.8 Reproducibility

Fixed seeds, sorted outputs, versioned feature definitions, exact dependencies and SHA-256 manifests support deterministic local reproduction. Two clean runs yielded byte-identical audit, preprocessing, snapshot and model outputs. The raw file and artifact are ignored, so independent clone-only reproduction remains blocked until lawful acquisition is documented.

## 3.9 Ethics and validity

Wallet addresses are pseudonymous behavioural identifiers. Results must not be used to accuse, deanonymise or penalise persons. Internal validity is constrained by unknown sampling, missing labels, sparse histories and detector assumptions. External validity is constrained to one provenance-unresolved sample. Construct validity is limited because unusualness is not wash trading. No direct graph claim is permitted.

## 3.10 Student work required

**[DOCUMENT REQUIRED]** Insert authoritative data source and licence. **[STUDENT INPUT REQUIRED]** Confirm the final methodology language, ethical-review requirements and whether the institution requires a formal data-management statement.
