# Config Standard — Secure YAML-Based Configuration

The `redsl` config standard provides a secure, auditable, and NLP-friendly way to manage configuration using YAML manifests with externalized secrets.

## Quick Start

### 1. Initialize a New Configuration

```bash
cd your-project
redsl config init --name my-project --profile production
```

This creates a `redsl-config/` directory with:
- `redsl.config.yaml` — main configuration manifest
- `secrets/` — directory for secret files (gitignored)
- `history/` — audit log of all changes

### 2. Configure Secrets (Safely)

Edit `redsl-config/redsl.config.yaml`:

```yaml
apiVersion: redsl.config/v1
kind: RedslConfig
metadata:
  name: my-project
  version: 1
spec:
  llm_policy:
    mode: frontier_lag
    max_age_days: 180
  coding:
    max_cost_per_call_usd: 0.10
secrets:
  openrouter_api_key:
    ref: env:OPENROUTER_API_KEY
    required: true
  anthropic_api_key:
    ref: env:ANTHROPIC_API_KEY
    required: false
```

**Never put secret values in YAML** — only references (`env:`, `file:`, `vault:`, `doppler:`).

### 3. Validate and Apply

```bash
# Validate syntax and schema
redsl config validate

# Show current effective configuration
redsl config show

# View change history
redsl config history
```

## Migration from Environment Variables

### Before (Legacy)

```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
export REFACTOR_DRY_RUN="true"
export REFACTOR_MAX_ITERATIONS="3"
```

### After (Config Standard)

```yaml
# redsl-config/redsl.config.yaml
apiVersion: redsl.config/v1
kind: RedslConfig
metadata:
  name: my-project
spec:
  llm_policy:
    mode: frontier_lag
  coding:
    max_cost_per_call_usd: 0.10
    default_tiers:
      extract_function: cheap
      architecture_review: premium
secrets:
  openrouter_api_key:
    ref: env:OPENROUTER_API_KEY
    required: true
```

**Backward compatibility:** `AgentConfig.from_env()` automatically detects `redsl-config/` and uses it, falling back to pure env-based loading if not found.

## Secret Resolution

### Supported Providers

| Prefix | Format | Example |
|--------|--------|---------|
| `env:` | Environment variable | `env:OPENROUTER_API_KEY` |
| `file:` | File path | `file:~/.secrets/openrouter.key` |
| `vault:` | HashiCorp Vault | `vault:secret/data/myapp#api_key` |
| `doppler:` | Doppler | `doppler:myproject/production/OPENROUTER_API_KEY` |

### Environment Variable Fallback

For `vault:` and `doppler:`, if the SDK/API is unavailable, the system checks for fallback env vars:

- Vault: `VAULT_SECRET_<KEY>`
- Doppler: The secret name directly (Doppler CLI injects these)

## Risk Levels and Safety

Every config path has an assigned risk level:

| Path | Risk | Requires Confirmation |
|------|------|---------------------|
| `spec.llm_policy.max_age_days` | low | No |
| `spec.coding.max_cost_per_call_usd` | medium | No |
| `spec.secrets.*` | critical | **Yes** |
| `profile` | high | **Yes** |

### NLP Agent Integration

The config standard exposes tools for LLM agents:

```python
from redsl.config_standard import dispatch_tool, ConfigStore

store = ConfigStore("./redsl-config")

# Inspect current value
result = dispatch_tool("inspect_config", {"path": "spec.coding.max_cost_per_call_usd"}, store=store)
# → {"path": "...", "value": 0.10, "risk_level": "medium"}

# Search schema
result = dispatch_tool("search_config_schema", {"query": "model age limit"})
# → {"matches": [{"path": "spec.llm_policy.max_age_days", ...}]}

# Propose changes (returns proposal, does NOT apply)
result = dispatch_tool("propose_changes", {
    "changes": [{"op": "set", "path": "spec.coding.max_cost_per_call_usd", "new_value": 0.05}],
    "summary": "Reduce cost limit"
}, store=store)
# → {"proposal": {...}, "aggregate_risk": "low", "requires_confirmation": false}
```

## CLI Reference

### `redsl config init`

Create a new configuration directory.

```bash
redsl config init [--name NAME] [--profile production|development|minimal-cost]
```

### `redsl config validate`

