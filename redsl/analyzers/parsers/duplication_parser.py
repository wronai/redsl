"""Parser dla pliku duplication_toon — grupy zduplikowanego kodu."""

from __future__ import annotations

import re
from typing import Any


class DuplicationParser:
    """Parser sekcji duplication_toon."""

    _GROUP_RE = re.compile(
        r"(STRU|EXAC)\s+([\w./-]+)\s+L=(\d+)\s+N=(\d+)\s+saved=(\d+)\s+sim=([\d.]+)"
    )
    _FILE_RE = re.compile(r"([\w/._-]+(?:\.py|\.[a-z]+)):(\d+)(?:-(\d+))?")

    def _is_group_header(self, line: str) -> bool:
        """Check if line is a new duplication group header."""
        return line.startswith("[") and ("STRU" in line or "EXAC" in line)

    def _parse_group_header(self, line: str) -> dict[str, Any] | None:
        """Parse group header line into dict or None if no match."""
        match = self._GROUP_RE.search(line)
        if not match:
            return None
        return {
            "type": match.group(1),
            "name": match.group(2),
            "lines": int(match.group(3)),
            "occurrences": int(match.group(4)),
            "saved_lines": int(match.group(5)),
            "similarity": float(match.group(6)),
            "files": [],
        }

    def _parse_file_entry(self, line: str) -> dict[str, Any] | None:
        """Parse file entry line into dict or None if no match."""
        match = self._FILE_RE.match(line)
        if not match:
            return None
        return {
            "path": match.group(1),
            "start": int(match.group(2)),
            "end": int(match.group(3)) if match.group(3) else int(match.group(2)),
        }

    def _append_current(self, duplicates: list, current: dict | None) -> dict | None:
        """Append current group to list and reset. Returns None."""
        if current:
            duplicates.append(current)
        return None

    def parse_duplication_toon(self, content: str) -> list[dict[str, Any]]:
        """Parsuj duplication_toon — obsługuje formaty legacy i code2llm [hash] ! STRU."""
        duplicates: list[dict[str, Any]] = []
        current: dict[str, Any] | None = None

        for line in content.splitlines():
            stripped = line.strip()
            if not stripped:
                continue

            if self._is_group_header(stripped):
                current = self._append_current(duplicates, current)
                current = self._parse_group_header(stripped)
            elif current:
                file_entry = self._parse_file_entry(stripped)
                if file_entry:
                    current["files"].append(file_entry)

        self._append_current(duplicates, current)
        return duplicates
