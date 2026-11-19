# API contract

The FastAPI service exposes health, point-in-time feature generation, and checksum-gated anomaly scoring. Protected routes analyze only caller-supplied transaction histories. The API does not retrieve a wallet's on-chain history.

## Base URLs

- Local development: `http://127.0.0.1:8080`
- Frontend development proxy: `/api`
- Hosted frontend: configured through `VITE_API_BASE_URL`

Production disables OpenAPI and documentation routes. Development mode exposes `/docs` and `/openapi.json`.

## Routes

| Method and path | Access | Success behavior |
| --- | --- | --- |
| `GET /healthz` | Public | Process health only |
| `GET /v1/health` | Public | Hosted application health alias |
| `GET /readyz` | Public | Reports whether verified experimental scoring is available |
| `POST /v1/features/preview` | Protected | Builds one registered 29-feature snapshot |
| `POST /v1/score` | Protected | Returns one non-probabilistic anomaly score |
| `POST /v1/score/batch` | Protected | Scores and ranks a bounded submitted batch |

`/readyz` returns HTTP 200 only when scoring is explicitly enabled and the model bundle passes all integrity checks. It returns HTTP 503 with `MODEL_NOT_APPROVED` when scoring is disabled, or `EXPERIMENTAL_MODEL_UNAVAILABLE` when enabled configuration cannot load a valid artifact.

## Authentication

Protected calls require:

```http
Authorization: Bearer <Firebase ID token>
```

The backend verifies token signature, issuer, audience, expiration, subject, Firebase project, verified email status, Google provider identity, and revocation status. The token UID must also appear in `SOLANA_RISK_ALLOWED_UIDS`.

- Missing, malformed, expired, revoked, or wrong-project tokens return HTTP 401.
- A valid user who is not allowlisted returns HTTP 403.
- Missing production authentication configuration fails closed with HTTP 503.

Firebase Web configuration is public application configuration. Service-account keys and user tokens must never appear in frontend environment variables, source code, logs, or documentation.

## Event input

Each wallet history contains a wallet identifier, an explicit UTC `as_of` value, and DEX events. Required event fields follow the preprocessing and feature schemas. The feature builder includes only events where:

```text
block_time < as_of
```

At-cutoff and future events are counted as excluded and do not affect features or scores. The service treats submitted histories as unverified input and does not assert authenticity or completeness.

## Feature preview

`POST /v1/features/preview` uses the same implementation as offline feature generation. It returns wallet and cutoff metadata, event inclusion counts, all 29 feature values, and the fixed feature order. It loads no model and makes no anomaly or fraud claim.

## Single scoring

`POST /v1/score` builds the snapshot, applies stored training-median imputation, and scores it with the selected Isolation Forest. The response identifies the experimental methodology, model, training cutoff, artifact metadata, excluded events, and a unitless anomaly score.

Higher values mean more unusual relative to the training reference. The score is not a percentage, probability, classification, or universal threshold.

## Batch scoring

`POST /v1/score/batch` accepts explicitly separated wallet histories, scores each independently, and ranks valid results by descending score with deterministic tie handling. A caller supplies a bounded review capacity. The service marks only the corresponding highest-ranked returned wallets as review candidates.

Default limits are:

- 20 wallets per batch
- 100 events across the batch
- 50 events per wallet
- 256 KiB request body

Limits are deployment configuration and can be made stricter. Unsupported wallet histories are reported without fabricating a result for them. A review-candidate marker is a workflow aid, not a fraud label.

## Errors

Errors use a structured JSON body with a stable code, human-readable message, and optional details. Important statuses are:

| Status | Meaning |
| ---: | --- |
| 401 | Firebase authentication failed |
| 403 | Authenticated UID is not approved |
| 413 | Request or event limit exceeded |
| 422 | Schema, UTC, wallet isolation, or feature input validation failed |
| 429 | Per-instance protected-request limit exceeded |
| 503 | Authentication verification or model capability is unavailable |

The frontend provides separate handling for 401, 403, and 503 responses. It clears protected results on sign-out.

## Security controls

- Exact-origin CORS allowlist with the `Authorization` header permitted only for configured origins
- Request-size, wallet-count, and event-count limits
- Firebase revocation checking in production
- Per-instance rate limiting for approved protected requests
- Model checksum, manifest, version, cutoff, feature-order, and registry validation
- No runtime training and no unverified artifact fallback
- No raw request bodies or bearer tokens in application logs

The rate limiter is per instance, not a distributed quota. Platform traffic, Firebase verification calls, and invalid requests require separate monitoring and cost controls.
