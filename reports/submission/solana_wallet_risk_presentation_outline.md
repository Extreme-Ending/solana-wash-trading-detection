# Solana Wallet Risk presentation outline

## Slide 1: Solana Wallet Risk

Unsupervised Wallet Anomaly Detection on Solana.

Speaker focus: Introduce the system as anomaly analysis over supplied DEX histories. Do not describe it as verified fraud detection.

## Slide 2: Problem and objectives

- Solana DEX activity is high-volume, temporal and sparsely labelled.
- Build leakage-safe wallet snapshots at explicit scoring times.
- Compare three unsupervised anomaly concepts.
- Deliver reproducible analysis through an authenticated application.

Speaker focus: Explain why missing verified outcomes rule out classification accuracy.

## Slide 3: Dune Analytics dataset

- 10,800 events, 18 columns, 2,312 wallets and 9,221 transaction hashes.
- January to November 2025 UTC.
- DEX swap semantics, not NFT marketplace-sale semantics.
- Exact query, extraction procedure and licence remain unavailable.

Speaker focus: Raw data remains private because redistribution permission is not established.

## Slide 4: End-to-end pipeline

Audit, preprocessing, point-in-time features, chronological training, evaluation, artifact validation and API inference.

Speaker focus: Training is local and offline. The API never trains on a request.

## Slide 5: Data quality and preprocessing

- 10,798 retained, two quarantined and zero silently removed.
- Missing fees remain missing.
- Repeated transaction hashes are preserved when instruction grain differs.
- Large USD values are retained as review flags.

Speaker focus: Relate the choices to the lecturer's audit-before-treatment principles.

## Slide 6: Features and temporal design

- 29 registered wallet features.
- Strict `block_time < as_of` rule.
- 1,754 training, 1,930 validation and 2,312 holdout snapshots.
- All 1,754 training wallets recur later; entrants are reported separately.

Speaker focus: Random row splitting would hide temporal dependence.

## Slide 7: Models compared

- Isolation Forest: nonlinear global isolation ranking.
- Novelty LOF: local-density comparison.
- Robust MAD: transparent marginal-deviation baseline.

Speaker focus: All transformations are fitted on the September reference only.

## Slide 8: Model selection and evaluation

- Isolation Forest sensitivity correlations: 0.9923 to 0.9980.
- Holdout rank correlation with robust MAD: 0.8662.
- Holdout rank correlation with LOF: 0.0488.
- All-three overlap: 0 at top 10 and 7 at top 100.

Speaker focus: Stability and agreement are not detection accuracy.

## Slide 9: Application architecture

React and Firebase Hosting, Google sign-in, FastAPI on Cloud Run, UID authorization, shared feature builder and checksum-verified Isolation Forest.

Speaker focus: Firebase tokens authenticate to FastAPI. They do not automatically grant Cloud Run IAM access.

## Slide 10: Live demonstration

- Open the live application.
- Sign in with an approved Google account.
- Load the clearly labelled synthetic example.
- Run single and batch analysis.
- Explain score, rank, review budget and feature context.

Speaker focus: Do not display tokens, private account information or raw research rows.

## Slide 11: Results and limitations

- Deterministic processing and artifact reproduction passed.
- Detector rankings differ materially.
- No verified fraud labels or direct counterparty edges exist.
- Source query, licence and clone-only acquisition remain unresolved.

Speaker focus: A review candidate is not a confirmed fraudulent wallet.

## Slide 12: Conclusion

- The project delivers a reproducible anomaly-ranking workflow and secured web application.
- Isolation Forest is the most stable tested operational ranker.
- Stronger claims require lawful provenance, independent outcomes and relational evidence.

Speaker focus: Close on scientific honesty, reproducibility and reviewer-oriented use.
