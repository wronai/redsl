"""Project doctor — diagnose and repair common project health issues.

Thin facade that delegates to:
  - doctor_data       — Issue, DoctorReport dataclasses
  - doctor_detectors  — all detection functions
  - doctor_fixers     — all repair functions
  - doctor_helpers    — _find_pip, _fix_via_git_revert
  - doctor_indent_fixers / doctor_fstring_fixers — specialized fixers
"""

from __future__ import annotations

import logging
from pathlib import Path

from .doctor_data import DoctorReport, Issue
from .doctor_detectors import (
    detect_broken_fstrings,
    detect_broken_guards,
    detect_missing_install,
    detect_module_level_exit,
    detect_pytest_cli_collision,
    detect_stale_pycache,
    detect_stolen_indent,
    detect_version_mismatch,
)
from .doctor_fixers import (
    fix_broken_fstrings,
    fix_broken_guards,
    fix_missing_install,
    fix_module_level_exit,
    fix_pytest_collision,
    fix_stale_pycache,
    fix_stolen_indent,
    fix_version_mismatch,
)
from .doctor_helpers import _find_pip, _fix_via_git_revert
from .doctor_indent_fixers import (
    _fix_guard_in_try_block,
    _fix_guard_with_excess_indent,
    _fix_stolen_indent,
)
from .doctor_fstring_fixers import (
    _escape_fstring_body_braces,
    _fix_broken_fstring,
    _is_fstring_expr,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Detector / Fixer registries
# ---------------------------------------------------------------------------

_DETECTORS = [
    detect_broken_guards,
    detect_stolen_indent,
    detect_broken_fstrings,
    detect_stale_pycache,
    detect_missing_install,
    detect_module_level_exit,
    detect_version_mismatch,
    detect_pytest_cli_collision,
]

_FIXERS = {
    "broken_guard": fix_broken_guards,
    "stolen_indent": fix_stolen_indent,
    "broken_fstring": fix_broken_fstrings,
    "stale_cache": fix_stale_pycache,
    "missing_install": fix_missing_install,
    "module_level_exit": fix_module_level_exit,
    "version_mismatch": fix_version_mismatch,
    "pytest_collision": fix_pytest_collision,
}


# ---------------------------------------------------------------------------
# Orchestrator functions
# ---------------------------------------------------------------------------

def diagnose(root: Path) -> DoctorReport:
    """Run all detectors on a project and return a report (no fixes applied)."""
    report = DoctorReport(project=root.name)
    for detector in _DETECTORS:
        try:
            issues = detector(root)
            report.issues.extend(issues)
        except Exception as exc:
            report.errors.append(f"Detector {detector.__name__} failed: {exc}")
    return report


def heal(root: Path, dry_run: bool = False) -> DoctorReport:
    """Diagnose and fix issues in a project."""
    report = diagnose(root)

    if dry_run or not report.issues:
        return report

    categories = {i.category for i in report.issues if i.auto_fixable}
    for category in categories:
        fixer = _FIXERS.get(category)
        if fixer:
            try:
                fixer(root, report)
            except Exception as exc:
                report.errors.append(f"Fixer {category} failed: {exc}")

    return report


def heal_batch(semcod_root: Path, dry_run: bool = False) -> list[DoctorReport]:
    """Run doctor on all semcod subprojects."""
    reports: list[DoctorReport] = []
    for project_dir in sorted(semcod_root.iterdir()):
        if not project_dir.is_dir():
            continue
        if not (project_dir / "tests").is_dir():
            continue
        logger.info("Doctor: %s", project_dir.name)
        report = heal(project_dir, dry_run=dry_run)
        reports.append(report)
    return reports
