# Config Standard Cheatsheet

## Commands

```bash
# Initialize
redsl config init --name my-project --profile production

# Validate
redsl config validate

# Show (with secrets redacted)
redsl config show
redsl config show --profile development

# History
redsl config history
redsl config history --limit 5

# Diff
redsl config diff --proposal changes.yaml

# Apply
redsl config apply changes.yaml
redsl config apply changes.yaml --yes  # Skip confirmation

# Clone
redsl config clone /path/to/target
```

## Secret References

| Format | Example | Use Case |
|--------|---------|----------|
| `env:` | `env:OPENROUTER_API_KEY` | CI/CD, local dev |
| `file:` | `file:~/.secrets/key` | Local files, Docker secrets |
| `vault:` | `vault:secret/data/app#key` | HashiCorp Vault |
| `doppler:` | `doppler:proj/prod/KEY` | Doppler.com |

## Risk Levels

| Level | Paths | Confirmation |
|-------|-------|--------------|
| `low` | Most `spec.*` settings | No |
| `medium` | `max_cost_per_call_usd`, `registry_sources` | No |
| `high` | `profile` | **Yes** |
| `critical` | `secrets.*`, `apiVersion` | **Yes** |

## Common Config Paths

```yaml
# LLM Policy
spec.llm_policy.mode                    # frontier_lag | frontier_only | bounded
spec.llm_policy.max_age_days            # 180
spec.llm_policy.strict                  # true | false

# Cost Control
spec.coding.max_cost_per_call_usd       # 0.10
spec.coding.cost_weights.input          # 0.8
spec.coding.cost_weights.output         # 0.2

# Tiers
spec.coding.tiers.cheap                 # 0.50
spec.coding.tiers.balanced              # 3.00
spec.coding.tiers.premium               # 15.00

# Operations
spec.coding.default_tiers.extract_function      # cheap | balanced | premium
spec.coding.default_tiers.split_module            # cheap | balanced | premium
spec.coding.default_tiers.architecture_review    # cheap | balanced | premium

# Cache
spec.cache.path                         # /var/cache/redsl/registry.json
spec.cache.ttl_seconds                  # 21600
```

## Environment Variables for Vault/Doppler

```bash
# HashiCorp Vault
export VAULT_ADDR="https://vault.example.com"
export VAULT_TOKEN="hvs.CAESQ..."
export VAULT_SECRET_OPENROUTER_API_KEY="fallback-value"

# Doppler
export DOPPLER_TOKEN="dp.st..."
# Or rely on Doppler CLI injection
```

## Programmatic API

```python
from redsl.config_standard import (
    ConfigStore, ConfigApplier, build_default_config,
    agent_config_from_substrate_or_env, dispatch_tool
)

# Load
store = ConfigStore("./redsl-config")
doc = store.load()

# Modify
doc.spec.coding.max_cost_per_call_usd = 0.05

# Save
store.save(doc)

# Bridge to legacy
agent_cfg = agent_config_from_substrate_or_env()

# NLP tools
result = dispatch_tool("inspect_config", {"path": "spec.coding.max_cost_per_call_usd"}, store=store)
```

## JSON Schema

```python
from redsl.config_standard import export_config_schema, export_proposal_schema

config_schema = export_config_schema()
proposal_schema = export_proposal_schema()
```

## File Structure

```
redsl-config/
├── redsl.config.yaml          # Main manifest
├── secrets/                   # Secret files (gitignored)
│   └── openrouter.key
├── profiles/                  # Profile overrides
│   ├── development.yaml
│   └── minimal-cost.yaml
└── history/
    └── changes.jsonl          # Audit log (append-only)
```

## Safety Features

- ✓ Secrets never appear in `config show`, logs, or API responses
- ✓ High/critical changes require confirmation
- ✓ Atomic apply with rollback on failure
- ✓ Append-only audit log
- ✓ Fingerprinting for optimistic concurrency
- ✓ Schema validation with NLP-friendly aliases

## Web UI (jeśli dostępny)

| Endpoint | Opis |
|----------|------|
| `/config-editor.php` | Edytor YAML z walidacją i backupami |
| `/config-api.php?path=validate` | Walidacja konfiguracji (JSON) |
| `/config-api.php?path=show` | Podgląd konfiguracji (z redakcją sekretów) |
| `/config-api.php?path=history` | Historia zmian (JSON) |

### Quick curl

```bash
# Walidacja
curl http://localhost:8080/config-api.php?path=validate | jq

# Podgląd configu
curl http://localhost:8080/config-api.php?path=show | jq '.config.metadata'
```
