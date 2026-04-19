"""Model selection for coding - "cheapest for coding" functionality.

Public API
----------
    CostProfile, CodingRequirements, ModelCandidate, ModelSelectionError
    SelectionStrategy, ModelSelector
    build_selector(), get_selector(), invalidate_selector()
    select_model_for_operation()
    track_model_selection(), check_cost_per_call()
"""

from __future__ import annotations

from .config import build_selector, get_selector, invalidate_selector
from .metrics import check_cost_per_call, track_model_selection
from .models import (
    CodingRequirements,
    CostProfile,
    ModelCandidate,
    ModelSelectionError,
)
from .ops import select_model_for_operation
from .selector import ModelSelector
from .strategy import SelectionStrategy

__all__ = [
    "SelectionStrategy",
    "CostProfile",
    "CodingRequirements",
    "ModelCandidate",
    "ModelSelectionError",
    "ModelSelector",
    "build_selector",
    "get_selector",
    "select_model_for_operation",
    "track_model_selection",
    "check_cost_per_call",
    "invalidate_selector",
]
