"""Scenario engine for what-if changes to project assumptions."""

from __future__ import annotations

from copy import deepcopy

from projectpulse.core.models import Project


class ScenarioEngine:
    """Apply a named scenario to a deep copy of a project."""

    def __init__(self, project: Project):
        self.project = project

    def apply(self, *, task_id: str | None = None, new_assignee: str | None = None, duration_delta: int = 0, deadline=None) -> Project:
        copied = deepcopy(self.project)
        if task_id is not None:
            task = next((item for item in copied.tasks if item.id == task_id), None)
            if task is not None and new_assignee is not None:
                task.assignee = new_assignee
            if task is not None and duration_delta:
                task.planned_end = task.planned_end
        if deadline is not None:
            copied.deadline = deadline
        return copied