Validate manifest against JSON Schema.

```bash
redsl config validate [--strict]
```

### `redsl config show`

Display effective configuration (with secrets redacted).

```bash
redsl config show [--profile NAME]
```

### `redsl config diff`

Compare current config with a proposal or another profile.

```bash
redsl config diff --proposal proposal.yaml
redsl config diff --compare-profile development
```

### `redsl config apply`

Apply a change proposal (requires confirmation for high/critical risk).

```bash
redsl config apply proposal.yaml [--yes]
```

### `redsl config history`

Show audit log of all changes.

```bash
redsl config history [--limit 10]
```

### `redsl config clone`

Copy configuration to another directory.

```bash
redsl config clone /path/to/target
```

## Programmatic API

```python
from redsl.config_standard import (
    ConfigStore,
    ConfigApplier,
    build_default_config,
    agent_config_from_substrate_or_env,
)

# Load/store configuration
store = ConfigStore("./redsl-config")
doc = store.load()

# Modify and save
doc.spec.coding.max_cost_per_call_usd = 0.05
doc.metadata.version += 1
store.save(doc)

# Apply change proposal
applier = ConfigApplier(store)
result = applier.apply(proposal, confirmed=True)

# Bridge to legacy AgentConfig
agent_config = agent_config_from_substrate_or_env()
```

## Security Best Practices

1. **Never commit secrets** — The `secrets/` directory is automatically gitignored
2. **Use least-privilege** — Mark secrets as `required: false` if optional
3. **Rotate regularly** — Set `rotation.rotate_every_days` on secret specs
4. **Audit everything** — All changes are logged to `history/changes.jsonl`
5. **Redaction by default** — Secrets never appear in logs, API responses, or LLM contexts

## Troubleshooting

### "No config root found"

Run `redsl config init` or ensure you're in a directory containing `redsl-config/redsl.config.yaml`.

### "Cannot resolve secret ref"

Check that:
- Environment variable is set (for `env:` refs)
- File exists and is readable (for `file:` refs)
- `VAULT_ADDR` and `VAULT_TOKEN` are set (for `vault:` refs)
- `DOPPLER_TOKEN` is set (for `doppler:` refs)

### Schema validation errors

Use `redsl config validate` to get detailed error messages. Common issues:
- Missing required fields (`metadata.name`, `apiVersion`)
- Invalid enum values (e.g., `mode` must be `frontier_lag`, `frontier_only`, or `bounded`)
- Secret refs with unsupported prefixes

## Advanced Topics

### Profiles

Create environment-specific profiles:

```bash
redsl config init --profile development
# Edit redsl-config/profiles/development.yaml
```

Switch profile:
```bash
redsl config show --profile development
```

### Custom Secret Providers

Extend `agent_bridge.resolve_secret_ref()` to add custom providers:

```python
if ref.startswith("aws:"):
    return _resolve_aws_secrets_manager(ref, secret)
```

### JSON Schema Export

```python
from redsl.config_standard import export_config_schema
schema = export_config_schema()
# Use for IDE autocomplete, validation, or documentation
```

## Web UI Editor

Dla wygody dostępny jest webowy edytor konfiguracji pod adresem `/config-editor.php` (jeśli wdrożony web interface):

### Funkcje edytora

- **Visual YAML Editor** — edycja z podświetlaniem składni
- **Secret Redaction** — sekrety są zredagowane (pokazuje tylko referencje, nie wartości)
- **Auto-backup** — tworzy backup przy każdym zapisie
- **Risk Level Indicators** — pokazuje które zmiany wymagają potwierdzenia
- **Validation** — walidacja struktury i schematu YAML
- **Quick Init** — tworzenie domyślnej konfiguracji jednym kliknięciem

### API Endpoints

```
GET /config-api.php?path=validate   — walidacja konfiguracji
GET /config-api.php?path=show        — pobranie konfiguracji (z redakcją sekretów)
GET /config-api.php?path=history     — lista historii zmian
POST /config-api.php?path=diff       — porównanie z proposal
```

### Przykład użycia API

```bash
# Walidacja
curl http://localhost:8080/config-api.php?path=validate

# Historia zmian
curl http://localhost:8080/config-api.php?path=history
```

Szczegóły w [`www/README_CONFIG.md`](./www/README_CONFIG.md).
