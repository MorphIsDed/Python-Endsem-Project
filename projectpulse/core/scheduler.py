"""Project scheduling and dependency management using DAG and critical-path logic."""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import date
from typing import Iterable

from .calendar import add_business_days
from .config import DEFAULT_HOURS_PER_DAY
from .exceptions import CircularDependencyError, UnknownDependencyError
from .models import Dependency, Project, Task


class Scheduler:
    """Compute task dates, critical path, and dependency validation."""

    def __init__(self, project: Project):
        self.project = project

    def validate_dependencies(self) -> None:
        task_ids = {task.id for task in self.project.tasks}
        for task in self.project.tasks:
            for dep in task.predecessors:
                if dep.predecessor_id == task.id:
                    raise ValueError(f"Task '{task.id}' cannot depend on itself.")
                if dep.predecessor_id not in task_ids:
                    raise UnknownDependencyError(
                        f"Task '{task.id}' references unknown predecessor '{dep.predecessor_id}'."
                    )

    def topo_sort(self) -> list[str]:
        self.validate_dependencies()
        indegree: dict[str, int] = {task.id: 0 for task in self.project.tasks}
        adjacency: dict[str, list[str]] = defaultdict(list)
        for task in self.project.tasks:
            for dep in task.predecessors:
                adjacency[dep.predecessor_id].append(task.id)
                indegree[task.id] += 1
        queue = deque(sorted(task_id for task_id, degree in indegree.items() if degree == 0))
        order: list[str] = []
        while queue:
            current = queue.popleft()
            order.append(current)
            for neighbor in sorted(adjacency.get(current, [])):
                indegree[neighbor] -= 1
                if indegree[neighbor] == 0:
                    queue.append(neighbor)
        if len(order) != len(self.project.tasks):
            cycle = sorted(set(indegree) - set(order))
            raise CircularDependencyError(cycle=cycle)
        return order

    def get_predecessor_map(self) -> dict[str, list[Dependency]]:
        return {task.id: task.predecessors for task in self.project.tasks}

    def compute_schedule(self) -> dict[str, dict[str, date | float | int]]:
        order = self.topo_sort()
        task_lookup = {task.id: task for task in self.project.tasks}
        early_start: dict[str, date] = {}
        early_finish: dict[str, date] = {}
        late_start: dict[str, date] = {}
        late_finish: dict[str, date] = {}
        project_deadline = self.project.deadline or max((task.planned_end for task in self.project.tasks), default=None)

        for task_id in order:
            task = task_lookup[task_id]
            preds = task.predecessors
            if not preds:
                early_start[task_id] = task.planned_start
                early_finish[task_id] = task.planned_end
            else:
                finish_dates = [
                    add_business_days(
                        early_finish[dep.predecessor_id],
                        dep.lag_days,
                        self.project.holidays,
                    )
                    for dep in preds
                ]
                earliest = max(finish_dates)
                early_start[task_id] = max(task.planned_start, earliest)
                early_finish[task_id] = add_business_days(
                    early_start[task_id],
                    max(task.duration_days(self.project.holidays) - 1, 0),
                    self.project.holidays,
                )

        if project_deadline is None:
            project_deadline = max(early_finish.values())

        latest_finish = {task_id: project_deadline for task_id in task_lookup}
        for task_id in reversed(order):
            task = task_lookup[task_id]
            successors = [child.id for child in self.project.tasks if any(dep.predecessor_id == task_id for dep in child.predecessors)]
            if not successors:
                late_finish[task_id] = project_deadline
                late_start[task_id] = max(task.planned_start, add_business_days(project_deadline, -max(task.duration_days(self.project.holidays) - 1, 0), self.project.holidays))
            else:
                candidate_dates = []
                for child_id in successors:
                    child = task_lookup[child_id]
                    child_dep = next(dep for dep in child.predecessors if dep.predecessor_id == task_id)
                    candidate = add_business_days(late_start[child_id], -child_dep.lag_days, self.project.holidays)
                    candidate_dates.append(candidate)
                late_finish[task_id] = min(candidate_dates)
                late_start[task_id] = add_business_days(late_finish[task_id], -max(task.duration_days(self.project.holidays) - 1, 0), self.project.holidays)

        schedule: dict[str, dict[str, date | float | int]] = {}
        for task_id in order:
            task = task_lookup[task_id]
            duration = max(task.duration_days(self.project.holidays), 1 if task.planned_start == task.planned_end else 0)
            es = early_start[task_id]
            ef = early_finish[task_id]
            ls = late_start[task_id]
            lf = late_finish[task_id]
            slack = max((ls - es).days, 0)
            schedule[task_id] = {
                "task_id": task_id,
                "name": task.name,
                "assignee": task.assignee_name,
                "early_start": es,
                "early_finish": ef,
                "late_start": ls,
                "late_finish": lf,
                "slack": slack,
                "duration": duration,
                "critical": slack == 0,
            }
        return schedule

    def critical_path_ids(self) -> list[str]:
        schedule = self.compute_schedule()
        critical = [task_id for task_id, data in schedule.items() if data["critical"]]
        return critical

    @staticmethod
    def working_hours_for_task(task: Task) -> float:
        return task.hours_per_day * max(task.duration_days(), 1)
