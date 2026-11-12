# Phase 5B containerization and local deployment

## Scope and readiness boundary

The container packages the Phase 5A FastAPI application for local demonstration. It provides process health and descriptive feature preview, but it does not contain or load an experimental model artifact. `/readyz` and `/v1/score` deliberately remain HTTP 503 `MODEL_NOT_APPROVED`. A healthy container is therefore infrastructure evidence, not evidence that a fraud or anomaly model is approved for serving.

No frontend, database, blockchain provider, CI/CD deployment, or cloud resource is part of Phase 5B.

## Image design

The root `Dockerfile` uses two stages:

1. A builder creates the project wheel and resolves the `api` dependency extra from `pyproject.toml`.
2. The runtime stage receives only the installed API environment. It does not receive the wheelhouse, repository checkout, tests, notebooks, datasets, reports, or model artifacts.

The base is the official multi-platform `python:3.11.14-slim-bookworm` image pinned to digest `sha256:65a93d69fa75478d554f4ad27c85c1e69fa184956261b4301ebaf6dbb0a3543d`. The patch tag explains the intended runtime; the digest prevents an unnoticed base change. Updating either is a deliberate maintenance action followed by a clean build and the complete smoke suite. Direct project dependencies are pinned in `pyproject.toml`; resolved transitive wheels should be reviewed whenever the image is rebuilt for a release.

The runtime:

- installs `pandas` plus the `api` extra (`fastapi`, `pydantic`, and `uvicorn`), excluding Jupyter, pytest, joblib, and scikit-learn;
- runs as numeric UID/GID `10001:10001` with no login shell;
- starts through exec-form `CMD ["python", "-m", "solana_risk.api.run"]`;
- binds Uvicorn to `0.0.0.0` without auto-reload;
- reads `PORT`, defaulting to `8080` and rejecting invalid ports;
- exposes a `/healthz` Docker health check rather than treating prediction readiness as container health;
- writes logs to stdout/stderr and does not log request bodies; and
- starts normally with no model artifact.

The `.dockerignore` excludes Git metadata, private steering instructions, prompts, secrets, environments, tests, raw and processed data, reports, notebooks, experimental artifacts, caches, and frontend outputs. The Dockerfile uses explicit `COPY` statements instead of `COPY .`.

## Runtime configuration

| Variable | Container default | Purpose |
|---|---:|---|
| `PORT` | `8080` | Uvicorn listener; Cloud Run supplies this variable |
| `SOLANA_RISK_ENVIRONMENT` | `production` in the image; `development` in Compose | Descriptive environment name |
| `SOLANA_RISK_CORS_ORIGINS` | `http://localhost:5173` | Comma-separated exact HTTP(S) origins; never `*` |
| `SOLANA_RISK_MAX_EVENTS` | `100` | Maximum events in one API request |
| `SOLANA_RISK_MAX_REQUEST_BYTES` | `262144` | Maximum raw request-body bytes |

`.env.example` contains non-secret examples. The application does not load `.env` itself. Compose may interpolate exported shell values or an untracked local `.env`, but only the five named variables above are passed to the service.

## Build and run directly

From the repository root:

```bash
docker build --tag solana-wallet-risk-api:phase5b .
docker run --rm \
  --name solana-wallet-risk-api \
  --publish 127.0.0.1:8080:8080 \
  --read-only \
  --tmpfs /tmp:size=16m,mode=1777 \
  --cap-drop ALL \
  --security-opt no-new-privileges:true \
  solana-wallet-risk-api:phase5b
```

To test a different internal port:

```bash
docker run --rm \
  --publish 127.0.0.1:9090:9090 \
  --env PORT=9090 \
  solana-wallet-risk-api:phase5b
```

## Docker Compose workflow

The Compose file defines one API service, binds only the local loopback interface, mounts no host path or Docker socket, drops all Linux capabilities, enables `no-new-privileges`, uses a read-only root filesystem with a small `/tmp` tmpfs, and retains scoring-disabled defaults.

```bash
docker compose config --quiet
docker compose up --detach --build --wait
docker compose ps
docker compose logs --follow api
```

Check the service:

```bash
curl --fail http://127.0.0.1:8080/healthz
curl --include http://127.0.0.1:8080/readyz
curl --fail http://127.0.0.1:8080/openapi.json
```

`/readyz` is expected to return 503. Test the full contract, including synthetic feature preview and unavailable scoring, with:

```bash
python3 scripts/container_smoke_test.py --skip-build
```

That script starts its own containers and therefore requires port 8080 to be free; stop Compose first if necessary.

Stop and remove the local Compose resources:

```bash
docker compose down
```

Rebuild after source or dependency changes:

```bash
docker compose build --no-cache api
docker compose up --detach --force-recreate --wait
```

## Future Google Cloud Run compatibility

The image already listens on the platform-provided `PORT`, keeps state out of the filesystem, logs to stdout/stderr, and handles SIGTERM cleanly. For an initial CPU-only academic demonstration, a provisional starting assumption is 1 vCPU, 512 MiB memory, request-based CPU, minimum instances 0, maximum instances 1, and a short request timeout. These are planning assumptions, not measured production sizing; cold-start latency and peak memory must be measured before deployment.

Scale-to-zero is compatible because startup performs no training, download, external lookup, or artifact deserialization. A cold instance only imports the installed application. Requests remain bounded by the application byte/event limits, though a future public service would additionally need platform-level authentication and rate controls.

After explicit student approval, a release would require a reviewed immutable image tag, an approved Artifact Registry repository, authenticated image upload, and a new Cloud Run revision referencing that image. Configure the exact deployed frontend origin through `SOLANA_RISK_CORS_ORIGINS`; do not use a wildcard. Keep the service private until its access policy is separately reviewed. Cloud Run supplies `PORT`; no credentials belong in the image or Compose file. Verify region pricing, registry storage, logging retention, egress, memory, concurrency, and budget alerts immediately before provisioning.

Phase 5B neither creates those resources nor authorizes a cloud deployment.
