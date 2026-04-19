"""Pydantic models and schema helpers for the redsl config standard.

This module is now a compatibility re-export wrapper.
The actual implementations have been split into submodules:
- core: ConfigOrigin, ConfigMetadata, RedslConfigDocument, etc.
- secrets: SecretRotation, SecretSpec
- llm_policy: LLMPolicy, CodingConfig, CostWeights, etc.
- proposals: ConfigChange, ConfigChangeProposal, etc.
- catalog: PathCatalogEntry, CONFIG_PATH_CATALOG, RISK_MATRIX, etc.
- profiles: build_default_config, DEFAULT_PROFILE_OVERRIDES, etc.
"""

from __future__ import annotations

# Rebuild CONFIG_AGENT_TOOLS with dynamic schema
from . import proposals as _proposals_module
from .catalog import (
    AUDIT_LOG_ALWAYS,
    CONFIG_PATH_CATALOG,
    CONFIRMATION_REQUIRED,
    RISK_MATRIX,
    PathCatalogEntry,
    get_risk_level,
    search_schema_matches,
)
from .core import (
    CONFIG_AGENT_VERSION,
    CONFIG_STANDARD_API_VERSION,
    CONFIG_STANDARD_KIND,
    CacheConfig,
    ConfigMetadata,
    ConfigOrigin,
    RedslConfigDocument,
    RedslConfigSpec,
    RegistrySource,
    _utcnow,
)
from .llm_policy import (
    CodingConfig,
    CodingTiers,
    CostWeights,
    DefaultOperationTiers,
    LLMPolicy,
)
from .profiles import (
    DEFAULT_PROFILE_OVERRIDES,
    build_default_config,
    config_doc_to_yaml,
    export_config_schema,
)
from .proposals import (
    CONFIG_PROPOSAL_KIND,
    ConfigChange,
    ConfigChangeProposal,
    ConfigPreconditions,
    ConfigValidationState,
    ProposalMetadata,
    export_proposal_schema,
    proposal_to_yaml,
)
from .secrets import SecretRotation, SecretSpec

CONFIG_AGENT_TOOLS = [
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
        "input_schema": _proposals_module.export_proposal_schema(),
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

__all__ = [
    "AUDIT_LOG_ALWAYS",
    "CONFIG_AGENT_TOOLS",
    "CONFIG_AGENT_VERSION",
    "CONFIG_PATH_CATALOG",
    "CONFIG_PROPOSAL_KIND",
    "CONFIG_STANDARD_API_VERSION",
    "CONFIG_STANDARD_KIND",
    "CONFIRMATION_REQUIRED",
    "RISK_MATRIX",
    "CacheConfig",
    "CodingConfig",
    "CodingTiers",
    "ConfigChange",
    "ConfigChangeProposal",
    "ConfigMetadata",
    "ConfigOrigin",
    "ConfigPreconditions",
    "ConfigValidationState",
    "CostWeights",
    "DEFAULT_PROFILE_OVERRIDES",
    "DefaultOperationTiers",
    "LLMPolicy",
    "PathCatalogEntry",
    "ProposalMetadata",
    "RedslConfigDocument",
    "RedslConfigSpec",
    "RegistrySource",
    "SecretRotation",
    "SecretSpec",
    "_utcnow",
    "build_default_config",
    "config_doc_to_yaml",
    "export_config_schema",
    "export_proposal_schema",
    "get_risk_level",
    "proposal_to_yaml",
    "search_schema_matches",
]
