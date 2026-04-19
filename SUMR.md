# Ze źródeł

SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Workflows](#workflows)
- [Quality Pipeline (`pyqual.yaml`)](#quality-pipeline-pyqualyaml)
- [Dependencies](#dependencies)
- [Source Map](#source-map)
- [Refactoring Analysis](#refactoring-analysis)
- [Intent](#intent)

## Metadata

- **name**: `redsl`
- **version**: `1.2.43`
- **python_requires**: `>=3.11`
- **license**: Apache-2.0
- **ai_model**: `openrouter/openai/gpt-5-mini`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, requirements.txt, Taskfile.yml, Makefile, app.doql.css, goal.yaml, .env.example, Dockerfile, docker-compose.yml, src(5 mod), project/(5 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.css`)

```css markpact:doql path=app.doql.css
app {
  name: "redsl";
  version: "1.2.28";
}

interface[type="cli"] {
  framework: click;
}
interface[type="cli"] page[name="redsl"] {

}

workflow[name="install"] {
  trigger: "manual";
  step-1: run cmd=$(PIP) install -r requirements.txt;
}

workflow[name="dev-install"] {
  trigger: "manual";
  step-1: run cmd=$(PIP) install -r requirements.txt;
  step-2: run cmd=$(PIP) install -e ".[dev]";
}

workflow[name="test"] {
  trigger: "manual";
  step-1: run cmd=$(PYTHON) -m pytest tests/ -v -m "not slow";
}

workflow[name="test-fast"] {
  trigger: "manual";
  step-1: run cmd=$(PYTHON) -m pytest tests/ -q -m "not slow and not integration and not e2e";
}

workflow[name="test-all"] {
  trigger: "manual";
  step-1: run cmd=$(PYTHON) -m pytest tests/ -v;
}

workflow[name="lint"] {
  trigger: "manual";
  step-1: run cmd=$(PYTHON) -m ruff check redsl/ tests/;
}

workflow[name="type-check"] {
  trigger: "manual";
  step-1: run cmd=$(PYTHON) -m mypy redsl/;
}

workflow[name="format"] {
  trigger: "manual";
  step-1: run cmd=$(PYTHON) -m ruff format redsl/ tests/;
  step-2: run cmd=$(PYTHON) -m ruff check --fix redsl/ tests/;
}

workflow[name="format-check"] {
  trigger: "manual";
  step-1: run cmd=$(PYTHON) -m ruff format --check redsl/ tests/;
}

workflow[name="docker-up"] {
  trigger: "manual";
  step-1: run cmd=$(DOCKER_COMPOSE) up -d;
}

workflow[name="docker-down"] {
  trigger: "manual";
  step-1: run cmd=$(DOCKER_COMPOSE) down;
}

workflow[name="docker-build"] {
  trigger: "manual";
  step-1: run cmd=$(DOCKER_COMPOSE) build;
}

workflow[name="run"] {
  trigger: "manual";
  step-1: depend target=docker-up;
}

workflow[name="run-local"] {
  trigger: "manual";
  step-1: run cmd=$(PYTHON) -m uvicorn redsl.api:app --reload --host 0.0.0.0 --port 8000;
}

workflow[name="clean"] {
  trigger: "manual";
  step-1: run cmd=find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true;
  step-2: run cmd=find . -type f -name "*.pyc" -delete 2>/dev/null || true;
  step-3: run cmd=find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true;
  step-4: run cmd=find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true;
  step-5: run cmd=rm -rf refactor_output/ 2>/dev/null || true;
}

workflow[name="fmt"] {
  trigger: "manual";
  step-1: run cmd=ruff format .;
}

workflow[name="build"] {
  trigger: "manual";
  step-1: run cmd=python -m build;
}

workflow[name="health"] {
  trigger: "manual";
  step-1: run cmd=docker compose ps;
  step-2: run cmd=docker compose exec app echo "Health check passed";
}

workflow[name="up"] {
  trigger: "manual";
  step-1: run cmd=docker compose up -d;
}

workflow[name="down"] {
  trigger: "manual";
  step-1: run cmd=docker compose down;
}

workflow[name="logs"] {
  trigger: "manual";
  step-1: run cmd=docker compose logs -f;
}

workflow[name="ps"] {
  trigger: "manual";
  step-1: run cmd=docker compose ps;
}

workflow[name="import-makefile-hint"] {
  trigger: "manual";
  step-1: run cmd=echo 'Run: taskfile import Makefile to import existing targets.';
}

workflow[name="help"] {
  trigger: "manual";
  step-1: run cmd=echo \"Dost\u0119pne komendy:\; 
  step-2: run cmd=echo \"  install       - Instalacja zale\u017Cno\u015Bci produkcyjnych\; 
  step-3: run cmd=echo \"  dev-install   - Instalacja zale\u017Cno\u015Bci deweloperskich\; 
  step-4: run cmd=echo \"  test          - Uruchomienie test\xF3w pytest (bez slow)\; 
  step-5: run cmd=echo "  test-fast     - Szybkie testy (bez slow/integration/e2e)";
  step-6: run cmd=echo \"  test-all      - Wszystkie testy w\u0142\u0105cznie z slow\; 
  step-7: run cmd=echo "  lint          - Sprawdzenie lintingu ruff";
  step-8: run cmd=echo \"  type-check    - Sprawdzenie typ\xF3w mypy\; 
  step-9: run cmd=echo "  format        - Formatowanie kodu ruff";
  step-10: run cmd=echo "  format-check  - Sprawdzenie formatowania kodu";
  step-11: run cmd=echo \"  docker-up     - Uruchomienie us\u0142ug Docker\; 
  step-12: run cmd=echo \"  docker-down   - Zatrzymanie us\u0142ug Docker\; 
  step-13: run cmd=echo \"  docker-build  - Budowanie obraz\xF3w Docker\; 
  step-14: run cmd=echo "  run           - Uruchomienie aplikacji w Docker";
  step-15: run cmd=echo "  run-local     - Uruchomienie aplikacji lokalnie";
  step-16: run cmd=echo \"  clean         - Czyszczenie plik\xF3w tymczasowych\; 
}

deploy {
  target: docker-compose;
  compose_file: docker-compose.yml;
}

environment[name="local"] {
  runtime: docker-compose;
  env_file: ".env";
}

workflow[name="all"] {
  trigger: "manual";
  step-1: run cmd=taskfile run install;
  step-2: run cmd=taskfile run lint;
  step-3: run cmd=taskfile run test;
}
```

### Source Modules

- `redsl.config`
- `redsl.consciousness_loop`
- `redsl.history`
- `redsl.main`
- `redsl.orchestrator`

## Workflows

### Taskfile Tasks (`Taskfile.yml`)

```yaml markpact:taskfile path=Taskfile.yml
version: '1'
name: redsl
description: Minimal Taskfile
variables:
  APP_NAME: redsl
environments:
  local:
    container_runtime: docker
    compose_command: docker compose
pipeline:
  python_version: "3.12"
  runner_image: ubuntu-latest
  branches: [main]
  cache: [~/.cache/pip]
  artifacts: [dist/]

  stages:
    - name: lint
      tasks: [lint]

    - name: test
      tasks: [test]

    - name: build
      tasks: [build]
      when: "branch:main"

tasks:
  install:
    desc: Install Python dependencies (editable)
    cmds:
    - pip install -e .[dev]
  test:
    desc: Run pytest suite
    cmds:
    - pytest -q
  lint:
    desc: Run ruff lint check
    cmds:
    - ruff check .
  fmt:
    desc: Auto-format with ruff
    cmds:
    - ruff format .
  build:
    desc: Build wheel + sdist
    cmds:
    - python -m build
  clean:
    desc: Remove build artefacts
    cmds:
    - rm -rf build/ dist/ *.egg-info
  up:
    desc: Start services via docker compose
    cmds:
    - docker compose up -d
  down:
    desc: Stop services
    cmds:
    - docker compose down
  logs:
    desc: Tail compose logs
    cmds:
    - docker compose logs -f
  ps:
    desc: Show running compose services
    cmds:
    - docker compose ps
  docker-build:
    desc: Build docker image
    cmds:
    - docker build -t redsl:latest .
  help:
    desc: '[imported from Makefile] help'
    cmds:
    - "echo \"Dost\u0119pne komendy:\""
    - "echo \"  install       - Instalacja zale\u017Cno\u015Bci produkcyjnych\""
    - "echo \"  dev-install   - Instalacja zale\u017Cno\u015Bci deweloperskich\""
    - "echo \"  test          - Uruchomienie test\xF3w pytest (bez slow)\""
    - echo "  test-fast     - Szybkie testy (bez slow/integration/e2e)"
    - "echo \"  test-all      - Wszystkie testy w\u0142\u0105cznie z slow\""
    - echo "  lint          - Sprawdzenie lintingu ruff"
    - "echo \"  type-check    - Sprawdzenie typ\xF3w mypy\""
    - echo "  format        - Formatowanie kodu ruff"
    - echo "  format-check  - Sprawdzenie formatowania kodu"
    - "echo \"  docker-up     - Uruchomienie us\u0142ug Docker\""
    - "echo \"  docker-down   - Zatrzymanie us\u0142ug Docker\""
    - "echo \"  docker-build  - Budowanie obraz\xF3w Docker\""
    - echo "  run           - Uruchomienie aplikacji w Docker"
    - echo "  run-local     - Uruchomienie aplikacji lokalnie"
    - "echo \"  clean         - Czyszczenie plik\xF3w tymczasowych\""
  dev-install:
    desc: '[imported from Makefile] dev-install'
    cmds:
    - $(PIP) install -r requirements.txt
    - $(PIP) install -e ".[dev]"
  test-fast:
    desc: '[imported from Makefile] test-fast'
    cmds:
    - $(PYTHON) -m pytest tests/ -q -m "not slow and not integration and not e2e"
  test-all:
    desc: '[imported from Makefile] test-all'
    cmds:
    - $(PYTHON) -m pytest tests/ -v
  type-check:
    desc: '[imported from Makefile] type-check'
    cmds:
    - $(PYTHON) -m mypy redsl/
  format:
    desc: '[imported from Makefile] format'
    cmds:
    - $(PYTHON) -m ruff format redsl/ tests/
    - $(PYTHON) -m ruff check --fix redsl/ tests/
  format-check:
    desc: '[imported from Makefile] format-check'
    cmds:
    - $(PYTHON) -m ruff format --check redsl/ tests/
  docker-up:
    desc: '[imported from Makefile] docker-up'
    cmds:
    - $(DOCKER_COMPOSE) up -d
  docker-down:
    desc: '[imported from Makefile] docker-down'
    cmds:
    - $(DOCKER_COMPOSE) down
  run:
    desc: '[imported from Makefile] run'
    deps:
    - docker-up
  run-local:
    desc: '[imported from Makefile] run-local'
    cmds:
    - $(PYTHON) -m uvicorn redsl.api:app --reload --host 0.0.0.0 --port 8000
  health:
    desc: '[from doql] workflow: health'
    cmds:
    - docker compose ps
    - docker compose exec app echo "Health check passed"
  import-makefile-hint:
    desc: '[from doql] workflow: import-makefile-hint'
    cmds:
    - 'echo ''Run: taskfile import Makefile to import existing targets.'''
  all:
    desc: Run install, lint, test
    cmds:
    - taskfile run install
    - taskfile run lint
    - taskfile run test
```

## Quality Pipeline (`pyqual.yaml`)

```yaml markpact:pyqual path=pyqual.yaml
project_root: .
package_name: redsl
include:
- '**/*.py'
exclude:
- '**/__pycache__/**'
- '**/node_modules/**'
- '**/.venv/**'
- '**/venv/**'
- '**/.git/**'
- '**/build/**'
- '**/dist/**'
- '**/*.egg-info/**'
- '**/tests/**'
- 'archive/**'
- 'redsl_output/**'
- 'refactor_output/**'
- 'vallm_analysis/**'
- 'vallm_json/**'
- 'vallm_text/**'
tools:
  parallel: true
  cache: true
  ruff:
    enabled: true
    max_line_length: 88
    select:
    - E
    - F
    - W
    - I
    - C
    - B
    - A
    - COM
    - C4
    - DTZ
    - T10
    - EM
    - EXE
    - FA
    - ISC
    - ICN
    - G
    - INP
    - PIE
    - T20
    - PT
    - Q
    - RSE
    - RET
    - SIM
    - TID
    - TCH
    - ARG
    - PTH
    - ERA
    - PGH
    - PL
    - TRY
    - FLAKE8-PYTESTSTYLE
    - RUF
    ignore:
    - E501
    - PLR0913
    - PLR0915
  mypy:
    enabled: true
    strict: false
    ignore_missing_imports: true
    disallow_untyped_defs: false
    disallow_incomplete_defs: false
    check_untyped_defs: true
    disallow_untyped_decorators: false
    no_implicit_optional: true
    warn_redundant_casts: true
    warn_unused_ignores: true
    warn_no_return: true
    warn_unreachable: true
    strict_equality: true
  isort:
    enabled: true
    profile: black
    multi_line_output: 3
    line_length: 88
  bandit:
    enabled: true
    exclude_dirs:
    - tests
  coverage:
    enabled: true
    fail_under: 80
  pydocstyle:
    enabled: true
    convention: google
  vulture:
    enabled: true
    min_confidence: 60
performance:
  max_workers: 4
  cache_size: 104857600
  chunk_size: 10
metrics:
  complexity:
    enabled: true
    max_complexity: 10
    tools:
    - radon
    - xenon
  maintainability:
    enabled: true
    min_maintainability: 70
    tools:
    - radon
  duplication:
    enabled: true
    min_similarity: 0.85
    tools:
    - jscpd
  test_coverage:
    enabled: true
    min_coverage: 80
    tools:
    - coverage
rules:
  unused-imports:
    enabled: true
    tools:
    - ruff
    - autoflake
    severity: error
  magic-numbers:
    enabled: true
    threshold: 2
    exclude:
    - 0
    - 1
    - -1
    - 2
    severity: warning
  print-statements:
    enabled: true
    severity: warning
  TODO-comments:
    enabled: true
    severity: info
  long-lines:
    enabled: true
    max_length: 88
    severity: warning
  missing-docstrings:
    enabled: true
    public_only: true
    severity: warning
  type-hints:
    enabled: true
    require_return_type: true
    require_param_types: false
    severity: warning
  security-issues:
    enabled: true
    tools:
    - bandit
    severity: error
  code-smells:
    enabled: true
    tools:
    - ruff
    - mypy
    severity: warning
plugins:
  enabled: true
  directories:
  - ~/.pyqual/plugins
  - ./.pyqual/plugins
environments:
  development:
    rules:
      print-statements:
        enabled: true
      magic-numbers:
        enabled: false
      TODO-comments:
        severity: warning
    performance:
      max_workers: 2
  production:
    rules:
      print-statements:
        enabled: false
      magic-numbers:
        enabled: true
      TODO-comments:
        severity: error
    performance:
      max_workers: 8
  testing:
    rules:
      print-statements:
        enabled: true
      magic-numbers:
        enabled: false
      missing-docstrings:
        enabled: false
    metrics:
      test_coverage:
        enabled: true
        min_coverage: 90
reporting:
  output_formats:
  - yaml
  - json
  - html
  include_summary: true
  include_details: true
  include_recommendations: true
  output_file: pyqual_report
```

## Dependencies

### Runtime

```text markpact:deps python
fastapi>=0.115.0
uvicorn>=0.44.0
pydantic>=2.10.0
litellm>=1.52.0
chromadb>=0.6.0
pyyaml>=6.0.2
rich>=13.9.0
httpx>=0.28.0
click>=8.1.7
python-dotenv>=1.0.1
goal>=2.1.0
costs>=0.1.20
pfix>=0.1.60
```

### Development

```text markpact:deps python scope=dev
pytest>=9.0
pytest-xdist>=3.5
pytest-cov>=7.1
ruff>=0.15.0
mypy>=1.13
goal>=2.1.0
costs>=0.1.20
pfix>=0.1.60
```

## Source Map

*Top 5 modules by symbol density — signatures for LLM orientation.*

### `redsl.main` (`redsl/main.py`)

```python
def _get_orchestrator(model)  # CC=2, fan=2
def _analysis_source_method(orch, path)  # CC=2, fan=3
def _analysis_function_metrics(result)  # CC=4, fan=1
def _print_analysis_summary(result, path, source_method)  # CC=2, fan=1
def _print_top_functions(func_metrics)  # CC=5, fan=1
def _print_alerts(result, func_metrics)  # CC=6, fan=2
def _print_duplicates(result)  # CC=3, fan=3
def _print_analysis_plan(result, path)  # CC=5, fan=7
def cmd_analyze(project_dir)  # CC=2, fan=13
def cmd_explain(project_dir)  # CC=1, fan=4
def _print_refactor_report(report, orch)  # CC=3, fan=3
def cmd_refactor(project_dir, dry_run, auto, max_actions, model)  # CC=2, fan=5
def cmd_memory_stats()  # CC=1, fan=4
def cmd_serve(port, host)  # CC=1, fan=1
def _print_usage()  # CC=1, fan=1
def _get_arg(args, name, default)  # CC=4, fan=2
def _has_flag(args, name)  # CC=1, fan=0
def _dispatch_analyze(args)  # CC=1, fan=2
def _dispatch_explain(args)  # CC=1, fan=2
def _dispatch_refactor(args)  # CC=2, fan=4
def _dispatch_memory_stats(args)  # CC=1, fan=1
def _dispatch_serve(args)  # CC=1, fan=3
def main()  # CC=3, fan=6
```

### `redsl.history` (`redsl/history.py`)

```python
def _default_history_dir(project_dir)  # CC=1, fan=0
class HistoryEvent:  # A single persisted event in the refactor history.
class HistoryWriter:  # Append-only history logger backed by .redsl/history.jsonl.
    def __init__(project_dir)  # CC=1
    def record(event)  # CC=1
    def record_event(event_type)  # CC=1
    def decision_signature()  # CC=2
    def has_recent_signature(signature, limit)  # CC=5
class HistoryReader:  # Read-only access to .redsl/history.jsonl for querying and de
    def __init__(project_dir)  # CC=1
    def load_events()  # CC=5
    def filter_by_file(target_file)  # CC=3
    def filter_by_type(event_type)  # CC=3
    def has_recent_proposal(target_file, action)  # CC=7
    def has_recent_ticket(title_prefix)  # CC=7
    def _format_event_header(ev)  # CC=3
    def _format_event_details(ev)  # CC=5
    def _maybe_add_cycle_header(ev, current_cycle)  # CC=3
    def generate_decision_report()  # CC=3
```

### `redsl.consciousness_loop` (`redsl/consciousness_loop.py`)

```python
def main_loop()  # CC=4, fan=6
class ConsciousnessLoop:  # Ciągła pętla „świadomości" agenta.
    def __init__(project_dir, interval_seconds, config)  # CC=2
    def run()  # CC=5
    def _inner_thought(cycle)  # CC=3
    def _self_assessment(cycle)  # CC=3
    def _profile_performance(cycle)  # CC=3
    def stop()  # CC=1
```

### `redsl.config` (`redsl/config.py`)

```python
def _default_llm_model()  # CC=6, fan=1
def _resolve_provider_key(model)  # CC=6, fan=3
class LLMConfig:  # Konfiguracja warstwy LLM.
    def is_local()  # CC=1
    def api_key()  # CC=1
    def api_key(value)  # CC=1
class MemoryConfig:  # Konfiguracja systemu pamięci.
class AnalyzerConfig:  # Konfiguracja analizatora kodu.
class RefactorConfig:  # Konfiguracja silnika refaktoryzacji.
class AgentConfig:  # Główna konfiguracja agenta.
    def from_env(cls)  # CC=4
```

### `redsl.orchestrator` (`redsl/orchestrator.py`)

```python
class CycleReport:  # Raport z jednego cyklu refaktoryzacji.
class RefactorOrchestrator:  # Główny orkiestrator — „mózg" systemu.
    def __init__(config)  # CC=2
    def run_cycle(project_dir, max_actions, use_code2llm, validate_regix, rollback_on_failure, use_sandbox, target_file)  # CC=1
    def run_from_toon_content(project_toon, duplication_toon, validation_toon, source_files, max_actions)  # CC=1
    def add_custom_rules(rules_yaml)  # CC=1
    def _resolve_limits(project_dir, default_max)  # CC=8
```

## Refactoring Analysis

*Pre-refactoring snapshot — use this section to identify targets. Generated from `project/` toon files.*

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 227f 32227L | python:225,shell:2 | 2026-04-19
# CC̄=3.8 | critical:7/1329 | dups:0 | cycles:0

HEALTH[8]:
  🔴 GOD   redsl/llm/selection.py = 508L, 6 classes, 27m, max CC=9
  🟡 CC    process_data CC=25 (limit:15)
  🟡 CC    process_data_copy CC=25 (limit:15)
  🟡 CC    refactor_plan_to_tasks CC=17 (limit:15)
  🟡 CC    generate_planfile CC=32 (limit:15)
  🟡 CC    format_cycle_report_toon CC=23 (limit:15)
  🟡 CC    planfile_sync CC=20 (limit:15)
  🟡 CC    pick_coding CC=16 (limit:15)

REFACTOR[2]:
  1. split redsl/llm/selection.py  (god module)
  2. split 7 high-CC methods  (CC>15)

PIPELINES[651]:
  [1] Src [main]: main → run_full_pipeline_example → load_example_yaml → _resolve_yaml_path → ...(1 more)
      PURITY: 100% pure
  [2] Src [main]: main
      PURITY: 100% pure
  [3] Src [main_function]: main_function → process_data
      PURITY: 100% pure
  [4] Src [main]: main → run_basic_analysis_example → load_example_yaml → _resolve_yaml_path → ...(1 more)
      PURITY: 100% pure
  [5] Src [__init__]: __init__
      PURITY: 100% pure

LAYERS:
  test_refactor_project/          CC̄=4.0    ←in:0  →out:0
  │ bad_code                    24L  1C    2m  CC=4      ←0
  │
  redsl/                          CC̄=3.9    ←in:30  →out:25  !! split
  │ !! sumr_planfile              510L  3C    6m  CC=32     ←1
  │ !! selection                  508L  6C   27m  CC=9      ←1
  │ !! models                     422L  0C   11m  CC=16     ←1
  │ sumd_bridge                412L  2C   13m  CC=11     ←0
  │ config                     410L  0C   13m  CC=7      ←1
  │ radon_analyzer             394L  1C   23m  CC=10     ←1
  │ pipeline                   390L  1C   14m  CC=10     ←1
  │ decision                   389L  0C    9m  CC=8      ←6
  │ nlp_handlers               358L  1C   10m  CC=12     ←0
  │ cli_autonomy               356L  0C   20m  CC=6      ←0
  │ __init__                   349L  2C   12m  CC=8      ←5
  │ engine                     336L  1C    9m  CC=12     ←1
  │ base                       335L  6C   13m  CC=14     ←0
  │ reporting                  332L  0C   25m  CC=12     ←1
  │ !! cycle                      328L  0C   12m  CC=23     ←1
  │ quality_gate               325L  1C   10m  CC=11     ←4
  │ __init__                   325L  2C   16m  CC=10     ←0
  │ agent_bridge               320L  1C    8m  CC=12     ←2
  │ doctor_detectors           319L  0C   17m  CC=8      ←1
  │ refactor                   319L  0C   13m  CC=6      ←1
  │ validator                  314L  0C    7m  CC=12     ←1
  │ regix_bridge               313L  1C    8m  CC=9      ←1
  │ aggregator                 310L  1C   15m  CC=8      ←0
  │ vallm_bridge               306L  1C    7m  CC=10     ←1
  │ llx_router                 305L  1C   15m  CC=10     ←2
  │ hybrid                     304L  0C   14m  CC=9      ←4
  │ project_parser             300L  1C   18m  CC=12     ←0
  │ testql_bridge              297L  2C   10m  CC=12     ←0
  │ toon_analyzer              296L  1C   13m  CC=14     ←0
  │ store                      294L  5C   22m  CC=8      ←1
  │ incremental                291L  2C   17m  CC=8      ←24
  │ refactor_routes            291L  0C    8m  CC=6      ←1
  │ engine                     290L  6C   12m  CC=10     ←0
  │ perf_bridge                289L  3C   11m  CC=6      ←2
  │ __init__                   288L  1C   13m  CC=7      ←0
  │ diff_manager               283L  0C    9m  CC=9      ←0
  │ growth_control             277L  3C   12m  CC=11     ←0
  │ prompts                    277L  0C    3m  CC=9      ←1
  │ python_analyzer            273L  1C    8m  CC=12     ←3
  │ main                       272L  0C   23m  CC=6      ←1
  │ rule_generator             271L  2C   11m  CC=6      ←0
  │ semantic_chunker           270L  2C   11m  CC=11     ←0
  │ scheduler                  264L  2C   16m  CC=9      ←0
  │ github_actions             260L  1C    6m  CC=6      ←0
  │ multi_project              251L  3C   10m  CC=5      ←0
  │ metrics                    249L  1C   11m  CC=7      ←2
  │ pyqual_bridge              249L  0C   12m  CC=11     ←2
  │ redup_bridge               246L  1C    7m  CC=9      ←1
  │ scan                       243L  4C   13m  CC=8      ←0
  │ catalog                    237L  1C    3m  CC=5      ←1
  │ __init__                   235L  4C   18m  CC=8      ←0
  │ doctor_fixers              230L  0C    9m  CC=10     ←0
  │ auto_fix                   220L  1C   13m  CC=8      ←2
  │ batch                      212L  0C   12m  CC=7      ←4
  │ history                    210L  3C   13m  CC=11     ←0
  │ direct_imports             210L  1C   14m  CC=7      ←0
  │ sandbox                    210L  3C    9m  CC=11     ←0
  │ quality_visitor            209L  1C   18m  CC=8      ←0
  │ consciousness_loop         204L  1C    7m  CC=5      ←0
  │ git_ops                    204L  0C    7m  CC=6      ←1
  │ body_restorer              203L  0C    7m  CC=11     ←1
  │ planfile_bridge            201L  0C    7m  CC=10     ←0
  │ !! planfile                   199L  0C    5m  CC=20     ←0
  │ model_policy               190L  0C    6m  CC=11     ←1
  │ paths                      189L  0C    9m  CC=12     ←4
  │ _indent_fixers             188L  0C    9m  CC=9      ←2
  │ applier                    187L  2C    7m  CC=8      ←0
  │ code2llm_bridge            185L  1C    5m  CC=5      ←1
  │ gate                       184L  2C    7m  CC=10     ←0
  │ refactor                   183L  0C    9m  CC=7      ←3
  │ _guard_fixers              179L  0C    7m  CC=11     ←1
  │ runner                     177L  1C    7m  CC=8      ←0
  │ timeline_toon              173L  1C   10m  CC=11     ←1
  │ cycle                      172L  0C    5m  CC=7      ←0
  │ orchestrator               170L  2C    5m  CC=8      ←0
  │ timeline_analysis          169L  1C    7m  CC=11     ←1
  │ audit                      168L  0C   10m  CC=4      ←1
  │ intent                     167L  0C    7m  CC=8      ←1
  │ git_timeline               165L  1C   23m  CC=5      ←0
  │ _scan_report               158L  0C    8m  CC=10     ←0
  │ badge                      158L  0C    8m  CC=6      ←1
  │ doctor_fstring_fixers      155L  0C   10m  CC=10     ←0
  │ analyzer                   155L  0C    6m  CC=8      ←1
  │ resolution                 154L  0C    6m  CC=9      ←3
  │ health_model               151L  3C    6m  CC=9      ←0
  │ reporter                   148L  1C    5m  CC=8      ←0
  │ direct_guard               148L  1C    6m  CC=8      ←0
  │ functions_parser           148L  1C    6m  CC=9      ←0
  │ config                     144L  5C    4m  CC=6      ←17
  │ review                     143L  0C    6m  CC=9      ←1
  │ security                   142L  2C    6m  CC=8      ←1
  │ llm_banner                 140L  0C    5m  CC=8      ←5
  │ utils                      140L  0C    9m  CC=7      ←4
  │ batch                      139L  0C    7m  CC=4      ←0
  │ reporting                  138L  0C    5m  CC=12     ←2
  │ proactive                  138L  2C    5m  CC=7      ←0
  │ models                     138L  0C    0m  CC=0.0    ←0
  │ profiles                   136L  0C    3m  CC=1      ←2
  │ pr_bot                     136L  0C    6m  CC=7      ←1
  │ __init__                   134L  0C    2m  CC=13     ←1
  │ ecosystem                  134L  2C   10m  CC=10     ←0
  │ ast_transformers           131L  2C    9m  CC=8      ←0
  │ direct_constants           130L  1C    6m  CC=9      ←0
  │ memory_learning            129L  0C    6m  CC=6      ←1
  │ timeline_git               128L  1C    7m  CC=8      ←1
  │ pipeline                   126L  0C    6m  CC=6      ←1
  │ change_patterns            125L  2C    6m  CC=12     ←0
  │ doctor                     124L  0C    3m  CC=8      ←1
  │ direct_types               124L  1C    5m  CC=8      ←0
  │ smart_scorer               122L  0C    5m  CC=7      ←0
  │ batch                      121L  0C    6m  CC=3      ←1
  │ self_model                 121L  3C    7m  CC=6      ←0
  │ llm_policy                 120L  5C    1m  CC=2      ←0
  │ examples                   118L  0C   14m  CC=4      ←1
  │ cli_doctor                 116L  0C    8m  CC=8      ←0
  │ __init__                   116L  0C    0m  CC=0.0    ←0
  │ core                       115L  6C    3m  CC=1      ←0
  │ models                     110L  7C    0m  CC=0.0    ←0
  │ verdict                    109L  0C    7m  CC=10     ←1
  │ webhook                    109L  0C    3m  CC=4      ←1
  │ timeline_models            107L  3C    3m  CC=3      ←0
  │ adaptive_executor          106L  1C    3m  CC=7      ←0
  │ reflector                  106L  0C    2m  CC=5      ←1
  │ fix_decisions              104L  0C    5m  CC=4      ←1
  │ proposals                  103L  5C    4m  CC=3      ←1
  │ awareness                  101L  0C    6m  CC=6      ←1
  │ resolver                    97L  1C    4m  CC=8      ←1
  │ models                      96L  13C    0m  CC=0.0    ←0
  │ example_routes              95L  0C    4m  CC=7      ←1
  │ _common                     94L  0C    6m  CC=4      ←12
  │ __init__                    89L  0C    3m  CC=1      ←0
  │ base                        89L  1C    2m  CC=6      ←2
  │ ast_analyzer                88L  1C    2m  CC=7      ←0
  │ config_gen                  87L  1C    3m  CC=4      ←1
  │ __init__                    87L  0C    0m  CC=0.0    ←0
  │ reporter                    86L  0C    4m  CC=9      ←6
  │ cli_awareness               83L  0C    8m  CC=1      ←0
  │ metrics                     81L  2C    2m  CC=2      ←0
  │ pyqual_example              74L  0C    2m  CC=8      ←1
  │ executor                    74L  0C    0m  CC=0.0    ←0
  │ todo_gen                    72L  0C    3m  CC=8      ←1
  │ pipeline                    71L  4C    4m  CC=4      ←0
  │ analyzer                    71L  1C    8m  CC=1      ←0
  │ __init__                    70L  0C    2m  CC=1      ←0
  │ sandbox_execution           69L  0C    1m  CC=4      ←1
  │ custom_rules                68L  0C    3m  CC=6      ←1
  │ full_pipeline               67L  0C    2m  CC=4      ←1
  │ __init__                    67L  0C    0m  CC=0.0    ←0
  │ discovery                   66L  0C    5m  CC=7      ←2
  │ __init__                    64L  0C    0m  CC=0.0    ←0
  │ direct                      63L  1C    6m  CC=1      ←0
  │ models                      62L  1C    0m  CC=0.0    ←0
  │ mypy_analyzer               61L  1C    2m  CC=7      ←0
  │ debug                       60L  0C    5m  CC=3      ←1
  │ debug_routes                59L  0C    1m  CC=1      ←1
  │ hybrid                      57L  0C    1m  CC=7      ←2
  │ validation                  57L  0C    2m  CC=6      ←1
  │ duplication_parser          57L  1C    1m  CC=12     ←0
  │ runner                      56L  0C    2m  CC=6      ←0
  │ __init__                    55L  0C    0m  CC=0.0    ←0
  │ basic_analysis              54L  0C    2m  CC=3      ←1
  │ secrets                     53L  2C    2m  CC=4      ←0
  │ ruff_analyzer               49L  1C    1m  CC=10     ←0
  │ models                      49L  3C    0m  CC=0.0    ←0
  │ logging                     48L  0C    1m  CC=6      ←3
  │ bandit_analyzer             47L  1C    1m  CC=9      ←0
  │ utils                       47L  0C    2m  CC=3      ←0
  │ models                      46L  6C    0m  CC=0.0    ←0
  │ doctor_data                 41L  2C    1m  CC=2      ←0
  │ api_integration             41L  0C    2m  CC=2      ←1
  │ scan                        41L  0C    2m  CC=6      ←0
  │ __init__                    41L  0C    0m  CC=0.0    ←0
  │ doctor_helpers              40L  0C    2m  CC=5      ←1
  │ reporter                    40L  0C    3m  CC=4      ←1
  │ validation_parser           40L  1C    1m  CC=12     ←0
  │ pyqual                      38L  0C    4m  CC=1      ←1
  │ __init__                    38L  0C    0m  CC=0.0    ←0
  │ utils                       37L  0C    3m  CC=4      ←0
  │ debug                       36L  0C    1m  CC=6      ←0
  │ pyqual_routes               33L  0C    1m  CC=1      ←1
  │ __init__                    33L  0C    0m  CC=0.0    ←0
  │ doctor_indent_fixers        31L  0C    0m  CC=0.0    ←0
  │ models                      30L  1C    0m  CC=0.0    ←0
  │ __init__                    30L  0C    0m  CC=0.0    ←0
  │ __init__                    29L  1C    0m  CC=0.0    ←0
  │ __init__                    28L  0C    0m  CC=0.0    ←0
  │ discovery                   26L  0C    2m  CC=5      ←0
  │ __init__                    23L  0C    0m  CC=0.0    ←0
  │ __init__                    22L  0C    0m  CC=0.0    ←0
  │ tool_check                  21L  0C    1m  CC=2      ←3
  │ health_routes               20L  0C    1m  CC=1      ←1
  │ __init__                    19L  0C    0m  CC=0.0    ←0
  │ helpers                     17L  0C    2m  CC=1      ←2
  │ json_helpers                17L  0C    1m  CC=4      ←0
  │ __init__                    17L  0C    0m  CC=0.0    ←0
  │ webhook_routes              16L  0C    1m  CC=1      ←1
  │ _base                       15L  1C    1m  CC=1      ←0
  │ __init__                    15L  0C    0m  CC=0.0    ←0
  │ __init__                    15L  0C    0m  CC=0.0    ←0
  │ core                        14L  0C    1m  CC=1      ←2
  │ _fixer_utils                13L  0C    1m  CC=2      ←3
  │ __main__                     6L  0C    0m  CC=0.0    ←0
  │ __init__                     3L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │ __main__                     1L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │
  test_refactor_bad/              CC̄=3.8    ←in:0  →out:0
  │ !! complex_code               137L  1C   17m  CC=25     ←0
  │
  examples/                       CC̄=2.3    ←in:0  →out:0
  │ main                       168L  0C    5m  CC=5      ←0
  │ 00_orders__service          88L  0C    6m  CC=6      ←0
  │ main                        32L  0C    1m  CC=1      ←0
  │ main                        30L  0C    1m  CC=1      ←0
  │ main                        29L  0C    1m  CC=1      ←0
  │ main                        27L  0C    1m  CC=1      ←0
  │ main                        27L  0C    1m  CC=1      ←0
  │ main                        27L  0C    1m  CC=1      ←0
  │ main                        26L  0C    1m  CC=1      ←0
  │ main                        25L  0C    1m  CC=1      ←0
  │ main                        25L  0C    1m  CC=1      ←0
  │ main                        25L  0C    1m  CC=1      ←0
  │
  test_sample_project/            CC̄=2.3    ←in:0  →out:0
  │ sample                      32L  0C    3m  CC=4      ←0
  │
  .goal/                          CC̄=2.0    ←in:0  →out:0
  │ pre-commit-hook             23L  0C    1m  CC=2      ←0
  │ vallm-pre-commit.sh         17L  0C    0m  CC=0.0    ←0
  │
  refactor_output/                CC̄=1.4    ←in:0  →out:0
  │ 00_app__models              29L  0C    5m  CC=3      ←0
  │
  app/                            CC̄=0.0    ←in:0  →out:0
  │ models                      48L  3C    0m  CC=0.0    ←0
  │
  ./                              CC̄=0.0    ←in:0  →out:0
  │ project.sh                  35L  0C    0m  CC=0.0    ←0
  │

COUPLING:
                                         redsl         redsl.commands         redsl.autonomy        redsl.analyzers              redsl.cli        redsl.execution              redsl.api       redsl.validation         redsl.examples              redsl.llm       redsl.formatters        redsl.refactors  redsl.config_standard      redsl.diagnostics            redsl.utils
                  redsl                     ──                     ←2                     ←6                      2                      8                      4                      6                     ←1                     ←1                      2                                                                    1                      2                         hub
         redsl.commands                      2                     ──                     13                      8                      4                      3                                             7                                                                    2                      1                                                                       hub
         redsl.autonomy                      6                      7                     ──                      8                     ←1                      3                                                                                                                                                                                                                 hub
        redsl.analyzers                     ←2                     ←8                     ←8                     ──                                            ←3                                            ←1                     ←1                     ←3                                            ←5                     ←1                                                hub
              redsl.cli                      8                      1                      1                                            ──                      1                                                                    1                      1                      4                                             4                      1                         hub
        redsl.execution                      2                     ←3                     ←3                      3                     ←1                     ──                     ←3                      3                     ←1                      4                                             1                                                                       hub
              redsl.api                      3                                                                                                                  3                     ──                                             2                                             6                                             1                                                hub
       redsl.validation                      1                     ←7                                             1                                            ←3                                            ──                                                                                          ←3                                                                    2  hub
         redsl.examples                      1                                                                    1                     ←1                      1                     ←2                                            ──                                                                                                                                            hub
              redsl.llm                      2                                                                    3                     ←1                     ←4                                                                                          ──                                                                                                                  1  hub
       redsl.formatters                                            ←2                                                                   ←4                                            ←6                                                                                          ──                                                                                              hub
        redsl.refactors                                            ←1                                             5                                            ←1                                             3                                                                                          ──                                                                       !! fan-out
  redsl.config_standard                      1                                                                    1                     ←4                                            ←1                                                                                                                                        ──                                                hub
      redsl.diagnostics                     ←2                                                                                          ←1                                                                                                                                                                                                             ──                      1
            redsl.utils                                                                                                                                                                                      ←2                                            ←1                                                                                          ←1                     ──
  CYCLES: none
  HUB: redsl.cli/ (fan-in=12)
  HUB: redsl.execution/ (fan-in=15)
  HUB: redsl.autonomy/ (fan-in=14)
  HUB: redsl.examples/ (fan-in=13)
  HUB: redsl.commands/ (fan-in=8)
  HUB: redsl.config_standard/ (fan-in=6)
  HUB: redsl.formatters/ (fan-in=12)
  HUB: redsl.llm/ (fan-in=7)
  HUB: redsl.api/ (fan-in=6)
  HUB: redsl.analyzers/ (fan-in=34)
  HUB: redsl.validation/ (fan-in=13)
  HUB: redsl/ (fan-in=30)
  SMELL: redsl.refactors/ fan-out=8 → split needed
  SMELL: redsl.cli/ fan-out=22 → split needed
  SMELL: redsl.execution/ fan-out=13 → split needed
  SMELL: redsl.autonomy/ fan-out=24 → split needed
  SMELL: redsl.commands/ fan-out=40 → split needed
  SMELL: redsl.api/ fan-out=16 → split needed
  SMELL: redsl/ fan-out=25 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 14 groups | 219f 31658L | 2026-04-19

SUMMARY:
  files_scanned: 219
  total_lines:   31658
  dup_groups:    14
  dup_fragments: 47
  saved_lines:   132
  scan_ms:       13458

DUPLICATES[14] (ranked by impact):
  [1907a33a0fa70761]   STRU  example_basic_analysis  L=3 N=9 saved=24 sim=1.00
      redsl/cli/examples.py:26-28  (example_basic_analysis)
      redsl/cli/examples.py:34-36  (example_custom_rules)
      redsl/cli/examples.py:51-53  (example_memory_learning)
      redsl/cli/examples.py:59-61  (example_api_integration)
      redsl/cli/examples.py:67-69  (example_awareness)
      redsl/cli/examples.py:75-77  (example_pyqual)
      redsl/cli/examples.py:83-85  (example_audit)
      redsl/cli/examples.py:91-93  (example_pr_bot)
      redsl/cli/examples.py:99-101  (example_badge)
  [3827f031a50510f3]   STRU  main  L=3 N=9 saved=24 sim=1.00
      redsl/examples/api_integration.py:35-37  (main)
      redsl/examples/audit.py:162-164  (main)
      redsl/examples/awareness.py:95-97  (main)
      redsl/examples/badge.py:152-154  (main)
      redsl/examples/basic_analysis.py:48-50  (main)
      redsl/examples/custom_rules.py:62-64  (main)
      redsl/examples/memory_learning.py:123-125  (main)
      redsl/examples/pr_bot.py:130-132  (main)
      redsl/examples/pyqual_example.py:68-70  (main)
  [66fffac820f1a666]   STRU  is_available  L=3 N=7 saved=18 sim=1.00
      redsl/analyzers/code2llm_bridge.py:47-49  (is_available)
      redsl/analyzers/radon_analyzer.py:31-33  (is_radon_available)
      redsl/analyzers/redup_bridge.py:40-42  (is_available)
      redsl/commands/batch_pyqual/config_gen.py:64-66  (_pyqual_cli_available)
      redsl/commands/batch_pyqual/runner.py:29-31  (_pyqual_cli_available)
      redsl/validation/regix_bridge.py:39-46  (is_available)
      redsl/validation/vallm_bridge.py:138-140  (is_available)
  [5e00de8bc3caf754]   STRU  _collect_guard_body  L=14 N=2 saved=14 sim=1.00
      redsl/commands/_guard_fixers.py:150-163  (_collect_guard_body)
      redsl/refactors/body_restorer.py:45-59  (_collect_guard_body)
  [9b2eb61629d4cf19]   STRU  fix_stolen_indent  L=11 N=2 saved=11 sim=1.00
      redsl/commands/doctor_fixers.py:69-79  (fix_stolen_indent)
      redsl/commands/doctor_fixers.py:81-91  (fix_broken_fstrings)
  [b027db1c8d821268]   STRU  _register_history_command  L=10 N=2 saved=10 sim=1.00
      redsl/commands/cli_awareness.py:22-31  (_register_history_command)
      redsl/commands/cli_awareness.py:44-53  (_register_health_command)
  [ce2537bbaad1fba9]   STRU  export_config_schema  L=7 N=2 saved=7 sim=1.00
      redsl/config_standard/profiles.py:82-88  (export_config_schema)
      redsl/config_standard/proposals.py:78-84  (export_proposal_schema)
  [42758e6f93d15e46]   STRU  _check_analysis_passed  L=5 N=2 saved=5 sim=1.00
      redsl/commands/batch_pyqual/verdict.py:8-12  (_check_analysis_passed)
      redsl/commands/batch_pyqual/verdict.py:15-19  (_check_gates_passed)
  [62499c819ffbba21]   STRU  batch_hybrid  L=4 N=2 saved=4 sim=1.00
      redsl/cli/batch.py:52-55  (batch_hybrid)
      redsl/cli/pyqual.py:31-34  (pyqual_fix)
  [d63bc3468205cd17]   EXAC  __init__  L=3 N=2 saved=3 sim=1.00
      redsl/llm/registry/sources/base.py:153-155  (__init__)
      redsl/llm/registry/sources/base.py:190-192  (__init__)
  [77d5f2d33a9f8d05]   STRU  _extract_file_path  L=3 N=2 saved=3 sim=1.00
      redsl/autonomy/auto_fix.py:65-67  (_extract_file_path)
      redsl/autonomy/auto_fix.py:70-72  (_extract_function_name)
  [be39955a1d8f8e68]   STRU  register_model_policy  L=3 N=2 saved=3 sim=1.00
      redsl/cli/model_policy.py:10-12  (register_model_policy)
      redsl/cli/models.py:10-12  (register_models)
  [aaae754bdb04529d]   STRU  model_policy  L=3 N=2 saved=3 sim=1.00
      redsl/cli/model_policy.py:16-18  (model_policy)
      redsl/cli/models.py:16-18  (models_group)
  [4e0c5433bfda0d64]   STRU  _dispatch_analyze  L=3 N=2 saved=3 sim=1.00
      redsl/main.py:214-216  (_dispatch_analyze)
      redsl/main.py:219-221  (_dispatch_explain)

REFACTOR[14] (ranked by priority):
  [1] ○ extract_function   → redsl/cli/utils/example_basic_analysis.py
      WHY: 9 occurrences of 3-line block across 1 files — saves 24 lines
      FILES: redsl/cli/examples.py
  [2] ○ extract_function   → redsl/examples/utils/main.py
      WHY: 9 occurrences of 3-line block across 9 files — saves 24 lines
      FILES: redsl/examples/api_integration.py, redsl/examples/audit.py, redsl/examples/awareness.py, redsl/examples/badge.py, redsl/examples/basic_analysis.py +4 more
  [3] ○ extract_function   → redsl/utils/is_available.py
      WHY: 7 occurrences of 3-line block across 7 files — saves 18 lines
      FILES: redsl/analyzers/code2llm_bridge.py, redsl/analyzers/radon_analyzer.py, redsl/analyzers/redup_bridge.py, redsl/commands/batch_pyqual/config_gen.py, redsl/commands/batch_pyqual/runner.py +2 more
  [4] ○ extract_function   → redsl/utils/_collect_guard_body.py
      WHY: 2 occurrences of 14-line block across 2 files — saves 14 lines
      FILES: redsl/commands/_guard_fixers.py, redsl/refactors/body_restorer.py
  [5] ○ extract_function   → redsl/commands/utils/fix_stolen_indent.py
      WHY: 2 occurrences of 11-line block across 1 files — saves 11 lines
      FILES: redsl/commands/doctor_fixers.py
  [6] ○ extract_function   → redsl/commands/utils/_register_history_command.py
      WHY: 2 occurrences of 10-line block across 1 files — saves 10 lines
      FILES: redsl/commands/cli_awareness.py
  [7] ○ extract_function   → redsl/config_standard/utils/export_config_schema.py
      WHY: 2 occurrences of 7-line block across 2 files — saves 7 lines
      FILES: redsl/config_standard/profiles.py, redsl/config_standard/proposals.py
  [8] ○ extract_function   → redsl/commands/batch_pyqual/utils/_check_analysis_passed.py
      WHY: 2 occurrences of 5-line block across 1 files — saves 5 lines
      FILES: redsl/commands/batch_pyqual/verdict.py
  [9] ○ extract_function   → redsl/cli/utils/batch_hybrid.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: redsl/cli/batch.py, redsl/cli/pyqual.py
  [10] ○ extract_function   → redsl/llm/registry/sources/utils/__init__.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: redsl/llm/registry/sources/base.py
  [11] ○ extract_function   → redsl/autonomy/utils/_extract_file_path.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: redsl/autonomy/auto_fix.py
  [12] ○ extract_function   → redsl/cli/utils/register_model_policy.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: redsl/cli/model_policy.py, redsl/cli/models.py
  [13] ○ extract_function   → redsl/cli/utils/model_policy.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: redsl/cli/model_policy.py, redsl/cli/models.py
  [14] ○ extract_function   → redsl/utils/_dispatch_analyze.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: redsl/main.py

METRICS-TARGET:
  dup_groups:  14 → 0
  saved_lines: 132 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 1255 func | 169f | 2026-04-19

NEXT[7] (ranked by impact):
  [1] !! SPLIT           redsl/commands/sumr_planfile.py
      WHY: 510L, 3 classes, max CC=32
      EFFORT: ~4h  IMPACT: 16320

  [2] !! SPLIT           redsl/llm/selection.py
      WHY: 508L, 6 classes, max CC=9
      EFFORT: ~4h  IMPACT: 4572

  [3] !! SPLIT-FUNC      generate_planfile  CC=32  fan=35
      WHY: CC=32 exceeds 15
      EFFORT: ~1h  IMPACT: 1120

  [4] !  SPLIT-FUNC      format_cycle_report_toon  CC=23  fan=15
      WHY: CC=23 exceeds 15
      EFFORT: ~1h  IMPACT: 345

  [5] !  SPLIT-FUNC      refactor_plan_to_tasks  CC=17  fan=20
      WHY: CC=17 exceeds 15
      EFFORT: ~1h  IMPACT: 340

  [6] !  SPLIT-FUNC      planfile_sync  CC=20  fan=16
      WHY: CC=20 exceeds 15
      EFFORT: ~1h  IMPACT: 320

  [7] !  SPLIT-FUNC      pick_coding  CC=16  fan=15
      WHY: CC=16 exceeds 15
      EFFORT: ~1h  IMPACT: 240


RISKS[2]:
  ⚠ Splitting redsl/commands/sumr_planfile.py may break 6 import paths
  ⚠ Splitting redsl/llm/selection.py may break 27 import paths

METRICS-TARGET:
  CC̄:          3.9 → ≤2.7
  max-CC:      32 → ≤16
  god-modules: 2 → 0
  high-CC(≥15): 7 → ≤3
  hub-types:   0 → ≤0

PATTERNS (language parser shared logic):
  _extract_declarations() in base.py — unified extraction for:
    - TypeScript: interfaces, types, classes, functions, arrow funcs
    - PHP: namespaces, traits, classes, functions, includes
    - Ruby: modules, classes, methods, requires
    - C++: classes, structs, functions, #includes
    - C#: classes, interfaces, methods, usings
    - Java: classes, interfaces, methods, imports
    - Go: packages, functions, structs
    - Rust: modules, functions, traits, use statements

  Shared regex patterns per language:
    - import: language-specific import/require/using patterns
    - class: class/struct/trait declarations with inheritance
    - function: function/method signatures with visibility
    - brace_tracking: for C-family languages ({ })
    - end_keyword_tracking: for Ruby (module/class/def...end)

  Benefits:
    - Consistent extraction logic across all languages
    - Reduced code duplication (~70% reduction in parser LOC)
    - Easier maintenance: fix once, apply everywhere
    - Standardized FunctionInfo/ClassInfo models

HISTORY:
  (first run — no previous data)
```

### Validation (`project/validation.toon.yaml`)

```toon markpact:analysis path=project/validation.toon.yaml
# vallm batch | 359f | 269✓ 3⚠ 0✗ | 2026-04-19

SUMMARY:
  scanned: 359  passed: 269 (74.9%)  warnings: 3  errors: 0  unsupported: 90

WARNINGS[3]{path,score}:
  redsl/commands/sumr_planfile.py,0.93
    issues[4]{rule,severity,message,line}:
      complexity.cyclomatic,warning,_extract_complexity_layers has cyclomatic complexity 20 (max: 15),219
      complexity.cyclomatic,warning,refactor_plan_to_tasks has cyclomatic complexity 17 (max: 15),345
      complexity.lizard_cc,warning,_extract_complexity_layers: CC=20 exceeds limit 15,219
      complexity.lizard_cc,warning,refactor_plan_to_tasks: CC=17 exceeds limit 15,345
  test_refactor_bad/complex_code.py,0.93
    issues[4]{rule,severity,message,line}:
      complexity.cyclomatic,warning,process_data has cyclomatic complexity 25 (max: 15),5
      complexity.cyclomatic,warning,process_data_copy has cyclomatic complexity 25 (max: 15),63
      complexity.lizard_cc,warning,process_data: CC=25 exceeds limit 15,5
      complexity.lizard_cc,warning,process_data_copy: CC=25 exceeds limit 15,63
  redsl/cli/models.py,0.98
    issues[1]{rule,severity,message,line}:
      complexity.cyclomatic,warning,pick_coding has cyclomatic complexity 16 (max: 15),76

UNSUPPORTED[5]{bucket,count}:
  *.md,64
  Dockerfile*,1
  *.txt,4
  *.yml,2
  other,19
```

## Intent

ReDSL — Refactor + DSL + Self-Learning. LLM-powered autonomous code refactoring.
