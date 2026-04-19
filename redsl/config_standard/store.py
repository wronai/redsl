"""Config store, loader, saver, diff and history helpers."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from .models import (
    CONFIG_STANDARD_API_VERSION,
    ConfigOrigin,
    RedslConfigDocument,
    build_default_config,
    config_doc_to_yaml,
)
from .paths import (
    deep_merge,
    get_nested_value,
    materialize_diff,
)
from .security import SecretInterceptor

try:
    import fcntl
except ImportError:  # pragma: no cover - non-Linux fallback
    fcntl = None  # type: ignore[assignment]


class ConfigStoreError(RuntimeError):
    pass


class ConfigVersionMismatch(ConfigStoreError):
    pass


class ConfigValidationError(ConfigStoreError):
    pass


class ConfigHistoryRecord(dict[str, Any]):
    pass


class ConfigStore:
    """Manage a redsl-config directory with manifest, profiles and history."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.manifest_path = self.root / "redsl.config.yaml"
        self.profiles_dir = self.root / "profiles"
        self.secrets_dir = self.root / "secrets"
        self.schema_path = self.root / "schema" / "redsl.config.schema.json"
        self.history_dir = self.root / "history"
        self.history_path = self.history_dir / "changes.jsonl"
        self.proposal_schema_path = self.root / "schema" / "redsl.config.proposal.schema.json"

    @classmethod
    def resolve(cls, path: Path | str) -> ConfigStore:
        root = Path(path)
        if root.is_file():
            root = root.parent
        if root.name == "redsl.config.yaml":
            root = root.parent
        return cls(root)

    def ensure_layout(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.secrets_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.schema_path.parent.mkdir(parents=True, exist_ok=True)
        self.proposal_schema_path.parent.mkdir(parents=True, exist_ok=True)

        gitignore = self.secrets_dir / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text("*\n!.gitignore\n", encoding="utf-8")

    def create_default(
        self, *, name: str = "redsl-production", profile: str = "production"
    ) -> RedslConfigDocument:
        document = build_default_config(name=name, profile=profile)
        document = self.apply_profile(document, profile)
        document.metadata.fingerprint = document.compute_fingerprint()
        return document

    def apply_profile(self, document: RedslConfigDocument, profile: str) -> RedslConfigDocument:
        from .models import DEFAULT_PROFILE_OVERRIDES

        overrides = DEFAULT_PROFILE_OVERRIDES.get(profile, {})
        if not overrides:
            document.profile = profile
            return document

        data = document.model_dump(mode="json")
        merged = deep_merge(data, overrides)
        merged["profile"] = profile
        return self.load_document(merged)

    def load_document(self, payload: dict[str, Any]) -> RedslConfigDocument:
        document = RedslConfigDocument.model_validate(payload)
        if not document.metadata.fingerprint:
            document.metadata.fingerprint = document.compute_fingerprint()
        return document

    def load(self) -> RedslConfigDocument:
        if not self.manifest_path.exists():
            raise FileNotFoundError(self.manifest_path)
        return self.load_any(self.manifest_path)

    def load_any(self, path: Path) -> RedslConfigDocument:
        if not path.exists():
            raise FileNotFoundError(path)
        if path.suffix == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
        else:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ConfigValidationError("Config file must be a mapping")
        return self.load_document(data)

    def save(self, document: RedslConfigDocument, *, write_schema: bool = True) -> Path:
        self.ensure_layout()
        document.metadata.updated = datetime.now(UTC)
        document.metadata.fingerprint = document.compute_fingerprint()
        payload = config_doc_to_yaml(document)
        self._atomic_write_text(self.manifest_path, payload)
        if write_schema:
            self.write_schema_files()
        return self.manifest_path

    def write_schema_files(self) -> None:
        from .models import export_config_schema, export_proposal_schema

        self._atomic_write_text(
            self.schema_path, json.dumps(export_config_schema(), indent=2, ensure_ascii=False)
        )
        self._atomic_write_text(
            self.proposal_schema_path,
            json.dumps(export_proposal_schema(), indent=2, ensure_ascii=False),
        )

    def save_profile(self, profile_name: str, document: RedslConfigDocument) -> Path:
        self.ensure_layout()
        profile_path = self.profiles_dir / f"{profile_name}.yaml"
        self._atomic_write_text(profile_path, config_doc_to_yaml(document))
        return profile_path

    def load_profile(self, profile_name: str) -> dict[str, Any]:
        profile_path = self.profiles_dir / f"{profile_name}.yaml"
        if not profile_path.exists():
            return {}
        payload = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ConfigValidationError(f"Profile {profile_name!r} must be a mapping")
        return payload

    def history(self, limit: int | None = None) -> list[dict[str, Any]]:
        if not self.history_path.exists():
            return []
        lines = [
            line.strip()
            for line in self.history_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if limit is not None and limit > 0:
            lines = lines[-limit:]
        records: list[dict[str, Any]] = []
        for line in lines:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return records

    def append_history(self, record: dict[str, Any]) -> None:
        self.ensure_layout()
        payload = json.dumps(record, ensure_ascii=False, default=str)
        with self.history_path.open("a", encoding="utf-8") as handle:
            handle.write(payload + "\n")

    def inspect(self, document: RedslConfigDocument, path: str) -> Any:
        return get_nested_value(document.model_dump(mode="json"), path)

    def diff_documents(
        self, left: RedslConfigDocument, right: RedslConfigDocument
    ) -> dict[str, Any]:
        left_payload = left.model_dump(mode="json")
        right_payload = right.model_dump(mode="json")
        return materialize_diff(left_payload, right_payload)

    def diff_manifest(self, other_path: Path) -> str:
        left = self.manifest_path.read_text(encoding="utf-8") if self.manifest_path.exists() else ""
        right = other_path.read_text(encoding="utf-8") if other_path.exists() else ""
        import difflib

        diff = difflib.unified_diff(
            left.splitlines(keepends=True),
            right.splitlines(keepends=True),
            fromfile=str(self.manifest_path),
            tofile=str(other_path),
        )
        return "".join(diff)

    def clone_from(
        self, source: Path | str, *, profile: str | None = None, replace_secrets: bool = False
    ) -> RedslConfigDocument:
        source_path = Path(source)
        source_store = ConfigStore.resolve(source_path)
        source_doc = (
            source_store.load_any(source_path) if source_path.is_file() else source_store.load()
        )
        cloned = self.load_document(source_doc.model_dump(mode="json"))
        cloned.metadata.version = 1
        cloned.metadata.origin = ConfigOrigin(
            cloned_from=str(Path(source).resolve()), cloned_at=datetime.now(UTC)
        )
        cloned.metadata.created = datetime.now(UTC)
        cloned.metadata.updated = datetime.now(UTC)
        if profile:
            cloned.profile = profile
            cloned = self.apply_profile(cloned, profile)
        if replace_secrets:
            cloned.secrets = {
                name: secret.model_copy(update={"ref": f"env:REPLACE_ME_{name.upper()}"})
                for name, secret in cloned.secrets.items()
            }
        cloned.metadata.fingerprint = cloned.compute_fingerprint()
        return cloned

    def validate(self, document: RedslConfigDocument) -> list[str]:
        errors: list[str] = []
        if document.apiVersion != CONFIG_STANDARD_API_VERSION:
            errors.append(f"Unsupported apiVersion: {document.apiVersion}")
        fingerprint = document.compute_fingerprint()
        if document.metadata.fingerprint and document.metadata.fingerprint != fingerprint:
            errors.append("Fingerprint mismatch")
        for name, secret in document.secrets.items():
            if not secret.ref.startswith(("file:", "env:", "vault:", "doppler:")):
                errors.append(f"Secret {name} uses unsupported ref: {secret.ref}")
        return errors

    def read_secret_placeholders(self, text: str) -> tuple[str, list[str]]:
        interceptor = SecretInterceptor()
        redacted, matches = interceptor.redact(text)
        return redacted, [match.placeholder for match in matches]

    def _atomic_write_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_fd, tmp_name = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
        )
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, path)
        finally:
            if os.path.exists(tmp_name):
                try:
                    os.unlink(tmp_name)
                except OSError:
                    pass

    @contextmanager
    def lock(self) -> Iterator[None]:
        self.ensure_layout()
        lock_path = self.root / ".redsl-config.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a+") as handle:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                if fcntl is not None:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


__all__ = [
    "ConfigHistoryRecord",
    "ConfigStore",
    "ConfigStoreError",
    "ConfigValidationError",
    "ConfigVersionMismatch",
]
