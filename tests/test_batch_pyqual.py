"""Tests for the batch pyqual multi-project orchestrator."""

from __future__ import annotations

from pathlib import Path

import pytest

from redsl.commands.batch_pyqual import (
    PyqualProjectResult,
    _find_packages,
    _build_summary,
    _PYQUAL_YAML_TEMPLATE,
)


def test_find_packages_finds_real_packages(tmp_path: Path) -> None:
    """Packages with pyproject.toml are detected."""
    pkg_a = tmp_path / "alpha"
    pkg_a.mkdir()
    (pkg_a / "pyproject.toml").write_text("[project]\nname='alpha'\n")

    pkg_b = tmp_path / "beta"
    pkg_b.mkdir()
    (pkg_b / "setup.py").write_text("# setup\n")

    # Not a package — no marker
    plain = tmp_path / "plain"
    plain.mkdir()

    # Skipped dirs
    venv = tmp_path / "venv"
    venv.mkdir()
    (venv / "pyproject.toml").write_text("[project]\n")

    hidden = tmp_path / ".hidden"
    hidden.mkdir()
    (hidden / "pyproject.toml").write_text("[project]\n")

    found = _find_packages(tmp_path)
    names = [p.name for p in found]
    assert "alpha" in names
    assert "beta" in names
    assert "plain" not in names
    assert "venv" not in names
    assert ".hidden" not in names


def test_build_summary_aggregates_correctly() -> None:
    r1 = PyqualProjectResult(name="a", path="/a", py_files=10, total_loc=500, avg_cc=5.0, gates_passed=True, gates_total=3, gates_passing=3)
    r2 = PyqualProjectResult(name="b", path="/b", py_files=20, total_loc=1200, avg_cc=8.0, redsl_fixes_applied=4, gates_passed=False, gates_total=3, gates_passing=2)

    summary = _build_summary([r1, r2])
    assert summary["projects_processed"] == 2
    assert summary["total_redsl_fixes"] == 4
    assert summary["total_py_files"] == 30
    assert summary["total_loc"] == 1700
    assert summary["projects_gates_passed"] == 1
    assert summary["total_gates_passing"] == 5
    assert summary["total_gates_total"] == 6


def test_pyqual_yaml_template_is_valid_yaml() -> None:
    import yaml
    data = yaml.safe_load(_PYQUAL_YAML_TEMPLATE.format(name="test-project"))
    assert data["pipeline"]["name"] == "quality-loop-test-project"
    assert "metrics" in data["pipeline"]
    assert "stages" in data["pipeline"]


def test_pyqual_project_result_defaults() -> None:
    r = PyqualProjectResult(name="x", path="/x")
    assert r.gates_passed is False
    assert r.pipeline_ran is False
    assert r.git_committed is False
    assert r.redsl_fixes_applied == 0
