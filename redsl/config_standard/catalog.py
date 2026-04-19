"""Config path catalog and risk matrix."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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


RISK_MATRIX: dict[str, str] = {
    "spec.llm_policy.max_age_days": "low",
    "spec.llm_policy.mode": "low",
    "spec.llm_policy.strict": "medium",
    "spec.llm_policy.unknown_release": "medium",
    "spec.llm_policy.min_sources_agree": "medium",
    "spec.coding.cost_weights": "low",
    "spec.coding.tiers.cheap": "low",
    "spec.coding.tiers.balanced": "low",
    "spec.coding.tiers.premium": "low",
    "spec.coding.default_tiers.extract_function": "low",
    "spec.coding.default_tiers.split_module": "low",
    "spec.coding.default_tiers.architecture_review": "low",
    "spec.coding.max_cost_per_call_usd": "medium",
    "spec.coding.require_tool_calling": "low",
    "spec.coding.min_context": "low",
    "spec.registry_sources": "medium",
    "spec.cache.path": "low",
    "spec.cache.ttl_seconds": "low",
    "spec.cache.stale_grace_seconds": "low",
    "spec.secrets.*.ref": "high",
    "spec.secrets.*": "critical",
    "profile": "high",
    "metadata.version": "low",
    "apiVersion": "critical",
}

CONFIRMATION_REQUIRED: frozenset[str] = frozenset({"high", "critical"})
AUDIT_LOG_ALWAYS: frozenset[str] = frozenset({"medium", "high", "critical"})


def get_risk_level(path: str) -> str:
    """Return risk level for a config path. Falls back to 'low' for unknown paths.

    Supports wildcard suffix matching (e.g. spec.secrets.mykey.ref → spec.secrets.*.ref).
    Any unknown path that starts with a protected prefix returns that prefix's risk level.
    """
    if path in RISK_MATRIX:
        return RISK_MATRIX[path]

    parts = path.split(".")
    if len(parts) >= 2:
        wildcard = ".".join(parts[:-2] + ["*"] + [parts[-1]])
        if wildcard in RISK_MATRIX:
            return RISK_MATRIX[wildcard]
        wildcard2 = ".".join(parts[:-1] + ["*"])
        if wildcard2 in RISK_MATRIX:
            return RISK_MATRIX[wildcard2]

    return "unknown"


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


__all__ = [
    "AUDIT_LOG_ALWAYS",
    "CONFIG_PATH_CATALOG",
    "CONFIRMATION_REQUIRED",
    "RISK_MATRIX",
    "PathCatalogEntry",
    "get_risk_level",
    "search_schema_matches",
]
