"""Scaffold checks for the Phase 0 package foundation."""

import solana_risk


def test_package_exposes_initial_version() -> None:
    """The importable package and project metadata start at the same version."""
    assert solana_risk.__version__ == "0.0.0"
