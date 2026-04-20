"""Workflow configuration — declarative YAML-based pipeline definition.

Format: ``apiVersion: redsl.workflow/v1``

The workflow YAML describes what redsl does at every phase of the refactor
cycle.  Any project can ship its own ``redsl.yaml`` to control
behaviour; if none is found redsl falls back to
``redsl/defaults/workflow.yaml``.

Example::

    apiVersion: redsl.workflow/v1
    kind: RefactorWorkflow
    metadata:
      name: my-project-workflow
    spec:
      perceive:
        use_code2llm: true
      decide:
        max_actions: 5
      execute:
        rollback_on_failure: true
      validate:
        steps:
          - name: regix
            enabled: true
            on_failure: warn
          - name: pyqual_gates
            enabled: auto
            on_failure: tune
            tune:
              strategy: conservative
              retry: true
          - name: tests
            enabled: false
            on_failure: rollback
      planfile:
        update_on_apply: true
      reflect:
        enabled: true
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Filename searched in project_dir first, then redsl package defaults
WORKFLOW_FILENAME = "redsl.yaml"

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class PerceiveConfig:
    use_code2llm: bool = False
    use_redup: bool = True


@dataclass
class DecideConfig:
    max_actions: int = 5


@dataclass
class ExecuteConfig:
    use_sandbox: bool = False
    rollback_on_failure: bool = False


@dataclass
class TuneConfig:
    strategy: str = "conservative"  # conservative | aggressive
    retry: bool = True


@dataclass
class ValidateStepConfig:
    name: str = ""
    enabled: Any = True     # True | False | "auto"
    on_failure: str = "warn"  # warn | rollback | stop | tune
    tune: TuneConfig = field(default_factory=TuneConfig)


@dataclass
class ValidateConfig:
    steps: list[ValidateStepConfig] = field(default_factory=list)

    def get_step(self, name: str) -> ValidateStepConfig | None:
        for s in self.steps:
            if s.name == name:
                return s
        return None


@dataclass
class PlanfileConfig:
    update_on_apply: bool = True


@dataclass
class ReflectConfig:
    enabled: bool = True


@dataclass
class WorkflowConfig:
    name: str = "default"
    source: str = "builtin"   # path to loaded file or "builtin"
    perceive: PerceiveConfig = field(default_factory=PerceiveConfig)
    decide: DecideConfig = field(default_factory=DecideConfig)
    execute: ExecuteConfig = field(default_factory=ExecuteConfig)
    validate: ValidateConfig = field(default_factory=ValidateConfig)
    planfile: PlanfileConfig = field(default_factory=PlanfileConfig)
    reflect: ReflectConfig = field(default_factory=ReflectConfig)


# ---------------------------------------------------------------------------
# Default workflow (mirrors previous hardcoded behaviour in cycle.py)
# ---------------------------------------------------------------------------

_DEFAULT_VALIDATE_STEPS = [
    ValidateStepConfig(name="regix",        enabled=True,   on_failure="warn"),
    ValidateStepConfig(name="pyqual_gates", enabled="auto", on_failure="tune",
                       tune=TuneConfig(strategy="conservative", retry=True)),
    ValidateStepConfig(name="tests",        enabled=False,  on_failure="rollback"),
]


def default_workflow() -> WorkflowConfig:
    wf = WorkflowConfig()
    wf.validate.steps = list(_DEFAULT_VALIDATE_STEPS)
    return wf


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def _parse_tune(raw: dict) -> TuneConfig:
    return TuneConfig(
        strategy=raw.get("strategy", "conservative"),
        retry=bool(raw.get("retry", True)),
    )


def _parse_validate_step(raw: dict) -> ValidateStepConfig:
    tune_raw = raw.get("tune", {})
    return ValidateStepConfig(
        name=raw.get("name", ""),
        enabled=raw.get("enabled", True),
        on_failure=raw.get("on_failure", "warn"),
        tune=_parse_tune(tune_raw) if isinstance(tune_raw, dict) else TuneConfig(),
    )


def _parse_workflow(data: dict, source: str) -> WorkflowConfig:
    spec = data.get("spec", {})
    meta = data.get("metadata", {})

    perceive_raw = spec.get("perceive", {})
    decide_raw   = spec.get("decide", {})
    execute_raw  = spec.get("execute", {})
    validate_raw = spec.get("validate", {})
    planfile_raw = spec.get("planfile", {})
    reflect_raw  = spec.get("reflect", {})

    steps_raw = validate_raw.get("steps", None)
    if steps_raw is not None:
        steps = [_parse_validate_step(s) for s in steps_raw if isinstance(s, dict)]
    else:
        steps = list(_DEFAULT_VALIDATE_STEPS)

    return WorkflowConfig(
        name=meta.get("name", "unnamed"),
        source=source,
        perceive=PerceiveConfig(
            use_code2llm=bool(perceive_raw.get("use_code2llm", False)),
            use_redup=bool(perceive_raw.get("use_redup", True)),
        ),
        decide=DecideConfig(
            max_actions=int(decide_raw.get("max_actions", 5)),
        ),
        execute=ExecuteConfig(
            use_sandbox=bool(execute_raw.get("use_sandbox", False)),
            rollback_on_failure=bool(execute_raw.get("rollback_on_failure", False)),
        ),
        validate=ValidateConfig(steps=steps),
        planfile=PlanfileConfig(
            update_on_apply=bool(planfile_raw.get("update_on_apply", True)),
        ),
        reflect=ReflectConfig(
            enabled=bool(reflect_raw.get("enabled", True)),
        ),
    )


def load_workflow(project_dir: Path | None = None) -> WorkflowConfig:
    """Load workflow config for *project_dir*.

    Search order:
    1. ``<project_dir>/redsl.yaml``
    2. ``<redsl_package>/defaults/workflow.yaml``
    3. Built-in defaults (no file needed)
    """
    candidates: list[Path] = []

    if project_dir is not None:
        candidates.append(project_dir / WORKFLOW_FILENAME)

    # Package-bundled default
    pkg_default = Path(__file__).parent.parent / "defaults" / "workflow.yaml"
    candidates.append(pkg_default)

    for path in candidates:
        if path.exists():
            try:
                import yaml  # type: ignore[import-untyped]
                with open(path, encoding="utf-8") as fh:
                    data = yaml.safe_load(fh) or {}
                api = data.get("apiVersion", "")
                if not api.startswith("redsl.workflow"):
                    logger.warning("workflow: %s has unexpected apiVersion '%s', skipping", path, api)
                    continue
                wf = _parse_workflow(data, source=str(path))
                logger.debug("workflow: loaded from %s", path)
                return wf
            except Exception as exc:
                logger.warning("workflow: failed to load %s: %s", path, exc)

    logger.debug("workflow: using builtin defaults")
    return default_workflow()


# ---------------------------------------------------------------------------
# YAML template for `redsl workflow init`
# ---------------------------------------------------------------------------

WORKFLOW_TEMPLATE = """\
apiVersion: redsl.workflow/v1
kind: RefactorWorkflow
metadata:
  name: {name}
  description: Workflow refaktoryzacji dla projektu {name}

