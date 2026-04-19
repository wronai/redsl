"""Bridge between config substrate and legacy AgentConfig."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from redsl.config import AgentConfig, LLMConfig, RefactorConfig

from .models import RedslConfigDocument, SecretSpec
from .store import ConfigStore


class ConfigBridgeError(RuntimeError):
    """Raised when config bridge cannot resolve configuration."""


def resolve_secret_ref(secret: SecretSpec) -> str:
    """Resolve a secret reference to its actual value."""
    ref = secret.ref

    if ref.startswith("env:"):
        env_var = ref[4:]
        value = os.getenv(env_var, "")
        if secret.required and not value:
            raise ConfigBridgeError(f"Required secret {env_var} not found in environment")
        return value

    if ref.startswith("file:"):
        file_path = Path(ref[5:]).expanduser()
        if not file_path.exists():
            if secret.required:
                raise ConfigBridgeError(f"Required secret file not found: {file_path}")
            return ""
        try:
            return file_path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            if secret.required:
                raise ConfigBridgeError(f"Cannot read secret file {file_path}: {exc}") from exc
            return ""

    # vault: and doppler: not yet implemented - treat as empty/unresolved
    if ref.startswith(("vault:", "doppler:")):
        if secret.required:
            raise ConfigBridgeError(f"Secret provider not implemented for ref: {ref}")
        return ""

    raise ConfigBridgeError(f"Unsupported secret ref format: {ref}")


def find_config_root(start_path: Path | None = None) -> Path | None:
    """Find redsl-config directory by walking up from start_path or cwd."""
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()

    # First check: is current dir a config root?
    if (current / "redsl.config.yaml").exists():
        return current

    # Walk up looking for redsl-config/ subdirectory or redsl.config.yaml
    for parent in [current] + list(current.parents):
        config_dir = parent / "redsl-config"
        if (config_dir / "redsl.config.yaml").exists():
            return config_dir
        if (parent / "redsl.config.yaml").exists():
            return parent

    return None


def load_agent_config_from_substrate(
    config_root: Path | None = None,
    profile: str | None = None,
) -> AgentConfig:
    """Load AgentConfig from config substrate, resolving secrets."""
    if config_root is None:
        config_root = find_config_root()

    if config_root is None:
        raise ConfigBridgeError("No config root found (tried cwd and parents)")

    store = ConfigStore(config_root)

    try:
        document = store.load()
    except FileNotFoundError as exc:
        raise ConfigBridgeError(f"Config manifest not found at {store.manifest_path}") from exc

    # Apply profile if specified or use document's profile
    active_profile = profile or document.profile
    if active_profile and active_profile != "default":
        profile_data = store.load_profile(active_profile)
        if profile_data:
            # Re-apply profile overrides
            from .models import deep_merge

            base_data = document.model_dump(mode="json")
            merged = deep_merge(base_data, profile_data)
            document = store.load_document(merged)

    return _document_to_agent_config(document)


def _document_to_agent_config(document: RedslConfigDocument) -> AgentConfig:
    """Convert RedslConfigDocument to legacy AgentConfig."""
    spec = document.spec

    # Resolve secrets
    secrets: dict[str, str] = {}
    for name, secret_spec in document.secrets.items():
        try:
            secrets[name] = resolve_secret_ref(secret_spec)
        except ConfigBridgeError:
            if secret_spec.required:
                raise
            secrets[name] = ""

    # Determine primary provider key
    provider_key = (
        secrets.get("openrouter_api_key")
        or secrets.get("anthropic_api_key")
        or secrets.get("openai_api_key")
        or ""
    )

    # Map coding tiers to model selection hints (stored in LLMConfig for now)
    # This is a bridge - the new system has richer model policy
    llm_policy = spec.llm_policy

    # Choose default model based on policy
    default_model = _select_model_from_policy(llm_policy, secrets)

    return AgentConfig(
        llm=LLMConfig(
            model=default_model,
            temperature=0.3,  # Not yet in substrate - use default
            max_tokens=4096,
            reflection_model=default_model,
            reflection_temperature=0.2,
            provider_key=provider_key,
        ),
        refactor=RefactorConfig(
            max_patch_lines=200,  # Not yet in substrate
            dry_run=True,  # Safe default for substrate
            auto_approve=False,  # Safe default
            backup_enabled=True,
            max_iterations=3,
            reflection_rounds=2,
            output_dir=spec.cache.path.parent / "refactor_output",
        ),
    )


def _select_model_from_policy(llm_policy: Any, secrets: dict[str, str]) -> str:
    """Select appropriate model based on policy and available keys."""
    # Priority: OpenRouter -> Anthropic -> OpenAI -> fallback
    if secrets.get("openrouter_api_key"):
        return "openrouter/x-ai/grok-code-fast-1"
    if secrets.get("anthropic_api_key"):
        return "anthropic/claude-sonnet-4-20250514"
    if secrets.get("openai_api_key"):
        return "openai/gpt-5.4-mini"

    # Fallback - will likely fail but maintains structure
    return "openrouter/x-ai/grok-code-fast-1"


def agent_config_from_substrate_or_env(
    config_root: Path | None = None,
    profile: str | None = None,
) -> AgentConfig:
    """Try substrate first, fall back to env-based config."""
    # If explicit config root provided, must use substrate
    if config_root is not None:
        return load_agent_config_from_substrate(config_root, profile)

    # Try to find substrate config
    found_root = find_config_root()
    if found_root is not None:
        try:
            return load_agent_config_from_substrate(found_root, profile)
        except ConfigBridgeError:
            # Fall through to env-based
            pass

    # Fall back to legacy env-based loading
    return AgentConfig.from_env()


__all__ = [
    "ConfigBridgeError",
    "agent_config_from_substrate_or_env",
    "find_config_root",
    "load_agent_config_from_substrate",
    "resolve_secret_ref",
]
