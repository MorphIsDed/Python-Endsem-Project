"""Domain models for ProjectPulse project scheduling and analytics."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Iterable

from .calendar import business_days_between
from .config import DEFAULT_HOURS_PER_DAY, PRIORITY_FACTORS
from .exceptions import DuplicateTaskError, InvalidPriorityError, InvalidDateRangeError


@dataclass(frozen=True)
class Dependency:
    predecessor_id: str
    lag_days: int = 0

    def __post_init__(self):
        if self.lag_days < 0:
            raise ValueError("Dependency lag_days cannot be negative.")


@dataclass
class TeamMember:
    name: str
    capacity_hours_per_day: float = DEFAULT_HOURS_PER_DAY
    leave_dates: list[date] = field(default_factory=list)


class Task(ABC):
    """Abstract task model with polymorphic weights and validation."""

    def __init__(
        self,
        task_id: str,
        name: str,
        planned_start: date,
        planned_end: date,
        assignee: str | None,
        priority: int,
        predecessors: Iterable[Dependency] | None = None,
        percent_complete: float = 0.0,
        hours_per_day: float = DEFAULT_HOURS_PER_DAY,
    ) -> None:
        self.id = task_id
        self.name = name
        self.planned_start = planned_start
        self.planned_end = planned_end
        self.assignee = assignee.strip() if assignee and assignee.strip() else None
        self.priority = priority
        self.predecessors = list(predecessors or [])
        self.percent_complete = float(percent_complete)
        self.hours_per_day = float(hours_per_day)
        self._validate()

    @property
    def assignee_name(self) -> str:
        return self.assignee or "Unassigned"

    @property
    def priority_factor(self) -> float:
        if self.priority not in PRIORITY_FACTORS:
            raise InvalidPriorityError(f"Priority {self.priority} is invalid.")
        return PRIORITY_FACTORS[self.priority]

    @property
    def duration(self) -> int:
        return self.duration_days()

    def _validate(self) -> None:
        if self.planned_end < self.planned_start:
            raise InvalidDateRangeError(f"Task {self.id} has an end date before its start date.")
        if self.priority not in PRIORITY_FACTORS:
            raise InvalidPriorityError(f"Priority {self.priority} is not supported.")
        if not 0.0 <= self.percent_complete <= 100.0:
            raise ValueError(f"Task {self.id} percent complete must be between 0 and 100.")

    @abstractmethod
    def duration_days(self, holidays: Iterable[date] | None = None) -> int:
        """Return task duration in working days."""

    @abstractmethod
    def weight(self) -> float:
        """Return relative working weight used for progress and criticality."""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id!r}, name={self.name!r})"

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Task):
            return NotImplemented
        return self.planned_start < other.planned_start

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Task):
            return NotImplemented
        return self.id == other.id and self.name == other.name and self.planned_start == other.planned_start

    def __hash__(self) -> int:
        return hash((self.id, self.name, self.planned_start))


class StandardTask(Task):
    """Normal task with duration-driven weight."""

    def duration_days(self, holidays: Iterable[date] | None = None) -> int:
        return business_days_between(self.planned_start, self.planned_end, holidays or [])

    def weight(self) -> float:
        return self.duration_days() * self.priority_factor


class MilestoneTask(Task):
    """Milestone consumes no working time and has fixed weight."""

    def duration_days(self, holidays: Iterable[date] | None = None) -> int:
        return 0

    def weight(self) -> float:
        return self.priority_factor


class BufferTask(Task):
    """Reserve tasks weight less than standard tasks and add no assignee workload."""

    def duration_days(self, holidays: Iterable[date] | None = None) -> int:
        return business_days_between(self.planned_start, self.planned_end, holidays or [])

    def weight(self) -> float:
        return 0.5 * self.duration_days() * self.priority_factor


class RecurringTask(Task):
    """Recurring tasks receive a small multiplier to emphasize repeated effort."""

    def duration_days(self, holidays: Iterable[date] | None = None) -> int:
        return business_days_between(self.planned_start, self.planned_end, holidays or [])

    def weight(self) -> float:
        return self.duration_days() * self.priority_factor * 1.1


@dataclass
class Project:
    name: str
    tasks: list[Task]
    team: list[TeamMember] = field(default_factory=list)
    deadline: date | None = None
    holidays: set[date] = field(default_factory=set)

    def __post_init__(self) -> None:
        ids = [task.id for task in self.tasks]
        if len(ids) != len(set(ids)):
            raise DuplicateTaskError("Project contains duplicate task IDs.")

    @property
    def task_ids(self) -> list[str]:
        return [task.id for task in self.tasks]

    def add_task(self, task: Task) -> None:
        if any(existing.id == task.id for existing in self.tasks):
            raise DuplicateTaskError(f"Task '{task.id}' already exists in the project.")
        self.tasks.append(task)

    def get_task(self, task_id: str) -> Task:
        for task in self.tasks:
            if task.id == task_id:
                return task
        raise KeyError(f"Task '{task_id}' not found.")
