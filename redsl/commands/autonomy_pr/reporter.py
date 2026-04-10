"""Output formatting and reporting for the autonomous PR workflow."""

from __future__ import annotations

import click

from .models import _ApplyResult


def _print_workflow_header(git_url, clone_url, use_gh, max_actions, branch_name, target_file):
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


def _print_workflow_complete(git_url, resolved_branch_name, clone_url):
    """Print workflow completion information."""
    proto = 'SSH' if clone_url.startswith('git@') else 'HTTPS'
    click.echo(f"\n=== Autonomous PR Workflow Complete ===")
    click.echo(f"Repository: {git_url}  Branch: {resolved_branch_name}  Protocol: {proto}")


def _abort_no_changes(apply_result: _ApplyResult) -> None:
    """Report and abort when no source-code changes were produced."""
    click.echo("\n  ✗ Refactor produced no source-code changes; only reports/logs were generated.")
    if apply_result.generated_changes:
        click.echo("  Generated artifacts:")
        for path in apply_result.generated_changes:
            click.echo(f"    - {path}")
    click.echo("  Aborting autonomous PR creation.")
    raise click.ClickException("Autonomous PR aborted: no source-code changes were produced")
