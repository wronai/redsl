"""Analiza typów z użyciem mypy."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class MypyAnalyzer:
    """Uruchamia mypy i zbiera wyniki."""

    def analyze(self, files: list[Path], results: dict[str, Any], config: dict) -> None:
        """Run mypy type checker i zapisz wyniki do results."""
        if not config.get("tools", {}).get("mypy", {}).get("enabled", False):
            return

        try:
            batch_size = 100
            all_issues = []

            for i in range(0, len(files), batch_size):
                batch = files[i:i + batch_size]
                result = subprocess.run(
                    ["mypy", "--show-error-codes", "--no-error-summary"] + [str(f) for f in batch],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                for line in result.stdout.splitlines():
                    issue = self._parse_mypy_line(line)
                    if issue:
                        all_issues.append(issue)

            results["issues"]["mypy"] = all_issues
            results["summary"]["mypy_issues"] = len(all_issues)

        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.warning("Failed to run mypy: %s", e)
            results["issues"]["mypy"] = []

    @staticmethod
    def _parse_mypy_line(line: str) -> dict[str, Any] | None:
        """Parsuj jedną linię wyjścia mypy."""
        if not line.strip():
            return None
        parts = line.split(":", 3)
        if len(parts) >= 4:
            try:
                return {
                    "file": parts[0],
                    "line": int(parts[1]),
                    "type": parts[2].strip(),
                    "message": parts[3].strip(),
                }
            except ValueError:
                pass
        return None
