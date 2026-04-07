"""Output formatters for reDSL."""

from __future__ import annotations

import json
import yaml
from typing import Any, Dict, List
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.syntax import Syntax

console = Console()


def format_refactor_plan(
    decisions: List[Any], 
    format: str = "text",
    analysis: Any = None
) -> str:
    """Format refactoring plan in specified format."""
    if format == "yaml":
        return _format_yaml(decisions, analysis)
    elif format == "json":
        return _format_json(decisions, analysis)
    else:
        return _format_text(decisions, analysis)


def _format_yaml(decisions: List[Any], analysis: Any = None) -> str:
    """Format as YAML."""
    data = {
        "refactoring_plan": {
            "timestamp": _get_timestamp(),
            "analysis": _serialize_analysis(analysis) if analysis else None,
            "decisions": [_serialize_decision(d) for d in decisions],
            "summary": {
                "total_decisions": len(decisions),
                "decision_types": _count_decision_types(decisions),
                "estimated_impact": sum(d.score for d in decisions)
            }
        }
    }
    return yaml.dump(data, default_flow_style=False, sort_keys=False)


def _format_json(decisions: List[Any], analysis: Any = None) -> str:
    """Format as JSON."""
    data = {
        "refactoring_plan": {
            "timestamp": _get_timestamp(),
            "analysis": _serialize_analysis(analysis) if analysis else None,
            "decisions": [_serialize_decision(d) for d in decisions],
            "summary": {
                "total_decisions": len(decisions),
                "decision_types": _count_decision_types(decisions),
                "estimated_impact": sum(d.score for d in decisions)
            }
        }
    }
    return json.dumps(data, indent=2, default=str)


def _format_text(decisions: List[Any], analysis: Any = None) -> str:
    """Format as rich text."""
    output = []
    
    # Header
    output.append("\n=== REFACTORING PLAN ===\n")
    
    # Analysis summary
    if analysis:
        output.append(f"Analysis complete: {len(analysis.files)} files, "
                     f"{analysis.total_lines} lines, avg CC={analysis.avg_complexity:.1f}, "
                     f"{len(analysis.critical_alerts)} critical\n")
    
    # Decision summary
    decision_types = _count_decision_types(decisions)
    output.append(f"Decision types: {decision_types}\n")
    output.append(f"Evaluated {len(analysis.files) if analysis else 'N/A'} contexts → {len(decisions)} decisions\n")
    
    # Top decisions table
    if decisions:
        table = Table(title=f"Top {min(5, len(decisions))} refactoring decisions")
        table.add_column("Rank", style="cyan", width=6)
        table.add_column("Decision", style="magenta")
        table.add_column("Rule", style="green")
        table.add_column("Target", style="yellow")
        table.add_column("Score", style="red", justify="right")
        table.add_column("Confidence", style="blue", justify="right")
        
        for i, decision in enumerate(decisions[:5], 1):
            table.add_row(
                str(i),
                decision.action.value,
                decision.rule.name if hasattr(decision, 'rule') and decision.rule else "N/A",
                str(decision.target_path),
                f"{decision.score:.2f}",
                f"{getattr(decision, 'confidence', 0):.2f}"
            )
        
        # Capture table output
        with console.capture() as capture:
            console.print(table)
        output.append(capture.get())
    
    # Detailed decisions
    for i, decision in enumerate(decisions[:5], 1):
        output.append(f"\n{i}. Decision: {decision.action.value}")
        output.append(f"   Rule: {decision.rule.name if hasattr(decision, 'rule') and decision.rule else 'N/A'}")
        output.append(f"   Target: {decision.target_path}")
        output.append(f"   Score: {decision.score:.2f}")
        if hasattr(decision, 'rationale') and decision.rationale:
            output.append(f"   Rationale: {decision.rationale}")
        if hasattr(decision, 'confidence'):
            output.append(f"   Confidence (metric): {decision.confidence:.2f}")
    
    return "\n".join(output)


def _serialize_analysis(analysis: Any) -> Dict[str, Any]:
    """Serialize analysis object to dict."""
    if not analysis:
        return None
    
    return {
        "project_name": analysis.project_name,
        "total_files": analysis.total_files,
        "total_lines": analysis.total_lines,
        "avg_complexity": analysis.avg_cc,
        "critical_count": analysis.critical_count,
        "alerts_count": len(analysis.alerts),
        "metrics_count": len(analysis.metrics),
        "metrics": [
            {
                "file": str(m.file_path),
                "name": m.function_name,
                "cc": m.cyclomatic_complexity,
                "loc": m.module_lines
            } for m in analysis.metrics[:10]
        ]
    }


def _serialize_decision(decision: Any) -> Dict[str, Any]:
    """Serialize decision object to dict."""
    data = {
        "action": decision.action.value if hasattr(decision, 'action') else str(decision.action),
        "target_path": str(decision.target_file),
        "score": decision.score,
    }
    
    if hasattr(decision, 'rule') and decision.rule:
        data["rule"] = decision.rule.name
    
    if hasattr(decision, 'rationale'):
        data["rationale"] = decision.rationale
    
    if hasattr(decision, 'confidence'):
        data["confidence"] = decision.confidence
    
    if hasattr(decision, 'metadata'):
        data["metadata"] = decision.metadata
    
    return data


def _count_decision_types(decisions: List[Any]) -> Dict[str, int]:
    """Count decisions by type."""
    types = {}
    for decision in decisions:
        action = decision.action.value if hasattr(decision, 'action') else str(decision.action)
        types[action] = types.get(action, 0) + 1
    return types


def _get_timestamp() -> str:
    """Get current timestamp."""
    from datetime import datetime
    return datetime.now().isoformat()


def format_batch_results(results: List[Dict[str, Any]], format: str = "text") -> str:
    """Format batch processing results."""
    if format == "yaml":
        return yaml.dump({"batch_results": results}, default_flow_style=False, sort_keys=False)
    elif format == "json":
        return json.dumps({"batch_results": results}, indent=2, default=str)
    else:
        # Rich text format
        output = ["\n=== BATCH PROCESSING RESULTS ===\n"]
        
        for i, result in enumerate(results, 1):
            output.append(f"{i}. Project: {result.get('project_name', 'Unknown')}")
            output.append(f"   Status: {result.get('status', 'Unknown')}")
            output.append(f"   Files processed: {result.get('files_processed', 0)}")
            output.append(f"   Changes applied: {result.get('changes_applied', 0)}")
            if result.get('error'):
                output.append(f"   Error: {result['error']}")
            output.append("")
        
        # Summary
        total = len(results)
        successful = sum(1 for r in results if r.get('status') == 'success')
        output.append(f"\nSummary: {successful}/{total} projects processed successfully")
        
        return "\n".join(output)


def format_debug_info(info: Dict[str, Any], format: str = "text") -> str:
    """Format debug information."""
    if format == "yaml":
        return yaml.dump(info, default_flow_style=False, sort_keys=False)
    elif format == "json":
        return json.dumps(info, indent=2, default=str)
    else:
        # Rich text format with syntax highlighting
        output = ["\n=== DEBUG INFORMATION ===\n"]
        
        for key, value in info.items():
            if isinstance(value, (dict, list)):
                output.append(f"{key}:")
                if format == "text":
                    value_str = json.dumps(value, indent=2, default=str)
                    syntax = Syntax(value_str, "json", theme="monokai", line_numbers=True)
                    with console.capture() as capture:
                        console.print(syntax)
                    output.append(capture.get())
            else:
                output.append(f"{key}: {value}")
        
        return "\n".join(output)
