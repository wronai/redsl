"""Cycle report formatters."""

from __future__ import annotations

from typing import Any, Dict, List
from pathlib import Path

import yaml

from .core import _get_timestamp
from .refactor import _serialize_analysis, _serialize_decision, _get_timestamp as _get_ts


def format_cycle_report_yaml(report: Any, decisions: List[Any] = None, analysis: Any = None) -> str:
    """Format full cycle report as YAML for stdout."""
    data: Dict[str, Any] = {
        "redsl_report": {
            "timestamp": _get_timestamp(),
            "cycle": report.cycle_number,
            "analysis": _serialize_analysis(analysis) if analysis else {
                "summary": report.analysis_summary,
            },
            "plan": {
                "total_decisions": report.decisions_count,
                "decisions": [_serialize_decision(d) for d in (decisions or [])],
            },
            "execution": {
                "proposals_generated": report.proposals_generated,
                "proposals_applied": report.proposals_applied,
                "proposals_rejected": report.proposals_rejected,
                "success_rate": (
                    round(report.proposals_applied / report.proposals_generated, 2)
                    if report.proposals_generated > 0 else 0.0
                ),
                "results": [_serialize_result(r) for r in (report.results or [])],
            },
            "errors": report.errors if report.errors else [],
        }
    }
    return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)


def _cycle_report_header_lines(
    title: str,
    now: str,
    project_path: Path | None,
    log_file: Path | None,
    report: Any,
    dry_run: bool,
) -> list[str]:
    lines = [
        f"# {title}",
        "",
        f"> Generated: **{now}**  ",
    ]
    if project_path is not None:
        lines.append(f"> Project: `{project_path}`  ")
    lines.append(f"> Mode: **{'dry-run' if dry_run else 'executed'}**  ")
    if log_file is not None:
        lines.append(f"> Log file: `{log_file}`  ")
    if report is not None and hasattr(report, "cycle_number"):
        lines.append(f"> Cycle: **{report.cycle_number}**  ")
    lines.append("")
    lines.extend(["---", ""])
    return lines


def _analysis_summary_lines(analysis: Any) -> list[str]:
    """Format analysis section of summary."""
    if analysis is None:
        return []
    serialized = _serialize_analysis(analysis) or {}
    return [
        f"- Project: `{serialized.get('project_name', 'Unknown')}`",
        f"- Files: **{serialized.get('total_files', 0)}** | "
        f"Lines: **{serialized.get('total_lines', 0)}** | "
        f"Avg CC: **{serialized.get('avg_complexity', 0)}**",
        f"- Critical: **{serialized.get('critical_count', 0)}** | "
        f"Alerts: **{serialized.get('alerts_count', 0)}**",
    ]


def _execution_summary_lines(report: Any, dry_run: bool) -> list[str]:
    """Format execution section of summary."""
    if report is None or dry_run:
        return []
    return [
        f"- Proposals generated: **{getattr(report, 'proposals_generated', 0)}**",
        f"- Proposals applied: **{getattr(report, 'proposals_applied', 0)}**",
        f"- Proposals rejected: **{getattr(report, 'proposals_rejected', 0)}**",
        f"- Errors: **{len(getattr(report, 'errors', []))}**",
    ]


def _cycle_summary_lines(analysis: Any, decision_list: list[Any], report: Any, dry_run: bool) -> list[str]:
    lines = ["## Summary", ""]
    lines.extend(_analysis_summary_lines(analysis))
    lines.append(f"- Decisions selected: **{len(decision_list)}**")
    lines.extend(_execution_summary_lines(report, dry_run))
    lines.append("")
    return lines


