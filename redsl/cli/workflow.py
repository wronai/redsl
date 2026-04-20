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
            line += (
                f"  (tune.strategy={step.tune.strategy}, retry={step.tune.retry},"
                f" run_on_missing_metrics={step.tune.run_on_missing_metrics},"
                f" create_planfile_task_on_failure={step.tune.create_planfile_task_on_failure})"
            )
        click.echo(line)
    click.echo("")
    click.echo(f"planfile.update_on_apply: {wf.planfile.update_on_apply}")
    click.echo(f"reflect.enabled:          {wf.reflect.enabled}")
    click.echo("")
    click.echo(f"storage.base_dir:         {wf.storage.base_dir}")
    click.echo(f"storage.chat_log:         {wf.storage.chat_log_enabled} → {wf.storage.chat_log_filename}")
    click.echo(f"storage.history:          {wf.storage.history_enabled} → {wf.storage.history_filename}")
    click.echo("")
    # Detect actual deploy mechanisms for this project
    from redsl.execution.deploy_detector import detect_deploy_config
    detected = detect_deploy_config(project)
    click.echo(f"deploy.enabled:           {wf.deploy.enabled}")
    click.echo(f"deploy.push:              {wf.deploy.push}  (detected: {detected.push.method} — {detected.push.label})")
    click.echo(f"deploy.publish:           {wf.deploy.publish}  (detected: {detected.publish.method} — {detected.publish.label})")
    click.echo(f"deploy.on_success_only:   {wf.deploy.on_success_only}")
    if detected.ci_handles_deploy:
        click.echo(f"deploy.ci_workflows:      {', '.join(detected.ci_workflow_files)}")
    click.echo("")
    # Project map summary
    if wf.project_map.categories:
        click.echo("project_map (from redsl.yaml):")
        for cat, files in wf.project_map.categories.items():
            click.echo(f"  {cat}: {', '.join(files)}")
    else:
        click.echo("project_map: (not scanned — run `redsl workflow scan`)")


@workflow_group.command("scan")
@click.argument("project_dir", default=".", type=click.Path(exists=True, file_okay=False))
@click.option("--write", "-w", is_flag=True, help="Write project_map into redsl.yaml (updates in-place)")
@click.option("--print-only", "-p", is_flag=True, default=False, help="Print map without writing")
def workflow_scan(project_dir: str, write: bool, print_only: bool) -> None:
    """Scan PROJECT_DIR and build a map of configuration files.

    By default prints the detected map.  Use --write to persist it into
    the project's redsl.yaml under the ``project_map:`` key.
    """
    from redsl.execution.project_scanner import scan_project, project_map_to_yaml_block
    from redsl.execution.workflow import WORKFLOW_FILENAME

    project = Path(project_dir).resolve()
    pm = scan_project(project)

    click.echo(f"Scanned: {project.name}")
    click.echo(f"Found {len(pm.all_files())} config files in {len(pm.categories)} categories:\n")

    for cat, files in pm.categories.items():
        click.echo(f"  [{cat}]")
        for f in files:
            click.echo(f"    {f}")
    click.echo("")

    if write or (not print_only and click.confirm("Write project_map into redsl.yaml?", default=True)):
        target = project / WORKFLOW_FILENAME
        if not target.exists():
            click.echo(f"No redsl.yaml found in {project.name} — run `redsl workflow init` first.")
            sys.exit(1)

        content = target.read_text(encoding="utf-8")
        yaml_block = project_map_to_yaml_block(pm, indent=4)

        # Replace existing project_map: block or append
        import re
        # Remove old project_map block if present
        content = re.sub(
            r"\n  project_map:.*?(?=\n  [a-z]|\Z)",
            "",
            content,
            flags=re.DOTALL,
        )
        # Append new block under spec:
        indented_block = "\n".join(
            "  " + line if line else line
            for line in yaml_block.splitlines()
        )
        content = content.rstrip() + "\n\n" + indented_block + "\n"

        target.write_text(content, encoding="utf-8")
        click.echo(f"✓ project_map written to {target}")


def register(cli_group: click.Group) -> None:
    cli_group.add_command(workflow_group)
