"""Bridge to redeploy — infrastructure migration toolkit (detect → plan → apply).

Wraps the `redeploy` package for use within redsl pipelines.
All public functions degrade gracefully when redeploy is not installed.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def is_available() -> bool:
    """Return True if the redeploy package is installed and importable."""
    try:
        import redeploy  # noqa: F401
        return True
    except ImportError:
        return False


def _unavailable(action: str) -> dict[str, Any]:
    return {"available": False, "error": f"redeploy not installed — cannot {action}"}


# ── detect ────────────────────────────────────────────────────────────────────

def detect(host: str, app: str = "app", domain: Optional[str] = None) -> dict[str, Any]:
    """Probe infrastructure on *host* and return InfraState as a dict.

    Args:
        host: SSH target (``user@ip``) or ``"local"``.
        app:  Application name used for service discovery.
        domain: Public domain for HTTP health probes.

    Returns:
        Dict with ``available``, ``state`` (InfraState dict), ``strategy``,
        ``version``, ``conflicts`` keys.  On failure: ``error`` key.
    """
    if not is_available():
        return _unavailable("detect")
    try:
        from redeploy.detect import Detector
        d = Detector(host=host, app=app, domain=domain)
        state = d.run()
        return {
            "available": True,
            "state": state.model_dump(mode="json"),
            "strategy": state.detected_strategy.value,
            "version": state.current_version,
            "conflicts": [c.model_dump(mode="json") for c in state.conflicts],
        }
    except Exception as exc:
        logger.warning("redeploy detect failed: %s", exc)
        return {"available": True, "error": str(exc)}


def detect_and_save(host: str, output: Path, app: str = "app",
                    domain: Optional[str] = None) -> dict[str, Any]:
    """Run detect and save InfraState YAML to *output*.  Returns same dict as :func:`detect`."""
    if not is_available():
        return _unavailable("detect")
    try:
        from redeploy.detect import Detector
        d = Detector(host=host, app=app, domain=domain)
        state = d.run()
        d.save(state, Path(output))
        return {
            "available": True,
            "state": state.model_dump(mode="json"),
            "strategy": state.detected_strategy.value,
            "version": state.current_version,
            "conflicts": [c.model_dump(mode="json") for c in state.conflicts],
            "saved_to": str(output),
        }
    except Exception as exc:
        logger.warning("redeploy detect_and_save failed: %s", exc)
        return {"available": True, "error": str(exc)}


# ── plan ──────────────────────────────────────────────────────────────────────

def plan(
    infra_path: Path,
    target_path: Optional[Path] = None,
    *,
    strategy: Optional[str] = None,
    domain: Optional[str] = None,
    version: Optional[str] = None,
    compose_files: Optional[list[str]] = None,
    env_file: Optional[str] = None,
) -> dict[str, Any]:
    """Generate a MigrationPlan from *infra_path* + optional *target_path*.

    Returns dict with ``available``, ``plan`` (MigrationPlan dict),
    ``steps``, ``risk``, ``estimated_downtime``.
    """
    if not is_available():
        return _unavailable("plan")
    try:
        from redeploy.plan import Planner
        from redeploy.models import DeployStrategy

        planner = Planner.from_files(Path(infra_path), Path(target_path) if target_path else None)
        if strategy:
            planner.target.strategy = DeployStrategy(strategy)
        if domain:
            planner.target.domain = domain
        if version:
            planner.target.verify_version = version
        if compose_files:
            planner.target.compose_files = list(compose_files)
        if env_file:
            planner.target.env_file = env_file

        migration = planner.run()
        return {
            "available": True,
            "plan": migration.model_dump(mode="json"),
            "steps": len(migration.steps),
            "risk": migration.risk.value,
            "estimated_downtime": migration.estimated_downtime,
        }
    except Exception as exc:
        logger.warning("redeploy plan failed: %s", exc)
        return {"available": True, "error": str(exc)}


def plan_from_spec(spec_path: Path) -> dict[str, Any]:
    """Generate a MigrationPlan from a single migration spec YAML (source + target)."""
    if not is_available():
        return _unavailable("plan_from_spec")
    try:
        from redeploy.models import MigrationSpec
        from redeploy.plan import Planner

        spec = MigrationSpec.from_file(Path(spec_path))
        planner = Planner.from_spec(spec)
        migration = planner.run()
        return {
            "available": True,
            "plan": migration.model_dump(mode="json"),
            "steps": len(migration.steps),
            "risk": migration.risk.value,
            "estimated_downtime": migration.estimated_downtime,
            "from_strategy": migration.from_strategy.value,
            "to_strategy": migration.to_strategy.value,
        }
    except Exception as exc:
        logger.warning("redeploy plan_from_spec failed: %s", exc)
        return {"available": True, "error": str(exc)}


def plan_and_save(
    infra_path: Path,
    output: Path,
    target_path: Optional[Path] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Like :func:`plan` but also saves the plan YAML to *output*."""
    if not is_available():
        return _unavailable("plan_and_save")
    try:
        from redeploy.plan import Planner
        from redeploy.models import DeployStrategy

        planner = Planner.from_files(Path(infra_path), Path(target_path) if target_path else None)
        if kwargs.get("strategy"):
            planner.target.strategy = DeployStrategy(kwargs["strategy"])
        if kwargs.get("domain"):
            planner.target.domain = kwargs["domain"]
        if kwargs.get("version"):
            planner.target.verify_version = kwargs["version"]
        if kwargs.get("compose_files"):
            planner.target.compose_files = list(kwargs["compose_files"])
        if kwargs.get("env_file"):
            planner.target.env_file = kwargs["env_file"]

        migration = planner.run()
        planner.save(migration, Path(output))
        return {
            "available": True,
            "plan": migration.model_dump(mode="json"),
            "steps": len(migration.steps),
            "risk": migration.risk.value,
            "estimated_downtime": migration.estimated_downtime,
            "saved_to": str(output),
        }
    except Exception as exc:
        logger.warning("redeploy plan_and_save failed: %s", exc)
        return {"available": True, "error": str(exc)}


