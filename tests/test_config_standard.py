from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from redsl.config_standard import (
    ConfigApplier,
    ConfigChange,
    ConfigChangeProposal,
    ConfigPreconditions,
    ConfigStore,
    ProposalMetadata,
    SecretInterceptor,
    build_default_config,
    search_schema_matches,
)


def test_secret_interceptor_redacts_and_resolves() -> None:
    interceptor = SecretInterceptor()
    secret = "sk-or-v1-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    redacted, matches = interceptor.redact(f"token={secret}")

    assert secret not in redacted
    assert "[REDACTED_SECRET_1]" in redacted
    assert matches[0].original == secret
    assert interceptor.resolve(matches[0].placeholder) == secret


def test_store_save_load_validate_and_clone(tmp_path: Path) -> None:
    root = tmp_path / "redsl-config"
    store = ConfigStore(root)
    document = store.create_default(name="demo-config", profile="minimal-cost")
    store.save(document)

    loaded = store.load()
    assert loaded.metadata.name == "demo-config"
    assert loaded.profile == "minimal-cost"
    assert loaded.metadata.fingerprint == document.metadata.fingerprint
    assert loaded.spec.coding.tiers.balanced == pytest.approx(1.0)
    assert store.validate(loaded) == []
    assert store.schema_path.exists()
    assert store.proposal_schema_path.exists()

    matches = search_schema_matches("oszczędzać kasę")
    assert any(match["path"] == "spec.coding.tiers.balanced" for match in matches)

    clone_root = tmp_path / "clone-config"
    clone_store = ConfigStore(clone_root)
    cloned = clone_store.clone_from(root, profile="production", replace_secrets=True)
    clone_store.save(cloned)

    reloaded = clone_store.load()
    assert reloaded.profile == "production"
    assert reloaded.metadata.origin.cloned_from is not None
    assert reloaded.secrets["openrouter_api_key"].ref.startswith("env:REPLACE_ME_")


def test_applier_apply_and_rollback(tmp_path: Path) -> None:
    root = tmp_path / "redsl-config"
    store = ConfigStore(root)
    document = build_default_config(name="apply-demo")
    store.save(document)

    proposal = ConfigChangeProposal(
        metadata=ProposalMetadata(
            source="user said: lower balanced tier to $2",
            risk_level="low",
        ),
        changes=[
            ConfigChange(
                op="set",
                path="spec.coding.tiers.balanced",
                current_value=document.spec.coding.tiers.balanced,
                new_value=2.0,
                rationale="Lower balanced tier budget",
                confidence=0.99,
                risk_level="low",
            )
        ],
        summary="Lower balanced tier budget",
        preconditions=ConfigPreconditions(
            config_version=document.metadata.version,
            config_fingerprint=document.metadata.fingerprint,
        ),
    )

    applier = ConfigApplier(store)
    result = applier.apply(proposal)

    assert result.success is True
    assert result.new_version == 2
    assert result.backup_path.exists()
    assert store.load().spec.coding.tiers.balanced == pytest.approx(2.0)

    history = store.history()
    assert history[-1]["version"] == 2
    assert history[-1]["changes"][0]["path"] == "spec.coding.tiers.balanced"

    rollback_result = applier.rollback(target_version=1)
    assert rollback_result.success is True
    assert store.load().spec.coding.tiers.balanced == pytest.approx(3.0)
    assert store.load().metadata.version == 3

    with open(store.manifest_path, encoding="utf-8") as handle:
        manifest = yaml.safe_load(handle)
    assert manifest["spec"]["coding"]["tiers"]["balanced"] == pytest.approx(3.0)


def test_store_history_can_be_serialized_as_json(tmp_path: Path) -> None:
    root = tmp_path / "redsl-config"
    store = ConfigStore(root)
    document = store.create_default(name="history-demo")
    store.save(document)
    store.append_history(
        {
            "ts": document.metadata.updated.isoformat(),
            "version": document.metadata.version,
            "actor": "tester",
            "user": "unit-test",
            "source": "manual",
            "changes": [],
            "risk": "low",
            "confirmed": True,
            "backup": None,
            "validation": {"schema_valid": True, "policy_valid": True, "conflicts": []},
        }
    )

    payload = json.loads(store.history_path.read_text(encoding="utf-8").splitlines()[-1])
    assert payload["actor"] == "tester"
    assert payload["user"] == "unit-test"
