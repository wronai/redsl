"""
Główny analizator kodu — fasada.

Deleguje do wyspecjalizowanych modułów:
- ToonAnalyzer  — parsowanie i przetwarzanie plików toon
- PythonAnalyzer — analiza plików .py przez stdlib ast
- PathResolver   — wyszukiwanie plików i kodu źródłowego funkcji
"""

from __future__ import annotations

from pathlib import Path

from .metrics import AnalysisResult, CodeMetrics
from .python_analyzer import PythonAnalyzer, ast_cyclomatic_complexity
from .resolver import PathResolver
from .toon_analyzer import ToonAnalyzer


class CodeAnalyzer:
    """
    Główny analizator kodu — fasada.

    Deleguje do ToonAnalyzer (toon), PythonAnalyzer (AST) i PathResolver (ścieżki).
    Zachowuje pełne backward-compatible API.
    """

    def __init__(self) -> None:
        self._resolver = PathResolver()
        self._python = PythonAnalyzer()
        self._toon = ToonAnalyzer(self._python, self._resolver)
        self.parser = self._toon.parser

    def analyze_project(self, project_dir: Path) -> AnalysisResult:
        """Przeprowadź pełną analizę projektu."""
        return self._toon.analyze_project(project_dir)

    def analyze_from_toon_content(
        self,
        project_toon: str = "",
        duplication_toon: str = "",
        validation_toon: str = "",
    ) -> AnalysisResult:
        """Analizuj z bezpośredniego contentu toon (bez plików)."""
        return self._toon.analyze_from_toon_content(
            project_toon=project_toon,
            duplication_toon=duplication_toon,
            validation_toon=validation_toon,
        )

    def resolve_file_path(self, project_dir: Path, func_name: str) -> str | None:
        """Znajdź plik .py zawierający definicję funkcji/metody o podanej nazwie."""
        return self._resolver.resolve_file_path(project_dir, func_name)

    @staticmethod
    def extract_function_source(abs_path: Path, func_name: str) -> str:
        """Wytnij źródło jednej funkcji/metody z pliku używając AST."""
        return PathResolver.extract_function_source(abs_path, func_name)

    def find_worst_function(self, abs_path: Path) -> tuple[str, int] | None:
        """Znajdź funkcję z najwyższym CC w pliku. Zwraca (name, cc) lub None."""
        return self._resolver.find_worst_function(abs_path)

    def resolve_metrics_paths(self, metrics: list[CodeMetrics], project_dir: Path) -> None:
        """Napraw ścieżki 'detected_from_alert' i krótkie nazwy modułów z LAYERS."""
        return self._resolver.resolve_metrics_paths(metrics, project_dir)

    @staticmethod
    def _ast_cyclomatic_complexity(node: object) -> int:
        """Backward-compat alias — deleguje do ast_cyclomatic_complexity z python_analyzer."""
        return ast_cyclomatic_complexity(node)  # type: ignore[arg-type]
