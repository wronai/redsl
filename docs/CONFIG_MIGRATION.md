# Migration Guide: Environment Variables → Config Standard

This guide helps you migrate from legacy environment-variable-based configuration to the new YAML-based config standard.

## Step 1: Analyze Current Configuration

List your current environment variables:

```bash
env | grep -E "^(REFACTOR_|OPENROUTER_|ANTHROPIC_|OPENAI_|XAI_)" | sort
```

Common variables to migrate:
- `OPENROUTER_API_KEY` → `secrets.openrouter_api_key.ref`
- `REFACTOR_DRY_RUN` → `spec.coding.*` (behavior change, see below)
- `REFACTOR_MAX_ITERATIONS` → Not yet in substrate (will use default)
- `LLM_MODEL` → `spec.llm_policy.mode` + provider key resolution

## Step 2: Initialize Config Directory

```bash
cd your-project
redsl config init --name $(basename $(pwd)) --profile production
```

## Step 3: Map Environment to YAML

### API Keys (Secrets)

**Before:**
```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

**After:**
```yaml
# redsl-config/redsl.config.yaml
secrets:
  openrouter_api_key:
    ref: env:OPENROUTER_API_KEY  # Keep using env var
    required: true
  anthropic_api_key:
    ref: env:ANTHROPIC_API_KEY
    required: false
```

Or move to files:
```yaml
secrets:
  openrouter_api_key:
    ref: file:~/.secrets/openrouter.key
    required: true
```

### Model Selection

**Before:**
```bash
export LLM_MODEL="anthropic/claude-sonnet-4-20250514"
export REFLECTION_LLM_MODEL="openrouter/x-ai/grok-code-fast-1"
```

**After:**
```yaml
spec:
  llm_policy:
    mode: frontier_lag  # or "frontier_only", "bounded"
    max_age_days: 180
```

The actual model is selected automatically based on available API keys and policy mode.

### Cost Control

**Before:**
```bash
export REFACTOR_DRY_RUN="true"
```

**After:**
```yaml
spec:
  coding:
    max_cost_per_call_usd: 0.10  # Kill switch per LLM call
    tiers:
      cheap: 0.50      # USD per 1M tokens
      balanced: 3.00
      premium: 15.00
    default_tiers:
      extract_function: cheap
      split_module: balanced
      architecture_review: premium
```

The `max_cost_per_call_usd` acts like a more precise dry-run — it allows the operation but fails if it would exceed the cost limit.

## Step 4: Validate and Test

```bash
# Validate syntax
redsl config validate

# Show effective config (secrets redacted)
redsl config show

# Test with dry-run refactor
redsl refactor --help  # Uses new config automatically
```

## Step 5: Gradual Migration

You don't need to migrate everything at once. The system supports **hybrid mode**:

1. Keep environment variables for now
2. Create `redsl-config/` directory
3. Config standard takes precedence where defined
4. Missing values fall back to environment variables

## Step 6: Clean Up Environment (Optional)

Once fully migrated, you can remove redundant env vars:

```bash
# These are now controlled by YAML
unset REFACTOR_DRY_RUN
unset REFACTOR_AUTO_APPROVE

# Keep these (referenced by YAML secrets.*.ref)
# export OPENROUTER_API_KEY="..."
```

## Common Migration Patterns

### Pattern A: Team Shared Config + Personal Secrets

```yaml
# redsl-config/redsl.config.yaml (committed to git)
spec:
  llm_policy:
    mode: frontier_lag
  coding:
    max_cost_per_call_usd: 0.10
secrets:
  openrouter_api_key:
    ref: env:OPENROUTER_API_KEY
    required: true
```

```bash
# ~/.bashrc (personal, not committed)
export OPENROUTER_API_KEY="sk-or-v1-..."
```

### Pattern B: Fully Local Files (No Env Vars)

```yaml
# redsl-config/redsl.config.yaml
secrets:
  openrouter_api_key:
    ref: file:secrets/openrouter.key
    required: true
```

```bash
# One-time setup
echo "sk-or-v1-..." > redsl-config/secrets/openrouter.key
chmod 600 redsl-config/secrets/openrouter.key
```

### Pattern C: Vault Integration

```yaml
secrets:
  openrouter_api_key:
    ref: vault:secret/data/redsl#openrouter_api_key
    required: true
    rotation:
      rotate_every_days: 90
```

```bash
export VAULT_ADDR="https://vault.company.com"
export VAULT_TOKEN="hvs.CAESQ..."
```

## Verification Checklist

- [ ] `redsl config validate` passes
- [ ] `redsl config show` displays expected values
- [ ] Test command uses correct model: `redsl scan --dry-run`
- [ ] Secrets don't appear in output: `redsl config show | grep -i secret` returns nothing
- [ ] Audit log works: `redsl config history` shows entries

## Rollback

If something goes wrong, simply delete or rename the config directory:

```bash
mv redsl-config redsl-config.backup
# Falls back to pure environment-based configuration
```

## Troubleshooting

### "AgentConfig not loading from substrate"

Check that `redsl-config/redsl.config.yaml` exists and is valid YAML:

```bash
redsl config validate --strict
```

### "Secret not found"

Verify the reference format:
```bash
# Should match exactly
redsl config show | grep -A2 "openrouter_api_key"
env | grep OPENROUTER_API_KEY
```

### "Model not selected correctly"

Check provider key priority in `agent_bridge.py`:
1. OpenRouter key → uses OpenRouter models
2. Anthropic key → uses Claude models
3. OpenAI key → uses Kimi-K2.5 models (via OpenRouter)

## Need Help?

- Open an issue with `redsl config show --format json` output (secrets are automatically redacted)
- Check `history/changes.jsonl` for recent changes
- Run with `DEBUG=1` for detailed logs
