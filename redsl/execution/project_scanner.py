"""Project configuration file scanner for redsl.

Scans a project directory and builds a ``ProjectMap`` — a structured
inventory of all configuration files relevant to:

- Package metadata        (pyproject.toml, setup.cfg, setup.py)
- Quality gates           (pyqual.yaml, .pre-commit-config.yaml)
- Task runners            (Taskfile.yml, Makefile, project.sh, scripts/)
- Containers              (Dockerfile*, docker-compose*.yml)
- CI/CD                   (.github/workflows/, .gitlab-ci.yml, .circleci/)
- Environment             (.env.example, .envrc, *.env)
- Redsl artefacts         (redsl.yaml, planfile.yaml, goal.yaml)
- Versioning              (VERSION, CHANGELOG.md, CHANGELOG.rst)
- Dependencies            (requirements*.txt, Pipfile, poetry.lock)

The scan result can be embedded into ``redsl.yaml`` under ``project_map:``
so that every redsl run has a stable, human-readable reference of *where*
to find each category of config.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Categories and their detection patterns
# ---------------------------------------------------------------------------

# (category_key, description, list-of-glob-patterns-or-exact-names)
_CATEGORIES: list[tuple[str, str, list[str]]] = [
    ("package", "Package metadata", [
        "pyproject.toml", "setup.cfg", "setup.py",
        "package.json", "Cargo.toml", "go.mod",
    ]),
    ("quality", "Quality gates & linting", [
        "pyqual.yaml", ".pre-commit-config.yaml",
        ".flake8", ".ruff.toml", "ruff.toml",
        "mypy.ini", ".mypy.ini", ".pylintrc",
        "sonar-project.properties",
    ]),
    ("task_runner", "Task runners & build scripts", [
        "Taskfile.yml", "Taskfile.yaml",
        "Makefile", "makefile",
        "project.sh", "build.sh",
        "scripts/push.sh", "scripts/publish.sh", "scripts/release.sh",
        "scripts/deploy.sh", "scripts/build.sh",
        "bin/push", "bin/publish", "bin/release", "bin/deploy",
    ]),
    ("container", "Container & compose", [
        "Dockerfile", "Dockerfile.dev", "Dockerfile.prod",
        "docker-compose.yml", "docker-compose.yaml",
        "docker-compose-prod.yml", "docker-compose-dev.yml",
        "docker-compose-prod.yaml", "docker-compose-dev.yaml",
        ".dockerignore",
    ]),
    ("ci_cd", "CI/CD pipelines", [
        ".github/workflows",           # directory
        ".gitlab-ci.yml",
        ".circleci/config.yml",
        "Jenkinsfile",
        ".travis.yml",
        "azure-pipelines.yml",
        "bitbucket-pipelines.yml",
    ]),
    ("environment", "Environment & secrets", [
        ".env.example", ".env.sample", ".envrc",
        ".env.template", "env.example",
    ]),
    ("redsl", "Redsl & project management", [
        "redsl.yaml", "planfile.yaml", "goal.yaml",
        "pyqual.yaml",   # also in quality but central to project management
    ]),
    ("versioning", "Version & changelog", [
        "VERSION", "version.txt",
        "CHANGELOG.md", "CHANGELOG.rst", "CHANGELOG.txt",
        "CHANGES.md", "HISTORY.md",
    ]),
    ("dependencies", "Dependencies", [
        "requirements.txt", "requirements-dev.txt",
        "requirements-test.txt", "requirements-prod.txt",
        "Pipfile", "Pipfile.lock",
        "poetry.lock", "pdm.lock", "uv.lock",
    ]),
    ("deploy", "Deploy configuration", [
        "vallm.toml", "deploy.yml", "deploy.yaml",
        "release.yml", "release.yaml",
        ".releaserc", ".releaserc.json", ".releaserc.yaml",
        "semantic-release.config.js",
    ]),
]

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class ProjectMap:
    """Structured inventory of config files found in a project."""

    project_dir: str = ""
    categories: dict[str, list[str]] = field(default_factory=dict)
    # Flat index: relative path → category key
    index: dict[str, str] = field(default_factory=dict)

    def all_files(self) -> list[str]:
        result: list[str] = []
        for files in self.categories.values():
            result.extend(files)
        return result

    def get(self, category: str) -> list[str]:
        return self.categories.get(category, [])

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_dir": self.project_dir,
            "categories": {k: v for k, v in self.categories.items() if v},
        }

    def summary(self) -> str:
        parts = []
        for cat, files in self.categories.items():
            if files:
                parts.append(f"{cat}({len(files)})")
        return " ".join(parts)


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------

def scan_project(project_dir: Path) -> ProjectMap:
    """Scan *project_dir* and return a :class:`ProjectMap`.

    Only files that actually exist are recorded.  Directories (like
    ``.github/workflows``) are recorded as-is if they exist.
    """
    project_dir = Path(project_dir).resolve()
    result = ProjectMap(project_dir=str(project_dir))

    for cat_key, _desc, patterns in _CATEGORIES:
        found: list[str] = []
        for pattern in patterns:
            candidate = project_dir / pattern
            if candidate.exists():
                rel = str(Path(pattern))
                if rel not in result.index:
                    found.append(rel)
                    result.index[rel] = cat_key
        if found:
            existing = result.categories.get(cat_key, [])
            # dedup keeping order
            seen = set(existing)
            for f in found:
                if f not in seen:
                    existing.append(f)
                    seen.add(f)
            result.categories[cat_key] = existing

    # Extra: scan scripts/ and bin/ for executable push/publish/deploy scripts
    _scan_scripts_dir(project_dir, result)

    logger.debug("project_scanner: %s → %s", project_dir.name, result.summary())
    return result


def _scan_scripts_dir(project_dir: Path, result: ProjectMap) -> None:
    """Scan scripts/ and bin/ for push/publish/deploy scripts."""
    deploy_keywords = {"push", "publish", "deploy", "release", "build"}
    for scripts_dir_name in ("scripts", "bin"):
        scripts_dir = project_dir / scripts_dir_name
        if not scripts_dir.is_dir():
            continue
        for f in sorted(scripts_dir.iterdir()):
            if f.is_file() and any(kw in f.stem.lower() for kw in deploy_keywords):
                rel = f.relative_to(project_dir).as_posix()
                cat = "task_runner"
                if rel not in result.index:
                    result.index[rel] = cat
                    result.categories.setdefault(cat, []).append(rel)


# ---------------------------------------------------------------------------
# YAML serialisation helper
# ---------------------------------------------------------------------------

def project_map_to_yaml_block(pm: ProjectMap, indent: int = 2) -> str:
    """Render a ProjectMap as a YAML block suitable for embedding in redsl.yaml."""
    pad = " " * indent
    lines: list[str] = ["project_map:"]
    for cat_key, _desc, _ in _CATEGORIES:
        files = pm.categories.get(cat_key, [])
        if not files:
            continue
        category_names = {k: d for k, d, _ in _CATEGORIES}
        desc = category_names.get(cat_key, cat_key)
        lines.append(f"{pad}# {desc}")
        lines.append(f"{pad}{cat_key}:")
        for f in files:
            lines.append(f"{pad}  - {f}")
    return "\n".join(lines)
