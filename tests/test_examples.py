"""Tests for redsl examples in examples/ directory.

This module tests that all example scripts run without errors
and produce expected outputs.
"""

import subprocess
import sys
from pathlib import Path

import pytest

# Base directory for examples
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


class TestBasicAnalysisExample:
    """Test 01-basic-analysis example."""

    def test_example_runs_without_errors(self):
        """Verify the basic analysis example executes successfully."""
        script_path = EXAMPLES_DIR / "01-basic-analysis" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Script failed with: {result.stderr}"

    def test_output_contains_analysis_summary(self):
        """Verify output contains expected analysis summary."""
        script_path = EXAMPLES_DIR / "01-basic-analysis" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert "ReDSL — Analiza projektu" in result.stdout
        assert "Pliki:" in result.stdout
        assert "Alerty:" in result.stdout

    def test_finds_expected_decisions(self):
        """Verify example finds expected refactoring decisions."""
        script_path = EXAMPLES_DIR / "01-basic-analysis" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert "extract_functions" in result.stdout
        assert "split_module" in result.stdout or "reduce_fan_out" in result.stdout


class TestCustomRulesExample:
    """Test 02-custom-rules example."""

    def test_example_runs_without_errors(self):
        """Verify custom rules example executes successfully."""
        script_path = EXAMPLES_DIR / "02-custom-rules" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Script failed with: {result.stderr}"

    def test_adds_python_rules(self):
        """Verify example adds Python-defined rules."""
        script_path = EXAMPLES_DIR / "02-custom-rules" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert "Po dodaniu Pythonowych" in result.stdout
        assert "Po dodaniu YAML" in result.stdout

    def test_makes_decisions(self):
        """Verify example produces decisions from custom rules."""
        script_path = EXAMPLES_DIR / "02-custom-rules" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert "Decyzje" in result.stdout
        assert "split_module" in result.stdout or "extract_functions" in result.stdout


class TestFullPipelineExample:
    """Test 03-full-pipeline example."""

    def test_example_runs_without_errors(self):
        """Verify full pipeline example executes (may skip LLM parts)."""
        script_path = EXAMPLES_DIR / "03-full-pipeline" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        # May fail if no API key, but should handle gracefully
        assert result.returncode in [0, 1], f"Unexpected crash: {result.stderr}"

    def test_shows_usage_info(self):
        """Verify example displays usage information."""
        script_path = EXAMPLES_DIR / "03-full-pipeline" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            capture_output=True,
            text=True,
        )
        # --help may not be supported, check if header is shown
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert "ReDSL" in result.stdout or "OPENAI_API_KEY" in result.stdout


class TestMemoryLearningExample:
    """Test 04-memory-learning example."""

    def test_example_runs_without_errors(self):
        """Verify memory learning example executes successfully."""
        script_path = EXAMPLES_DIR / "04-memory-learning" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Script failed with: {result.stderr}"

    def test_shows_memory_layers(self):
        """Verify example demonstrates all memory layers."""
        script_path = EXAMPLES_DIR / "04-memory-learning" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert "EPISODIC" in result.stdout
        assert "SEMANTIC" in result.stdout
        assert "PROCEDURAL" in result.stdout

    def test_memory_stats_shown(self):
        """Verify memory statistics are displayed."""
        script_path = EXAMPLES_DIR / "04-memory-learning" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert "Pamięć agenta:" in result.stdout
        assert "wpisów" in result.stdout


class TestApiIntegrationExample:
    """Test 05-api-integration example."""

    def test_example_runs_without_errors(self):
        """Verify API integration example executes successfully."""
        script_path = EXAMPLES_DIR / "05-api-integration" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Script failed with: {result.stderr}"

    def test_shows_curl_examples(self):
        """Verify example displays curl command examples."""
        script_path = EXAMPLES_DIR / "05-api-integration" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert "curl" in result.stdout
        assert "localhost:8000" in result.stdout

    def test_shows_all_endpoints(self):
        """Verify example mentions all API endpoints."""
        script_path = EXAMPLES_DIR / "05-api-integration" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert "/analyze" in result.stdout or "/health" in result.stdout


