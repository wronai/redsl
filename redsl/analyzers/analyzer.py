"""
Główny analizator kodu.

Łączy dane z toon.yaml, linterów i własnej analizy w zunifikowane metryki.
"""

from __future__ import annotations

import ast
import logging
import re
from pathlib import Path
from typing import Any

from .metrics import AnalysisResult, CodeMetrics
from .parsers import ToonParser
from .quality_visitor import CodeQualityVisitor
from .utils import _load_gitignore_patterns, _should_ignore_file

logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """
    Główny analizator kodu.
    Łączy dane z toon.yaml, linterów i własnej analizy w zunifikowane metryki.
    """

    def __init__(self) -> None:
        self.parser = ToonParser()

    def analyze_project(self, project_dir: Path) -> AnalysisResult:
        """Przeprowadź pełną analizę projektu."""
        result = AnalysisResult()

        # 1. Szukaj plików toon.yaml
        toon_files = self._find_toon_files(project_dir)

        # 1b. T004: jeśli brak jakichkolwiek toon — fallback na AST Python
        if not toon_files:
            return self._analyze_python_files(project_dir)

        # 2. Parsuj project_toon
        project_key = self._select_project_key(toon_files)
        if project_key:
            self._process_project_ton(toon_files[project_key], result)

        # 3. Parsuj duplikaty
        self._process_duplicates(toon_files, result)

        # 4. Parsuj walidację
        self._process_validation(toon_files, result)

        # 5. Rozwiąż ścieżki i usuń ghost-metrics
        self._resolve_and_filter_metrics(result.metrics, project_dir)

        # 6. Dodaj quality metrics
        self._add_quality_metrics(result, project_dir)

        # 7. Oblicz finalne statystyki
        self._calculate_statistics(result)

        logger.info(
            "Analysis complete: %d files, %d lines, avg CC=%.1f, %d critical",
            result.total_files,
            result.total_lines,
            result.avg_cc,
            result.critical_count,
        )

        return result

    def _select_project_key(self, toon_files: dict[str, Path]) -> str | None:
        """T005: wybierz klucz projektu — 'project' lub 'analysis' jako fallback."""
        if "project" in toon_files:
            return "project"
        if "analysis" in toon_files:
            return "analysis"
        return None

    def _process_project_ton(self, toon_file: Path, result: AnalysisResult) -> None:
        """Parsuj plik project_toon i zaktualizuj result."""
        raw_content = toon_file.read_text(encoding="utf-8")

        # T006: wykryj format functions.toon
        if raw_content.lstrip().startswith("project:") and "function_details:" in raw_content:
            project_data = self.parser.parse_functions_toon(raw_content)
        else:
            project_data = self.parser.parse_project_toon(raw_content)

        health = project_data.get("health", {})
        result.project_name = health.get("name", str(toon_file.parent))
        result.avg_cc = health.get("CC\u0304", 0.0)
        result.critical_count = health.get("critical", 0)
        result.alerts = project_data.get("alerts", [])

        # T017: dane z nagłówka jako fallback
        result._header_files = health.get("total_files", 0)  # type: ignore[attr-defined]
        result._header_lines = health.get("total_lines", 0)  # type: ignore[attr-defined]

        # Konwertuj moduły na metryki
        self._convert_modules_to_metrics(project_data.get("modules", []), result)

        # Przetwórz hotspoty
        self._process_hotspots(project_data.get("hotspots", []), result)

        # Przetwórz alerty
        self._process_alerts(project_data.get("alerts", []), result)

    def _convert_modules_to_metrics(
        self, modules: list[dict], result: AnalysisResult
    ) -> None:
        """Konwertuj moduły z toon na CodeMetrics."""
        for mod in modules:
            metrics = CodeMetrics(
                file_path=mod["path"],
                module_lines=mod["lines"],
                function_count=mod["functions"],
                class_count=mod["classes"],
                cyclomatic_complexity=mod["max_cc"],
            )
            result.metrics.append(metrics)

    def _process_hotspots(self, hotspots: list[dict], result: AnalysisResult) -> None:
        """Dodaj fan-out z hotspotów do istniejących metryk."""
        for hotspot in hotspots:
            for m in result.metrics:
                if hotspot["name"] in (m.function_name or "") or hotspot["name"] in m.file_path:
                    m.fan_out = max(m.fan_out, hotspot["fan_out"])

    def _process_alerts(self, alerts: list[dict], result: AnalysisResult) -> None:
        """Przetwórz alerty i zaktualizuj lub dodaj metryki."""
        # T009: Indeks metryk po nazwie funkcji — deduplikacja
        func_index: dict[str, CodeMetrics] = {
            m.function_name: m for m in result.metrics if m.function_name
        }

        for alert in alerts:
            func_name = alert.get("name", "")
            alert_type = alert.get("type", "")
            value = alert.get("value", 0)

            existing = func_index.get(func_name)
            if existing is None:
                existing = CodeMetrics(
                    file_path="detected_from_alert",
                    function_name=func_name,
                )
                result.metrics.append(existing)
                func_index[func_name] = existing

            if "cc" in alert_type:
                existing.cyclomatic_complexity = max(existing.cyclomatic_complexity, value)
            elif "fan" in alert_type:
                existing.fan_out = max(existing.fan_out, value)

    def _process_duplicates(
        self, toon_files: dict[str, Path], result: AnalysisResult
    ) -> None:
        """Parsuj duplikaty i dodaj metryki."""
        if "duplication" not in toon_files:
            return

        dups = self.parser.parse_duplication_toon(
            toon_files["duplication"].read_text(encoding="utf-8")
        )
        result.duplicates = dups

        for dup in dups:
            for f in dup.get("files", []):
                for m in result.metrics:
                    if m.file_path == f["path"]:
                        m.duplicate_lines += dup.get("lines", 0)
                        m.duplicate_similarity = max(
                            m.duplicate_similarity, dup.get("similarity", 0.0)
                        )

    def _process_validation(
        self, toon_files: dict[str, Path], result: AnalysisResult
    ) -> None:
        """Parsuj walidację i dodaj metryki lintera."""
        if "validation" not in toon_files:
            return

        issues = self.parser.parse_validation_toon(
            toon_files["validation"].read_text(encoding="utf-8")
        )
        for issue in issues:
            for m in result.metrics:
                if m.file_path == issue.get("file", ""):
                    if issue.get("severity") == "error":
                        m.linter_errors += 1
                    else:
                        m.linter_warnings += 1

    def _resolve_and_filter_metrics(
        self, metrics: list[CodeMetrics], project_dir: Path
    ) -> None:
        """Rozwiąż ścieżki i usuń ghost-metrics."""
        self.resolve_metrics_paths(metrics, project_dir)

        # Usuń ghost-metrics
        valid_metrics = [
            m
            for m in metrics
            if ".py" in m.file_path or (project_dir / m.file_path).exists()
        ]
        metrics[:] = valid_metrics

    def _calculate_statistics(self, result: AnalysisResult) -> None:
        """Oblicz finalne statystyki projektu."""
        # Oblicz avg_cc z rzeczywistych metryk
        cc_values = [
            m.cyclomatic_complexity for m in result.metrics if m.cyclomatic_complexity > 0
        ]
        if cc_values:
            result.avg_cc = round(sum(cc_values) / len(cc_values), 2)

        # Oblicz totals z metryk
        result.total_files = len(
            {m.file_path for m in result.metrics if not m.function_name}
        )
        result.total_lines = sum(
            m.module_lines for m in result.metrics if not m.function_name
        )

        # T017: użyj danych z nagłówka jako lepszy fallback
        hdr_files = getattr(result, "_header_files", 0)
        hdr_lines = getattr(result, "_header_lines", 0)
        if hdr_files and hdr_files > result.total_files:
            result.total_files = hdr_files
        if hdr_lines and hdr_lines > result.total_lines:
            result.total_lines = hdr_lines


    def analyze_from_toon_content(
        self,
        project_toon: str = "",
        duplication_toon: str = "",
        validation_toon: str = "",
    ) -> AnalysisResult:
        """Analizuj z bezpośredniego contentu toon (bez plików)."""
        result = AnalysisResult()

        if project_toon:
            data = self.parser.parse_project_toon(project_toon)
            result.alerts = data.get("alerts", [])

            for mod in data.get("modules", []):
                result.metrics.append(
                    CodeMetrics(
                        file_path=mod["path"],
                        module_lines=mod["lines"],
                        function_count=mod["functions"],
                        class_count=mod["classes"],
                        cyclomatic_complexity=mod["max_cc"],
                    )
                )

            # T009: Deduplikacja — nie twórz duplikatu jeśli funkcja już jest w metrykach
            func_index: dict[str, CodeMetrics] = {
                m.function_name: m for m in result.metrics if m.function_name
            }
            for alert in data.get("alerts", []):
                func_name = alert.get("name")
                alert_type = alert.get("type", "")
                value = alert.get("value", 0)
                existing = func_index.get(func_name)
                if existing is None:
                    existing = CodeMetrics(
                        file_path="detected_from_alert",
                        function_name=func_name,
                        cyclomatic_complexity=value if "cc" in alert_type else 0,
                        fan_out=value if "fan" in alert_type else 0,
                    )
                    result.metrics.append(existing)
                    func_index[func_name] = existing
                else:
                    if "cc" in alert_type:
                        existing.cyclomatic_complexity = max(existing.cyclomatic_complexity, value)
                    elif "fan" in alert_type:
                        existing.fan_out = max(existing.fan_out, value)

        if duplication_toon:
            result.duplicates = self.parser.parse_duplication_toon(duplication_toon)

        result.total_files = len(set(m.file_path for m in result.metrics))
        result.total_lines = sum(m.module_lines for m in result.metrics)

        return result

    def _find_toon_files(self, project_dir: Path) -> dict[str, Path]:
        """Znajdź pliki toon w projekcie — obsługuje wiele wzorców i formatów."""
        files: dict[str, Path] = {}
        for pattern, key in [
            ("*project*toon*", "project"),
            ("*analysis*toon*", "analysis"),
            ("*evolution*toon*", "evolution"),
            ("*duplication*toon*", "duplication"),
            ("*validation*toon*", "validation"),
            ("*map*toon*", "map"),
        ]:
            found = list(project_dir.glob(pattern))
            if found:
                files[key] = found[0]

        # Tfix1: Fallback — dowolny *.toon jako "project" jeśli żaden wzorzec nie pasuje
        if "project" not in files and "analysis" not in files:
            toon_candidates = [
                f
                for f in project_dir.glob("*.toon")
                if "duplication" not in f.name
                and "validation" not in f.name
                and "evolution" not in f.name
                and "map" not in f.name
            ]
            if toon_candidates:
                files["project"] = toon_candidates[0]

        logger.info("Found toon files: %s", list(files.keys()))
        return files

    def _analyze_python_files(self, project_dir: Path) -> AnalysisResult:
        """T004: Fallback — analiza .py przez stdlib ast gdy brak toon plików."""
        result = AnalysisResult()
        result.project_name = project_dir.name

        # Load gitignore patterns once
        gitignore_patterns = _load_gitignore_patterns(project_dir)

        py_files = [
            f
            for f in project_dir.rglob("*.py")
            if not _should_ignore_file(f, project_dir, gitignore_patterns)
        ]

        for py_file in py_files:
            try:
                source = py_file.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(source, filename=str(py_file))
            except SyntaxError:
                continue

            lines = len(source.splitlines())
            rel_path = str(py_file.relative_to(project_dir))

            # Run quality visitor to detect additional issues
            quality_visitor = CodeQualityVisitor()
            quality_visitor.visit(tree)
            quality_metrics = quality_visitor.get_metrics()

            # Debug: Log quality metrics for first few files
            if len(result.metrics) < 3:
                logger.info("Quality metrics for %s: %s", rel_path, quality_metrics)

            func_count = 0
            class_count = 0
            max_cc = 0
            high_cc_funcs: list[str] = []

            # Iteruj tylko po top-level i class-level funkcjach
            top_nodes = list(ast.iter_child_nodes(tree))
            for top in top_nodes:
                if isinstance(top, ast.ClassDef):
                    class_count += 1
                    for item in ast.iter_child_nodes(top):
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            func_count += 1
                            cc = self._ast_cyclomatic_complexity(item)
                            max_cc = max(max_cc, cc)
                            if cc > 10:
                                high_cc_funcs.append(item.name)
                                result.metrics.append(
                                    CodeMetrics(
                                        file_path=rel_path,
                                        function_name=item.name,
                                        module_lines=lines,
                                        cyclomatic_complexity=cc,
                                    )
                                )
                                result.alerts.append({
                                    "type": "cc_exceeded",
                                    "name": item.name,
                                    "severity": 3 if cc > 20 else 2,
                                    "value": cc,
                                    "limit": 10,
                                })
                elif isinstance(top, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_count += 1
                    cc = self._ast_cyclomatic_complexity(top)
                    max_cc = max(max_cc, cc)
                    if cc > 10:
                        high_cc_funcs.append(top.name)
                        result.metrics.append(
                            CodeMetrics(
                                file_path=rel_path,
                                function_name=top.name,
                                module_lines=lines,
                                cyclomatic_complexity=cc,
                            )
                        )
                        result.alerts.append({
                            "type": "cc_exceeded",
                            "name": top.name,
                            "severity": 3 if cc > 20 else 2,
                            "value": cc,
                            "limit": 10,
                        })

            # Metryka modułu (bez duplikowania jeśli już są per-funkcja)
            module_metrics = CodeMetrics(
                file_path=rel_path,
                module_lines=lines,
                function_count=func_count,
                class_count=class_count,
                cyclomatic_complexity=max_cc,
                unused_imports=quality_metrics["unused_imports"],
                magic_numbers=quality_metrics["magic_numbers"],
                module_execution_block=quality_metrics["module_execution_block"],
                missing_return_types=quality_metrics["missing_return_types"],
            )
            # Store detailed lists for direct refactoring
            module_metrics._quality_details = {
                "unused_import_list": quality_metrics["unused_import_list"],
                "magic_number_list": quality_metrics["magic_number_list"],
                "functions_missing_return": quality_metrics["functions_missing_return"],
                "module_statements": quality_metrics["module_statements"],
            }
            result.metrics.append(module_metrics)

        result.total_files = len(py_files)
        result.total_lines = sum(m.module_lines for m in result.metrics if not m.function_name)
        result.critical_count = sum(1 for a in result.alerts if a.get("severity", 0) >= 2)

        cc_vals = [m.cyclomatic_complexity for m in result.metrics if m.cyclomatic_complexity > 0]
        result.avg_cc = round(sum(cc_vals) / len(cc_vals), 2) if cc_vals else 0.0

        logger.info(
            "AST fallback: %d py files, %d lines, %d critical CC",
            result.total_files,
            result.total_lines,
            result.critical_count,
        )
        return result

    @staticmethod
    def _ast_cyclomatic_complexity(node: ast.AST) -> int:
        """Oblicz CC dla funkcji — nie wchodzi w zagniedzone definicje funkcji/klas."""
        branch_types = (
            ast.If,
            ast.For,
            ast.While,
            ast.ExceptHandler,
            ast.With,
            ast.Assert,
            ast.comprehension,
        )
        count = 1

        def _walk(n: ast.AST) -> None:
            nonlocal count
            for child in ast.iter_child_nodes(n):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    continue  # nie licz złożoności zagnieżdżonych definicji
                if isinstance(child, branch_types):
                    count += 1
                elif isinstance(child, ast.BoolOp):
                    count += len(child.values) - 1
                _walk(child)

        _walk(node)
        return count

    def resolve_file_path(self, project_dir: Path, func_name: str) -> str | None:
        """Znajdź plik .py zawierający definicję funkcji/metody o podanej nazwie."""
        short_name = func_name.split(".")[-1]  # handle Class.method
        pattern = re.compile(
            rf"^\s*(?:async\s+)?def\s+{re.escape(short_name)}\s*\(",
            re.MULTILINE,
        )
        # Load gitignore patterns once
        gitignore_patterns = _load_gitignore_patterns(project_dir)
        for py_file in project_dir.rglob("*.py"):
            if _should_ignore_file(py_file, project_dir, gitignore_patterns):
                continue
            try:
                text = py_file.read_text(encoding="utf-8", errors="ignore")
                if pattern.search(text):
                    return str(py_file.relative_to(project_dir))
            except OSError:
                continue
        return None

    @staticmethod
    def extract_function_source(abs_path: Path, func_name: str) -> str:
        """Wytnij źródło jednej funkcji/metody z pliku używając AST."""
        short_name = func_name.split(".")[-1]
        try:
            source = abs_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source)
            lines = source.splitlines(keepends=True)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name == short_name:
                        start = node.lineno - 1
                        end = node.end_lineno if hasattr(node, "end_lineno") else len(lines)
                        return "".join(lines[start:end])
        except (OSError, SyntaxError):
            pass
        return ""

    def find_worst_function(self, abs_path: Path) -> tuple[str, int] | None:
        """Znajdź funkcję z najwyższym CC w pliku. Zwraca (name, cc) lub None."""
        try:
            source = abs_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source)
            worst: tuple[str, int] | None = None
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    cc = self._ast_cyclomatic_complexity(node)
                    if worst is None or cc > worst[1]:
                        worst = (node.name, cc)
            return worst
        except (OSError, SyntaxError):
            return None

    def resolve_metrics_paths(self, metrics: list[CodeMetrics], project_dir: Path) -> None:
        """Napraw ścieżki 'detected_from_alert' i krótkie nazwy modułów z LAYERS.

        Przeszukuje project_dir aby znaleźć prawdziwe ścieżki dla funkcji z alertów.
        Modyfikuje metryki in-place.
        """
        _cache: dict[str, str | None] = {}
        for m in metrics:
            if m.file_path in ("detected_from_alert", "unknown") or (
                m.function_name and not Path(project_dir / m.file_path).exists()
            ):
                func_name = m.function_name or m.file_path
                if func_name not in _cache:
                    _cache[func_name] = self.resolve_file_path(project_dir, func_name)
                resolved = _cache[func_name]
                if resolved:
                    m.file_path = resolved
                    logger.debug("Resolved %r → %s", func_name, resolved)

    def _add_quality_metrics(self, result: AnalysisResult, project_dir: Path) -> None:
        """Add quality metrics to existing analysis results."""
        # Create a mapping from file path to metrics
        metrics_by_file: dict[str, CodeMetrics] = {}
        for m in result.metrics:
            if not m.function_name:  # Only module-level metrics
                metrics_by_file[m.file_path] = m

        # Load gitignore patterns once
        gitignore_patterns = _load_gitignore_patterns(project_dir)

        # Analyze Python files for quality issues
        py_files = [
            f
            for f in project_dir.rglob("*.py")
            if not _should_ignore_file(f, project_dir, gitignore_patterns)
        ]

        for py_file in py_files:
            try:
                source = py_file.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(source, filename=str(py_file))
            except SyntaxError:
                continue

            rel_path = str(py_file.relative_to(project_dir))

            # Run quality visitor
            quality_visitor = CodeQualityVisitor()
            quality_visitor.visit(tree)
            quality_metrics = quality_visitor.get_metrics()

            # Update existing metrics or create new ones
            if rel_path in metrics_by_file:
                m = metrics_by_file[rel_path]
                m.unused_imports = quality_metrics["unused_imports"]
                m.magic_numbers = quality_metrics["magic_numbers"]
                m.module_execution_block = quality_metrics["module_execution_block"]
                m.missing_return_types = quality_metrics["missing_return_types"]

                # Store detailed lists for direct refactoring
                m._quality_details = {
                    "unused_import_list": quality_metrics["unused_import_list"],
                    "magic_number_list": quality_metrics["magic_number_list"],
                    "functions_missing_return": quality_metrics["functions_missing_return"],
                    "module_statements": quality_metrics["module_statements"],
                }
