"""
Resolver ścieżek — wyszukiwanie plików i funkcji w projekcie.

Odpowiada za:
- Znajdowanie pliku .py zawierającego definicję funkcji
- Wycinanie kodu źródłowego funkcji przez AST
- Znajdowanie funkcji z najwyższym CC w pliku
- Naprawianie ścieżek 'detected_from_alert' w metrykach
"""

from __future__ import annotations

import ast
import logging
import re
from pathlib import Path

from .metrics import CodeMetrics
from .utils import _load_gitignore_patterns, _should_ignore_file

logger = logging.getLogger(__name__)


class PathResolver:
    """Resolver ścieżek i kodu źródłowego funkcji."""

    def resolve_file_path(self, project_dir: Path, func_name: str) -> str | None:
        """Znajdź plik .py zawierający definicję funkcji/metody o podanej nazwie."""
        short_name = func_name.split(".")[-1]
        pattern = re.compile(
            rf"^\s*(?:async\s+)?def\s+{re.escape(short_name)}\s*\(",
            re.MULTILINE,
        )
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
        from .python_analyzer import ast_cyclomatic_complexity
        try:
            source = abs_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source)
            worst: tuple[str, int] | None = None
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    cc = ast_cyclomatic_complexity(node)
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
