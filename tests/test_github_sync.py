"""Tests for GitHub source adapter and plan_sync merge logic."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from redsl.commands.github_source import (
    fingerprint_issue,
    resolve_auth_ref,
    _priority_from_labels,
    _normalise_issue,
)
from redsl.commands.plan_sync import (
    merge_tasks,
    _generate_task_id,
    _load_tasks,
    _planfile_fingerprint,
)


# ---------------------------------------------------------------------------
# resolve_auth_ref
# ---------------------------------------------------------------------------

class TestResolveAuthRef:
    def test_env_present(self, monkeypatch):
        monkeypatch.setenv("TEST_GH_TOKEN", "ghp_test123")
        assert resolve_auth_ref("env:TEST_GH_TOKEN") == "ghp_test123"

    def test_env_missing_raises(self, monkeypatch):
        monkeypatch.delenv("MISSING_VAR", raising=False)
        with pytest.raises(ValueError, match="MISSING_VAR"):
            resolve_auth_ref("env:MISSING_VAR")

    def test_file_ref(self, tmp_path):
        token_file = tmp_path / "github.token"
        token_file.write_text("ghp_filetoken\n")
        result = resolve_auth_ref(f"file:{token_file}")
        assert result == "ghp_filetoken"

    def test_file_missing_raises(self, tmp_path):
        with pytest.raises(ValueError, match="not found"):
            resolve_auth_ref(f"file:{tmp_path}/nonexistent.token")

    def test_unknown_scheme_raises(self):
        with pytest.raises(ValueError, match="Unknown auth_ref"):
            resolve_auth_ref("plain:token")

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            resolve_auth_ref("")


# ---------------------------------------------------------------------------
# fingerprint_issue
# ---------------------------------------------------------------------------

class TestFingerprintIssue:
    def _make_issue(self, **overrides):
        base = {
            "title": "Fix login bug",
            "state": "open",
            "labels": [{"name": "bug"}],
            "assignee": {"login": "alice"},
            "body": "Some description",
        }
        base.update(overrides)
        return base

    def test_returns_sha256_prefix(self):
        fp = fingerprint_issue(self._make_issue())
        assert fp.startswith("sha256:")

    def test_same_issue_same_fingerprint(self):
        issue = self._make_issue()
        assert fingerprint_issue(issue) == fingerprint_issue(issue)

    def test_title_change_changes_fingerprint(self):
        a = fingerprint_issue(self._make_issue(title="A"))
        b = fingerprint_issue(self._make_issue(title="B"))
        assert a != b

    def test_label_change_changes_fingerprint(self):
        a = fingerprint_issue(self._make_issue(labels=[{"name": "bug"}]))
        b = fingerprint_issue(self._make_issue(labels=[{"name": "feature"}]))
        assert a != b

    def test_body_change_changes_fingerprint(self):
        a = fingerprint_issue(self._make_issue(body="Old body"))
        b = fingerprint_issue(self._make_issue(body="New body"))
        assert a != b

    def test_null_body_handled(self):
        fp = fingerprint_issue(self._make_issue(body=None))
        assert fp.startswith("sha256:")


# ---------------------------------------------------------------------------
# _priority_from_labels
# ---------------------------------------------------------------------------

class TestPriorityFromLabels:
    def test_critical_label(self):
        assert _priority_from_labels(["critical", "bug"]) == 1

    def test_high_label(self):
        assert _priority_from_labels(["high"]) == 2

    def test_low_label(self):
        assert _priority_from_labels(["low"]) == 4

    def test_default_medium(self):
        assert _priority_from_labels(["enhancement", "docs"]) == 3

    def test_empty_labels(self):
        assert _priority_from_labels([]) == 3

    def test_p0_label(self):
        assert _priority_from_labels(["P0"]) == 1


# ---------------------------------------------------------------------------
# merge_tasks
# ---------------------------------------------------------------------------

def _make_existing_task(ext_id="org/repo#1", fp="sha256:aaa", source="gh-main"):
    return {
        "id": "GH-001",
        "source": source,
        "external_id": ext_id,
        "external_fingerprint": fp,
        "title": "Old title",
        "status": "todo",
        "priority": 3,
        "labels": ["bug"],
        "url": "https://github.com/org/repo/issues/1",
        "local_notes": "my note",
        "priority_override": None,
        "estimated_effort": "M",
        "action": "github_issue",
        "file": "",
        "description": "",
        "assignee": "",
    }


def _make_incoming_issue(ext_id="org/repo#1", fp="sha256:aaa", number=1):
    return {
        "source": "gh-main",
        "external_id": ext_id,
        "external_fingerprint": fp,
        "number": number,
        "title": "New title",
        "status": "todo",
        "priority": 2,
        "labels": ["bug"],
        "url": "https://github.com/org/repo/issues/1",
        "assignee": "alice",
        "body_snippet": "description",
    }


class TestMergeTasks:
    def test_new_issue_added(self):
        result = merge_tasks([], [_make_incoming_issue()], "gh-main")
        assert len(result.added) == 1
        assert result.added[0]["title"] == "New title"

    def test_unchanged_issue_not_modified(self):
        existing = [_make_existing_task(fp="sha256:aaa")]
        incoming = [_make_incoming_issue(fp="sha256:aaa")]
        result = merge_tasks(existing, incoming, "gh-main")
        assert len(result.unchanged) == 1
        assert len(result.updated) == 0
        assert result.unchanged[0]["title"] == "Old title"

    def test_changed_issue_updates_external_fields(self):
        existing = [_make_existing_task(fp="sha256:old")]
        incoming = [_make_incoming_issue(fp="sha256:new")]
        result = merge_tasks(existing, incoming, "gh-main")
        assert len(result.updated) == 1
        updated = result.updated[0]
        assert updated["external_fingerprint"] == "sha256:new"
        assert updated["title"] == "New title"

    def test_local_notes_preserved_on_update(self):
        existing = [_make_existing_task(fp="sha256:old")]
        incoming = [_make_incoming_issue(fp="sha256:new")]
        result = merge_tasks(existing, incoming, "gh-main")
        assert result.updated[0]["local_notes"] == "my note"

    def test_priority_override_wins(self):
        existing = _make_existing_task(fp="sha256:old")
        existing["priority_override"] = 1  # user set critical
        incoming = _make_incoming_issue(fp="sha256:new")
        result = merge_tasks([existing], [incoming], "gh-main")
        assert result.updated[0]["priority"] == 1

    def test_removed_issue_archived(self):
        existing = [_make_existing_task()]
        result = merge_tasks(existing, [], "gh-main")  # no incoming
        assert len(result.archived) == 1
        assert result.archived[0]["external_id"] == "org/repo#1"

    def test_other_source_tasks_untouched(self):
        other = {"id": "Q01", "source": "sumr-refactor", "title": "Refactor X",
                 "status": "todo", "action": "split_module", "file": "x.py",
                 "description": "", "priority": 2}
        result = merge_tasks([other], [], "gh-main")
        assert any(t["id"] == "Q01" for t in result.all_tasks)

    def test_all_tasks_includes_all(self):
        existing = [_make_existing_task(fp="sha256:aaa")]
        incoming = [_make_incoming_issue(fp="sha256:aaa")]
        result = merge_tasks(existing, incoming, "gh-main")
        assert len(result.all_tasks) == 1


# ---------------------------------------------------------------------------
# apply_planfile_sources (integration, with mocked fetch_issues)
# ---------------------------------------------------------------------------

class TestApplyPlanfileSources:
    def _write_planfile(self, tmp_path: Path, sources=None, tasks=None) -> Path:
        data = {
            "apiVersion": "redsl.plan/v1",
            "kind": "Planfile",
            "metadata": {"name": "test", "version": 1},
            "sources": sources or [],
            "spec": {"tasks": tasks or []},
        }
        pf = tmp_path / "planfile.yaml"
        pf.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
        return pf

    def test_dry_run_does_not_write(self, tmp_path):
        pf = self._write_planfile(tmp_path, sources=[
            {"id": "gh-main", "type": "github", "repo": "org/repo",
             "auth_ref": "env:GITHUB_TOKEN", "filters": {}}
        ])

        fake_issues = [_make_incoming_issue()]
        with patch("redsl.commands.plan_sync._gh_source.fetch_issues", return_value=fake_issues):
            from redsl.commands.plan_sync import apply_planfile_sources
            result = apply_planfile_sources(pf, dry_run=True)

        assert result.written is False
        assert result.dry_run is True
        assert "gh-main" in result.sources_synced

    def test_sync_adds_new_tasks(self, tmp_path, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_fake")
        pf = self._write_planfile(tmp_path, sources=[
            {"id": "gh-main", "type": "github", "repo": "org/repo",
             "auth_ref": "env:GITHUB_TOKEN", "filters": {}}
        ])

        fake_issues = [_make_incoming_issue()]
        with patch("redsl.commands.plan_sync._gh_source.fetch_issues", return_value=fake_issues):
            from redsl.commands.plan_sync import apply_planfile_sources
            result = apply_planfile_sources(pf, dry_run=False)

        assert result.written is True
        written_data = yaml.safe_load(pf.read_text())
        tasks = written_data["spec"]["tasks"]
        assert any(t.get("external_id") == "org/repo#1" for t in tasks)

    def test_missing_planfile_raises(self, tmp_path):
        from redsl.commands.plan_sync import apply_planfile_sources
        with pytest.raises(FileNotFoundError):
            apply_planfile_sources(tmp_path / "planfile.yaml")

    def test_non_github_sources_skipped(self, tmp_path):
        pf = self._write_planfile(tmp_path, sources=[
            {"id": "sumr-local", "type": "sumr_extract", "path": "./SUMR.md"}
        ])
        from redsl.commands.plan_sync import apply_planfile_sources
        result = apply_planfile_sources(pf, dry_run=True)
        assert result.sources_synced == []

    def test_archived_tasks_preserved_across_sync(self, tmp_path, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_fake")
        existing_task = _make_existing_task()
        pf = self._write_planfile(tmp_path, sources=[
            {"id": "gh-main", "type": "github", "repo": "org/repo",
             "auth_ref": "env:GITHUB_TOKEN", "filters": {}}
        ], tasks=[existing_task])

        # Empty incoming — issue was closed/removed
        with patch("redsl.commands.plan_sync._gh_source.fetch_issues", return_value=[]):
            from redsl.commands.plan_sync import apply_planfile_sources
            result = apply_planfile_sources(pf, dry_run=False)

        written_data = yaml.safe_load(pf.read_text())
        archived = written_data.get("sync_state", {}).get("archived", [])
        assert any(a.get("external_id") == "org/repo#1" for a in archived)
