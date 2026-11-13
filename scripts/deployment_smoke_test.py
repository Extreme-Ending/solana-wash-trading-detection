"""Smoke-test a deployed private API with synthetic data and no token logging."""

from __future__ import annotations

import argparse
import getpass
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


def _payload() -> dict[str, Any]:
    return {
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
                "inner_instruction_index": 0,
            }
        ],
    }


def _request(
    base_url: str,
    cloud_run_token: str,
    firebase_token: str,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any]]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}{path}",
        data=data,
        method=method,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {firebase_token}",
            "X-Serverless-Authorization": f"Bearer {cloud_run_token}",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def _validate_base_url(value: str) -> str:
    parsed = urllib.parse.urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise ValueError("--base-url must be an HTTPS origin without a path or credentials")
    return f"https://{parsed.netloc}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument(
        "--tokens-stdin",
        action="store_true",
        help="read Cloud Run then Firebase short-lived tokens from stdin without command arguments",
    )
    args = parser.parse_args()
    try:
        base_url = _validate_base_url(args.base_url)
    except ValueError as exc:
        parser.error(str(exc))
    if not args.tokens_stdin:
        parser.error("--tokens-stdin is required; tokens are never accepted as command arguments")
    if sys.stdin.isatty():
        cloud_run_token = getpass.getpass("Cloud Run identity token: ")
        firebase_token = getpass.getpass("Firebase ID token: ")
    else:
        cloud_run_token = sys.stdin.readline().strip()
        firebase_token = sys.stdin.readline().strip()
    if not cloud_run_token or not firebase_token:
        parser.error("non-empty short-lived Cloud Run and Firebase tokens are required")

    payload = _payload()
    health_status, health = _request(base_url, cloud_run_token, firebase_token, "GET", "/healthz")
    ready_status, ready = _request(base_url, cloud_run_token, firebase_token, "GET", "/readyz")
    preview_status, preview = _request(base_url, cloud_run_token, firebase_token, "POST", "/v1/features/preview", payload)
    score_status, score = _request(base_url, cloud_run_token, firebase_token, "POST", "/v1/score", payload)

    assert health_status == 200 and health.get("status") == "ok"
    assert ready_status == 503 and ready["error"]["code"] == "MODEL_NOT_APPROVED"
    assert preview_status == 200 and len(preview["feature_order"]) == 29
    assert score_status == 503 and score["error"]["code"] == "MODEL_NOT_APPROVED"
    score_text = json.dumps(score).casefold()
    assert "anomaly_score" not in score_text and "fraud_probability" not in score_text
    print("Deployment smoke test: PASS (health 200, readiness 503, preview 200/29 features, score 503)")


if __name__ == "__main__":
    main()
