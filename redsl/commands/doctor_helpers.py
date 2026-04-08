"""Helper functions for project doctor."""

import ast
import subprocess
import sys
from pathlib import Path

def _find_pip(root: Path) -> str:
    """Find the best pip executable for a project."""
    for venv_name in (".venv", "venv"):
        venv_pip = root / venv_name / "bin" / "pip"
        if venv_pip.exists():
            try:
                proc = subprocess.run(
                    [str(venv_pip), "--version"],
                    capture_output=True, text=True, timeout=5,
                )
                if proc.returncode == 0:
                    return str(venv_pip)
            except (subprocess.TimeoutExpired, OSError):
                pass
    # Fallback: use sys.executable -m pip (most reliable)
    return f"{sys.executable} -m pip"

def _fix_via_git_revert(path: Path, root: Path) -> bool:
    """Last resort: revert a broken file to its git HEAD version if it parses."""
    rel = str(path.relative_to(root))
    try:
        proc = subprocess.run(
            ["git", "show", f"HEAD:{rel}"],
            capture_output=True, text=True, cwd=str(root), timeout=5,
        )
        if proc.returncode != 0:
            return False
        head_src = proc.stdout
        ast.parse(head_src)
        path.write_text(head_src, encoding="utf-8")
        return True
    except (subprocess.TimeoutExpired, SyntaxError, OSError):
        return False
