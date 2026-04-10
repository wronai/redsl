"""Autonomous PR workflow implementation for redsl."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import click


def _echo_json(payload: Any) -> None:
    click.echo(__import__("json").dumps(payload, indent=2, default=str))


def _https_to_ssh(url: str) -> str:
    """Convert HTTPS GitHub URL to SSH if possible.

    >>> _https_to_ssh('https://github.com/semcod/vallm.git')
    'git@github.com:semcod/vallm.git'
    """
    m = re.match(r'https?://github\.com/(.+)', url)
    if m:
        return f'git@github.com:{m.group(1)}'
    return url


def _gh_available() -> bool:
    """Return True if the GitHub CLI (gh) is installed and authenticated."""
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True, timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


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


@dataclass
class _CloneResult:
    """Result of repository cloning step."""
    clone_path: Path | None
    error: str = ""


def _step_clone(git_url: str, clone_url: str, work_dir: Path) -> _CloneResult:
    """Clone repository to working directory."""
    repo_name = git_url.rstrip('/').split('/')[-1].replace('.git', '')
    clone_path = work_dir / repo_name

    if clone_path.exists():
        click.echo(f"  Repository already cloned at {clone_path}; refreshing workspace")
        shutil.rmtree(clone_path)

    try:
        subprocess.run(
            ["git", "clone", clone_url, str(clone_path)],
            check=True,
            capture_output=True,
            timeout=60
        )
        click.echo(f"  ✓ Cloned to {clone_path}")
    except subprocess.CalledProcessError as e:
        return _CloneResult(None, f"Failed to clone: {e.stderr.decode()}")
    except subprocess.TimeoutExpired:
        return _CloneResult(None, "Clone timed out")

    # Clear stale reDSL history so LLM-based refactors aren't blocked
    redsl_dir = clone_path / ".redsl"
    if redsl_dir.exists():
        shutil.rmtree(redsl_dir)
        click.echo(f"  ✓ Cleared stale .redsl/ history")

    return _CloneResult(clone_path)


@dataclass
class _AnalysisResult:
    """Result of analysis step."""
    success: bool
    error: str = ""


def _step_analyze(clone_path: Path, max_actions: int, target_file: str | None) -> _AnalysisResult:
    """Run reDSL analysis (dry-run)."""
    click.echo(f"\nStep 2: Running reDSL analysis...")
    click.echo(f"  Analyzing {max_actions} top issues...")

    try:
        result = subprocess.run(
            ["/usr/bin/python3", "-m", "redsl.cli", "refactor", str(clone_path),
             "--max-actions", str(max_actions), "--dry-run", "--format", "text",
             "--use-code2llm", "--validate-regix",
             *(["--target-file", target_file] if target_file else [])],
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


@dataclass
class _ApplyResult:
    """Result of apply fixes step."""
    success: bool
    real_changes: list[str]
    generated_changes: list[str]
    error: str = ""


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
        click.echo(f"  Auto-apply mode: Running reDSL refactor without dry-run...")
        try:
            result = subprocess.run(
                ["/usr/bin/python3", "-m", "redsl.cli", "refactor", str(clone_path),
                 "--max-actions", str(max_actions), "--format", "yaml",
                 "--use-code2llm", "--validate-regix",
                 *(["--target-file", target_file] if target_file else [])],
                capture_output=True,
                text=True,
                timeout=600
            )
            if result.returncode != 0:
                click.echo(f"  ⚠ Refactor execution had issues: {result.stderr}")
                click.echo(f"  Continuing with whatever changes were made...")
            else:
                click.echo(f"  ✓ Refactor applied")
        except subprocess.TimeoutExpired:
            return _ApplyResult(False, [], [], "Refactor timed out")
        except Exception as e:
            return _ApplyResult(False, [], [], f"Refactor error: {e}")
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


def _resolve_branch_name(clone_path: Path, branch_name: str) -> str:
    """Resolve unique branch name if needed."""
    existing_local = subprocess.run(
        ["git", "branch", "--list", branch_name],
        cwd=str(clone_path),
        capture_output=True,
        text=True,
    )
    existing_remote = subprocess.run(
        ["git", "ls-remote", "--heads", "origin", branch_name],
        cwd=str(clone_path),
        capture_output=True,
        text=True,
    )
    if existing_local.stdout.strip() or existing_remote.stdout.strip():
        return f"{branch_name}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    return branch_name


@dataclass
class _CommitResult:
    """Result of branch/commit step."""
    resolved_branch_name: str
    success: bool
    error: str = ""


def _step_branch_and_commit(
    clone_path: Path,
    branch_name: str,
    real_changes: list[str],
    max_actions: int,
) -> _CommitResult:
    """Create branch and commit changes."""
    resolved_branch_name = _resolve_branch_name(clone_path, branch_name)

    click.echo(f"\nStep 4: Creating branch {resolved_branch_name}...")
    try:
        subprocess.run(
            ["git", "checkout", "-b", resolved_branch_name],
            cwd=str(clone_path),
            check=True,
            capture_output=True
        )
        click.echo(f"  ✓ Branch created")
    except subprocess.CalledProcessError as e:
        return _CommitResult(resolved_branch_name, False, f"Failed to create branch: {e.stderr.decode()}")

    try:
        subprocess.run(
            ["git", "add", "--", *real_changes],
            cwd=str(clone_path),
            check=True,
            capture_output=True,
        )
        click.echo(f"  ✓ Staged {len(real_changes)} source file(s)")

        click.echo(f"\nStep 5: Committing changes...")
        commit_msg = f"Autonomous refactoring by ReDSL\n\nApplied {max_actions} top refactoring suggestions automatically."
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=str(clone_path),
            check=True,
            capture_output=True
        )
        click.echo(f"  ✓ Changes committed")
    except subprocess.CalledProcessError as e:
        return _CommitResult(resolved_branch_name, False, f"Failed to commit: {e.stderr.decode()}")

    return _CommitResult(resolved_branch_name, True)


@dataclass
class _PushResult:
    """Result of push step."""
    success: bool
    error: str = ""


def _step_push(clone_path: Path, resolved_branch_name: str, use_gh: bool) -> _PushResult:
    """Push branch to GitHub."""
    click.echo(f"\nStep 6: Pushing to GitHub...")
    try:
        push_cmd = ["git", "push", "-u", "origin", resolved_branch_name]
        env = None
        if not use_gh:
            env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
        subprocess.run(
            push_cmd,
            cwd=str(clone_path),
            check=True,
            capture_output=True,
            timeout=120,
            env=env,
        )
        click.echo(f"  ✓ Pushed successfully")
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode() if e.stderr else ""
        return _PushResult(False, f"Failed to push: {stderr}")
    except subprocess.TimeoutExpired:
        return _PushResult(False, "Push timed out")

    return _PushResult(True)


def _step_create_pr(
    clone_path: Path,
    resolved_branch_name: str,
    use_gh: bool,
    real_changes: list[str],
    max_actions: int,
    clone_url: str,
) -> bool:
    """Create Pull Request using gh CLI. Returns True if PR created or skipped gracefully."""
    click.echo(f"\nStep 7: Creating Pull Request...")
    if not use_gh:
        click.echo("  ⚠ GitHub CLI (gh) not available — skipping PR creation")
        click.echo(f"  Push succeeded. Create PR manually for branch: {resolved_branch_name}")
        return True

    pr_title = "Autonomous refactoring by ReDSL"
    changes_list = "\n".join(f"- `{path}`" for path in real_changes)
    pr_body = (
        "## Summary\n\n"
        "This PR applies autonomous refactoring suggested by ReDSL.\n\n"
        f"## Changes ({len(real_changes)} file(s))\n\n"
        f"{changes_list}\n\n"
        "## Pipeline\n\n"
        "| Step | Status |\n"
        "|------|--------|\n"
        "| Clone (SSH) | ✅ |\n"
        f"| Analysis (code2llm + regix) | ✅ {max_actions} actions |\n"
        "| Apply refactors | ✅ |\n"
        "| Push | ✅ |\n"
        "| PR | ✅ |\n\n"
        "---\n"
        "*Generated by reDSL autonomous-pr command*\n"
    )
    try:
        subprocess.run(
            ["gh", "pr", "create", "--title", pr_title, "--body", pr_body],
            cwd=str(clone_path),
            check=True,
            capture_output=True,
            timeout=30,
        )
        click.echo(f"  ✓ PR created successfully")
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode() if e.stderr else ""
        click.echo(f"  ✗ Failed to create PR: {stderr}")
        return False
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        click.echo(f"  ✗ gh CLI error: {e}")
        return False

    return True


def _print_workflow_header(
    git_url: str,
    clone_url: str,
    use_gh: bool,
    max_actions: int,
    branch_name: str,
    target_file: str | None,
) -> None:
    """Print workflow header information."""
    click.echo(f"=== Autonomous PR Workflow ===")
    click.echo(f"Target: {git_url}")
    if clone_url != git_url:
        click.echo(f"Using SSH: {clone_url}")
    if use_gh:
        click.echo(f"GitHub CLI: available")
    click.echo(f"Max actions: {max_actions}")
    click.echo(f"Branch: {branch_name}")
    if target_file:
        click.echo(f"Target file: {target_file}")
    click.echo("")


def _print_workflow_complete(
    git_url: str,
    resolved_branch_name: str,
    clone_url: str,
) -> None:
    """Print workflow completion information."""
    click.echo(f"\n=== Autonomous PR Workflow Complete ===")
    click.echo(f"Repository: {git_url}")
    click.echo(f"Branch: {resolved_branch_name}")
    click.echo(f"Protocol: {'SSH' if clone_url.startswith('git@') else 'HTTPS'}")


def run_autonomous_pr(
    git_url: str,
    max_actions: int,
    dry_run: bool,
    auto_apply: bool,
    target_file: str | None,
    work_dir: Path,
    branch_name: str,
) -> None:
    """Run the autonomous PR workflow.

    This function orchestrates 7 steps:
    1. Clone repository
    2. Run reDSL analysis
    3. Apply refactoring suggestions
    4. Create branch
    5. Commit changes
    6. Push to GitHub
    7. Create a Pull Request
    """
    use_gh = _gh_available()
    clone_url = _https_to_ssh(git_url) if "github.com" in git_url else git_url

    _print_workflow_header(git_url, clone_url, use_gh, max_actions, branch_name, target_file)

    # Step 1: Clone
    work_dir.mkdir(parents=True, exist_ok=True)
    click.echo("Step 1: Cloning repository...")
    clone_result = _step_clone(git_url, clone_url, work_dir)
    if not clone_result.clone_path:
        click.echo(f"  ✗ {clone_result.error}")
        return
    clone_path = clone_result.clone_path

    # Step 2: Analyze
    analyze_result = _step_analyze(clone_path, max_actions, target_file)
    if not analyze_result.success:
        click.echo(f"  ✗ {analyze_result.error}")
        return

    if dry_run:
        click.echo("\nDry run complete - no PR created")
        return

    # Step 3: Apply
    apply_result = _step_apply(clone_path, max_actions, target_file, auto_apply)
    if not apply_result.success:
        click.echo(f"\n  ✗ Refactor produced no source-code changes; only reports/logs were generated.")
        if apply_result.generated_changes:
            click.echo("  Generated artifacts:")
            for path in apply_result.generated_changes:
                click.echo(f"    - {path}")
        click.echo("  Aborting autonomous PR creation.")
        raise click.ClickException("Autonomous PR aborted: no source-code changes were produced")

    real_changes = apply_result.real_changes

    # Step 4 & 5: Branch and Commit
    commit_result = _step_branch_and_commit(clone_path, branch_name, real_changes, max_actions)
    if not commit_result.success:
        click.echo(f"  ✗ {commit_result.error}")
        return
    resolved_branch_name = commit_result.resolved_branch_name

    # Step 6: Push
    push_result = _step_push(clone_path, resolved_branch_name, use_gh)
    if not push_result.success:
        click.echo(f"  ✗ {push_result.error}")
        if "github.com" in git_url and not clone_url.startswith("git@"):
            click.echo("  Hint: configure SSH keys or install `gh` CLI for authentication")
        return

    # Step 7: Create PR
    pr_success = _step_create_pr(clone_path, resolved_branch_name, use_gh, real_changes, max_actions, clone_url)
    if not pr_success:
        return

    _print_workflow_complete(git_url, resolved_branch_name, clone_url)
