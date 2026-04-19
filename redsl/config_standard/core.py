"""Core config document models."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

CONFIG_STANDARD_API_VERSION = "redsl.config/v1"
CONFIG_STANDARD_KIND = "RedslConfig"
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


# Forward imports to avoid circular deps
from pathlib import Path  # noqa: E402
from .secrets import SecretSpec  # noqa: E402
from .llm_policy import LLMPolicy, CodingConfig  # noqa: E402


class RedslConfigSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    llm_policy: LLMPolicy = Field(default_factory=LLMPolicy)
    coding: CodingConfig = Field(default_factory=CodingConfig)
    registry_sources: list[RegistrySource] = Field(default_factory=list)
    cache: CacheConfig = Field(default_factory=CacheConfig)


class RedslConfigDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    apiVersion: str = CONFIG_STANDARD_API_VERSION
    kind: str = CONFIG_STANDARD_KIND
    metadata: ConfigMetadata
    profile: str = "production"
    secrets: dict[str, SecretSpec] = Field(default_factory=dict)
    spec: RedslConfigSpec = Field(default_factory=RedslConfigSpec)

    def fingerprint_payload(self) -> dict[str, Any]:
        """Return only the ``spec`` subtree — the canonical fingerprint payload.

        Two configs with the same fingerprint have identical operational behaviour
        regardless of metadata, secrets refs or profile name.
        """
        return {
            "apiVersion": self.apiVersion,
            "kind": self.kind,
            "spec": self.model_dump(mode="json")["spec"],
        }

    def compute_fingerprint(self) -> str:
        raw = json.dumps(
            self.fingerprint_payload(), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


__all__ = [
    "CONFIG_AGENT_VERSION",
    "CONFIG_STANDARD_API_VERSION",
    "CONFIG_STANDARD_KIND",
    "CacheConfig",
    "ConfigMetadata",
    "ConfigOrigin",
    "RedslConfigDocument",
    "RedslConfigSpec",
    "RegistrySource",
    "_utcnow",
]
