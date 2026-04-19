"""Post-apply test validation for the refactoring cycle.

Runs the project test suite after proposals are applied.  If tests that were
passing *before* the cycle now fail, the changes are rolled back via git and a
high-priority ``PlanTask`` is appended to ``planfile.yaml`` in the project root
so the regression is tracked and not forgotten.

Public API
----------
    run_tests_baseline(project_dir) -> TestResult | None
    validate_with_tests(project_dir, baseline, applied_files, report) -> bool
    create_regression_task(project_dir, test_result, applied_files) -> None
"""

from __future__ import annotations

import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from redsl.validation.test_runner import TestResult, discover_test_command, run_tests

if TYPE_CHECKING:
    from redsl.orchestrator import CycleReport

logger = logging.getLogger(__name__)

_PLANFILE_NAME = "planfile.yaml"


# ---------------------------------------------------------------------------
# Baseline capture
# ---------------------------------------------------------------------------


def run_tests_baseline(project_dir: Path) -> TestResult | None:
    """Run project tests and return the baseline result.

    Returns None when no test suite is discovered (so callers can skip).
    """
    command = discover_test_command(project_dir)
    if command is None:
        logger.info("test_validation: no test command found in %s — skipping", project_dir)
        return None

    logger.info("test_validation: capturing baseline in %s", project_dir)
    return run_tests(project_dir, command)


# ---------------------------------------------------------------------------
# Post-apply validation
# ---------------------------------------------------------------------------


def validate_with_tests(
    project_dir: Path,
    baseline: TestResult | None,
    applied_files: list[str],
    report: "CycleReport",
) -> bool:
    """Run tests after refactoring and handle regressions.

    If the baseline was passing and tests now fail:
     - Roll back changed files via ``git checkout``
     - Append a high-priority regression task to planfile.yaml
     - Record the failure in *report*

    Returns True when tests pass (or no tests exist / baseline already failed).
    """
    if baseline is None:
        return True  # no test suite → nothing to validate

    command = discover_test_command(project_dir)
    after = run_tests(project_dir, command)

    if baseline.passed and not after.passed:
        logger.error(
            "test_validation: tests BROKE after refactor in %s (%.1fs)",
            project_dir,
            after.duration,
        )
        _rollback_files(project_dir, applied_files)
        report.proposals_applied -= len(applied_files) if applied_files else 1
        report.proposals_applied = max(report.proposals_applied, 0)
        report.errors.append(
            f"test_validation: regression detected — {len(applied_files)} file(s) rolled back"
        )
        create_regression_task(project_dir, after, applied_files)
        return False

    if after.passed:
        logger.info("test_validation: tests PASS after refactor ✓ (%.1fs)", after.duration)
    else:
        logger.warning(
            "test_validation: tests were already failing before refactor — continuing"
        )
    return True


# ---------------------------------------------------------------------------
# Planfile task creation
# ---------------------------------------------------------------------------


def create_regression_task(
    project_dir: Path,
    test_result: TestResult,
    applied_files: list[str],
) -> None:
    """Append a high-priority regression PlanTask to planfile.yaml.

    Creates planfile.yaml with a minimal skeleton if it does not exist yet.
    Uses atomic write (write to temp then rename).
    """
    try:
        import yaml  # type: ignore[import]
    except ImportError:
        logger.warning("test_validation: PyYAML not available, cannot write planfile task")
        return

    planfile_path = project_dir / _PLANFILE_NAME
    data = _load_or_create_planfile(planfile_path, project_dir)

    task = _build_regression_task(test_result, applied_files, data)

    spec = data.setdefault("spec", {})
    tasks: list[dict] = spec.setdefault("tasks", [])
    tasks.append(task)

    _atomic_write_yaml(planfile_path, data, yaml)
    logger.info(
        "test_validation: regression task '%s' added to %s",
        task["id"],
        planfile_path,
    )


def _load_or_create_planfile(planfile_path: Path, project_dir: Path) -> dict:
    """Load existing planfile.yaml or return a fresh skeleton."""
    try:
        import yaml  # type: ignore[import]
    except ImportError:
        return {}

    if planfile_path.exists():
        try:
            data = yaml.safe_load(planfile_path.read_text(encoding="utf-8")) or {}
            if isinstance(data, dict):
                return data
        except Exception as exc:
            logger.warning("test_validation: failed to parse %s: %s", planfile_path, exc)

    return {
        "apiVersion": "redsl.plan/v1",
        "kind": "Planfile",
        "metadata": {
            "project": project_dir.name,
            "created": datetime.now(timezone.utc).isoformat(),
        },
        "spec": {"tasks": []},
    }


def _build_regression_task(
    test_result: TestResult,
    applied_files: list[str],
    data: dict,
) -> dict:
    """Build the regression PlanTask dict."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    task_id = f"REGRESSION-{timestamp}"

    # Avoid id collision with existing tasks
    existing_ids = {
        t.get("id", "")
        for t in (data.get("spec") or {}).get("tasks", [])
    }
    counter = 1
    while task_id in existing_ids:
        task_id = f"REGRESSION-{timestamp}-{counter}"
        counter += 1

    snippet = test_result.output[-500:].strip() if test_result.output else "(no output)"
    files_str = ", ".join(applied_files) if applied_files else "unknown"

    return {
        "id": task_id,
        "title": "Fix test regression caused by auto-refactor",
        "description": (
            f"Auto-refactor of [{files_str}] broke the test suite. "
            f"Changes were rolled back automatically.\n\n"
            f"Test output (tail):\n```\n{snippet}\n```"
        ),
        "status": "todo",
        "priority": 1,
        "effort": "low",
        "labels": ["regression", "test-failure", "auto-generated"],
        "file": applied_files[0] if applied_files else "",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "redsl:test_validation",
    }


def _atomic_write_yaml(path: Path, data: dict, yaml_module) -> None:
    """Write YAML to a temp file then rename atomically."""
    tmp = path.with_suffix(".yaml.tmp")
    try:
        tmp.write_text(
            yaml_module.dump(data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        tmp.replace(path)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


# ---------------------------------------------------------------------------
# Git rollback helpers
# ---------------------------------------------------------------------------


def _rollback_files(project_dir: Path, files: list[str]) -> None:
    """Roll back specific files via git checkout, or whole working tree as fallback."""
    if files:
        _rollback_specific(project_dir, files)
    else:
        _rollback_all(project_dir)


def _rollback_specific(project_dir: Path, files: list[str]) -> None:
    """git checkout HEAD -- <files>"""
    try:
        subprocess.run(
            ["git", "checkout", "HEAD", "--"] + files,
            cwd=project_dir,
            check=True,
            capture_output=True,
        )
        logger.info("test_validation: rolled back %d file(s) via git", len(files))
    except subprocess.CalledProcessError as exc:
        logger.error("test_validation: git rollback failed: %s", exc.stderr.decode())
        _rollback_all(project_dir)
    except FileNotFoundError:
        logger.error("test_validation: git not found, cannot rollback")


def _rollback_all(project_dir: Path) -> None:
    """git checkout -- . as a last-resort fallback."""
    try:
        subprocess.run(
            ["git", "checkout", "--", "."],
            cwd=project_dir,
            check=True,
            capture_output=True,
        )
        logger.info("test_validation: rolled back working tree via git checkout -- .")
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        logger.error("test_validation: full rollback also failed: %s", exc)


__all__ = [
    "run_tests_baseline",
    "validate_with_tests",
    "create_regression_task",
]
