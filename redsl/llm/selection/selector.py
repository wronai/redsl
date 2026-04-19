"""ModelSelector - main selection logic."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING

from .checks import check_hard_requirements, score_quality
from .models import ModelCandidate, ModelSelectionError
from .strategy import SelectionStrategy, apply_strategy

if TYPE_CHECKING:
    from ..gate import ModelAgeGate
    from ..registry.aggregator import RegistryAggregator
    from ..registry.models import ModelInfo
    from .models import CodingRequirements, CostProfile

log = logging.getLogger(__name__)


class ModelSelector:
    """Wybiera najtańszy model spełniający wymagania."""

    def __init__(
        self,
        aggregator: "RegistryAggregator",
        gate: "ModelAgeGate",
        cost_profile: CostProfile,
        requirements: CodingRequirements,
        tiers: dict[str, Decimal],
        strategy: SelectionStrategy,
        known_good: set[str],
        fallback_to_next_tier: bool = True,
    ):
        self.agg = aggregator
        self.gate = gate
        self.cost = cost_profile
        self.req = requirements
        self.tiers = tiers
        self.strategy = strategy
        self.known_good = known_good
        self.fallback_to_next_tier = fallback_to_next_tier

    def candidates(self) -> list[ModelCandidate]:
        """Wszystkie modele przefiltrowane, posortowane po koszcie."""
        all_models = self.agg.get_all()
        result = []

        for mid, info in all_models.items():
            info = self._apply_known_good_override(info, mid)

            # Policy gate (wiek, deprecation)
            gate_result = self._check_gate(mid, info)
            if gate_result:
                result.append(gate_result)
                continue

            # Hard requirements
            ok, reason = check_hard_requirements(info, self.req)
            cost = self.cost.weighted_per_1m(info.pricing)

            result.append(ModelCandidate(
                info=info,
                weighted_cost_per_1m=cost,
                quality_score=score_quality(info),
                passes_requirements=ok,
                rejection_reason=None if ok else reason,
            ))

        return sorted(
            result,
            key=lambda c: (c.weighted_cost_per_1m or Decimal("Infinity")),
        )

    def _apply_known_good_override(self, info: "ModelInfo", mid: str) -> "ModelInfo":
        """Apply known_good override to quality signals."""
        from dataclasses import replace
        from ..registry.models import QualitySignals

        in_known_good = mid in self.known_good
        if in_known_good:
            return replace(
                info,
                quality=replace(info.quality, in_known_good_list=True),
            )
        return info

    def _check_gate(self, mid: str, info: "ModelInfo") -> ModelCandidate | None:
        """Check policy gate, return candidate if rejected."""
        try:
            gate_decision = self.gate.check(mid)
            if not gate_decision.allowed:
                return ModelCandidate(
                    info=info,
                    weighted_cost_per_1m=None,
                    quality_score=0,
                    passes_requirements=False,
                    rejection_reason=f"policy: {gate_decision.reason}",
                )
        except Exception as e:
            return ModelCandidate(
                info=info,
                weighted_cost_per_1m=None,
                quality_score=0,
                passes_requirements=False,
                rejection_reason=f"policy: {e}",
            )
        return None

    def pick(self, tier: str | None = None) -> ModelCandidate:
        """Wybierz jeden model zgodnie ze strategią i tierem."""
        candidates = self._get_passing_candidates()

        if tier:
            candidates = self._filter_by_tier(candidates, tier)

        return apply_strategy(candidates, self.strategy)

    def _get_passing_candidates(self) -> list[ModelCandidate]:
        """Get candidates that pass requirements."""
        candidates = [c for c in self.candidates() if c.passes_requirements]
        if not candidates:
            raise ModelSelectionError("No model passes requirements")
        return candidates

    def _filter_by_tier(self, candidates: list[ModelCandidate], tier: str) -> list[ModelCandidate]:
        """Filter candidates by tier, with fallback if enabled."""
        max_cost = self.tiers.get(tier)
        if max_cost is None:
            raise ModelSelectionError(f"Unknown tier: {tier}")

        in_tier = [
            c for c in candidates
            if c.weighted_cost_per_1m and c.weighted_cost_per_1m <= max_cost
        ]

        if in_tier:
            return in_tier

        if not self.fallback_to_next_tier:
            raise ModelSelectionError(f"No models in tier '{tier}' (≤${max_cost}/1M)")

        higher = self._next_tier(tier)
        if higher:
            log.warning("Tier '%s' empty, falling back to '%s'", tier, higher)
            return self._get_passing_candidates_for_tier(higher)

        raise ModelSelectionError(f"No models in tier '{tier}' and no higher tier")

    def _get_passing_candidates_for_tier(self, tier: str) -> list[ModelCandidate]:
        """Get passing candidates for a specific tier."""
        candidates = self._get_passing_candidates()
        return self._filter_by_tier(candidates, tier)

    def _next_tier(self, current: str) -> str | None:
        """Get next tier up (cheap → balanced → premium)."""
        order = ["cheap", "balanced", "premium"]
        try:
            idx = order.index(current)
            return order[idx + 1] if idx + 1 < len(order) else None
        except ValueError:
            return None
