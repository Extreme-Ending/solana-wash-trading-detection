#!/usr/bin/env python3
"""Verify live authenticated scoring without storing or printing the Firebase token."""

from __future__ import annotations

import argparse
import json
import math
import os
import urllib.error
import urllib.request
from typing import Any


DEFAULT_API = "https://solana-wallet-risk-api-jm24jzeesq-bq.a.run.app"
AS_OF = "2025-11-01T00:00:00Z"


def event(wallet: str, row: int, time: str, amount: float) -> dict[str, Any]:
    return {
        "source_row_number": row,
        "wallet": wallet,
        "block_time": time,
        "block_slot": 9000 + row,
        "tx_hash": f"{wallet}-acceptance-{row}",
        "dex": "synthetic-acceptance-dex",
        "token_pair": "TOKEN-A/TOKEN-B",
        "token_in": "synthetic-token-a",
        "token_out": "synthetic-token-b",
        "amount_usd": amount,
        "fee_usd": 0.1,
        "outer_instruction_index": 1,
        "inner_instruction_index": row,
    }


HISTORIES = [
    {
        "wallet": "synthetic-acceptance-bursty",
        "events": [
            event("synthetic-acceptance-bursty", 1, "2025-10-31T23:57:00Z", 4500.0),
            event("synthetic-acceptance-bursty", 2, "2025-10-31T23:58:00Z", 5200.0),
            event("synthetic-acceptance-bursty", 3, "2025-10-31T23:59:00Z", 6100.0),
        ],
    },
    {
        "wallet": "synthetic-acceptance-steady",
        "events": [
            event("synthetic-acceptance-steady", 11, "2025-09-20T10:00:00Z", 110.0),
            event("synthetic-acceptance-steady", 12, "2025-10-05T10:00:00Z", 105.0),
            event("synthetic-acceptance-steady", 13, "2025-10-20T10:00:00Z", 115.0),
        ],
    },
]


def request_json(
    base_url: str,
    path: str,
    token: str,
    payload: dict[str, Any],
) -> tuple[int, dict[str, Any]]:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        base_url.rstrip("/") + path,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Origin": "https://solana-wallet-risk.web.app",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status != 200:
                raise RuntimeError(f"Unexpected HTTP status {response.status} for {path}")
            decoded = json.loads(response.read().decode("utf-8"))
            if not isinstance(decoded, dict):
                raise RuntimeError(f"{path} returned a non-object JSON response")
            return response.status, decoded
    except urllib.error.HTTPError as exc:
        error_code = "UNKNOWN_ERROR"
        error_message = "The service rejected the acceptance request."
        try:
            decoded = json.loads(exc.read().decode("utf-8", errors="replace"))
            error = decoded.get("error") if isinstance(decoded, dict) else None
            if isinstance(error, dict):
                if isinstance(error.get("code"), str):
                    error_code = error["code"]
                if isinstance(error.get("message"), str):
                    error_message = error["message"]
        except json.JSONDecodeError:
            pass
        raise RuntimeError(
            f"{path} returned HTTP {exc.code} ({error_code}): {error_message}"
        ) from exc


def validate_and_sanitize(
    single_http_status: int,
    single: dict[str, Any],
    batch_http_status: int,
    batch: dict[str, Any],
) -> dict[str, Any]:
    """Validate the production response contract and retain only safe evidence."""

    expected_methodology = "experimental_unsupervised_research_only"
    if single_http_status != 200 or batch_http_status != 200:
        raise RuntimeError("Authenticated scoring did not return HTTP 200")
    for name, response in (("single", single), ("batch", batch)):
        if response.get("methodology_status") != expected_methodology:
            raise RuntimeError(f"{name} response has an unexpected methodology status")
        if response.get("model_id") != "isolation_forest":
            raise RuntimeError(f"{name} response has an unexpected model identifier")
        if response.get("is_probability") is not False:
            raise RuntimeError(f"{name} response violates the non-probability contract")
        if not isinstance(response.get("model_version"), str):
            raise RuntimeError(f"{name} response has no model version")
        if not isinstance(response.get("interpretation"), str):
            raise RuntimeError(f"{name} response has no interpretation")
    if single["model_version"] != batch["model_version"]:
        raise RuntimeError("Single and batch responses use different model versions")
    score = single.get("anomaly_score")
    if (
        not isinstance(score, (int, float))
        or isinstance(score, bool)
        or not math.isfinite(float(score))
    ):
        raise RuntimeError("Single-score response has no finite numeric anomaly score")
    wallets = batch.get("ranked_wallets")
    if not isinstance(wallets, list) or len(wallets) != 2:
        raise RuntimeError("Batch response does not contain two ranked wallet results")
    for item in wallets:
        item_score = item.get("anomaly_score") if isinstance(item, dict) else None
        if (
            not isinstance(item_score, (int, float))
            or isinstance(item_score, bool)
            or not math.isfinite(float(item_score))
        ):
            raise RuntimeError("Batch response contains a non-numeric anomaly score")

    return {
        "single": {
            "http_status": single_http_status,
            "model_id": single["model_id"],
            "model_version": single["model_version"],
            "methodology_status": single["methodology_status"],
            "anomaly_score": score,
            "is_probability": single["is_probability"],
            "training_cutoff": single.get("training_cutoff"),
            "feature_registry_sha256": single.get("feature_registry_sha256"),
            "interpretation": single["interpretation"],
        },
        "batch": {
            "http_status": batch_http_status,
            "model_id": batch["model_id"],
            "model_version": batch["model_version"],
            "methodology_status": batch["methodology_status"],
            "is_probability": batch["is_probability"],
            "interpretation": batch["interpretation"],
            "ranked_wallets": [
                {
                    "wallet": item.get("wallet"),
                    "anomaly_score": item.get("anomaly_score"),
                    "rank": item.get("rank"),
                    "selected_for_review": item.get("selected_for_review"),
                }
                for item in wallets
            ],
        },
        "input_provenance": (
            "Bounded synthetic acceptance data; this verifies production inference, "
            "not research effectiveness or fraud detection."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-base-url", default=DEFAULT_API)
    args = parser.parse_args()
    token = os.environ.get("SOLANA_RISK_FIREBASE_ID_TOKEN", "").strip()
    if not token:
        print(
            "Set SOLANA_RISK_FIREBASE_ID_TOKEN to a fresh Firebase ID token from an "
            "approved signed-in account. The script never prints or writes the token."
        )
        return 2

    single_payload = {"as_of": AS_OF, "events": HISTORIES[0]["events"]}
    single_status, single = request_json(
        args.api_base_url,
        "/v1/score",
        token,
        single_payload,
    )
    batch_status, batch = request_json(
        args.api_base_url,
        "/v1/score/batch",
        token,
        {"as_of": AS_OF, "wallet_histories": HISTORIES, "review_budget": 1},
    )
    sanitized = validate_and_sanitize(single_status, single, batch_status, batch)
    print(json.dumps(sanitized, indent=2, sort_keys=True))
    print("Authenticated live scoring acceptance: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
