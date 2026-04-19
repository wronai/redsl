"""Data models for model selection."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..registry.models import ModelInfo, Pricing


@dataclass(frozen=True)
class CostProfile:
    """Jak liczymy koszt per model."""

    weight_input: float = 0.8
    weight_output: float = 0.2

    def weighted_per_1m(self, p: "Pricing") -> Decimal | None:
        """Calculate weighted cost per 1M tokens."""
        if not p.is_known:
            return None
        # ceny OpenRouter są per token, skala do 1M
        return (
            p.prompt * Decimal(self.weight_input) +
            p.completion * Decimal(self.weight_output)
        ) * Decimal(1_000_000)


@dataclass(frozen=True)
class CodingRequirements:
    """Wymagania techniczne dla modelu do kodowania."""

    min_context: int = 32768
    require_tool_calling: bool = True
    require_json_mode: bool = False
    require_streaming: bool = True
    min_aider_score: float = 30.0
    require_quality_signal: bool = True  # musi mieć JAKIKOLWIEK quality signal


@dataclass
class ModelCandidate:
    """Kandydat na model z metrykami."""

    info: "ModelInfo"
    weighted_cost_per_1m: Decimal | None
    quality_score: float  # 0-100, syntetyczne
    passes_requirements: bool
    rejection_reason: str | None = None


class ModelSelectionError(Exception):
    """Raised when no model can be selected."""
    pass
