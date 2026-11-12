# Phase 5B container validation results

## Validation status

**PASS — local container packaging and Compose deployment validated on 12 November 2026.**

This status applies only to container infrastructure and the existing descriptive API. Prediction readiness remains unavailable by design.

## Environment and image

| Item | Observed value |
|---|---|
| Docker Engine | `29.9.3`, Linux `x86_64` |
| Docker Compose | `v5.7.0` during initial capability check; Compose output later reported `5.7.1` |
| Base image | `python:3.11.14-slim-bookworm` pinned to multi-platform digest `sha256:65a93d69fa75478d554f4ad27c85c1e69fa184956261b4301ebaf6dbb0a3543d` |
| Built tag | `solana-wallet-risk-api:phase5b` |
| Final uncompressed image size | `345,274,935` bytes, approximately `329 MiB` |
| First uncached build-context transfer | approximately `388 KB` |
| Runtime identity | UID/GID `10001:10001` |

The final image is CPU-only. Its largest necessary application dependencies are pandas and its NumPy dependency, required by the shared Phase 3 feature builder. The image excludes scikit-learn, joblib, notebooks, and development/test packages.

## Commands and observed results

### Static and Python checks

```text
pytest -q tests/test_container_config.py
12 passed in 0.18s

docker compose -f docker-compose.yml config --quiet
exit 0

python3 -m compileall -q src tests scripts
exit 0
```

### Image build and direct-container smoke test

```bash
python3 scripts/container_smoke_test.py
```

Observed final result:

| Check | Result |
|---|---|
| Image build | PASS |
| Installed `solana_risk.api.main` import | PASS |
| Default internal port 8080 | PASS |
| Custom `PORT=9090` | PASS |
| `GET /healthz` | HTTP 200 |
| `GET /readyz` | HTTP 503 `MODEL_NOT_APPROVED` |
| `POST /v1/features/preview` | HTTP 200, 29 ordered features |
| `POST /v1/score` | HTTP 503 `MODEL_NOT_APPROVED` |
| `GET /openapi.json` | HTTP 200 |
| Runtime UID | `10001` |
| Docker health state | `healthy` |
| SIGTERM/graceful shutdown | exit code 0; `Application shutdown complete` observed |

The first smoke run exposed a test timing race: the HTTP health endpoint was already available before Docker had performed its scheduled health probe. The script was corrected to poll Docker health status, and the complete suite then passed. This was not an application or image failure.

### Compose deployment

```bash
docker compose -f docker-compose.yml up --detach --build --wait
```

Compose created one API container and one private network. `docker compose ps --format json` reported:

- state `running` and health `healthy`;
- `127.0.0.1:8080 -> 8080/tcp`;
- zero local volumes and no mounts; and
- image `solana-wallet-risk-api:phase5b`.

The same endpoint sequence returned `[200, 503, 200, 503, 200]` for health, readiness, feature preview, score, and OpenAPI respectively. `docker compose stop` produced Uvicorn shutdown logs ending in `Application shutdown complete`, after which `docker compose down` removed the temporary container and network successfully.

One host-side HTTP probe initially failed with `PermissionError: Operation not permitted` because the execution sandbox blocked socket creation. Repeating the identical localhost probe with local-network permission passed. This was an orchestration sandbox restriction, not a container failure.

## Security and content checks

Automated inspection confirmed:

- configured and effective non-root UID `10001`;
- exec-form production startup with no reload;
- read-only Compose root filesystem, small `/tmp` tmpfs, all capabilities dropped, and `no-new-privileges`;
- no Docker socket, dataset, artifact, or host-path mount;
- no installed `joblib` or `sklearn` runtime package;
- no `/app/nft.csv`, `/app/nft_trades.csv`, `.env`, `.agents`, `AGENTS.md`, `data`, `reports`, `artifacts`, `models`, `notebooks`, or `tests` path;
- no model artifact loading during startup;
- no credentials baked into Dockerfile or Compose; and
- `/healthz`, not the deliberately unavailable `/readyz`, used for health checks.

The build is reproducible at the pinned base-image and direct-dependency level. A future release should capture and review resolved transitive dependency versions or introduce an approved lock mechanism if byte-for-byte environment reconstruction is required.

## Scientific boundary and limitations

- Container success does not validate an anomaly detector or supervised classifier.
- The Phase 4B artifacts are absent from the image and remain unserved.
- No fraud probability, wash-trading verdict, or model score is returned.
- No authentication or distributed rate limiter is implemented; do not expose this image publicly yet.
- Cloud Run behavior, memory under load, concurrency, cold-start latency, vulnerability scanning, and regional cost were not tested because live cloud deployment is outside Phase 5B.
