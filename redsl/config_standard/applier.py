"""Atomic config proposal application and rollback."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .models import ConfigChange, ConfigChangeProposal, RedslConfigDocument
from .paths import get_nested_value, remove_nested_value, set_nested_value
from .store import ConfigStore, ConfigStoreError, ConfigValidationError, ConfigVersionMismatch


@dataclass(slots=True)
class ApplyResult:
    success: bool
    new_version: int
    config_path: Path
    backup_path: Path
    fingerprint: str
    changed_paths: list[str] = field(default_factory=list)
    validation_errors: list[str] = field(default_factory=list)
    policy_errors: list[str] = field(default_factory=list)


class ConfigApplier:
    """Apply config proposals atomically with locking and audit logging."""

    def __init__(self, store: ConfigStore) -> None:
        self.store = store

    def apply(
        self, proposal: ConfigChangeProposal, *, actor: str = "config-agent", user: str = "user"
    ) -> ApplyResult:
        with self.store.lock():
            current = self.store.load()
            self._check_preconditions(current, proposal)
            backup_path = self._backup(current)
            current_payload = current.model_dump(mode="json")
            changed_paths: list[str] = []
            change_log: list[dict[str, Any]] = []

            for change in proposal.changes:
                before = get_nested_value(current_payload, change.path)
                after = self._apply_change(current_payload, change)
                changed_paths.append(change.path)
                change_log.append(
                    {
                        "op": change.op,
                        "path": change.path,
                        "from": before,
                        "to": after,
                        "risk": change.risk_level,
                        "confidence": change.confidence,
                    }
                )

            try:
                updated = self.store.load_document(current_payload)
            except ValidationError as exc:
                errors = [str(error) for error in exc.errors()]
                raise ConfigValidationError(
                    "Config validation failed: " + "; ".join(errors)
                ) from exc

            updated.metadata.version = current.metadata.version + 1
            updated.metadata.created = current.metadata.created
            updated.metadata.origin = current.metadata.origin
            updated.metadata.updated = datetime.now(UTC)
            updated.metadata.fingerprint = updated.compute_fingerprint()

            validation_errors = self.store.validate(updated)
            if validation_errors:
                raise ConfigValidationError("; ".join(validation_errors))

            self.store.save(updated, write_schema=True)
            self.store.append_history(
                {
                    "ts": datetime.now(UTC).isoformat(),
                    "version": updated.metadata.version,
                    "actor": actor,
                    "user": user,
                    "source": proposal.metadata.source or proposal.summary or "nlp proposal",
                    "changes": change_log,
                    "risk": proposal.metadata.risk_level,
                    "confirmed": any(change.requires_confirmation for change in proposal.changes),
                    "backup": str(backup_path),
                    "validation": {
                        "schema_valid": not validation_errors,
                        "policy_valid": not validation_errors,
                        "conflicts": proposal.validation.conflicts,
                    },
                }
            )
            return ApplyResult(
                success=True,
                new_version=updated.metadata.version,
                config_path=self.store.manifest_path,
                backup_path=backup_path,
                fingerprint=updated.metadata.fingerprint,
                changed_paths=changed_paths,
            )

    def rollback(self, target_version: int | None = None) -> ApplyResult:
        with self.store.lock():
            current = self.store.load()
            target_version = target_version or max(current.metadata.version - 1, 1)
            backup_path = self.store.history_dir / f"backup-v{target_version}.yaml"
            if not backup_path.exists():
                raise ConfigStoreError(f"No backup found for version {target_version}")
            import yaml

            payload = yaml.safe_load(backup_path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ConfigValidationError(f"Backup file is not a mapping: {backup_path}")
            document = self.store.load_document(payload)
            document.metadata.version = current.metadata.version + 1
            document.metadata.updated = datetime.now(UTC)
            document.metadata.fingerprint = document.compute_fingerprint()
            self.store.save(document, write_schema=True)
            self.store.append_history(
                {
                    "ts": datetime.now(UTC).isoformat(),
                    "version": document.metadata.version,
                    "actor": "rollback",
                    "user": "system",
                    "source": f"rollback to {target_version}",
                    "changes": [],
                    "risk": "medium",
                    "confirmed": True,
                    "backup": str(backup_path),
                    "validation": {"schema_valid": True, "policy_valid": True, "conflicts": []},
                }
            )
            return ApplyResult(
                success=True,
                new_version=document.metadata.version,
                config_path=self.store.manifest_path,
                backup_path=backup_path,
                fingerprint=document.metadata.fingerprint,
            )

    def _check_preconditions(
        self, current: RedslConfigDocument, proposal: ConfigChangeProposal
    ) -> None:
        if (
            proposal.preconditions.config_version is not None
            and current.metadata.version != proposal.preconditions.config_version
        ):
            raise ConfigVersionMismatch(
                "Config version mismatch: expected "
                f"{proposal.preconditions.config_version}, got {current.metadata.version}"
            )
        if (
            proposal.preconditions.config_fingerprint is not None
            and current.metadata.fingerprint != proposal.preconditions.config_fingerprint
        ):
            raise ConfigVersionMismatch(
                "Config fingerprint mismatch: expected "
                f"{proposal.preconditions.config_fingerprint}, got {current.metadata.fingerprint}"
            )

    def _backup(self, current: RedslConfigDocument) -> Path:
        backup_path = self.store.history_dir / f"backup-v{current.metadata.version}.yaml"
        self.store.history_dir.mkdir(parents=True, exist_ok=True)
        self.store._atomic_write_text(backup_path, self._dump_yaml(current))
        return backup_path

    def _dump_yaml(self, document: RedslConfigDocument) -> str:
        import yaml

        return yaml.safe_dump(document.model_dump(mode="json"), sort_keys=False, allow_unicode=True)

    def _apply_change(self, payload: dict[str, Any], change: ConfigChange) -> Any:
        if change.op == "remove":
            return remove_nested_value(payload, change.path)

        value = change.new_value

        set_nested_value(payload, change.path, value, allow_create=True, add=change.op == "add")
        return get_nested_value(payload, change.path)


__all__ = ["ApplyResult", "ConfigApplier"]
