"""Hard requirement checks for model selection."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..registry.models import ModelInfo, QualitySignals
    from .models import CodingRequirements


def check_hard_requirements(
    info: "ModelInfo",
    req: "CodingRequirements",
) -> tuple[bool, str | None]:
    """Check if model meets hard requirements."""
    cap = info.capabilities
    q = info.quality

    checks = [
        _check_context_length(cap.context_length, req.min_context),
        _check_tool_calling(cap.supports_tool_calling, req.require_tool_calling),
        _check_json_mode(cap.supports_json_mode, req.require_json_mode),
        _check_streaming(cap.supports_streaming, req.require_streaming),
        _check_quality_signal(q, req.require_quality_signal),
        _check_aider_score(q, req.min_aider_score),
        _check_pricing(info.pricing),
    ]

    for passed, reason in checks:
        if not passed:
            return False, reason

    return True, None


def _check_context_length(context_length: int | None, min_context: int) -> tuple[bool, str | None]:
    if context_length and context_length < min_context:
        return False, f"context {context_length} < {min_context}"
    return True, None


def _check_tool_calling(supports_tool_calling: bool, require: bool) -> tuple[bool, str | None]:
    if require and not supports_tool_calling:
        return False, "no tool_calling"
    return True, None


def _check_json_mode(supports_json_mode: bool, require: bool) -> tuple[bool, str | None]:
    if require and not supports_json_mode:
        return False, "no json_mode"
    return True, None


def _check_streaming(supports_streaming: bool, require: bool) -> tuple[bool, str | None]:
    if require and not supports_streaming:
        return False, "no streaming"
    return True, None


def _check_quality_signal(q: "QualitySignals", require: bool) -> tuple[bool, str | None]:
    if require and not q.has_any:
        return False, "no quality signal (not in programming category, no benchmark, not in known_good)"
    return True, None


def _check_aider_score(q: "QualitySignals", min_score: float) -> tuple[bool, str | None]:
    if min_score > 0 and q.aider_polyglot_score is not None:
        if q.aider_polyglot_score < min_score:
            return False, f"aider {q.aider_polyglot_score} < {min_score}"
    return True, None


def _check_pricing(pricing) -> tuple[bool, str | None]:
    if not pricing.is_known:
        return False, "unknown pricing"
    return True, None


def score_quality(info: "ModelInfo") -> float:
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
