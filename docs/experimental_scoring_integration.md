# Phase 8A–8B experimental scoring integration

## Scope and status

Phase 8A exposes one existing Phase 4B detector for authenticated **local research use only**. Phase 8B applies that same loaded detector to bounded, isolated wallet histories and ranks the resulting scores within one request. Neither phase retrains a model, promotes an artifact, chooses a fraud threshold, flags a wallet as fraudulent, deploys a service, or alters the production container. The score is an unsupervised, model-specific ranking signal: higher means more unusual relative to the September 2025 training reference.

Isolation Forest is the provisional integration candidate because the Phase 4B evidence found stable validation ranks across the predeclared tree-count and sample-size alternatives. The robust MAD detector remains a transparent comparison and LOF remains a disagreement diagnostic. Stability does not establish outcome validity, and no labelled performance metric exists.

## Trust boundary

Experimental loading is disabled by default. It is possible only when all of the following are true:

1. `SOLANA_RISK_ENVIRONMENT=development`;
2. `SOLANA_RISK_ENABLE_EXPERIMENTAL_SCORING=true`;
3. the server is given explicit artifact and manifest paths;
4. a 64-character expected SHA-256 is configured;
5. the manifest digest equals that configured value and the artifact bytes hash to it;
6. the manifest and bundle agree on experiment status/version, training cutoff, package versions, feature-rule version, registry fingerprint and exact 29-field order; and
7. the selected object is a fitted `Pipeline` containing the expected imputer and Isolation Forest with 29 named inputs.

The manifest is parsed and the digest is verified before `joblib.load`. This matters because joblib artifacts use Python object serialization and must never be loaded from an untrusted source. Symlinked files are rejected. Artifact paths are server configuration and cannot be supplied in an API request.

Failure is closed: a missing, tampered or incompatible artifact produces HTTP 503 `EXPERIMENTAL_MODEL_UNAVAILABLE` without exposing a filesystem path or deserialization detail. Scoring errors produce HTTP 503 `EXPERIMENTAL_SCORING_FAILED`. The API never trains or repairs an artifact at startup.

## Point-in-time scoring contract

`POST /v1/score` accepts the same one-wallet event schema as feature preview and first invokes the shared Phase 3 builder. Only events satisfying `block_time < as_of` contribute to the 29 registered inputs. At-cutoff and later events are counted as excluded. An `as_of` earlier than the fitted training reference is rejected with HTTP 422 `SCORING_TIME_PRECEDES_MODEL_REFERENCE`; using a later-trained reference for an earlier decision would violate temporal interpretation.

The response includes:

- a finite `anomaly_score` with explicit direction and model-specific units;
- `methodology_status=experimental_unsupervised_research_only`;
- `model_id=isolation_forest` and artifact model version;
- training cutoff, feature rules version and registry fingerprint;
- supplied, included and excluded event counts;
- observable history length and warnings for incomplete/sparse history; and
- an explicit statement that the value is not a probability, label, fraud determination, or evidence of wash trading.

There is no threshold, class, severity band, percentile, cross-wallet normalization or automatic wallet flag. Scores from other algorithms are not comparable by magnitude.

## Batch scoring and review-budget contract

Authenticated `POST /v1/score/batch` accepts one explicit UTC `as_of`, 1–20 unique wallet-history groups, at most 100 events across the batch, at most 50 events in one group, and an optional integer review budget from 1 to 20. The existing 256 KiB raw request limit also applies. The maximum returned ranking is therefore 20 wallets. Authentication, verified-email/provider checks, UID authorization and per-instance rate limiting run before body parsing or feature work.

Each wallet is passed independently through the same Phase 3 feature builder and fitted Phase 4B pipeline as `POST /v1/score`. Only `block_time < as_of` contributes. The model is loaded once at application startup and receives one matrix for all eligible wallet snapshots; no artifact is loaded per wallet and no external data is fetched. Equivalent one-wallet inputs produce the same numeric score from the single and batch paths.

Results are sorted by descending anomaly score, then by wallet identifier for a deterministic tie. The rank is relative only to the successfully scored wallets in that submitted batch. Input wallet order and event order do not change the result. `review_budget` selects the first N ranked wallets as manual-review candidates and is reduced to the scored count when necessary; it never changes scores and is not a model threshold.

The partial-failure policy is explicit:

- malformed schema values, invalid identifiers/timestamps/numerics, duplicate wallet groups, pre-training scoring time, review-budget overflow, byte/total/per-wallet limits, missing authentication, or unavailable/incompatible artifacts fail the whole request;
- an empty group, an event whose wallet differs from its group, duplicate source row, exact duplicate event, no pre-cutoff history, or wallet-local feature-input failure rejects that wallet only;
- exact event duplicates are rejected rather than silently removed, while repeated transaction hashes with distinct instruction records remain permitted; and
- if no wallet is scorable, the request fails with `NO_SCORABLE_WALLETS` and the rejection details.

The work has no separate wall-clock interrupt inside the synchronous feature/model call. Instead, input size, wallet count, returned rows and request rate are bounded, and scoring performs no network I/O. A future hosted service would require measured timeout and concurrency validation before this limit could be described as an enforceable processing-time guarantee.

