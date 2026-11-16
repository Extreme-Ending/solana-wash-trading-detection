# API contract through Phase 8C

## Scope

The FastAPI service provides process health, production-readiness status, descriptive point-in-time feature previews, an explicitly gated local experimental anomaly score, and bounded batch ranking. It never trains a model, calls a blockchain provider, returns a fraud/wash-trading class, or presents an anomaly score as a probability. The normal and all production configurations load no experimental artifact.

Interactive OpenAPI documentation is available at `/docs` in development, with the machine-readable schema at `/openapi.json`. `/docs`, `/redoc` and `/openapi.json` return 404 when `SOLANA_RISK_ENVIRONMENT=production`.

## Configuration

Configuration is read from environment variables. The tracked `.env.example` contains non-secret local examples; the application does not automatically read `.env` files.

| Variable | Default | Constraint |
|---|---:|---|
| `SOLANA_RISK_ENVIRONMENT` | `development` | Nonempty descriptive environment name |
| `SOLANA_RISK_CORS_ORIGINS` | `http://localhost:5173` | Comma-separated exact HTTP(S) origins; wildcard, paths, credentials, query and fragments are rejected |
| `SOLANA_RISK_MAX_EVENTS` | `100` | Integer from 1 to 10,000 |
| `SOLANA_RISK_MAX_BATCH_WALLETS` | `20` | Integer from 1 to 100; configured runtime ranking cap |
| `SOLANA_RISK_MAX_BATCH_EVENTS` | `100` | Integer from 1 to 10,000 |
| `SOLANA_RISK_MAX_BATCH_EVENTS_PER_WALLET` | `50` | Integer from 1 to 10,000 |
| `SOLANA_RISK_MAX_REQUEST_BYTES` | `262144` | Integer from 1 byte to 10 MiB |
| `SOLANA_RISK_FIREBASE_PROJECT_ID` | unset | Firebase/Google Cloud project ID; mandatory in production |
| `SOLANA_RISK_ALLOWED_UIDS` | unset | Comma-separated approved Firebase UIDs; mandatory and nonempty in production |
| `SOLANA_RISK_CHECK_REVOKED_TOKENS` | `true` | Strict boolean; must remain true in production |
| `SOLANA_RISK_RATE_LIMIT_REQUESTS` | `30` | Per-process protected requests per UID, 1–10,000 |
| `SOLANA_RISK_RATE_LIMIT_WINDOW_SECONDS` | `60` | Per-process window, 1–3,600 seconds |
| `SOLANA_RISK_ENABLE_EXPERIMENTAL_SCORING` | `false` | Strict boolean; effective only when environment is exactly `development` |
| `SOLANA_RISK_EXPERIMENTAL_MODEL_ARTIFACT` | unset | Server-side path to a trusted local generated joblib bundle |
| `SOLANA_RISK_EXPERIMENTAL_MODEL_MANIFEST` | unset | Server-side path to the matching generated manifest |
| `SOLANA_RISK_EXPERIMENTAL_ARTIFACT_SHA256` | unset | Expected 64-character SHA-256 pinned before deserialization |

Firebase Admin uses Google Cloud Application Default Credentials. No service-account key path, API key, RPC endpoint, or client-supplied server path is accepted. The experimental model paths are trusted server startup configuration only and never request fields. Development may start without Firebase settings so public health can be checked, but protected endpoints then fail closed with HTTP 503.

## Authentication and authorization

`/v1/features/preview`, `/v1/score` and `/v1/score/batch` require `Authorization: Bearer FIREBASE_ID_TOKEN`. Authentication is rejected at the protected-route boundary before JSON/schema processing. The Firebase Admin SDK verifies the signature, expiration, revocation/disabled-user state, issuer, and audience against the configured project. The application additionally requires matching `sub`/`uid`, a verified email, `google.com` as the sign-in provider, and membership in `SOLANA_RISK_ALLOWED_UIDS`. Tokens are never logged or returned.

The 30-request/60-second default is per UID **within one process**. It resets on restart and is not shared across Cloud Run instances, so it is a bounded application safeguard rather than a global quota or complete abuse control.

Missing, malformed, expired, wrong-project, wrong-issuer, or otherwise invalid credentials return HTTP 401 with `WWW-Authenticate: Bearer`. Authenticated users who fail the verified-email, Google-provider, or UID-allowlist policy receive HTTP 403. Missing server configuration or temporarily unavailable certificate verification returns HTTP 503. `/healthz` and `/readyz` remain public.

## Error envelope

Errors use one stable shape and do not echo submitted values:

