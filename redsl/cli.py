"""Command-line interface for reDSL."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
load_dotenv()

import click

from .orchestrator import RefactorOrchestrator
from .config import AgentConfig
from .dsl import RefactorAction
from .analyzers import CodeAnalyzer
from .commands import batch as batch_commands
from .commands import hybrid as hybrid_commands
from .commands import pyqual as pyqual_commands
from .formatters import format_refactor_plan, format_batch_results, format_debug_info

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="1.2.0")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def cli(verbose: bool) -> None:
    """reDSL - Automated code refactoring tool."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


@cli.command()
@click.argument("project_path", type=click.Path(exists=True, path_type=Path))
@click.option("--max-actions", "-n", default=10, help="Maximum number of actions to apply")
@click.option("--dry-run", is_flag=True, help="Show what would be done without applying changes")
@click.option("--format", "-f", default="text", type=click.Choice(["text", "yaml", "json"]), help="Output format")
def refactor(project_path: Path, max_actions: int, dry_run: bool, format: str) -> None:
    """Run refactoring on a project."""
    if format == "text":
        click.echo(f"Running reDSL on {project_path}")
    
    config = AgentConfig.from_env()
    if dry_run:
        config.refactor.dry_run = True
        config.refactor.reflection_rounds = 0
    else:
        config.refactor.dry_run = False
    
    orchestrator = RefactorOrchestrator(config)
    
    # Get decisions and format output
    analysis = orchestrator.analyzer.analyze_project(project_path)
    contexts = analysis.to_dsl_contexts()
    decisions = orchestrator.dsl_engine.evaluate(contexts)
    decisions = sorted(decisions, key=lambda d: d.score, reverse=True)[:max_actions]
    
    # Format and output the plan
    formatted_output = format_refactor_plan(decisions, format, analysis)
    click.echo(formatted_output)
    
    if not dry_run:
        if click.confirm("\nApply these changes?"):
            click.echo("\n=== APPLYING REFACTORING ===")
            report = orchestrator.run_cycle(project_path, max_actions=max_actions)
            
            click.echo(f"\n=== RESULTS ===")
            click.echo(f"Cycle {report.cycle_number} complete")
            click.echo(f"Analysis: {report.analysis_summary}")
            click.echo(f"Decisions: {report.decisions_count}")
            click.echo(f"Proposals generated: {report.proposals_generated}")
            click.echo(f"Applied: {report.proposals_applied}")
            click.echo(f"Rejected: {report.proposals_rejected}")
            
            if report.errors:
                click.echo(f"\nErrors:")
                for error in report.errors[:5]:
                    click.echo(f"  - {error}")


@cli.group()
def batch() -> None:
    """Batch refactoring commands."""


@batch.command("semcod")
@click.argument("semcod_root", type=click.Path(exists=True, path_type=Path))
@click.option("--max-actions", "-n", default=10, help="Maximum actions per project")
@click.option("--format", "-f", default="text", type=click.Choice(["text", "yaml", "json"]), help="Output format")
def batch_semcod(semcod_root: Path, max_actions: int, format: str) -> None:
    """Apply refactoring to semcod projects."""
    if format == "text":
        click.echo(f"Batch processing semcod projects in {semcod_root}")
    results = batch_commands.run_semcod_batch(semcod_root, max_actions)
    
    # Convert results to format expected by formatter
    formatted_results = []
    for detail in results.get("project_details", []):
        formatted_results.append({
            "project_name": detail["name"],
            "status": "success",
            "files_processed": detail.get("files", 0),
            "changes_applied": detail["applied"],
            "todo_reduction": detail.get("todo_reduction", 0)
        })
    
    # Format and output results
    formatted_output = format_batch_results(formatted_results, format)
    click.echo(formatted_output)


@batch.command("hybrid")
@click.argument("semcod_root", type=click.Path(exists=True, path_type=Path))
@click.option("--max-changes", "-n", default=30, help="Maximum changes per project")
def batch_hybrid(semcod_root: Path, max_changes: int) -> None:
    """Apply hybrid quality refactorings (no LLM needed)."""
    hybrid_commands.run_hybrid_batch(semcod_root, max_changes)


@cli.group()
def pyqual() -> None:
    """Python code quality analysis commands."""


@pyqual.command("analyze")
@click.argument("project_path", type=click.Path(exists=True, path_type=Path))
@click.option("--config", "-c", type=click.Path(exists=True, path_type=Path), help="Path to pyqual.yaml config")
@click.option("--format", "-f", default="yaml", type=click.Choice(["yaml", "json"]), help="Output format")
def pyqual_analyze(project_path: Path, config: Path, format: str) -> None:
    """Analyze Python code quality."""
    pyqual_commands.run_pyqual_analysis(project_path, config, format)


@pyqual.command("fix")
@click.argument("project_path", type=click.Path(exists=True, path_type=Path))
@click.option("--config", "-c", type=click.Path(exists=True, path_type=Path), help="Path to pyqual.yaml config")
def pyqual_fix(project_path: Path, config: Path) -> None:
    """Apply automatic quality fixes."""
    pyqual_commands.run_pyqual_fix(project_path, config)


@cli.group()
def debug() -> None:
    """Debug and diagnostic commands."""


@debug.command("config")
@click.option("--show-env", is_flag=True, help="Show environment variables")
def debug_config(show_env: bool) -> None:
    """Debug configuration loading."""
    config = AgentConfig.from_env()
    
    click.echo("=== reDSL Configuration ===")
    click.echo(f"LLM Model: {config.llm.model}")
    click.echo(f"Temperature: {config.llm.temperature}")
    click.echo(f"Max Tokens: {config.llm.max_tokens}")
    click.echo(f"Reflection Model: {config.llm.reflection_model}")
    click.echo(f"API Key: {'***' + config.llm.api_key[-4:] if config.llm.api_key else 'Not set'}")
    
    if show_env:
        import os
        click.echo("\n=== Environment Variables ===")
        for key in ["OPENAI_API_KEY", "OPENROUTER_API_KEY", "LLM_MODEL", "REFACTOR_LLM_MODEL"]:
            value = os.getenv(key)
            click.echo(f"{key}: {'***' + value[-4:] if value and 'KEY' in key else value or 'Not set'}")


@debug.command("decisions")
@click.argument("project_path", type=click.Path(exists=True, path_type=Path))
@click.option("--limit", "-n", default=20, help="Number of decisions to show")
def debug_decisions(project_path: Path, limit: int) -> None:
    """Debug DSL decision making."""
    analyzer = CodeAnalyzer()
    analysis = analyzer.analyze_project(project_path)
    contexts = analysis.to_dsl_contexts()
    
    orchestrator = RefactorOrchestrator(AgentConfig())
    decisions = orchestrator.dsl_engine.evaluate(contexts)
    
    click.echo(f"=== DSL Decisions for {project_path.name} ===")
    click.echo(f"Total decisions: {len(decisions)}")
    click.echo()
    
    for i, decision in enumerate(decisions[:limit]):
        click.echo(f"{i+1}. {decision.action.value} on {decision.target_file}")
        click.echo(f"   Score: {decision.score:.2f}")
        click.echo(f"   Rule: {decision.rule_name}")
        click.echo(f"   Rationale: {decision.rationale}")
        click.echo()


if __name__ == "__main__":
    cli()
