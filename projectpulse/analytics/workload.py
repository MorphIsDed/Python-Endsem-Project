"""Workload analysis utilities for daily assignment pressure."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

import pandas as pd

from projectpulse.core.calendar import business_days_between
from projectpulse.core.models import Project, Task


class WorkloadAnalyzer:
    """Aggregate task hours by person and working day."""

    def daily_load_table(self, project: Project) -> pd.DataFrame:
        rows: list[dict[str, object]] = []
        for task in project.tasks:
            if task.assignee is None:
                continue
            start = task.planned_start
            end = task.planned_end
            duration = business_days_between(start, end, project.holidays)
            hours = task.hours_per_day * max(duration, 1)
            current = start
            while current <= end:
                if current.weekday() < 5 and current not in project.holidays:
                    rows.append(
                        {
                            "date": current,
                            "assignee": task.assignee,
                            "task_id": task.id,
                            "hours": task.hours_per_day,
                        }
                    )
                current += timedelta(days=1)
            if duration == 0:
                rows.append({"date": start, "assignee": task.assignee, "task_id": task.id, "hours": hours})
        df = pd.DataFrame(rows)
        if df.empty:
            return pd.DataFrame(columns=["date", "assignee", "task_id", "hours"])
        return df

    def workload_by_assignee(self, project: Project) -> pd.DataFrame:
        df = self.daily_load_table(project)
        if df.empty:
            return pd.DataFrame(columns=["assignee", "total_hours", "days_over_capacity", "peak_load"])
        loads = df.groupby(["assignee", "date"], as_index=False)["hours"].sum()
        capacities = {
            member.name: member.capacity_hours_per_day for member in project.team
        }
        loads["capacity"] = loads["assignee"].map(capacities)
        loads["over_capacity"] = loads["hours"] > loads["capacity"]
        return loads.groupby("assignee").agg(
            total_hours=("hours", "sum"),
            days_over_capacity=("over_capacity", "sum"),
            peak_load=("hours", "max"),
        ).reset_index()
