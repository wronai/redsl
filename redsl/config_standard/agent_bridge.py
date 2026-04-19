"""Bridge between config substrate and legacy AgentConfig."""

from __future__ import annotations

import json
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

    # vault: and doppler: — attempt resolution via env-based fallback or SDK
    if ref.startswith("vault:"):
        return _resolve_vault_ref(ref, secret)

    if ref.startswith("doppler:"):
        return _resolve_doppler_ref(ref, secret)

    raise ConfigBridgeError(f"Unsupported secret ref format: {ref}")


def _resolve_vault_ref(ref: str, secret: SecretSpec) -> str:  # noqa: F821
    """Resolve a ``vault:<path>#<key>`` secret reference via HashiCorp Vault.

    Supports two resolution strategies (tried in order):
    1. Environment variable fallback — ``VAULT_SECRET_<UPPER_KEY>``
    2. ``hvac`` SDK if installed and ``VAULT_ADDR`` / ``VAULT_TOKEN`` are set.

    Format: ``vault:secret/data/myapp#my_key``
    """
    # Strip scheme
    remainder = ref[len("vault:"):]
    path, _, field = remainder.partition("#")
    field = field or "value"

    # Strategy 1: env fallback (useful for CI/CD that injects vault secrets as env vars)
    env_key = f"VAULT_SECRET_{field.upper()}"
    env_val = os.getenv(env_key, "")
    if env_val:
        return env_val

    # Strategy 2: hvac SDK
    vault_addr = os.getenv("VAULT_ADDR", "")
    vault_token = os.getenv("VAULT_TOKEN", "")
    if vault_addr and vault_token:
        try:
            import hvac  # type: ignore[import-untyped]

            client = hvac.Client(url=vault_addr, token=vault_token)
            # Support KV v2 (secret/data/path)
            if "/data/" in path:
                mount_point, _, secret_path = path.partition("/data/")
                response = client.secrets.kv.v2.read_secret_version(
                    path=secret_path, mount_point=mount_point
                )
                data: dict[str, Any] = response["data"]["data"]
            else:
                response = client.read(path)
                data = (response or {}).get("data", {}) or {}

            value = str(data.get(field, ""))
            if not value and secret.required:
                raise ConfigBridgeError(
                    f"Key {field!r} not found in Vault path {path!r} (ref: {ref})"
                )
            return value
        except ImportError:
            pass  # hvac not installed — fall through to error

    if secret.required:
        raise ConfigBridgeError(
            f"Cannot resolve vault ref {ref!r}: "
            "set VAULT_ADDR + VAULT_TOKEN or install 'hvac', "
            f"or export {env_key} as env fallback."
        )
    return ""


def _resolve_doppler_ref(ref: str, secret: SecretSpec) -> str:  # noqa: F821
    """Resolve a ``doppler:<project>/<config>/<secret>`` reference.

    Supports two resolution strategies (tried in order):
    1. Environment variable — Doppler CLI injects secrets as env vars by name.
    2. Doppler REST API via ``DOPPLER_TOKEN``.

    Format: ``doppler:myproject/production/OPENROUTER_API_KEY``
    """
    remainder = ref[len("doppler:"):]
    # Last segment is the secret name
    parts = remainder.split("/")
    if len(parts) < 1:
        raise ConfigBridgeError(f"Invalid doppler ref format: {ref!r}")

    secret_name = parts[-1]

    # Strategy 1: direct env var (Doppler CLI / doppler run injects these)
    env_val = os.getenv(secret_name, "")
    if env_val:
        return env_val

    # Strategy 2: Doppler REST API
    doppler_token = os.getenv("DOPPLER_TOKEN", "")
    if doppler_token and len(parts) >= 3:
        project, config_name = parts[0], parts[1]
        try:
            import urllib.error
            import urllib.request

            url = (
                f"https://api.doppler.com/v3/configs/config/secret"
                f"?project={project}&config={config_name}&name={secret_name}"
            )
            req = urllib.request.Request(  # noqa: S310
                url,
                headers={"Authorization": f"Bearer {doppler_token}"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
                body = json.loads(resp.read())
            value = (body.get("secret") or {}).get("computed", "") or ""
            if not value and secret.required:
                raise ConfigBridgeError(
                    f"Doppler returned empty value for {secret_name!r} (ref: {ref})"
                )
            return value
        except (ImportError, Exception) as exc:
            if secret.required:
                raise ConfigBridgeError(
                    f"Doppler API call failed for ref {ref!r}: {exc}"
                ) from exc
            return ""

    if secret.required:
        raise ConfigBridgeError(
            f"Cannot resolve doppler ref {ref!r}: "
            "export DOPPLER_TOKEN (and ensure project/config/name format) "
            f"or export {secret_name} directly as an env var."
        )
    return ""


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
        return "moonshotai/kimi-k2.5"

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
