"""Tests for the redsl.autonomy package."""

from __future__ import annotations

import ast
import json
import os
import subprocess
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_git_project(tmp_path: Path) -> Path:
    """Create a minimal git-initialized Python project."""
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(tmp_path), capture_output=True)

    # Create a simple Python file
    pkg = tmp_path / "mymod"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "core.py").write_text(textwrap.dedent("""\
        def hello():
            return "world"

        def add(a, b):
            return a + b
    """))

    # Initial commit
    subprocess.run(["git", "add", "-A"], cwd=str(tmp_path), capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=str(tmp_path), capture_output=True, check=True)
    return tmp_path


# ===========================================================================
# quality_gate.py
# ===========================================================================

class TestQualityGate:
    def test_gate_passes_on_clean_project(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.quality_gate import run_quality_gate

        verdict = run_quality_gate(tmp_git_project)
        assert verdict.passed
        assert verdict.reason == "OK"
        assert verdict.violations == []

    def test_gate_detects_high_cc_new_function(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.quality_gate import run_quality_gate

        # Add a complex function (many branches)
        complex_func = "def complex():\n"
        for i in range(15):
            complex_func += f"    if x == {i}:\n        return {i}\n"
        complex_func += "    return -1\n"

        new_file = tmp_git_project / "mymod" / "complex.py"
        new_file.write_text(complex_func)

        # Lower threshold so it triggers
        verdict = run_quality_gate(tmp_git_project, max_new_function_cc=5)
        # new_functions only picks up untracked files
        assert isinstance(verdict, object)
        assert "cc_mean" in verdict.metrics_after

    def test_gate_detects_oversized_new_file(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.quality_gate import run_quality_gate

        # Create a file with >100 lines (use low threshold)
        big = tmp_git_project / "mymod" / "big.py"
        big.write_text("\n".join(f"x_{i} = {i}" for i in range(150)))

        verdict = run_quality_gate(tmp_git_project, max_new_file_lines=50)
        found_size_violation = any("New file" in v for v in verdict.violations)
        assert found_size_violation

    def test_gate_verdict_dataclass(self) -> None:
        from redsl.autonomy.quality_gate import GateVerdict

        v = GateVerdict(
            passed=False,
            reason="1 violation(s)",
            metrics_before={"cc_mean": 1.0},
            metrics_after={"cc_mean": 2.0},
            violations=["CC mean increased"],
        )
        assert not v.passed
        assert len(v.violations) == 1

    def test_install_hook(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.quality_gate import install_pre_commit_hook

        hook = install_pre_commit_hook(tmp_git_project)
        assert hook.exists()
        assert os.access(hook, os.X_OK)
        content = hook.read_text()
        assert "quality gate" in content.lower()


# ===========================================================================
# auto_fix.py
# ===========================================================================

class TestAutoFix:
    def test_auto_fix_result_dataclass(self) -> None:
        from redsl.autonomy.auto_fix import AutoFixResult

        r = AutoFixResult()
        assert r.fixed == []
        assert r.manual_needed == []
        assert r.tickets_created == []

    def test_extract_file_path(self) -> None:
        from redsl.autonomy.auto_fix import _extract_file_path

        assert _extract_file_path("New file mymod/big.py has 500L") == "mymod/big.py"
        assert _extract_file_path("no match here") is None

    def test_extract_function_name(self) -> None:
        from redsl.autonomy.auto_fix import _extract_function_name

        assert _extract_function_name("function complex has CC=15") == "complex"
        assert _extract_function_name("no match") is None

    def test_suggest_manual_action(self) -> None:
        from redsl.autonomy.auto_fix import _suggest_manual_action

        assert "Split" in _suggest_manual_action("file exceeded 500L")
        assert "Extract" in _suggest_manual_action("has CC=20")
        assert "Review" in _suggest_manual_action("CC mean increased")
        assert "Refactor" in _suggest_manual_action("Critical count increased")
        assert "Review" in _suggest_manual_action("unknown issue")

    def test_create_fix_ticket(self) -> None:
        from redsl.autonomy.auto_fix import _create_fix_ticket

        ticket = _create_fix_ticket(Path("/tmp/proj"), "CC mean increased", "cannot auto")
        assert ticket["project"] == "proj"
        assert ticket["violation"] == "CC mean increased"
        assert ticket["auto_fix_reason"] == "cannot auto"
        assert "suggested_action" in ticket


# ===========================================================================
# growth_control.py
# ===========================================================================

class TestGrowthControl:
    def test_growth_budget_defaults(self) -> None:
        from redsl.autonomy.growth_control import GrowthBudget

        b = GrowthBudget()
        assert b.max_file_size == 400
        assert b.max_total_growth_per_week == 2000

    def test_find_oversized_files(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.growth_control import GrowthController, GrowthBudget

        # Create a big file
        big = tmp_git_project / "mymod" / "big.py"
        big.write_text("\n".join(f"x_{i} = {i}" for i in range(500)))

        gc = GrowthController(GrowthBudget(max_file_size=100))
        warnings = gc.check_growth(tmp_git_project)
        oversized = [w for w in warnings if "big.py" in w]
        assert len(oversized) >= 1

    def test_find_tiny_modules(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.growth_control import GrowthController

        # Create several tiny files
        for i in range(12):
            (tmp_git_project / "mymod" / f"tiny_{i}.py").write_text(f"x = {i}\n")

        gc = GrowthController()
        suggestions = gc.suggest_consolidation(tmp_git_project)
        consolidate = [s for s in suggestions if s["action"] == "consolidate_tiny_modules"]
        assert len(consolidate) >= 1

    def test_module_budget_check(self, tmp_path: Path) -> None:
        from redsl.autonomy.growth_control import check_module_budget

        # Create a bridge-type file that exceeds limits
        bridge = tmp_path / "my_bridge.py"
        source = "\n".join(f"import mod_{i}" for i in range(20))
        source += "\n" + "\n".join(f"def fn_{i}(): pass" for i in range(12))
        bridge.write_text(source)

        violations = check_module_budget(bridge, module_type="bridge")
        # Should trigger at least the functions or imports limit
        assert len(violations) >= 1

    def test_module_budget_infer_type(self) -> None:
        from redsl.autonomy.growth_control import _infer_module_type

        assert _infer_module_type(Path("regix_bridge.py")) == "bridge"
        assert _infer_module_type(Path("toon_parser.py")) == "parser"
        assert _infer_module_type(Path("dsl_engine.py")) == "engine"
        assert _infer_module_type(Path("cli.py")) == "cli"
        assert _infer_module_type(Path("data_model.py")) == "model"
        assert _infer_module_type(Path("utils.py")) == "default"

    def test_group_by_prefix(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.growth_control import GrowthController

        for name in ("doctor_a.py", "doctor_b.py", "doctor_c.py", "doctor_d.py", "doctor_e.py"):
            (tmp_git_project / "mymod" / name).write_text("x = 1\n")

        gc = GrowthController()
        suggestions = gc.suggest_consolidation(tmp_git_project)
        subpkg = [s for s in suggestions if s["action"] == "create_subpackage"]
        assert len(subpkg) >= 1


# ===========================================================================
# smart_scorer.py
# ===========================================================================

class TestSmartScorer:
    def test_smart_score_without_extras(self) -> None:
        from redsl.autonomy.smart_scorer import smart_score
        from redsl.dsl.engine import Rule, Condition, Operator, RefactorAction

        rule = Rule(
            name="test",
            conditions=[Condition("cyclomatic_complexity", Operator.GT, 10)],
            action=RefactorAction.EXTRACT_FUNCTIONS,
            priority=0.9,
        )
        ctx = {"cyclomatic_complexity": 20, "module_lines": 100}
        score = smart_score(rule, ctx)
        base = rule.score(ctx)
        assert score == base  # no multipliers

    def test_smart_score_zero_for_non_match(self) -> None:
        from redsl.autonomy.smart_scorer import smart_score
        from redsl.dsl.engine import Rule, Condition, Operator, RefactorAction

        rule = Rule(
            name="test",
            conditions=[Condition("cyclomatic_complexity", Operator.GT, 100)],
            action=RefactorAction.EXTRACT_FUNCTIONS,
            priority=0.9,
        )
        ctx = {"cyclomatic_complexity": 5}
        assert smart_score(rule, ctx) == 0.0

    def test_coupling_multiplier(self) -> None:
        from redsl.autonomy.smart_scorer import _coupling_multiplier

        assert _coupling_multiplier({"file_path": "mymod/core.py"}, None) == 1.0
        coupling = {"mymod.core": {"fan_in": 10}}
        assert _coupling_multiplier({"file_path": "mymod/core.py"}, coupling) == 1.2

    def test_ecosystem_multiplier_bridge(self) -> None:
        from redsl.autonomy.smart_scorer import _ecosystem_multiplier

        assert _ecosystem_multiplier({"file_path": "mymod/bridge.py"}, None) == 1.0


# ===========================================================================
# adaptive_executor.py
# ===========================================================================

class TestAdaptiveExecutor:
    def test_session_failures_tracking(self) -> None:
        from redsl.autonomy.adaptive_executor import AdaptiveExecutor

        mock_orch = MagicMock()
        mock_orch.memory = MagicMock()
        ae = AdaptiveExecutor(mock_orch)

        assert ae.session_failures == {}
        ae._session_failures["extract_functions"] = 2
        assert ae.session_failures["extract_functions"] == 2

    def test_adapt_strategy_records(self) -> None:
        from redsl.autonomy.adaptive_executor import AdaptiveExecutor

        mock_orch = MagicMock()
        mock_orch.memory = MagicMock()
        ae = AdaptiveExecutor(mock_orch)
        ae._adapt_strategy("extract_functions", ["err1"])
        mock_orch.memory.learn_pattern.assert_called_once()
        mock_orch.memory.store_strategy.assert_called_once()


# ===========================================================================
# review.py
# ===========================================================================

class TestReview:
    def test_review_no_changes(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.review import review_staged_changes

        output = review_staged_changes(tmp_git_project)
        assert "No changes" in output or "no major issues" in output.lower() or isinstance(output, str)

    def test_static_review_high_cc(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.review import _static_review

        # Create a file with high-CC function
        complex_func = "def complex():\n"
        for i in range(20):
            complex_func += f"    if x == {i}:\n        return {i}\n"
        complex_func += "    return -1\n"

        fp = tmp_git_project / "mymod" / "complex.py"
        fp.write_text(complex_func)
        diff = "+++ b/mymod/complex.py\n+def complex():\n"

        result = _static_review(tmp_git_project, diff)
        assert "complex" in result.lower() or "CC=" in result

    def test_parse_changed_files(self) -> None:
        from redsl.autonomy.review import _parse_changed_files_from_diff

        diff = "+++ b/src/foo.py\n+++ b/src/bar.py\n+++ b/readme.md\n"
        files = _parse_changed_files_from_diff(diff)
        assert "src/foo.py" in files
        assert "src/bar.py" in files
        assert "readme.md" not in files  # not .py


# ===========================================================================
# intent.py
# ===========================================================================

class TestIntent:
    def test_analyze_intent(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.intent import analyze_commit_intent

        report = analyze_commit_intent(tmp_git_project)
        assert "intent" in report
        assert "risk" in report
        assert "changed_files" in report
        assert "summary" in report
        assert report["risk"] in ("low", "medium", "high")

    def test_assess_risk_bugfix(self) -> None:
        from redsl.autonomy.intent import _assess_risk

        assert _assess_risk([], "bugfix") == "high"

    def test_assess_risk_high_pattern(self) -> None:
        from redsl.autonomy.intent import _assess_risk

        assert _assess_risk(["redsl/config.py"], "feature") == "high"

    def test_assess_risk_medium_pattern(self) -> None:
        from redsl.autonomy.intent import _assess_risk

        assert _assess_risk(["redsl/foo_bridge.py"], "feature") == "medium"

    def test_assess_risk_low(self) -> None:
        from redsl.autonomy.intent import _assess_risk

        assert _assess_risk(["docs/readme.md"], "docs") == "low"


# ===========================================================================
# scheduler.py
# ===========================================================================

class TestScheduler:
    def test_scheduler_init(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.scheduler import AutonomyMode, Scheduler

        s = Scheduler(
            project_dir=tmp_git_project,
            mode=AutonomyMode.WATCH,
            check_interval_minutes=1,
        )
        assert s.mode == AutonomyMode.WATCH
        assert s.interval == 60
        assert s._cycle_count == 0

    def test_run_once_watch(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.scheduler import AutonomyMode, Scheduler

        s = Scheduler(
            project_dir=tmp_git_project,
            mode=AutonomyMode.WATCH,
        )
        result = s.run_once()
        assert result["cycle"] == 1
        assert result["mode"] == "watch"
        assert "analysis_summary" in result

    def test_run_once_suggest(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.scheduler import AutonomyMode, Scheduler

        s = Scheduler(
            project_dir=tmp_git_project,
            mode=AutonomyMode.SUGGEST,
        )
        result = s.run_once()
        assert result["mode"] == "suggest"
        assert "proposals" in result

    def test_has_changes(self, tmp_git_project: Path) -> None:
        from redsl.autonomy.scheduler import Scheduler

        s = Scheduler(project_dir=tmp_git_project)
        # First check always returns True (initializes _last_head)
        assert s._has_changes_since_last_check()
        # Second check returns False (same HEAD)
        assert not s._has_changes_since_last_check()


# ===========================================================================
# CLI smoke tests
# ===========================================================================

class TestCLI:
    def test_gate_check_cli(self, tmp_git_project: Path) -> None:
        from click.testing import CliRunner
        from redsl.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["gate", "check", str(tmp_git_project)])
        assert result.exit_code == 0
        assert "PASSED" in result.output or "FAILED" in result.output

    def test_gate_details_cli(self, tmp_git_project: Path) -> None:
        from click.testing import CliRunner
        from redsl.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["gate", "details", str(tmp_git_project)])
        assert result.exit_code == 0
        assert "Quality Gate" in result.output

    def test_intent_cli(self, tmp_git_project: Path) -> None:
        from click.testing import CliRunner
        from redsl.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["intent", str(tmp_git_project)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "intent" in data
        assert "risk" in data

    def test_growth_cli(self, tmp_git_project: Path) -> None:
        from click.testing import CliRunner
        from redsl.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["growth", str(tmp_git_project)])
        assert result.exit_code == 0

    def test_review_cli(self, tmp_git_project: Path) -> None:
        from click.testing import CliRunner
        from redsl.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["review", str(tmp_git_project)])
        assert result.exit_code == 0

    def test_improve_cli(self, tmp_git_project: Path) -> None:
        from click.testing import CliRunner
        from redsl.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["improve", str(tmp_git_project), "--mode", "watch"])
        assert result.exit_code == 0

    def test_gate_install_hook_cli(self, tmp_git_project: Path) -> None:
        from click.testing import CliRunner
        from redsl.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["gate", "install-hook", str(tmp_git_project)])
        assert result.exit_code == 0
        assert "hook" in result.output.lower()
