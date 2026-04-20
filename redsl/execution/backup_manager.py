"""Backup lifecycle management for redsl.

Backups of modified source files are stored inside ``.redsl/backups/``
in the project directory — never next to the original ``.py`` file.

Directory structure::

    <project>/
      .redsl/
        backups/
          goal/cli.py.bak
          goal/cli/hooks_cmd.py.bak
        chat.jsonl
        history.jsonl

Lifecycle:
- ``engine.py`` writes backups before each ``apply``
- After a **successful** cycle → ``cleanup_backups()`` removes them
- After a **failed** cycle (rollback) → ``rollback_from_backups()`` restores files
  then calls ``cleanup_backups()``
- ``.redsl/`` is added to ``.gitignore`` by ``ensure_gitignore()``
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

_BACKUPS_SUBDIR = "backups"


def _backup_dir(project_dir: Path) -> Path:
    return project_dir / ".redsl" / _BACKUPS_SUBDIR


# ---------------------------------------------------------------------------
# Ensure .redsl/ is in .gitignore
# ---------------------------------------------------------------------------

def ensure_gitignore(project_dir: Path) -> None:
    """Add .redsl/ to project .gitignore if not already present.

    Also adds ``*.bak`` as a safety net for stray backup files.
    """
    gitignore = project_dir / ".gitignore"
    entries_needed = [".redsl/", "*.bak"]

    if gitignore.exists():
        existing = gitignore.read_text(encoding="utf-8")
    else:
        existing = ""

    missing = [e for e in entries_needed if e not in existing.splitlines()]
    if not missing:
        return

    separator = "\n" if existing and not existing.endswith("\n") else ""
    addition = separator + "\n".join(missing) + "\n"
    with gitignore.open("a", encoding="utf-8") as fh:
        fh.write(addition)

    logger.info("backup_manager: added %s to %s/.gitignore", missing, project_dir.name)


# ---------------------------------------------------------------------------
# Backup enumeration
# ---------------------------------------------------------------------------

def list_backups(project_dir: Path) -> list[Path]:
    """Return all ``.bak`` files stored in ``.redsl/backups/``."""
    bdir = _backup_dir(project_dir)
    if not bdir.exists():
        return []
    return sorted(bdir.rglob("*.bak"))


def has_backups(project_dir: Path) -> bool:
    return bool(list_backups(project_dir))


# ---------------------------------------------------------------------------
# Cleanup (success path)
# ---------------------------------------------------------------------------

def cleanup_backups(project_dir: Path) -> int:
    """Remove all backups after a successful cycle.

    Returns the number of files deleted.
    """
    backups = list_backups(project_dir)
    for bak in backups:
        try:
            bak.unlink()
            logger.debug("backup_manager: removed %s", bak.relative_to(project_dir))
        except OSError as exc:
            logger.warning("backup_manager: could not remove %s: %s", bak, exc)

    # Also remove any stray .bak files left next to source files (migration)
    stray = _find_stray_bak_files(project_dir)
    for bak in stray:
        try:
            bak.unlink()
            logger.info("backup_manager: removed stray %s", bak.relative_to(project_dir))
        except OSError:
            pass

    total = len(backups) + len(stray)
    if total:
        logger.info("backup_manager: cleaned up %d backup file(s) in %s", total, project_dir.name)
    return total


def _find_stray_bak_files(project_dir: Path) -> list[Path]:
    """Find .bak files sitting next to source files (legacy location)."""
    results: list[Path] = []
    exclude = {".redsl", ".venv", "venv", ".git", "__pycache__", "node_modules"}
    for bak in project_dir.rglob("*.bak"):
        # Skip if already inside .redsl/backups
        try:
            bak.relative_to(_backup_dir(project_dir))
            continue
        except ValueError:
            pass
        # Skip excluded dirs
        parts = set(bak.parts)
        if parts & {str(project_dir / e) for e in exclude}:
            continue
        # Only collect files that sit next to a matching source file
        original = bak.with_suffix("")
        if original.exists():
            results.append(bak)
    return results


# ---------------------------------------------------------------------------
# Rollback (failure path)
# ---------------------------------------------------------------------------

def rollback_from_backups(project_dir: Path) -> int:
    """Restore all backed-up files to their original locations.

    Called after a cycle failure.  Cleans up backups after restoring.
    Returns the number of files restored.
    """
    backups = list_backups(project_dir)
    bdir = _backup_dir(project_dir)
    restored = 0

    for bak in backups:
        # Derive original path: strip .bak suffix, reconstruct relative to project
        rel_bak = bak.relative_to(bdir)            # e.g. goal/cli.py.bak
        original_rel = rel_bak.with_suffix("")     # goal/cli.py
        original = project_dir / original_rel

        try:
            original.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(bak), str(original))
            logger.info("backup_manager: restored %s", original_rel)
            restored += 1
        except OSError as exc:
            logger.error("backup_manager: could not restore %s: %s", original_rel, exc)

    cleanup_backups(project_dir)

    if restored:
        logger.info(
            "backup_manager: rolled back %d file(s) in %s",
            restored, project_dir.name,
        )
    return restored
