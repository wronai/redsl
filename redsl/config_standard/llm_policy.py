"""LLM policy and coding configuration models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LLMPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["frontier_lag", "frontier_only", "bounded"] = "frontier_lag"
    max_age_days: int = Field(
        default=180,
        ge=1,
        le=3650,
        description="Maksymalny wiek modelu LLM w dniach. Modele starsze zostaną odrzucone.",
        json_schema_extra={
            "x-nlp-aliases": ["wiek modelu", "age limit", "model age", "jak stare modele"],
            "x-risk-level": "low",
        },
    )
    strict: bool = Field(
        default=True,
        description="Jeśli true, odrzucone modele rzucają wyjątek. Jeśli false, używają fallbacku.",
        json_schema_extra={
            "x-nlp-aliases": ["tryb strict", "strict mode", "twardo", "blokuj"],
            "x-risk-level": "medium",
            "x-requires-confirmation": True,
        },
    )
    unknown_release: Literal["deny", "warn", "allow"] = "deny"
    min_sources_agree: int = Field(default=2, ge=1, le=10)


class CostWeights(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input: float = Field(default=0.8, ge=0.0, le=100.0)
    output: float = Field(default=0.2, ge=0.0, le=100.0)

    @model_validator(mode="after")
    def _check_total(self) -> CostWeights:
        if self.input + self.output <= 0:
            raise ValueError("At least one cost weight must be positive")
        return self


class CodingTiers(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cheap: float = Field(
        default=0.50,
        ge=0.0,
        le=100.0,
        description="Maksymalny koszt USD/1M tokenów dla tieru 'cheap'",
        json_schema_extra={
            "x-nlp-aliases": ["tani tier", "tani limit", "max koszt tani"],
            "x-risk-level": "low",
        },
    )
    balanced: float = Field(
        default=3.00,
        ge=0.0,
        le=100.0,
        description="Maksymalny koszt USD/1M tokenów dla tieru 'balanced'",
        json_schema_extra={
            "x-nlp-aliases": ["balanced tier", "średni koszt", "zbalansowany"],
            "x-risk-level": "low",
        },
    )
    premium: float = Field(
        default=15.00,
        ge=0.0,
        le=100.0,
        description="Maksymalny koszt USD/1M tokenów dla tieru 'premium'",
        json_schema_extra={
            "x-nlp-aliases": ["premium tier", "drogi tier", "najlepszy model"],
            "x-risk-level": "low",
        },
    )


class DefaultOperationTiers(BaseModel):
    model_config = ConfigDict(extra="forbid")

    extract_function: Literal["cheap", "balanced", "premium"] = "cheap"
    split_module: Literal["cheap", "balanced", "premium"] = "balanced"
    architecture_review: Literal["cheap", "balanced", "premium"] = "premium"


class CodingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cost_metric: Literal["weighted", "prompt", "completion", "blended_1m"] = "weighted"
    cost_weights: CostWeights = Field(default_factory=CostWeights)
    min_context: int = Field(default=32768, ge=1)
    require_tool_calling: bool = True
    tiers: CodingTiers = Field(default_factory=CodingTiers)
    default_tiers: DefaultOperationTiers = Field(default_factory=DefaultOperationTiers)
    max_cost_per_call_usd: float = Field(
        default=0.10,
        ge=0.0,
        le=100.0,
        description="Kill switch dla pojedynczego wywołania LLM.",
        json_schema_extra={
            "x-nlp-aliases": ["limit kosztu", "max koszt per call", "safety limit"],
            "x-risk-level": "medium",
        },
    )


__all__ = [
    "CodingConfig",
    "CodingTiers",
    "CostWeights",
    "DefaultOperationTiers",
    "LLMPolicy",
]
