"""Parser dla pliku duplication_toon — grupy zduplikowanego kodu."""

from __future__ import annotations

import re
from typing import Any


class DuplicationParser:
    """Parser sekcji duplication_toon."""

    def parse_duplication_toon(self, content: str) -> list[dict[str, Any]]:
        """Parsuj duplication_toon — obsługuje formaty legacy i code2llm [hash] ! STRU."""
        duplicates = []
        current: dict[str, Any] | None = None

        for line in content.splitlines():
            stripped = line.strip()

            # T010: Nowa grupa duplikatów — oba formaty:
            # Legacy:     [STRU name L=25 N=3 saved=50 sim=1.00
            # code2llm:  [1899ff8e67d31c77] ! STRU  setup_logging  L=25 N=3 saved=50 sim=1.00
            if re.search(r"(STRU|EXAC)", stripped) and stripped.startswith("["):
                if current:
                    duplicates.append(current)
                match = re.search(
                    r"(STRU|EXAC)\s+([\w./-]+)\s+L=(\d+)\s+N=(\d+)\s+saved=(\d+)\s+sim=([\d.]+)",
                    stripped,
                )
                if match:
                    current = {
                        "type": match.group(1),
                        "name": match.group(2),
                        "lines": int(match.group(3)),
                        "occurrences": int(match.group(4)),
                        "saved_lines": int(match.group(5)),
                        "similarity": float(match.group(6)),
                        "files": [],
                    }

            elif current and stripped and ":" in stripped:
                file_match = re.match(
                    r"([\w/._-]+(?:\.py|\.[a-z]+)):(\d+)(?:-(\d+))?", stripped
                )
                if file_match:
                    current["files"].append({
                        "path": file_match.group(1),
                        "start": int(file_match.group(2)),
                        "end": int(file_match.group(3))
                        if file_match.group(3)
                        else int(file_match.group(2)),
                    })

        if current:
            duplicates.append(current)

        return duplicates
