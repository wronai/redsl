#!/usr/bin/env python3
"""Batch apply reDSL to semcod projects."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from app.orchestrator import RefactorOrchestrator, CycleReport
from app.config import AgentConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def apply_refactor(project_path: Path, max_actions: int = 10) -> CycleReport:
    """Apply reDSL to a project and return the report."""
    logger.info(f"Starting reDSL on {project_path}")
    
    # Initialize orchestrator with apply_changes=True
    config = AgentConfig()
    config.refactor.apply_changes = True
    config.refactor.reflection_rounds = 1  # Keep some reflection for quality
    
    orchestrator = RefactorOrchestrator(config)
    
    # Run the refactoring cycle
    report = orchestrator.run_cycle(project_path, max_actions=max_actions)
    
    return report


def measure_todo_reduction(project_path: Path) -> dict[str, Any]:
    """Measure TODO.md before and after refactoring."""
    todo_file = project_path / "TODO.md"
    if not todo_file.exists():
        return {"before": 0, "after": 0, "reduction": 0}
    
    content = todo_file.read_text(encoding="utf-8")
    lines = content.splitlines()
    
    # Count active issues (lines starting with - [ ])
    active_issues = sum(1 for line in lines if line.startswith("- [ ]"))
    
    return {"active_issues": active_issues, "total_lines": len(lines)}


def main() -> None:
    """Process semcod projects."""
    if len(sys.argv) < 2:
        print("Usage: python batch_refactor_semcod.py <semcod_root> [--max-actions N]")
        sys.exit(1)
    
    semcod_root = Path(sys.argv[1])
    max_actions = 10
    
    if "--max-actions" in sys.argv:
        idx = sys.argv.index("--max-actions")
        if idx + 1 < len(sys.argv):
            max_actions = int(sys.argv[idx + 1])
    
    # Find all projects with TODO.md
    projects = []
    for item in semcod_root.iterdir():
        if item.is_dir() and (item / "TODO.md").exists():
            projects.append(item)
    
    print(f"\nFound {len(projects)} projects with TODO.md")
    
    # Process each project
    total_results = {
        "projects_processed": 0,
        "total_decisions": 0,
        "total_applied": 0,
        "total_errors": 0,
        "project_details": []
    }
    
    for project in sorted(projects):
        print(f"\n{'='*60}")
        print(f"Processing: {project.name}")
        print(f"{'='*60}")
        
        # Measure before
        before = measure_todo_reduction(project)
        print(f"TODO.md: {before['active_issues']} active issues")
        
        # Apply refactoring
        try:
            report = apply_refactor(project, max_actions)
            
            print(f"\nResults:")
            print(f"  Decisions: {report.decisions_count}")
            print(f"  Proposals generated: {report.proposals_generated}")
            print(f"  Applied: {report.proposals_applied}")
            print(f"  Rejected: {report.proposals_rejected}")
            
            if report.errors:
                print(f"  Errors: {len(report.errors)}")
                for error in report.errors[:3]:
                    print(f"    - {error}")
            
            # Measure after
            after = measure_todo_reduction(project)
            reduction = before['active_issues'] - after['active_issues']
            
            print(f"\nTODO.md change: {before['active_issues']} → {after['active_issues']} (reduction: {reduction})")
            
            # Collect results
            total_results["projects_processed"] += 1
            total_results["total_decisions"] += report.decisions_count
            total_results["total_applied"] += report.proposals_applied
            total_results["total_errors"] += len(report.errors)
            
            total_results["project_details"].append({
                "name": project.name,
                "decisions": report.decisions_count,
                "applied": report.proposals_applied,
                "errors": len(report.errors),
                "todo_reduction": reduction
            })
            
        except Exception as e:
            logger.error(f"Failed to process {project}: {e}")
            total_results["total_errors"] += 1
    
    # Summary
    print(f"\n{'='*60}")
    print("BATCH REFACTORING SUMMARY")
    print(f"{'='*60}")
    print(f"Projects processed: {total_results['projects_processed']}")
    print(f"Total decisions: {total_results['total_decisions']}")
    print(f"Total changes applied: {total_results['total_applied']}")
    print(f"Total errors: {total_results['total_errors']}")
    
    print(f"\nProject details:")
    for detail in total_results["project_details"]:
        print(f"  {detail['name']}: {detail['applied']} applied, {detail['todo_reduction']} TODO reduction")
    
    # Save results
    import json
    results_file = semcod_root / "redsl_results.json"
    results_file.write_text(json.dumps(total_results, indent=2))
    print(f"\nResults saved to: {results_file}")


if __name__ == "__main__":
    main()
