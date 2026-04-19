"""Three-way merge logic for planfile GitHub sync.

Merges external state (from GitHub) with local planfile state.

Merge rules per task:
  - New (exists in GH, not in planfile)       → add with auto-id
  - Unchanged (external_fingerprint matches)  → no-op
  - Changed in GH (fingerprint differs)       → update external fields only
      * preserved: local_notes, priority_override, estimated_effort, status (if local-only change)
  - Removed from GH                           → move to sync_state.archived

Public API
----------
    merge_tasks(existing_tasks, incoming_issues, source_id) -> MergeResult
    apply_planfile_sources(planfile_path, dry_run) -> SyncResult
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from redsl.commands import github_source as _gh_source

logger = logging.getLogger(__name__)

_LOCAL_ONLY_FIELDS = {"local_notes", "priority_override", "estimated_effort"}
_EXTERNAL_FIELDS = {
    "title", "status", "priority", "labels", "url", "external_fingerprint", "assignee"
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class MergeResult:
    added: list[dict[str, Any]] = field(default_factory=list)
    updated: list[dict[str, Any]] = field(default_factory=list)
    unchanged: list[dict[str, Any]] = field(default_factory=list)
    archived: list[dict[str, Any]] = field(default_factory=list)
    all_tasks: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class SyncResult:
    planfile_path: Path
    written: bool
    dry_run: bool
    sources_synced: list[str]
    merge_results: dict[str, MergeResult]
    errors: list[str]
    timestamp: str


# ---------------------------------------------------------------------------
# Merge logic
# ---------------------------------------------------------------------------

def merge_tasks(
    existing_tasks: list[dict[str, Any]],
    incoming_issues: list[dict[str, Any]],
    source_id: str,
) -> MergeResult:
    """Merge incoming GitHub issues into existing local tasks for one source."""
    result = MergeResult()
    source_tasks, other_tasks = _partition_tasks(existing_tasks, source_id)
    incoming_by_id = {i["external_id"]: i for i in incoming_issues}

    _detect_archived(source_tasks, incoming_by_id, result)
    _classify_incoming(source_tasks, incoming_by_id, existing_tasks, result)

    result.all_tasks = other_tasks + result.added + result.updated + result.unchanged
    return result


def _partition_tasks(
    existing: list[dict[str, Any]], source_id: str
) -> tuple[dict[str, dict], list[dict[str, Any]]]:
    """Split tasks into {ext_id: task} for source and pass-through list for others."""
    source_tasks: dict[str, dict] = {}
    other_tasks: list[dict[str, Any]] = []
    for t in existing:
        if isinstance(t, dict) and t.get("source") == source_id and t.get("external_id"):
            source_tasks[t["external_id"]] = t
        else:
            other_tasks.append(t)
    return source_tasks, other_tasks


def _detect_archived(
    source_tasks: dict[str, dict],
    incoming_by_id: dict[str, dict],
    result: MergeResult,
) -> None:
    """Populate result.archived with tasks no longer present in incoming."""
    for ext_id, task in source_tasks.items():
        if ext_id not in incoming_by_id:
            result.archived.append(task)
            logger.debug("Archived task %s (removed from GH)", ext_id)


def _classify_incoming(
    source_tasks: dict[str, dict],
    incoming_by_id: dict[str, dict],
    existing_tasks: list[dict[str, Any]],
    result: MergeResult,
) -> None:
    """Classify each incoming issue as added, updated, or unchanged."""
    for ext_id, issue in incoming_by_id.items():
        existing = source_tasks.get(ext_id)
        if existing is None:
            new_task = _issue_to_task(issue, existing_tasks)
            result.added.append(new_task)
            logger.debug("Added task %s: %s", new_task["id"], new_task["title"])
        elif existing.get("external_fingerprint") == issue["external_fingerprint"]:
            result.unchanged.append(existing)
        else:
            result.updated.append(_apply_external_update(existing, issue))
            logger.debug("Updated task %s (fingerprint changed)", ext_id)


def _apply_external_update(existing: dict[str, Any], issue: dict[str, Any]) -> dict[str, Any]:
    """Apply changed external fields to a task, preserving local overrides."""
    updated = dict(existing)
    for fld in _EXTERNAL_FIELDS:
        if fld in issue:
            updated[fld] = issue[fld]
    if updated.get("priority_override") is not None:
        updated["priority"] = updated["priority_override"]
    return updated


def _issue_to_task(issue: dict[str, Any], existing_tasks: list[dict[str, Any]]) -> dict[str, Any]:
    """Convert a new incoming GitHub issue to a planfile task dict."""
    new_id = _generate_task_id(issue, existing_tasks)
    return {
        "id": new_id,
        "source": issue["source"],
        "external_id": issue["external_id"],
        "external_fingerprint": issue["external_fingerprint"],
        "title": issue["title"],
        "description": issue.get("body_snippet", ""),
        "file": "",                  # no file for GH issues
        "action": "github_issue",
        "status": issue["status"],
        "priority": issue["priority"],
        "labels": issue["labels"],
        "url": issue["url"],
        "assignee": issue.get("assignee", ""),
        "local_notes": "",
        "priority_override": None,
        "estimated_effort": "",
    }


def _generate_task_id(issue: dict[str, Any], existing_tasks: list[dict[str, Any]]) -> str:
    """Generate a short stable task id like GH-042."""
    existing_ids = {t.get("id", "") for t in existing_tasks if isinstance(t, dict)}
    # Prefer GH-<number>
    number = issue.get("number", 0)
    candidate = f"GH-{number:03d}"
    if candidate not in existing_ids:
        return candidate
    # Fallback: GH-<number>-<hash>
    h = hashlib.sha256(issue["external_id"].encode()).hexdigest()[:4]
    return f"GH-{number:03d}-{h}"


# ---------------------------------------------------------------------------
# Full planfile sync
# ---------------------------------------------------------------------------

def apply_planfile_sources(
    planfile_path: Path,
    dry_run: bool = False,
) -> SyncResult:
    """Read planfile.yaml, sync all github sources, write result."""
    if not planfile_path.exists():
        raise FileNotFoundError(
            f"planfile.yaml not found: {planfile_path}. "
            "Run: redsl planfile sync <project> first."
        )

    data: dict[str, Any] = yaml.safe_load(planfile_path.read_text(encoding="utf-8")) or {}
    existing_tasks = _load_tasks(data)
    existing_archived: list[Any] = (data.get("sync_state") or {}).get("archived") or []

    all_tasks, existing_archived, merge_results, sources_synced, errors = _sync_all_sources(
        data.get("sources") or [], existing_tasks, existing_archived
    )

    timestamp = datetime.now(timezone.utc).isoformat()
    _update_planfile_metadata(data, all_tasks, existing_archived, timestamp)

    written = False
    if not dry_run and sources_synced:
        _atomic_write(planfile_path, data)
        _append_history(
            planfile_path.parent / ".redsl" / "plan-changes.jsonl",
            _build_history_entry(timestamp, sources_synced, merge_results),
        )
        written = True

    return SyncResult(
        planfile_path=planfile_path,
        written=written,
        dry_run=dry_run,
        sources_synced=sources_synced,
        merge_results=merge_results,
        errors=errors,
        timestamp=timestamp,
    )


def _sync_all_sources(
    sources: list[dict[str, Any]],
    existing_tasks: list[dict[str, Any]],
    existing_archived: list[Any],
) -> tuple[list, list, dict, list, list]:
    """Iterate github sources, merge each, accumulate results."""
    errors: list[str] = []
    merge_results: dict[str, MergeResult] = {}
    sources_synced: list[str] = []
    all_tasks = list(existing_tasks)

    for source in sources:
        if source.get("type") != "github":
            continue
        sid = source.get("id", "unknown")
        try:
            issues = _gh_source.fetch_issues(source)
            mr = merge_tasks(all_tasks, issues, sid)
            all_tasks = mr.all_tasks
            existing_archived = _merge_archived(existing_archived, mr.archived)
            merge_results[sid] = mr
            sources_synced.append(sid)
        except Exception as exc:
            logger.error("Error syncing source %s: %s", sid, exc)
            errors.append(f"{sid}: {exc}")

    return all_tasks, existing_archived, merge_results, sources_synced, errors


def _update_planfile_metadata(
    data: dict[str, Any],
    all_tasks: list[dict[str, Any]],
    archived: list[Any],
    timestamp: str,
) -> None:
    """Mutate data dict in-place with updated tasks, sync_state, and metadata."""
    data.setdefault("spec", {})["tasks"] = all_tasks
    data["sync_state"] = {"last_sync": timestamp, "conflicts": [], "archived": archived}
    meta = data.setdefault("metadata", {})
    meta["version"] = (meta.get("version") or 0) + 1
    meta["updated"] = timestamp
    meta["fingerprint"] = _planfile_fingerprint(all_tasks)


def _build_history_entry(
    timestamp: str,
    sources_synced: list[str],
    merge_results: dict[str, MergeResult],
) -> dict[str, Any]:
    return {
        "timestamp": timestamp,
        "sources_synced": sources_synced,
        "added": sum(len(mr.added) for mr in merge_results.values()),
        "updated": sum(len(mr.updated) for mr in merge_results.values()),
        "archived": sum(len(mr.archived) for mr in merge_results.values()),
    }


def _load_tasks(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Load tasks from spec.tasks or top-level tasks key."""
    spec = data.get("spec") or {}
    tasks = spec.get("tasks") or data.get("tasks") or []
    return [t for t in tasks if isinstance(t, dict)]


def _merge_archived(existing: list[Any], new_archived: list[dict[str, Any]]) -> list[Any]:
    """Add newly archived items without duplicating by external_id."""
    existing_ids = {
        item.get("external_id") for item in existing if isinstance(item, dict)
    }
    result = list(existing)
    for item in new_archived:
        if item.get("external_id") not in existing_ids:
            result.append(item)
    return result


def _planfile_fingerprint(tasks: list[dict[str, Any]]) -> str:
    raw = json.dumps(
        [t.get("id") for t in tasks],
        sort_keys=True,
    )
    return "sha256:" + hashlib.sha256(raw.encode()).hexdigest()[:16]


def _atomic_write(path: Path, data: dict[str, Any]) -> None:
    """Write planfile.yaml atomically (temp + rename)."""
    tmp = path.with_suffix(".yaml.tmp")
    content = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _append_history(history_path: Path, entry: dict[str, Any]) -> None:
    """Append a sync entry to append-only JSONL history log."""
    try:
        history_path.parent.mkdir(parents=True, exist_ok=True)
        with history_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.warning("Could not write sync history: %s", exc)
