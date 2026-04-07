"""
Narzędzia pomocnicze dla analizatora kodu.
"""

from __future__ import annotations

import fnmatch
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# Default patterns to always ignore (common virtualenv/cache dirs)
DEFAULT_IGNORE_PATTERNS = {
    ".venv",
    "venv",
    ".testvenv",
    "testvenv",
    ".tox",
    "tox",
    "dist",
    "build",
    "__pycache__",
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
    "*.egg-info",
    ".eggs",
    "htmlcov",
    ".coverage",
}


def _load_gitignore_patterns(project_dir: Path) -> set[str]:
    """Read .gitignore file and return set of patterns."""
    patterns = set()
    gitignore = project_dir / ".gitignore"
    if gitignore.exists():
        try:
            content = gitignore.read_text(encoding="utf-8", errors="ignore")
            for line in content.splitlines():
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue
                # Remove leading / if present (anchored patterns)
                if line.startswith("/"):
                    line = line[1:]
                patterns.add(line)
        except OSError:
            pass
    return patterns


def _should_ignore_file(
    file_path: Path, project_dir: Path, gitignore_patterns: set[str]
) -> bool:
    """Check if file should be ignored based on default patterns and .gitignore."""
    # Check default patterns (match against path parts)
    for part in file_path.parts:
        if part in DEFAULT_IGNORE_PATTERNS:
            return True
        # Check wildcard patterns like *.egg-info
        for pattern in DEFAULT_IGNORE_PATTERNS:
            if pattern.startswith("*") and fnmatch.fnmatch(part, pattern):
                return True

    # Check gitignore patterns
    if gitignore_patterns:
        try:
            rel_path = file_path.relative_to(project_dir)
            rel_str = str(rel_path).replace("\\", "/")

            for pattern in gitignore_patterns:
                # Handle directory patterns (ending with /)
                if pattern.endswith("/"):
                    dir_pattern = pattern.rstrip("/")
                    if any(part == dir_pattern for part in rel_path.parts):
                        return True
                # Handle wildcard patterns
                elif "*" in pattern or "?" in pattern or "[" in pattern:
                    # Match against full path or filename
                    if fnmatch.fnmatch(rel_str, pattern):
                        return True
                    if fnmatch.fnmatch(rel_path.name, pattern):
                        return True
                # Handle exact matches
                else:
                    if pattern in rel_str.split("/"):
                        return True
                    if rel_str.startswith(pattern + "/"):
                        return True
        except ValueError:
            pass  # file_path is not relative to project_dir

    return False


def _try_number(val: str) -> int | float | str:
    """Spróbuj skonwertować na liczbę."""
    try:
        return int(val)
    except ValueError:
        try:
            return float(val)
        except ValueError:
            return val
