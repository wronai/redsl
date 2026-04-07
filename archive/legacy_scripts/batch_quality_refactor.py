#!/usr/bin/env python3
"""Batch apply quality refactorings to semcod projects."""

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


def apply_quality_refactors(project_path: Path) -> dict[str, Any]:
    """Apply all quality refactorings to a project."""
    print(f"\n{'='*60}")
    print(f"Processing: {project_path.name}")
    print(f"{'='*60}")
    
    # Initialize orchestrator
    config = AgentConfig()
    config.refactor.apply_changes = True
    config.refactor.reflection_rounds = 0
    
    orchestrator = RefactorOrchestrator(config)
    analyzer = CodeAnalyzer()
    
    # Get all decisions
    analysis = analyzer.analyze_project(project_path)
    contexts = analysis.to_dsl_contexts()
    all_decisions = orchestrator.dsl_engine.evaluate(contexts)
    
    # Filter for quality decisions only
    quality_decisions = [d for d in all_decisions if d.action in [
        RefactorAction.REMOVE_UNUSED_IMPORTS,
        RefactorAction.FIX_MODULE_EXECUTION_BLOCK,
        RefactorAction.EXTRACT_CONSTANTS,
        RefactorAction.ADD_RETURN_TYPES,
    ]]
    
    print(f"Found {len(quality_decisions)} quality decisions")
    
    # Group by file to avoid conflicts
    decisions_by_file: dict[str, list[Any]] = {}
    for d in quality_decisions:
        if d.target_file not in decisions_by_file:
            decisions_by_file[d.target_file] = []
        decisions_by_file[d.target_file].append(d)
    
    # Execute decisions file by file
    total_applied = 0
    total_errors = 0
    
    for file_path, decisions in decisions_by_file.items():
        print(f"\n  Processing {file_path}:")
        
        # Sort by priority (execute in order)
        decisions.sort(key=lambda d: d.score, reverse=True)
        
        for decision in decisions:
            result = orchestrator._execute_decision(decision, project_path)
            if result.applied:
                total_applied += 1
                print(f"    ✓ {decision.action.value}")
            else:
                total_errors += 1
                if result.errors:
                    print(f"    ✗ {decision.action.value}: {result.errors[0]}")
    
    # Get detailed changes
    changes = orchestrator.direct_refactor.get_applied_changes()
    
    # Measure TODO reduction
    todo_file = project_path / "TODO.md"
    before_issues = 0
    after_issues = 0
    
    if todo_file.exists():
        content = todo_file.read_text(encoding="utf-8")
        before_issues = sum(1 for line in content.splitlines() if line.startswith("- [ ]"))
    
    return {
        "project": project_path.name,
        "quality_decisions": len(quality_decisions),
        "changes_applied": total_applied,
        "errors": total_errors,
        "before_issues": before_issues,
        "after_issues": after_issues,
        "changes": changes,
    }


def main() -> None:
    """Process semcod projects."""
    if len(sys.argv) < 2:
        print("Usage: python batch_quality_refactor.py <semcod_root>")
        sys.exit(1)
    
    semcod_root = Path(sys.argv[1])
    
    # Find all projects with TODO.md
    projects = []
    for item in semcod_root.iterdir():
        if item.is_dir() and (item / "TODO.md").exists():
            projects.append(item)
    
    print(f"Found {len(projects)} projects with TODO.md")
    
    # Process each project
    all_results = []
    for project in sorted(projects):
        result = apply_quality_refactors(project)
        all_results.append(result)
        
        # Regenerate TODO.md with prefact
        print(f"  Regenerating TODO.md with prefact...")
        import subprocess
        subprocess.run(["prefact", "-a"], cwd=project, capture_output=True)
        
        # Count issues after
        todo_file = project / "TODO.md"
        if todo_file.exists():
            content = todo_file.read_text(encoding="utf-8")
            result["after_issues"] = sum(1 for line in content.splitlines() if line.startswith("- [ ]"))
            reduction = result["before_issues"] - result["after_issues"]
            print(f"  TODO reduction: {result['before_issues']} → {result['after_issues']} ({reduction} fewer)")
    
    # Summary
    print(f"\n{'='*60}")
    print("BATCH QUALITY REFACTORING SUMMARY")
    print(f"{'='*60}")
    
    total_before = sum(r["before_issues"] for r in all_results)
    total_after = sum(r["after_issues"] for r in all_results)
    total_applied = sum(r["changes_applied"] for r in all_results)
    
    print(f"Total projects: {len(all_results)}")
    print(f"Total issues before: {total_before}")
    print(f"Total issues after: {total_after}")
    print(f"Total reduction: {total_before - total_after}")
    print(f"Total changes applied: {total_applied}")
    
    print(f"\nPer-project results:")
    for r in all_results:
        if r["changes_applied"] > 0:
            reduction = r["before_issues"] - r["after_issues"]
            print(f"  {r['project']}: {r['changes_applied']} changes, {reduction} TODO reduction")
    
    # Save results
    import json
    results_file = semcod_root / "quality_refactor_results.json"
    results_file.write_text(json.dumps(all_results, indent=2))
    print(f"\nResults saved to: {results_file}")


if __name__ == "__main__":
    main()
