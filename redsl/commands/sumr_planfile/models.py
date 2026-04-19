"""Data models for SUMR.md → planfile.yaml bridge."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PlanTask:
    id: str
    title: str
    description: str
    file: str
    action: str
    priority: int = 3          # 1=critical, 2=high, 3=medium, 4=low
    effort: str = "medium"   # low | medium | high
    status: str = "todo"     # todo | in_progress | done
    labels: list[str] = field(default_factory=list)
    source: str = ""          # where task came from

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "file": self.file,
            "action": self.action,
            "priority": self.priority,
            "effort": self.effort,
            "status": self.status,
            "labels": self.labels,
            "source": self.source,
        }


@dataclass
class SumrData:
    project_name: str
    project_version: str
    refactor_sections: list[str]         # raw TOON/yaml text blocks
    refactor_plan_path: Path | None        # path to refactor_plan.yaml if found
    toon_paths: list[Path]                 # paths to *.toon.yaml files found


@dataclass
class PlanfileResult:
    project_path: Path
    planfile_path: Path
    tasks: list[PlanTask]
    written: bool
    dry_run: bool
    sources: list[str]
