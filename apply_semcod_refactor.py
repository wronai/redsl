#!/usr/bin/env python3
"""Apply reDSL to semcod projects."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from app.orchestrator import RefactorOrchestrator
from app.config import AgentConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Apply reDSL to a semcod project."""
    if len(sys.argv) < 2:
        print("Usage: python apply_semcod_refactor.py <project_path> [--dry-run]")
        sys.exit(1)
    
    project_path = Path(sys.argv[1])
    dry_run = "--dry-run" in sys.argv
    
    if not project_path.exists():
        logger.error(f"Project path does not exist: {project_path}")
        sys.exit(1)
    
    logger.info(f"Starting reDSL on {project_path} (dry_run={dry_run})")
    
    # Initialize orchestrator
    config = AgentConfig()
    if dry_run:
        config.refactor.apply_changes = False
        config.refactor.reflection_rounds = 0
    
    orchestrator = RefactorOrchestrator(config)
    
    # First, explain what we're going to do
    print("\n=== REFACTORING PLAN ===")
    explanation = orchestrator.explain_decisions(project_path, limit=20)
    print(explanation)
    
    if not dry_run:
        # Ask for confirmation
        response = input("\nApply these changes? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            return
        
        # Run the refactoring cycle
        print("\n=== APPLYING REFACTORING ===")
        report = orchestrator.run_cycle(project_path, max_actions=10)
        
        print(f"\n=== RESULTS ===")
        print(f"Cycle {report.cycle_number} complete")
        print(f"Analysis: {report.analysis_summary}")
        print(f"Decisions: {report.decisions_count}")
        print(f"Proposals generated: {report.proposals_generated}")
        print(f"Applied: {report.proposals_applied}")
        print(f"Rejected: {report.proposals_rejected}")
        
        if report.errors:
            print(f"\nErrors:")
            for error in report.errors[:5]:
                print(f"  - {error}")
        
        # Show memory stats
        stats = orchestrator.get_memory_stats()
        print(f"\nMemory: {stats}")


if __name__ == "__main__":
    main()
