"""Metrics and safety checks for model selection."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from prometheus_client import Counter

log = logging.getLogger(__name__)

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


def check_cost_per_call(estimated_cost_usd: Decimal) -> bool:
    """Check if cost is within safety limits."""
    import os
    max_cost = Decimal(os.getenv("LLM_CODING_MAX_COST_PER_CALL_USD", "0.10"))
    if estimated_cost_usd > max_cost:
        log.warning(
            "Estimated cost $%.4f exceeds safety limit $%.4f",
            estimated_cost_usd, max_cost
        )
        return False
    return True
