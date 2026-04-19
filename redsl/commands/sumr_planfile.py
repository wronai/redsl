"""SUMR.md → planfile.yaml bridge.

Backward-compatibility wrapper for the refactored sumr_planfile package.
All implementation moved to redsl.commands.sumr_planfile package.

Public API
----------
    parse_sumr(path: Path) -> SumrData
    toon_to_tasks(toon_content: str, source: str) -> list[PlanTask]
    refactor_plan_to_tasks(yaml_content: str, source: str) -> list[PlanTask]
    generate_planfile(project_path: Path, *, dry_run: bool = False) -> PlanfileResult
"""

from __future__ import annotations

# Re-export all public API from the package
from .sumr_planfile import (
    PlanTask,
    PlanfileResult,
    SumrData,
    generate_planfile,
    parse_sumr,
    parse_refactor_plan_yaml,
    refactor_plan_to_tasks,
    toon_to_tasks,
    extract_refactor_decisions,
    extract_complexity_layers,
    extract_duplications,
)

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
