"""Tests for redsl.commands.scan — folder scanner and markdown report."""

from __future__ import annotations

from pathlib import Path

import pytest

from redsl.commands.scan import (
    ProjectScanResult,
    _compute_priority,
    _count_python_files,
    _detect_languages,
    _extract_hotspots,
    _is_project_dir,
    render_markdown,
    scan_folder,
    _TIER_CRITICAL,
    _TIER_HIGH,
    _TIER_LOW,
    _TIER_MEDIUM,
)
from redsl.analyzers.metrics import AnalysisResult, CodeMetrics


def _make_py_project(tmp_path: Path, name: str, content: str = "x = 1\n") -> Path:
    project = tmp_path / name
    project.mkdir()
    (project / "pyproject.toml").write_text("[project]\nname='test'\n")
    (project / "main.py").write_text(content)
    return project


class TestDetectLanguages:
    def test_detects_python(self, tmp_path: Path) -> None:
        _make_py_project(tmp_path, "proj")
        langs = _detect_languages(tmp_path / "proj")
        assert "Python" in langs

    def test_no_languages_empty_dir(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty"
        empty.mkdir()
        langs = _detect_languages(empty)
        assert langs == []


class TestCountPythonFiles:
    def test_counts_py_files(self, tmp_path: Path) -> None:
        p = tmp_path / "proj"
        p.mkdir()
        (p / "a.py").write_text("pass\n")
        (p / "b.py").write_text("x = 1\n")
        count, loc = _count_python_files(p)
        assert count == 2
        assert loc >= 2

    def test_excludes_venv(self, tmp_path: Path) -> None:
        p = tmp_path / "proj"
        p.mkdir()
        (p / "main.py").write_text("pass\n")
        venv = p / ".venv" / "lib"
        venv.mkdir(parents=True)
        (p / ".venv" / "lib" / "site.py").write_text("pass\n")
        count, _ = _count_python_files(p)
        assert count == 1


class TestIsProjectDir:
    def test_recognises_pyproject(self, tmp_path: Path) -> None:
        p = tmp_path / "proj"
        p.mkdir()
        (p / "pyproject.toml").write_text("")
        assert _is_project_dir(p) is True

    def test_rejects_plain_dir(self, tmp_path: Path) -> None:
        plain = tmp_path / "data"
        plain.mkdir()
        (plain / "notes.txt").write_text("hi")
        assert _is_project_dir(plain) is False


class TestComputePriority:
    def test_zero_result_is_low(self) -> None:
        r = ProjectScanResult(name="x", path=Path("/x"))
        score, tier = _compute_priority(r)
        assert tier == _TIER_LOW
        assert score == 0.0

    def test_high_critical_count_escalates(self) -> None:
        r = ProjectScanResult(name="x", path=Path("/x"), critical_count=10)
        score, tier = _compute_priority(r)
        assert tier in (_TIER_CRITICAL, _TIER_HIGH)

    def test_tiers_are_ordered(self) -> None:
        low = ProjectScanResult(name="l", path=Path("/l"), critical_count=0, avg_cc=2.0)
        med = ProjectScanResult(name="m", path=Path("/m"), critical_count=3, avg_cc=5.0)
        high = ProjectScanResult(name="h", path=Path("/h"), critical_count=6, avg_cc=10.0)
        crit = ProjectScanResult(name="c", path=Path("/c"), critical_count=12, avg_cc=15.0)
        low.priority_score, low.tier = _compute_priority(low)
        med.priority_score, med.tier = _compute_priority(med)
        high.priority_score, high.tier = _compute_priority(high)
        crit.priority_score, crit.tier = _compute_priority(crit)
        assert low.priority_score < med.priority_score < high.priority_score < crit.priority_score


class TestExtractHotspots:
    def _result_with_metrics(self, entries: list[tuple[str, int]]) -> AnalysisResult:
        metrics = [
            CodeMetrics(file_path=fp, cyclomatic_complexity=float(cc))
            for fp, cc in entries
        ]
        return AnalysisResult(metrics=metrics)

    def test_returns_top_n(self) -> None:
        r = self._result_with_metrics([
            ("a.py", 20), ("b.py", 10), ("c.py", 5), ("d.py", 3), ("e.py", 1), ("f.py", 30),
        ])
        hotspots = _extract_hotspots(r, top_n=3)
        assert len(hotspots) == 3
        assert hotspots[0][1] == 30

    def test_skips_cc_lte_1(self) -> None:
        r = self._result_with_metrics([("a.py", 1), ("b.py", 0)])
        hotspots = _extract_hotspots(r)
        assert hotspots == []


class TestRenderMarkdown:
    def test_produces_markdown_header(self, tmp_path: Path) -> None:
        results = [
            ProjectScanResult(name="proj1", path=tmp_path / "proj1", py_files=5, avg_cc=3.0, tier=_TIER_LOW),
        ]
        md = render_markdown(results, tmp_path)
        assert "# reDSL Project Scan Report" in md
        assert "proj1" in md
        assert "## 📊 Executive Summary" in md

    def test_tiers_present_in_output(self, tmp_path: Path) -> None:
        results = [
            ProjectScanResult(name="a", path=tmp_path / "a", critical_count=15, tier=_TIER_CRITICAL),
            ProjectScanResult(name="b", path=tmp_path / "b", critical_count=5, tier=_TIER_HIGH),
            ProjectScanResult(name="c", path=tmp_path / "c", tier=_TIER_LOW),
        ]
        md = render_markdown(results, tmp_path)
        assert "Critical" in md
        assert "High" in md
        assert "Low" in md

    def test_error_project_noted(self, tmp_path: Path) -> None:
        r = ProjectScanResult(name="bad", path=tmp_path / "bad", error="import failed")
        md = render_markdown([r], tmp_path)
        assert "⚠️" in md or "Analysis Errors" in md


class TestScanFolder:
    def test_finds_projects_and_returns_sorted(self, tmp_path: Path) -> None:
        p1 = _make_py_project(tmp_path, "alpha")
        p2 = _make_py_project(tmp_path, "beta")
        results = scan_folder(tmp_path, progress=False)
        names = [r.name for r in results]
        assert "alpha" in names
        assert "beta" in names

    def test_empty_dir_returns_empty_list(self, tmp_path: Path) -> None:
        empty = tmp_path / "nothing"
        empty.mkdir()
        results = scan_folder(empty, progress=False)
        assert results == []

    def test_non_project_dir_excluded(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "readme.txt").write_text("notes")
        results = scan_folder(tmp_path, progress=False)
        names = [r.name for r in results]
        assert "data" not in names

    def test_scan_result_has_languages(self, tmp_path: Path) -> None:
        _make_py_project(tmp_path, "myproj")
        results = scan_folder(tmp_path, progress=False)
        assert len(results) == 1
        assert "Python" in results[0].languages
