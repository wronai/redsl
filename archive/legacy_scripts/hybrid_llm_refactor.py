#!/usr/bin/env python3
"""Hybrid quality refactoring with LLM supervision - applies quality changes with optional LLM validation."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from app.orchestrator import RefactorOrchestrator
from app.config import AgentConfig
from app.dsl import RefactorAction
from app.analyzers import CodeAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def apply_changes_with_llm_supervision(
    project_path: Path, 
    max_changes: int = 50,
    enable_llm: bool = True,
    validate_direct_changes: bool = True
) -> dict[str, Any]:
    """Apply refactorings with optional LLM supervision."""
    print(f"\n{'='*60}")
    print(f"Processing: {project_path.name}")
    print(f"LLM enabled: {enable_llm}")
    print(f"{'='*60}")
    
    # Initialize orchestrator
    if enable_llm:
        config = AgentConfig.from_env()  # Load LLM config from .env
        # Override model from .env if specified
        import os
        if os.getenv("LLM_MODEL"):
            config.llm.model = os.getenv("LLM_MODEL")
        elif os.getenv("REFACTOR_LLM_MODEL"):
            config.llm.model = os.getenv("REFACTOR_LLM_MODEL")
        config.refactor.apply_changes = True
        config.refactor.reflection_rounds = 1  # Enable reflection
        config.refactor.dry_run = False  # Ensure we apply changes
        print(f"  Using LLM model: {config.llm.model}")
        print(f"  API key configured: {bool(config.llm.api_key)}")
    else:
        config = AgentConfig()
        config.refactor.apply_changes = True
        config.refactor.reflection_rounds = 0
        config.refactor.dry_run = False
    
    orchestrator = RefactorOrchestrator(config)
    analyzer = CodeAnalyzer()
    
    # Get all decisions
    analysis = analyzer.analyze_project(project_path)
    contexts = analysis.to_dsl_contexts()
    
    if enable_llm:
        # Get top decisions including complex ones
        all_decisions = orchestrator.dsl_engine.top_decisions(contexts, limit=max_changes * 2)
    else:
        # Only quality decisions for direct mode
        all_decisions = orchestrator.dsl_engine.evaluate(contexts)
        quality_actions = {
            RefactorAction.REMOVE_UNUSED_IMPORTS,
            RefactorAction.FIX_MODULE_EXECUTION_BLOCK,
            RefactorAction.EXTRACT_CONSTANTS,
            RefactorAction.ADD_RETURN_TYPES,
        }
        all_decisions = [d for d in all_decisions if d.action in quality_actions]
    
    print(f"Found {len(all_decisions)} decisions")
    
    # Group by file and apply changes
    decisions_by_file: dict[str, list[Any]] = {}
    for d in all_decisions:
        if d.target_file not in decisions_by_file:
            decisions_by_file[d.target_file] = []
        decisions_by_file[d.target_file].append(d)
    
    # Execute decisions
    total_applied = 0
    total_errors = 0
    changes_by_type = {
        "remove_unused_imports": 0,
        "fix_module_execution_block": 0,
        "extract_constants": 0,
        "add_return_types": 0,
        "extract_method": 0,
        "simplify_conditionals": 0,
        "reduce_complexity": 0,
        "other": 0,
    }
    
    for file_path, decisions in decisions_by_file.items():
        print(f"\n  Processing {file_path}:")
        
        # Sort by score
        decisions.sort(key=lambda d: d.score, reverse=True)
        
        for decision in decisions:
            if total_applied >= max_changes:
                print(f"  Reached max changes limit ({max_changes})")
                break
            
            # Use orchestrator's execute_decision which handles both direct and LLM
            try:
                result = orchestrator._execute_decision(decision, project_path)
                
                if result.applied:
                    total_applied += 1
                    action_key = decision.action.value.replace("-", "_")
                    if action_key in changes_by_type:
                        changes_by_type[action_key] += 1
                    else:
                        changes_by_type["other"] += 1
                    print(f"    ✓ {decision.action.value}")
                else:
                    total_errors += 1
                    if result.errors:
                        print(f"    ✗ {decision.action.value}: {result.errors[0]}")
                        
            except Exception as e:
                total_errors += 1
                print(f"    ✗ {decision.action.value}: {str(e)[:100]}")
    
    # Get detailed changes from direct refactor
    changes = orchestrator.direct_refactor.get_applied_changes()
    
    return {
        "project": project_path.name,
        "decisions": len(all_decisions),
        "changes_applied": total_applied,
        "errors": total_errors,
        "changes_by_type": changes_by_type,
        "changes": changes,
        "llm_enabled": enable_llm,
    }


def main() -> None:
    """Process semcod projects with hybrid refactoring."""
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help", "help"]:
        print("Usage: python hybrid_llm_refactor.py <semcod_root> [--max-changes N] [--no-llm] [--no-validation]")
        print("")
        print("Arguments:")
        print("  semcod_root    Path to semcod directory containing projects")
        print("  --max-changes N Maximum changes per project (default: 50)")
        print("  --no-llm       Disable LLM entirely (same as hybrid_quality_refactor.py)")
        print("  --no-validation Skip LLM validation of direct changes")
        print("")
        print("Examples:")
        print("  python hybrid_llm_refactor.py /home/tom/github/semcod --max-changes 30")
        print("  python hybrid_llm_refactor.py /home/tom/github/semcod --no-llm")
        sys.exit(0 if sys.argv[1] in ["-h", "--help", "help"] else 1)
    
    semcod_root = Path(sys.argv[1])
    max_changes = 50
    enable_llm = True
    validate_direct = True
    
    if "--max-changes" in sys.argv:
        idx = sys.argv.index("--max-changes")
        if idx + 1 < len(sys.argv):
            max_changes = int(sys.argv[idx + 1])
    
    if "--no-llm" in sys.argv:
        enable_llm = False
    
    if "--no-validation" in sys.argv:
        validate_direct = False
    
    # Find all projects with TODO.md
    projects = []
    for item in semcod_root.iterdir():
        if item.is_dir() and (item / "TODO.md").exists():
            projects.append(item)
    
    # Special case: if semcod_root itself is a project with TODO.md
    if (semcod_root / "TODO.md").exists():
        projects = [semcod_root]
    
    print(f"Found {len(projects)} projects with TODO.md")
    print(f"Max changes per project: {max_changes}")
    
    # Process each project
    all_results = []
    total_before = 0
    total_after = 0
    
    for project in sorted(projects):
        # Count TODO issues before
        todo_file = project / "TODO.md"
        if todo_file.exists():
            content = todo_file.read_text(encoding="utf-8")
            before_issues = sum(1 for line in content.splitlines() if line.startswith("- [ ]"))
            total_before += before_issues
        else:
            before_issues = 0
        
        # Apply refactoring
        result = apply_changes_with_llm_supervision(
            project, max_changes, enable_llm, validate_direct
        )
        result["before_issues"] = before_issues
        all_results.append(result)
        
        # Regenerate TODO.md with prefact
        print(f"  Regenerating TODO.md with prefact...")
        import subprocess
        result_prefact = subprocess.run(["prefact", "-a"], cwd=project, capture_output=True, text=True)
        
        # Count issues after
        if todo_file.exists():
            content = todo_file.read_text(encoding="utf-8")
            after_issues = sum(1 for line in content.splitlines() if line.startswith("- [ ]"))
            total_after += after_issues
            result["after_issues"] = after_issues
            reduction = before_issues - after_issues
            print(f"  TODO reduction: {before_issues} → {after_issues} ({reduction} fewer)")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"HYBRID REFACTORING SUMMARY (LLM: {enable_llm})")
    print(f"{'='*60}")
    
    total_applied = sum(r["changes_applied"] for r in all_results)
    
    print(f"Total projects: {len(all_results)}")
    print(f"Total issues before: {total_before}")
    print(f"Total issues after: {total_after}")
    print(f"Total reduction: {total_before - total_after}")
    print(f"\nTotal changes applied: {total_applied}")
    
    # Show breakdown by type
    all_types = set()
    for r in all_results:
        all_types.update(r["changes_by_type"].keys())
    
    for change_type in sorted(all_types):
        count = sum(r["changes_by_type"].get(change_type, 0) for r in all_results)
        if count > 0:
            print(f"  - {change_type}: {count}")
    
    # Show projects with most improvements
    print(f"\nTop improvements:")
    sorted_results = sorted(
        all_results, 
        key=lambda r: r.get("before_issues", 0) - r.get("after_issues", 0), 
        reverse=True
    )
    for r in sorted_results[:5]:
        reduction = r.get("before_issues", 0) - r.get("after_issues", 0)
        if reduction > 0:
            print(f"  {r['project']}: {reduction} fewer TODOs ({r['changes_applied']} changes)")
    
    # Save results
    import json
    results_file = semcod_root / f"hybrid_llm_refactor_results_{('llm' if enable_llm else 'direct')}.json"
    results_file.write_text(json.dumps(all_results, indent=2))
    print(f"\nResults saved to: {results_file}")


if __name__ == "__main__":
    main()