def _cycle_top_decisions_lines(decision_list: list[Any]) -> list[str]:
    if not decision_list:
        return []

    lines = ["## Top Decisions", ""]
    for index, decision in enumerate(decision_list[:10], 1):
        action_obj = getattr(decision, "action", None)
        if action_obj is None:
            action = getattr(decision, "rule_name", "unknown")
        else:
            action = action_obj.value if hasattr(action_obj, "value") else str(action_obj)
        target = getattr(decision, "target_file", None)
        rule = getattr(getattr(decision, "rule", None), "name", None)
        if target is not None:
            lines.append(f"{index}. **{action}** → `{target}`")
        else:
            lines.append(f"{index}. **{action}**")
        lines.append(f"   - Score: `{getattr(decision, 'score', 0):.2f}`")
        if rule:
            lines.append(f"   - Rule: `{rule}`")
        rationale = getattr(decision, "rationale", None)
        if rationale:
            lines.append(f"   - Rationale: {rationale}")
        confidence = getattr(decision, "confidence", None)
        if confidence is not None:
            lines.append(f"   - Confidence: `{confidence:.2f}`")
    lines.append("")
    return lines


def _cycle_execution_results_lines(report: Any) -> list[str]:
    lines = ["## Execution Results", ""]
    for index, result in enumerate(getattr(report, "results", [])[:10], 1):
        serialized = _serialize_result(result)
        lines.append(f"{index}. **{serialized.get('action', 'direct_refactor')}**")
        lines.append(f"   - Target: `{serialized.get('target', 'N/A')}`")
        lines.append(f"   - Applied: `{serialized.get('applied', False)}`")
        lines.append(f"   - Validated: `{serialized.get('validated', False)}`")
        if serialized.get("confidence") is not None:
            lines.append(f"   - Confidence: `{serialized['confidence']:.2f}`")
        if serialized.get("summary"):
            lines.append(f"   - Summary: {serialized['summary']}")
        if serialized.get("errors"):
            lines.append(f"   - Errors: {', '.join(serialized['errors'])}")
    lines.append("")
    return lines


def _cycle_error_lines(report: Any) -> list[str]:
    if not getattr(report, "errors", None):
        return []

    lines = ["## Errors", ""]
    for error in report.errors:
        lines.append(f"- {error}")
    lines.append("")
    return lines


def format_cycle_report_markdown(
    report: Any,
    decisions: List[Any] | None = None,
    analysis: Any = None,
    project_path: Path | None = None,
    log_file: Path | None = None,
    dry_run: bool = False,
) -> str:
    """Format a refactor cycle as a Markdown report."""
    from datetime import datetime

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    decision_list = decisions or []
    title = "reDSL Refactor Plan" if dry_run else "reDSL Refactor Report"
    lines: list[str] = []
    lines.extend(_cycle_report_header_lines(title, now, project_path, log_file, report, dry_run))
    lines.extend(_cycle_summary_lines(analysis, decision_list, report, dry_run))
    lines.extend(_cycle_top_decisions_lines(decision_list))
    if report is not None and not dry_run:
        lines.extend(_cycle_execution_results_lines(report))
        lines.extend(_cycle_error_lines(report))
    lines.extend([
        "---",
        "",
        "_Report generated by [reDSL](https://github.com/wronai/redsl)_",
    ])
    return "\n".join(lines)


def format_plan_yaml(decisions: List[Any], analysis: Any = None) -> str:
    """Format dry-run plan as YAML for stdout."""
    from .refactor import _count_decision_types

    data: Dict[str, Any] = {
        "redsl_plan": {
            "timestamp": _get_timestamp(),
            "analysis": _serialize_analysis(analysis) if analysis else None,
            "decisions": [_serialize_decision(d) for d in decisions],
            "summary": {
                "total_decisions": len(decisions),
                "decision_types": _count_decision_types(decisions),
                "estimated_impact": round(sum(d.score for d in decisions), 2),
            },
        }
    }
    return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)


def _serialize_result(result: Any) -> Dict[str, Any]:
    """Serialize a RefactorResult to dict."""
    entry: Dict[str, Any] = {
        "applied": result.applied,
        "validated": result.validated,
    }
    if result.errors:
        entry["errors"] = result.errors
    if result.warnings:
        entry["warnings"] = result.warnings

    proposal = result.proposal
    if proposal is not None:
        entry["action"] = proposal.refactor_type
        entry["target"] = proposal.decision.target_file if proposal.decision else None
        entry["confidence"] = round(proposal.confidence, 2)
        entry["summary"] = proposal.summary
        if proposal.changes:
            entry["files_changed"] = [c.file_path for c in proposal.changes]
    else:
        # Direct refactor — no proposal object
        entry["action"] = "direct_refactor"
    return entry


