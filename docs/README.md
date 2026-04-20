---
path: /home/tom/github/semcod/redsl
---

<!-- code2docs:start --># redsl

![version](https://img.shields.io/badge/version-0.1.0-blue) ![python](https://img.shields.io/badge/python-%3E%3D3.11-blue) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey) ![functions](https://img.shields.io/badge/functions-1544-green)
> **1544** functions | **221** classes | **277** files | CC̄ = 3.8

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




## Architecture

```
redsl/
├── project
    ├── propozycje
    ├── nda-wzor
    ├── smoke-test
    ├── nda-form
    ├── email-notifications
    ├── install-plesk
    ├── polityka-prywatnosci
    ├── config-editor
    ├── test-plesk
    ├── config-api
    ├── project
    ├── regulamin
    ├── app
    ├── index
        ├── access_token
        ├── authorize
        ├── user
        ├── logs
        ├── index
        ├── tickets
        ├── auth
        ├── invoices
        ├── scans
        ├── contracts
        ├── clients
        ├── index
        ├── invoice-generator
        ├── scan-worker
        ├── projects
        ├── vallm-pre-commit
        ├── index
        ├── main
        ├── main
        ├── main
├── redsl/
    ├── __main__
    ├── consciousness_loop
        ├── main
        ├── main
        ├── _fixer_utils
        ├── cli_awareness
        ├── doctor
        ├── sumr_planfile/
        ├── doctor_indent_fixers
        ├── _scan_report
        ├── planfile_bridge
        ├── main
        ├── main
        ├── doctor_fstring_fixers
        ├── _guard_fixers
        ├── doctor_fixers
        ├── doctor_helpers
        ├── main
        ├── github_source
        ├── main
        ├── cli_doctor
        ├── cli_autonomy
        ├── hybrid
        ├── _indent_fixers
        ├── main
        ├── batch
    ├── history
            ├── verdict
        ├── batch_pyqual/
        ├── pre-commit-hook
        ├── doctor_data
            ├── utils
        ├── scan
            ├── runner
        ├── main
            ├── helpers
        ├── doctor_detectors
            ├── config_gen
        ├── autofix/
            ├── runner
            ├── discovery
            ├── models
            ├── reporting
            ├── todo_gen
            ├── discovery
            ├── reporting
            ├── hybrid
            ├── parsers
            ├── ruff_analyzer
    ├── bad_code
            ├── mypy_analyzer
            ├── core
            ├── pipeline
        ├── plan_sync
            ├── bandit_analyzer
            ├── utils
            ├── extractors
            ├── fix_decisions
            ├── models
            ├── ast_analyzer
    ├── complex_code
            ├── reporter
            ├── reporter
        ├── pyqual/
        ├── autonomy_pr/
            ├── validator
            ├── git_ops
            ├── analyzer
        ├── catalog
        ├── nlp_handlers
        ├── security
        ├── models
    ├── config_standard/
        ├── multi_project
        ├── store
        ├── paths
    ├── defaults/
        ├── basic_analysis
    ├── examples/
        ├── profiles
        ├── _common
        ├── agent_bridge
        ├── badge
        ├── custom_rules
    ├── config
        ├── awareness
        ├── api_integration
            ├── models
        ├── audit
    ├── diagnostics/
    ├── core/
        ├── pr_bot
        ├── pipeline
        ├── review
        ├── intent
    ├── autonomy/
        ├── perf_bridge
        ├── metrics
        ├── adaptive_executor
        ├── smart_scorer
        ├── full_pipeline
            ├── pipeline
    ├── formatters/
        ├── refactor
        ├── growth_control
            ├── models
        ├── core
        ├── debug
        ├── quality_gate
        ├── batch
    ├── memory/
        ├── examples
        ├── cycle
        ├── pyqual
        ├── config
        ├── __main__
    ├── cli/
        ├── scan
        ├── refactor
        ├── llm_banner
        ├── utils
        ├── applier
        ├── model_policy
        ├── debug
        ├── batch
        ├── models
        ├── planfile
        ├── reporter
    ├── execution/
        ├── resolution
        ├── decision
        ├── auto_fix
        ├── sandbox_execution
        ├── validation
        ├── executor
        ├── scheduler
        ├── backup_manager
        ├── project_scanner
        ├── memory_learning
        ├── base
    ├── bridges/
        ├── gate
    ├── llm/
        ├── selection/
        ├── reflector
        ├── registry/
        ├── llx_router
        ├── pyqual_example
            ├── aggregator
            ├── sources/
            ├── ops
            ├── config
            ├── metrics
                ├── base
            ├── checks
    ├── orchestrator
            ├── models
            ├── selector
        ├── direct_types
        ├── direct_guard
        ├── direct
        ├── engine
        ├── diff_manager
        ├── prompts
        ├── direct_imports
        ├── body_restorer
    ├── refactors/
        ├── cycle
            ├── models
        ├── _base
    ├── ci/
        ├── direct_constants
        ├── workflow
        ├── github_actions
        ├── workflow
        ├── git_timeline
            ├── strategy
        ├── timeline_git
        ├── timeline_toon
        ├── timeline_analysis
        ├── proactive
    ├── awareness/
        ├── change_patterns
        ├── self_model
    ├── validation/
        ├── sandbox
        ├── ecosystem
        ├── health_model
        ├── timeline_models
        ├── tool_check
    ├── utils/
        ├── json_helpers
        ├── planfile_updater
        ├── testql_bridge
        ├── vallm_bridge
        ├── pyqual_bridge
        ├── analyzer
        ├── python_analyzer
    ├── analyzers/
        ├── regix_bridge
        ├── incremental
        ├── metrics
        ├── utils
        ├── sumd_bridge
        ├── toon_analyzer
        ├── redup_bridge
        ├── resolver
        ├── semantic_chunker
        ├── code2llm_bridge
        ├── parsers/
            ├── validation_parser
            ├── duplication_parser
    ├── integrations/
        ├── webhook
        ├── pyqual_routes
            ├── functions_parser
        ├── health_routes
    ├── api/
        ├── webhook_routes
        ├── debug_routes
        ├── example_routes
        ├── radon_analyzer
    ├── dsl/
            ├── project_parser
        ├── rule_generator
        ├── engine
        ├── deploy_detector
        ├── ast_transformers
        ├── refactor_routes
    ├── main
    ├── models
        ├── quality_visitor
        ├── models
        ├── secrets
        ├── llm_policy
        ├── proposals
        ├── core
        ├── models
        ├── logging
```

## API Overview

### Classes

- **`ConsciousnessLoop`** — Ciągła pętla „świadomości" agenta.
- **`HistoryEvent`** — A single persisted event in the refactor history.
- **`HistoryWriter`** — Append-only history logger backed by .redsl/history.jsonl.
- **`HistoryReader`** — Read-only access to .redsl/history.jsonl for querying and dedup.
- **`Issue`** — A single detected issue.
- **`DoctorReport`** — Aggregated report for one project.
- **`ProjectScanResult`** — Scan result for a single project.
- **`ProjectFixResult`** — Result of autofix processing for a single project.
- **`RuffAnalyzer`** — Uruchamia ruff i zbiera wyniki.
- **`BadClass`** — —
- **`MypyAnalyzer`** — Uruchamia mypy i zbiera wyniki.
- **`MergeResult`** — —
- **`SyncResult`** — —
- **`BanditAnalyzer`** — Uruchamia bandit i zbiera wyniki bezpieczeństwa.
- **`PyqualProjectResult`** — Result of pyqual pipeline for a single project.
- **`AstAnalyzer`** — Analizuje pliki Python przez AST w poszukiwaniu typowych problemów jakości.
- **`GodClass`** — A god class with too many responsibilities.
- **`Reporter`** — Generuje rekomendacje i zapisuje raporty analizy jakości.
- **`PyQualAnalyzer`** — Python code quality analyzer — fasada nad wyspecjalizowanymi analizatorami.
- **`PathCatalogEntry`** — —
- **`ToolError`** — Raised when a tool call fails validation or execution.
- **`SecretMatch`** — —
- **`SecretInterceptor`** — Redact secret-looking substrings before data is shown to an LLM.
- **`ProjectAnalysis`** — Wyniki analizy pojedynczego projektu.
- **`MultiProjectReport`** — Zbiorczy raport z analizy wielu projektów.
- **`MultiProjectRunner`** — Uruchamia ReDSL na wielu projektach.
- **`ConfigStoreError`** — —
- **`ConfigVersionMismatch`** — —
- **`ConfigValidationError`** — —
- **`ConfigHistoryRecord`** — —
- **`ConfigStore`** — Manage a redsl-config directory with manifest, profiles and history.
- **`ConfigBridgeError`** — Raised when config bridge cannot resolve configuration.
- **`LLMConfig`** — Konfiguracja warstwy LLM.
- **`MemoryConfig`** — Konfiguracja systemu pamięci.
- **`AnalyzerConfig`** — Konfiguracja analizatora kodu.
- **`RefactorConfig`** — Konfiguracja silnika refaktoryzacji.
- **`AgentConfig`** — Główna konfiguracja agenta.
- **`StepResult`** — —
- **`PipelineStep`** — Abstract base for a single pipeline step.
- **`PipelineResult`** — —
- **`Pipeline`** — Run a sequence of PipelineStep objects against a shared context dict.
- **`Bottleneck`** — —
- **`CriticalStep`** — —
- **`PerformanceReport`** — —
- **`AutonomyMetrics`** — Metrics for the autonomy subsystem.
- **`AdaptiveExecutor`** — Execute decisions while adapting strategy on repeated failures.
- **`ProjectContext`** — Mutable context passed through pipeline stages.
- **`GrowthBudget`** — LOC growth budget per iteration.
- **`GrowthController`** — Enforce growth budgets on a project.
- **`ModuleBudget`** — Complexity budget for a single module.
- **`PlanTask`** — —
- **`SumrData`** — —
- **`PlanfileResult`** — —
- **`GateVerdict`** — Result of a quality gate check.
- **`MemoryEntry`** — Pojedynczy wpis w pamięci.
- **`MemoryLayer`** — Warstwa pamięci oparta na ChromaDB.
- **`InMemoryCollection`** — Fallback gdy ChromaDB nie jest dostępne.
- **`AgentMemory`** — Kompletny system pamięci z trzema warstwami.
- **`ApplyResult`** — —
- **`ConfigApplier`** — Apply config proposals atomically with locking and audit logging.
- **`AutoFixResult`** — Outcome of the auto-fix pipeline.
- **`AutonomyMode`** — —
- **`Scheduler`** — Periodic quality-improvement loop.
- **`ProjectMap`** — Structured inventory of config files found in a project.
- **`CliBridge`** — Base class for bridges wrapping external CLI tools.
- **`ModelRejectedError`** — Raised when model is rejected by policy.
- **`ModelAgeGate`** — Enforces model age and lifecycle policy before LLM calls.
- **`LLMResponse`** — Odpowiedź z modelu LLM.
- **`LLMLayer`** — Warstwa abstrakcji nad LLM z obsługą:
- **`ModelSelection`** — —
- **`RegistryAggregator`** — Aggregates model info from multiple sources with caching.
- **`ModelRegistrySource`** — Abstract base class for model registry sources.
- **`OpenRouterSource`** — OpenRouter public API - no auth required, ~300+ models.
- **`ModelsDevSource`** — Models.dev community API - public, ~200+ models.
- **`OpenAIProviderSource`** — Native OpenAI API - requires key, authoritative for OpenAI models.
- **`AnthropicProviderSource`** — Native Anthropic API - requires key, authoritative for Claude models.
- **`AiderLeaderboardSource`** — Drugie niezależne źródło — benchmark polyglot od Aider.
- **`CycleReport`** — Raport z jednego cyklu refaktoryzacji.
- **`RefactorOrchestrator`** — Główny orkiestrator — „mózg" systemu.
- **`CostProfile`** — Jak liczymy koszt per model.
- **`CodingRequirements`** — Wymagania techniczne dla modelu do kodowania.
- **`ModelCandidate`** — Kandydat na model z metrykami.
- **`ModelSelectionError`** — Raised when no model can be selected.
- **`ModelSelector`** — Wybiera najtańszy model spełniający wymagania.
- **`DirectTypesRefactorer`** — Handles return type annotation addition.
- **`DirectGuardRefactorer`** — Handles main guard wrapping for module-level execution code.
- **`DirectRefactorEngine`** — Applies simple refactorings directly via AST manipulation.
- **`RefactorEngine`** — Silnik refaktoryzacji z pętlą refleksji.
- **`DirectImportRefactorer`** — Handles import-related direct refactoring.
- **`PolicyMode`** — Policy mode for model age checking.
- **`UnknownReleaseAction`** — Action when model release date is unknown.
- **`Pricing`** — Ceny USD per token (nie per million!).
- **`Capabilities`** — Features modelu istotne dla programowania.
- **`QualitySignals`** — Sygnały jakości z różnych benchmarków.
- **`ModelInfo`** — Information about an LLM model.
- **`PolicyDecision`** — Result of policy check for a model.
- **`DirectRefactorBase`** — Mixin that provides ``get_applied_changes`` for Direct* refactorers.
- **`DirectConstantsRefactorer`** — Handles magic number to constant extraction.
- **`PerceiveConfig`** — —
- **`DecideConfig`** — —
- **`ExecuteConfig`** — —
- **`TuneConfig`** — —
- **`ValidateStepConfig`** — —
- **`ValidateConfig`** — —
- **`PlanfileConfig`** — —
- **`ReflectConfig`** — —
- **`StorageConfig`** — Controls where redsl stores its logs and LLM chat history.
- **`DeployConfig`** — Controls whether and how redsl performs push / publish after a cycle.
- **`ProjectMapConfig`** — Inventory of configuration files found in the project.
- **`WorkflowConfig`** — —
- **`WorkflowConfig`** — Konfiguracja generowanego workflow.
- **`GitTimelineAnalyzer`** — Build a historical metric timeline from git commits — facade.
- **`SelectionStrategy`** — Strategia wyboru modelu.
- **`GitTimelineProvider`** — Provides git-based timeline data.
- **`ToonCollector`** — Collects and processes toon files from git history.
- **`TimelineAnalyzer`** — Analyzes metric trends from timeline data.
- **`ProactiveAlert`** — A proactive issue detected from trends.
- **`ProactiveAnalyzer`** — Turn trend forecasts into alerts and suggested interventions.
- **`AwarenessSnapshot`** — Compact overview of the current awareness state for a project.
- **`AwarenessManager`** — Facade that combines all awareness layers into one snapshot.
- **`ChangePattern`** — A learned pattern describing a recurring change shape.
- **`ChangePatternLearner`** — Infer patterns from timeline deltas and trend transitions.
- **`CapabilityStat`** — Track how well the agent performs a capability.
- **`AgentCapabilityProfile`** — Structured self-assessment summary.
- **`SelfModel`** — Introspective model backed by agent memory.
- **`DockerNotFoundError`** — Raised when Docker daemon is not available.
- **`SandboxError`** — Raised for sandbox-level failures.
- **`RefactorSandbox`** — Docker sandbox do bezpiecznego testowania refaktoryzacji.
- **`ProjectNode`** — Single project node in the ecosystem graph.
- **`EcosystemGraph`** — Basic ecosystem graph for semcod-style project collections.
- **`HealthDimension`** — Single health dimension with score and rationale.
- **`UnifiedHealth`** — Aggregated health snapshot.
- **`HealthModel`** — Combine timeline metrics into a single health snapshot.
- **`MetricPoint`** — Single timeline point captured from a git commit.
- **`TrendAnalysis`** — Trend summary for a single metric series.
- **`TimelineSummary`** — High-level summary of a git timeline.
- **`TestqlVerdict`** — Validation verdict from testql scenario execution.
- **`TestqlValidator`** — Post-refactoring validator using testql scenarios.
- **`CodeAnalyzer`** — Główny analizator kodu — fasada.
- **`PythonAnalyzer`** — Analizator plików .py przez stdlib ast.
- **`EvolutionaryCache`** — Cache wyników analizy per-plik oparty o hash pliku.
- **`IncrementalAnalyzer`** — Analizuje tylko zmienione pliki i scala z cached wynikami.
- **`CodeMetrics`** — Metryki pojedynczej funkcji/modułu.
- **`AnalysisResult`** — Wynik analizy projektu.
- **`SumdMetrics`** — Metrics extracted from sumd analysis.
- **`SumdAnalyzer`** — Native project analyzer using sumd extractor patterns.
- **`ToonAnalyzer`** — Analizator plików toon — przetwarza dane z code2llm.
- **`PathResolver`** — Resolver ścieżek i kodu źródłowego funkcji.
- **`SemanticChunk`** — Wycięty semantyczny fragment kodu gotowy do wysłania do LLM.
- **`SemanticChunker`** — Buduje semantyczne chunki kodu dla LLM.
- **`ToonParser`** — Parser plików toon — fasada nad wyspecjalizowanymi parserami.
- **`ValidationParser`** — Parser sekcji validation_toon.
- **`DuplicationParser`** — Parser sekcji duplication_toon.
- **`FunctionsParser`** — Parser sekcji functions_toon — per-funkcja CC.
- **`ProjectParser`** — Parser sekcji project_toon.
- **`LearnedRule`** — Reguła DSL wygenerowana z wzorców w pamięci.
- **`RuleGenerator`** — Generuje nowe reguły DSL z historii refaktoryzacji w pamięci agenta.
- **`Operator`** — —
- **`RefactorAction`** — —
- **`Condition`** — Pojedynczy warunek DSL.
- **`Rule`** — Reguła DSL: warunki → akcja z priorytetem.
- **`Decision`** — Wynik ewaluacji reguł — decyzja co refaktoryzować.
- **`DSLEngine`** — Silnik ewaluacji reguł DSL.
- **`DeployAction`** — A single detected push or publish action.
- **`DetectedDeployConfig`** — Result of auto-detection for a single project.
- **`ReturnTypeAdder`** — AST transformer to add return type annotations.
- **`UnusedImportRemover`** — AST transformer to remove unused imports.
- **`FileChange`** — Zmiana w pojedynczym pliku.
- **`RefactorProposal`** — Propozycja refaktoryzacji wygenerowana przez LLM.
- **`RefactorResult`** — Wynik zastosowania refaktoryzacji.
- **`CodeQualityVisitor`** — Detects common code quality issues in Python AST.
- **`FileChange`** — Zmiana w pojedynczym pliku.
- **`RefactorProposal`** — Propozycja refaktoryzacji wygenerowana przez LLM.
- **`RefactorResult`** — Wynik zastosowania refaktoryzacji.
- **`SecretRotation`** — —
- **`SecretSpec`** — —
- **`LLMPolicy`** — —
- **`CostWeights`** — —
- **`CodingTiers`** — —
- **`DefaultOperationTiers`** — —
- **`CodingConfig`** — —
- **`ProposalMetadata`** — —
- **`ConfigPreconditions`** — —
- **`ConfigValidationState`** — —
- **`ConfigChange`** — —
- **`ConfigChangeProposal`** — —
- **`ConfigOrigin`** — —
- **`ConfigMetadata`** — —
- **`RegistrySource`** — —
- **`CacheConfig`** — —
- **`RedslConfigSpec`** — —
- **`RedslConfigDocument`** — —
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

- `parseSelection()` — —
- `h()` — —
- `check_http()` — —
- `check_content()` — —
- `check_php_syntax()` — —
- `check_env_exists()` — —
- `check_encryption_key()` — —
- `check_directories()` — —
- `check_admin_auth()` — —
- `check_cron_scripts()` — —
- `fetchCompanyData()` — —
- `h()` — —
- `generateNDAText()` — —
- `generateProposalEmail()` — —
- `sendProposalEmail()` — —
- `generateAccessToken()` — —
- `verifyAccessToken()` — —
- `loadConfig()` — —
- `saveConfig()` — —
- `getNestedValue()` — —
- `getRiskLevel()` — —
- `check_status()` — —
- `check_contains()` — —
- `check_not_contains()` — —
- `validateConfig()` — —
- `getHistory()` — —
- `redactSecrets()` — —
- `target()` — —
- `form()` — —
- `emailField()` — —
- `nameField()` — —
- `repoField()` — —
- `submitBtn()` — —
- `setInvalid()` — —
- `validEmail()` — —
- `validRepo()` — —
- `io()` — —
- `details()` — —
- `flash()` — —
- `headline()` — —
- `y()` — —
- `load_env()` — —
- `env()` — —
- `h()` — —
- `csrf_token()` — —
- `check_rate_limit()` — —
- `send_notification()` — —
- `send_notification_smtp()` — —
- `h()` — —
- `classForLevel()` — —
- `fmtSize()` — —
- `validateCsrfToken()` — —
- `h()` — —
- `main()` — —
- `main()` — —
- `demo_policy_check()` — Demonstrate checking models against policy.
- `demo_list_allowed()` — Demonstrate listing all allowed models.
- `demo_safe_completion()` — Demonstrate safe completion with policy enforcement.
- `demo_strict_mode()` — Demonstrate strict vs non-strict mode.
- `main()` — Run all demos.
- `main_loop()` — Punkt wejścia dla pętli ciągłej.
- `main()` — —
- `main()` — —
- `register(cli, host_module)` — Register all awareness commands on the given Click group.
- `diagnose(root)` — Run all detectors on a project and return a report (no fixes applied).
- `heal(root, dry_run)` — Diagnose and fix issues in a project.
- `heal_batch(semcod_root, dry_run)` — Run doctor on all semcod subprojects.
- `render_markdown(results, folder)` — Render a markdown priority report from scan results.
- `is_available()` — Return True if planfile CLI is installed and functional.
- `create_ticket(project_dir, title, description, priority)` — Create a planfile ticket for a refactoring action.
- `list_tickets(project_dir, status)` — List planfile tickets, optionally filtered by status.
- `report_refactor_results(project_dir, decisions_applied, files_modified, avg_cc_before)` — Create a summary ticket for a completed refactor cycle.
- `main()` — —
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
- `resolve_auth_ref(auth_ref)` — Resolve an auth_ref string to a plaintext token.
- `fingerprint_issue(issue)` — Compute a stable fingerprint of the externally-visible issue state.
- `fetch_issues(source_config)` — Fetch issues from GitHub according to source_config.
- `main()` — —
- `register(cli)` — Register the doctor command group on the given Click group.
- `register(cli, host_module)` — Register all autonomy commands on the given Click group.
- `run_hybrid_quality_refactor(project_path, max_changes)` — Apply ALL quality refactorings to a project without LLM.
- `run_hybrid_batch(semcod_root, max_changes)` — Run hybrid refactoring on all semcod projects.
- `main()` — —
- `run_semcod_batch(semcod_root, max_actions)` — Run batch refactoring on semcod projects.
- `apply_refactor(project_path, max_actions)` — Apply reDSL to a project and return the report.
- `measure_todo_reduction(project_path)` — Measure TODO.md before and after refactoring.
- `compute_verdict(result, require_pipeline, require_push, require_publish)` — Compute final verdict for a project result.
- `main()` — Run pre-commit validation.
- `run_cmd(cmd, cwd, timeout)` — Run a shell command and return the result.
- `git_status_lines(project)` — Return non-empty git status lines for *project*, or [] on error.
- `resolve_profile(requested_profile, run_pipeline, publish)` — Resolve the effective pyqual profile based on CLI options.
- `scan_folder(folder, progress)` — Scan all sub-projects in *folder* and return sorted results.
- `run_pyqual_batch(workspace_root, max_fixes, run_pipeline, git_push)` — Run ReDSL + pyqual on all projects in workspace.
- `main()` — —
- `detect_broken_guards(root)` — Find Python files with syntax errors caused by misplaced ``if __name__`` guards.
- `detect_stolen_indent(root)` — Find files where function/class body lost indentation after guard removal.
- `detect_broken_fstrings(root)` — Find files with broken f-strings (single brace, missing open brace).
- `detect_stale_pycache(root)` — Find stale __pycache__ directories.
- `detect_missing_install(root)` — Check whether the project's own package is importable.
- `detect_module_level_exit(root)` — Find test files with bare ``sys.exit(...)`` outside ``if __name__`` guard.
- `detect_version_mismatch(root)` — Find tests that hardcode a version string that differs from VERSION file.
- `detect_pytest_cli_collision(root)` — Check if ``python -m pytest`` is hijacked by a Typer/Click CLI.
- `run_autofix_batch(semcod_root, max_changes)` — Run full autofix pipeline on all semcod packages.
- `refactor_plan_to_tasks(yaml_content, source)` — Backward-compat alias: parse refactor_plan.yaml → list[PlanTask].
- `parse_sumr(path)` — Parse a SUMR.md file and extract refactoring-relevant data.
- `parse_refactor_plan_yaml(yaml_content, source)` — Parse refactor_plan.yaml content into raw task dicts.
- `get_toon_patterns()` — Get all TOON parsing regex patterns.
- `calculate(x, y, z)` — —
- `generate_planfile(project_path)` — Generate or update planfile.yaml for *project_path* from SUMR.md.
- `merge_tasks(existing_tasks, incoming_issues, source_id)` — Merge incoming GitHub issues into existing local tasks for one source.
- `apply_planfile_sources(planfile_path, dry_run)` — Read planfile.yaml, sync all github sources, write result.
- `make_id_generator()` — Return a closure that generates sequential IDs with given prefix.
- `deduplicate_tasks(tasks)` — Remove duplicate tasks with same (action, file) pair.
- `merge_with_existing_planfile(tasks, planfile_path)` — Merge task statuses with existing planfile (preserve in_progress/done).
- `tasks_to_planfile_yaml(tasks, project_name, project_version, sources)` — Serialise tasks to planfile.yaml YAML string.
- `extract_refactor_decisions(toon_content, source, _next_id)` — Extract tasks from refactor cycle TOON (DECISIONS[] section).
- `extract_complexity_layers(toon_content, source, _next_id, project_path)` — Extract tasks from code analysis TOON (LAYERS with high CC).
- `extract_duplications(toon_content, source, _next_id)` — Extract tasks from Duplication TOON (DUPLICATES section).
- `refactor_plan_to_tasks(yaml_content, source)` — Convert a redsl ``refactor_plan.yaml`` to PlanTask list.
- `toon_to_tasks(toon_content, source, project_path)` — Extract PlanTask list from TOON-format content.
- `build_pyqual_fix_decisions(issues, project_path)` — Build direct-refactor Decisions grouped by file from pyqual issues.
- `process_data(data, mode, threshold, callback)` — Very complex function with high CC.
- `process_data_copy(data, mode, threshold, callback)` — Copy of process_data - exact duplicate.
- `run_pyqual_analysis(project_path, config_path, output_format)` — Run pyqual analysis on a project.
- `run_pyqual_fix(project_path, config_path)` — Run automatic fixes based on pyqual analysis.
- `run_autonomous_pr(git_url, max_actions, dry_run, auto_apply)` — Run the autonomous PR workflow.
- `get_risk_level(path)` — Return risk level for a config path. Falls back to 'low' for unknown paths.
- `search_schema_matches(query)` — Return catalog entries matching *query* across path/title/description/aliases.
- `dispatch_tool(tool_name, arguments)` — Route an LLM tool call to the correct handler.
- `is_sensitive_key(key)` — —
- `mask_sensitive_mapping(data)` — Return a shallow copy with secret-like values masked.
- `run_multi_analysis(project_dirs, config)` — Convenience function — analiza wielu projektów.
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
- `build_default_config()` — —
- `config_doc_to_yaml(document)` — —
- `export_config_schema()` — —
- `load_example_yaml(example_name, scenario, source)` — —
- `list_available_examples()` — Return metadata for every example that has at least a ``default.yaml``.
- `print_banner(title, width, char)` — —
- `parse_scenario(argv)` — —
- `resolve_secret_ref(secret)` — Resolve a secret reference to its actual value.
- `find_config_root(start_path)` — Find redsl-config directory by walking up from start_path or cwd.
- `load_agent_config_from_substrate(config_root, profile)` — Load AgentConfig from config substrate, resolving secrets.
- `agent_config_from_substrate_or_env(config_root, profile)` — Try substrate first, fall back to env-based config.
- `run_badge_example(scenario, source)` — —
- `main(argv)` — —
- `run_custom_rules_example(scenario, source)` — —
- `main(argv)` — —
- `run_awareness_example(scenario, source)` — —
- `main(argv)` — —
- `run_api_integration_example(scenario, source)` — —
- `main(argv)` — —
- `run_audit_example(scenario, source)` — —
- `main(argv)` — —
- `run_pr_bot_example(scenario, source)` — —
- `main(argv)` — —
- `review_staged_changes(project_dir, model_override, max_diff_chars)` — Return a textual code review for all staged/unstaged changes.
- `analyze_commit_intent(project_dir)` — Analyse the current working-tree changes and return an intent report.
- `profile_refactor_cycle(project_dir)` — Profiluj jeden cykl analizy/refaktoryzacji za pomocą metrun (lub fallback).
- `profile_llm_latency()` — Zmierz latencję wywołań LLM — kluczowy bottleneck.
- `profile_memory_operations()` — Zmierz czas operacji ChromaDB — store, recall, similarity search.
- `generate_optimization_report(project_dir)` — Wygeneruj raport z sugestiami optymalizacji (używany przez CLI i loop).
- `collect_autonomy_metrics(project_dir)` — Collect all autonomy metrics for a project.
- `save_metrics(metrics, path)` — Save metrics to a JSON file.
- `load_metrics(path)` — Load metrics from a JSON file.
- `smart_score(rule, context)` — Compute a multi-dimensional score for a refactoring decision.
- `run_full_pipeline_example(scenario, source, model)` — —
- `main(argv)` — —
- `process_project(project, max_fixes, run_pipeline, git_push)` — Full ReDSL + pyqual pipeline for a single project.
- `format_refactor_plan(decisions, format, analysis)` — Format refactoring plan in specified format.
- `check_module_budget(file_path, module_type)` — Check whether a module stays within its complexity budget.
- `format_debug_info(info, format)` — Format debug information.
- `run_quality_gate(project_dir)` — Check whether current changes pass the quality gate.
- `install_pre_commit_hook(project_dir)` — Install a git pre-commit hook that runs the quality gate.
- `format_batch_results(results, format)` — Format batch processing results.
- `format_batch_report_markdown(report, root, title)` — Format a batch run report as Markdown.
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
- `format_cycle_report_yaml(report, decisions, analysis)` — Format full cycle report as YAML for stdout.
- `format_cycle_report_markdown(report, decisions, analysis, project_path)` — Format a refactor cycle as a Markdown report.
- `format_plan_yaml(decisions, analysis)` — Format dry-run plan as YAML for stdout.
- `format_cycle_report_toon(report, decisions, analysis, project_path)` — Format a refactor cycle as TOON for planfile integration.
- `pyqual()` — Python code quality analysis commands.
- `pyqual_analyze(project_path, config, format)` — Analyze Python code quality.
- `pyqual_fix(project_path, config)` — Apply automatic quality fixes.
- `register_pyqual(cli)` — —
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
- `cli(ctx, verbose)` — reDSL - Automated code refactoring tool.
- `scan(ctx, folder, output_path, quiet)` — Scan a folder of projects and produce a markdown priority report.
- `refactor(ctx, project_path, max_actions, dry_run)` — Run refactoring on a project.
- `register_refactor(cli)` — —
- `print_llm_banner()` — Print the LLM config banner to stderr.
- `perf_command(ctx, project_path)` — Profile a refactoring cycle and report performance bottlenecks.
- `cost_command(ctx, project_path, max_actions)` — Estimate LLM cost for the next refactoring cycle without running it.
- `register_model_policy(cli)` — Register model-policy commands.
- `model_policy()` — Manage LLM model age and lifecycle policy.
- `check_model(model, json_output)` — Check if a model is allowed by policy.
- `list_models(max_age, provider, json_output, limit)` — List models currently allowed by policy.
- `refresh_registry()` — Force refresh model registry from sources.
- `show_config()` — Show current model policy configuration.
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
- `register_models(cli)` — Register model selection commands.
- `models_group()` — Model selection for coding - cheapest suitable model.
- `pick_coding(tier, min_context, require_tools, show_all)` — Pokaż jaki model zostałby wybrany dla danego tieru.
- `list_coding(tier, limit, show_rejected, sort)` — Tabela modeli spełniających wymagania coding, posortowana po cenie.
- `estimate_cost(tier, input_tokens, output_tokens, ops_per_day)` — Estimate monthly cost for given tier and usage pattern.
- `show_coding_config()` — Show current coding model selection configuration.
- `planfile_group()` — SUMR.md → planfile.yaml task generation.
- `planfile_sync(project_path, sumr_path, dry_run, no_merge)` — Generate or update planfile.yaml from SUMR.md.
- `planfile_show(project_path, status, output_format)` — Show tasks from an existing planfile.yaml.
- `auth_group()` — Manage authentication credentials for planfile sources.
- `auth_github()` — GitHub authentication helpers.
- `auth_github_login(token, env_var)` — Store a GitHub token for planfile sync.
- `source_group()` — Manage task sources (GitHub, SUMR) in planfile.yaml.
- `source_list(project_path)` — List configured sources in planfile.yaml.
- `source_remove(source_id, project_path)` — Remove a source from planfile.yaml.
- `source_add(repo, auth_ref, labels, state)` — Add a GitHub source to planfile.yaml.
- `planfile_gh_sync(project_path, dry_run, output_format)` — Fetch GitHub issues into planfile.yaml (three-way merge).
- `register(cli_group)` — —
- `explain_decisions(orchestrator, project_dir, limit)` — Explain refactoring decisions without executing them.
- `get_memory_stats(orchestrator)` — Return memory and runtime statistics for the orchestrator.
- `estimate_cycle_cost(orchestrator, project_dir, max_actions)` — Estimate the cost of the next cycle without executing it.
- `auto_fix_violations(project_dir, violations)` — Try to automatically fix each violation; create ticket on failure.
- `execute_sandboxed(orchestrator, decision, project_dir)` — Execute a decision in a sandboxed environment.
- `ensure_gitignore(project_dir)` — Add .redsl/ to project .gitignore if not already present.
- `list_backups(project_dir)` — Return all ``.bak`` files stored in ``.redsl/backups/``.
- `has_backups(project_dir)` — —
- `cleanup_backups(project_dir)` — Remove all backups after a successful cycle.
- `rollback_from_backups(project_dir)` — Restore all backed-up files to their original locations.
- `scan_project(project_dir)` — Scan *project_dir* and return a :class:`ProjectMap`.
- `project_map_to_yaml_block(pm, indent)` — Render a ProjectMap as a YAML block suitable for embedding in redsl.yaml.
- `run_memory_learning_example(scenario, source)` — —
- `main(argv)` — —
- `get_gate()` — Get or create the global ModelAgeGate singleton.
- `safe_completion(model)` — Drop-in replacement for litellm.completion with policy enforcement.
- `check_model_policy(model)` — Check if a model is allowed without making an LLM call.
- `list_allowed_models()` — List all models currently allowed by policy.
- `select_model(action, context, budget_remaining)` — Wybierz optymalny model na podstawie akcji i kontekstu.
- `select_reflection_model(use_local)` — Wybierz model do refleksji — zawsze tańszy.
- `estimate_cycle_cost(decisions, contexts)` — Szacuj koszt całego cyklu refaktoryzacji — lista per decyzja.
- `apply_provider_prefix(model, configured_model)` — Apply provider prefix from configured model to a bare model name.
- `call_via_llx(messages, task_type)` — Deleguj wywołanie LLM do llx CLI jeśli dostępne.
- `run_pyqual_example(scenario, source)` — —
- `main(argv)` — —
- `select_model_for_operation(operation)` — Mapping: 'extract_function' → tier z .env → konkretny model.
- `build_selector(aggregator, gate)` — Build ModelSelector from environment configuration.
- `get_selector()` — Get or build the global ModelSelector.
- `invalidate_selector()` — Invalidate the global selector cache (e.g., after config change).
- `track_model_selection(model, tier, operation)` — Track model selection for metrics.
- `check_cost_per_call(estimated_cost_usd)` — Check if cost is within safety limits.
- `check_hard_requirements(info, req)` — Check if model meets hard requirements.
- `score_quality(info)` — Syntetyczna jakość 0-100 z dostępnych sygnałów.
- `generate_diff(original, refactored, file_path)` — Wygeneruj unified diff dla dwóch wersji pliku.
- `preview_proposal(proposal, project_dir)` — Wygeneruj sformatowany diff wszystkich zmian w propozycji.
- `create_checkpoint(project_dir)` — Utwórz checkpoint aktualnego stanu projektu.
- `rollback_to_checkpoint(checkpoint_id, project_dir)` — Cofnij projekt do stanu z checkpointa.
- `rollback_single_file(file_path, checkpoint_id, project_dir)` — Cofnij jeden plik do stanu z checkpointa.
- `build_ecosystem_context(context)` — Render a short ecosystem/context block for prompts.
- `repair_file(path)` — Attempt to restore stolen class/function bodies in *path*.
- `repair_directory(root, dry_run)` — Walk *root* and repair all damaged Python files.
- `run_cycle(orchestrator, project_dir, max_actions, use_code2llm)` — Run a complete refactoring cycle driven by WorkflowConfig.
- `run_from_toon_content(orchestrator, project_toon, duplication_toon, validation_toon)` — Run a cycle from pre-parsed toon content.
- `default_workflow()` — —
- `load_workflow(project_dir)` — Load workflow config for *project_dir*.
- `generate_github_workflow(project_dir, config, output_path)` — Wygeneruj zawartość pliku .github/workflows/redsl.yml.
- `install_github_workflow(project_dir, config, overwrite)` — Zainstaluj workflow w projekcie (.github/workflows/redsl.yml).
- `workflow_group()` — Manage redsl.yaml — declarative refactor pipeline config.
- `workflow_init(project_dir, name, force)` — Generate redsl.yaml in PROJECT_DIR.
- `workflow_show(project_dir)` — Show effective workflow config for PROJECT_DIR (resolved with fallbacks).
- `workflow_scan(project_dir, write, print_only)` — Scan PROJECT_DIR and build a map of configuration files.
- `register(cli_group)` — —
- `apply_strategy(candidates, strategy)` — Apply selection strategy to candidates.
- `sandbox_available()` — True if Docker or pactfix is available for sandbox testing.
- `is_tool_available(cmd, timeout)` — Return True if running *cmd* exits with code 0 within *timeout* seconds.
- `extract_json_block(text)` — Extract first JSON block from *text*, skipping preamble lines.
- `mark_applied_tasks_done(project_dir, applied_files)` — Mark planfile tasks whose ``file:`` matches applied files as done.
- `get_todo_tasks(project_dir)` — Return list of todo tasks from planfile.yaml, sorted by priority (ascending).
- `run_tasks_from_planfile(orchestrator, project_dir, max_actions, use_code2llm)` — Iterate over planfile todo tasks and run refactor for each file directly.
- `add_quality_task(project_dir, title, description, priority)` — Append a new todo task to planfile.yaml for quality improvement.
- `validate_with_testql(project_dir, scenarios_dir, config)` — Validate project using testql scenarios.
- `check_testql_available()` — Check if testql CLI is available.
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
- `tune(project_dir, aggressive, conservative, dry_run)` — Run `pyqual tune` to auto-adjust quality gate thresholds.
- `ast_max_nesting_depth(node)` — Oblicz max glębokość zagnieżdżenia pętli/warunków — nie wchodzi w zagnieżdżone def/class.
- `ast_cyclomatic_complexity(node)` — Oblicz CC dla funkcji — nie wchodzi w zagnieżdżone definicje funkcji/klas.
- `is_available()` — Sprawdź czy regix jest zainstalowane i działa poprawnie.
- `snapshot(project_dir, ref, timeout)` — Zrób snapshot metryk projektu przez regix.
- `compare(project_dir, before_ref, after_ref)` — Porównaj metryki między dwoma git refs przez regix.
- `compare_snapshots(project_dir, before, after)` — Porównaj dwa snapshoty (obiekty z `snapshot()`).
- `check_gates(project_dir)` — Sprawdź quality gates z regix.yaml (lub domyślne progi).
- `rollback_working_tree(project_dir)` — Cofnij niezatwierdzone zmiany w working tree przez `git checkout -- .`.
- `validate_no_regression(project_dir, rollback_on_failure)` — Porównaj HEAD~1 → HEAD i sprawdź czy nie ma regresji metryk.
- `validate_working_tree(project_dir, before_snapshot, rollback_on_failure)` — Porównaj snapshot 'przed' ze stanem working tree (po zmianach, przed commitem).
- `get_changed_files(project_dir, since)` — Pobierz listę zmienionych plików .py od podanego commita/ref.
- `get_staged_files(project_dir)` — Pobierz listę staged plików .py (git diff --cached).
- `analyze_with_sumd(project_dir)` — Analyze project using sumd if available, fallback to native analyzer.
- `is_available()` — Sprawdź czy redup jest zainstalowane i dostępne w PATH.
- `scan_duplicates(project_dir, min_lines, min_similarity)` — Uruchom redup i zwróć listę grup duplikatów.
- `scan_as_toon(project_dir, min_lines, min_similarity)` — Uruchom redup w formacie toon i zwróć zawartość jako string.
- `enrich_analysis(analysis, project_dir)` — Wzbogać istniejący AnalysisResult o dane z redup.
- `get_refactor_suggestions(project_dir)` — Pobierz sugestie refaktoryzacji duplikatów z redup.
- `is_available()` — Sprawdź czy code2llm jest zainstalowane i dostępne w PATH.
- `generate_toon_files(project_dir, output_dir, timeout)` — Uruchom code2llm na projekcie i zwróć katalog z wygenerowanymi plikami toon.
- `read_toon_contents(toon_dir)` — Wczytaj pliki toon z katalogu wyjściowego code2llm.
- `analyze_with_code2llm(project_dir, analyzer, output_dir, timeout)` — Pełna ścieżka percepcji z code2llm:
- `maybe_analyze(project_dir, analyzer, output_dir)` — Spróbuj analizy przez code2llm; zwróć None jeśli niezainstalowane.
- `handle_push_webhook(payload)` — Process a GitHub push webhook payload.
- `create_app()` — Tworzenie aplikacji FastAPI.
- `is_radon_available()` — Sprawdź czy radon jest zainstalowany i dostępny.
- `run_radon_cc(project_dir, excludes)` — Uruchom `radon cc -j` i zwróć sparsowane wyniki.
- `extract_max_cc_per_file(radon_results, project_dir)` — Ekstraktuj maksymalne CC per plik z wyników radon.
- `enhance_metrics_with_radon(metrics, project_dir)` — Uzupełnij metryki o dokładne CC z radon (jeśli dostępne).
- `detect_deploy_config(project_dir)` — Auto-detect push/publish mechanisms for *project_dir*.
- `run_deploy_action(action, project_dir, dry_run)` — Execute a single deploy action. Returns True on success.
- `cmd_analyze(project_dir)` — Analiza projektu — wyświetl metryki i alerty.
- `cmd_explain(project_dir)` — Wyjaśnij decyzje refaktoryzacji bez ich wykonywania.
- `cmd_refactor(project_dir, dry_run, auto, max_actions)` — Uruchom cykl refaktoryzacji.
- `cmd_memory_stats()` — Statystyki pamięci agenta.
- `cmd_serve(port, host)` — Uruchom serwer API.
- `main()` — Główny punkt wejścia CLI.
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
📄 `redsl.analyzers.parsers.duplication_parser` (5 functions, 1 classes)
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
📄 `redsl.cli.models` (14 functions)
📄 `redsl.cli.planfile` (27 functions)
📄 `redsl.cli.pyqual` (4 functions)
📄 `redsl.cli.refactor` (14 functions)
📄 `redsl.cli.scan` (2 functions)
📄 `redsl.cli.utils` (2 functions)
📄 `redsl.cli.workflow` (5 functions)
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
📦 `redsl.commands.autonomy_pr` (11 functions)
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
📄 `redsl.commands.github_source` (9 functions)
📄 `redsl.commands.hybrid` (14 functions)
📄 `redsl.commands.multi_project` (10 functions, 3 classes)
📄 `redsl.commands.plan_sync` (16 functions, 2 classes)
📄 `redsl.commands.planfile_bridge` (7 functions)
📦 `redsl.commands.pyqual` (13 functions, 1 classes)
📄 `redsl.commands.pyqual.ast_analyzer` (2 functions, 1 classes)
📄 `redsl.commands.pyqual.bandit_analyzer` (1 functions, 1 classes)
📄 `redsl.commands.pyqual.fix_decisions` (5 functions)
📄 `redsl.commands.pyqual.mypy_analyzer` (2 functions, 1 classes)
📄 `redsl.commands.pyqual.reporter` (5 functions, 1 classes)
📄 `redsl.commands.pyqual.ruff_analyzer` (1 functions, 1 classes)
📄 `redsl.commands.scan` (13 functions, 4 classes)
📦 `redsl.commands.sumr_planfile` (5 functions)
📄 `redsl.commands.sumr_planfile.core` (5 functions)
📄 `redsl.commands.sumr_planfile.extractors` (15 functions)
📄 `redsl.commands.sumr_planfile.models` (1 functions, 3 classes)
📄 `redsl.commands.sumr_planfile.parsers` (3 functions)
📄 `redsl.commands.sumr_planfile.utils` (4 functions)
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
📦 `redsl.defaults`
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
📄 `redsl.execution.backup_manager` (7 functions)
📄 `redsl.execution.cycle` (17 functions)
📄 `redsl.execution.decision` (9 functions)
📄 `redsl.execution.deploy_detector` (10 functions, 2 classes)
📄 `redsl.execution.executor`
📄 `redsl.execution.planfile_updater` (14 functions)
📄 `redsl.execution.project_scanner` (7 functions, 1 classes)
📄 `redsl.execution.reflector` (2 functions)
📄 `redsl.execution.reporter` (4 functions)
📄 `redsl.execution.resolution` (6 functions)
📄 `redsl.execution.sandbox_execution` (1 functions)
📄 `redsl.execution.validation` (2 functions)
📄 `redsl.execution.workflow` (11 functions, 12 classes)
📦 `redsl.formatters`
📄 `redsl.formatters.batch` (12 functions)
📄 `redsl.formatters.core` (1 functions)
📄 `redsl.formatters.cycle` (18 functions)
📄 `redsl.formatters.debug` (1 functions)
📄 `redsl.formatters.refactor` (9 functions)
📄 `redsl.history` (16 functions, 3 classes)
📦 `redsl.integrations`
📄 `redsl.integrations.webhook` (3 functions)
📦 `redsl.llm` (14 functions, 2 classes)
📄 `redsl.llm.gate` (7 functions, 2 classes)
📄 `redsl.llm.llx_router` (15 functions, 1 classes)
📦 `redsl.llm.registry`
📄 `redsl.llm.registry.aggregator` (16 functions, 1 classes)
📄 `redsl.llm.registry.models` (7 classes)
📦 `redsl.llm.registry.sources`
📄 `redsl.llm.registry.sources.base` (13 functions, 6 classes)
📦 `redsl.llm.selection`
📄 `redsl.llm.selection.checks` (9 functions)
📄 `redsl.llm.selection.config` (7 functions)
📄 `redsl.llm.selection.metrics` (2 functions)
📄 `redsl.llm.selection.models` (1 functions, 4 classes)
📄 `redsl.llm.selection.ops` (1 functions)
📄 `redsl.llm.selection.selector` (9 functions, 1 classes)
📄 `redsl.llm.selection.strategy` (3 functions, 1 classes)
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
📄 `redsl.validation.pyqual_bridge` (13 functions)
📄 `redsl.validation.regix_bridge` (8 functions, 1 classes)
📄 `redsl.validation.sandbox` (9 functions, 3 classes)
📄 `redsl.validation.testql_bridge` (10 functions, 2 classes)
📄 `redsl.validation.vallm_bridge` (7 functions, 1 classes)
📄 `test_refactor_bad.complex_code` (17 functions, 1 classes)
📄 `test_refactor_project.bad_code` (2 functions, 1 classes)
📄 `www.admin.auth` (1 functions)
📄 `www.admin.clients`
📄 `www.admin.contracts`
📄 `www.admin.index`
📄 `www.admin.invoices`
📄 `www.admin.logs` (3 functions)
📄 `www.admin.projects`
📄 `www.admin.scans`
📄 `www.admin.tickets`
📄 `www.app` (14 functions)
📄 `www.blog.index`
📄 `www.config-api` (3 functions)
📄 `www.config-editor` (4 functions)
📄 `www.cron.invoice-generator`
📄 `www.cron.scan-worker`
📄 `www.email-notifications` (4 functions)
📄 `www.index` (7 functions)
📄 `www.install-plesk`
📄 `www.klient.index` (1 functions)
📄 `www.mock-github.access_token`
📄 `www.mock-github.authorize`
📄 `www.mock-github.user`
📄 `www.nda-form` (3 functions)
📄 `www.nda-wzor`
📄 `www.polityka-prywatnosci`
📄 `www.project`
📄 `www.propozycje` (2 functions)
📄 `www.regulamin`
📄 `www.smoke-test` (8 functions)
📄 `www.test-plesk` (3 functions)

## Requirements

- Python >= >=3.11
- fastapi >=0.115.0- uvicorn >=0.44.0- pydantic >=2.10.0- litellm >=1.52.0- chromadb >=0.6.0- pyyaml >=6.0.2- rich >=13.9.0- httpx >=0.28.0- click >=8.1.7- python-dotenv >=1.0.1- goal >=2.1.0- costs >=0.1.20- pfix >=0.1.60

## Contributing

**Contributors:**
- Tom Sapletta

We welcome contributions! Open an issue or pull request to get started.
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

- 💡 [Examples](./examples) — Usage examples and code samples

### Generated Files

| Output | Description | Link |
|--------|-------------|------|
| `README.md` | Project overview (this file) | — |
| `examples` | Usage examples and code samples | [View](./examples) |

<!-- code2docs:end -->