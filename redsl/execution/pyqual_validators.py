"""Pyqual project validators — extracted from cycle.py."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redsl.execution.workflow import WorkflowConfig
    from redsl.orchestrator import CycleReport

logger = logging.getLogger(__name__)


def _find_project_pyqual(project_dir: Path) -> str | None:
    """Find pyqual executable that supports `tune` subcommand.

    Prefers project venv if it has `tune`, falls back to global PATH.
    """
    import shutil
    import subprocess

    def _supports_tune(exe: str) -> bool:
        try:
            r = subprocess.run(
                [exe, "tune", "--help"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return r.returncode == 0
        except Exception:
            return False

    candidates = [
        project_dir / ".venv" / "bin" / "pyqual",
        project_dir / "venv" / "bin" / "pyqual",
    ]
    for c in candidates:
        if c.exists() and _supports_tune(str(c)):
            return str(c)
    # Fall back to global pyqual
    global_exe = shutil.which("pyqual")
    return global_exe


def _pyqual_tune_conservative(exe: str, project_dir: Path) -> bool:
    """Run `pyqual tune --conservative` to relax thresholds. Returns True on success."""
    import subprocess
    try:
        proc = subprocess.run(
            [exe, "tune", "--conservative", "--config", "pyqual.yaml"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(project_dir),
        )
        if proc.returncode == 0:
            logger.info(
                "pyqual tune --conservative: thresholds relaxed in %s", project_dir.name
            )
            return True
        logger.warning(
            "pyqual tune failed in %s (rc=%d): %s",
            project_dir.name,
            proc.returncode,
            (proc.stdout + proc.stderr)[-500:],
        )
        return False
    except Exception as exc:
        logger.warning("pyqual tune error in %s: %s", project_dir.name, exc)
        return False


def _run_tune_strategy(exe: str, project_dir: Path, step, _hw) -> bool:
    """Run pyqual tune with the configured strategy. Returns True on success."""
    import subprocess

    strategy = step.tune.strategy  # conservative | aggressive
    tune_flag = f"--{strategy}"
    try:
        tune_proc = subprocess.run(
            [exe, "tune", tune_flag, "--config", "pyqual.yaml"],
            capture_output=True, text=True, timeout=60, cwd=str(project_dir),
        )
        tune_out = (tune_proc.stdout + tune_proc.stderr)

        # If metrics are missing, run `pyqual run` first to collect them
        if tune_proc.returncode != 0 and "No metrics" in tune_out and step.tune.run_on_missing_metrics:
            logger.info(
                "pyqual tune: no metrics in %s — running 'pyqual run' to collect them",
                project_dir.name,
            )
            _hw.record_event(
                "validator_tune_no_metrics",
                status="retrying",
                reason="pyqual tune: no metrics — running pyqual run first",
                details={"step": "pyqual_gates", "tune_output": tune_out[-300:]},
            )
            run_proc = subprocess.run(
                [exe, "run", "--config", "pyqual.yaml"],
                capture_output=True, text=True, timeout=300, cwd=str(project_dir),
            )
            if run_proc.returncode != 0:
                run_out = (run_proc.stdout + run_proc.stderr)[-500:]
                logger.warning("pyqual run: failed in %s: %s", project_dir.name, run_out)
                _hw.record_event(
                    "validator_tune_failed",
                    status="failed",
                    reason="pyqual run failed — could not collect metrics",
                    details={"step": "pyqual_gates", "output": run_out},
                )
                return False
            logger.info("pyqual run: collected metrics in %s", project_dir.name)
            # Retry tune after metrics are available
            tune_proc = subprocess.run(
                [exe, "tune", tune_flag, "--config", "pyqual.yaml"],
                capture_output=True, text=True, timeout=60, cwd=str(project_dir),
            )
            tune_out = (tune_proc.stdout + tune_proc.stderr)

        if tune_proc.returncode != 0:
            logger.warning("pyqual tune: failed in %s: %s", project_dir.name, tune_out[-500:])
            _hw.record_event(
                "validator_tune_failed",
                status="failed",
                reason=f"pyqual tune {tune_flag} failed",
                details={"step": "pyqual_gates", "strategy": strategy, "output": tune_out[-500:]},
            )
            return False

        logger.info("pyqual tune %s: thresholds relaxed in %s", tune_flag, project_dir.name)
        _hw.record_event(
            "validator_tune_applied",
            status="ok",
            thought=f"pyqual tune {tune_flag} relaxed thresholds in {project_dir.name}",
            details={"step": "pyqual_gates", "strategy": strategy, "output": tune_out[-300:]},
        )
        return True
    except Exception as exc:
        logger.warning("pyqual tune error in %s: %s", project_dir.name, exc)
        _hw.record_event(
            "validator_tune_failed",
            status="failed",
            reason=f"pyqual tune exception: {exc}",
            details={"step": "pyqual_gates"},
        )
        return False


def _retry_gates_after_tune(exe: str, project_dir: Path, step, _hw) -> None:
    """Re-run pyqual gates after tune. Create planfile task if still failing."""
    import subprocess

    strategy = step.tune.strategy
    proc2 = subprocess.run(
        [exe, "gates", "--config", "pyqual.yaml"],
        capture_output=True, text=True, timeout=120, cwd=str(project_dir),
    )
    if proc2.returncode == 0:
        logger.info("pyqual gates: PASSED after tune in %s", project_dir.name)
        _hw.record_event(
            "validator_gates_passed",
            status="passed",
            thought=f"pyqual gates PASSED after tune ({strategy}) in {project_dir.name}",
            details={
                "step": "pyqual_gates",
                "after_tune": True,
                "strategy": strategy,
                "output": (proc2.stdout + proc2.stderr)[-300:],
            },
        )
        return

    gates_output = (proc2.stdout + proc2.stderr)[-1000:]
    logger.warning(
        "pyqual gates: still FAILING after tune in %s — "
        "quality thresholds need manual review\n%s",
        project_dir.name, gates_output,
    )
    _hw.record_event(
        "validator_gates_failed",
        status="failed",
        reason=f"pyqual gates still failing after tune ({strategy}) — manual review needed",
        details={
            "step": "pyqual_gates",
            "after_tune": True,
            "strategy": strategy,
            "planfile_task_created": step.tune.create_planfile_task_on_failure,
            "output": gates_output,
        },
    )
    # Create a planfile task so the quality issue is addressed later
    if step.tune.create_planfile_task_on_failure:
        from redsl.execution.planfile_updater import add_quality_task
        add_quality_task(
            project_dir,
            title=f"Fix pyqual quality gates in {project_dir.name}",
            description=(
                "pyqual gates failed even after `pyqual tune --conservative`. "
                "Review quality thresholds and fix the underlying issues.\n"
                f"Last gate output:\n{gates_output[:500]}"
            ),
            priority=2,
        )


def _run_project_validators_phase(
    project_dir: Path,
    report: "CycleReport",
    workflow: "WorkflowConfig | None" = None,
) -> None:
    """Run project's own validators (pyqual) guided by WorkflowConfig.

    Behaviour is driven by the ``pyqual_gates`` step in ``workflow.validate.steps``:
    - ``enabled: auto``  — run only if ``pyqual.yaml`` exists in project
    - ``on_failure: tune`` — run ``pyqual tune`` (strategy from ``tune.strategy``) then retry
    - ``on_failure: warn`` — log warning, continue
    - ``on_failure: stop`` — log error, continue (non-fatal for now)
    """
    if report.proposals_applied == 0:
        return

    from redsl.execution.workflow import WorkflowConfig, load_workflow

    wf: WorkflowConfig = workflow or load_workflow(project_dir)
    step = wf.validate.get_step("pyqual_gates")
    if step is None:
        return

    # Resolve "auto": run only if pyqual.yaml present
    if step.enabled == "auto":
        enabled = (project_dir / "pyqual.yaml").exists()
    else:
        enabled = bool(step.enabled)

    if not enabled:
        return

    if not (project_dir / "pyqual.yaml").exists():
        logger.debug("pyqual.yaml not found in %s — skipping pyqual_gates", project_dir.name)
        return

    exe = _find_project_pyqual(project_dir)
    if not exe:
        logger.debug("pyqual.yaml found in %s but pyqual not installed", project_dir.name)
        return

    import subprocess
    from redsl.history import HistoryWriter

    _hw = HistoryWriter(project_dir)

    logger.info("=== PROJECT VALIDATORS: pyqual gates (%s) ===", project_dir.name)
    try:
        proc = subprocess.run(
            [exe, "gates", "--config", "pyqual.yaml"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(project_dir),
        )
        if proc.returncode == 0:
            logger.info("pyqual gates: PASSED in %s", project_dir.name)
            _hw.record_event(
                "validator_gates_passed",
                status="passed",
                thought=f"pyqual gates PASSED in {project_dir.name}",
                details={"step": "pyqual_gates", "output": (proc.stdout + proc.stderr)[-500:]},
            )
            return

        # Gates failed — apply on_failure strategy
        on_failure = step.on_failure
        gates_fail_output = (proc.stdout + proc.stderr)[-1000:]
        logger.warning(
            "pyqual gates: FAILED in %s (rc=%d) — on_failure=%s",
            project_dir.name, proc.returncode, on_failure,
        )
        _hw.record_event(
            "validator_gates_failed",
            status="failed",
            reason=f"pyqual gates FAILED rc={proc.returncode} on_failure={on_failure}",
            details={
                "step": "pyqual_gates",
                "returncode": proc.returncode,
                "on_failure": on_failure,
                "output": gates_fail_output,
            },
        )

        if on_failure == "tune":
            tune_ok = _run_tune_strategy(exe, project_dir, step, _hw)
            if not tune_ok:
                return
            if step.tune.retry:
                _retry_gates_after_tune(exe, project_dir, step, _hw)
        elif on_failure in ("warn", "stop"):
            logger.warning(
                "pyqual gates: FAILED in %s (on_failure=%s) — continuing",
                project_dir.name, on_failure,
            )
        # rollback not implemented for pyqual gates (no direct file to revert)

    except subprocess.TimeoutExpired:
        logger.warning("pyqual gates: timed out in %s", project_dir.name)
        _hw.record_event(
            "validator_gates_failed",
            status="failed",
            reason="pyqual gates timed out",
            details={"step": "pyqual_gates"},
        )
    except Exception as exc:
        logger.warning("pyqual gates: error in %s: %s", project_dir.name, exc)
        _hw.record_event(
            "validator_gates_failed",
            status="failed",
            reason=f"pyqual gates exception: {exc}",
            details={"step": "pyqual_gates"},
        )
