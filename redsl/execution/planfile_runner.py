"""Run refactor actions from planfile tasks — extracted from planfile_updater.py."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


_PLANFILE_ACTION_MAP: dict[str, str] = {
    "reduce_complexity": "extract_functions",
    "extract_functions": "extract_functions",
    "split_module": "split_module",
    "deduplicate": "deduplicate",
    "rename_variables": "rename_variables",
    "add_type_hints": "add_type_hints",
    "remove_dead_code": "remove_dead_code",
    "simplify_conditionals": "simplify_conditionals",
    "extract_class": "extract_class",
    "remove_unused_imports": "remove_unused_imports",
}


def _planfile_action_to_refactor_action(action_str: str) -> "Any":
    """Map planfile action string to RefactorAction enum value."""
    from redsl.dsl.engine import RefactorAction
    mapped = _PLANFILE_ACTION_MAP.get(action_str, "extract_functions")
    try:
        return RefactorAction(mapped)
    except ValueError:
        return RefactorAction.EXTRACT_FUNCTIONS


def _run_direct_refactor_for_task(
    orchestrator: "Any",
    project_dir: Path,
    task_file: str,
    task_action: str,
    validate_regix: bool = False,
    rollback_on_failure: bool = False,
    use_sandbox: bool = False,
    run_tests: bool = False,
) -> "Any":
    """Force-execute a refactor action for a specific file from a planfile task.

    Bypasses DSL scoring — creates a Decision directly from the task data.
    """
    from redsl.dsl.engine import Decision
    from redsl.execution.cycle import (
        _get_applied_files,
        _new_cycle_report,
        _run_execute_phase,
        _run_project_validators_phase,
        _run_reflect_phase,
        _run_test_validation_phase,
        _run_update_planfile_phase,
        _run_validate_phase,
    )
    from redsl.execution.resolution import _consult_memory_for_decisions
    from redsl.execution.test_validation import run_tests_baseline
    from redsl.execution.validation import _snapshot_regix_before

    orchestrator._cycle_count += 1
    report = _new_cycle_report(orchestrator)

    refactor_action = _planfile_action_to_refactor_action(task_action)
    decision = Decision(
        rule_name=f"planfile:{task_action}",
        action=refactor_action,
        score=1.0,
        target_file=task_file,
        rationale=f"planfile task: {task_action} on {task_file}",
    )

    decisions = [decision]
    report.decisions_count = 1

    regix_before = _snapshot_regix_before(project_dir, validate_regix)
    _consult_memory_for_decisions(orchestrator, decisions)
    tests_baseline = run_tests_baseline(project_dir) if run_tests else None

    _run_execute_phase(orchestrator, decisions, project_dir, use_sandbox, report)
    _run_validate_phase(orchestrator, project_dir, regix_before, rollback_on_failure, validate_regix, report)
    _run_update_planfile_phase(orchestrator, project_dir, report)
    _run_project_validators_phase(project_dir, report)
    _run_test_validation_phase(orchestrator, project_dir, tests_baseline, run_tests, report)
    _run_reflect_phase(orchestrator, report)

    return report


def run_tasks_from_planfile(
    orchestrator: Any,
    project_dir: Path,
    max_actions: int = 5,
    use_code2llm: bool = False,
    validate_regix: bool = False,
    rollback_on_failure: bool = False,
    use_sandbox: bool = False,
    run_tests: bool = False,
) -> dict:
    """Iterate over planfile todo tasks and run refactor for each file directly.

    Uses ``_run_direct_refactor_for_task`` to bypass DSL scoring and force the
    action specified in the planfile task.

    Returns summary dict with keys: attempted, applied, skipped.
    """
    from redsl.execution.planfile_updater import get_todo_tasks

    todo_tasks = get_todo_tasks(project_dir)
    if not todo_tasks:
        logger.info("planfile_runner: no todo tasks in planfile.yaml for %s", project_dir)
        return {"attempted": 0, "applied": 0, "skipped": 0}

    remaining = min(max_actions, len(todo_tasks))
    attempted = applied = skipped = 0

    for task in todo_tasks[:remaining]:
        task_file = task.get("file", "")
        task_action = task.get("action", "reduce_complexity")
        task_id = task.get("id", "?")
        full_path = project_dir / task_file
        if not full_path.exists():
            logger.warning(
                "planfile_runner: task [%s] file not found: %s — skipping",
                task_id, task_file,
            )
            skipped += 1
            continue

        logger.info("planfile_runner: processing task [%s] action=%s file=%s", task_id, task_action, task_file)
        attempted += 1
        report = _run_direct_refactor_for_task(
            orchestrator,
            project_dir,
            task_file=task_file,
            task_action=task_action,
            validate_regix=validate_regix,
            rollback_on_failure=rollback_on_failure,
            use_sandbox=use_sandbox,
            run_tests=run_tests,
        )
        if report.proposals_applied > 0:
            applied += 1
            logger.info("planfile_runner: task [%s] applied successfully", task_id)
        else:
            logger.info("planfile_runner: task [%s] no changes applied (proposals_applied=0)", task_id)

    return {"attempted": attempted, "applied": applied, "skipped": skipped}
