from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

import redsl.cli as cli_module
from redsl.config_standard import ConfigStore


def test_config_init_validate_and_show(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / "redsl-config"

    result = runner.invoke(
        cli_module.cli,
        ["config", "init", "--root", str(root), "--name", "cli-demo", "--profile", "development"],
    )
    assert result.exit_code == 0, result.output
    assert (root / "redsl.config.yaml").exists()
    assert (root / "schema" / "redsl.config.schema.json").exists()
    assert (root / "profiles" / "production.yaml").exists()

    validate = runner.invoke(cli_module.cli, ["config", "validate", "--root", str(root)])
    assert validate.exit_code == 0, validate.output
    assert "Fingerprint" in validate.output

    show = runner.invoke(
        cli_module.cli, ["config", "show", "--root", str(root), "--format", "json"]
    )
    assert show.exit_code == 0, show.output
    payload = json.loads(show.output)
    assert payload["metadata"]["name"] == "cli-demo"


def test_config_diff_history_apply_and_clone(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / "redsl-config"
    other_root = tmp_path / "other-config"
    clone_root = tmp_path / "clone-config"

    runner.invoke(cli_module.cli, ["config", "init", "--root", str(root), "--name", "main-config"])
    runner.invoke(
        cli_module.cli,
        [
            "config",
            "init",
            "--root",
            str(other_root),
            "--name",
            "other-config",
            "--profile",
            "minimal-cost",
        ],
    )

    store = ConfigStore(root)
    proposal_path = tmp_path / "proposal.yaml"
    proposal_path.write_text(
        "\n".join(
            [
                "apiVersion: redsl.config/v1",
                "kind: ConfigChangeProposal",
                "metadata:",
                "  source: user request",
                "  risk_level: low",
                "changes:",
                "  - op: set",
                "    path: spec.coding.tiers.balanced",
                "    current_value: 3.0",
                "    new_value: 2.5",
                "    rationale: lower balanced budget",
                "    confidence: 0.98",
                "    risk_level: low",
                "summary: lower balanced budget",
                "preconditions:",
                f"  config_version: {store.load().metadata.version}",
                f"  config_fingerprint: {store.load().metadata.fingerprint}",
            ]
        ),
        encoding="utf-8",
    )

    apply = runner.invoke(
        cli_module.cli, ["config", "apply", "--root", str(root), str(proposal_path)]
    )
    assert apply.exit_code == 0, apply.output
    assert "Applied proposal" in apply.output

    history = runner.invoke(
        cli_module.cli, ["config", "history", "--root", str(root), "--format", "json"]
    )
    assert history.exit_code == 0, history.output
    history_payload = json.loads(history.output)
    assert history_payload["records"]

    diff = runner.invoke(
        cli_module.cli, ["config", "diff", "--root", str(root), "--against", str(other_root)]
    )
    assert diff.exit_code == 0, diff.output
    assert "spec:" in diff.output or "---" in diff.output

    clone = runner.invoke(
        cli_module.cli,
        [
            "config",
            "clone",
            "--from",
            str(root),
            "--to",
            str(clone_root),
            "--profile",
            "production",
            "--replace-secrets",
        ],
    )
    assert clone.exit_code == 0, clone.output
    cloned_doc = ConfigStore(clone_root).load()
    assert cloned_doc.profile == "production"
    assert cloned_doc.secrets["openrouter_api_key"].ref.startswith("env:REPLACE_ME_")


def test_config_rollback(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / "redsl-config"

    runner.invoke(
        cli_module.cli, ["config", "init", "--root", str(root), "--name", "rollback-test"]
    )

    store = ConfigStore(root)
    original_cheap = store.load().spec.coding.tiers.cheap

    proposal_path = tmp_path / "proposal.yaml"
    proposal_path.write_text(
        "\n".join(
            [
                "apiVersion: redsl.config/v1",
                "kind: ConfigChangeProposal",
                "metadata:",
                "  source: test rollback",
                "  risk_level: low",
                "changes:",
                "  - op: set",
                "    path: spec.coding.tiers.cheap",
                "    new_value: 0.01",
                "    rationale: test change",
                "    confidence: 0.99",
                "    risk_level: low",
                "summary: test rollback",
                "preconditions:",
                f"  config_version: {store.load().metadata.version}",
                f"  config_fingerprint: {store.load().metadata.fingerprint}",
            ]
        ),
        encoding="utf-8",
    )

    apply = runner.invoke(
        cli_module.cli, ["config", "apply", "--root", str(root), str(proposal_path)]
    )
    assert apply.exit_code == 0, apply.output
    assert "Applied proposal" in apply.output

    new_cheap = store.load().spec.coding.tiers.cheap
    assert new_cheap == 0.01

    rollback = runner.invoke(
        cli_module.cli, ["config", "rollback", "--root", str(root), "--format", "json"]
    )
    assert rollback.exit_code == 0, rollback.output
    rollback_payload = json.loads(rollback.output)
    assert rollback_payload["success"] is True
    assert rollback_payload["new_version"] == 3

    final_cheap = store.load().spec.coding.tiers.cheap
    assert final_cheap == original_cheap
