"""Selection strategies for model picking."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import ModelCandidate


class SelectionStrategy(str, Enum):
    """Strategia wyboru modelu."""

    CHEAPEST = "cheapest"
    CHEAPEST_QUALITY = "cheapest_quality"
    PARETO = "pareto"
    ROUND_ROBIN = "round_robin"


def apply_strategy(
    candidates: list["ModelCandidate"],
    strategy: SelectionStrategy,
) -> "ModelCandidate":
    """Apply selection strategy to candidates."""
    if strategy == SelectionStrategy.CHEAPEST:
        return candidates[0]  # już posortowane po koszcie

    if strategy == SelectionStrategy.CHEAPEST_QUALITY:
        # najtańszy który przechodzi próg jakości
        with_quality = [c for c in candidates if c.quality_score >= 50]
        return with_quality[0] if with_quality else candidates[0]

    if strategy == SelectionStrategy.PARETO:
        # krzywa Pareto: niedominowany w (koszt, jakość)
        pareto = _pareto_front(candidates)
        # wybierz środek krzywej
        return pareto[len(pareto) // 2]

    if strategy == SelectionStrategy.ROUND_ROBIN:
        return _round_robin_pick(candidates)

    return candidates[0]


def _pareto_front(candidates: list["ModelCandidate"]) -> list["ModelCandidate"]:
    """Modele niedominowane (najtańsze dla swojej jakości)."""
    front = []
    for c in candidates:
        if c.weighted_cost_per_1m is None:
            continue
        dominated = any(
            other.weighted_cost_per_1m <= c.weighted_cost_per_1m
            and other.quality_score >= c.quality_score
            and other is not c
            for other in candidates
            if other.weighted_cost_per_1m is not None
        )
        if not dominated:
            front.append(c)
    return sorted(front, key=lambda c: c.weighted_cost_per_1m or Decimal("Infinity"))


def _round_robin_pick(candidates: list["ModelCandidate"]) -> "ModelCandidate":
    """Round-robin selection (for A/B testing)."""
    import time
    hour_hash = int(time.time() / 3600)
    index = hour_hash % len(candidates)
    return candidates[index]
