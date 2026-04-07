"""
Parser plików toon — subpackage.

Eksportuje ToonParser jako fasadę łączącą wszystkie wyspecjalizowane parsery:
- ProjectParser  — HEALTH, ALERTS, HOTSPOTS, MODULES, LAYERS, REFACTOR
- DuplicationParser — grupy zduplikowanego kodu
- ValidationParser — błędy linterów
- FunctionsParser — per-funkcja CC
"""

from __future__ import annotations

from .duplication_parser import DuplicationParser
from .functions_parser import FunctionsParser
from .project_parser import ProjectParser
from .validation_parser import ValidationParser


class ToonParser(ProjectParser, DuplicationParser, ValidationParser, FunctionsParser):
    """Parser plików toon — fasada nad wyspecjalizowanymi parserami."""


__all__ = [
    "ToonParser",
    "ProjectParser",
    "DuplicationParser",
    "ValidationParser",
    "FunctionsParser",
]
