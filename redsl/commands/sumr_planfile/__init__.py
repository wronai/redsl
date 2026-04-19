"""SUMR.md → planfile.yaml bridge.

Reads a SUMR.md from any project, extracts refactoring decisions from:
  - ``## Refactoring Analysis`` section (embedded TOON files via markpact blocks)
  - ``redsl_refactor_plan.toon.yaml`` if present next to SUMR.md
  - ``project/analysis.toon.yaml`` / ``project/refactor_plan.yaml``

Generates or updates ``planfile.yaml`` in the project root with structured
tasks ready for planfile CLI consumption.

Public API
----------
    parse_sumr(path: Path) -> SumrData
    toon_to_tasks(toon_content: str, source: str) -> list[PlanTask]
    refactor_plan_to_tasks(yaml_content: str, source: str) -> list[PlanTask]
    generate_planfile(project_path: Path, *, dry_run: bool = False) -> PlanfileResult
"""

from __future__ import annotations

from .core import generate_planfile
from .extractors import toon_to_tasks, extract_refactor_decisions, extract_complexity_layers, extract_duplications
from .models import PlanTask, SumrData, PlanfileResult
from .parsers import parse_sumr, parse_refactor_plan_yaml


def _raw_task_status(raw: dict) -> str:
    status_raw = str(raw.get("status", "")).lower()
    if "done" in status_raw:
        return "done"
    if "in_progress" in status_raw or "in-progress" in status_raw:
        return "in_progress"
    return "todo"


def _raw_task_target(raw: dict) -> str:
    target = raw.get("file", raw.get("target", ""))
    if not target:
        locations = raw.get("locations", [])
        if locations:
            target = str(locations[0]).split(":")[0]
    return target


def _raw_task_effort(raw: dict, phase_name: str) -> str:
    effort_map = {"low": "low", "quick_wins": "low", "structural": "medium"}
    effort = effort_map.get(phase_name, "medium")
    if raw.get("saved_lines", 0) >= 20:
        effort = "low"
    return effort


def _raw_task_to_plan_task(raw: dict, index: int, source: str) -> PlanTask:
    from pathlib import Path as _Path

    task_id = str(raw.get("id", ""))
    action = raw.get("type", raw.get("pattern", "refactor"))
    target = _raw_task_target(raw)
    phase_name = raw.get("_phase_name", "")

    priority_raw = raw.get("priority", 3)
    try:
        priority = int(priority_raw)
    except (TypeError, ValueError):
        priority = 3

    labels = ["refactor"]
    if phase_name:
        labels.append(phase_name.replace("_", "-"))
    if action:
        labels.append(str(action).replace("_", "-"))

    return PlanTask(
        id=task_id or f"{phase_name[:1].upper() if phase_name else 'T'}{index + 1}",
        title=f"{action}: {_Path(target).name}" if target else str(action),
        description=str(raw.get("action", "")),
        file=target,
        action=str(action),
        priority=priority,
        effort=_raw_task_effort(raw, phase_name),
        status=_raw_task_status(raw),
        labels=labels,
        source=raw.get("_source", source),
    )


def refactor_plan_to_tasks(yaml_content: str, source: str = "") -> list[PlanTask]:
    """Backward-compat alias: parse refactor_plan.yaml → list[PlanTask]."""
    raw_tasks = parse_refactor_plan_yaml(yaml_content, source)
    return [_raw_task_to_plan_task(raw, i, source) for i, raw in enumerate(raw_tasks)]


__all__ = [
    "PlanTask",
    "PlanfileResult",
    "SumrData",
    "generate_planfile",
    "parse_sumr",
    "parse_refactor_plan_yaml",
    "refactor_plan_to_tasks",
    "toon_to_tasks",
    "extract_refactor_decisions",
    "extract_complexity_layers",
    "extract_duplications",
]
