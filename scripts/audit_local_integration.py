#!/usr/bin/env python3
"""Exercise the real local artifact through FastAPI with a test-only auth seam.

This audit intentionally does not contact Firebase or create a production auth bypass.
The application factory's existing verifier dependency is replaced only in this process,
in the same way as the authentication unit tests. No credential or token is logged.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import httpx

from solana_risk.api.auth import TokenExpiredError, TokenInvalidError
from solana_risk.api.config import Settings
from solana_risk.api.main import create_app
from solana_risk.features.build import MODEL_FEATURE_COLUMNS


class AuditTokenVerifier:
    """Deterministic verifier for local integration evidence; never used by production."""

    def verify(self, token: str) -> Mapping[str, Any]:
        if token == "expired-audit-token":
            raise TokenExpiredError
        if token != "valid-audit-token":
            raise TokenInvalidError
        uid = "phase8d-auditor"
        return {
            "aud": "phase8d-project",
            "iss": "https://securetoken.google.com/phase8d-project",
            "sub": uid,
            "uid": uid,
            "exp": time.time() + 300,
            "email": "local-audit@example.invalid",
            "email_verified": True,
            "firebase": {"sign_in_provider": "google.com"},
        }


def _event(wallet: str, row: int, timestamp: str, amount: float) -> dict[str, Any]:
    return {
        "source_row_number": row,
        "wallet": wallet,
        "block_time": timestamp,
        "block_slot": 500_000_000 + row,
        "tx_hash": f"synthetic-phase8d-transaction-{wallet}-{row}",
        "dex": "synthetic-dex",
        "token_pair": "TOKEN-A/TOKEN-B",
        "token_in": "synthetic-token-a",
        "token_out": "synthetic-token-b",
        "amount_usd": amount,
        "fee_usd": amount * 0.0025,
        "outer_instruction_index": 1,
        "inner_instruction_index": 0,
    }


def _histories() -> list[dict[str, Any]]:
    definitions = {
        "synthetic-bursty": [
            (1, "2025-10-31T23:30:00Z", 900.0),
            (2, "2025-10-31T23:40:00Z", 1_100.0),
            (3, "2025-10-31T23:50:00Z", 1_300.0),
        ],
        "synthetic-steady": [
            (11, "2025-10-10T00:00:00Z", 120.0),
            (12, "2025-10-20T00:00:00Z", 130.0),
            (13, "2025-10-30T00:00:00Z", 125.0),
        ],
        "synthetic-sparse": [(21, "2025-10-15T00:00:00Z", 30.0)],
    }
    return [
        {
            "wallet": wallet,
            "events": [_event(wallet, row, timestamp, amount) for row, timestamp, amount in rows],
        }
        for wallet, rows in definitions.items()
    ]


def _settings(artifact: Path, manifest: Path, digest: str, *, production: bool = False) -> Settings:
    return Settings(
        environment="production" if production else "development",
        firebase_project_id="phase8d-project",
        allowed_user_uids=frozenset({"phase8d-auditor"}),
        experimental_scoring_enabled=True,
        experimental_model_artifact=artifact,
        experimental_model_manifest=manifest,
        experimental_artifact_sha256=digest,
        rate_limit_requests=100,
    )


async def audit(artifact: Path, manifest: Path) -> dict[str, Any]:
    artifact = artifact.resolve()
    manifest = manifest.resolve()
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    verifier = AuditTokenVerifier()
    app = create_app(_settings(artifact, manifest, digest), token_verifier=verifier)
    transport = httpx.ASGITransport(app=app)
    authorization = {"Authorization": "Bearer valid-audit-token"}
    histories = _histories()
    batch_payload = {
        "as_of": "2025-11-01T00:00:00Z",
        "review_budget": 2,
        "wallet_histories": histories,
    }

    async with httpx.AsyncClient(transport=transport, base_url="http://audit.local") as client:
        health = await client.get("/healthz")
        ready = await client.get("/readyz")
        missing_auth = await client.post("/v1/score/batch", json=batch_payload)
        invalid_auth = await client.post(
            "/v1/score/batch",
            json=batch_payload,
            headers={"Authorization": "Bearer invalid-audit-token"},
        )
        expired_auth = await client.post(
            "/v1/score/batch",
            json=batch_payload,
            headers={"Authorization": "Bearer expired-audit-token"},
        )
        preview = await client.post(
            "/v1/features/preview",
            json={"as_of": batch_payload["as_of"], "events": histories[0]["events"]},
            headers=authorization,
        )
        batch = await client.post(
            "/v1/score/batch", json=batch_payload, headers=authorization
        )
        singles = []
        for history in histories:
            singles.append(
                await client.post(
                    "/v1/score",
                    json={"as_of": batch_payload["as_of"], "events": history["events"]},
                    headers=authorization,
                )
            )

    expected = {
        "health": 200,
        "ready": 503,
        "missing_auth": 401,
        "invalid_auth": 401,
        "expired_auth": 401,
        "preview": 200,
        "batch": 200,
    }
    observed = {
        "health": health.status_code,
        "ready": ready.status_code,
        "missing_auth": missing_auth.status_code,
        "invalid_auth": invalid_auth.status_code,
        "expired_auth": expired_auth.status_code,
        "preview": preview.status_code,
        "batch": batch.status_code,
    }
    if observed != expected or any(response.status_code != 200 for response in singles):
        raise RuntimeError(f"API status contract failed: expected={expected}, observed={observed}")

    preview_body = preview.json()
    batch_body = batch.json()
    if preview_body["feature_order"] != list(MODEL_FEATURE_COLUMNS):
        raise RuntimeError("Feature preview order does not match the training contract")
    if list(preview_body["features"]) != list(MODEL_FEATURE_COLUMNS):
        raise RuntimeError("Feature preview values do not match the training contract")
    if batch_body["feature_reference"]["feature_order"] != list(MODEL_FEATURE_COLUMNS):
        raise RuntimeError("Training reference does not match the feature contract")

    single_scores = {
        history["wallet"]: response.json()["anomaly_score"]
        for history, response in zip(histories, singles, strict=True)
    }
    batch_scores = {
        item["wallet"]: item["anomaly_score"] for item in batch_body["ranked_wallets"]
    }
    if single_scores != batch_scores:
        raise RuntimeError("Single and batch scoring are not exactly equivalent")
    ranks = [item["rank"] for item in batch_body["ranked_wallets"]]
    scores = [item["anomaly_score"] for item in batch_body["ranked_wallets"]]
    if ranks != [1, 2, 3] or scores != sorted(scores, reverse=True):
        raise RuntimeError("Batch rank ordering is invalid")

    production = create_app(
        _settings(artifact, manifest, digest, production=True),
        token_verifier=verifier,
    )
    production_transport = httpx.ASGITransport(app=production)
    async with httpx.AsyncClient(
        transport=production_transport, base_url="http://audit.local"
    ) as client:
        production_score = await client.post(
            "/v1/score",
            json={"as_of": batch_payload["as_of"], "events": histories[0]["events"]},
            headers=authorization,
        )
    if production_score.status_code != 503:
        raise RuntimeError("Production scoring did not fail closed")

    return {
        "status": "passed",
        "scope": "actual artifact through in-process FastAPI ASGI transport",
        "firebase_note": "test-only injected verifier; real Firebase was not contacted",
        "artifact_sha256": digest,
        "endpoint_statuses": {**observed, "production_score": production_score.status_code},
        "feature_count": len(MODEL_FEATURE_COLUMNS),
        "single_batch_scores_exactly_equal": True,
        "ranked_wallets": [
            {
                "wallet": item["wallet"],
                "rank": item["rank"],
                "anomaly_score": item["anomaly_score"],
                "selected_for_review": item["selected_for_review"],
            }
            for item in batch_body["ranked_wallets"]
        ],
        "interpretation": (
            "Synthetic functional evidence only; scores are not probabilities, labels, or "
            "evidence of fraud effectiveness."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact",
        type=Path,
        default=Path("artifacts/experimental/anomaly_models.joblib"),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("artifacts/experimental/anomaly_models_manifest.json"),
    )
    args = parser.parse_args()
    try:
        result = asyncio.run(audit(args.artifact, args.manifest))
    except (OSError, RuntimeError, ValueError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, indent=2))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
