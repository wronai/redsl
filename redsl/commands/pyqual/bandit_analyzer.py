"""Analiza bezpieczeństwa z użyciem bandit."""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class BanditAnalyzer:
    """Uruchamia bandit i zbiera wyniki bezpieczeństwa."""

    def analyze(self, files: list[Path], results: dict[str, Any], config: dict) -> None:
        """Run bandit security linter i zapisz wyniki do results."""
        if not config.get("tools", {}).get("bandit", {}).get("enabled", False):
            return

        try:
            dirs_to_check = set(f.parent for f in files)
            all_issues = []
            file_set = set(str(f) for f in files)

            for dir_path in dirs_to_check:
                result = subprocess.run(
                    ["bandit", "-f", "json", "-r", str(dir_path)],
                    capture_output=True,
                    text=True,
                )
                if result.stdout:
                    bandit_result = json.loads(result.stdout)
                    dir_issues = [
                        i for i in bandit_result.get("results", [])
                        if i.get("filename") in file_set
                    ]
                    all_issues.extend(dir_issues)

            results["issues"]["bandit"] = all_issues
            results["summary"]["security_issues"] = len(all_issues)

        except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning("Failed to run bandit: %s", e)
            results["issues"]["bandit"] = []
