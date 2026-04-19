"""High-level operations using model selection."""

from __future__ import annotations

import logging
from decimal import Decimal

from .config import get_selector
from .models import ModelSelectionError

log = logging.getLogger(__name__)


def select_model_for_operation(operation: str) -> str:
    """
    Mapping: 'extract_function' → tier z .env → konkretny model.
    Wywoływane przed każdym completion w pipeline refactoringu.
    """
    tier = __import__("os").getenv(f"LLM_DEFAULT_TIER_{operation.upper()}", "balanced")

    from .. import get_gate
    from ..registry import RegistryAggregator
    from ..registry.sources import (
        AiderLeaderboardSource,
        OpenRouterSource,
        ModelsDevSource,
    )

    gate = get_gate()
    agg = gate.agg

    from .config import build_selector
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
        from .. import LLMConfig
        config = LLMConfig.from_env()
        return config.model
