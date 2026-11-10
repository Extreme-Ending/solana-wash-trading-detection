# Phase 5A API contract

## Scope

The FastAPI service provides process health, prediction-readiness status, and descriptive point-in-time feature previews from user-supplied events. It does not load the Phase 4B experimental artifacts, train a model, call a blockchain provider, or return anomaly, fraud, wash-trading, or probability outputs.

Interactive OpenAPI documentation is available at `/docs` while the service is running. The machine-readable schema is at `/openapi.json`.

## Configuration

Configuration is read from environment variables. The tracked `.env.example` contains non-secret local examples; the application does not automatically read `.env` files.

| Variable | Default | Constraint |
|---|---:|---|
| `SOLANA_RISK_ENVIRONMENT` | `development` | Nonempty descriptive environment name |
| `SOLANA_RISK_CORS_ORIGINS` | `http://localhost:5173` | Comma-separated exact HTTP(S) origins; wildcard, paths, credentials, query and fragments are rejected |
| `SOLANA_RISK_MAX_EVENTS` | `100` | Integer from 1 to 10,000 |
| `SOLANA_RISK_MAX_REQUEST_BYTES` | `262144` | Integer from 1 byte to 10 MiB |

No model path, credential, API key, RPC endpoint, or client-supplied server path is accepted.

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

Reports whether prediction capability is available. Phase 5A always returns HTTP 503 because no approved prediction capability is configured.

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

The request shape is reserved for future interface stability, but Phase 5A never loads a model or returns a score. A valid request returns HTTP 503 with `MODEL_NOT_APPROVED`, using the same body as `/readyz`. Invalid request bodies may first return the normal HTTP 422 validation envelope.

## Status codes

| Status | Meaning |
|---:|---|
| 200 | Process health or successfully computed descriptive features |
| 413 | Raw request byte limit or event-count limit exceeded |
| 422 | Malformed schema, unsafe value, incompatible event set, or insufficient pre-cutoff history |
| 503 | Prediction capability unavailable |

## Local startup

```bash
python -m pip install -e '.[dev]'
uvicorn solana_risk.api.main:app --reload
```

Then open `http://127.0.0.1:8000/docs`. The service performs no wallet-address lookup and makes no external network request.
