"""Run a deterministic, synthetic Phase 8B check against a trusted local artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from solana_risk.api.experimental_scoring import TrustedExperimentalScorer
from solana_risk.api.schemas import BatchScoreRequest, ScoreRequest


def _event(
    wallet: str,
    row: int,
    block_time: str,
    amount_usd: float,
    *,
    dex: str = "synthetic-dex-a",
) -> dict[str, Any]:
    return {
        "source_row_number": row,
        "wallet": wallet,
        "block_time": block_time,
        "block_slot": 2_000 + row,
        "tx_hash": f"{wallet}-synthetic-transaction-{row}",
        "dex": dex,
        "token_pair": "TOKEN-A/TOKEN-B",
        "token_in": "synthetic-token-a",
        "token_out": "synthetic-token-b",
        "amount_usd": amount_usd,
        "fee_usd": 0.1,
        "outer_instruction_index": 1,
        "inner_instruction_index": row,
    }


def _payload() -> dict[str, Any]:
    return {
        "as_of": "2025-11-01T00:00:00Z",
        "review_budget": 2,
        "wallet_histories": [
            {
                "wallet": "synthetic-wallet-bursty",
                "events": [
                    _event("synthetic-wallet-bursty", 1, "2025-10-31T23:57:00Z", 4_500),
                    _event("synthetic-wallet-bursty", 2, "2025-10-31T23:58:00Z", 5_200),
                    _event("synthetic-wallet-bursty", 3, "2025-10-31T23:59:00Z", 6_100),
                ],
            },
            {
                "wallet": "synthetic-wallet-steady",
                "events": [
                    _event("synthetic-wallet-steady", 1, "2025-09-20T10:00:00Z", 110),
                    _event("synthetic-wallet-steady", 2, "2025-10-05T10:00:00Z", 105),
                    _event("synthetic-wallet-steady", 3, "2025-10-20T10:00:00Z", 115),
                ],
            },
            {
                "wallet": "synthetic-wallet-sparse",
                "events": [
                    _event(
                        "synthetic-wallet-sparse",
                        1,
                        "2025-10-15T12:00:00Z",
                        80,
                        dex="synthetic-dex-b",
                    )
                ],
            },
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()

    scorer = TrustedExperimentalScorer.load(
        artifact_path=args.artifact,
        manifest_path=args.manifest,
        expected_sha256=args.sha256,
    )
    payload = BatchScoreRequest.model_validate(_payload())
    limits = {"max_wallets": 20, "max_events": 100, "max_events_per_wallet": 50}
    first = scorer.score_batch(payload, **limits)
    repeated = scorer.score_batch(payload, **limits)
    if first.model_dump(mode="json") != repeated.model_dump(mode="json"):
        raise RuntimeError("Repeated batch scoring was not deterministic")

    batch_scores = {item.wallet: item.anomaly_score for item in first.ranked_wallets}
    single_scores: dict[str, float] = {}
    for history in payload.wallet_histories:
        single = scorer.score(
            ScoreRequest.model_validate(
                {
                    "as_of": payload.as_of.isoformat().replace("+00:00", "Z"),
                    "events": [event.model_dump(mode="json") for event in history.events],
                }
            )
        )
        single_scores[history.wallet] = single.anomaly_score
    if single_scores != batch_scores:
        raise RuntimeError("Single-wallet and batch scores differ")

    print(
        json.dumps(
            {
                "status": first.status,
                "model_version": first.model_version,
                "is_probability": first.is_probability,
                "ranked_wallets": [
                    {
                        "rank": item.rank,
                        "wallet": item.wallet,
                        "anomaly_score": item.anomaly_score,
                        "selected_for_review": item.selected_for_review,
                    }
                    for item in first.ranked_wallets
                ],
                "review_candidates": first.review_candidates,
                "deterministic_repeat": True,
                "single_endpoint_equivalence": True,
                "interpretation": first.interpretation,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
