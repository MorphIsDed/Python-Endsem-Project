"""Custom exceptions used throughout ProjectPulse."""


class ProjectPulseError(Exception):
    """Base exception for ProjectPulse domain errors."""


class InvalidDateRangeError(ProjectPulseError):
    """Raised when a task date range is invalid."""


class InvalidPriorityError(ProjectPulseError):
    """Raised when a task priority is outside the valid range."""


class CircularDependencyError(ProjectPulseError):
    """Raised when the task graph contains a cycle."""

    def __init__(self, cycle: list[str] | None = None):
        super().__init__("Circular dependency detected in task graph.")
        self.cycle = cycle or []


class UnknownDependencyError(ProjectPulseError):
    """Raised when a task references an unknown predecessor."""


class DuplicateTaskError(ProjectPulseError):
    """Raised when a task id is duplicated."""


class TaskParseError(ProjectPulseError):
    """Raised when a task line cannot be parsed."""

    def __init__(self, line_number: int, reason: str):
        super().__init__(f"Line {line_number}: {reason}")
        self.line_number = line_number
        self.reason = reason


class StorageError(ProjectPulseError):
    """Raised when a persistence operation fails."""


class HolidayAPIError(ProjectPulseError):
    """Raised when a holiday API request fails."""


class ScenarioError(ProjectPulseError):
    """Raised when a what-if scenario is invalid."""


class InvalidProjectError(ProjectPulseError):
    """Raised when a project graph is invalid."""
