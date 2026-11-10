# Phase 5A API implementation findings

## Result

The local FastAPI foundation implements four endpoints with explicit separation between process health, descriptive feature calculation, and unavailable prediction capability. No Phase 4B model module or artifact loader is imported by the API. Startup sets only a boolean not-ready state and performs no training, file read, deserialization, blockchain lookup, or external request.

## Module boundaries

| Module | Responsibility |
|---|---|
| `api/config.py` | Validated environment configuration and restricted CORS origins |
| `api/schemas.py` | Pydantic request/response models and UTC/value validation |
| `api/errors.py` | Stable error envelope without submitted input values |
| `api/middleware.py` | Raw request-byte enforcement before JSON parsing |
| `api/feature_service.py` | Thin adapter to the Phase 3 feature builder |
| `api/routes/health.py` | `/healthz` and `/readyz` |
| `api/routes/features.py` | `/v1/features/preview` and event-count limit |
| `api/routes/scoring.py` | Hard-gated `/v1/score` response |
| `api/main.py` | Application factory, lifecycle, CORS, middleware and routers |

## Feature parity evidence

The API does not reimplement feature formulas. It converts the validated Pydantic events to a DataFrame and calls `build_wallet_snapshots` from `solana_risk.features.build`. The response feature order comes directly from `MODEL_FEATURE_COLUMNS`; version and fingerprint come from `FEATURE_RULES_VERSION` and `feature_registry_sha256`.

The regression fixture supplies two historical events and one future event to both the HTTP endpoint and the Python builder. Every one of the 29 returned feature values is compared, including JSON `null` for unavailable values. A separate boundary fixture confirms that an event exactly equal to `as_of` and an event after it are excluded, leaving only the strictly prior event.

No statistical transform or model is fitted by feature preview. Wallet and cutoff remain response metadata, not feature values.

## Validation and security findings

- Wallet values are nonempty printable strings up to 128 characters; this validates transport safety without claiming on-chain authenticity.
- UTC is explicit. Naive timestamps, malformed timestamps and nonzero offsets are rejected.
- Numerical inputs are typed; strings, nonpositive required values, negative fees and nonfinite values are rejected.
- Extra fields are forbidden, preventing client-supplied server paths or undeclared attributes.
- One request cannot mix wallet identities or duplicate source row numbers.
- Event count and raw request bytes are independently configurable and enforced.
- CORS allows only configured exact HTTP(S) origins; wildcard origins are rejected at startup.
- Error rendering omits the Pydantic `input` value, avoiding reflection of complete wallet/event values.
- No credentials, API keys, artifact paths, public RPC calls or paid integrations exist.
- Uvicorn access logging may record method/path/status but the application does not log request bodies or full wallet identifiers.

## Readiness and scoring gate

`/healthz` returns 200 whenever the process can respond. `/readyz` and a valid `/v1/score` request return 503 with `MODEL_NOT_APPROVED`. The API source contains no artifact path and does not call `joblib.load`. Tests monkeypatch `joblib.load` to fail and prove that health, readiness and feature preview still operate.

The Phase 4B anomaly artifacts remain local research outputs. They are not exposed through the API and no score is reformatted as a fraud outcome or probability.

## Lecturer-lab adaptation

The verified lecturer `lab10_fastapi/api/main.py` demonstrates a Pydantic input model, FastAPI-generated documentation, feature ordering and loading a serialized bundle once. `fraud_mlops/api/main.py` similarly separates a health endpoint and model metadata, while `fraud_mlops/tests/test_api.py` exercises health, prediction and missing-field behavior with an HTTP client.

Phase 5A retains typed schemas, generated OpenAPI, modular routing, feature-order discipline and automated endpoint testing. It deliberately does not copy eager `joblib.load`, unconditional prediction, random-training assumptions, or fraud-probability output because this repository has no approved prediction capability. It adds separate readiness semantics, strict UTC/event-history boundaries, shared feature engineering, bounded requests, restricted CORS and structured not-ready errors.

Lecturer checkout consulted: commit `6a0b7e92ab4ffb6f168c08295eb378c19a0109f7`.

## Limitations

- The service accepts user-supplied events but cannot independently verify their origin, completeness or on-chain authenticity.
- It has no authorized wallet-address event provider and cannot score an address alone.
- Feature preview describes only the submitted history and is not evidence of wash trading.
- Prediction remains unavailable pending methodological and artifact approval.
- Authentication, rate limiting across requests, Docker, Compose, React, Firebase and cloud deployment are not part of Phase 5A.
- This phase provides an application foundation, not a deployed prediction service.
