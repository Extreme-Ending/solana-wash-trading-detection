"""Contract tests for sanitized live authenticated-scoring evidence."""

from __future__ import annotations

import json

import pytest

from scripts.verify_live_authenticated_scoring import validate_and_sanitize


def _responses() -> tuple[dict, dict]:
    interpretation = (
        "Experimental unsupervised anomaly score; not a probability or fraud determination."
    )
    single = {
        "methodology_status": "experimental_unsupervised_research_only",
        "model_id": "isolation_forest",
        "model_version": "4B.1",
        "anomaly_score": 0.7,
        "is_probability": False,
        "training_cutoff": "2025-09-01T00:00:00Z",
        "feature_registry_sha256": "a" * 64,
        "interpretation": interpretation,
        "uid": "must-not-be-copied",
    }
    batch = {
        "methodology_status": "experimental_unsupervised_research_only",
        "model_id": "isolation_forest",
        "model_version": "4B.1",
        "is_probability": False,
        "interpretation": (
            "Experimental statistical anomalies requiring review; not confirmed fraud."
        ),
        "ranked_wallets": [
            {
                "wallet": "synthetic-a",
                "anomaly_score": 0.7,
                "rank": 1,
                "selected_for_review": True,
            },
            {
                "wallet": "synthetic-b",
                "anomaly_score": 0.5,
                "rank": 2,
                "selected_for_review": False,
            },
        ],
        "allowed_uids": ["must-not-be-copied"],
    }
    return single, batch


def test_sanitized_evidence_records_required_contract_without_identity_values() -> None:
    single, batch = _responses()

    evidence = validate_and_sanitize(200, single, 200, batch)

    assert evidence["single"]["http_status"] == 200
    assert evidence["batch"]["http_status"] == 200
    assert evidence["single"]["anomaly_score"] == 0.7
    assert evidence["single"]["model_version"] == "4B.1"
    assert evidence["single"]["methodology_status"] == (
        "experimental_unsupervised_research_only"
    )
    assert "not a probability" in evidence["single"]["interpretation"]
    serialized = json.dumps(evidence)
    assert "must-not-be-copied" not in serialized
    assert "uid" not in serialized.casefold()


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("anomaly_score", "0.7", "finite numeric anomaly score"),
        ("methodology_status", "unsupported", "methodology status"),
        ("is_probability", True, "non-probability contract"),
    ],
)
def test_invalid_single_response_is_rejected(field: str, value: object, message: str) -> None:
    single, batch = _responses()
    single[field] = value

    with pytest.raises(RuntimeError, match=message):
        validate_and_sanitize(200, single, 200, batch)
