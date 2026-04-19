"""Profile defaults and config builders."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .core import CONFIG_AGENT_VERSION, ConfigMetadata, RedslConfigDocument
from .llm_policy import LLMPolicy, CodingConfig, CodingTiers, CostWeights, DefaultOperationTiers
from .secrets import SecretSpec
from .core import RedslConfigSpec, RegistrySource, CacheConfig


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


def config_doc_to_yaml(document: RedslConfigDocument) -> str:
    data = document.model_dump(mode="json")
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


def export_config_schema() -> dict[str, Any]:
    import json

    schema = RedslConfigDocument.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://redsl.io/schemas/config/v1.json"
    schema.setdefault("title", "RedslConfig")
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
        "input_schema": {},  # Populated dynamically
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
    "CONFIG_AGENT_TOOLS",
    "CONFIG_AGENT_VERSION",
    "DEFAULT_PROFILE_OVERRIDES",
    "build_default_config",
    "config_doc_to_yaml",
    "export_config_schema",
]