## Local startup

Install local model and API dependencies. The tracked production Dockerfile deliberately installs only the `api` extra and cannot load this artifact.

```bash
python -m pip install -e '.[api,models]'
python -m solana_risk.features.build \
  --as-of 2025-09-01T00:00:00Z \
  --as-of 2025-10-01T00:00:00Z \
  --as-of 2025-12-01T00:00:00Z
python -m solana_risk.models.train_anomaly
sha256sum artifacts/experimental/anomaly_models.joblib
```

Training reads the registered snapshot file and writes both the joblib bundle and expanded manifest under the Git-ignored `artifacts/experimental/` directory. It is an explicit offline command, never an API startup/request side effect.

Set the existing Firebase project/UID configuration plus these development-only variables using the digest printed by `sha256sum`:

```bash
export SOLANA_RISK_ENVIRONMENT=development
export SOLANA_RISK_ENABLE_EXPERIMENTAL_SCORING=true
export SOLANA_RISK_EXPERIMENTAL_MODEL_ARTIFACT=artifacts/experimental/anomaly_models.joblib
export SOLANA_RISK_EXPERIMENTAL_MODEL_MANIFEST=artifacts/experimental/anomaly_models_manifest.json
export SOLANA_RISK_EXPERIMENTAL_ARTIFACT_SHA256='<verified 64-character digest>'
uvicorn solana_risk.api.main:app --host 127.0.0.1 --port 8080
```

With a current Firebase ID token and a JSON file matching the request shown in the API contract, make an authenticated local request:

```bash
export FIREBASE_ID_TOKEN='<current Firebase ID token>'
curl --fail-with-body \
  --request POST \
  --header "Authorization: Bearer ${FIREBASE_ID_TOKEN}" \
  --header 'Content-Type: application/json' \
  --data-binary @/path/to/score-request.json \
  http://127.0.0.1:8080/v1/score
```

For batch scoring, use a body with `as_of`, `wallet_histories` and optional `review_budget`, then send it to `/v1/score/batch` with the same authorization header. The repository includes a deterministic offline check using three clearly synthetic behaviours and the trusted local artifact:

```bash
python scripts/demonstrate_batch_scoring.py \
  --artifact artifacts/experimental/anomaly_models.joblib \
  --manifest artifacts/experimental/anomaly_models_manifest.json \
  --sha256 "$(sha256sum artifacts/experimental/anomaly_models.joblib | cut -d' ' -f1)"
```

With the local Phase 4B.1 artifact digest `737b1358a4907707f70f7c0cb34213902cd08f4685417c4da4ce8be716bf5af6`, the verified run ranked the synthetic bursty, steady and sparse histories at `0.7112287827056774`, `0.5244905161109438` and `0.45179068711851816`. A review budget of two selected the first two. An immediate repeat was identical at the response-model level, and each score exactly equalled its single-wallet result. These synthetic outputs demonstrate software behavior only, not real-world performance or misconduct.

To reproduce a score, keep the artifact SHA-256, manifest, pinned Python packages and request bytes unchanged, then repeat the request. Automated tests load the same synthetic artifact twice and require the complete response—including the numeric score—to be identical.

The artifact and manifest remain generated, local and Git-ignored. The application does not automatically read `.env`; values must be exported by the student-operated shell. Returning `SOLANA_RISK_ENABLE_EXPERIMENTAL_SCORING=false` restores the normal 503 gate.

## Production and container boundary

`experimental_scoring_allowed` is false for every environment except `development`, even if the enable flag and paths are present. Production therefore returns `MODEL_NOT_APPROVED`, does not import the model-serving module and does not deserialize an injected scorer. `/readyz` also remains 503 because the experimental local path is not production readiness.

The production Dockerfile, Compose definition and Cloud Run plan are unchanged: they contain no `joblib`, scikit-learn, data, model artifact or artifact mount. Phase 8A–8B performs no Firebase or Google Cloud mutation.

## Frontend behavior

The authenticated dashboard keeps the one-wallet `/v1/score` flow and adds a separate batch form for one cutoff, wallet-history JSON and a review budget. The batch section displays only schema-validated API output: rank, raw score, history count/duration, review-candidate status, batch warnings and explicit wallet-local rejections. It has loading, authentication, disabled-model and safe error states. It does not append a percent sign, create score bands, hide rejected groups, or convert a score/rank into a fraud label. Existing descriptive feature cards and charts remain separate and unchanged.

## Limitations

- Submitted events are user-supplied and are not authenticated against an on-chain provider.
- Incomplete history can change counts, recency, coverage and therefore the score.
- The training population contains DEX swap events and has no independently verified fraud outcome.
- Repeated wallets and entrant coverage shift limit Phase 4B interpretation.
- A score is relative to one historical reference and has no calibrated probability meaning.
- A batch rank depends on which other eligible wallets were submitted and is not an absolute risk ordering.
- Review-budget membership expresses analyst capacity only and has no validated decision-threshold meaning.
- The local artifact is not a production release and is intentionally absent from Git and Docker.
