"""Utility functions for SUMR planfile generation."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

import yaml

from .models import PlanTask

logger = logging.getLogger(__name__)


def make_id_generator() -> Callable[[str], str]:
    """Return a closure that generates sequential IDs with given prefix."""
    counter = [0]

    def _next_id(prefix: str) -> str:
        counter[0] += 1
        return f"{prefix}{counter[0]:02d}"

    return _next_id


def deduplicate_tasks(tasks: list[PlanTask]) -> list[PlanTask]:
    """Remove duplicate tasks with same (action, file) pair."""
    seen: set[tuple[str, str]] = set()
    deduped: list[PlanTask] = []
    for t in tasks:
        key = (t.action, t.file)
        if key not in seen:
            seen.add(key)
            deduped.append(t)
    return deduped


def merge_with_existing_planfile(
    tasks: list[PlanTask],
    planfile_path: Path,
) -> None:
    """Merge task statuses with existing planfile (preserve in_progress/done)."""
    if not planfile_path.exists():
        return

    try:
        content = planfile_path.read_text(encoding="utf-8")
        if "\ntasks:" not in content:
            return

        existing_tasks_raw = yaml.safe_load("tasks:" + content.split("\ntasks:")[1])
        existing_tasks = (existing_tasks_raw or {}).get("tasks", [])
        keep = {
            t["id"]: t
            for t in existing_tasks
            if isinstance(t, dict) and t.get("status") in ("in_progress", "done")
        }
        # Update status for tasks present in existing
        for t in tasks:
            if t.id in keep:
                t.status = keep[t.id].get("status", t.status)
    except Exception as exc:
        logger.debug("Could not merge existing planfile: %s", exc)


def tasks_to_planfile_yaml(
    tasks: list[PlanTask],
    project_name: str,
    project_version: str,
    sources: list[str],
    schema_version: str = "1.0",
) -> str:
    """Serialise tasks to planfile.yaml YAML string."""
    from datetime import date
    
    today = date.today().isoformat()

    # Group by status
    todo = [t for t in tasks if t.status == "todo"]
    done = [t for t in tasks if t.status == "done"]

    priority_labels = {1: "critical", 2: "high", 3: "medium", 4: "low"}

    header: dict[str, object] = {
        "schema": schema_version,
        "project": project_name,
        "version": project_version,
        "generated": today,
        "generator": "redsl planfile sync",
        "sources": sources,
        "stats": {
            "total": len(tasks),
            "todo": len(todo),
            "done": len(done),
        },
    }

    task_dicts = []
    for t in tasks:
        d = t.to_dict()
        d["priority_label"] = priority_labels.get(t.priority, "medium")
        task_dicts.append(d)

    output = yaml.safe_dump(header, sort_keys=False, allow_unicode=True)
    output += "\n"
    output += yaml.safe_dump({"tasks": task_dicts}, sort_keys=False, allow_unicode=True)
    return output
