"""Project analysis steps for the autonomous PR workflow."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import click

from .models import _AnalysisResult, _ApplyResult


def _parse_worktree_changes(status_output: str) -> list[str]:
    """Parse `git status --porcelain` output into a list of file paths."""
    paths: list[str] = []
    for line in status_output.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip()
        if path:
            paths.append(path)
    return paths


def _split_generated_and_real_changes(paths: list[str]) -> tuple[list[str], list[str]]:
    """Separate real source changes from generated reports/logs."""
    generated_names = {"redsl_refactor_plan.md", "redsl_refactor_report.md"}
    real_changes: list[str] = []
    generated_changes: list[str] = []

    for path in paths:
        normalized = path.replace("\\", "/")
        if normalized.startswith(".redsl/") or normalized.startswith("logs/"):
            continue
        if Path(normalized).name in generated_names:
            generated_changes.append(path)
        else:
            real_changes.append(path)

    return real_changes, generated_changes


def _refactor_cmd(clone_path: Path, max_actions: int, target_file: str | None, dry_run: bool) -> list[str]:
    """Build the reDSL refactor subprocess command."""
    cmd = [
        sys.executable, "-m", "redsl.cli", "refactor", str(clone_path),
        "--max-actions", str(max_actions),
        "--format", "text" if dry_run else "yaml",
        "--use-code2llm", "--validate-regix",
    ]
    if dry_run:
        cmd.append("--dry-run")
    if target_file:
        cmd.extend(["--target-file", target_file])
    return cmd


def _step_analyze(clone_path: Path, max_actions: int, target_file: str | None) -> _AnalysisResult:
    """Run reDSL analysis (dry-run)."""
    click.echo(f"\nStep 2: Running reDSL analysis...")
    click.echo(f"  Analyzing {max_actions} top issues...")

    try:
        result = subprocess.run(
            _refactor_cmd(clone_path, max_actions, target_file, dry_run=True),
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:
            return _AnalysisResult(False, f"Analysis failed: {result.stderr}")

        click.echo(f"  ✓ Analysis complete")
        click.echo(f"\n  Suggestions:")
        for line in result.stdout.split('\n'):
            if re.match(r'\s*\d+\.\s', line):
                click.echo(f"    {line}")

    except subprocess.TimeoutExpired:
        return _AnalysisResult(False, "Analysis timed out")
    except Exception as e:
        return _AnalysisResult(False, f"Analysis error: {e}")

    return _AnalysisResult(True)


def _run_auto_apply(clone_path: Path, max_actions: int, target_file: str | None) -> _ApplyResult | None:
    """Run auto-apply refactor; return _ApplyResult on early-exit, None to continue."""
    click.echo(f"  Auto-apply mode: Running reDSL refactor without dry-run...")
    try:
        result = subprocess.run(
            _refactor_cmd(clone_path, max_actions, target_file, dry_run=False),
            capture_output=True,
            text=True,
            timeout=600
        )
        if result.returncode != 0:
            click.echo(f"  ⚠ Refactor execution had issues: {result.stderr}")
            click.echo(f"  Continuing with whatever changes were made...")
        else:
            click.echo(f"  ✓ Refactor applied")
            suggestions = [l for l in result.stdout.split('\n') if re.match(r'\s*\d+\.\s', l)]
            if suggestions:
                click.echo(f"\n  Suggestions:")
                for line in suggestions:
                    click.echo(f"    {line}")
    except subprocess.TimeoutExpired:
        return _ApplyResult(False, [], [], "Refactor timed out")
    except Exception as e:
        return _ApplyResult(False, [], [], f"Refactor error: {e}")
    return None


def _step_apply(
    clone_path: Path,
    max_actions: int,
    target_file: str | None,
    auto_apply: bool,
) -> _ApplyResult:
    """Apply refactoring fixes."""
    click.echo(f"\nStep 3: Applying fixes...")

    dry_run_history = clone_path / ".redsl" / "history.jsonl"
    if dry_run_history.exists():
        dry_run_history.unlink()

    if auto_apply:
        early = _run_auto_apply(clone_path, max_actions, target_file)
        if early is not None:
            return early
    else:
        click.echo(f"  ⚠ Manual step: Please apply the suggested refactoring from the analysis above")
        click.echo(f"  Then press Enter to continue, or Ctrl+C to abort...")
        try:
            input()
        except KeyboardInterrupt:
            click.echo(f"\n  Aborted by user")
            return _ApplyResult(False, [], [], "Aborted by user")

    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(clone_path),
        capture_output=True,
        text=True,
    )
    changed_paths = _parse_worktree_changes(status.stdout)
    real_changes, generated_changes = _split_generated_and_real_changes(changed_paths)

    if not real_changes:
        return _ApplyResult(False, real_changes, generated_changes, "No source-code changes produced")

    return _ApplyResult(True, real_changes, generated_changes)
