#!/usr/bin/env python3
"""Hybrid quality refactoring - applies all quality changes without LLM dependency."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from app.orchestrator import RefactorOrchestrator
from app.config import AgentConfig
from app.dsl import RefactorAction
from app.analyzers import CodeAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce log noise for batch processing
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def apply_all_quality_changes(project_path: Path, max_changes: int = 50) -> dict[str, Any]:
    """Apply ALL quality refactorings to a project without LLM."""
    print(f"\n{'='*60}")
    print(f"Processing: {project_path.name}")
    print(f"{'='*60}")
    
    # Initialize orchestrator with no LLM dependency
    config = AgentConfig()
    config.refactor.apply_changes = True
    config.refactor.reflection_rounds = 0
    
    orchestrator = RefactorOrchestrator(config)
    analyzer = CodeAnalyzer()
    
    # Get all decisions
    analysis = analyzer.analyze_project(project_path)
    contexts = analysis.to_dsl_contexts()
    all_decisions = orchestrator.dsl_engine.evaluate(contexts)
    
    # Filter for quality decisions ONLY (no LLM needed)
    quality_decisions = [d for d in all_decisions if d.action in [
        RefactorAction.REMOVE_UNUSED_IMPORTS,
        RefactorAction.FIX_MODULE_EXECUTION_BLOCK,
        RefactorAction.EXTRACT_CONSTANTS,
        RefactorAction.ADD_RETURN_TYPES,
    ]]
    
    print(f"Found {len(quality_decisions)} quality decisions")
    
    # Group by file and apply all changes per file
    decisions_by_file: dict[str, list[Any]] = {}
    for d in quality_decisions:
        if d.target_file not in decisions_by_file:
            decisions_by_file[d.target_file] = []
        decisions_by_file[d.target_file].append(d)
    
    # Execute decisions file by file
    total_applied = 0
    total_errors = 0
    changes_by_type = {
        "remove_unused_imports": 0,
        "fix_module_execution_block": 0,
        "extract_constants": 0,
        "add_return_types": 0,
    }
    
    for file_path, decisions in decisions_by_file.items():
        print(f"\n  Processing {file_path}:")
        
        # Sort by score to apply most important first
        decisions.sort(key=lambda d: d.score, reverse=True)
        
        for decision in decisions:
            if total_applied >= max_changes:
                print(f"  Reached max changes limit ({max_changes})")
                break
                
            result = orchestrator._execute_direct_refactor(decision, project_path)
            if result.applied:
                total_applied += 1
                changes_by_type[decision.action.value] += 1
                print(f"    ✓ {decision.action.value}")
            else:
                total_errors += 1
                if result.errors:
                    print(f"    ✗ {decision.action.value}: {result.errors[0]}")
    
    # Get detailed changes
    changes = orchestrator.direct_refactor.get_applied_changes()
    
    return {
        "project": project_path.name,
        "quality_decisions": len(quality_decisions),
        "changes_applied": total_applied,
        "errors": total_errors,
        "changes_by_type": changes_by_type,
        "changes": changes,
    }


def main() -> None:
    """Process semcod projects with hybrid refactoring."""
    if len(sys.argv) < 2:
        print("Usage: python hybrid_quality_refactor.py <semcod_root> [--max-changes N]")
        sys.exit(1)
    
    semcod_root = Path(sys.argv[1])
    max_changes = 50
    
    if "--max-changes" in sys.argv:
        idx = sys.argv.index("--max-changes")
        if idx + 1 < len(sys.argv):
            max_changes = int(sys.argv[idx + 1])
    
    # Find all projects with TODO.md
    projects = []
    for item in semcod_root.iterdir():
        if item.is_dir() and (item / "TODO.md").exists():
            projects.append(item)
    
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
        result = apply_all_quality_changes(project, max_changes)
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
    print("HYBRID QUALITY REFACTORING SUMMARY")
    print(f"{'='*60}")
    
    total_applied = sum(r["changes_applied"] for r in all_results)
    total_unused_removed = sum(r["changes_by_type"]["remove_unused_imports"] for r in all_results)
    total_constants_extracted = sum(r["changes_by_type"]["extract_constants"] for r in all_results)
    total_modules_fixed = sum(r["changes_by_type"]["fix_module_execution_block"] for r in all_results)
    total_returns_added = sum(r["changes_by_type"]["add_return_types"] for r in all_results)
    
    print(f"Total projects: {len(all_results)}")
    print(f"Total issues before: {total_before}")
    print(f"Total issues after: {total_after}")
    print(f"Total reduction: {total_before - total_after}")
    print(f"\nTotal changes applied: {total_applied}")
    print(f"  - Unused imports removed: {total_unused_removed}")
    print(f"  - Constants extracted: {total_constants_extracted}")
    print(f"  - Module blocks fixed: {total_modules_fixed}")
    print(f"  - Return types added: {total_returns_added}")
    
    # Show projects with most improvements
    print(f"\nTop improvements:")
    sorted_results = sorted(all_results, key=lambda r: r.get("before_issues", 0) - r.get("after_issues", 0), reverse=True)
    for r in sorted_results[:5]:
        reduction = r.get("before_issues", 0) - r.get("after_issues", 0)
        if reduction > 0:
            print(f"  {r['project']}: {reduction} fewer TODOs ({r['changes_applied']} changes)")
    
    # Save results
    import json
    results_file = semcod_root / "hybrid_refactor_results.json"
    results_file.write_text(json.dumps(all_results, indent=2))
    print(f"\nResults saved to: {results_file}")


if __name__ == "__main__":
    main()
