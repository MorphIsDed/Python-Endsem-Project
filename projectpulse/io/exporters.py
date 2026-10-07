"""Helpers for export summaries and chart artifacts."""

from __future__ import annotations

from pathlib import Path


class Exporter:
    """Simple exporter for a project summary report."""

    def export_text(self, project_name: str, schedule: dict, path: str | Path) -> None:
        lines = [f"Project: {project_name}"]
        for task_id, entry in schedule.items():
            lines.append(f"{task_id}: {entry['early_start']} -> {entry['early_finish']} | critical={entry['critical']}")
        Path(path).write_text("\n".join(lines), encoding="utf-8")