```json
{
  "error": {
    "code": "REQUEST_VALIDATION_ERROR",
    "message": "Request validation failed.",
    "details": {
      "issues": [
        {
          "location": ["body", "events", "0", "amount_usd"],
          "message": "Input should be greater than 0",
          "type": "greater_than"
        }
      ]
    }
  }
}
```

## `GET /healthz`

Reports only that the application process is running. It does not depend on a model.

Response: HTTP 200

```json
{
  "status": "ok",
  "service": "Solana Wallet Feature Service",
  "version": "0.1.0"
}
```

## `GET /readyz`

Reports whether production prediction capability is available. It remains HTTP 503 because the local experimental path is not production readiness.

```json
{
  "error": {
    "code": "MODEL_NOT_APPROVED",
    "message": "Prediction capability is unavailable.",
    "details": {
      "prediction_available": false
    }
  }
}
```

## `POST /v1/features/preview`

Builds the registered Phase 3 wallet snapshot from complete user-supplied event records. The endpoint:

- requires an authorized Firebase user as described above;
- accepts exactly one wallet per request;
- requires explicit UTC `block_time` and `as_of` strings using `Z` or `+00:00`;
- requires unique positive `source_row_number` values;
- requires finite positive `amount_usd` and finite nonnegative `fee_usd` when supplied;
- uses only events satisfying `block_time < as_of`;
- reports how many at-cutoff or future events were excluded;
- fails with `INSUFFICIENT_HISTORY` if no strictly prior event exists;
- returns all 29 features in registry order; and
- identifies the source as user-supplied and unverified.

Wallet values are validated as bounded, nonempty, printable strings. The service does not claim that a submitted value is a genuine on-chain wallet. Token, transaction and DEX identifiers are similarly treated as unverified submitted strings.

Synthetic example request:

```json
{
  "as_of": "2025-02-01T00:00:00Z",
  "events": [
    {
      "source_row_number": 1,
      "wallet": "synthetic-wallet-001",
      "block_time": "2025-01-15T12:00:00Z",
      "block_slot": 1001,
      "tx_hash": "synthetic-transaction-001",
      "dex": "synthetic-dex",
      "token_pair": "TOKEN-A/TOKEN-B",
      "token_in": "synthetic-token-a",
      "token_out": "synthetic-token-b",
      "amount_usd": 125.5,
      "fee_usd": 0.25,
      "outer_instruction_index": 1,
      "inner_instruction_index": 0
    }
  ]
}
```

Response excerpt: HTTP 200

```json
{
  "status": "descriptive_features",
  "source": "user_supplied_unverified_events",
  "interpretation": "Descriptive point-in-time features only; they do not establish wash trading, fraud, intent or misconduct.",
  "wallet": "synthetic-wallet-001",
  "as_of": "2025-02-01T00:00:00Z",
  "supplied_event_count": 1,
  "included_historical_event_count": 1,
  "excluded_at_or_after_cutoff_count": 0,
  "feature_rules_version": "1.0.0",
  "feature_order": ["historical_event_count", "... 28 more registered names"],
  "features": {
    "historical_event_count": 1,
    "inter_event_mean_seconds": null
  }
}
```

The real response contains all 29 registered feature names. Missing inter-event values remain JSON `null`; the API does not fabricate gap history.

## `POST /v1/score`

The protected endpoint uses the same bounded one-wallet request as feature preview. By default and in production, an authorized request returns HTTP 503 `MODEL_NOT_APPROVED`. In an explicitly enabled `development` process, a checksum-pinned compatible Phase 4B artifact returns a finite experimental Isolation Forest score. It reuses the shared feature builder and excludes every event at or after `as_of`.

The successful response identifies `methodology_status=experimental_unsupervised_research_only`, the model/version, training cutoff, feature-rule version, registry fingerprint, history coverage, event counts, score direction and warnings. `is_probability` is always false. An `as_of` before the model training cutoff returns HTTP 422. Missing/tampered/incompatible local artifacts return HTTP 503 without leaking paths. See [`experimental_scoring_integration.md`](experimental_scoring_integration.md) for the loader and interpretation contract.

## `POST /v1/score/batch`

The protected local-development endpoint accepts this top-level shape:

