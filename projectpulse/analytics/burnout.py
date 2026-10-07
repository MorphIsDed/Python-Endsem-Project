"""Burnout scoring and overload heuristics."""

from __future__ import annotations

from datetime import date

import pandas as pd

from projectpulse.core.config import BURNOUT_WEIGHTS


class BurnoutAnalyzer:
    """Score workload stress using a configurable weighted formula."""

    def __init__(self, weights: dict[str, float] | None = None):
        self.weights = weights or BURNOUT_WEIGHTS

    def score_series(self, usage: pd.DataFrame) -> dict[str, float]:
        if usage.empty:
            return {"score": 0.0, "peak_utilization": 0.0, "streak": 0.0, "share_over_capacity": 0.0, "weekend_work": 0.0}
        peak = float(usage["hours"].max() / max(usage["capacity"].max(), 1)) * 100
        streak = float(usage["over_capacity"].sum())
        share = float(usage["over_capacity"].mean()) * 100
        weekend = float(usage.get("weekend_work", 0).sum())
        score = (
            peak * self.weights["peak_utilization"]
            + min(streak * 10, 100) * self.weights["streak"]
            + share * self.weights["share_over_capacity"]
            + weekend * self.weights["weekend_work"]
        )
        return {
            "score": min(score, 100.0),
            "peak_utilization": peak,
            "streak": streak,
            "share_over_capacity": share,
            "weekend_work": weekend,
        }

    def traffic_light(self, score: float) -> str:
        if score < 35:
            return "green"
        if score <= 65:
            return "amber"
        return "red"
