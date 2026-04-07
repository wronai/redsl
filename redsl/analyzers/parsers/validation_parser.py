"""Parser dla pliku validation_toon — błędy i ostrzeżenia linterów."""

from __future__ import annotations

from typing import Any


class ValidationParser:
    """Parser sekcji validation_toon."""

    def parse_validation_toon(self, content: str) -> list[dict[str, Any]]:
        """Parsuj validation_toon.yaml — błędy walidacji."""
        issues = []
        current_file = ""

        for line in content.splitlines():
            stripped = line.strip()

            if (
                stripped
                and "," in stripped
                and "/" in stripped
                and not stripped.startswith("issues")
            ):
                parts = stripped.split(",")
                if len(parts) >= 2:
                    current_file = parts[0].strip()

            elif stripped and "," in stripped and current_file:
                parts = stripped.split(",")
                if len(parts) >= 4:
                    issues.append({
                        "file": current_file,
                        "rule": parts[0].strip(),
                        "severity": parts[1].strip(),
                        "message": parts[2].strip(),
                        "line": int(parts[3].strip()) if parts[3].strip().isdigit() else 0,
                    })

        return issues
