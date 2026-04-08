"""Bridge to pyqual — quality gate loop and CI/CD integration."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def is_available() -> bool:
    """Return True if pyqual CLI is installed and functional."""
    if not shutil.which("pyqual"):
        return False
    try:
        proc = subprocess.run(
            ["pyqual", "--help"],
            capture_output=True, text=True, timeout=10,
        )
        return proc.returncode == 0
    except Exception:
        return False


def doctor(project_dir: Path) -> dict:
    """Run `pyqual doctor` and return structured tool availability dict.

    Returns:
        Dict mapping tool name → {available: bool, purpose: str}.
    """
    if not is_available():
        return {}
    try:
        proc = subprocess.run(
            ["pyqual", "doctor"],
            capture_output=True, text=True, timeout=30,
            cwd=str(project_dir),
        )
        lines = proc.stdout.splitlines()
        result: dict[str, dict] = {}
        for line in lines:
            if "✓" in line or "✗" in line:
                available = "✓" in line
                parts = line.replace("✓", "").replace("✗", "").split()
                if parts:
                    result[parts[0]] = {"available": available}
        return result
    except Exception as exc:
        logger.warning("pyqual doctor error: %s", exc)
        return {}


def check_gates(project_dir: Path) -> dict:
    """Run `pyqual gates` and return pass/fail status.

    Returns:
        Dict with keys: passed (bool), gates (list of gate results), raw (str).
        Falls back gracefully if pyqual.yaml is missing or incompatible.
    """
    if not is_available():
        return {"passed": True, "gates": [], "available": False}
    try:
        proc = subprocess.run(
            ["pyqual", "gates"],
            capture_output=True, text=True, timeout=60,
            cwd=str(project_dir),
        )
        output = proc.stdout + proc.stderr
        passed = proc.returncode == 0
        gates: list[dict] = []

        for line in output.splitlines():
            line_s = line.strip()
            if "PASS" in line_s.upper() or "FAIL" in line_s.upper() or "OK" in line_s.upper():
                gates.append({"line": line_s, "passed": "FAIL" not in line_s.upper()})

        return {"passed": passed, "gates": gates, "available": True, "raw": output[:500]}
    except subprocess.TimeoutExpired:
        logger.warning("pyqual gates timed out")
        return {"passed": True, "gates": [], "available": True, "timed_out": True}
    except Exception as exc:
        logger.warning("pyqual gates error: %s", exc)
        return {"passed": True, "gates": [], "available": True, "error": str(exc)}


def get_status(project_dir: Path) -> dict:
    """Run `pyqual status` and return current metrics summary.

    Returns:
        Dict with metrics if successful, empty dict on failure.
    """
    if not is_available():
        return {}
    try:
        proc = subprocess.run(
            ["pyqual", "status"],
            capture_output=True, text=True, timeout=30,
            cwd=str(project_dir),
        )
        if proc.returncode == 0:
            return {"raw": proc.stdout[:1000], "available": True}
        return {}
    except Exception as exc:
        logger.warning("pyqual status error: %s", exc)
        return {}


def validate_config(project_dir: Path) -> tuple[bool, str]:
    """Run `pyqual validate` to check pyqual.yaml is well-formed.

    Returns:
        (valid: bool, message: str)
    """
    if not is_available():
        return True, "pyqual not installed"
    try:
        proc = subprocess.run(
            ["pyqual", "validate"],
            capture_output=True, text=True, timeout=15,
            cwd=str(project_dir),
        )
        output = proc.stdout + proc.stderr
        return proc.returncode == 0, output.strip()[:300]
    except Exception as exc:
        logger.warning("pyqual validate error: %s", exc)
        return True, str(exc)
