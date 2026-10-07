"""Storage ABC and JSON/XML/CSV persistence for ProjectPulse."""

from __future__ import annotations

import csv
import json
from abc import ABC, abstractmethod
from pathlib import Path
from xml.etree import ElementTree as ET

from projectpulse.core.exceptions import StorageError
from projectpulse.core.models import Dependency, Project, Task


class Storage(ABC):
    """Abstract storage backend for project files."""

    @abstractmethod
    def save(self, project: Project, path: str | Path) -> None:
        """Persist a project to a file."""

    @abstractmethod
    def load(self, path: str | Path) -> Project:
        """Load a project from a file."""


class JsonStorage(Storage):
    """JSON storage implementation."""

    def save(self, project: Project, path: str | Path) -> None:
        payload = {
            "schema_version": 1,
            "name": project.name,
            "deadline": project.deadline.isoformat() if project.deadline else None,
            "tasks": [
                {
                    "id": task.id,
                    "name": task.name,
                    "planned_start": task.planned_start.isoformat(),
                    "planned_end": task.planned_end.isoformat(),
                    "assignee": task.assignee,
                    "priority": task.priority,
                    "predecessors": [
                        {"predecessor_id": dep.predecessor_id, "lag_days": dep.lag_days}
                        for dep in task.predecessors
                    ],
                    "percent_complete": task.percent_complete,
                    "hours_per_day": task.hours_per_day,
                    "type": task.__class__.__name__,
                }
                for task in project.tasks
            ],
        }
        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def load(self, path: str | Path) -> Project:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if payload.get("schema_version") != 1:
            raise StorageError("Unsupported schema version.")
        task_objects = []
        for item in payload.get("tasks", []):
            cls_map = {
                "StandardTask": "standard",
                "MilestoneTask": "milestone",
                "BufferTask": "buffer",
                "RecurringTask": "recurring",
            }
            task_type = cls_map.get(item["type"], "standard")
            if task_type == "milestone":
                task_obj = __import__("projectpulse.core.models", fromlist=["MilestoneTask"]).MilestoneTask(
                    item["id"], item["name"], __import__("datetime").date.fromisoformat(item["planned_start"]), __import__("datetime").date.fromisoformat(item["planned_end"]), item.get("assignee"), item["priority"], [Dependency(dep["predecessor_id"], dep["lag_days"]) for dep in item.get("predecessors", [])], item.get("percent_complete", 0), item.get("hours_per_day", 8.0)
                )
            elif task_type == "buffer":
                task_obj = __import__("projectpulse.core.models", fromlist=["BufferTask"]).BufferTask(
                    item["id"], item["name"], __import__("datetime").date.fromisoformat(item["planned_start"]), __import__("datetime").date.fromisoformat(item["planned_end"]), item.get("assignee"), item["priority"], [Dependency(dep["predecessor_id"], dep["lag_days"]) for dep in item.get("predecessors", [])], item.get("percent_complete", 0), item.get("hours_per_day", 8.0)
                )
            elif task_type == "recurring":
                task_obj = __import__("projectpulse.core.models", fromlist=["RecurringTask"]).RecurringTask(
                    item["id"], item["name"], __import__("datetime").date.fromisoformat(item["planned_start"]), __import__("datetime").date.fromisoformat(item["planned_end"]), item.get("assignee"), item["priority"], [Dependency(dep["predecessor_id"], dep["lag_days"]) for dep in item.get("predecessors", [])], item.get("percent_complete", 0), item.get("hours_per_day", 8.0)
                )
            else:
                task_obj = __import__("projectpulse.core.models", fromlist=["StandardTask"]).StandardTask(
                    item["id"], item["name"], __import__("datetime").date.fromisoformat(item["planned_start"]), __import__("datetime").date.fromisoformat(item["planned_end"]), item.get("assignee"), item["priority"], [Dependency(dep["predecessor_id"], dep["lag_days"]) for dep in item.get("predecessors", [])], item.get("percent_complete", 0), item.get("hours_per_day", 8.0)
                )
            task_objects.append(task_obj)
        return Project(name=payload.get("name", "Loaded Project"), tasks=task_objects)


class CsvStorage(Storage):
    """CSV export/import storage."""

    def save(self, project: Project, path: str | Path) -> None:
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["id", "name", "planned_start", "planned_end", "assignee", "priority", "percent_complete"])
            for task in project.tasks:
                writer.writerow([task.id, task.name, task.planned_start.isoformat(), task.planned_end.isoformat(), task.assignee or "", task.priority, task.percent_complete])

    def load(self, path: str | Path) -> Project:
        with open(path, newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        tasks = []
        for row in rows:
            from datetime import date
            tasks.append(
                StandardTask(
                    row["id"],
                    row["name"],
                    date.fromisoformat(row["planned_start"]),
                    date.fromisoformat(row["planned_end"]),
                    row.get("assignee") or None,
                    int(row["priority"]),
                    percent_complete=float(row.get("percent_complete", 0)),
                )
            )
        return Project(name="Imported CSV", tasks=tasks)
