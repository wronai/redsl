"""Analiza AST — wykrywanie nieużywanych importów, magic numbers, brakujących docstringów."""

from __future__ import annotations

import ast
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AstAnalyzer:
    """Analizuje pliki Python przez AST w poszukiwaniu typowych problemów jakości."""

    def analyze(self, files: list[Path], results: dict[str, Any], config: dict) -> None:
        """Przeanalizuj pliki AST i zapisz wyniki do results."""
        unused_imports: list[dict] = []
        magic_numbers: list[dict] = []
        print_statements: list[dict] = []
        missing_docstrings: list[dict] = []

        for file_path in files:
            try:
                content = file_path.read_text(encoding="utf-8")
                tree = ast.parse(content, filename=str(file_path))
                self._analyze_file(tree, file_path, unused_imports, magic_numbers,
                                   print_statements, missing_docstrings)
            except Exception as e:
                logger.warning("Failed to analyze %s: %s", file_path, e)

        results["issues"]["unused_imports"] = unused_imports
        results["issues"]["magic_numbers"] = magic_numbers
        results["issues"]["print_statements"] = print_statements
        results["issues"]["missing_docstrings"] = missing_docstrings
        results["summary"]["unused_imports"] = len(unused_imports)
        results["summary"]["magic_numbers"] = len(magic_numbers)
        results["summary"]["print_statements"] = len(print_statements)
        results["summary"]["missing_docstrings"] = len(missing_docstrings)

    def _analyze_file(
        self,
        tree: ast.AST,
        file_path: Path,
        unused_imports: list,
        magic_numbers: list,
        print_statements: list,
        missing_docstrings: list,
    ) -> None:
        """Przeanalizuj jeden plik AST."""
        from ...analyzers.quality_visitor import CodeQualityVisitor

        visitor = CodeQualityVisitor()
        visitor.visit(tree)

        for imp_name in visitor.get_unused_imports():
            unused_imports.append({
                "file": str(file_path),
                "line": visitor.imports[imp_name].lineno,
                "name": imp_name,
                "message": f"Unused import: {imp_name}",
            })

        for lineno, value in visitor.magic_numbers:
            magic_numbers.append({
                "file": str(file_path),
                "line": lineno,
                "value": value,
                "message": f"Magic number: {value}",
            })

        for lineno, stmt_type in visitor.module_level_statements:
            print_statements.append({
                "file": str(file_path),
                "line": lineno,
                "message": f"Module execution block detected: {stmt_type}",
            })

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                if not ast.get_docstring(node):
                    missing_docstrings.append({
                        "file": str(file_path),
                        "line": getattr(node, "lineno", 0),
                        "type": type(node).__name__,
                        "name": getattr(node, "name", "module"),
                        "message": f"Missing docstring for {type(node).__name__}",
                    })
