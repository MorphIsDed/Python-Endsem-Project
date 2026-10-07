"""Configuration and default constants for ProjectPulse."""

from __future__ import annotations

PRIORITY_FACTORS = {1: 1.0, 2: 1.25, 3: 1.5, 4: 2.0, 5: 2.5}
DEFAULT_HOURS_PER_DAY = 8.0
DEFAULT_SIMULATION_ITERATIONS = 1000
MAX_SIMULATION_ITERATIONS = 10000

BURNOUT_WEIGHTS = {
    "peak_utilization": 0.30,
    "streak": 0.30,
    "share_over_capacity": 0.25,
    "weekend_work": 0.15,
}
