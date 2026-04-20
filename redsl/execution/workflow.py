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
    llm_model: str = "auto"   # auto = use env/config, or explicit e.g. "openrouter/x-ai/grok-code-fast-1"
    llm_temperature: float | None = None  # None = use env/config default


@dataclass
class ExecuteConfig:
    use_sandbox: bool = False
    rollback_on_failure: bool = False


@dataclass
class TuneConfig:
    strategy: str = "conservative"  # conservative | aggressive
    retry: bool = True
    run_on_missing_metrics: bool = True   # run pyqual run first if tune reports no metrics
    create_planfile_task_on_failure: bool = True  # add planfile ticket if gates still fail after tune


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
class StorageConfig:
    """Controls where redsl stores its logs and LLM chat history."""

    # Base directory for all redsl artefacts (relative to project root)
    base_dir: str = ".redsl"

    # System log — WARNING+ to stderr, INFO+ to log file
    # Relative path created inside <project>/logs/
    system_log_enabled: bool = True

    # LLM chat log — every prompt + response recorded as JSONL
    # Path: <project>/.redsl/chat.jsonl
    chat_log_enabled: bool = True
    chat_log_filename: str = "chat.jsonl"

    # history.jsonl — decision / action / outcome events
    history_enabled: bool = True
    history_filename: str = "history.jsonl"


@dataclass
class DeployConfig:
    """Controls whether and how redsl performs push / publish after a cycle.

    ``enabled``:
        - ``"auto"``  — detect from project files (pyqual.yaml, Taskfile, Makefile)
        - ``True``    — always run detected or explicit commands
        - ``False``   — never deploy automatically

    ``push`` / ``publish``:
        - ``"auto"``  — use detected command for this project
        - ``True``    — force run (must be detectable or ``command`` set)
        - ``False``   — skip this action

    ``on_success_only``:
        If True, deploy only when the refactor cycle applied ≥1 action *and*
        all validator steps passed.
    """

    enabled: Any = "auto"   # auto | true | false
    push: Any = "auto"      # auto | true | false
    publish: Any = False    # auto | true | false  (default: skip registry publish)
    on_success_only: bool = True


@dataclass
class ProjectMapConfig:
    """Inventory of configuration files found in the project.

    Populated by ``redsl workflow scan`` and embedded in ``redsl.yaml``.
    The map is informational — used by redsl phases to find the correct
    sources of truth for build, deploy, environment, etc.

    Each key is a category name, value is a list of project-relative paths.
    Categories: package, quality, task_runner, container, ci_cd,
                environment, redsl, versioning, dependencies, deploy
    """

    categories: dict[str, list[str]] = field(default_factory=dict)

    def get(self, category: str) -> list[str]:
        return self.categories.get(category, [])

    def all_files(self) -> list[str]:
        result: list[str] = []
        for files in self.categories.values():
            result.extend(files)
        return result


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
    storage: StorageConfig = field(default_factory=StorageConfig)
    deploy: DeployConfig = field(default_factory=DeployConfig)
    project_map: ProjectMapConfig = field(default_factory=ProjectMapConfig)


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

def _parse_storage(raw: dict) -> StorageConfig:
    return StorageConfig(
        base_dir=raw.get("base_dir", ".redsl"),
        system_log_enabled=bool(raw.get("system_log_enabled", True)),
        chat_log_enabled=bool(raw.get("chat_log_enabled", True)),
        chat_log_filename=raw.get("chat_log_filename", "chat.jsonl"),
        history_enabled=bool(raw.get("history_enabled", True)),
        history_filename=raw.get("history_filename", "history.jsonl"),
    )


def _parse_deploy(raw: dict) -> DeployConfig:
    def _coerce(val: Any, default: Any) -> Any:
        if isinstance(val, bool):
            return val
        if isinstance(val, str) and val.lower() == "auto":
            return "auto"
        return default

    return DeployConfig(
        enabled=_coerce(raw.get("enabled", "auto"), "auto"),
        push=_coerce(raw.get("push", "auto"), "auto"),
        publish=_coerce(raw.get("publish", False), False),
        on_success_only=bool(raw.get("on_success_only", True)),
    )


def _parse_project_map(raw: dict) -> ProjectMapConfig:
    categories: dict[str, list[str]] = {}
    for key, val in raw.items():
        if isinstance(val, list):
            categories[key] = [str(v) for v in val if v]
    return ProjectMapConfig(categories=categories)


def _parse_tune(raw: dict) -> TuneConfig:
    return TuneConfig(
        strategy=raw.get("strategy", "conservative"),
        retry=bool(raw.get("retry", True)),
        run_on_missing_metrics=bool(raw.get("run_on_missing_metrics", True)),
        create_planfile_task_on_failure=bool(raw.get("create_planfile_task_on_failure", True)),
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
    storage_raw  = spec.get("storage", {})
    deploy_raw   = spec.get("deploy", {})
    project_map_raw = spec.get("project_map", {})

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
            llm_model=decide_raw.get("llm_model", "auto"),
            llm_temperature=float(decide_raw["llm_temperature"]) if "llm_temperature" in decide_raw else None,
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
        storage=_parse_storage(storage_raw) if isinstance(storage_raw, dict) else StorageConfig(),
        deploy=_parse_deploy(deploy_raw) if isinstance(deploy_raw, dict) else DeployConfig(),
        project_map=_parse_project_map(project_map_raw) if isinstance(project_map_raw, dict) else ProjectMapConfig(),
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
    llm_model: auto        # auto = env LLM_MODEL / domyślny; lub np. openrouter/x-ai/grok-code-fast-1
    llm_temperature: null  # null = użyj domyślnej temperatury z konfiguracji

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
        on_failure: tune       # tune = jeśli gates fail:
                               #   1. pyqual tune --conservative (dopasuj progi)
                               #   2. jeśli brak metryk → najpierw pyqual run (zbierz metryki)
                               #   3. retry pyqual gates
                               #   4. jeśli nadal fail → dodaj ticket do planfile.yaml
        tune:
          strategy: conservative              # conservative | aggressive
          retry: true                         # ponów gates po tune
          run_on_missing_metrics: true        # uruchom pyqual run gdy brak metryk
          create_planfile_task_on_failure: true  # dodaj ticket do planfile gdy gates nadal fail

      - name: tests
        enabled: false         # true = uruchom testy projektu po zmianach
        on_failure: rollback

  # ── PLANFILE ───────────────────────────────────────────────────────────
  planfile:
    update_on_apply: true      # true = oznacz zadania done po apply

  # ── REFLEKSJA ──────────────────────────────────────────────────────────
  reflect:
    enabled: true              # true = redsl uczy się z każdego cyklu

  # ── STORAGE — gdzie trafiają logi i konwersacje LLM ───────────────────
  storage:
    base_dir: .redsl            # katalog artefaktów w projekcie
    system_log_enabled: true    # logs/redsl_YYYYMMDD.log
    chat_log_enabled: true      # .redsl/chat.jsonl — każdy prompt + response
    chat_log_filename: chat.jsonl
    history_enabled: true       # .redsl/history.jsonl — decyzje i wyniki
    history_filename: history.jsonl

  # ── DEPLOY — push do git i/lub publish do registry po cyklu ───────────
  deploy:
    enabled: auto           # auto | true | false
    push: auto              # auto = wykryj z pyqual.yaml / Taskfile / Makefile
    publish: false          # domyślnie NIE publikuj do PyPI/registry
    on_success_only: true   # deployuj tylko gdy cycle zastosował ≥1 akcję
"""
