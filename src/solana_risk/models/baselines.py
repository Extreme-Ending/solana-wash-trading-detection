"""Robust statistical reference scorer for the provisional anomaly experiment."""

from __future__ import annotations

import numpy as np
from sklearn.base import BaseEstimator
from sklearn.utils.validation import check_array, check_is_fitted


class RobustMADDetector(BaseEstimator):
    """Score multivariate distance from train medians using robust dispersion.

    Non-constant dimensions use ``1.4826 * MAD``. A value different from a
    train-constant dimension receives ``constant_penalty``; an unchanged value
    receives zero. Per-feature contributions are clipped before their root mean
    square is calculated so one unit-dependent extreme cannot grow without
    bound. The resulting score is descriptive: larger means less typical of the
    training reference, never a probability or confirmed outcome.
    """

    def __init__(self, *, clip: float = 25.0, constant_penalty: float = 10.0) -> None:
        self.clip = clip
        self.constant_penalty = constant_penalty

    def fit(self, X: object, y: object | None = None) -> "RobustMADDetector":
        del y
        values = check_array(X, dtype=float, ensure_all_finite=True)
        if self.clip <= 0:
            raise ValueError("clip must be positive")
        if self.constant_penalty <= 0:
            raise ValueError("constant_penalty must be positive")
        self.location_ = np.median(values, axis=0)
        mad = np.median(np.abs(values - self.location_), axis=0)
        self.scale_ = 1.4826 * mad
        self.constant_mask_ = self.scale_ == 0.0
        self.n_features_in_ = values.shape[1]
        return self

    def score_samples(self, X: object) -> np.ndarray:
        """Return nonnegative anomaly scores; larger means more unusual."""

        check_is_fitted(self, ("location_", "scale_", "constant_mask_"))
        values = check_array(X, dtype=float, ensure_all_finite=True)
        if values.shape[1] != self.n_features_in_:
            raise ValueError(
                f"Expected {self.n_features_in_} features, received {values.shape[1]}"
            )
        distance = np.abs(values - self.location_)
        contributions = np.zeros_like(distance, dtype=float)
        regular = ~self.constant_mask_
        contributions[:, regular] = distance[:, regular] / self.scale_[regular]
        if self.constant_mask_.any():
            changed = distance[:, self.constant_mask_] > np.finfo(float).eps
            contributions[:, self.constant_mask_] = changed * self.constant_penalty
        clipped = np.minimum(contributions, self.clip)
        return np.sqrt(np.mean(np.square(clipped), axis=1))
