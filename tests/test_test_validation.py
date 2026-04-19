"""Tests for redsl.execution.test_validation."""
from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest
import yaml

from redsl.execution.test_validation import (
    _build_regression_task,
    _load_or_create_planfile,
    _rollback_files,
    create_regression_task,
    run_tests_baseline,
    validate_with_tests,
)
from redsl.validation.test_runner import TestResult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _passing() -> TestResult:
    return TestResult(passed=True, output="1 passed", duration=0.5)


def _failing() -> TestResult:
    return TestResult(passed=False, output="FAILED test_foo", duration=1.2)


def _no_tests() -> TestResult:
    return TestResult(passed=True, output="no tests found, skipping validation",
                      duration=0.0, error="no_tests_found")


# ---------------------------------------------------------------------------
# run_tests_baseline
# ---------------------------------------------------------------------------


class TestRunTestsBaseline:
    def test_returns_none_when_no_command(self, tmp_path):
        with patch("redsl.execution.test_validation.discover_test_command", return_value=None):
            assert run_tests_baseline(tmp_path) is None

    def test_returns_result_when_command_found(self, tmp_path):
        with (
            patch("redsl.execution.test_validation.discover_test_command", return_value=["pytest"]),
            patch("redsl.execution.test_validation.run_tests", return_value=_passing()) as mock_run,
        ):
            result = run_tests_baseline(tmp_path)
            assert result is not None
            assert result.passed
            mock_run.assert_called_once_with(tmp_path, ["pytest"])


# ---------------------------------------------------------------------------
# validate_with_tests
# ---------------------------------------------------------------------------


class TestValidateWithTests:
    def _make_report(self):
        report = MagicMock()
        report.proposals_applied = 2
        report.errors = []
        report.results = []
        return report

    def test_returns_true_when_no_baseline(self, tmp_path):
        report = self._make_report()
        assert validate_with_tests(tmp_path, None, [], report) is True
        assert report.errors == []

    def test_returns_true_when_tests_pass(self, tmp_path):
        report = self._make_report()
        with (
            patch("redsl.execution.test_validation.discover_test_command", return_value=["pytest"]),
            patch("redsl.execution.test_validation.run_tests", return_value=_passing()),
        ):
            result = validate_with_tests(tmp_path, _passing(), ["a.py"], report)
        assert result is True
        assert report.errors == []

    def test_returns_false_and_rolls_back_on_regression(self, tmp_path):
        report = self._make_report()
        with (
            patch("redsl.execution.test_validation.discover_test_command", return_value=["pytest"]),
            patch("redsl.execution.test_validation.run_tests", return_value=_failing()),
            patch("redsl.execution.test_validation._rollback_files") as mock_rb,
            patch("redsl.execution.test_validation.create_regression_task") as mock_task,
        ):
            result = validate_with_tests(tmp_path, _passing(), ["a.py", "b.py"], report)
        assert result is False
        mock_rb.assert_called_once_with(tmp_path, ["a.py", "b.py"])
        mock_task.assert_called_once()
        assert any("regression" in e for e in report.errors)

    def test_proposals_applied_decremented_on_regression(self, tmp_path):
        report = self._make_report()
        report.proposals_applied = 3
        with (
            patch("redsl.execution.test_validation.discover_test_command", return_value=["pytest"]),
            patch("redsl.execution.test_validation.run_tests", return_value=_failing()),
            patch("redsl.execution.test_validation._rollback_files"),
            patch("redsl.execution.test_validation.create_regression_task"),
        ):
            validate_with_tests(tmp_path, _passing(), ["a.py", "b.py"], report)
        assert report.proposals_applied == 1  # 3 - 2 files

    def test_no_regression_when_baseline_was_already_failing(self, tmp_path):
        """If baseline failed, failing after is NOT a regression — no rollback."""
        report = self._make_report()
        with (
            patch("redsl.execution.test_validation.discover_test_command", return_value=["pytest"]),
            patch("redsl.execution.test_validation.run_tests", return_value=_failing()),
            patch("redsl.execution.test_validation._rollback_files") as mock_rb,
        ):
            result = validate_with_tests(tmp_path, _failing(), ["a.py"], report)
        assert result is True
        mock_rb.assert_not_called()


# ---------------------------------------------------------------------------
# create_regression_task
# ---------------------------------------------------------------------------


