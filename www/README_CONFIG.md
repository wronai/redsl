# ReDSL Config Web Editor

Web-based editor for managing `redsl-config/redsl.config.yaml` with safety features and secret redaction.

## Files

| File | Purpose |
|------|---------|
| `config-editor.php` | Main editor UI — read/write YAML config |
| `config-api.php` | JSON API — validate, show, history, diff |

## Features

- ✓ **Visual YAML Editor** with syntax highlighting support
- ✓ **Secret Redaction** — never displays secret values (only refs like `env:VAR`)
- ✓ **Risk Level Indicators** — shows which changes require confirmation
- ✓ **Auto-backup** — creates timestamped backups on every save
- ✓ **Validation** — validates YAML structure and schema
- ✓ **Quick Init** — creates default configuration with one click

## Usage

### Docker (Recommended)

```bash
cd www
docker-compose up -d
# Access at http://localhost:8080/config-editor.php
```

### Manual (with PHP 8.2+ and YAML extension)

```bash
# Install YAML extension
sudo apt-get install php-yaml

# Start PHP server
cd www
php -S localhost:8080

# Access at http://localhost:8080/config-editor.php
```

## API Endpoints

All endpoints return JSON:

### GET /config-api.php?path=validate

Validate current configuration:
```bash
curl http://localhost:8080/config-api.php?path=validate
```

Response:
```json
{
  "valid": true,
  "errors": [],
  "config": { /* redacted secrets */ }
}
```

### GET /config-api.php?path=show

Show current configuration with fingerprint:
```bash
curl http://localhost:8080/config-api.php?path=show
```

### GET /config-api.php?path=history

List backup history:
```bash
curl http://localhost:8080/config-api.php?path=history
```

### POST /config-api.php?path=diff

Compare current config with proposal:
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"proposal": {"changes": [{"path": "spec.llm_policy.mode", "new_value": "bounded"}]}}' \
  http://localhost:8080/config-api.php?path=diff
```

## Security

- Secrets are **redacted** in all API responses
- Backups are stored in `redsl-config/history/`
- `.env` files are blocked via Apache config
- No authentication (add your own if exposing publicly)

## Risk Levels

| Level | Color | Requires Confirmation |
|-------|-------|---------------------|
| Low | Green | No |
| Medium | Yellow | No |
| High | Orange | Yes |
| Critical | Red | Yes |

Critical paths include `secrets.*` and `apiVersion`.

## Integration with CLI

The web editor works with the same config files as the CLI:

```bash
# CLI creates config
redsl config init --name my-project

# Web editor can edit it
curl http://localhost:8080/config-api.php?path=show

# CLI validates
redsl config validate
```

## Screenshots

The editor provides:
- Left pane: YAML text editor
- Right sidebar: Config info, risk levels, common paths
- Top: Action buttons (Save, Reset)
- Warnings: Security notices about secret handling
