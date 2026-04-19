"""Configuration and factory functions for model selection."""

from __future__ import annotations

import logging
import os
from decimal import Decimal
from typing import TYPE_CHECKING

from .models import CodingRequirements, CostProfile
from .selector import ModelSelector
from .strategy import SelectionStrategy

if TYPE_CHECKING:
    from ..gate import ModelAgeGate
    from ..registry.aggregator import RegistryAggregator

log = logging.getLogger(__name__)


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


def _build_cost_profile() -> CostProfile:
    """Build CostProfile from environment."""
    cost_metric = os.getenv("LLM_COST_METRIC", "weighted")
    if cost_metric == "weighted":
        return CostProfile(
            weight_input=float(os.getenv("LLM_COST_WEIGHT_INPUT", "0.8")),
            weight_output=float(os.getenv("LLM_COST_WEIGHT_OUTPUT", "0.2")),
        )
    elif cost_metric == "completion":
        return CostProfile(weight_input=0.0, weight_output=1.0)
    elif cost_metric == "prompt":
        return CostProfile(weight_input=1.0, weight_output=0.0)
    else:  # blended_1m
        return CostProfile(weight_input=0.5, weight_output=0.5)


def _build_requirements() -> CodingRequirements:
    """Build CodingRequirements from environment."""
    return CodingRequirements(
        min_context=int(os.getenv("LLM_CODING_MIN_CONTEXT", "32768")),
        require_tool_calling=os.getenv("LLM_CODING_REQUIRE_TOOL_CALLING", "true").lower() == "true",
        require_json_mode=os.getenv("LLM_CODING_REQUIRE_JSON_MODE", "false").lower() == "true",
        require_streaming=os.getenv("LLM_CODING_REQUIRE_STREAMING", "true").lower() == "true",
        min_aider_score=float(os.getenv("LLM_CODING_MIN_AIDER_SCORE", "30.0")),
        require_quality_signal=os.getenv("LLM_CODING_REQUIRE_QUALITY_SIGNAL", "true").lower() == "true",
    )


def build_selector(
    aggregator: RegistryAggregator,
    gate: ModelAgeGate,
) -> ModelSelector:
    """Build ModelSelector from environment configuration."""
    cost_profile = _build_cost_profile()
    requirements = _build_requirements()

    strategy_str = os.getenv("LLM_CODING_SELECTION_STRATEGY", "cheapest_quality")
    strategy = SelectionStrategy(strategy_str)

    known_good = _parse_known_good(os.getenv(
        "LLM_CODING_KNOWN_GOOD",
        "anthropic/claude-sonnet-4-5,anthropic/claude-haiku-4-5,openai/gpt-4o,moonshotai/kimi-k2.5,deepseek/deepseek-v3,qwen/qwen-3-coder,mistralai/codestral-latest,google/gemini-2.5-pro"
    ))

    tiers = _parse_tiers()
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


# Global selector cache
_selector: ModelSelector | None = None


def get_selector() -> ModelSelector:
    """Get or build the global ModelSelector."""
    global _selector
    if _selector is None:
        from .. import get_gate
        from ..registry import RegistryAggregator

        gate = get_gate()
        _selector = build_selector(gate.agg, gate)
    return _selector


def invalidate_selector() -> None:
    """Invalidate the global selector cache (e.g., after config change)."""
    global _selector
    _selector = None
    log.debug("Model selector cache invalidated")
