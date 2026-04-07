#!/usr/bin/env python3
"""Debug script to see what decisions are generated for a project."""

from pathlib import Path
from app.orchestrator import RefactorOrchestrator
from app.config import AgentConfig
from app.analyzers import CodeAnalyzer
from dotenv import load_dotenv

load_dotenv()

def debug_decisions(project_path: Path):
    """Show all decisions generated for a project."""
    print(f"\n{'='*60}")
    print(f"Debugging decisions for: {project_path.name}")
    print(f"{'='*60}")
    
    # Initialize
    config = AgentConfig.from_env()
    config.refactor.apply_changes = False  # Don't apply changes
    config.refactor.reflection_rounds = 1
    
    orchestrator = RefactorOrchestrator(config)
    analyzer = CodeAnalyzer()
    
    # Analyze
    analysis = analyzer.analyze_project(project_path)
    contexts = analysis.to_dsl_contexts()
    
    # Get ALL decisions (not just top)
    all_decisions = orchestrator.dsl_engine.evaluate(contexts)
    
    print(f"\nTotal decisions found: {len(all_decisions)}")
    
    # Group by action
    by_action = {}
    for d in all_decisions:
        if d.action not in by_action:
            by_action[d.action] = []
        by_action[d.action].append(d)
    
    print("\nDecisions by action type:")
    for action, decisions in sorted(by_action.items()):
        print(f"\n{action.value} ({len(decisions)} decisions):")
        for d in decisions[:3]:  # Show top 3 for each
            print(f"  - {d.target_file} (score={d.score:.2f}, rule={d.rule_name})")
        if len(decisions) > 3:
            print(f"  ... and {len(decisions) - 3} more")
    
    # Show top decisions
    top_decisions = orchestrator.dsl_engine.top_decisions(contexts, limit=10)
    print(f"\nTop 10 decisions by score:")
    for i, d in enumerate(top_decisions, 1):
        print(f"{i:2d}. {d.action.value:20s} {d.target_file:30s} (score={d.score:.2f})")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python debug_decisions.py <project_path>")
        sys.exit(1)
    
    debug_decisions(Path(sys.argv[1]))
