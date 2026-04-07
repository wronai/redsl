"""
Metryki kodu - klasy danych dla analizy kodu.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CodeMetrics:
    """Metryki pojedynczej funkcji/modułu."""

    file_path: str
    function_name: str | None = None
    module_lines: int = 0
    function_count: int = 0
    class_count: int = 0
    cyclomatic_complexity: float = 0.0
    fan_out: int = 0
    nested_depth: int = 0
    duplicate_lines: int = 0
    duplicate_similarity: float = 0.0
    missing_type_hints: int = 0
    is_public_api: bool = False
    linter_errors: int = 0
    linter_warnings: int = 0
    unused_imports: int = 0
    magic_numbers: int = 0
    module_execution_block: int = 0
    missing_return_types: int = 0

    def to_dsl_context(self) -> dict[str, Any]:
        """Konwertuj na kontekst DSL do ewaluacji reguł."""
        # For module-level metrics, we need to get the detailed quality info
        context = {
            "file_path": self.file_path,
            "function_name": self.function_name,
            "module_lines": self.module_lines,
            "function_count": self.function_count,
            "class_count": self.class_count,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "fan_out": self.fan_out,
            "nested_depth": self.nested_depth,
            "duplicate_lines": self.duplicate_lines,
            "duplicate_similarity": self.duplicate_similarity,
            "missing_type_hints": self.missing_type_hints,
            "is_public_api": self.is_public_api,
            "linter_errors": self.linter_errors,
            "linter_warnings": self.linter_warnings,
            "unused_imports": self.unused_imports,
            "magic_numbers": self.magic_numbers,
            "module_execution_block": self.module_execution_block,
            "missing_return_types": self.missing_return_types,
        }

        # Add detailed lists for direct refactoring
        if hasattr(self, "_quality_details"):
            context.update(self._quality_details)

        return context


@dataclass
class AnalysisResult:
    """Wynik analizy projektu."""

    project_name: str = ""
    total_files: int = 0
    total_lines: int = 0
    avg_cc: float = 0.0
    critical_count: int = 0
    metrics: list[CodeMetrics] = field(default_factory=list)
    alerts: list[dict[str, Any]] = field(default_factory=list)
    duplicates: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def to_dsl_contexts(self) -> list[dict[str, Any]]:
        """Konwertuj na listę kontekstów DSL."""
        return [m.to_dsl_context() for m in self.metrics]
