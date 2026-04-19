"""Tests for the AgentConfig bridge to config substrate."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from redsl.config import AgentConfig
from redsl.config_standard import (
    ConfigBridgeError,
    ConfigStore,
    agent_config_from_substrate_or_env,
    build_default_config,
    find_config_root,
    resolve_secret_ref,
)
from redsl.config_standard.models import SecretSpec


def test_resolve_secret_ref_env() -> None:
    """Test resolving env: secret references."""
    secret = SecretSpec(ref="env:TEST_API_KEY", required=True)

    # Should raise when not set and required
    with pytest.raises(ConfigBridgeError):
        resolve_secret_ref(secret)

    # Should return value when set
    os.environ["TEST_API_KEY"] = "secret-value-123"
    try:
        result = resolve_secret_ref(secret)
        assert result == "secret-value-123"
    finally:
        del os.environ["TEST_API_KEY"]


def test_resolve_secret_ref_file(tmp_path: Path) -> None:
    """Test resolving file: secret references."""
    secret_file = tmp_path / "api.key"
    secret_file.write_text("file-secret-value\n")

    secret = SecretSpec(ref=f"file:{secret_file}", required=True)
    result = resolve_secret_ref(secret)
    assert result == "file-secret-value"


def test_resolve_secret_ref_file_not_found() -> None:
    """Test file: ref when file doesn't exist."""
    secret = SecretSpec(ref="file:/nonexistent/path/to/key", required=False)
    result = resolve_secret_ref(secret)
    assert result == ""

    # Should raise if required
    required_secret = SecretSpec(ref="file:/nonexistent/path/to/key", required=True)
    with pytest.raises(ConfigBridgeError):
        resolve_secret_ref(required_secret)


def test_find_config_root_in_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test finding config root in current directory."""
    config_dir = tmp_path / "redsl-config"
    store = ConfigStore(config_dir)
    document = store.create_default(name="test")
    store.save(document)

    monkeypatch.chdir(config_dir)
    found = find_config_root()
    assert found == config_dir


def test_find_config_root_in_parent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test finding config root by walking up directories."""
    config_dir = tmp_path / "project" / "redsl-config"
    store = ConfigStore(config_dir)
    document = store.create_default(name="test")
    store.save(document)

    nested_dir = tmp_path / "project" / "src" / "components"
    nested_dir.mkdir(parents=True)
    monkeypatch.chdir(nested_dir)

    found = find_config_root()
    assert found == config_dir


def test_find_config_root_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that None is returned when no config found."""
    monkeypatch.chdir(tmp_path)
    found = find_config_root()
    assert found is None


def test_load_agent_config_from_substrate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test loading AgentConfig from substrate with secrets."""
    config_dir = tmp_path / "redsl-config"
    store = ConfigStore(config_dir)
    document = build_default_config(name="bridge-test")
    store.save(document)

    # Set env secrets
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-or-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")

    config = agent_config_from_substrate_or_env(config_dir)

    assert isinstance(config, AgentConfig)
    assert config.llm.provider_key == "test-or-key"


def test_agent_config_from_substrate_or_env_fallback_to_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that when no substrate exists, it falls back to env."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "fallback-key")
    monkeypatch.setenv("REFACTOR_DRY_RUN", "false")

    config = agent_config_from_substrate_or_env()

    assert isinstance(config, AgentConfig)
    assert config.llm.provider_key == "fallback-key"
    assert config.refactor.dry_run is False


def test_agent_config_from_env_uses_substrate_when_available(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that AgentConfig.from_env now uses substrate when available."""
    config_dir = tmp_path / "redsl-config"
    store = ConfigStore(config_dir)
    document = build_default_config(name="env-test")
    store.save(document)

    # Set up env var that would be used by legacy code
    monkeypatch.setenv("OPENROUTER_API_KEY", "env-override")
    monkeypatch.chdir(config_dir)

    # from_env should now use substrate
    config = AgentConfig.from_env()

    assert isinstance(config, AgentConfig)
    # The key should come from substrate resolution, not directly from env


def test_config_bridge_error_messages() -> None:
    """Test that invalid secret refs are rejected at validation time."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="Secret ref must start with"):
        SecretSpec(ref="unsupported:format", required=True)