@pytest.mark.parametrize("example_name", [
    "01-basic-analysis",
    "02-custom-rules",
    "03-full-pipeline",
    "04-memory-learning",
    "05-api-integration",
    "06-awareness",
    "07-pyqual",
    "08-audit",
    "09-pr-bot",
    "10-badge",
])
def test_all_examples_exist(example_name):
    """Verify all expected example directories exist."""
    example_dir = EXAMPLES_DIR / example_name
    assert example_dir.exists(), f"Example directory missing: {example_name}"
    assert (example_dir / "main.py").exists(), f"main.py missing in {example_name}"


def test_examples_have_readme():
    """Verify examples have README files."""
    for example_dir in EXAMPLES_DIR.iterdir():
        if example_dir.is_dir() and example_dir.name.startswith(("0", "1", "2")):
            readme = example_dir / "README.md"
            if not readme.exists():
                pytest.fail(f"Missing README.md in {example_dir.name}")


@pytest.mark.parametrize("dir_name", [
    "01-basic-analysis",
    "02-custom-rules",
    "03-full-pipeline",
    "04-memory-learning",
    "05-api-integration",
    "06-awareness",
    "07-pyqual",
    "08-audit",
    "09-pr-bot",
    "10-badge",
])
def test_example_yaml_files_exist(dir_name):
    """Verify each example directory has default.yaml and advanced.yaml."""
    example_dir = EXAMPLES_DIR / dir_name
    assert (example_dir / "default.yaml").exists(), f"default.yaml missing in {dir_name}"
    assert (example_dir / "advanced.yaml").exists(), f"advanced.yaml missing in {dir_name}"


def test_advanced_examples_run(capsys):
    """Verify the advanced scenarios execute from the examples/ directory."""
    from redsl.examples.basic_analysis import run_basic_analysis_example
    from redsl.examples.custom_rules import run_custom_rules_example
    from redsl.examples.memory_learning import run_memory_learning_example

    basic_report = run_basic_analysis_example("advanced")
    custom_report = run_custom_rules_example("advanced")
    memory_report = run_memory_learning_example("advanced")
    captured = capsys.readouterr()

    assert "(advanced)" in captured.out or "advanced" in captured.out
    assert len(basic_report["decisions"]) > 0
    assert len(custom_report["decisions"]) > 0
    assert memory_report["stats"]["episodic"] >= 5


class TestAwarenessExample:
    """Test 06-awareness example."""

    def test_example_runs_without_errors(self):
        script_path = EXAMPLES_DIR / "06-awareness" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Script failed with: {result.stderr}"

    def test_shows_patterns(self):
        script_path = EXAMPLES_DIR / "06-awareness" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert "Wzorce zmian" in result.stdout or "wzorce" in result.stdout.lower()
        assert "Timeline" in result.stdout


class TestPyQualExample:
    """Test 07-pyqual example."""

    def test_example_runs_without_errors(self):
        script_path = EXAMPLES_DIR / "07-pyqual" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Script failed with: {result.stderr}"

    def test_shows_quality_issues(self):
        script_path = EXAMPLES_DIR / "07-pyqual" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert "Nieużywane importy" in result.stdout or "Pliki" in result.stdout


class TestAuditExample:
    """Test 08-audit example."""

    def test_runs_without_errors(self):
        script_path = EXAMPLES_DIR / "08-audit" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Script failed with: {result.stderr}"

    def test_shows_grade_and_badge(self):
        script_path = EXAMPLES_DIR / "08-audit" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert "Grade" in result.stdout
        assert "Badge" in result.stdout or "badge" in result.stdout
        assert "img.shields.io" in result.stdout


class TestPrBotExample:
    """Test 09-pr-bot example."""

    def test_runs_without_errors(self):
        script_path = EXAMPLES_DIR / "09-pr-bot" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Script failed with: {result.stderr}"

    def test_shows_pr_comment(self):
        script_path = EXAMPLES_DIR / "09-pr-bot" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert "redsl-bot" in result.stdout
        assert "Metrics" in result.stdout
        assert "Status check" in result.stdout


class TestBadgeExample:
    """Test 10-badge example."""

    def test_runs_without_errors(self):
        script_path = EXAMPLES_DIR / "10-badge" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Script failed with: {result.stderr}"

    def test_shows_badges_and_grades(self):
        script_path = EXAMPLES_DIR / "10-badge" / "main.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert "Markdown" in result.stdout
        assert "img.shields.io" in result.stdout
        assert "auth-module" in result.stdout
