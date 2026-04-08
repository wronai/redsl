"""Data models for project doctor."""

from dataclasses import dataclass, field
from typing import Any

@dataclass
class Issue:
    """A single detected issue."""
    category: str
    path: str
    description: str
    auto_fixable: bool = True

@dataclass
class DoctorReport:
    """Aggregated report for one project."""
    project: str
    issues: list[Issue] = field(default_factory=list)
    fixes_applied: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return not self.issues and not self.errors

    def summary_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "issues_found": len(self.issues),
            "fixes_applied": len(self.fixes_applied),
            "errors": len(self.errors),
            "healthy": self.healthy,
            "details": {
                "issues": [
                    {"category": i.category, "path": i.path, "description": i.description, "auto_fixable": i.auto_fixable}
                    for i in self.issues
                ],
                "fixes": self.fixes_applied,
                "errors": self.errors,
            },
        }
