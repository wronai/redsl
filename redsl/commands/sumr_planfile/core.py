"""Core planfile generation logic."""

from __future__ import annotations

import logging
from pathlib import Path

from .extractors import toon_to_tasks
from .models import PlanTask, PlanfileResult, SumrData
from .parsers import parse_sumr, parse_refactor_plan_yaml
from .utils import deduplicate_tasks, make_id_generator, merge_with_existing_planfile, tasks_to_planfile_yaml

logger = logging.getLogger(__name__)


def _collect_from_sumr_source(
    sumr_file: Path,
    project_path: Path,
) -> tuple[list[PlanTask], list[str], str, str]:
    """Collect tasks from SUMR.md and related files (Sources 1-3).

    Returns: (tasks, sources, project_name, project_version)
    """
    all_tasks: list[PlanTask] = []
    sources: list[str] = []

    try:
        sumr = parse_sumr(sumr_file)
    except Exception as exc:
        logger.warning("Failed to parse SUMR.md at %s: %s", sumr_file, exc)
        toon_paths = sorted(project_path.glob("project/*.toon.yaml"))
        toon_paths += sorted(project_path.glob("*.toon.yaml"))
        sumr = SumrData(
            project_name=project_path.name,
            project_version="0.0.0",
            refactor_sections=[],
            refactor_plan_path=None,
            toon_paths=toon_paths,
        )

    project_name = sumr.project_name
    project_version = sumr.project_version

    # Source 1: SUMR.md embedded refactoring blocks
    for idx, block in enumerate(sumr.refactor_sections):
        src = f"SUMR.md#refactoring-block-{idx+1}"
        tasks = toon_to_tasks(block, source=src, project_path=project_path)
        if tasks:
            sources.append(src)
            all_tasks.extend(tasks)

    # Source 2: project/refactor_plan.yaml
    if sumr.refactor_plan_path and sumr.refactor_plan_path.exists():
        src = str(sumr.refactor_plan_path.relative_to(project_path))
        try:
            tasks = _tasks_from_refactor_plan(sumr.refactor_plan_path, src)
            if tasks:
                sources.append(src)
                all_tasks.extend(tasks)
        except Exception as exc:
            logger.warning("Failed to parse refactor_plan.yaml: %s", exc)

    # Source 3: standalone *.toon.yaml files
    for toon_path in sumr.toon_paths:
        src = str(toon_path.relative_to(project_path))
        try:
            tasks = toon_to_tasks(toon_path.read_text(encoding="utf-8"), source=src, project_path=project_path)
            if tasks:
                sources.append(src)
                all_tasks.extend(tasks)
        except Exception as exc:
            logger.warning("Failed to parse toon file %s: %s", toon_path, exc)

    return all_tasks, sources, project_name, project_version


def _tasks_from_refactor_plan(plan_path: Path, source: str) -> list[PlanTask]:
    """Convert a redsl ``refactor_plan.yaml`` to PlanTask list."""
    from . import refactor_plan_to_tasks as _rpt
    return _rpt(
        plan_path.read_text(encoding="utf-8"),
        source=source,
    )


def _collect_from_generated_files(project_path: Path) -> tuple[list[PlanTask], list[str]]:
    """Collect tasks from redsl-generated TOON files (Source 4).

    Returns: (tasks, sources)
    """
    all_tasks: list[PlanTask] = []
    sources: list[str] = []

    for candidate in [
        project_path / "redsl_refactor_plan.toon.yaml",
        project_path / "redsl_refactor_report.toon.yaml",
    ]:
        if candidate.exists():
            src = candidate.name
            try:
                tasks = toon_to_tasks(candidate.read_text(encoding="utf-8"), source=src, project_path=project_path)
                if tasks:
                    sources.append(src)
                    all_tasks.extend(tasks)
            except Exception as exc:
                logger.warning("Failed to parse %s: %s", candidate.name, exc)

    return all_tasks, sources


def _collect_from_standalone_toons(
    project_path: Path,
    _next_id: object,
) -> tuple[list[PlanTask], list[str]]:
    """Collect tasks from standalone toon files when SUMR.md is missing."""
    all_tasks: list[PlanTask] = []
    sources: list[str] = []
    
    for toon_path in sorted(project_path.glob("project/*.toon.yaml")) + sorted(project_path.glob("*.toon.yaml")):
        src = str(toon_path.relative_to(project_path))
        try:
            tasks = toon_to_tasks(toon_path.read_text(encoding="utf-8"), source=src, project_path=project_path)
            if tasks:
                sources.append(src)
                all_tasks.extend(tasks)
        except Exception as exc:
            logger.warning("Failed to parse toon file %s: %s", toon_path, exc)
            
    return all_tasks, sources


def generate_planfile(
    project_path: Path,
    *,
    dry_run: bool = False,
    merge: bool = True,
    sumr_path: Path | None = None,
) -> PlanfileResult:
    """Generate or update planfile.yaml for *project_path* from SUMR.md.

    Parameters
    ----------
    project_path:
        Root of the target project.
    dry_run:
        If True, build tasks but do not write planfile.yaml.
    merge:
        If True and planfile.yaml exists, preserve 'in_progress'/'done' tasks.
    sumr_path:
        Override SUMR.md location (default: project_path/SUMR.md).
    """
    project_path = Path(project_path).resolve()
    sumr_file = sumr_path or project_path / "SUMR.md"
    planfile_path = project_path / "planfile.yaml"

    all_tasks: list[PlanTask] = []
    sources: list[str] = []
    project_name: str
    project_version: str

    # --- Source 1-3: SUMR.md and related files ---
    if sumr_file.exists():
        sumr_tasks, sumr_sources, project_name, project_version = _collect_from_sumr_source(
            sumr_file, project_path
        )
        all_tasks.extend(sumr_tasks)
        sources.extend(sumr_sources)
    else:
        logger.warning("SUMR.md not found at %s", sumr_file)
        project_name = project_path.name
        project_version = "0.0.0"
        _next_id = make_id_generator()
        standalone_tasks, standalone_sources = _collect_from_standalone_toons(project_path, _next_id)
        all_tasks.extend(standalone_tasks)
        sources.extend(standalone_sources)

    # --- Source 4: redsl-generated files ---
    gen_tasks, gen_sources = _collect_from_generated_files(project_path)
    all_tasks.extend(gen_tasks)
    sources.extend(gen_sources)

    # --- Dedup ---
    all_tasks = deduplicate_tasks(all_tasks)

    # --- Merge with existing planfile ---
    if merge and not dry_run:
        merge_with_existing_planfile(all_tasks, planfile_path)

    # --- Write ---
    written = False
    if not dry_run and all_tasks:
        content = tasks_to_planfile_yaml(
            all_tasks, project_name, project_version, sources
        )
        planfile_path.write_text(content, encoding="utf-8")
        written = True
        logger.info("planfile.yaml written: %d tasks → %s", len(all_tasks), planfile_path)

    return PlanfileResult(
        project_path=project_path,
        planfile_path=planfile_path,
        tasks=all_tasks,
        written=written,
        dry_run=dry_run,
        sources=sources,
    )
