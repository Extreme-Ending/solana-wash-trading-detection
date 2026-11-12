"""Production container entry point with Cloud Run-compatible port handling."""

from __future__ import annotations

import os
from collections.abc import Mapping

import uvicorn


def port_from_env(environ: Mapping[str, str] | None = None) -> int:
    """Return a validated TCP port, defaulting to Cloud Run's conventional 8080."""

    values = os.environ if environ is None else environ
    raw_port = values.get("PORT", "8080")
    try:
        port = int(raw_port)
    except ValueError as exc:
        raise ValueError("PORT must be an integer between 1 and 65535") from exc
    if not 1 <= port <= 65_535:
        raise ValueError("PORT must be an integer between 1 and 65535")
    return port


def main() -> None:
    """Start one production Uvicorn process without reload or model loading."""

    uvicorn.run(
        "solana_risk.api.main:app",
        host="0.0.0.0",
        port=port_from_env(),
        reload=False,
        access_log=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
