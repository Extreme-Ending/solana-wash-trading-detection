# syntax=docker/dockerfile:1

# The patch-level tag documents the runtime and the digest makes rebuilds
# deterministic until this value is deliberately reviewed and updated.
ARG PYTHON_IMAGE=python:3.11.14-slim-bookworm@sha256:65a93d69fa75478d554f4ad27c85c1e69fa184956261b4301ebaf6dbb0a3543d

FROM ${PYTHON_IMAGE} AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

COPY pyproject.toml README.md ./
COPY src/ ./src/

# Build the project and only its API extra into an isolated wheelhouse.
RUN python -m pip wheel --no-cache-dir --wheel-dir /wheels ".[api]"
RUN python -m pip install --no-cache-dir --no-compile --no-index \
        --find-links=/wheels --prefix=/install \
        "solana-wallet-risk[api]==0.0.0"

FROM ${PYTHON_IMAGE} AS runtime

LABEL org.opencontainers.image.title="Solana wallet feature API" \
      org.opencontainers.image.description="Firebase-authenticated descriptive FastAPI service with scoring disabled" \
      org.opencontainers.image.source="https://github.com/Extreme-Ending/solana-wash-trading-detection"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080 \
    SOLANA_RISK_ENVIRONMENT=production \
    SOLANA_RISK_CORS_ORIGINS=http://localhost:5173 \
    SOLANA_RISK_MAX_EVENTS=100 \
    SOLANA_RISK_MAX_REQUEST_BYTES=262144

WORKDIR /app

RUN groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid appuser --no-create-home \
        --home-dir /nonexistent --shell /usr/sbin/nologin appuser

COPY --from=builder /install/ /usr/local/

USER 10001:10001

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\", \"8080\")}/healthz', timeout=3)"]

CMD ["python", "-m", "solana_risk.api.run"]
