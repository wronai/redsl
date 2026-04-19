---
path: /home/tom/github/semcod/redsl
---

<!-- code2docs:start --># redsl

![version](https://img.shields.io/badge/version-0.1.0-blue) ![python](https://img.shields.io/badge/python-%3E%3D3.11-blue) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey) ![functions](https://img.shields.io/badge/functions-1337-green)
> **1337** functions | **204** classes | **224** files | CC̄ = 3.8

> Auto-generated project documentation from source code analysis.

**Author:** ReDSL Team  
**License:** Apache-2.0[(LICENSE)](./LICENSE)  
**Repository:** [https://github.com/semcod/redsl](https://github.com/semcod/redsl)

## Installation

### From PyPI

```bash
pip install redsl
```

### From Source

```bash
git clone https://github.com/semcod/redsl
cd redsl
pip install -e .
```

### Optional Extras

```bash
pip install redsl[dev]    # development tools
```

## Quick Start

### CLI Usage

```bash
# Generate full documentation for your project
redsl ./my-project

# Only regenerate README
redsl ./my-project --readme-only

# Preview what would be generated (no file writes)
redsl ./my-project --dry-run

# Check documentation health
redsl check ./my-project

# Sync — regenerate only changed modules
redsl sync ./my-project
```

### Python API

```python
from redsl import generate_readme, generate_docs, Code2DocsConfig

# Quick: generate README
generate_readme("./my-project")

# Full: generate all documentation
config = Code2DocsConfig(project_name="mylib", verbose=True)
docs = generate_docs("./my-project", config=config)
```

## Generated Output

When you run `redsl`, the following files are produced:

```
<project>/
├── README.md                 # Main project README (auto-generated sections)
├── docs/
│   ├── api.md               # Consolidated API reference
│   ├── modules.md           # Module documentation with metrics
│   ├── architecture.md      # Architecture overview with diagrams
│   ├── dependency-graph.md  # Module dependency graphs
│   ├── coverage.md          # Docstring coverage report
│   ├── getting-started.md   # Getting started guide
│   ├── configuration.md    # Configuration reference
│   └── api-changelog.md    # API change tracking
├── examples/
│   ├── quickstart.py       # Basic usage examples
│   └── advanced_usage.py   # Advanced usage examples
├── CONTRIBUTING.md         # Contribution guidelines
└── mkdocs.yml             # MkDocs site configuration
```

## Configuration

Create `redsl.yaml` in your project root (or run `redsl init`):

```yaml
project:
  name: my-project
  source: ./
  output: ./docs/

readme:
  sections:
    - overview
    - install
    - quickstart
    - api
    - structure
  badges:
    - version
    - python
    - coverage
  sync_markers: true

docs:
  api_reference: true
  module_docs: true
  architecture: true
  changelog: true

examples:
  auto_generate: true
  from_entry_points: true

sync:
  strategy: markers    # markers | full | git-diff
  watch: false
  ignore:
    - "tests/"
    - "__pycache__"
```

## Sync Markers

redsl can update only specific sections of an existing README using HTML comment markers:

```markdown
<!-- redsl:start -->
# Project Title
... auto-generated content ...
<!-- redsl:end -->
```

Content outside the markers is preserved when regenerating. Enable this with `sync_markers: true` in your configuration.

## Architecture

```
redsl/
├── project        ├── vallm-pre-commit    ├── complex_code    ├── consciousness_loop├── redsl/    ├── __main__        ├── main        ├── pre-commit-hook        ├── main        ├── cli_awareness        ├── _fixer_utils        ├── main    ├── config        ├── main        ├── doctor_indent_fixers        ├── doctor    ├── bad_code        ├── main        ├── main        ├── main        ├── main        ├── planfile_bridge        ├── _scan_report        ├── doctor_helpers        ├── doctor_fstring_fixers        ├── _guard_fixers        ├── main        ├── doctor_fixers        ├── main        ├── cli_doctor        ├── batch        ├── _indent_fixers        ├── batch_pyqual/            ├── verdict            ├── utils        ├── main        ├── sumr_planfile        ├── hybrid            ├── config_gen            ├── discovery            ├── helpers        ├── cli_autonomy        ├── autofix/            ├── runner            ├── reporting        ├── doctor_detectors            ├── todo_gen            ├── runner            ├── pipeline            ├── discovery            ├── ruff_analyzer            ├── reporting            ├── reporter            ├── mypy_analyzer            ├── ast_analyzer            ├── bandit_analyzer            ├── hybrid        ├── autonomy_pr/            ├── analyzer            ├── fix_decisions            ├── reporter            ├── git_ops        ├── pyqual/        ├── doctor_data            ├── validator    ├── history        ├── store    ├── config_standard/        ├── nlp_handlers            ├── models        ├── models            ├── models        ├── profiles        ├── security        ├── agent_bridge        ├── paths    ├── examples/            ├── models        ├── basic_analysis        ├── _common        ├── multi_project        ├── awareness        ├── api_integration        ├── audit        ├── custom_rules        ├── pr_bot    ├── diagnostics/        ├── perf_bridge    ├── core/        ├── pipeline        ├── quality_gate        ├── catalog        ├── review    ├── autonomy/        ├── metrics        ├── adaptive_executor        ├── intent        ├── smart_scorer    ├── main        ├── scan        ├── applier    ├── formatters/        ├── core        ├── growth_control        ├── debug        ├── batch        ├── badge    ├── memory/        ├── refactor        ├── llm_banner        ├── scheduler        ├── config        ├── pyqual    ├── cli/        ├── __main__        ├── scan        ├── examples            ├── pipeline        ├── utils        ├── refactor        ├── debug        ├── batch        ├── cycle        ├── resolution        ├── model_policy    ├── execution/        ├── reporter        ├── validation        ├── sandbox_execution        ├── executor        ├── reflector        ├── base    ├── bridges/        ├── planfile        ├── cycle        ├── gate        ├── memory_learning        ├── decision        ├── registry/        ├── llx_router        ├── models            ├── sources/    ├── llm/        ├── direct_types                ├── base        ├── direct_guard        ├── direct            ├── aggregator        ├── prompts        ├── diff_manager        ├── direct_imports    ├── refactors/        ├── engine        ├── pyqual_example        ├── direct_constants    ├── ci/        ├── _base        ├── git_timeline        ├── github_actions        ├── full_pipeline        ├── timeline_git        ├── ecosystem        ├── timeline_toon        ├── proactive        ├── timeline_analysis        ├── body_restorer            ├── models        ├── health_model        ├── sandbox    ├── validation/        ├── vallm_bridge        ├── change_patterns    ├── awareness/        ├── pyqual_bridge        ├── tool_check    ├── utils/        ├── self_model        ├── json_helpers        ├── testql_bridge        ├── sumd_bridge        ├── auto_fix        ├── analyzer        ├── regix_bridge    ├── analyzers/        ├── redup_bridge        ├── metrics        ├── incremental        ├── toon_analyzer        ├── python_analyzer        ├── resolver        ├── utils        ├── semantic_chunker        ├── parsers/            ├── functions_parser        ├── radon_analyzer        ├── code2llm_bridge            ├── validation_parser    ├── integrations/        ├── pyqual_routes            ├── duplication_parser        ├── health_routes    ├── api/        ├── webhook        ├── webhook_routes        ├── selection            ├── project_parser        ├── debug_routes        ├── refactor_routes    ├── dsl/        ├── example_routes        ├── rule_generator        ├── ast_transformers    ├── models        ├── timeline_models    ├── orchestrator        ├── models        ├── quality_visitor        ├── proposals        ├── engine        ├── llm_policy        ├── core        ├── secrets        ├── models        ├── logging```

## API Overview

### Classes

- **`GodClass`** — A god class with too many responsibilities.
- **`ConsciousnessLoop`** — Ciągła pętla „świadomości" agenta.
- **`LLMConfig`** — Konfiguracja warstwy LLM.
- **`MemoryConfig`** — Konfiguracja systemu pamięci.
- **`AnalyzerConfig`** — Konfiguracja analizatora kodu.
- **`RefactorConfig`** — Konfiguracja silnika refaktoryzacji.
- **`AgentConfig`** — Główna konfiguracja agenta.
- **`BadClass`** — —
- **`PlanTask`** — —
- **`SumrData`** — —
- **`PlanfileResult`** — —
- **`RuffAnalyzer`** — Uruchamia ruff i zbiera wyniki.
- **`Reporter`** — Generuje rekomendacje i zapisuje raporty analizy jakości.
- **`MypyAnalyzer`** — Uruchamia mypy i zbiera wyniki.
- **`AstAnalyzer`** — Analizuje pliki Python przez AST w poszukiwaniu typowych problemów jakości.
- **`BanditAnalyzer`** — Uruchamia bandit i zbiera wyniki bezpieczeństwa.
- **`PyQualAnalyzer`** — Python code quality analyzer — fasada nad wyspecjalizowanymi analizatorami.
- **`Issue`** — A single detected issue.
- **`DoctorReport`** — Aggregated report for one project.
- **`HistoryEvent`** — A single persisted event in the refactor history.
- **`HistoryWriter`** — Append-only history logger backed by .redsl/history.jsonl.
- **`HistoryReader`** — Read-only access to .redsl/history.jsonl for querying and dedup.
- **`ConfigStoreError`** — —
- **`ConfigVersionMismatch`** — —
- **`ConfigValidationError`** — —
- **`ConfigHistoryRecord`** — —
- **`ConfigStore`** — Manage a redsl-config directory with manifest, profiles and history.
- **`ToolError`** — Raised when a tool call fails validation or execution.
- **`ProjectFixResult`** — Result of autofix processing for a single project.
- **`SecretMatch`** — —
- **`SecretInterceptor`** — Redact secret-looking substrings before data is shown to an LLM.
- **`ConfigBridgeError`** — Raised when config bridge cannot resolve configuration.
- **`PyqualProjectResult`** — Result of pyqual pipeline for a single project.
- **`ProjectAnalysis`** — Wyniki analizy pojedynczego projektu.
- **`MultiProjectReport`** — Zbiorczy raport z analizy wielu projektów.
- **`MultiProjectRunner`** — Uruchamia ReDSL na wielu projektach.
- **`Bottleneck`** — —
- **`CriticalStep`** — —
- **`PerformanceReport`** — —
- **`StepResult`** — —
- **`PipelineStep`** — Abstract base for a single pipeline step.
- **`PipelineResult`** — —
- **`Pipeline`** — Run a sequence of PipelineStep objects against a shared context dict.
- **`GateVerdict`** — Result of a quality gate check.
- **`PathCatalogEntry`** — —
- **`AutonomyMetrics`** — Metrics for the autonomy subsystem.
- **`AdaptiveExecutor`** — Execute decisions while adapting strategy on repeated failures.
- **`ProjectScanResult`** — Scan result for a single project.
- **`ApplyResult`** — —
- **`ConfigApplier`** — Apply config proposals atomically with locking and audit logging.
- **`GrowthBudget`** — LOC growth budget per iteration.
- **`GrowthController`** — Enforce growth budgets on a project.
- **`ModuleBudget`** — Complexity budget for a single module.
- **`MemoryEntry`** — Pojedynczy wpis w pamięci.
- **`MemoryLayer`** — Warstwa pamięci oparta na ChromaDB.
- **`InMemoryCollection`** — Fallback gdy ChromaDB nie jest dostępne.
- **`AgentMemory`** — Kompletny system pamięci z trzema warstwami.
- **`AutonomyMode`** — —
- **`Scheduler`** — Periodic quality-improvement loop.
- **`ProjectContext`** — Mutable context passed through pipeline stages.
- **`CliBridge`** — Base class for bridges wrapping external CLI tools.
- **`ModelRejectedError`** — Raised when model is rejected by policy.
- **`ModelAgeGate`** — Enforces model age and lifecycle policy before LLM calls.
- **`ModelSelection`** — —
- **`LLMResponse`** — Odpowiedź z modelu LLM.
- **`LLMLayer`** — Warstwa abstrakcji nad LLM z obsługą:
- **`DirectTypesRefactorer`** — Handles return type annotation addition.
- **`ModelRegistrySource`** — Abstract base class for model registry sources.
- **`OpenRouterSource`** — OpenRouter public API - no auth required, ~300+ models.
- **`ModelsDevSource`** — Models.dev community API - public, ~200+ models.
- **`OpenAIProviderSource`** — Native OpenAI API - requires key, authoritative for OpenAI models.
- **`AnthropicProviderSource`** — Native Anthropic API - requires key, authoritative for Claude models.
- **`AiderLeaderboardSource`** — Drugie niezależne źródło — benchmark polyglot od Aider.
- **`DirectGuardRefactorer`** — Handles main guard wrapping for module-level execution code.
- **`DirectRefactorEngine`** — Applies simple refactorings directly via AST manipulation.
- **`RegistryAggregator`** — Aggregates model info from multiple sources with caching.
- **`DirectImportRefactorer`** — Handles import-related direct refactoring.
- **`RefactorEngine`** — Silnik refaktoryzacji z pętlą refleksji.
- **`DirectConstantsRefactorer`** — Handles magic number to constant extraction.
- **`DirectRefactorBase`** — Mixin that provides ``get_applied_changes`` for Direct* refactorers.
- **`GitTimelineAnalyzer`** — Build a historical metric timeline from git commits — facade.
- **`WorkflowConfig`** — Konfiguracja generowanego workflow.
- **`GitTimelineProvider`** — Provides git-based timeline data.
- **`ProjectNode`** — Single project node in the ecosystem graph.
- **`EcosystemGraph`** — Basic ecosystem graph for semcod-style project collections.
- **`ToonCollector`** — Collects and processes toon files from git history.
- **`ProactiveAlert`** — A proactive issue detected from trends.
- **`ProactiveAnalyzer`** — Turn trend forecasts into alerts and suggested interventions.
- **`TimelineAnalyzer`** — Analyzes metric trends from timeline data.
- **`PolicyMode`** — Policy mode for model age checking.
- **`UnknownReleaseAction`** — Action when model release date is unknown.
- **`Pricing`** — Ceny USD per token (nie per million!).
- **`Capabilities`** — Features modelu istotne dla programowania.
- **`QualitySignals`** — Sygnały jakości z różnych benchmarków.
- **`ModelInfo`** — Information about an LLM model.
- **`PolicyDecision`** — Result of policy check for a model.
- **`HealthDimension`** — Single health dimension with score and rationale.
- **`UnifiedHealth`** — Aggregated health snapshot.
- **`HealthModel`** — Combine timeline metrics into a single health snapshot.
- **`DockerNotFoundError`** — Raised when Docker daemon is not available.
- **`SandboxError`** — Raised for sandbox-level failures.
- **`RefactorSandbox`** — Docker sandbox do bezpiecznego testowania refaktoryzacji.
- **`ChangePattern`** — A learned pattern describing a recurring change shape.
- **`ChangePatternLearner`** — Infer patterns from timeline deltas and trend transitions.
- **`AwarenessSnapshot`** — Compact overview of the current awareness state for a project.
- **`AwarenessManager`** — Facade that combines all awareness layers into one snapshot.
- **`CapabilityStat`** — Track how well the agent performs a capability.
- **`AgentCapabilityProfile`** — Structured self-assessment summary.
- **`SelfModel`** — Introspective model backed by agent memory.
- **`TestqlVerdict`** — Validation verdict from testql scenario execution.
- **`TestqlValidator`** — Post-refactoring validator using testql scenarios.
- **`SumdMetrics`** — Metrics extracted from sumd analysis.
- **`SumdAnalyzer`** — Native project analyzer using sumd extractor patterns.
- **`AutoFixResult`** — Outcome of the auto-fix pipeline.
- **`CodeAnalyzer`** — Główny analizator kodu — fasada.
- **`CodeMetrics`** — Metryki pojedynczej funkcji/modułu.
- **`AnalysisResult`** — Wynik analizy projektu.
- **`EvolutionaryCache`** — Cache wyników analizy per-plik oparty o hash pliku.
- **`IncrementalAnalyzer`** — Analizuje tylko zmienione pliki i scala z cached wynikami.
- **`ToonAnalyzer`** — Analizator plików toon — przetwarza dane z code2llm.
- **`PythonAnalyzer`** — Analizator plików .py przez stdlib ast.
- **`PathResolver`** — Resolver ścieżek i kodu źródłowego funkcji.
- **`SemanticChunk`** — Wycięty semantyczny fragment kodu gotowy do wysłania do LLM.
- **`SemanticChunker`** — Buduje semantyczne chunki kodu dla LLM.
- **`ToonParser`** — Parser plików toon — fasada nad wyspecjalizowanymi parserami.
- **`FunctionsParser`** — Parser sekcji functions_toon — per-funkcja CC.
- **`ValidationParser`** — Parser sekcji validation_toon.
- **`DuplicationParser`** — Parser sekcji duplication_toon.
- **`SelectionStrategy`** — Strategia wyboru modelu.
- **`CostProfile`** — Jak liczymy koszt per model.
- **`CodingRequirements`** — Wymagania techniczne dla modelu do kodowania.
- **`ModelCandidate`** — Kandydat na model z metrykami.
- **`ModelSelectionError`** — Raised when no model can be selected.
- **`ModelSelector`** — Wybiera najtańszy model spełniający wymagania.
- **`ProjectParser`** — Parser sekcji project_toon.
- **`LearnedRule`** — Reguła DSL wygenerowana z wzorców w pamięci.
- **`RuleGenerator`** — Generuje nowe reguły DSL z historii refaktoryzacji w pamięci agenta.
- **`ReturnTypeAdder`** — AST transformer to add return type annotations.
- **`UnusedImportRemover`** — AST transformer to remove unused imports.
- **`FileChange`** — Zmiana w pojedynczym pliku.
- **`RefactorProposal`** — Propozycja refaktoryzacji wygenerowana przez LLM.
- **`RefactorResult`** — Wynik zastosowania refaktoryzacji.
- **`MetricPoint`** — Single timeline point captured from a git commit.
- **`TrendAnalysis`** — Trend summary for a single metric series.
- **`TimelineSummary`** — High-level summary of a git timeline.
- **`CycleReport`** — Raport z jednego cyklu refaktoryzacji.
- **`RefactorOrchestrator`** — Główny orkiestrator — „mózg" systemu.
- **`FileChange`** — Zmiana w pojedynczym pliku.
- **`RefactorProposal`** — Propozycja refaktoryzacji wygenerowana przez LLM.
- **`RefactorResult`** — Wynik zastosowania refaktoryzacji.
- **`CodeQualityVisitor`** — Detects common code quality issues in Python AST.
- **`ProposalMetadata`** — —
- **`ConfigPreconditions`** — —
- **`ConfigValidationState`** — —
- **`ConfigChange`** — —
- **`ConfigChangeProposal`** — —
- **`Operator`** — —
- **`RefactorAction`** — —
- **`Condition`** — Pojedynczy warunek DSL.
- **`Rule`** — Reguła DSL: warunki → akcja z priorytetem.
- **`Decision`** — Wynik ewaluacji reguł — decyzja co refaktoryzować.
- **`DSLEngine`** — Silnik ewaluacji reguł DSL.
- **`LLMPolicy`** — —
- **`CostWeights`** — —
- **`CodingTiers`** — —
- **`DefaultOperationTiers`** — —
- **`CodingConfig`** — —
- **`ConfigOrigin`** — —
- **`ConfigMetadata`** — —
- **`RegistrySource`** — —
- **`CacheConfig`** — —
- **`RedslConfigSpec`** — —
- **`RedslConfigDocument`** — —
- **`SecretRotation`** — —
- **`SecretSpec`** — —
- **`AnalyzeRequest`** — —
- **`RefactorRequest`** — —
- **`BatchSemcodRequest`** — —
- **`BatchHybridRequest`** — —
- **`DebugConfigRequest`** — —
- **`DebugDecisionsRequest`** — —
- **`PyQualAnalyzeRequest`** — —
- **`PyQualFixRequest`** — —
- **`RulesRequest`** — —
- **`ExampleRunRequest`** — —
- **`DecisionResponse`** — —
- **`CycleRequest`** — —
- **`CycleResponse`** — —

### Functions

- `process_data(data, mode, threshold, callback)` — Very complex function with high CC.
- `process_data_copy(data, mode, threshold, callback)` — Copy of process_data - exact duplicate.
- `main_loop()` — Punkt wejścia dla pętli ciągłej.
- `main()` — —
- `main()` — Run pre-commit validation.
- `main()` — —
- `register(cli, host_module)` — Register all awareness commands on the given Click group.
- `main()` — —
- `main()` — —
- `diagnose(root)` — Run all detectors on a project and return a report (no fixes applied).
- `heal(root, dry_run)` — Diagnose and fix issues in a project.
- `heal_batch(semcod_root, dry_run)` — Run doctor on all semcod subprojects.
- `calculate(x, y, z)` — —
- `main()` — —
- `main()` — —
- `main()` — —
- `main()` — —
- `is_available()` — Return True if planfile CLI is installed and functional.
- `create_ticket(project_dir, title, description, priority)` — Create a planfile ticket for a refactoring action.
- `list_tickets(project_dir, status)` — List planfile tickets, optionally filtered by status.
- `report_refactor_results(project_dir, decisions_applied, files_modified, avg_cc_before)` — Create a summary ticket for a completed refactor cycle.
- `render_markdown(results, folder)` — Render a markdown priority report from scan results.
- `main()` — —
- `fix_broken_guards(root, report)` — Use body_restorer to repair stolen class/function bodies.
- `fix_stolen_indent(root, report)` — Restore indentation for function/class bodies that lost it.
- `fix_broken_fstrings(root, report)` — Fix common broken f-string patterns.
- `fix_stale_pycache(root, report)` — Remove all __pycache__ directories.
- `fix_missing_install(root, report)` — Run pip install -e . for the project.
- `fix_module_level_exit(root, report)` — Wrap bare sys.exit() calls in if __name__ == '__main__' guards.
- `fix_version_mismatch(root, report)` — Update hardcoded version strings in test files.
- `fix_pytest_collision(root, report)` — Add override_name to pytest config so it doesn't collide with Typer CLI.
- `main()` — —
- `register(cli)` — Register the doctor command group on the given Click group.
- `run_semcod_batch(semcod_root, max_actions)` — Run batch refactoring on semcod projects.
- `apply_refactor(project_path, max_actions)` — Apply reDSL to a project and return the report.
- `measure_todo_reduction(project_path)` — Measure TODO.md before and after refactoring.
- `compute_verdict(result, require_pipeline, require_push, require_publish)` — Compute final verdict for a project result.
- `run_cmd(cmd, cwd, timeout)` — Run a shell command and return the result.
- `git_status_lines(project)` — Return non-empty git status lines for *project*, or [] on error.
- `resolve_profile(requested_profile, run_pipeline, publish)` — Resolve the effective pyqual profile based on CLI options.
- `demo_policy_check()` — Demonstrate checking models against policy.
- `demo_list_allowed()` — Demonstrate listing all allowed models.
- `demo_safe_completion()` — Demonstrate safe completion with policy enforcement.
- `demo_strict_mode()` — Demonstrate strict vs non-strict mode.
- `main()` — Run all demos.
- `parse_sumr(path)` — Parse a SUMR.md file and extract refactoring-relevant data.
- `toon_to_tasks(toon_content, source, project_path)` — Extract PlanTask list from TOON-format content.
- `refactor_plan_to_tasks(yaml_content, source)` — Convert a redsl ``refactor_plan.yaml`` to PlanTask list.
- `generate_planfile(project_path)` — Generate or update planfile.yaml for *project_path* from SUMR.md.
- `run_hybrid_quality_refactor(project_path, max_changes)` — Apply ALL quality refactorings to a project without LLM.
- `run_hybrid_batch(semcod_root, max_changes)` — Run hybrid refactoring on all semcod projects.
- `register(cli, host_module)` — Register all autonomy commands on the given Click group.
- `run_pyqual_batch(workspace_root, max_fixes, run_pipeline, git_push)` — Run ReDSL + pyqual on all projects in workspace.
- `detect_broken_guards(root)` — Find Python files with syntax errors caused by misplaced ``if __name__`` guards.
- `detect_stolen_indent(root)` — Find files where function/class body lost indentation after guard removal.
- `detect_broken_fstrings(root)` — Find files with broken f-strings (single brace, missing open brace).
- `detect_stale_pycache(root)` — Find stale __pycache__ directories.
- `detect_missing_install(root)` — Check whether the project's own package is importable.
- `detect_module_level_exit(root)` — Find test files with bare ``sys.exit(...)`` outside ``if __name__`` guard.
- `detect_version_mismatch(root)` — Find tests that hardcode a version string that differs from VERSION file.
- `detect_pytest_cli_collision(root)` — Check if ``python -m pytest`` is hijacked by a Typer/Click CLI.
- `run_autofix_batch(semcod_root, max_changes)` — Run full autofix pipeline on all semcod packages.
- `run_autonomous_pr(git_url, max_actions, dry_run, auto_apply)` — Run the autonomous PR workflow.
- `build_pyqual_fix_decisions(issues, project_path)` — Build direct-refactor Decisions grouped by file from pyqual issues.
- `run_pyqual_analysis(project_path, config_path, output_format)` — Run pyqual analysis on a project.
- `run_pyqual_fix(project_path, config_path)` — Run automatic fixes based on pyqual analysis.
- `dispatch_tool(tool_name, arguments)` — Route an LLM tool call to the correct handler.
- `build_default_config()` — —
- `config_doc_to_yaml(document)` — —
- `export_config_schema()` — —
- `is_sensitive_key(key)` — —
- `mask_sensitive_mapping(data)` — Return a shallow copy with secret-like values masked.
- `resolve_secret_ref(secret)` — Resolve a secret reference to its actual value.
- `find_config_root(start_path)` — Find redsl-config directory by walking up from start_path or cwd.
- `load_agent_config_from_substrate(config_root, profile)` — Load AgentConfig from config substrate, resolving secrets.
- `agent_config_from_substrate_or_env(config_root, profile)` — Try substrate first, fall back to env-based config.
- `parse_config_path(path)` — Parse a dotted / indexed config path into navigation tokens.
- `get_nested_value(data, path)` — —
- `set_nested_value(data, path, value)` — —
- `remove_nested_value(data, path)` — —
- `deep_merge(base, overlay)` — Recursively merge *overlay* into *base* and return a new object.
- `deep_diff(base, current)` — Return the minimal overlay needed to transform *base* into *current*.
- `materialize_diff(base, current)` — Public wrapper around :func:`deep_diff` that always returns JSON-friendly data.
- `walk_paths(data, prefix)` — Yield dotted paths for scalar leaves in a nested mapping/list tree.
- `run_basic_analysis_example(scenario, source)` — —
- `main(argv)` — —
- `load_example_yaml(example_name, scenario, source)` — —
- `list_available_examples()` — Return metadata for every example that has at least a ``default.yaml``.
- `print_banner(title, width, char)` — —
- `parse_scenario(argv)` — —
- `run_multi_analysis(project_dirs, config)` — Convenience function — analiza wielu projektów.
- `run_awareness_example(scenario, source)` — —
- `main(argv)` — —
- `run_api_integration_example(scenario, source)` — —
- `main(argv)` — —
- `run_audit_example(scenario, source)` — —
- `main(argv)` — —
- `run_custom_rules_example(scenario, source)` — —
- `main(argv)` — —
- `run_pr_bot_example(scenario, source)` — —
- `main(argv)` — —
- `profile_refactor_cycle(project_dir)` — Profiluj jeden cykl analizy/refaktoryzacji za pomocą metrun (lub fallback).
- `profile_llm_latency()` — Zmierz latencję wywołań LLM — kluczowy bottleneck.
- `profile_memory_operations()` — Zmierz czas operacji ChromaDB — store, recall, similarity search.
- `generate_optimization_report(project_dir)` — Wygeneruj raport z sugestiami optymalizacji (używany przez CLI i loop).
- `run_quality_gate(project_dir)` — Check whether current changes pass the quality gate.
- `install_pre_commit_hook(project_dir)` — Install a git pre-commit hook that runs the quality gate.
- `get_risk_level(path)` — Return risk level for a config path. Falls back to 'low' for unknown paths.
- `search_schema_matches(query)` — Return catalog entries matching *query* across path/title/description/aliases.
- `review_staged_changes(project_dir, model_override, max_diff_chars)` — Return a textual code review for all staged/unstaged changes.
- `collect_autonomy_metrics(project_dir)` — Collect all autonomy metrics for a project.
- `save_metrics(metrics, path)` — Save metrics to a JSON file.
- `load_metrics(path)` — Load metrics from a JSON file.
- `analyze_commit_intent(project_dir)` — Analyse the current working-tree changes and return an intent report.
- `smart_score(rule, context)` — Compute a multi-dimensional score for a refactoring decision.
- `cmd_analyze(project_dir)` — Analiza projektu — wyświetl metryki i alerty.
- `cmd_explain(project_dir)` — Wyjaśnij decyzje refaktoryzacji bez ich wykonywania.
- `cmd_refactor(project_dir, dry_run, auto, max_actions)` — Uruchom cykl refaktoryzacji.
- `cmd_memory_stats()` — Statystyki pamięci agenta.
- `cmd_serve(port, host)` — Uruchom serwer API.
- `main()` — Główny punkt wejścia CLI.
- `scan_folder(folder, progress)` — Scan all sub-projects in *folder* and return sorted results.
- `check_module_budget(file_path, module_type)` — Check whether a module stays within its complexity budget.
- `format_debug_info(info, format)` — Format debug information.
- `format_batch_results(results, format)` — Format batch processing results.
- `format_batch_report_markdown(report, root, title)` — Format a batch run report as Markdown.
- `run_badge_example(scenario, source)` — —
- `main(argv)` — —
- `format_refactor_plan(decisions, format, analysis)` — Format refactoring plan in specified format.
- `print_llm_banner()` — Print the LLM config banner to stderr.
- `config()` — Config substrate commands for manifests, profiles and audit logs.
- `config_init(root, name, profile, force)` — Initialize a new redsl-config layout.
- `config_validate(root, output_format)` — Validate a config manifest against the standard.
- `config_diff(root, against, output_format)` — Diff current config against another config file or root.
- `config_history(root, limit, output_format)` — Show the append-only config audit history.
- `config_apply(root, proposal_path, actor, user)` — Apply a ConfigChangeProposal atomically.
- `config_clone(source, target, profile, replace_secrets)` — Clone a config substrate locally.
- `config_show(root, output_format)` — Print the current manifest.
- `config_rollback(root, to_version, output_format)` — Rollback config to a previous version atomically.
- `register_config(cli)` — —
- `pyqual()` — Python code quality analysis commands.
- `pyqual_analyze(project_path, config, format)` — Analyze Python code quality.
- `pyqual_fix(project_path, config)` — Apply automatic quality fixes.
- `register_pyqual(cli)` — —
- `cli(ctx, verbose)` — reDSL - Automated code refactoring tool.
- `scan(ctx, folder, output_path, quiet)` — Scan a folder of projects and produce a markdown priority report.
- `example()` — Run built-in examples and demos.
- `example_basic_analysis(scenario, source)` — Run the basic code-analysis demo.
- `example_custom_rules(scenario, source)` — Run the custom DSL rules demo.
- `example_full_pipeline(scenario, model, source)` — Run the full refactoring-pipeline demo (requires LLM key).
- `example_memory_learning(scenario, source)` — Run the agent-memory demo (episodic / semantic / procedural).
- `example_api_integration(scenario, source)` — Show API curl / httpx / WebSocket usage examples.
- `example_awareness(scenario, source)` — Run the awareness / change-pattern detection demo.
- `example_pyqual(scenario, source)` — Run the PyQual code-quality analysis demo.
- `example_audit(scenario, source)` — Run One-click Audit - full scan -> grade report -> badge.
- `example_pr_bot(scenario, source)` — Run PR Bot - realistic GitHub PR comment preview.
- `example_badge(scenario, source)` — Run Badge Generator - grade A+ to F with Markdown/HTML code.
- `example_list()` — List available example scenarios.
- `register_examples(cli)` — —
- `process_project(project, max_fixes, run_pipeline, git_push)` — Full ReDSL + pyqual pipeline for a single project.
- `perf_command(ctx, project_path)` — Profile a refactoring cycle and report performance bottlenecks.
- `cost_command(ctx, project_path, max_actions)` — Estimate LLM cost for the next refactoring cycle without running it.
- `refactor(ctx, project_path, max_actions, dry_run)` — Run refactoring on a project.
- `register_refactor(cli)` — —
- `debug()` — Debug utilities for development.
- `debug_ast(project_path, file)` — Show AST analysis for debugging.
- `debug_llm(prompt, model)` — Test LLM with a simple prompt.
- `debug_metrics(project_path)` — Show project metrics for debugging.
- `register_debug(cli)` — —
- `batch()` — Batch refactoring commands.
- `batch_semcod(semcod_root, max_actions, format)` — Apply refactoring to semcod projects.
- `batch_hybrid(semcod_root, max_changes)` — Apply hybrid quality refactorings (no LLM needed).
- `batch_autofix(ctx, semcod_root, max_changes)` — Auto-fix all packages: scan -> generate TODO.md -> apply hybrid fixes -> gate fix.
- `batch_pyqual_run(ctx, workspace_root, max_fixes, limit)` — Multi-project quality pipeline: ReDSL analysis + pyqual gates + optional push.
- `register_batch(cli)` — —
- `format_cycle_report_yaml(report, decisions, analysis)` — Format full cycle report as YAML for stdout.
- `format_cycle_report_markdown(report, decisions, analysis, project_path)` — Format a refactor cycle as a Markdown report.
- `format_plan_yaml(decisions, analysis)` — Format dry-run plan as YAML for stdout.
- `format_cycle_report_toon(report, decisions, analysis, project_path)` — Format a refactor cycle as TOON for planfile integration.
- `register_model_policy(cli)` — Register model-policy commands.
- `model_policy()` — Manage LLM model age and lifecycle policy.
- `check_model(model, json_output)` — Check if a model is allowed by policy.
- `list_models(max_age, provider, json_output, limit)` — List models currently allowed by policy.
- `refresh_registry()` — Force refresh model registry from sources.
- `show_config()` — Show current model policy configuration.
- `explain_decisions(orchestrator, project_dir, limit)` — Explain refactoring decisions without executing them.
- `get_memory_stats(orchestrator)` — Return memory and runtime statistics for the orchestrator.
- `estimate_cycle_cost(orchestrator, project_dir, max_actions)` — Estimate the cost of the next cycle without executing it.
- `execute_sandboxed(orchestrator, decision, project_dir)` — Execute a decision in a sandboxed environment.
- `planfile_group()` — SUMR.md → planfile.yaml task generation.
- `planfile_sync(project_path, sumr_path, dry_run, no_merge)` — Generate or update planfile.yaml from SUMR.md.
- `planfile_show(project_path, status, output_format)` — Show tasks from an existing planfile.yaml.
- `register(cli_group)` — —
- `run_cycle(orchestrator, project_dir, max_actions, use_code2llm)` — Run a complete refactoring cycle.
- `run_from_toon_content(orchestrator, project_toon, duplication_toon, validation_toon)` — Run a cycle from pre-parsed toon content.
- `run_memory_learning_example(scenario, source)` — —
- `main(argv)` — —
- `select_model(action, context, budget_remaining)` — Wybierz optymalny model na podstawie akcji i kontekstu.
- `select_reflection_model(use_local)` — Wybierz model do refleksji — zawsze tańszy.
- `estimate_cycle_cost(decisions, contexts)` — Szacuj koszt całego cyklu refaktoryzacji — lista per decyzja.
- `apply_provider_prefix(model, configured_model)` — Apply provider prefix from configured model to a bare model name.
- `call_via_llx(messages, task_type)` — Deleguj wywołanie LLM do llx CLI jeśli dostępne.
- `register_models(cli)` — Register model selection commands.
- `models_group()` — Model selection for coding - cheapest suitable model.
- `pick_coding(tier, min_context, require_tools, show_all)` — Pokaż jaki model zostałby wybrany dla danego tieru.
- `list_coding(tier, limit, show_rejected, sort)` — Tabela modeli spełniających wymagania coding, posortowana po cenie.
- `estimate_cost(tier, input_tokens, output_tokens, ops_per_day)` — Estimate monthly cost for given tier and usage pattern.
- `show_coding_config()` — Show current coding model selection configuration.
- `get_gate()` — Get or create the global ModelAgeGate singleton.
- `safe_completion(model)` — Drop-in replacement for litellm.completion with policy enforcement.
- `check_model_policy(model)` — Check if a model is allowed without making an LLM call.
- `list_allowed_models()` — List all models currently allowed by policy.
- `build_ecosystem_context(context)` — Render a short ecosystem/context block for prompts.
- `generate_diff(original, refactored, file_path)` — Wygeneruj unified diff dla dwóch wersji pliku.
- `preview_proposal(proposal, project_dir)` — Wygeneruj sformatowany diff wszystkich zmian w propozycji.
- `create_checkpoint(project_dir)` — Utwórz checkpoint aktualnego stanu projektu.
- `rollback_to_checkpoint(checkpoint_id, project_dir)` — Cofnij projekt do stanu z checkpointa.
- `rollback_single_file(file_path, checkpoint_id, project_dir)` — Cofnij jeden plik do stanu z checkpointa.
- `run_pyqual_example(scenario, source)` — —
- `main(argv)` — —
- `generate_github_workflow(project_dir, config, output_path)` — Wygeneruj zawartość pliku .github/workflows/redsl.yml.
- `install_github_workflow(project_dir, config, overwrite)` — Zainstaluj workflow w projekcie (.github/workflows/redsl.yml).
- `run_full_pipeline_example(scenario, source, model)` — —
- `main(argv)` — —
- `repair_file(path)` — Attempt to restore stolen class/function bodies in *path*.
- `repair_directory(root, dry_run)` — Walk *root* and repair all damaged Python files.
- `sandbox_available()` — True if Docker or pactfix is available for sandbox testing.
- `is_available()` — Sprawdź czy vallm jest zainstalowane i w pełni działa (nie tylko czy jest w PATH).
- `validate_patch(file_path, refactored_code, project_dir)` — Waliduj wygenerowany kod przez pipeline vallm.
- `validate_proposal(proposal, project_dir)` — Waliduj wszystkie zmiany w propozycji refaktoryzacji.
- `blend_confidence(base_confidence, vallm_score)` — Połącz confidence z metryk ReDSL z wynikiem vallm (punkt 2.3).
- `is_available()` — Return True if pyqual CLI is installed and functional.
- `doctor(project_dir)` — Run `pyqual doctor` and return structured tool availability dict.
- `check_gates(project_dir)` — Run `pyqual gates` and return pass/fail status.
- `get_status(project_dir)` — Run `pyqual status` and return current metrics summary.
- `validate_config(project_dir, fix)` — Run `pyqual validate` to check pyqual.yaml is well-formed.
- `init_config(project_dir, profile)` — Generate pyqual.yaml using `pyqual init`.
- `run_pipeline(project_dir, fix_config, dry_run)` — Run `pyqual run` and parse iterations plus push/publish status.
- `git_commit(project_dir, message, add_all, if_changed)` — Create a commit via `pyqual git commit`.
- `git_push(project_dir, detect_protection, dry_run)` — Push changes via `pyqual git push`.
- `is_tool_available(cmd, timeout)` — Return True if running *cmd* exits with code 0 within *timeout* seconds.
- `extract_json_block(text)` — Extract first JSON block from *text*, skipping preamble lines.
- `validate_with_testql(project_dir, scenarios_dir, config)` — Validate project using testql scenarios.
- `check_testql_available()` — Check if testql CLI is available.
- `analyze_with_sumd(project_dir)` — Analyze project using sumd if available, fallback to native analyzer.
- `auto_fix_violations(project_dir, violations)` — Try to automatically fix each violation; create ticket on failure.
- `is_available()` — Sprawdź czy regix jest zainstalowane i działa poprawnie.
- `snapshot(project_dir, ref, timeout)` — Zrób snapshot metryk projektu przez regix.
- `compare(project_dir, before_ref, after_ref)` — Porównaj metryki między dwoma git refs przez regix.
- `compare_snapshots(project_dir, before, after)` — Porównaj dwa snapshoty (obiekty z `snapshot()`).
- `check_gates(project_dir)` — Sprawdź quality gates z regix.yaml (lub domyślne progi).
- `rollback_working_tree(project_dir)` — Cofnij niezatwierdzone zmiany w working tree przez `git checkout -- .`.
- `validate_no_regression(project_dir, rollback_on_failure)` — Porównaj HEAD~1 → HEAD i sprawdź czy nie ma regresji metryk.
- `validate_working_tree(project_dir, before_snapshot, rollback_on_failure)` — Porównaj snapshot 'przed' ze stanem working tree (po zmianach, przed commitem).
- `is_available()` — Sprawdź czy redup jest zainstalowane i dostępne w PATH.
- `scan_duplicates(project_dir, min_lines, min_similarity)` — Uruchom redup i zwróć listę grup duplikatów.
- `scan_as_toon(project_dir, min_lines, min_similarity)` — Uruchom redup w formacie toon i zwróć zawartość jako string.
- `enrich_analysis(analysis, project_dir)` — Wzbogać istniejący AnalysisResult o dane z redup.
- `get_refactor_suggestions(project_dir)` — Pobierz sugestie refaktoryzacji duplikatów z redup.
- `get_changed_files(project_dir, since)` — Pobierz listę zmienionych plików .py od podanego commita/ref.
- `get_staged_files(project_dir)` — Pobierz listę staged plików .py (git diff --cached).
- `ast_max_nesting_depth(node)` — Oblicz max glębokość zagnieżdżenia pętli/warunków — nie wchodzi w zagnieżdżone def/class.
- `ast_cyclomatic_complexity(node)` — Oblicz CC dla funkcji — nie wchodzi w zagnieżdżone definicje funkcji/klas.
- `is_radon_available()` — Sprawdź czy radon jest zainstalowany i dostępny.
- `run_radon_cc(project_dir, excludes)` — Uruchom `radon cc -j` i zwróć sparsowane wyniki.
- `extract_max_cc_per_file(radon_results, project_dir)` — Ekstraktuj maksymalne CC per plik z wyników radon.
- `enhance_metrics_with_radon(metrics, project_dir)` — Uzupełnij metryki o dokładne CC z radon (jeśli dostępne).
- `is_available()` — Sprawdź czy code2llm jest zainstalowane i dostępne w PATH.
- `generate_toon_files(project_dir, output_dir, timeout)` — Uruchom code2llm na projekcie i zwróć katalog z wygenerowanymi plikami toon.
- `read_toon_contents(toon_dir)` — Wczytaj pliki toon z katalogu wyjściowego code2llm.
- `analyze_with_code2llm(project_dir, analyzer, output_dir, timeout)` — Pełna ścieżka percepcji z code2llm:
- `maybe_analyze(project_dir, analyzer, output_dir)` — Spróbuj analizy przez code2llm; zwróć None jeśli niezainstalowane.
- `create_app()` — Tworzenie aplikacji FastAPI.
- `handle_push_webhook(payload)` — Process a GitHub push webhook payload.
- `build_selector(aggregator, gate)` — Build ModelSelector from environment configuration.
- `select_model_for_operation(operation)` — Mapping: 'extract_function' → tier z .env → konkretny model.
- `get_selector()` — Get or build the global ModelSelector.
- `invalidate_selector()` — Invalidate the global selector cache (e.g., after config change).
- `track_model_selection(model, tier, operation)` — Track model selection for metrics.
- `check_cost_per_call(estimated_cost_usd)` — Check if cost is within safety limits.
- `export_proposal_schema()` — —
- `proposal_to_yaml(proposal)` — —
- `setup_logging(project_path, verbose)` — Route all logging to a timestamped log file, keep stdout clean.


## Project Structure

📄 `.goal.pre-commit-hook` (1 functions)
📄 `.goal.vallm-pre-commit`
📄 `app.models` (3 classes)
📄 `examples.01-basic-analysis.main` (1 functions)
📄 `examples.02-custom-rules.main` (1 functions)
📄 `examples.03-full-pipeline.main` (1 functions)
📄 `examples.04-memory-learning.main` (1 functions)
📄 `examples.05-api-integration.main` (1 functions)
📄 `examples.06-awareness.main` (1 functions)
📄 `examples.07-pyqual.main` (1 functions)
📄 `examples.08-audit.main` (1 functions)
📄 `examples.09-pr-bot.main` (1 functions)
📄 `examples.10-badge.main` (1 functions)
📄 `examples.11-model-policy.main` (5 functions)
📄 `project`
📦 `redsl`
📄 `redsl.__main__`
📦 `redsl.analyzers`
📄 `redsl.analyzers.analyzer` (8 functions, 1 classes)
📄 `redsl.analyzers.code2llm_bridge` (5 functions, 1 classes)
📄 `redsl.analyzers.incremental` (17 functions, 2 classes)
📄 `redsl.analyzers.metrics` (2 functions, 2 classes)
📦 `redsl.analyzers.parsers` (1 classes)
📄 `redsl.analyzers.parsers.duplication_parser` (1 functions, 1 classes)
📄 `redsl.analyzers.parsers.functions_parser` (6 functions, 1 classes)
📄 `redsl.analyzers.parsers.project_parser` (18 functions, 1 classes)
📄 `redsl.analyzers.parsers.validation_parser` (1 functions, 1 classes)
📄 `redsl.analyzers.python_analyzer` (8 functions, 1 classes)
📄 `redsl.analyzers.quality_visitor` (18 functions, 1 classes)
📄 `redsl.analyzers.radon_analyzer` (23 functions, 1 classes)
📄 `redsl.analyzers.redup_bridge` (7 functions, 1 classes)
📄 `redsl.analyzers.resolver` (4 functions, 1 classes)
📄 `redsl.analyzers.semantic_chunker` (11 functions, 2 classes)
📄 `redsl.analyzers.sumd_bridge` (13 functions, 2 classes)
📄 `redsl.analyzers.toon_analyzer` (13 functions, 1 classes)
📄 `redsl.analyzers.utils` (9 functions)
📦 `redsl.api` (2 functions)
📄 `redsl.api.debug_routes` (1 functions)
📄 `redsl.api.example_routes` (4 functions)
📄 `redsl.api.health_routes` (1 functions)
📄 `redsl.api.models` (13 classes)
📄 `redsl.api.pyqual_routes` (1 functions)
📄 `redsl.api.refactor_routes` (8 functions)
📄 `redsl.api.webhook_routes` (1 functions)
📦 `redsl.autonomy`
📄 `redsl.autonomy.adaptive_executor` (3 functions, 1 classes)
📄 `redsl.autonomy.auto_fix` (13 functions, 1 classes)
📄 `redsl.autonomy.growth_control` (12 functions, 3 classes)
📄 `redsl.autonomy.intent` (7 functions)
📄 `redsl.autonomy.metrics` (11 functions, 1 classes)
📄 `redsl.autonomy.quality_gate` (10 functions, 1 classes)
📄 `redsl.autonomy.review` (6 functions)
📄 `redsl.autonomy.scheduler` (16 functions, 2 classes)
📄 `redsl.autonomy.smart_scorer` (5 functions)
📦 `redsl.awareness` (16 functions, 2 classes)
📄 `redsl.awareness.change_patterns` (6 functions, 2 classes)
📄 `redsl.awareness.ecosystem` (10 functions, 2 classes)
📄 `redsl.awareness.git_timeline` (23 functions, 1 classes)
📄 `redsl.awareness.health_model` (6 functions, 3 classes)
📄 `redsl.awareness.proactive` (5 functions, 2 classes)
📄 `redsl.awareness.self_model` (7 functions, 3 classes)
📄 `redsl.awareness.timeline_analysis` (7 functions, 1 classes)
📄 `redsl.awareness.timeline_git` (7 functions, 1 classes)
📄 `redsl.awareness.timeline_models` (3 functions, 3 classes)
📄 `redsl.awareness.timeline_toon` (10 functions, 1 classes)
📦 `redsl.bridges`
📄 `redsl.bridges.base` (2 functions, 1 classes)
📦 `redsl.ci`
📄 `redsl.ci.github_actions` (6 functions, 1 classes)
📦 `redsl.cli` (4 functions)
📄 `redsl.cli.__main__`
📄 `redsl.cli.batch` (6 functions)
📄 `redsl.cli.config` (13 functions)
📄 `redsl.cli.debug` (5 functions)
📄 `redsl.cli.examples` (14 functions)
📄 `redsl.cli.llm_banner` (5 functions)
📄 `redsl.cli.logging` (1 functions)
📄 `redsl.cli.model_policy` (6 functions)
📄 `redsl.cli.models` (11 functions)
📄 `redsl.cli.planfile` (9 functions)
📄 `redsl.cli.pyqual` (4 functions)
📄 `redsl.cli.refactor` (13 functions)
📄 `redsl.cli.scan` (2 functions)
📄 `redsl.cli.utils` (2 functions)
📄 `redsl.commands._fixer_utils` (1 functions)
📄 `redsl.commands._guard_fixers` (7 functions)
📄 `redsl.commands._indent_fixers` (9 functions)
📄 `redsl.commands._scan_report` (8 functions)
📦 `redsl.commands.autofix`
📄 `redsl.commands.autofix.discovery` (2 functions)
📄 `redsl.commands.autofix.helpers` (2 functions)
📄 `redsl.commands.autofix.hybrid` (1 functions)
📄 `redsl.commands.autofix.models` (1 classes)
📄 `redsl.commands.autofix.pipeline` (6 functions)
📄 `redsl.commands.autofix.reporting` (5 functions)
📄 `redsl.commands.autofix.runner` (2 functions)
📄 `redsl.commands.autofix.todo_gen` (3 functions)
📦 `redsl.commands.autonomy_pr` (2 functions)
📄 `redsl.commands.autonomy_pr.analyzer` (6 functions)
📄 `redsl.commands.autonomy_pr.git_ops` (7 functions)
📄 `redsl.commands.autonomy_pr.models` (6 classes)
📄 `redsl.commands.autonomy_pr.reporter` (3 functions)
📄 `redsl.commands.autonomy_pr.validator` (7 functions)
📄 `redsl.commands.batch` (7 functions)
📦 `redsl.commands.batch_pyqual`
📄 `redsl.commands.batch_pyqual.config_gen` (3 functions, 1 classes)
📄 `redsl.commands.batch_pyqual.discovery` (5 functions)
📄 `redsl.commands.batch_pyqual.models` (1 classes)
📄 `redsl.commands.batch_pyqual.pipeline` (14 functions, 1 classes)
📄 `redsl.commands.batch_pyqual.reporting` (25 functions)
📄 `redsl.commands.batch_pyqual.runner` (7 functions, 1 classes)
📄 `redsl.commands.batch_pyqual.utils` (3 functions)
📄 `redsl.commands.batch_pyqual.verdict` (7 functions)
📄 `redsl.commands.cli_autonomy` (20 functions)
📄 `redsl.commands.cli_awareness` (8 functions)
📄 `redsl.commands.cli_doctor` (8 functions)
📄 `redsl.commands.doctor` (3 functions)
📄 `redsl.commands.doctor_data` (1 functions, 2 classes)
📄 `redsl.commands.doctor_detectors` (17 functions)
📄 `redsl.commands.doctor_fixers` (9 functions)
📄 `redsl.commands.doctor_fstring_fixers` (10 functions)
📄 `redsl.commands.doctor_helpers` (2 functions)
📄 `redsl.commands.doctor_indent_fixers`
📄 `redsl.commands.hybrid` (14 functions)
📄 `redsl.commands.multi_project` (10 functions, 3 classes)
📄 `redsl.commands.planfile_bridge` (7 functions)
📦 `redsl.commands.pyqual` (13 functions, 1 classes)
📄 `redsl.commands.pyqual.ast_analyzer` (2 functions, 1 classes)
📄 `redsl.commands.pyqual.bandit_analyzer` (1 functions, 1 classes)
📄 `redsl.commands.pyqual.fix_decisions` (5 functions)
📄 `redsl.commands.pyqual.mypy_analyzer` (2 functions, 1 classes)
📄 `redsl.commands.pyqual.reporter` (5 functions, 1 classes)
📄 `redsl.commands.pyqual.ruff_analyzer` (1 functions, 1 classes)
📄 `redsl.commands.scan` (13 functions, 4 classes)
📄 `redsl.commands.sumr_planfile` (14 functions, 3 classes)
📄 `redsl.config` (4 functions, 5 classes)
📦 `redsl.config_standard`
📄 `redsl.config_standard.agent_bridge` (8 functions, 1 classes)
📄 `redsl.config_standard.applier` (7 functions, 2 classes)
📄 `redsl.config_standard.catalog` (3 functions, 1 classes)
📄 `redsl.config_standard.core` (3 functions, 6 classes)
📄 `redsl.config_standard.llm_policy` (1 functions, 5 classes)
📄 `redsl.config_standard.models`
📄 `redsl.config_standard.nlp_handlers` (10 functions, 1 classes)
📄 `redsl.config_standard.paths` (9 functions)
📄 `redsl.config_standard.profiles` (3 functions)
📄 `redsl.config_standard.proposals` (4 functions, 5 classes)
📄 `redsl.config_standard.secrets` (2 functions, 2 classes)
📄 `redsl.config_standard.security` (6 functions, 2 classes)
📄 `redsl.config_standard.store` (22 functions, 5 classes)
📄 `redsl.consciousness_loop` (7 functions, 1 classes)
📦 `redsl.core`
📄 `redsl.core.pipeline` (4 functions, 4 classes)
📦 `redsl.diagnostics`
📄 `redsl.diagnostics.perf_bridge` (11 functions, 3 classes)
📦 `redsl.dsl`
📄 `redsl.dsl.engine` (12 functions, 6 classes)
📄 `redsl.dsl.rule_generator` (11 functions, 2 classes)
📦 `redsl.examples`
📄 `redsl.examples._common` (6 functions)
📄 `redsl.examples.api_integration` (2 functions)
📄 `redsl.examples.audit` (10 functions)
📄 `redsl.examples.awareness` (6 functions)
📄 `redsl.examples.badge` (8 functions)
📄 `redsl.examples.basic_analysis` (2 functions)
📄 `redsl.examples.custom_rules` (3 functions)
📄 `redsl.examples.full_pipeline` (2 functions)
📄 `redsl.examples.memory_learning` (6 functions)
📄 `redsl.examples.pr_bot` (6 functions)
📄 `redsl.examples.pyqual_example` (2 functions)
📦 `redsl.execution`
📄 `redsl.execution.cycle` (5 functions)
📄 `redsl.execution.decision` (9 functions)
📄 `redsl.execution.executor`
📄 `redsl.execution.reflector` (2 functions)
📄 `redsl.execution.reporter` (4 functions)
📄 `redsl.execution.resolution` (6 functions)
📄 `redsl.execution.sandbox_execution` (1 functions)
📄 `redsl.execution.validation` (2 functions)
📦 `redsl.formatters`
📄 `redsl.formatters.batch` (12 functions)
📄 `redsl.formatters.core` (1 functions)
📄 `redsl.formatters.cycle` (18 functions)
📄 `redsl.formatters.debug` (1 functions)
📄 `redsl.formatters.refactor` (9 functions)
📄 `redsl.history` (16 functions, 3 classes)
📦 `redsl.integrations`
📄 `redsl.integrations.webhook` (3 functions)
📦 `redsl.llm` (12 functions, 2 classes)
📄 `redsl.llm.gate` (7 functions, 2 classes)
📄 `redsl.llm.llx_router` (15 functions, 1 classes)
📦 `redsl.llm.registry`
📄 `redsl.llm.registry.aggregator` (15 functions, 1 classes)
📄 `redsl.llm.registry.models` (7 classes)
📦 `redsl.llm.registry.sources`
📄 `redsl.llm.registry.sources.base` (13 functions, 6 classes)
📄 `redsl.llm.selection` (27 functions, 6 classes)
📄 `redsl.main` (23 functions)
📦 `redsl.memory` (18 functions, 4 classes)
📄 `redsl.orchestrator` (5 functions, 2 classes)
📦 `redsl.refactors`
📄 `redsl.refactors._base` (1 functions, 1 classes)
📄 `redsl.refactors.ast_transformers` (9 functions, 2 classes)
📄 `redsl.refactors.body_restorer` (7 functions)
📄 `redsl.refactors.diff_manager` (9 functions)
📄 `redsl.refactors.direct` (6 functions, 1 classes)
📄 `redsl.refactors.direct_constants` (6 functions, 1 classes)
📄 `redsl.refactors.direct_guard` (6 functions, 1 classes)
📄 `redsl.refactors.direct_imports` (14 functions, 1 classes)
📄 `redsl.refactors.direct_types` (5 functions, 1 classes)
📄 `redsl.refactors.engine` (9 functions, 1 classes)
📄 `redsl.refactors.models` (3 classes)
📄 `redsl.refactors.prompts` (3 functions)
📦 `redsl.utils`
📄 `redsl.utils.json_helpers` (1 functions)
📄 `redsl.utils.tool_check` (1 functions)
📦 `redsl.validation`
📄 `redsl.validation.pyqual_bridge` (12 functions)
📄 `redsl.validation.regix_bridge` (8 functions, 1 classes)
📄 `redsl.validation.sandbox` (9 functions, 3 classes)
📄 `redsl.validation.testql_bridge` (10 functions, 2 classes)
📄 `redsl.validation.vallm_bridge` (7 functions, 1 classes)
📄 `test_refactor_bad.complex_code` (17 functions, 1 classes)
📄 `test_refactor_project.bad_code` (2 functions, 1 classes)

## Requirements

- Python >= >=3.11
- fastapi >=0.115.0- uvicorn >=0.44.0- pydantic >=2.10.0- litellm >=1.52.0- chromadb >=0.6.0- pyyaml >=6.0.2- rich >=13.9.0- httpx >=0.28.0- click >=8.1.7- python-dotenv >=1.0.1- goal >=2.1.0- costs >=0.1.20- pfix >=0.1.60

## Contributing

**Contributors:**
- Tom Sapletta

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/semcod/redsl
cd redsl

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## Documentation

- 📖 [Full Documentation](https://github.com/semcod/redsl/tree/main/docs) — API reference, module docs, architecture
- 🚀 [Getting Started](https://github.com/semcod/redsl/blob/main/docs/getting-started.md) — Quick start guide
- 📚 [API Reference](https://github.com/semcod/redsl/blob/main/docs/api.md) — Complete API documentation
- 🔧 [Configuration](https://github.com/semcod/redsl/blob/main/docs/configuration.md) — Configuration options
- 💡 [Examples](./examples) — Usage examples and code samples

### Generated Files

| Output | Description | Link |
|--------|-------------|------|
| `README.md` | Project overview (this file) | — |
| `docs/api.md` | Consolidated API reference | [View](./docs/api.md) |
| `docs/modules.md` | Module reference with metrics | [View](./docs/modules.md) |
| `docs/architecture.md` | Architecture with diagrams | [View](./docs/architecture.md) |
| `docs/dependency-graph.md` | Dependency graphs | [View](./docs/dependency-graph.md) |
| `docs/coverage.md` | Docstring coverage report | [View](./docs/coverage.md) |
| `docs/getting-started.md` | Getting started guide | [View](./docs/getting-started.md) |
| `docs/configuration.md` | Configuration reference | [View](./docs/configuration.md) |
| `docs/api-changelog.md` | API change tracking | [View](./docs/api-changelog.md) |
| `CONTRIBUTING.md` | Contribution guidelines | [View](./CONTRIBUTING.md) |
| `examples/` | Usage examples | [Browse](./examples) |
| `mkdocs.yml` | MkDocs configuration | — |

<!-- code2docs:end -->