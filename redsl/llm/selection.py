"""Model selection for coding - "cheapest for coding" functionality."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .gate import ModelAgeGate
    from .registry.aggregator import RegistryAggregator
    from .registry.models import ModelInfo, Pricing

log = logging.getLogger(__name__)


class SelectionStrategy(str, Enum):
    """Strategia wyboru modelu."""

    CHEAPEST = "cheapest"
    CHEAPEST_QUALITY = "cheapest_quality"
    PARETO = "pareto"
    ROUND_ROBIN = "round_robin"


@dataclass(frozen=True)
class CostProfile:
    """Jak liczymy koszt per model."""

    weight_input: float = 0.8
    weight_output: float = 0.2

    def weighted_per_1m(self, p: Pricing) -> Decimal | None:
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

    info: ModelInfo
    weighted_cost_per_1m: Decimal | None
    quality_score: float  # 0-100, syntetyczne
    passes_requirements: bool
    rejection_reason: str | None = None


class ModelSelectionError(Exception):
    """Raised when no model can be selected."""

    pass


class ModelSelector:
    """Wybiera najtańszy model spełniający wymagania."""

    def __init__(
        self,
        aggregator: RegistryAggregator,
        gate: ModelAgeGate,
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
            # 1. Quality signal check (soft — zależy od require_quality_signal)
            in_known_good = mid in self.known_good
            if in_known_good:
                from dataclasses import replace
                from .registry.models import QualitySignals
                info = replace(
                    info,
                    quality=replace(info.quality, in_known_good_list=True),
                )

            # 2. Policy gate (wiek, deprecation)
            gate_decision = self.gate.check(mid)
            if not gate_decision.allowed:
                result.append(ModelCandidate(
                    info=info,
                    weighted_cost_per_1m=None,
                    quality_score=0,
                    passes_requirements=False,
                    rejection_reason=f"policy: {gate_decision.reason}",
                ))
                continue

            # 3. Hard requirements
            ok, reason = self._check_hard_requirements(info)
            cost = self.cost.weighted_per_1m(info.pricing)

            result.append(ModelCandidate(
                info=info,
                weighted_cost_per_1m=cost,
                quality_score=self._score_quality(info),
                passes_requirements=ok,
                rejection_reason=None if ok else reason,
            ))

        return sorted(
            result,
            key=lambda c: (c.weighted_cost_per_1m or Decimal("Infinity")),
        )

    def pick(self, tier: str | None = None) -> ModelCandidate:
        """Wybierz jeden model zgodnie ze strategią i tierem."""
        candidates = [c for c in self.candidates() if c.passes_requirements]
        if not candidates:
            raise ModelSelectionError("No model passes requirements")

        if tier:
            max_cost = self.tiers.get(tier)
            if max_cost is None:
                raise ModelSelectionError(f"Unknown tier: {tier}")

            in_tier = [
                c for c in candidates
                if c.weighted_cost_per_1m and c.weighted_cost_per_1m <= max_cost
            ]
            if not in_tier:
                if not self.fallback_to_next_tier:
                    raise ModelSelectionError(
                        f"No models in tier '{tier}' (≤${max_cost}/1M)"
                    )
                # spróbuj następny tier w górę
                higher = self._next_tier(tier)
                if higher:
                    log.warning("Tier '%s' empty, falling back to '%s'", tier, higher)
                    return self.pick(higher)
                raise ModelSelectionError(
                    f"No models in tier '{tier}' and no higher tier"
                )
            candidates = in_tier

        return self._apply_strategy(candidates)

    def _apply_strategy(self, candidates: list[ModelCandidate]) -> ModelCandidate:
        """Apply selection strategy to candidates."""
        if self.strategy == SelectionStrategy.CHEAPEST:
            return candidates[0]  # już posortowane po koszcie

        if self.strategy == SelectionStrategy.CHEAPEST_QUALITY:
            # najtańszy który przechodzi próg jakości
            with_quality = [c for c in candidates if c.quality_score >= 50]
            return with_quality[0] if with_quality else candidates[0]

        if self.strategy == SelectionStrategy.PARETO:
            # krzywa Pareto: niedominowany w (koszt, jakość)
            pareto = self._pareto_front(candidates)
            # wybierz środek krzywej
            return pareto[len(pareto) // 2]

        if self.strategy == SelectionStrategy.ROUND_ROBIN:
            return self._round_robin_pick(candidates)

        return candidates[0]

    def _check_hard_requirements(self, info: ModelInfo) -> tuple[bool, str | None]:
        """Check if model meets hard requirements."""
        cap = info.capabilities

        if cap.context_length and cap.context_length < self.req.min_context:
            return False, f"context {cap.context_length} < {self.req.min_context}"

        if self.req.require_tool_calling and not cap.supports_tool_calling:
            return False, "no tool_calling"

        if self.req.require_json_mode and not cap.supports_json_mode:
            return False, "no json_mode"

        if self.req.require_streaming and not cap.supports_streaming:
            return False, "no streaming"

        q = info.quality
        if self.req.require_quality_signal and not q.has_any:
            return False, "no quality signal (not in programming category, no benchmark, not in known_good)"

        if self.req.min_aider_score > 0 and q.aider_polyglot_score is not None:
            if q.aider_polyglot_score < self.req.min_aider_score:
                return False, f"aider {q.aider_polyglot_score} < {self.req.min_aider_score}"

        if not info.pricing.is_known:
            return False, "unknown pricing"

        return True, None

    def _score_quality(self, info: ModelInfo) -> float:
        """Syntetyczna jakość 0-100 z dostępnych sygnałów."""
        q = info.quality
        score = 0.0
        signals = 0

        if q.aider_polyglot_score is not None:
            score += q.aider_polyglot_score
            signals += 1

        if q.openrouter_category_programming:
            score += 60
            signals += 1

        if q.in_known_good_list:
            score += 70
            signals += 1

        return score / signals if signals else 0.0

    def _pareto_front(self, candidates: list[ModelCandidate]) -> list[ModelCandidate]:
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

    def _round_robin_pick(self, candidates: list[ModelCandidate]) -> ModelCandidate:
        """Round-robin selection (for A/B testing)."""
        # Simple implementation: use hash of current hour
        import time
        hour_hash = int(time.time() / 3600)
        index = hour_hash % len(candidates)
        return candidates[index]

    def _next_tier(self, current: str) -> str | None:
        """Get next tier up (cheap → balanced → premium)."""
        order = ["cheap", "balanced", "premium"]
        try:
            idx = order.index(current)
            return order[idx + 1] if idx + 1 < len(order) else None
        except ValueError:
            return None


def _parse_known_good(env_value: str) -> set[str]:
    """Parse comma-separated list of known good models."""
    return set(m.strip() for m in env_value.split(",") if m.strip())


def _parse_tiers() -> dict[str, Decimal]:
    """Parse tier definitions from environment."""
    return {
        "cheap": Decimal(os.getenv("LLM_CODING_TIER_CHEAP", "0.50")),
        "balanced": Decimal(os.getenv("LLM_CODING_TIER_BALANCED", "3.00")),
        "premium": Decimal(os.getenv("LLM_CODING_TIER_PREMIUM", "15.00")),
    }


def build_selector(
    aggregator: RegistryAggregator,
    gate: ModelAgeGate,
) -> ModelSelector:
    """Build ModelSelector from environment configuration."""
    # Cost profile
    cost_metric = os.getenv("LLM_COST_METRIC", "weighted")
    if cost_metric == "weighted":
        cost_profile = CostProfile(
            weight_input=float(os.getenv("LLM_COST_WEIGHT_INPUT", "0.8")),
            weight_output=float(os.getenv("LLM_COST_WEIGHT_OUTPUT", "0.2")),
        )
    elif cost_metric == "completion":
        cost_profile = CostProfile(weight_input=0.0, weight_output=1.0)
    elif cost_metric == "prompt":
        cost_profile = CostProfile(weight_input=1.0, weight_output=0.0)
    else:  # blended_1m
        cost_profile = CostProfile(weight_input=0.5, weight_output=0.5)

    # Requirements
    requirements = CodingRequirements(
        min_context=int(os.getenv("LLM_CODING_MIN_CONTEXT", "32768")),
        require_tool_calling=os.getenv("LLM_CODING_REQUIRE_TOOL_CALLING", "true").lower() == "true",
        require_json_mode=os.getenv("LLM_CODING_REQUIRE_JSON_MODE", "false").lower() == "true",
        require_streaming=os.getenv("LLM_CODING_REQUIRE_STREAMING", "true").lower() == "true",
        min_aider_score=float(os.getenv("LLM_CODING_MIN_AIDER_SCORE", "30.0")),
        require_quality_signal=os.getenv("LLM_CODING_REQUIRE_QUALITY_SIGNAL", "true").lower() == "true",
    )

    # Strategy
    strategy_str = os.getenv("LLM_CODING_SELECTION_STRATEGY", "cheapest_quality")
    strategy = SelectionStrategy(strategy_str)

    # Known good list
    known_good = _parse_known_good(os.getenv(
        "LLM_CODING_KNOWN_GOOD",
        "anthropic/claude-sonnet-4-5,anthropic/claude-haiku-4-5,openai/gpt-4o,openai/gpt-4o-mini,deepseek/deepseek-v3,qwen/qwen-3-coder,mistralai/codestral-latest,google/gemini-2.5-pro"
    ))

    # Tiers
    tiers = _parse_tiers()

    # Fallback
    fallback = os.getenv("LLM_CODING_FALLBACK_TO_NEXT_TIER", "true").lower() == "true"

    return ModelSelector(
        aggregator=aggregator,
        gate=gate,
        cost_profile=cost_profile,
        requirements=requirements,
        tiers=tiers,
        strategy=strategy,
        known_good=known_good,
        fallback_to_next_tier=fallback,
    )


def select_model_for_operation(operation: str) -> str:
    """
    Mapping: 'extract_function' → tier z .env → konkretny model.
    Wywoływane przed każdym completion w pipeline refactoringu.
    """
    tier = os.getenv(f"LLM_DEFAULT_TIER_{operation.upper()}", "balanced")

    from . import get_gate
    from .registry import RegistryAggregator
    from .registry.sources import (
        AiderLeaderboardSource,
        OpenRouterSource,
        ModelsDevSource,
    )

    gate = get_gate()

    # Check if selector is already built into gate's aggregator
    agg = gate.agg

    # Build selector on the fly if needed
    selector = build_selector(agg, gate)

    try:
        pick = selector.pick(tier=tier)
        log.info(
            "Operation=%s tier=%s → model=%s ($%.2f/1M, quality=%.0f)",
            operation, tier, pick.info.id,
            pick.weighted_cost_per_1m or Decimal(0), pick.quality_score,
        )
        return pick.info.id
    except ModelSelectionError as e:
        log.error("Model selection failed for %s: %s", operation, e)
        # Fallback to default model from config
        from . import LLMConfig
        config = LLMConfig.from_env()
        return config.model


# Global selector cache
_selector: ModelSelector | None = None


def get_selector() -> ModelSelector:
    """Get or build the global ModelSelector."""
    global _selector
    if _selector is None:
        from . import get_gate
        from .registry import RegistryAggregator

        gate = get_gate()
        _selector = build_selector(gate.agg, gate)
    return _selector


def invalidate_selector() -> None:
    """Invalidate the global selector cache (e.g., after config change)."""
    global _selector
    _selector = None
    log.debug("Model selector cache invalidated")


# Prometheus-style metrics (if prometheus_client available)
try:
    from prometheus_client import Counter

    MODEL_SELECTED_COUNTER = Counter(
        "redsl_llm_model_selected_total",
        "Total model selections",
        ["model", "tier", "operation"],
    )
except ImportError:
    MODEL_SELECTED_COUNTER = None


def track_model_selection(model: str, tier: str, operation: str) -> None:
    """Track model selection for metrics."""
    if MODEL_SELECTED_COUNTER is not None:
        MODEL_SELECTED_COUNTER.labels(model=model, tier=tier, operation=operation).inc()
    else:
        log.debug("Model selected: model=%s tier=%s operation=%s", model, tier, operation)


# Safety checks
def check_cost_per_call(estimated_cost_usd: Decimal) -> bool:
    """Check if cost is within safety limits."""
    max_cost = Decimal(os.getenv("LLM_CODING_MAX_COST_PER_CALL_USD", "0.10"))
    if estimated_cost_usd > max_cost:
        log.warning(
            "Estimated cost $%.4f exceeds safety limit $%.4f",
            estimated_cost_usd, max_cost
        )
        return False
    return True


__all__ = [
    "SelectionStrategy",
    "CostProfile",
    "CodingRequirements",
    "ModelCandidate",
    "ModelSelector",
    "ModelSelectionError",
    "build_selector",
    "get_selector",
    "select_model_for_operation",
    "track_model_selection",
    "check_cost_per_call",
    "invalidate_selector",
]
