"""Model selection for coding - "cheapest for coding" functionality.

Backward-compatibility wrapper for the refactored selection package.
All implementation moved to redsl.llm.selection package.

Public API
----------
    CostProfile, CodingRequirements, ModelCandidate, ModelSelectionError
    SelectionStrategy, ModelSelector
    build_selector(), get_selector(), invalidate_selector()
    select_model_for_operation()
    track_model_selection(), check_cost_per_call()
"""

from __future__ import annotations

from .selection import (
    CodingRequirements,
    CostProfile,
    ModelCandidate,
    ModelSelectionError,
    ModelSelector,
    SelectionStrategy,
    build_selector,
    check_cost_per_call,
    get_selector,
    invalidate_selector,
    select_model_for_operation,
    track_model_selection,
)

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
