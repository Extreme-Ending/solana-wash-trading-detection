"""Provisional, label-free wallet anomaly scoring experiments.

These modules produce anomaly scores for research review. They do not infer or
confirm wash trading, fraud, misconduct, or any other ground-truth outcome.
"""

from solana_risk.models.baselines import RobustMADDetector

__all__ = ["RobustMADDetector"]
