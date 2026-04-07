"""
Parser dla pliku functions_toon — per-funkcja dane CC z code2llm.

Format:
    project: name
    modules[N]{path,lang,items}:
      file.py,python,14
    function_details:
      file.py:
        functions[N]{name,kind,sig,loc,async,lines,cc,does}:
          func,method,(),21-35,false,15,7,description
"""

from __future__ import annotations

import re
from typing import Any


class FunctionsParser:
    """Parser sekcji functions_toon — per-funkcja CC."""

    def parse_functions_toon(self, content: str) -> dict[str, Any]:
        """T006: Parsuj project.functions.toon — format YAML per-funkcja z CC."""
        result: dict[str, Any] = {
            "health": {},
            "alerts": [],
            "modules": [],
            "functions": [],
        }

        current_file = ""
        section = ""
        fields_order: list[str] = []

        for line in content.splitlines():
            stripped = line.strip()

            if stripped.startswith("project:"):
                result["health"]["name"] = stripped.split(":", 1)[1].strip()
                continue

            if re.match(r"modules\[\d+\]", stripped):
                section = "modules"
                continue

            if stripped == "function_details:":
                section = "function_details"
                continue

            if section == "modules":
                current_file, fields_order = self._handle_modules_line(
                    stripped, result, current_file, fields_order
                )
            elif section == "function_details":
                current_file, fields_order = self._handle_function_details_line(
                    line, stripped, result, current_file, fields_order
                )

        return result

    def _handle_modules_line(
        self,
        stripped: str,
        result: dict[str, Any],
        current_file: str,
        fields_order: list[str],
    ) -> tuple[str, list[str]]:
        """Parsuj linię w sekcji modules."""
        if "," in stripped:
            parts = stripped.split(",")
            if len(parts) >= 2:
                result["modules"].append({
                    "path": parts[0].strip(),
                    "lines": 0,
                    "classes": 0,
                    "functions": int(parts[2]) if len(parts) > 2 and parts[2].strip().isdigit() else 0,
                    "max_cc": 0,
                })
        return current_file, fields_order

    def _handle_function_details_line(
        self,
        line: str,
        stripped: str,
        result: dict[str, Any],
        current_file: str,
        fields_order: list[str],
    ) -> tuple[str, list[str]]:
        """Parsuj linię w sekcji function_details."""
        file_match = re.match(r"^\s{2}([\w./]+\.\w+):\s*$", line)
        if file_match:
            return file_match.group(1), []

        header_match = re.match(r"functions\[\d+\]\{(.+)\}:", stripped)
        if header_match:
            return current_file, [f.strip() for f in header_match.group(1).split(",")]

        if current_file and fields_order and "," in stripped and not stripped.endswith(":"):
            func = self._parse_function_csv_line(stripped, fields_order, current_file)
            if func:
                result["functions"].append(func)
                self._update_module_max_cc(result, current_file, func)
                self._maybe_add_alert(result, func)

        return current_file, fields_order

    def _update_module_max_cc(
        self, result: dict[str, Any], current_file: str, func: dict[str, Any]
    ) -> None:
        """Aktualizuj max_cc w module po dodaniu funkcji."""
        for mod in result["modules"]:
            if mod["path"] == current_file:
                mod["max_cc"] = max(mod["max_cc"], func.get("cc", 0))
                break

    def _maybe_add_alert(self, result: dict[str, Any], func: dict[str, Any]) -> None:
        """Generuj alert jeśli CC > 10."""
        cc = func.get("cc", 0)
        if cc > 10:
            result["alerts"].append({
                "type": "cc_exceeded",
                "name": func["name"].split(".")[-1],
                "severity": 3 if cc > 20 else 2 if cc > 15 else 1,
                "value": cc,
                "limit": 10,
                "file": func.get("file", ""),
            })

    def _parse_function_csv_line(
        self, line: str, fields: list[str], file_path: str
    ) -> dict[str, Any] | None:
        """Parsuj CSV linię funkcji wg pól z nagłówka."""
        parts = re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', line)
        if len(parts) < len(fields):
            return None
        result: dict[str, Any] = {"file": file_path}
        for i, field_name in enumerate(fields):
            if i >= len(parts):
                break
            val = parts[i].strip().strip('"')
            if field_name in ("lines", "cc"):
                result[field_name] = int(val) if val.isdigit() else 0
            elif field_name == "async":
                result[field_name] = val.lower() == "true"
            else:
                result[field_name] = val
        return result
