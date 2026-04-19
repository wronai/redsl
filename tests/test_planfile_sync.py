"""Tests for SUMR → planfile bridge (redsl.commands.sumr_planfile)."""
from __future__ import annotations

import re
import textwrap
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from redsl.commands.sumr_planfile import (
    PlanTask,
    generate_planfile,
    parse_sumr,
    refactor_plan_to_tasks,
    toon_to_tasks,
)

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

TOON_DECISIONS = textwrap.dedent("""\
    REFACTOR[2] (ranked by priority):
      [1] ○ extract_function   → redsl/core.py
          WHY: 5 occurrences of 4-line block — saves 16 lines
          FILES: redsl/core.py
      [2] ○ remove_dead_code   → redsl/utils.py
          WHY: unused helper function
          FILES: redsl/utils.py
""")

TOON_LAYERS = textwrap.dedent("""\
    LAYERS:
      redsl/                          CC̄=12.0    ←in:2  →out:1
      │ heavy                      386L  0C   16m  CC=15     ←1
      │ light                      120L  0C    3m  CC=5      ←0
""")

REFACTOR_PLAN_YAML = textwrap.dedent("""\
    ---
    phase: Q1
    tasks:
      - id: Q1-T01
        action: Extract BaseConfig class
        file: redsl/config.py
        priority: 2
        status: todo
      - id: Q1-T02
        action: Add unit tests
        file: tests/test_config.py
        priority: 3
        status: done
    ---
    phase: S1
    tasks:
      - id: S1-T01
        action: Refactor CLI entrypoint
        target: redsl/cli/__init__.py
        priority: 4
        status: in_progress
""")

SUMR_MD = textwrap.dedent("""\
    # SUMR — redsl v0.9.0

    ## Metadata
    - **Project**: redsl
    - **Version**: 0.9.0

    ## Refactoring Analysis

    ```toon
    REFACTOR[1] (ranked by priority):
      [1] ○ extract_function   → redsl/core.py
          WHY: 5 occurrences of 4-line block across 3 files — saves 16 lines
          FILES: redsl/core.py
    ```
""")


# ---------------------------------------------------------------------------
# Unit: toon_to_tasks – DECISIONS[] section
# ---------------------------------------------------------------------------

def test_toon_to_tasks_decisions():
    tasks = toon_to_tasks(TOON_DECISIONS, source="test-decisions")
    assert len(tasks) == 2
    files = {t.file for t in tasks}
    assert "redsl/core.py" in files
    assert "redsl/utils.py" in files
    t = next(t for t in tasks if t.file == "redsl/core.py")
    assert t.action == "extract_function"
    assert t.source == "test-decisions"


def test_toon_to_tasks_layers_high_cc():
    tasks = toon_to_tasks(TOON_LAYERS, source="test-layers")
    # Only CC≥10 files should produce tasks
    assert len(tasks) == 1
    assert "heavy" in tasks[0].file
    assert 15 == int(re.search(r'CC=(\d+)', tasks[0].title).group(1))


# ---------------------------------------------------------------------------
# Unit: refactor_plan_to_tasks – multi-doc YAML
# ---------------------------------------------------------------------------

def test_refactor_plan_to_tasks():
    tasks = refactor_plan_to_tasks(REFACTOR_PLAN_YAML, source="refactor_plan.yaml")
    ids = {t.id for t in tasks}
    assert "Q1-T01" in ids
    assert "Q1-T02" in ids
    assert "S1-T01" in ids
    # done task keeps "done" status
    done = next(t for t in tasks if t.id == "Q1-T02")
    assert done.status == "done"
    # in_progress task keeps status
    ip = next(t for t in tasks if t.id == "S1-T01")
    assert ip.status == "in_progress"


# ---------------------------------------------------------------------------
# Integration: generate_planfile end-to-end (tmp_path)
# ---------------------------------------------------------------------------

def _write_sumr(tmp_path: Path) -> Path:
    (tmp_path / "project").mkdir(parents=True, exist_ok=True)
    sumr = tmp_path / "SUMR.md"
    sumr.write_text(SUMR_MD, encoding="utf-8")
    return sumr


def test_generate_planfile_dry_run(tmp_path):
    _write_sumr(tmp_path)
    result = generate_planfile(tmp_path, dry_run=True)
    assert result.dry_run is True
    assert result.written is False
    assert not result.planfile_path.exists()
    # Tasks parsed from inline TOON
    assert any("extract_function" in t.action or "extract" in t.title.lower() for t in result.tasks)


def test_generate_planfile_writes_yaml(tmp_path):
    _write_sumr(tmp_path)
    result = generate_planfile(tmp_path, dry_run=False)
    assert result.written is True
    assert result.planfile_path.exists()
    data = yaml.safe_load(result.planfile_path.read_text())
    assert "tasks" in data
    assert len(data["tasks"]) >= 1


def test_generate_planfile_merge_preserves_done(tmp_path):
    _write_sumr(tmp_path)
    # First run
    generate_planfile(tmp_path, dry_run=False)
    # Manually mark first task as done
    planfile_path = tmp_path / "planfile.yaml"
    data = yaml.safe_load(planfile_path.read_text())
    data["tasks"][0]["status"] = "done"
    planfile_path.write_text(yaml.dump(data), encoding="utf-8")
    # Second run with merge=True (default)
    result = generate_planfile(tmp_path, dry_run=False, merge=True)
    data2 = yaml.safe_load(result.planfile_path.read_text())
    # The previously-done task should still be done
    first_id = data["tasks"][0]["id"]
    merged_task = next(t for t in data2["tasks"] if t["id"] == first_id)
    assert merged_task["status"] == "done"


# ---------------------------------------------------------------------------
# CLI: planfile sync + show
# ---------------------------------------------------------------------------

def test_cli_planfile_sync_dry_run(tmp_path):
    from redsl.cli import cli
    _write_sumr(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["planfile", "sync", str(tmp_path), "--dry-run"])
    assert result.exit_code == 0, result.output
    assert "dry" in result.output.lower() or "plan" in result.output.lower()


def test_cli_planfile_show(tmp_path):
    from redsl.cli import cli
    _write_sumr(tmp_path)
    runner = CliRunner()
    # First sync to create planfile
    runner.invoke(cli, ["planfile", "sync", str(tmp_path)])
    # Then show
    result = runner.invoke(cli, ["planfile", "show", str(tmp_path)])
    assert result.exit_code == 0, result.output


def test_cli_planfile_sync_json_format(tmp_path):
    from redsl.cli import cli
    _write_sumr(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        cli, ["planfile", "sync", str(tmp_path), "--dry-run", "--format", "json"]
    )
    assert result.exit_code == 0, result.output
    import json
    data = json.loads(result.output)
    assert "tasks" in data
