# Research claims and limitations

## Supported claims

Repository evidence supports the following statements:

- The private input contains 10,800 Solana wallet-attributed DEX swap events for 2,312 wallet identifiers between January and November 2025.
- Deterministic preprocessing retains 10,798 events and quarantines two records with explicit reasons.
- The point-in-time builder produces 29 registered features using only `block_time < as_of`.
- Three unsupervised methods were fitted on the 1 September 2025 reference and compared on later cumulative snapshots.
- Isolation Forest produced stable validation rankings across the tested tree and sample settings and was selected for application scoring.
- The model artifact and manifest are reproducible in the pinned environment and are validated before API loading.
- The application can score and rank bounded, user-supplied wallet histories for manual review.

## Interpretation boundary

An anomaly score indicates that a wallet snapshot differs from the training reference according to one fitted model. It is not a fraud probability, legal conclusion, confirmed wash-trading label, or estimate of malicious prevalence. A high rank is a candidate for investigation only.

## Data limitations

- The dataset was extracted from Dune Analytics query 6561080 in multiple batches of approximately 1,000 rows. The query was executed again after the original extraction, so its currently visible SQL should not be treated as a preserved snapshot of the extraction-time query. The exact historical SQL revision, execution identifiers, parameters, extraction timestamps, and data-sharing permission remain unrecorded.
- The file contains no independently verified fraud outcome, case evidence, or evidence timestamp.
- No direct buyer, seller, sender, receiver, or counterparty-wallet edge is present.
- Wallet histories are sparse. Most wallets occur in one event month, and later entrants have shorter observable histories.
- The dataset ends on 30 November 2025, so it cannot support a later outcome window after the December scoring cutoff.
- The application analyzes supplied events and does not establish their completeness or retrieve live chain history.

## Evaluation limitations

- Precision, recall, accuracy, PR-AUC, MCC, calibration, and fraud-detection effectiveness cannot be measured without verified outcomes.
- All 1,754 training wallets recur in the later cumulative snapshots. Full-period comparisons are longitudinal rather than wallet-independent tests.
- Rank agreement and top-K overlap compare algorithms, not correctness.
- Sensitivity checks cover a predeclared set of parameter alternatives and do not prove stability under every dataset or feature representation.
- Correlated features and coverage indicators can influence detector rankings.
- Synthetic demonstration histories validate software behavior only.

## Operational limitations

- Access to protected live analysis requires Google sign-in and an approved Firebase UID.
- Cloud Run platform reachability is separate from FastAPI authentication and authorization.
- The per-instance rate limiter is not a distributed abuse-control system.
- Model loading is intentionally unavailable if the artifact or configuration fails validation.
- Cloud Run reserves some paths ending in `z`; external monitoring therefore uses `/v1/health`, while `/healthz` remains a local Docker health route.

## Appropriate use

Use results to inspect supplied DEX histories, compare wallets within a submitted batch, and prioritize analyst review. Do not use the system alone to accuse a wallet owner, block a transaction, report confirmed fraud, or claim validated wash-trading detection.

## Evidence needed for stronger claims

Outcome evaluation would require independently verified wallet labels for the same transaction domain, a clear label definition, evidence and knowledge timestamps, wallet identity matching, documented adjudication, and enough positives across chronological splits. Direct coordination analysis would additionally require time-bounded wallet-to-wallet relationship evidence.
