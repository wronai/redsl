"""Config change proposal models."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


def _utcnow() -> datetime:
    return datetime.now(UTC)


CONFIG_PROPOSAL_KIND = "ConfigChangeProposal"


class ProposalMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str = ""
    generated_at: datetime = Field(default_factory=_utcnow)
    agent_model: str = ""
    conversation_id: str = ""
    risk_level: Literal["low", "medium", "high", "critical"] = "low"


class ConfigPreconditions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    config_version: int | None = None
    config_fingerprint: str | None = None


class ConfigValidationState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_valid: bool | None = None
    policy_valid: bool | None = None
    conflicts: list[str] = Field(default_factory=list)


class ConfigChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    op: Literal["set", "add", "remove", "replace_secret"]
    path: str = Field(
        ..., min_length=1, description="JSONPath-like path, e.g. spec.coding.tiers.balanced"
    )
    current_value: Any | None = None
    new_value: Any | None = None
    rationale: str = Field(..., min_length=1)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    risk_level: Literal["low", "medium", "high", "critical"] = "low"
    requires_confirmation: bool = False


class ConfigChangeProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    apiVersion: str = "redsl.config/v1"
    kind: str = CONFIG_PROPOSAL_KIND
    metadata: ProposalMetadata = Field(default_factory=ProposalMetadata)
    changes: list[ConfigChange] = Field(default_factory=list)
    summary: str = ""
    requires_new_secret: bool = False
    new_secret_name: str | None = None
    preconditions: ConfigPreconditions = Field(default_factory=ConfigPreconditions)
    validation: ConfigValidationState = Field(default_factory=ConfigValidationState)

    @model_validator(mode="after")
    def _check_secret_fields(self) -> ConfigChangeProposal:
        if self.requires_new_secret and not self.new_secret_name:
            raise ValueError("new_secret_name is required when requires_new_secret is true")
        return self


def export_proposal_schema() -> dict[str, Any]:

    schema = ConfigChangeProposal.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://redsl.io/schemas/config/proposal/v1.json"
    schema.setdefault("title", "ConfigChangeProposal")
    return schema


def proposal_to_yaml(proposal: ConfigChangeProposal) -> str:
    import yaml

    data = proposal.model_dump(mode="json")
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


__all__ = [
    "CONFIG_PROPOSAL_KIND",
    "ConfigChange",
    "ConfigChangeProposal",
    "ConfigPreconditions",
    "ConfigValidationState",
    "ProposalMetadata",
    "export_proposal_schema",
    "proposal_to_yaml",
]