def format_cycle_report_toon(
    report: Any,
    decisions: List[Any] | None = None,
    analysis: Any = None,
    project_path: Path | None = None,
    log_file: Path | None = None,
    dry_run: bool = False,
) -> str:
    """Format a refactor cycle as TOON for planfile integration.

    TOON format allows planfile to parse report structurally
    and auto-create tickets from decisions.
    """
    from datetime import datetime

    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M")
    date_str = now.strftime("%Y-%m-%d")
    decision_list = decisions or []

    lines: list[str] = []

    # Header with metadata (code2llm-style)
    serialized = _serialize_analysis(analysis) if analysis else {}
    total_files = serialized.get("total_files", 0)
    total_lines = serialized.get("total_lines", 0)
    avg_cc = serialized.get("avg_complexity", 0)
    critical_count = serialized.get("critical_count", 0)

    lines.append(f"# redsl | refactor | {date_str}")
    lines.append(f"# mode={'dry-run' if dry_run else 'executed'} | files={total_files} | lines={total_lines}")
    lines.append(f"# CC̄={avg_cc:.1f} | critical={critical_count} | decisions={len(decision_list)}")
    lines.append("")

    # STATUS section
    status = "planned" if dry_run else ("success" if not getattr(report, "errors", []) else "partial")
    lines.append(f"STATUS[{status}]")
    lines.append("")

    # DECISIONS section (like REFACTOR in analysis.toon)
    if decision_list:
        lines.append(f"DECISIONS[{len(decision_list)}]:")
        for idx, d in enumerate(decision_list, 1):
            action_obj = getattr(d, "action", None)
            action = action_obj.value if hasattr(action_obj, "value") else str(action_obj or "unknown")
            target = getattr(d, "target_file", "unknown")
            score = getattr(d, "score", 0)
            rationale = getattr(d, "rationale", "")[:60]  # Truncate for TOON
            lines.append(f"  {idx}. {action} → {target} (score={score:.2f}) {rationale}")
        lines.append("")

    # EXECUTION section (only for non-dry-run)
    if report is not None and not dry_run:
        generated = getattr(report, "proposals_generated", 0)
        applied = getattr(report, "proposals_applied", 0)
        rejected = getattr(report, "proposals_rejected", 0)
        success_rate = round(applied / generated, 2) if generated > 0 else 0.0

        lines.append(f"EXECUTION[applied={applied}, rejected={rejected}, rate={success_rate}]:")

        for result in getattr(report, "results", [])[:10]:
            serialized_result = _serialize_result(result)
            act = serialized_result.get("action", "unknown")
            tgt = serialized_result.get("target", "N/A")
            ok = "✓" if serialized_result.get("applied") else "✗"
            lines.append(f"  {ok} {act}: {tgt}")
        lines.append("")

    # ERRORS section
    errors = getattr(report, "errors", []) if report else []
    if errors:
        lines.append(f"ERRORS[{len(errors)}]:")
        for err in errors:
            lines.append(f"  ! {err}")
        lines.append("")

    # METRICS section (like LAYERS in analysis.toon)
    if serialized.get("metrics"):
        lines.append(f"METRICS[{len(serialized['metrics'])}]:")
        for m in serialized["metrics"][:10]:
            file_path = m.get("file", "unknown")
            func = m.get("name", "-")
            cc = m.get("cc", 0)
            loc = m.get("loc", 0)
            flag = "🔴" if cc >= 15 else ("🟡" if cc >= 10 else "🟢")
            lines.append(f"  {flag} {file_path}::{func} CC={cc} LOC={loc}")
        lines.append("")

    # Footer with log reference
    if log_file:
        lines.append(f"LOG: {log_file}")

    return "\n".join(lines)
