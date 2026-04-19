"""Autonomous PR workflow package."""

from __future__ import annotations

from pathlib import Path

import click

from .analyzer import _step_analyze, _step_apply
from .git_ops import _gh_available, _https_to_ssh, _step_branch_and_commit, _step_create_pr, _step_clone, _step_push
from .reporter import _abort_no_changes, _print_workflow_complete, _print_workflow_header
from .validator import _step_validate

import sys as _sys


def _step_finalize(
    clone_path: Path,
    branch_name: str,
    real_changes: list[str],
    max_actions: int,
    use_gh: bool,
    git_url: str,
    clone_url: str,
) -> None:
    """Execute Steps 4–7: branch, commit, push, create PR."""
    commit_result = _step_branch_and_commit(clone_path, branch_name, real_changes, max_actions)
    if not commit_result.success:
        click.echo(f"  ✗ {commit_result.error}")
        return
    resolved_branch_name = commit_result.resolved_branch_name

    push_result = _step_push(clone_path, resolved_branch_name, use_gh)
    if not push_result.success:
        click.echo(f"  ✗ {push_result.error}")
        if "github.com" in git_url and not clone_url.startswith("git@"):
            click.echo("  Hint: configure SSH keys or install `gh` CLI for authentication")
        return

    pr_success = _step_create_pr(clone_path, resolved_branch_name, use_gh, real_changes, max_actions, clone_url)
    if not pr_success:
        return

    _print_workflow_complete(git_url, resolved_branch_name, clone_url)


def _setup_workflow(git_url: str) -> tuple[bool, str]:
    """Setup: determine gh availability and clone URL."""
    _mod = _sys.modules[__name__]
    use_gh = _mod._gh_available()
    clone_url = _mod._https_to_ssh(git_url) if "github.com" in git_url else git_url
    return use_gh, clone_url


def _run_clone_step(
    git_url: str, clone_url: str, work_dir: Path, fmt: str
) -> Path | None:
    """Step 1: Clone repository. Returns clone_path or None on failure."""
    click.echo("Step 1: Cloning repository...")
    clone_result = _step_clone(git_url, clone_url, work_dir)
    if not clone_result.clone_path:
        click.echo(f"  ✗ {clone_result.error}")
        if fmt == "json":
            import json
            click.echo(json.dumps({"status": "error", "step": "clone", "error": clone_result.error}))
        return None
    return clone_result.clone_path


def _output_dry_run_json(analyze_result) -> None:
    """Output dry run results as JSON."""
    import json
    click.echo(json.dumps({
        "status": "dry_run",
        "decisions": getattr(analyze_result, "decisions", []),
        "estimated_cost": getattr(analyze_result, "estimated_cost", 0),
    }, default=str))


def _output_dry_run_text(analyze_result) -> None:
    """Output dry run results as text."""
    click.echo("\nDry run complete - no PR created")


def _run_dry_run(
    clone_path: Path, max_actions: int, target_file: str | None, fmt: str
) -> bool:
    """Run dry-run mode: analyze only. Returns True if should exit."""
    analyze_result = _step_analyze(clone_path, max_actions, target_file)
    if not analyze_result.success:
        click.echo(f"  ✗ {analyze_result.error}")
        if fmt == "json":
            import json
            click.echo(json.dumps({"status": "error", "step": "analyze", "error": analyze_result.error}))
        return True

    if fmt == "json":
        _output_dry_run_json(analyze_result)
    else:
        _output_dry_run_text(analyze_result)
    return True


def _run_analyze_step(
    clone_path: Path, max_actions: int, target_file: str | None, auto_apply: bool
) -> bool:
    """Step 2: Analyze project. Skipped if auto_apply (combined with apply)."""
    if auto_apply:
        click.echo(f"\nStep 2+3: Analyzing & applying fixes (single pass)...")
        return True

    analyze_result = _step_analyze(clone_path, max_actions, target_file)
    if not analyze_result.success:
        click.echo(f"  ✗ {analyze_result.error}")
        return False
    return True


def _run_apply_step(
    clone_path: Path, max_actions: int, target_file: str | None, auto_apply: bool
) -> list[str] | None:
    """Step 3: Apply refactoring. Returns list of changed files or None on failure."""
    apply_result = _step_apply(clone_path, max_actions, target_file, auto_apply)
    if not apply_result.success:
        _abort_no_changes(apply_result)
        return None
    return apply_result.real_changes


def _run_validate_step(clone_path: Path) -> bool:
    """Step 4: Validate changes with testql."""
    validate_result = _step_validate(clone_path)
    if not validate_result.success:
        click.echo(f"  ✗ Validation failed: {validate_result.error}")
        click.echo("  Refusing to create PR until tests pass")
        return False
    return True


def _output_success_json(real_changes: list[str], branch_name: str) -> None:
    """Output success result as JSON."""
    import json
    click.echo(json.dumps({
        "status": "pr_created",
        "changes": len(real_changes),
        "branch": branch_name,
        "files": real_changes,
    }, default=str))


def run_autonomous_pr(
    git_url: str,
    max_actions: int,
    dry_run: bool,
    auto_apply: bool,
    target_file: str | None,
    work_dir: Path,
    branch_name: str,
    fmt: str = "text",
) -> None:
    """Run the autonomous PR workflow.

    This function orchestrates 7 steps:
    1. Clone repository
    2. Run reDSL analysis
    3. Apply refactoring suggestions
    4. Validate changes
    5. Create branch
    6. Commit changes
    7. Push to GitHub and create PR
    """
    use_gh, clone_url = _setup_workflow(git_url)
    _print_workflow_header(git_url, clone_url, use_gh, max_actions, branch_name, target_file)

    work_dir.mkdir(parents=True, exist_ok=True)
    clone_path = _run_clone_step(git_url, clone_url, work_dir, fmt)
    if clone_path is None:
        return

    if dry_run:
        if _run_dry_run(clone_path, max_actions, target_file, fmt):
            return

    if not _run_analyze_step(clone_path, max_actions, target_file, auto_apply):
        return

    real_changes = _run_apply_step(clone_path, max_actions, target_file, auto_apply)
    if real_changes is None:
        return

    if not _run_validate_step(clone_path):
        return

    _step_finalize(clone_path, branch_name, real_changes, max_actions, use_gh, git_url, clone_url)

    if fmt == "json":
        _output_success_json(real_changes, branch_name)
