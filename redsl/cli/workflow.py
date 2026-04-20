"""CLI commands for workflow management — `redsl workflow`."""

from __future__ import annotations

import sys
from pathlib import Path

import click


@click.group("workflow")
def workflow_group() -> None:
    """Manage redsl.yaml — declarative refactor pipeline config."""


@workflow_group.command("init")
@click.argument("project_dir", default=".", type=click.Path(exists=True, file_okay=False))
@click.option("--name", "-n", default=None, help="Workflow name (defaults to directory name)")
@click.option("--force", "-f", is_flag=True, help="Overwrite existing redsl.yaml")
def workflow_init(project_dir: str, name: str | None, force: bool) -> None:
    """Generate redsl.yaml in PROJECT_DIR.

    The generated file documents all decisions redsl makes during refactoring
    and can be edited to customise the pipeline per project.
    """
    from redsl.execution.workflow import WORKFLOW_TEMPLATE, WORKFLOW_FILENAME

    project = Path(project_dir).resolve()
    target = project / WORKFLOW_FILENAME
    workflow_name = name or project.name

    if target.exists() and not force:
        click.echo(
            f"[workflow] {target} already exists. Use --force to overwrite.", err=True
        )
        sys.exit(1)

    content = WORKFLOW_TEMPLATE.format(name=workflow_name)
    target.write_text(content, encoding="utf-8")
    click.echo(f"[workflow] created: {target}")
    click.echo(
        "\nEdit the file to customise when and how redsl refactors your project.\n"
        "Key sections:\n"
        "  spec.decide.max_actions      — how many files per cycle\n"
        "  spec.validate.steps          — what to check after changes\n"
        "  spec.validate.steps[pyqual_gates].on_failure — tune | warn | stop\n"
    )


@workflow_group.command("show")
@click.argument("project_dir", default=".", type=click.Path(exists=True, file_okay=False))
def workflow_show(project_dir: str) -> None:
    """Show effective workflow config for PROJECT_DIR (resolved with fallbacks)."""
    from redsl.execution.workflow import load_workflow

    project = Path(project_dir).resolve()
    wf = load_workflow(project)

    click.echo(f"Workflow: {wf.name}")
    click.echo(f"Source:   {wf.source}")
    click.echo("")
    click.echo("perceive:")
    click.echo(f"  use_code2llm: {wf.perceive.use_code2llm}")
    click.echo(f"  use_redup:    {wf.perceive.use_redup}")
    click.echo("")
    click.echo("decide:")
    click.echo(f"  max_actions: {wf.decide.max_actions}")
    click.echo("")
    click.echo("execute:")
    click.echo(f"  use_sandbox:         {wf.execute.use_sandbox}")
    click.echo(f"  rollback_on_failure: {wf.execute.rollback_on_failure}")
    click.echo("")
    click.echo("validate.steps:")
    for step in wf.validate.steps:
        line = f"  - {step.name:<16} enabled={str(step.enabled):<5}  on_failure={step.on_failure}"
        if step.on_failure == "tune":
            line += f"  (tune.strategy={step.tune.strategy}, retry={step.tune.retry})"
        click.echo(line)
    click.echo("")
    click.echo(f"planfile.update_on_apply: {wf.planfile.update_on_apply}")
    click.echo(f"reflect.enabled:          {wf.reflect.enabled}")


def register(cli_group: click.Group) -> None:
    cli_group.add_command(workflow_group)
