"""Base class and implementations for model registry sources."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from ..models import ModelInfo


class ModelRegistrySource(ABC):
    """Abstract base class for model registry sources."""

    name: str
    enabled: bool = True

    @abstractmethod
    def fetch(self) -> list[ModelInfo]:
        """Fetch models from this source."""
        ...

    def _http_get(
        self,
        url: str,
        headers: dict | None = None,
        timeout: int = 10,
    ) -> dict:
        """Make HTTP GET request and return JSON."""
        with httpx.Client(timeout=timeout) as client:
            r = client.get(url, headers=headers or {})
            r.raise_for_status()
            return r.json()


class OpenRouterSource(ModelRegistrySource):
    """OpenRouter public API - no auth required, ~300+ models."""

    name = "openrouter"
    URL = "https://openrouter.ai/api/v1/models"

    def fetch(self) -> list[ModelInfo]:
        """Fetch models from OpenRouter with full pricing and capabilities."""
        from ..models import ModelInfo, Pricing, Capabilities, QualitySignals

        data = self._http_get(self.URL)
        programming_ids = self._fetch_programming_category()

        out = []
        for m in data.get("data", []):
            created = m.get("created")
            release_date = datetime.utcfromtimestamp(created) if created else None
            model_id = m["id"]  # e.g., "openai/gpt-4o"
            provider = model_id.split("/")[0] if "/" in model_id else "unknown"

            pricing_raw = m.get("pricing", {})
            arch = m.get("architecture", {})
            top_provider = m.get("top_provider", {})
            supported_params = m.get("supported_parameters", [])

            out.append(
                ModelInfo(
                    id=model_id,
                    provider=provider,
                    release_date=release_date,
                    context_length=m.get("context_length"),
                    sources=(self.name,),
                    source_dates={self.name: release_date} if release_date else {},
                    pricing=Pricing(
                        prompt=self._to_decimal(pricing_raw.get("prompt")),
                        completion=self._to_decimal(pricing_raw.get("completion")),
                        request=self._to_decimal(pricing_raw.get("request")),
                        image=self._to_decimal(pricing_raw.get("image")),
                    ),
                    capabilities=Capabilities(
                        context_length=m.get("context_length"),
                        supports_tool_calling="tools" in supported_params,
                        supports_json_mode="response_format" in supported_params,
                        supports_streaming=True,  # OR streaming jest uniwersalne
                        supports_vision="image" in (arch.get("input_modalities") or []),
                        output_modalities=tuple(arch.get("output_modalities", ["text"])),
                        max_output_tokens=top_provider.get("max_completion_tokens"),
                    ),
                    quality=QualitySignals(
                        openrouter_category_programming=(model_id in programming_ids),
                    ),
                    raw=m,
                )
            )
        return out

    def _fetch_programming_category(self) -> set[str]:
        """Fetch model IDs from OpenRouter programming category."""
        try:
            data = self._http_get(f"{self.URL}?category=programming")
            return {m["id"] for m in data.get("data", [])}
        except Exception:
            return set()

    def _to_decimal(self, value) -> Decimal | None:
        """Convert value to Decimal, handling None and empty strings."""
        if value is None or value == "":
            return None
        try:
            return Decimal(str(value))
        except Exception:
            return None


class ModelsDevSource(ModelRegistrySource):
    """Models.dev community API - public, ~200+ models."""

    name = "models_dev"
    URL = "https://models.dev/api.json"

    def fetch(self) -> list[ModelInfo]:
        """Fetch models from models.dev."""
        from ..models import ModelInfo

        data = self._http_get(self.URL)
        out = []
        # Structure: { "providers": { "openai": { "models": { "gpt-4o": {...} } } } }
        for provider, pdata in data.get("providers", {}).items():
            for model_name, mdata in pdata.get("models", {}).items():
                rd_str = mdata.get("release_date")
                _dt = datetime.fromisoformat(rd_str) if rd_str else None
                release_date = _dt.replace(tzinfo=timezone.utc) if _dt is not None and _dt.tzinfo is None else _dt
                model_id = f"{provider}/{model_name}"
                out.append(
                    ModelInfo(
                        id=model_id,
                        provider=provider,
                        release_date=release_date,
                        deprecated=mdata.get("deprecated", False),
                        context_length=mdata.get("context_length"),
                        sources=(self.name,),
                        source_dates={self.name: release_date} if release_date else {},
                        raw=mdata,
                    )
                )
        return out


class OpenAIProviderSource(ModelRegistrySource):
    """Native OpenAI API - requires key, authoritative for OpenAI models."""

    name = "openai_native"
    URL = "https://api.openai.com/v1/models"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.enabled = bool(api_key)

    def fetch(self) -> list[ModelInfo]:
        """Fetch models from OpenAI."""
        from ..models import ModelInfo

        if not self.api_key:
            return []
        data = self._http_get(
            self.URL, headers={"Authorization": f"Bearer {self.api_key}"}
        )
        out = []
        for m in data.get("data", []):
            created = m.get("created")
            release_date = datetime.fromtimestamp(created, tz=timezone.utc) if created else None
            model_id = f"openai/{m['id']}"
            out.append(
                ModelInfo(
                    id=model_id,
                    provider="openai",
                    release_date=release_date,
                    sources=(self.name,),
                    source_dates={self.name: release_date} if release_date else {},
                    raw=m,
                )
            )
        return out


class AnthropicProviderSource(ModelRegistrySource):
    """Native Anthropic API - requires key, authoritative for Claude models."""

    name = "anthropic_native"
    URL = "https://api.anthropic.com/v1/models"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.enabled = bool(api_key)

    def fetch(self) -> list[ModelInfo]:
        """Fetch models from Anthropic."""
        from ..models import ModelInfo

        if not self.api_key:
            return []
        data = self._http_get(
            self.URL,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        out = []
        for m in data.get("data", []):
            rd_str = m.get("created_at")
            release_date = (
                datetime.fromisoformat(rd_str.replace("Z", "+00:00"))
                if rd_str
                else None
            )
            model_id = f"anthropic/{m['id']}"
            out.append(
                ModelInfo(
                    id=model_id,
                    provider="anthropic",
                    release_date=release_date,
                    sources=(self.name,),
                    source_dates={self.name: release_date} if release_date else {},
                    raw=m,
                )
            )
        return out


class AiderLeaderboardSource:
    """
    Drugie niezależne źródło — benchmark polyglot od Aider.
    Wzbogaca istniejące modele o quality.aider_polyglot_score.
    NIE tworzy nowych modeli (to ModelInfoEnricher, nie Source).
    """

    name = "aider"
    # Aider leaderboard URLs - they change frequently, try multiple
    URLS = [
        "https://raw.githubusercontent.com/Aider-AI/aider/main/aider/website/assets/polyglot-leaderboard.json",
        "https://aider.chat/assets/polyglot-leaderboard.json",
        "https://raw.githubusercontent.com/Aider-AI/aider/main/aider/website/_data/polyglot_leaderboard.yml",
    ]

    def enrich(self, models: dict[str, ModelInfo]) -> dict[str, ModelInfo]:
        """Enrich existing models with Aider polyglot scores."""
        from dataclasses import replace
        from ..models import QualitySignals
        import logging

        log = logging.getLogger(__name__)
        data = None

        # Try multiple URLs
        for url in self.URLS:
            try:
                data = self._http_get(url)
                log.debug("Aider leaderboard loaded from: %s", url)
                break
            except Exception as e:
                log.debug("Aider URL failed %s: %s", url, e)
                continue

        if data is None:
            log.warning("Aider leaderboard fetch failed from all URLs")
            return models

        # Map: model_name → score (pass_rate_2 or similar field)
        aider_scores = {}
        for row in data if isinstance(data, list) else data.get("data", []):
            model_name = row.get("model")
            score = row.get("pass_rate_2") or row.get("score") or row.get("percent")
            if model_name and score is not None:
                try:
                    aider_scores[model_name] = float(score)
                except (ValueError, TypeError):
                    continue

        # Aider uses different names than OpenRouter — need mapping
        updated = {}
        for mid, info in models.items():
            score = self._match_score(mid, aider_scores)
            if score is None:
                updated[mid] = info
                continue
            updated[mid] = replace(
                info,
                quality=replace(
                    info.quality,
                    aider_polyglot_score=score,
                ),
                sources=info.sources + (self.name,),
            )
        return updated

    def _http_get(self, url: str, headers: dict | None = None, timeout: int = 10) -> dict:
        """Make HTTP GET request and return JSON."""
        with httpx.Client(timeout=timeout) as client:
            r = client.get(url, headers=headers or {})
            r.raise_for_status()
            return r.json()

    def _match_score(self, model_id: str, aider_scores: dict) -> float | None:
        """Match OpenRouter model ID to Aider score."""
        # Exact match
        if model_id in aider_scores:
            return aider_scores[model_id]

        # Strip provider prefix
        bare = model_id.split("/", 1)[-1] if "/" in model_id else model_id
        if bare in aider_scores:
            return aider_scores[bare]

        # Common provider aliases
        aliases = {
            "claude-sonnet-4-5": "claude-sonnet-4-5",
            "claude-sonnet-4-5": "claude-3.5-sonnet",
            "claude-haiku-4-5": "claude-haiku-4-5",
            "gpt-5.4": "gpt-4",
            "gpt-5.4-mini": "gpt-4-mini",
        }
        for alias, target in aliases.items():
            if alias in model_id or bare.startswith(alias):
                if target in aider_scores:
                    return aider_scores[target]

        # Fuzzy: 'claude-sonnet-4-5' vs 'claude-sonnet-4-5-20250929'
        for k, v in aider_scores.items():
            if k.startswith(bare) or bare.startswith(k):
                return v
            # Also try without version suffixes
            k_base = k.split("-")[0] if "-" in k else k
            bare_base = bare.split("-")[0] if "-" in bare else bare
            if k_base == bare_base:
                return v
        return None