spec:
  # ── PERCEPCJA ──────────────────────────────────────────────────────────
  perceive:
    use_code2llm: false    # true = głębsza analiza przez code2llm
    use_redup: true        # true = wykrywanie duplikatów

  # ── DECYZJE ────────────────────────────────────────────────────────────
  decide:
    max_actions: 5         # max liczba plików do refaktoryzacji na cykl

  # ── WYKONANIE ──────────────────────────────────────────────────────────
  execute:
    use_sandbox: false          # true = testowe środowisko przed apply
    rollback_on_failure: false  # true = cofnij zmiany jeśli walidacja failuje

  # ── WALIDACJA (kroki wykonywane po apply, w kolejności) ────────────────
  validate:
    steps:
      - name: regix
        enabled: true
        on_failure: warn       # warn | rollback | stop

      - name: pyqual_gates
        enabled: auto          # auto = uruchom jeśli pyqual.yaml istnieje w projekcie
        on_failure: tune       # tune = pyqual tune --conservative, potem retry
        tune:
          strategy: conservative   # conservative | aggressive
          retry: true

      - name: tests
        enabled: false         # true = uruchom testy projektu po zmianach
        on_failure: rollback

  # ── PLANFILE ───────────────────────────────────────────────────────────
  planfile:
    update_on_apply: true      # true = oznacz zadania done po apply

  # ── REFLEKSJA ──────────────────────────────────────────────────────────
  reflect:
    enabled: true              # true = redsl uczy się z każdego cyklu
"""
