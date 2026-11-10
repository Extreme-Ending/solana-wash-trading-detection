"""Application factory for the Phase 5A FastAPI service foundation."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from solana_risk.api.config import Settings
from solana_risk.api.errors import install_error_handlers
from solana_risk.api.middleware import RequestSizeLimitMiddleware
from solana_risk.api.routes import features, health, scoring


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create an app with no model deserialization or training side effects."""

    selected = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        application.state.prediction_available = False
        yield
        application.state.prediction_available = False

    application = FastAPI(
        title=selected.service_name,
        version=selected.api_version,
        description=(
            "Descriptive point-in-time wallet feature previews. Process health is separate "
            "from prediction readiness; model scoring is unavailable."
        ),
        lifespan=lifespan,
    )
    application.state.settings = selected
    application.state.prediction_available = False
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(selected.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Accept"],
    )
    application.add_middleware(
        RequestSizeLimitMiddleware,
        max_bytes=selected.max_request_bytes,
    )
    install_error_handlers(application)
    application.include_router(health.router)
    application.include_router(features.router)
    application.include_router(scoring.router)
    return application


app = create_app()
