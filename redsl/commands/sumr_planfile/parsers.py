"""Parsers for SUMR.md and TOON content."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from .models import SumrData

logger = logging.getLogger(__name__)

# Regex patterns for SUMR.md parsing
_MARKPACT_BLOCK_RE = re.compile(
    r"```(?:\w+\s+)?markpact[^\n]*\n(.*?)```",
    re.DOTALL,
)
_TOON_BLOCK_RE = re.compile(
    r"```toon(?:[^\n]*)\n(.*?)```",
    re.DOTALL,
)
_METADATA_NAME_RE = re.compile(r"\*\*name\*\*[:\s]+`([^`]+)`")
_METADATA_VERSION_RE = re.compile(r"\*\*version\*\*[:\s]+`([^`]+)`")
_REFACTOR_SECTION_RE = re.compile(
    r"## Refactoring Analysis.*?(?=\n## |\Z)",
    re.DOTALL,
)

# Regex patterns for TOON content parsing
_TOON_DECISION_RE = re.compile(
    r"^\s+\[(\d+)\]\s+[○●*-]\s+([\w_]+)\s+→\s+(\S+)",
    re.MULTILINE,
)
_TOON_WHY_RE = re.compile(
    r"^\s+WHY:\s+(.+)$",
    re.MULTILINE,
)
_TOON_REFACTOR_RE = re.compile(
    r"^REFACTOR\[(\d+)\](?::\s*(.*))?$",
    re.MULTILINE,
)
_TOON_LAYER_RE = re.compile(
    r"^\s*(?:[│|]\s*)+(\S+)\s+(\d+)L\s+(\d+)C\s+\S+\s+CC=(\d+)",
    re.MULTILINE,
)
_TOON_DIR_RE = re.compile(
    r"^\s{2}(\S+/)\s+CC",
    re.MULTILINE,
)
_TOON_HEALTH_RE = re.compile(r"^HEALTH\[(\d+)\]", re.MULTILINE)
_TOON_DUP_GROUP_RE = re.compile(
    r"^\s+\[[0-9a-f]+\]\s+[!\s]*\w+\s+(\S+)\s+L=(\d+)\s+N=(\d+)\s+saved=(\d+)",
    re.MULTILINE,
)
_TOON_DUP_FILE_RE = re.compile(
    r"^\s{6}(\S+\.py):(\d+)-(\d+)",
    re.MULTILINE,
)


def parse_sumr(path: Path) -> SumrData:
    """Parse a SUMR.md file and extract refactoring-relevant data."""
    text = path.read_text(encoding="utf-8")
    project_root = path.parent

    name = _METADATA_NAME_RE.search(text)
    version = _METADATA_VERSION_RE.search(text)

    # Extract markpact blocks AND raw toon blocks from refactoring section
    refactor_match = _REFACTOR_SECTION_RE.search(text)
    refactor_raw = refactor_match.group(0) if refactor_match else ""
    refactor_blocks = [m.group(1).strip() for m in _MARKPACT_BLOCK_RE.finditer(refactor_raw)]
    refactor_blocks += [m.group(1).strip() for m in _TOON_BLOCK_RE.finditer(refactor_raw)]

    # Discover toon files in project/
    toon_paths = sorted(project_root.glob("project/*.toon.yaml"))
    toon_paths += sorted(project_root.glob("*.toon.yaml"))

    # Locate refactor_plan.yaml
    plan_candidates = [
        project_root / "project" / "refactor_plan.yaml",
        project_root / "refactor_plan.yaml",
        project_root / "redsl_refactor_plan.yaml",
    ]
    plan_path = next((p for p in plan_candidates if p.exists()), None)

    return SumrData(
        project_name=name.group(1) if name else project_root.name,
        project_version=version.group(1) if version else "0.0.0",
        refactor_sections=refactor_blocks,
        refactor_plan_path=plan_path,
        toon_paths=toon_paths,
    )


def parse_refactor_plan_yaml(yaml_content: str, source: str = "") -> list[dict]:
    """Parse refactor_plan.yaml content into raw task dicts.
    
    The format is a multi-document YAML (``---`` separated) where each
    document is either a ``meta`` block or a ``phase`` block with ``tasks``.
    """
    import yaml
    
    docs = list(yaml.safe_load_all(yaml_content))
    raw_tasks = []

    for doc in docs:
        if not isinstance(doc, dict):
            continue
        phase_tasks = doc.get("tasks", [])
        phase_name = doc.get("name", "")
        for raw in phase_tasks:
            if not isinstance(raw, dict):
                continue
            raw["_phase_name"] = phase_name
            raw["_source"] = source
            raw_tasks.append(raw)

    return raw_tasks


def get_toon_patterns() -> dict[str, re.Pattern]:
    """Get all TOON parsing regex patterns."""
    return {
        "decision": _TOON_DECISION_RE,
        "why": _TOON_WHY_RE,
        "refactor": _TOON_REFACTOR_RE,
        "layer": _TOON_LAYER_RE,
        "dir": _TOON_DIR_RE,
        "health": _TOON_HEALTH_RE,
        "dup_group": _TOON_DUP_GROUP_RE,
        "dup_file": _TOON_DUP_FILE_RE,
    }
