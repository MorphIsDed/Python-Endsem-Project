"""Text parser for task lists and project ingestion."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from projectpulse.core.config import PRIORITY_FACTORS
from projectpulse.core.exceptions import DuplicateTaskError, TaskParseError, UnknownDependencyError
from projectpulse.core.models import BufferTask, Dependency, MilestoneTask, Project, RecurringTask, StandardTask, Task, TeamMember


LINE_PATTERN = re.compile(
    r"""
    ^\s*
    (?P<task_id>[^|]+?)\s*\|\s*
    (?P<name>[^|]+?)\s*\|\s*
    (?P<start>\d{4}-\d{2}-\d{2})\s*\|\s*
    (?P<end>\d{4}-\d{2}-\d{2})\s*\|\s*
    (?P<assignee>[^|]*?)\s*\|\s*
    (?P<priority>\d)\s*\|\s*
    (?P<deps>[^|]*?)
    (?:\s*\|\s*(?P<progress>\d+(?:\.\d+)?)\s*)?
    \s*$
    """,
    re.VERBOSE,
)


@dataclass
class ParseResult:
    accepted: list[Task]
    rejected: list[str]


def _parse_date(value: str) -> datetime.date:
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError as exc:
        raise TaskParseError(0, f"invalid date '{value}'") from exc


def _parse_dependencies(value: str) -> list[Dependency]:
    cleaned = (value or "").strip()
    if cleaned.lower() in {"", "none"}:
        return []
    items = []
    for part in cleaned.split(","):
        piece = part.strip()
        if not piece:
            continue
        match = re.fullmatch(r"(?P<dep_id>[A-Za-z0-9_.-]+)(?:\+(?P<lag>\d+))?", piece)
        if not match:
            raise TaskParseError(0, f"invalid dependency '{piece}'")
        lag = int(match.group("lag") or 0)
        items.append(Dependency(match.group("dep_id"), lag))
    return items


def _build_task(task_id: str, name: str, start: str, end: str, assignee: str, priority: str, deps: str, progress: str) -> Task:
    start_date = _parse_date(start)
    end_date = _parse_date(end)
    if end_date < start_date:
        raise TaskParseError(0, "end date before start date")
    priority_value = int(priority)
    if priority_value not in PRIORITY_FACTORS:
        raise TaskParseError(0, f"invalid priority '{priority}'")
    predecessor_list = _parse_dependencies(deps)
    comp = float(progress) if progress else 0.0

    task_type = "standard"
    if task_id.startswith("M"):
        task_type = "milestone"
    elif task_id.startswith("B"):
        task_type = "buffer"
    elif task_id.startswith("R"):
        task_type = "recurring"

    if task_type == "milestone":
        return MilestoneTask(task_id, name, start_date, end_date, assignee or None, priority_value, predecessor_list, comp)
    if task_type == "buffer":
        return BufferTask(task_id, name, start_date, end_date, assignee or None, priority_value, predecessor_list, comp)
    if task_type == "recurring":
        return RecurringTask(task_id, name, start_date, end_date, assignee or None, priority_value, predecessor_list, comp)
    return StandardTask(task_id, name, start_date, end_date, assignee or None, priority_value, predecessor_list, comp)


def parse_task_lines(content: str) -> ParseResult:
    """Parse a raw text schedule and return accepted tasks plus rejected lines."""
    accepted: list[Task] = []
    rejected: list[str] = []
    seen_ids: set[str] = set()

    for line_number, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = LINE_PATTERN.match(line)
        if not match:
            rejected.append(f"Line {line_number}: invalid task format")
            continue
        fields = match.groupdict()
        try:
            task = _build_task(
                fields["task_id"].strip(),
                fields["name"].strip(),
                fields["start"].strip(),
                fields["end"].strip(),
                fields["assignee"].strip(),
                fields["priority"].strip(),
                fields["deps"].strip(),
                fields["progress"].strip() if fields.get("progress") else "",
            )
        except (ValueError, TaskParseError) as exc:
            rejected.append(f"Line {line_number}: {exc}")
            continue
        if task.id in seen_ids:
            rejected.append(f"Line {line_number}: duplicate task id '{task.id}'")
            continue
        seen_ids.add(task.id)
        accepted.append(task)
    return ParseResult(accepted=accepted, rejected=rejected)


def parse_project_file(path: str | Path) -> Project:
    file_path = Path(path)
    tasks = parse_task_lines(file_path.read_text(encoding="utf-8")).accepted
    project = Project(name=file_path.stem.replace("_", " ").title(), tasks=tasks, team=[TeamMember(name="Alice"), TeamMember(name="Bob")])
    return project
