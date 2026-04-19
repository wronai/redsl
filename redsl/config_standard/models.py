"""Pydantic models and schema helpers for the redsl config standard."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

CONFIG_STANDARD_API_VERSION = "redsl.config/v1"
CONFIG_STANDARD_KIND = "RedslConfig"
CONFIG_PROPOSAL_KIND = "ConfigChangeProposal"
CONFIG_AGENT_VERSION = "redsl-config-agent@1.0.0"


def _utcnow() -> datetime:
    return datetime.now(UTC)


class ConfigOrigin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cloned_from: str | None = None
    cloned_at: datetime | None = None


class ConfigMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    version: int = Field(default=1, ge=1)
    created: datetime = Field(default_factory=_utcnow)
    updated: datetime = Field(default_factory=_utcnow)
    fingerprint: str = ""
    origin: ConfigOrigin = Field(default_factory=ConfigOrigin)
    managed_by: str = CONFIG_AGENT_VERSION


class SecretRotation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    last_rotated: datetime | None = None
    rotate_every_days: int | None = Field(default=None, ge=1, le=3650)
    next_rotation_due: datetime | None = None

    @model_validator(mode="after")
    def _check_rotation_order(self) -> SecretRotation:
        if (
            self.last_rotated
            and self.next_rotation_due
            and self.next_rotation_due < self.last_rotated
        ):
            raise ValueError("next_rotation_due cannot be earlier than last_rotated")
        return self


class SecretSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ref: str = Field(..., min_length=1)
    required: bool = True
    rotation: SecretRotation = Field(default_factory=SecretRotation)

    @field_validator("ref")
    @classmethod
    def _validate_ref(cls, value: str) -> str:
        if not value.startswith(("file:", "env:", "vault:", "doppler:")):
            raise ValueError("Secret ref must start with file:, env:, vault:, or doppler:")
        return value


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


class RegistrySource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    enabled: bool = True
    url: str | None = None


class CacheConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: Path = Field(default_factory=lambda: Path("/var/cache/redsl/registry.json"))
    ttl_seconds: int = Field(default=21600, ge=0)
    stale_grace_seconds: int = Field(default=604800, ge=0)


class RedslConfigSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    llm_policy: LLMPolicy = Field(default_factory=LLMPolicy)
    coding: CodingConfig = Field(default_factory=CodingConfig)
    registry_sources: list[RegistrySource] = Field(default_factory=list)
    cache: CacheConfig = Field(default_factory=CacheConfig)


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

    apiVersion: Literal[CONFIG_STANDARD_API_VERSION] = CONFIG_STANDARD_API_VERSION
    kind: Literal[CONFIG_PROPOSAL_KIND] = CONFIG_PROPOSAL_KIND
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


class RedslConfigDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    apiVersion: Literal[CONFIG_STANDARD_API_VERSION] = CONFIG_STANDARD_API_VERSION
    kind: Literal[CONFIG_STANDARD_KIND] = CONFIG_STANDARD_KIND
    metadata: ConfigMetadata
    profile: str = "production"
    secrets: dict[str, SecretSpec] = Field(default_factory=dict)
    spec: RedslConfigSpec = Field(default_factory=RedslConfigSpec)

    def fingerprint_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"metadata"})

    def compute_fingerprint(self) -> str:
        raw = json.dumps(
            self.fingerprint_payload(), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(slots=True)
class PathCatalogEntry:
    path: str
    title: str
    description: str
    aliases: tuple[str, ...]
    risk_level: str = "low"
    requires_confirmation: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "title": self.title,
            "description": self.description,
            "aliases": list(self.aliases),
            "risk_level": self.risk_level,
            "requires_confirmation": self.requires_confirmation,
        }


CONFIG_PATH_CATALOG: list[PathCatalogEntry] = [
    PathCatalogEntry(
        path="spec.llm_policy.max_age_days",
        title="Maximum model age",
        description="Maksymalny wiek modelu LLM w dniach. Modele starsze zostaną odrzucone.",
        aliases=("wiek modelu", "age limit", "model age", "jak stare modele"),
        risk_level="low",
    ),
    PathCatalogEntry(
        path="spec.llm_policy.strict",
        title="Strict model policy",
        description="Jeśli true, odrzucone modele rzucają wyjątek. Jeśli false, używają fallbacku.",
        aliases=("tryb strict", "strict mode", "twardo", "blokuj"),
        risk_level="medium",
        requires_confirmation=True,
    ),
    PathCatalogEntry(
        path="spec.coding.tiers.cheap",
        title="Cheap tier budget",
        description="Maksymalny koszt USD/1M tokenów dla tieru 'cheap'.",
        aliases=("tani tier", "tani limit", "max koszt tani", "cheap tier"),
        risk_level="low",
    ),
    PathCatalogEntry(
        path="spec.coding.tiers.balanced",
        title="Balanced tier budget",
        description="Maksymalny koszt USD/1M tokenów dla tieru 'balanced'.",
        aliases=(
            "balanced tier",
            "średni koszt",
            "zbalansowany",
            "oszczędzanie kasa",
            "oszczędzać kasę",
        ),
        risk_level="low",
    ),
    PathCatalogEntry(
        path="spec.coding.tiers.premium",
        title="Premium tier budget",
        description="Maksymalny koszt USD/1M tokenów dla tieru 'premium'.",
        aliases=("premium tier", "drogi tier", "najlepszy model"),
        risk_level="low",
    ),
    PathCatalogEntry(
        path="spec.coding.cost_weights",
        title="Input/output cost weights",
        description="Wagi kosztu wejścia i wyjścia w trybie weighted.",
        aliases=("wagi kosztu", "input weight", "output weight"),
        risk_level="low",
    ),
    PathCatalogEntry(
        path="spec.coding.max_cost_per_call_usd",
        title="Per-call cost safety limit",
        description="Kill switch dla pojedynczego wywołania LLM.",
        aliases=("limit kosztu", "max koszt per call", "safety limit"),
        risk_level="medium",
        requires_confirmation=True,
    ),
    PathCatalogEntry(
        path="spec.coding.require_tool_calling",
        title="Require tool calling",
        description="Wymuś obsługę tool calling przy wyborze modelu.",
        aliases=("tool calling", "narzędzia", "funkcje"),
        risk_level="low",
    ),
    PathCatalogEntry(
        path="spec.registry_sources",
        title="Registry sources",
        description="Lista źródeł rejestru modeli.",
        aliases=("źródła rejestru", "sources", "registry"),
        risk_level="medium",
        requires_confirmation=True,
    ),
    PathCatalogEntry(
        path="spec.cache.path",
        title="Registry cache path",
        description="Ścieżka do cache rejestru modeli.",
        aliases=("cache path", "ścieżka cache", "cache"),
        risk_level="low",
    ),
    PathCatalogEntry(
        path="spec.cache.ttl_seconds",
        title="Registry cache TTL",
        description="Czas życia cache w sekundach.",
        aliases=("ttl", "cache ttl", "cache age"),
        risk_level="low",
    ),
    PathCatalogEntry(
        path="spec.secrets.*.ref",
        title="Secret reference",
        description="Deklaracja źródła sekretu, bez plaintextu.",
        aliases=("sekret ref", "secret ref", "file ref", "env ref"),
        risk_level="high",
        requires_confirmation=True,
    ),
    PathCatalogEntry(
        path="spec.secrets.*",
        title="Secret declaration",
        description="Dodanie, usunięcie lub zmiana sekretu jest zawsze krytyczna.",
        aliases=("sekret", "secret", "klucz api", "api key"),
        risk_level="critical",
        requires_confirmation=True,
    ),
    PathCatalogEntry(
        path="profile",
        title="Active profile",
        description="Wybrany profil ładowany z profiles/.",
        aliases=("profil", "profile", "environment profile"),
        risk_level="high",
        requires_confirmation=True,
    ),
    PathCatalogEntry(
        path="metadata.version",
        title="Config version",
        description="Numer wersji bumpowany przy każdej zmianie.",
        aliases=("wersja", "version", "rewizja"),
        risk_level="low",
    ),
    PathCatalogEntry(
        path="apiVersion",
        title="API version",
        description="Wersjonowanie schematu konfiguracji.",
        aliases=("api version", "schemat v1", "migracja"),
        risk_level="critical",
        requires_confirmation=True,
    ),
]


def build_default_config(
    *, name: str = "redsl-production", profile: str = "production"
) -> RedslConfigDocument:
    return RedslConfigDocument(
        metadata=ConfigMetadata(name=name),
        profile=profile,
        secrets={
            "openrouter_api_key": SecretSpec(ref="env:OPENROUTER_API_KEY", required=True),
            "anthropic_api_key": SecretSpec(ref="env:ANTHROPIC_API_KEY", required=False),
        },
        spec=RedslConfigSpec(
            llm_policy=LLMPolicy(),
            coding=CodingConfig(),
            registry_sources=[
                RegistrySource(
                    name="openrouter", enabled=True, url="https://openrouter.ai/api/v1/models"
                ),
                RegistrySource(name="models_dev", enabled=True, url=None),
                RegistrySource(name="aider_leaderboard", enabled=True, url=None),
            ],
            cache=CacheConfig(),
        ),
    )


DEFAULT_PROFILE_OVERRIDES: dict[str, dict[str, Any]] = {
    "default": {},
    "development": {
        "spec": {
            "llm_policy": {"strict": False, "mode": "bounded"},
            "cache": {"ttl_seconds": 3600, "stale_grace_seconds": 86400},
            "coding": {"tiers": {"cheap": 0.25, "balanced": 1.5, "premium": 8.0}},
        }
    },
    "production": {
        "spec": {
            "llm_policy": {"strict": True, "mode": "frontier_lag", "unknown_release": "deny"},
            "cache": {"ttl_seconds": 21600, "stale_grace_seconds": 604800},
        }
    },
    "minimal-cost": {
        "spec": {
            "llm_policy": {"strict": False, "mode": "bounded"},
            "coding": {
                "cost_weights": {"input": 0.9, "output": 0.1},
                "tiers": {"cheap": 0.20, "balanced": 1.0, "premium": 5.0},
                "default_tiers": {
                    "extract_function": "cheap",
                    "split_module": "cheap",
                    "architecture_review": "balanced",
                },
            },
        }
    },
}


def export_config_schema() -> dict[str, Any]:
    schema = RedslConfigDocument.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://redsl.io/schemas/config/v1.json"
    schema.setdefault("title", "RedslConfig")
    return schema


def export_proposal_schema() -> dict[str, Any]:
    schema = ConfigChangeProposal.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://redsl.io/schemas/config/proposal/v1.json"
    schema.setdefault("title", "ConfigChangeProposal")
    return schema


CONFIG_AGENT_TOOLS: list[dict[str, Any]] = [
    {
        "name": "inspect_config",
        "description": "Odczytaj aktualny stan fragmentu configu zanim zaproponujesz zmianę.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "search_config_schema",
        "description": "Znajdź ścieżki w config standard pasujące do opisu użytkownika.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "propose_changes",
        "description": "Zwróć ustrukturyzowaną propozycję zmian. Nie zapisuj bezpośrednio.",
        "input_schema": export_proposal_schema(),
    },
    {
        "name": "test_api_key",
        "description": "Zweryfikuj klucz API bez ujawniania jego wartości.",
        "input_schema": {
            "type": "object",
            "properties": {
                "provider": {"type": "string", "enum": ["openrouter", "anthropic", "openai"]},
            },
            "required": ["provider"],
        },
    },
]


def search_schema_matches(
    query: str, *, catalog: list[PathCatalogEntry] | None = None
) -> list[dict[str, Any]]:
    """Return catalog entries matching *query* across path/title/description/aliases."""
    needle = query.strip().lower()
    if not needle:
        return []

    entries = catalog or CONFIG_PATH_CATALOG
    matches: list[dict[str, Any]] = []
    for entry in entries:
        haystack = " ".join(
            [entry.path, entry.title, entry.description, " ".join(entry.aliases)]
        ).lower()
        if needle in haystack:
            matches.append(entry.as_dict())
    return matches


def config_doc_to_yaml(document: RedslConfigDocument) -> str:
    import yaml

    data = document.model_dump(mode="json")
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


def proposal_to_yaml(proposal: ConfigChangeProposal) -> str:
    import yaml

    data = proposal.model_dump(mode="json")
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


__all__ = [
    "CONFIG_AGENT_TOOLS",
    "CONFIG_AGENT_VERSION",
    "CONFIG_PATH_CATALOG",
    "CONFIG_PROPOSAL_KIND",
    "CONFIG_STANDARD_API_VERSION",
    "CONFIG_STANDARD_KIND",
    "ConfigChange",
    "ConfigChangeProposal",
    "ConfigMetadata",
    "ConfigOrigin",
    "ConfigPreconditions",
    "ConfigValidationState",
    "CostWeights",
    "CodingConfig",
    "CodingTiers",
    "DefaultOperationTiers",
    "DEFAULT_PROFILE_OVERRIDES",
    "LLMPolicy",
    "PathCatalogEntry",
    "ProposalMetadata",
    "RedslConfigDocument",
    "RedslConfigSpec",
    "RegistrySource",
    "SecretRotation",
    "SecretSpec",
    "build_default_config",
    "config_doc_to_yaml",
    "export_config_schema",
    "export_proposal_schema",
    "proposal_to_yaml",
    "search_schema_matches",
]
