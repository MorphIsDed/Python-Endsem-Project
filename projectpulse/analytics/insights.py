"""Plain-English insight generation."""

from __future__ import annotations


class InsightEngine:
    """Build human-friendly risk and opportunity statements."""

    def summarise(self, deadline_probability: float, p90: float, critical_tasks: list[str], overloaded_people: list[str]) -> list[str]:
        insights: list[str] = []
        if deadline_probability < 0.5:
            insights.append(f"There is only a {deadline_probability * 100:.0f}% chance of hitting the deadline; P90 is {p90:.1f} working days.")
        else:
            insights.append(f"The project has a {deadline_probability * 100:.0f}% chance of meeting the deadline.")
        if critical_tasks:
            insights.append(f"Critical tasks this cycle: {', '.join(critical_tasks)}.")
        if overloaded_people:
            insights.append(f"Team overload detected for: {', '.join(overloaded_people)}.")
        return insights
