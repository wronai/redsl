"""Analiza kodu z użyciem ruff — szybki linter Python."""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class RuffAnalyzer:
    """Uruchamia ruff i zbiera wyniki."""

    def analyze(self, files: list[Path], results: dict[str, Any], config: dict) -> None:
        """Run ruff linter i zapisz wyniki do results."""
        if not config.get("tools", {}).get("ruff", {}).get("enabled", False):
            return

        try:
            batch_size = 100
            all_issues = []

            for i in range(0, len(files), batch_size):
                batch = files[i:i + batch_size]
                result = subprocess.run(
                    ["ruff", "check", "--format=json"] + [str(f) for f in batch],
                    capture_output=True,
                    text=True,
                )
                if result.stdout:
                    all_issues.extend(json.loads(result.stdout))

            results["issues"]["ruff"] = all_issues
            error_count = sum(
                1 for i in all_issues if i.get("fix", {}).get("severity") == "error"
            )
            warning_count = sum(
                1 for i in all_issues if i.get("fix", {}).get("severity") == "warning"
            )
            results["summary"]["ruff_errors"] = error_count
            results["summary"]["ruff_warnings"] = warning_count

        except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning("Failed to run ruff: %s", e)
            results["issues"]["ruff"] = []