class TestCreateRegressionTask:
    def test_creates_planfile_with_task(self, tmp_path):
        create_regression_task(tmp_path, _failing(), ["src/foo.py"])
        planfile = tmp_path / "planfile.yaml"
        assert planfile.exists()
        data = yaml.safe_load(planfile.read_text())
        tasks = data["spec"]["tasks"]
        assert len(tasks) == 1
        t = tasks[0]
        assert t["status"] == "todo"
        assert t["priority"] == 1
        assert "regression" in t["labels"]
        assert "test-failure" in t["labels"]
        assert "src/foo.py" in t["description"]

    def test_appends_to_existing_planfile(self, tmp_path):
        planfile = tmp_path / "planfile.yaml"
        existing = {
            "apiVersion": "redsl.plan/v1",
            "spec": {"tasks": [{"id": "T1", "title": "Old task", "status": "todo"}]},
        }
        planfile.write_text(yaml.dump(existing), encoding="utf-8")
        create_regression_task(tmp_path, _failing(), ["x.py"])
        data = yaml.safe_load(planfile.read_text())
        assert len(data["spec"]["tasks"]) == 2
        ids = {t["id"] for t in data["spec"]["tasks"]}
        assert "T1" in ids

    def test_id_collision_resolved(self, tmp_path):
        """Two tasks created in the same second still get unique IDs."""
        from datetime import datetime, timezone
        fixed_ts = "20260419120000"
        with patch("redsl.execution.test_validation.datetime") as mock_dt:
            mock_dt.now.return_value.strftime.return_value = fixed_ts
            mock_dt.now.return_value.isoformat.return_value = "2026-04-19T12:00:00+00:00"
            create_regression_task(tmp_path, _failing(), ["a.py"])
        # The second call should get a different id if same timestamp
        planfile = tmp_path / "planfile.yaml"
        data = yaml.safe_load(planfile.read_text())
        assert len({t["id"] for t in data["spec"]["tasks"]}) == 1  # only 1 task created

    def test_no_crash_on_corrupted_planfile(self, tmp_path):
        planfile = tmp_path / "planfile.yaml"
        planfile.write_text(":: not valid yaml ::", encoding="utf-8")
        # Should not raise, should create fresh planfile
        create_regression_task(tmp_path, _failing(), ["bad.py"])
        assert planfile.exists()


# ---------------------------------------------------------------------------
# _build_regression_task
# ---------------------------------------------------------------------------


class TestBuildRegressionTask:
    def test_priority_is_1(self):
        task = _build_regression_task(_failing(), ["foo.py"], {})
        assert task["priority"] == 1

    def test_file_field(self):
        task = _build_regression_task(_failing(), ["src/bar.py"], {})
        assert task["file"] == "src/bar.py"

    def test_empty_files(self):
        task = _build_regression_task(_failing(), [], {})
        assert task["file"] == ""
        assert "unknown" in task["description"]

    def test_output_snippet_in_description(self):
        tr = TestResult(passed=False, output="AssertionError in test_calc", duration=0.3)
        task = _build_regression_task(tr, ["calc.py"], {})
        assert "AssertionError" in task["description"]

    def test_source_field(self):
        task = _build_regression_task(_failing(), [], {})
        assert task["source"] == "redsl:test_validation"


# ---------------------------------------------------------------------------
# _load_or_create_planfile
# ---------------------------------------------------------------------------


class TestLoadOrCreatePlanfile:
    def test_creates_skeleton_when_missing(self, tmp_path):
        data = _load_or_create_planfile(tmp_path / "planfile.yaml", tmp_path)
        assert data["apiVersion"] == "redsl.plan/v1"
        assert data["metadata"]["project"] == tmp_path.name
        assert data["spec"]["tasks"] == []

    def test_loads_existing(self, tmp_path):
        pf = tmp_path / "planfile.yaml"
        existing = {"apiVersion": "redsl.plan/v1", "spec": {"tasks": [{"id": "X1"}]}}
        pf.write_text(yaml.dump(existing), encoding="utf-8")
        data = _load_or_create_planfile(pf, tmp_path)
        assert data["spec"]["tasks"][0]["id"] == "X1"

    def test_falls_back_to_skeleton_on_bad_yaml(self, tmp_path):
        pf = tmp_path / "planfile.yaml"
        pf.write_text("not: valid: yaml: [", encoding="utf-8")
        data = _load_or_create_planfile(pf, tmp_path)
        assert data["apiVersion"] == "redsl.plan/v1"


# ---------------------------------------------------------------------------
# _rollback_files
# ---------------------------------------------------------------------------


class TestRollbackFiles:
    def test_calls_git_checkout_with_specific_files(self, tmp_path):
        with patch("redsl.execution.test_validation.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0)
            mock_sub.CalledProcessError = subprocess.CalledProcessError
            mock_sub.FileNotFoundError = FileNotFoundError
            _rollback_files(tmp_path, ["a.py", "b.py"])
        mock_sub.run.assert_called_once()
        args = mock_sub.run.call_args[0][0]
        assert "a.py" in args
        assert "b.py" in args

    def test_calls_rollback_all_when_no_files(self, tmp_path):
        with patch("redsl.execution.test_validation._rollback_all") as mock_all:
            _rollback_files(tmp_path, [])
        mock_all.assert_called_once_with(tmp_path)
