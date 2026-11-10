"""Leakage-safe point-in-time wallet feature engineering.

Import the public feature contract from :mod:`solana_risk.features.build`. Keeping
this package initializer side-effect free also lets ``python -m
solana_risk.features.build`` execute without pre-importing the CLI module.
"""
