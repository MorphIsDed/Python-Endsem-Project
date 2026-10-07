"""Vectorised Monte Carlo risk engine for project completion predictions."""

from __future__ import annotations

import numpy as np

from projectpulse.core.config import DEFAULT_SIMULATION_ITERATIONS


class MonteCarloEngine:
    """Compute project completion risk using triangular task durations."""

    def __init__(self, iterations: int = DEFAULT_SIMULATION_ITERATIONS, seed: int | None = None):
        self.iterations = max(1, min(iterations, 10000))
        self.seed = seed

    def simulate(self, durations: np.ndarray) -> dict[str, np.ndarray | float]:
        rng = np.random.default_rng(self.seed)
        min_values = durations * 0.8
        mode_values = durations
        max_values = durations * 1.3
        samples = rng.triangular(min_values, mode_values, max_values, size=(self.iterations, durations.size))
        finish = samples.sum(axis=1)
        return {
            "samples": samples,
            "finish_days": finish,
            "p50": float(np.percentile(finish, 50)),
            "p80": float(np.percentile(finish, 80)),
            "p90": float(np.percentile(finish, 90)),
        }