```json
{
  "as_of": "2025-11-01T00:00:00Z",
  "review_budget": 2,
  "wallet_histories": [
    {
      "wallet": "synthetic-wallet-a",
      "events": [{
        "source_row_number": 1,
        "wallet": "synthetic-wallet-a",
        "block_time": "2025-10-20T10:00:00Z",
        "block_slot": 2001,
        "tx_hash": "synthetic-a-transaction-1",
        "dex": "synthetic-dex",
        "token_pair": "TOKEN-A/TOKEN-B",
        "token_in": "synthetic-token-a",
        "token_out": "synthetic-token-b",
        "amount_usd": 100.0,
        "fee_usd": 0.1,
        "outer_instruction_index": 1,
        "inner_instruction_index": 0
      }]
    },
    {
      "wallet": "synthetic-wallet-b",
      "events": [{
        "source_row_number": 1,
        "wallet": "synthetic-wallet-b",
        "block_time": "2025-10-31T23:59:00Z",
        "block_slot": 2002,
        "tx_hash": "synthetic-b-transaction-1",
        "dex": "synthetic-dex",
        "token_pair": "TOKEN-A/TOKEN-B",
        "token_in": "synthetic-token-a",
        "token_out": "synthetic-token-b",
        "amount_usd": 5000.0,
        "fee_usd": 0.1,
        "outer_instruction_index": 1,
        "inner_instruction_index": 0
      }]
    }
  ]
}
```

The event objects use the exact fields and validation shown for feature preview. Each group identifier must be unique. Event wallet values must match their group. One explicit UTC cutoff applies to every wallet, and only `block_time < as_of` contributes. Limits are 20 wallets, 100 total events, 50 events per wallet, and 256 KiB for the raw body; because at most 20 wallets can be scored, at most 20 ranking rows are returned. The endpoint performs no provider lookup, retraining or per-wallet model deserialization.

Eligible wallets are scored with the same 29-field builder and fitted pipeline as `/v1/score`, then ordered by descending score and ascending wallet identifier for ties. `review_budget` is optional, is limited to 20, and is clamped to the number of scored wallets. Selected rows are manual-review candidates only. The response always declares `is_probability=false` and includes:

- model/version, shared cutoff, training cutoff, score direction/units, feature-rule version and registry SHA-256;
- submitted/scored/rejected counts and requested/applied review budgets;
- a training-only reference summary for the exact 29 registered features, including its version, cutoff, snapshot fingerprint, wallet count and per-feature observed/missing counts, min/Q1/median/mean/Q3/max and binary/constant flags;
- ranked wallet, raw anomaly score, the exact 29 point-in-time feature values, included/excluded event counts, observable history, warnings and review-candidate boolean;
- separate wallet-local rejection code/message/count records; and
- `Experimental statistical anomalies requiring review; not confirmed wash trading or fraud.`

Invalid top-level schema, timestamp or numeric data, duplicate wallet groups, resource-limit violations, pre-training cutoff, authentication failure and missing/incompatible model artifacts fail the whole request. Empty histories, group/event wallet mismatch, duplicate source rows, exact duplicate event records, no pre-cutoff history and wallet-local feature-input errors reject only that wallet. Rejected data never contributes to another wallet. If all groups are rejected, HTTP 422 `NO_SCORABLE_WALLETS` is returned. Repeated transaction hashes are accepted when their instruction-level event records differ.

No inner wall-clock cancellation is claimed for the synchronous feature/model operation. Bounded inputs, bounded output, rate limiting and zero request-time external I/O provide the current resource control. Default and production configurations return HTTP 503 `MODEL_NOT_APPROVED` before any artifact is used.

The reference summary is computed only from the earliest-cutoff training partition when the ignored local artifact is generated. It contains aggregates, not raw training rows. The loader rejects a stale version, feature order/set, registry fingerprint, snapshot fingerprint, wallet count, nonfinite or unordered statistic, or incorrect binary/constant declaration. The frontend uses it only for descriptive median/IQR context; it is not an explanation of how Isolation Forest produced a score.

## Status codes

| Status | Meaning |
|---:|---|
| 200 | Process health, descriptive features, or explicitly enabled local experimental single/batch scoring |
| 401 | Firebase Bearer token missing, expired, malformed, or for the wrong project |
| 403 | Verified-email, Google-provider, or UID-allowlist authorization policy failed |
| 413 | Raw request byte, batch-wallet, event, per-wallet event, or review-budget limit exceeded |
| 422 | Malformed schema, unsafe value, incompatible event set, or insufficient pre-cutoff history |
| 429 | Per-instance authorized-UID request limit exceeded; response includes `Retry-After` |
| 503 | Production prediction unavailable, local artifact/scoring unavailable, or authentication configuration/verification unavailable |

## Local startup

```bash
python -m pip install -e '.[dev]'
uvicorn solana_risk.api.main:app --reload
```

Then open `http://127.0.0.1:8000/docs`. Token verification may fetch Google's public signing certificates and uses ADC; feature computation performs no wallet-address lookup or external provider call.
