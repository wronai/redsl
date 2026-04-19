"""Config substrate CLI commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click
import yaml

from redsl.config_standard import (
    ConfigApplier,
    ConfigChangeProposal,
    ConfigStore,
    ConfigStoreError,
    ConfigValidationError,
    ConfigVersionMismatch,
    RedslConfigDocument,
)
from redsl.config_standard.models import DEFAULT_PROFILE_OVERRIDES, config_doc_to_yaml


@click.group()
def config() -> None:
    """Config substrate commands for manifests, profiles and audit logs."""


def _resolve_store(root: Path | str) -> ConfigStore:
    return ConfigStore.resolve(Path(root))


def _load_document_from_path(path: Path) -> RedslConfigDocument:
    if path.is_dir():
        return _resolve_store(path).load()
    if path.name == "redsl.config.yaml":
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise click.ClickException(f"Config file must contain a mapping: {path}")
        return RedslConfigDocument.model_validate(data)
    if path.suffix in {".yaml", ".yml", ".json"}:
        payload = (
            yaml.safe_load(path.read_text(encoding="utf-8"))
            if path.suffix != ".json"
            else json.loads(path.read_text(encoding="utf-8"))
        )
        if not isinstance(payload, dict):
            raise click.ClickException(f"File must contain a mapping: {path}")
        return RedslConfigDocument.model_validate(payload)
    raise click.ClickException(f"Unsupported config path: {path}")


def _dump_json(data: Any) -> None:
    click.echo(json.dumps(data, indent=2, ensure_ascii=False, default=str))


@config.command("init")
@click.option(
    "--root",
    type=click.Path(path_type=Path),
    default=Path("redsl-config"),
    show_default=True,
    help="Config root directory",
)
@click.option("--name", default="redsl-production", show_default=True, help="Config metadata name")
@click.option("--profile", default="production", show_default=True, help="Active profile")
@click.option("--force/--no-force", default=False, help="Overwrite existing files")
def config_init(root: Path, name: str, profile: str, force: bool) -> None:
    """Initialize a new redsl-config layout."""
    store = _resolve_store(root)
    if store.manifest_path.exists() and not force:
        raise click.ClickException(f"Config manifest already exists: {store.manifest_path}")

    store.ensure_layout()
    document = store.create_default(name=name, profile=profile)
    store.save(document)
    for profile_name, override in DEFAULT_PROFILE_OVERRIDES.items():
        profile_path = store.profiles_dir / f"{profile_name}.yaml"
        if profile_path.exists() and not force:
            continue
        if profile_name == "default":
            store._atomic_write_text(profile_path, "{}\n")
        else:
            store._atomic_write_text(
                profile_path, yaml.safe_dump(override, sort_keys=False, allow_unicode=True)
            )
    store.append_history(
        {
            "ts": document.metadata.updated.isoformat(),
            "version": document.metadata.version,
            "actor": "config-init",
            "user": "system",
            "source": f"init profile={profile}",
            "changes": [],
            "risk": "low",
            "confirmed": True,
            "backup": None,
            "validation": {"schema_valid": True, "policy_valid": True, "conflicts": []},
        }
    )
    click.echo(f"Initialized config at {store.root}")
    click.echo(f"Manifest: {store.manifest_path}")
    click.echo(f"Fingerprint: {document.metadata.fingerprint}")


@config.command("validate")
@click.option(
    "--root",
    type=click.Path(path_type=Path),
    default=Path("redsl-config"),
    show_default=True,
    help="Config root directory",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
)
def config_validate(root: Path, output_format: str) -> None:
    """Validate a config manifest against the standard."""
    store = _resolve_store(root)
    try:
        document = store.load()
    except FileNotFoundError as exc:
        raise click.ClickException(f"Missing manifest: {exc}") from exc

    errors = store.validate(document)
    if output_format == "json":
        _dump_json(
            {
                "valid": not errors,
                "root": str(store.root),
                "manifest": str(store.manifest_path),
                "version": document.metadata.version,
                "fingerprint": document.metadata.fingerprint,
                "errors": errors,
            }
        )
    else:
        if errors:
            click.echo("Config validation failed:")
            for error in errors:
                click.echo(f"- {error}")
        else:
            click.echo(f"Config valid: {store.manifest_path}")
            click.echo(f"Version: {document.metadata.version}")
            click.echo(f"Fingerprint: {document.metadata.fingerprint}")

    if errors:
        raise SystemExit(1)


@config.command("diff")
@click.option(
    "--root",
    type=click.Path(path_type=Path),
    default=Path("redsl-config"),
    show_default=True,
    help="Current config root",
)
@click.option(
    "--against",
    type=click.Path(path_type=Path, exists=True),
    required=True,
    help="Other config root or manifest to compare",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
)
def config_diff(root: Path, against: Path, output_format: str) -> None:
    """Diff current config against another config file or root."""
    store = _resolve_store(root)
    left = store.load()
    right = _load_document_from_path(against)
    diff = store.diff_documents(left, right)
    if output_format == "json":
        _dump_json({"root": str(store.root), "against": str(against), "diff": diff})
    else:
        import difflib

        left_yaml = config_doc_to_yaml(left)
        right_yaml = config_doc_to_yaml(right)
        unified = difflib.unified_diff(
            left_yaml.splitlines(keepends=True),
            right_yaml.splitlines(keepends=True),
            fromfile=str(store.manifest_path),
            tofile=str(against),
        )
        click.echo("".join(unified) or "(no differences)")


@config.command("history")
@click.option(
    "--root",
    type=click.Path(path_type=Path),
    default=Path("redsl-config"),
    show_default=True,
    help="Config root directory",
)
@click.option(
    "--limit", type=int, default=20, show_default=True, help="Number of recent records to show"
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
)
def config_history(root: Path, limit: int, output_format: str) -> None:
    """Show the append-only config audit history."""
    store = _resolve_store(root)
    records = store.history(limit=limit)
    if output_format == "json":
        _dump_json({"root": str(store.root), "records": records})
        return

    if not records:
        click.echo("(no history records)")
        return

    for record in records:
        ts = str(record.get("ts", "?"))
        version = record.get("version", "?")
        actor = record.get("actor", "?")
        source = record.get("source", "")
        risk = record.get("risk", "unknown")
        click.echo(f"- [{ts}] v{version} {actor} risk={risk} {source}")
        for change in record.get("changes", []):
            path = change.get("path", "")
            op = change.get("op", "")
            click.echo(f"  - {op} {path}")


@config.command("apply")
@click.option(
    "--root",
    type=click.Path(path_type=Path),
    default=Path("redsl-config"),
    show_default=True,
    help="Config root directory",
)
@click.argument("proposal_path", type=click.Path(path_type=Path, exists=True))
@click.option(
    "--actor", default="config-cli", show_default=True, help="Actor recorded in the audit log"
)
@click.option("--user", default="user", show_default=True, help="User recorded in the audit log")
@click.option("--dry-run/--no-dry-run", default=False, help="Validate proposal without writing")
def config_apply(root: Path, proposal_path: Path, actor: str, user: str, dry_run: bool) -> None:
    """Apply a ConfigChangeProposal atomically."""
    store = _resolve_store(root)
    payload = yaml.safe_load(proposal_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise click.ClickException(f"Proposal file must be a mapping: {proposal_path}")
    proposal = ConfigChangeProposal.model_validate(payload)

    if dry_run:
        click.echo("Dry-run proposal:")
        click.echo(
            json.dumps(proposal.model_dump(mode="json"), indent=2, ensure_ascii=False, default=str)
        )
        return

    applier = ConfigApplier(store)
    try:
        result = applier.apply(proposal, actor=actor, user=user)
    except ConfigVersionMismatch as exc:
        raise click.ClickException(str(exc)) from exc
    except ConfigValidationError as exc:
        raise click.ClickException(str(exc)) from exc
    except ConfigStoreError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Applied proposal -> version {result.new_version}")
    click.echo(f"Fingerprint: {result.fingerprint}")
    click.echo(f"Backup: {result.backup_path}")


@config.command("clone")
@click.option(
    "--from",
    "source",
    type=click.Path(path_type=Path, exists=True),
    required=True,
    help="Source config root or manifest",
)
@click.option(
    "--to",
    "target",
    type=click.Path(path_type=Path),
    default=Path("redsl-config-clone"),
    show_default=True,
    help="Target config root",
)
@click.option("--profile", default=None, help="Profile to apply after cloning")
@click.option(
    "--replace-secrets/--no-replace-secrets",
    default=False,
    help="Normalize secret refs after cloning",
)
@click.option("--force/--no-force", default=False, help="Overwrite existing target files")
def config_clone(
    source: Path, target: Path, profile: str | None, replace_secrets: bool, force: bool
) -> None:
    """Clone a config substrate locally."""
    target_store = _resolve_store(target)
    if target_store.manifest_path.exists() and not force:
        raise click.ClickException(f"Target config already exists: {target_store.manifest_path}")

    target_store.ensure_layout()
    cloned = target_store.clone_from(source, profile=profile, replace_secrets=replace_secrets)
    target_store.save(cloned)
    for profile_name, override in DEFAULT_PROFILE_OVERRIDES.items():
        profile_path = target_store.profiles_dir / f"{profile_name}.yaml"
        if profile_name == "default":
            target_store._atomic_write_text(profile_path, "{}\n")
        else:
            target_store._atomic_write_text(
                profile_path, yaml.safe_dump(override, sort_keys=False, allow_unicode=True)
            )
    click.echo(f"Cloned config from {source} -> {target_store.root}")
    click.echo(f"Fingerprint: {cloned.metadata.fingerprint}")


@config.command("show")
@click.option(
    "--root",
    type=click.Path(path_type=Path),
    default=Path("redsl-config"),
    show_default=True,
    help="Config root directory",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["yaml", "json"]),
    default="yaml",
    show_default=True,
)
def config_show(root: Path, output_format: str) -> None:
    """Print the current manifest."""
    store = _resolve_store(root)
    document = store.load()
    payload = document.model_dump(mode="json")
    if output_format == "json":
        _dump_json(payload)
    else:
        click.echo(config_doc_to_yaml(document))


@config.command("rollback")
@click.option(
    "--root",
    type=click.Path(path_type=Path),
    default=Path("redsl-config"),
    show_default=True,
    help="Config root directory",
)
@click.option(
    "--to-version",
    type=int,
    default=None,
    help="Target version to rollback to (default: previous version)",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
)
def config_rollback(root: Path, to_version: int | None, output_format: str) -> None:
    """Rollback config to a previous version atomically."""
    store = _resolve_store(root)
    applier = ConfigApplier(store)
    try:
        result = applier.rollback(target_version=to_version)
    except ConfigStoreError as exc:
        raise click.ClickException(str(exc)) from exc
    except ConfigValidationError as exc:
        raise click.ClickException(str(exc)) from exc

    if output_format == "json":
        _dump_json(
            {
                "success": result.success,
                "new_version": result.new_version,
                "config_path": str(result.config_path),
                "backup_path": str(result.backup_path),
                "fingerprint": result.fingerprint,
                "changed_paths": result.changed_paths,
            }
        )
    else:
        click.echo(f"Rolled back config -> version {result.new_version}")
        click.echo(f"Fingerprint: {result.fingerprint}")
        click.echo(f"Restored from: {result.backup_path}")


def register_config(cli: click.Group) -> None:
    cli.add_command(config)


__all__ = ["config", "register_config"]
