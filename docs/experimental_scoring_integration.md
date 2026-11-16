# Phase 8A experimental scoring integration

## Scope and status

Phase 8A exposes one existing Phase 4B detector for authenticated **local research use only**. It does not retrain a model, promote an artifact, choose a fraud threshold, flag a wallet as fraudulent, deploy a service, or alter the production container. The score is an unsupervised, model-specific ranking signal: higher means more unusual relative to the September 2025 training reference.

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

To reproduce a score, keep the artifact SHA-256, manifest, pinned Python packages and request bytes unchanged, then repeat the request. Automated tests load the same synthetic artifact twice and require the complete response—including the numeric score—to be identical.

The artifact and manifest remain generated, local and Git-ignored. The application does not automatically read `.env`; values must be exported by the student-operated shell. Returning `SOLANA_RISK_ENABLE_EXPERIMENTAL_SCORING=false` restores the normal 503 gate.

## Production and container boundary

`experimental_scoring_allowed` is false for every environment except `development`, even if the enable flag and paths are present. Production therefore returns `MODEL_NOT_APPROVED`, does not import the model-serving module and does not deserialize an injected scorer. `/readyz` also remains 503 because the experimental local path is not production readiness.

The production Dockerfile, Compose definition and Cloud Run plan are unchanged: they contain no `joblib`, scikit-learn, data, model artifact or artifact mount. Phase 8A performs no Firebase or Google Cloud mutation.

## Frontend behavior

The existing authenticated dashboard sends the last validated event request to `/v1/score`. It supports four distinct states: no validated request, request in progress, expected disabled/unavailable response, and a schema-validated successful experimental result. It displays the raw finite model-specific value, metadata and warnings; it does not append a percent sign or convert the score into a fraud label. Existing descriptive feature cards and charts remain separate and unchanged.

## Limitations

- Submitted events are user-supplied and are not authenticated against an on-chain provider.
- Incomplete history can change counts, recency, coverage and therefore the score.
- The training population contains DEX swap events and has no independently verified fraud outcome.
- Repeated wallets and entrant coverage shift limit Phase 4B interpretation.
- A score is relative to one historical reference and has no calibrated probability meaning.
- The local artifact is not a production release and is intentionally absent from Git and Docker.