# ── apply ─────────────────────────────────────────────────────────────────────

def apply(plan_path: Path, *, dry_run: bool = False,
          step_id: Optional[str] = None) -> dict[str, Any]:
    """Execute a MigrationPlan from *plan_path*.

    Returns dict with ``available``, ``ok``, ``summary``, ``results``.
    """
    if not is_available():
        return _unavailable("apply")
    try:
        from redeploy.apply import Executor

        executor = Executor.from_file(Path(plan_path))
        if step_id:
            matched = [s for s in executor.plan.steps if s.id == step_id]
            if not matched:
                return {"available": True, "error": f"step '{step_id}' not found"}
            executor.plan.steps = matched
        executor.dry_run = dry_run
        ok = executor.run()
        return {
            "available": True,
            "ok": ok,
            "summary": executor.summary(),
            "dry_run": dry_run,
            "results": [
                {"id": s.id, "status": s.status.value, "result": s.result, "error": s.error}
                for s in executor.plan.steps
            ],
        }
    except Exception as exc:
        logger.warning("redeploy apply failed: %s", exc)
        return {"available": True, "error": str(exc)}


# ── full pipeline ─────────────────────────────────────────────────────────────

def run_spec(spec_path: Path, *, dry_run: bool = False,
             plan_only: bool = False, do_detect: bool = False,
             plan_out: Optional[Path] = None) -> dict[str, Any]:
    """Run the full pipeline from a migration spec YAML (source + target).

    Wraps ``redeploy run`` command logic without spawning a subprocess.

    Returns dict with ``available``, ``ok``, ``plan``, ``results``, ``summary``.
    """
    if not is_available():
        return _unavailable("run_spec")
    try:
        from redeploy.models import MigrationSpec
        from redeploy.plan import Planner
        from redeploy.apply import Executor

        spec = MigrationSpec.from_file(Path(spec_path))

        if do_detect:
            from redeploy.detect import Detector
            d = Detector(host=spec.source.host, app=spec.source.app, domain=spec.source.domain)
            state = d.run()
            planner = Planner(state, spec.to_target_config())
            planner._spec = spec
        else:
            planner = Planner.from_spec(spec)

        migration = planner.run()

        if plan_out:
            planner.save(migration, Path(plan_out))

        plan_dict = migration.model_dump(mode="json")

        if plan_only:
            return {
                "available": True,
                "ok": True,
                "plan_only": True,
                "plan": plan_dict,
                "steps": len(migration.steps),
                "risk": migration.risk.value,
                "estimated_downtime": migration.estimated_downtime,
            }

        executor = Executor(migration, dry_run=dry_run)
        ok = executor.run()
        return {
            "available": True,
            "ok": ok,
            "dry_run": dry_run,
            "plan": plan_dict,
            "steps": len(migration.steps),
            "risk": migration.risk.value,
            "summary": executor.summary(),
            "results": [
                {"id": s.id, "status": s.status.value, "result": s.result, "error": s.error}
                for s in migration.steps
            ],
        }
    except Exception as exc:
        logger.warning("redeploy run_spec failed: %s", exc)
        return {"available": True, "error": str(exc)}


def migrate(
    host: str,
    *,
    app: str = "app",
    domain: Optional[str] = None,
    strategy: str = "docker_full",
    version: Optional[str] = None,
    compose_files: Optional[list[str]] = None,
    env_file: Optional[str] = None,
    dry_run: bool = False,
    infra_out: Optional[Path] = None,
    plan_out: Optional[Path] = None,
) -> dict[str, Any]:
    """Full detect → plan → apply pipeline without intermediate YAML files.

    Returns dict with ``available``, ``ok``, ``strategy``, ``conflicts``,
    ``steps``, ``risk``, ``summary``, ``results``.
    """
    if not is_available():
        return _unavailable("migrate")
    try:
        from redeploy.detect import Detector
        from redeploy.plan import Planner
        from redeploy.apply import Executor
        from redeploy.models import DeployStrategy, TargetConfig

        d = Detector(host=host, app=app, domain=domain)
        state = d.run()
        if infra_out:
            d.save(state, Path(infra_out))

        target = TargetConfig(
            strategy=DeployStrategy(strategy),
            app=app,
            version=version,
            compose_files=compose_files or [],
            env_file=env_file,
            remote_dir=f"~/{app}",
            domain=domain,
            verify_version=version,
        )
        planner = Planner(state, target)
        migration = planner.run()
        if plan_out:
            planner.save(migration, Path(plan_out))

        executor = Executor(migration, dry_run=dry_run)
        ok = executor.run()
        return {
            "available": True,
            "ok": ok,
            "dry_run": dry_run,
            "strategy": state.detected_strategy.value,
            "conflicts": len(state.conflicts),
            "steps": len(migration.steps),
            "risk": migration.risk.value,
            "summary": executor.summary(),
            "results": [
                {"id": s.id, "status": s.status.value, "result": s.result, "error": s.error}
                for s in migration.steps
            ],
        }
    except Exception as exc:
        logger.warning("redeploy migrate failed: %s", exc)
        return {"available": True, "error": str(exc)}
