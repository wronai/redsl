"""Review — staged-change code review assistant.

Generates a structured code review for the current git diff (staged + unstaged)
using the LLM. Falls back to a static AST-based review if LLM is unavailable.
"""

from __future__ import annotations

import ast
import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def review_staged_changes(
    project_dir: Path,
    model_override: str | None = None,
    max_diff_chars: int = 8000,
) -> str:
    """Return a textual code review for all staged/unstaged changes.

    Uses the reDSL LLM layer when configured; otherwise falls back to a
    static AST analysis of changed files.
    """
    project_dir = Path(project_dir).resolve()
    diff = _get_diff(project_dir)

    if not diff.strip():
        return "No changes detected."

    try:
        from redsl.config import AgentConfig
        from redsl.llm import LLMLayer

        config = AgentConfig.from_env()
        llm = LLMLayer(config.llm)
        return _llm_review(llm, diff[:max_diff_chars], model_override)
    except Exception as exc:
        logger.warning("LLM review failed (%s); falling back to static review.", exc)
        return _static_review(project_dir, diff)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_diff(project_dir: Path) -> str:
    """Return combined staged + unstaged diff for Python files."""
    diffs: list[str] = []
    for flag in (["--cached"], []):
        try:
            proc = subprocess.run(
                ["git", "diff", *flag, "--", "*.py"],
                capture_output=True, text=True,
                cwd=str(project_dir), timeout=15,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                diffs.append(proc.stdout)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
    return "\n".join(diffs)


def _llm_review(llm: Any, diff: str, model_override: str | None) -> str:
    """Ask the LLM to review the diff."""
    messages = [
        {
            "role": "system",
            "content": (
                "You are a senior Python code reviewer. "
                "Analyze the diff and provide a structured review with: "
                "1) Summary, 2) Potential bugs, 3) Complexity concerns, "
                "4) Suggestions. Be concise and actionable."
            ),
        },
        {
            "role": "user",
            "content": f"Review this Python diff:\n\n```diff\n{diff}\n```",
        },
    ]
    response = llm.call(messages, model=model_override)
    return response.content


def _static_review(project_dir: Path, diff: str) -> str:
    """AST-based static review when LLM is unavailable."""
    changed_files = _parse_changed_files_from_diff(diff)
    issues: list[str] = []

    for rel_path in changed_files:
        fp = project_dir / rel_path
        if not fp.exists():
            continue
        try:
            source = fp.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source)
        except (OSError, SyntaxError) as e:
            issues.append(f"  - {rel_path}: cannot parse ({e})")
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                cc = _simple_cc(node)
                if cc > 12:
                    issues.append(
                        f"  - {rel_path}:{node.lineno} {node.name}() CC={cc} (high)"
                    )

        lines = len(source.splitlines())
        if lines > 400:
            issues.append(f"  - {rel_path}: {lines} lines (consider splitting)")

    if not issues:
        return "Static review: no major issues detected."
    return "Static review found:\n" + "\n".join(issues)


def _parse_changed_files_from_diff(diff: str) -> list[str]:
    """Extract changed file paths from a unified diff."""
    paths: list[str] = []
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            path = line[6:].strip()
            if path.endswith(".py"):
                paths.append(path)
    return paths


def _simple_cc(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """Very fast CC estimate (branch count + 1)."""
    count = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                               ast.With, ast.Assert, ast.BoolOp)):
            count += 1
    return count
