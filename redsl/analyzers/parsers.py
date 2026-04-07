"""
Parser plików toon — parser plików .toon.yaml + metryki.

Konwertuje dane z:
- project_toon.yaml  (health, alerts, hotspots)
- analysis_toon.yaml (layers, CC, pipelines)
- evolution_toon.yaml (recommendations, risks)
- duplication_toon.yaml (duplicate blocks)
- validation_toon.yaml (linter errors, warnings)

na zunifikowane konteksty DSL do ewaluacji przez DSLEngine.
"""

from __future__ import annotations

import re
from typing import Any

from .utils import _try_number


class ToonParser:
    """Parser plików toon — obsługuje wiele formatów wyjścia code2llm."""

    def parse_project_toon(self, content: str) -> dict[str, Any]:
        """Parsuj plik toon — obsługuje formaty: legacy, code2llm v2 (HEALTH[N]/LAYERS), M[N] list."""
        result: dict[str, Any] = {
            "health": {},
            "alerts": [],
            "hotspots": [],
            "refactors": [],
            "modules": [],
        }

        # T017: Parsuj header line
        self._parse_header_lines(content, result)

        # Parsuj sekcje
        section = ""
        module_list_mode = False

        for line in content.splitlines():
            stripped = line.strip()

            # Wykryj zmianę sekcji
            new_section, new_mode = self._detect_section_change(stripped)
            if new_section is not None:
                section = new_section
                module_list_mode = new_mode
                continue

            # Parsuj zawartość sekcji
            self._parse_section_line(line, stripped, section, module_list_mode, result)

        return result

    def _parse_header_lines(self, content: str, result: dict[str, Any]) -> None:
        """T017: Parsuj nagłówki z pierwszych 3 linii."""
        for line in content.splitlines()[:3]:
            if line.startswith("#"):
                hdr = self._parse_header_line(line)
                if hdr:
                    result["health"].update(hdr)

    def _detect_section_change(self, stripped: str) -> tuple[str | None, bool]:
        """Wykryj zmianę sekcji na podstawie linii."""
        # HEALTH sekcja
        if re.match(r"HEALTH(\[\d+\])?:", stripped):
            return "health", False

        # ALERTS sekcja
        if re.match(r"ALERTS", stripped):
            return "alerts", False

        # HOTSPOTS sekcja
        if stripped.startswith("HOTSPOTS"):
            return "hotspots", False

        # REFACTOR sekcja
        if stripped.startswith("REFACTOR"):
            return "refactors", False

        # MODULES sekcja (legacy format)
        if re.match(r"MODULES", stripped):
            return "modules", False

        # EVOLUTION sekcja
        if stripped.startswith("EVOLUTION"):
            return "evolution", False

        # LAYERS sekcja (code2llm v2)
        if stripped.startswith("LAYERS:"):
            return "layers", False

        # M[N]: format - T003
        if re.match(r"M\[\d+\]:", stripped):
            return "modules", True

        return None, False

    def _parse_section_line(
        self,
        line: str,
        stripped: str,
        section: str,
        module_list_mode: bool,
        result: dict[str, Any],
    ) -> None:
        """Parsuj pojedynczą linię w kontekście aktualnej sekcji."""
        if not section:
            return

        # --- HEALTH sekcja ---
        if section == "health":
            self._parse_health_line(stripped, result)

        # --- ALERTS sekcja ---
        elif section == "alerts":
            self._parse_alerts_line(stripped, result)

        # --- HOTSPOTS sekcja ---
        elif section == "hotspots":
            self._parse_hotspots_line(stripped, result)

        # --- MODULES sekcja ---
        elif section == "modules":
            self._parse_modules_line(line, stripped, module_list_mode, result)

        # --- LAYERS sekcja ---
        elif section == "layers":
            self._parse_layers_section_line(line, stripped, result)

        # --- REFACTORS sekcja ---
        elif section == "refactors":
            self._parse_refactors_line(stripped, result)

    def _parse_health_line(self, stripped: str, result: dict[str, Any]) -> None:
        """Parsuj linię w sekcji HEALTH."""
        # Legacy HEALTH: key=val
        if "=" in stripped and not stripped.startswith("🟡"):
            parts = stripped.split()
            for part in parts:
                if "=" in part:
                    key, val = part.split("=", 1)
                    result["health"][key.strip()] = _try_number(val.strip())

        # T001: code2llm v2 HEALTH[N]: 🟡 CC func CC=41 (limit:10)
        elif "🟡" in stripped or "🔴" in stripped or "⚠" in stripped:
            alert = self._parse_emoji_alert_line(stripped)
            if alert:
                result["alerts"].append(alert)

    def _parse_alerts_line(self, stripped: str, result: dict[str, Any]) -> None:
        """Parsuj linię w sekcji ALERTS."""
        if stripped.startswith("!"):
            alert = self._parse_alert_line(stripped)
            if alert:
                result["alerts"].append(alert)

    def _parse_hotspots_line(self, stripped: str, result: dict[str, Any]) -> None:
        """Parsuj linię w sekcji HOTSPOTS."""
        if stripped.startswith("★"):
            hotspot = self._parse_hotspot_line(stripped)
            if hotspot:
                result["hotspots"].append(hotspot)

    def _parse_modules_line(
        self,
        line: str,
        stripped: str,
        module_list_mode: bool,
        result: dict[str, Any],
    ) -> None:
        """Parsuj linię w sekcji MODULES."""
        # Legacy MODULES: M[file] 450L C:3 F:12 CC↑35
        if not module_list_mode and stripped.startswith("M["):
            module = self._parse_module_line(stripped)
            if module:
                result["modules"].append(module)

        # T003: M[N]: file,line_count list
        elif module_list_mode and "," in stripped and stripped:
            module = self._parse_module_list_line(stripped)
            if module:
                result["modules"].append(module)

    def _parse_layers_section_line(
        self, line: str, stripped: str, result: dict[str, Any]
    ) -> None:
        """Parsuj linię w sekcji LAYERS."""
        if "│" in line or stripped.startswith("│"):
            module = self._parse_layers_line(stripped)
            if module:
                result["modules"].append(module)

    def _parse_refactors_line(self, stripped: str, result: dict[str, Any]) -> None:
        """Parsuj linię w sekcji REFACTOR."""
        if stripped.startswith("["):
            refactor = self._parse_refactor_line(stripped)
            if refactor:
                result["refactors"].append(refactor)

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
                # Linia z plikiem: path/file.py:start-end lub path/file.py:line
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

    def parse_validation_toon(self, content: str) -> list[dict[str, Any]]:
        """Parsuj validation_toon.yaml — błędy walidacji."""
        issues = []
        current_file = ""

        for line in content.splitlines():
            stripped = line.strip()

            # Plik z wynikiem
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

    # -- Parsery pomocnicze --

    def _parse_header_line(self, line: str) -> dict[str, Any] | None:
        """T017: Parsuj nagłówek: # project | 113f 20532L | python:109 | date"""
        cleaned = line.lstrip("# ").strip()
        parts = [p.strip() for p in cleaned.split("|")]
        if not parts:
            return None
        name_candidate = parts[0]
        result: dict[str, Any] = {}
        if name_candidate and "=" not in name_candidate and not name_candidate.startswith("CC"):
            result["name"] = name_candidate
        for part in parts[1:]:
            files_match = re.search(r"(\d+)f", part)
            lines_match = re.search(r"(\d+)L", part)
            cc_match = re.search(r"CC[=̄](\d+\.?\d*)", part)
            critical_match = re.search(r"critical:(\d+)", part)
            if files_match:
                result["total_files"] = int(files_match.group(1))
            if lines_match:
                result["total_lines"] = int(lines_match.group(1))
            if cc_match:
                result["CC\u0304"] = float(cc_match.group(1))
            if critical_match:
                result["critical"] = int(critical_match.group(1))
        return result if result else None

    def _parse_emoji_alert_line(self, line: str) -> dict[str, Any] | None:
        """T001: Parsuj linie code2llm v2: 🟡 CC func_name CC=41 (limit:10)"""
        # Usuń emoji i leading whitespace
        cleaned = re.sub(r"[🟡🔴⚠️\s]+", " ", line).strip()
        # Wykryj typ alertu i nazwę funkcji
        # Format: CC func_name CC=41 (limit:10)
        #      lub: FAN func_name FAN=26 (limit:10)
        match = re.match(
            r"(CC|FAN|DUP|LINES|CYCLE)\s+([\w.]+)\s+(?:CC|FAN|DUP|LINES|CYCLE)?[=\s]+(\d+)(?:\s*\(limit:(\d+)\))?",
            cleaned,
        )
        if not match:
            # Fallback: szukaj CC= pattern
            val_match = re.search(r"CC=(\d+)", line)
            name_match = re.search(r"CC\s+([\w.]+)", line.replace("🟡", "").replace("🔴", ""))
            if val_match and name_match:
                return {
                    "type": "cc_exceeded",
                    "name": name_match.group(1).strip(),
                    "severity": 2,
                    "value": int(val_match.group(1)),
                    "limit": 10,
                }
            return None
        alert_type_map = {"CC": "cc_exceeded", "FAN": "high_fan_out", "DUP": "duplicate_block"}
        raw_type = match.group(1)
        return {
            "type": alert_type_map.get(raw_type, raw_type.lower()),
            "name": match.group(2),
            "severity": 2,
            "value": int(match.group(3)),
            "limit": int(match.group(4)) if match.group(4) else 10,
        }

    def _parse_alert_line(self, line: str) -> dict[str, Any] | None:
        severity = line.count("!")
        cleaned = line.lstrip("! ").strip()
        parts = cleaned.split(None, 2)
        if len(parts) >= 2:
            alert_type = parts[0]
            name = parts[1]
            rest = parts[2] if len(parts) > 2 else ""
            value_match = re.search(r"=\s*(\d+)", rest)
            limit_match = re.search(r"limit:(\d+)", rest)
            return {
                "type": alert_type,
                "name": name,
                "severity": severity,
                "value": int(value_match.group(1)) if value_match else 0,
                "limit": int(limit_match.group(1)) if limit_match else 0,
            }
        return None

    def _parse_hotspot_line(self, line: str) -> dict[str, Any] | None:
        cleaned = line.lstrip("★ ").strip()
        match = re.match(r"(\w+)\s+fan=(\d+)", cleaned)
        if match:
            return {"name": match.group(1), "fan_out": int(match.group(2))}
        return None

    def _parse_module_line(self, line: str) -> dict[str, Any] | None:
        """Legacy format: M[file] 450L C:3 F:12 CC↑35"""
        match = re.match(r"M\[(.+?)\]\s+(\d+)L\s+C:(\d+)\s+F:(\d+)\s+CC[↑=](\d+)", line)
        if match:
            return {
                "path": match.group(1),
                "lines": int(match.group(2)),
                "classes": int(match.group(3)),
                "functions": int(match.group(4)),
                "max_cc": int(match.group(5)),
            }
        return None

    def _parse_module_list_line(self, line: str) -> dict[str, Any] | None:
        """T003: Format M[N] list: file_path,line_count"""
        parts = line.split(",")
        if len(parts) >= 2 and parts[-1].strip().isdigit():
            return {
                "path": parts[0].strip(),
                "lines": int(parts[-1].strip()),
                "classes": 0,
                "functions": 0,
                "max_cc": 0,
            }
        return None

    def _parse_layers_line(self, line: str) -> dict[str, Any] | None:
        """T002: Format LAYERS: │ !! module_name 721L 1C CC=5"""
        # Usuń prefix │ i symbole alertów
        cleaned = re.sub(r"[│├└─!\s]+", " ", line).strip()
        # Format: name 721L 1C Nm CC=5
        match = re.match(r"([\w./]+)\s+(\d+)L\s+(\d+)C\s+\S+\s+CC[=↑](\d+)", cleaned)
        if match:
            return {
                "path": match.group(1),
                "lines": int(match.group(2)),
                "classes": int(match.group(3)),
                "functions": 0,
                "max_cc": int(match.group(4)),
            }
        return None

    def _parse_refactor_line(self, line: str) -> dict[str, str] | None:
        match = re.match(r"\[(\d+)\]\s+(.+)", line)
        if match:
            return {"index": match.group(1), "description": match.group(2).strip()}
        return None

    def parse_functions_toon(self, content: str) -> dict[str, Any]:
        """T006: Parsuj project.functions.toon — format YAML per-funkcja z CC.

        Format:
            project: name
            modules[N]{path,lang,items}:
              file.py,python,14
            function_details:
              file.py:
                functions[N]{name,kind,sig,loc,async,lines,cc,does}:
                  func,method,(),21-35,false,15,7,description
        """
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

            if section == "modules" and "," in stripped:
                parts = stripped.split(",")
                if len(parts) >= 2:
                    result["modules"].append({
                        "path": parts[0].strip(),
                        "lines": 0,
                        "classes": 0,
                        "functions": int(parts[2]) if len(parts) > 2 and parts[2].strip().isdigit() else 0,
                        "max_cc": 0,
                    })

            elif section == "function_details":
                # Linia pliku: "  file.py:"
                file_match = re.match(r"^\s{2}([\w./]+\.\w+):\s*$", line)
                if file_match:
                    current_file = file_match.group(1)
                    fields_order = []
                    continue

                # Nagłówek kolumn: "functions[N]{name,kind,sig,loc,async,lines,cc,does}:"
                header_match = re.match(r"functions\[\d+\]\{(.+)\}:", stripped)
                if header_match:
                    fields_order = [f.strip() for f in header_match.group(1).split(",")]
                    continue

                # Linia funkcji — CSV wg fields_order
                if current_file and fields_order and "," in stripped and not stripped.endswith(":"):
                    func = self._parse_function_csv_line(stripped, fields_order, current_file)
                    if func:
                        result["functions"].append(func)
                        # Aktualizuj max_cc w module
                        for mod in result["modules"]:
                            if mod["path"] == current_file:
                                mod["max_cc"] = max(mod["max_cc"], func.get("cc", 0))
                                break
                        # Generuj alert jeśli CC > 10
                        cc = func.get("cc", 0)
                        if cc > 10:
                            result["alerts"].append({
                                "type": "cc_exceeded",
                                "name": func["name"].split(".")[-1],
                                "severity": 3 if cc > 20 else 2 if cc > 15 else 1,
                                "value": cc,
                                "limit": 10,
                                "file": current_file,
                            })

        return result

    def _parse_function_csv_line(
        self, line: str, fields: list[str], file_path: str
    ) -> dict[str, Any] | None:
        """Parsuj CSV linię funkcji wg pól z nagłówka."""
        # Uwaga: sig może zawierać przecinki w cudzysłowach
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
