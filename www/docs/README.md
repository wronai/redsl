<!-- code2docs:start --># www

![version](https://img.shields.io/badge/version-0.1.0-blue) ![php](https://img.shields.io/badge/php-any-777BB4) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey) ![functions](https://img.shields.io/badge/functions-37-green)
> **37** functions | **0** classes | **12** files | CC̄ = 3.9

> Auto-generated project documentation from source code analysis.

**Author:** ReDSL Team  
**License:** Apache-2.0  


## Installation

### Requirements

- PHP 8.0+
- [Composer](https://getcomposer.org/)

### From Source

```bash
git clone <repository-url>
cd www
composer install
```

## Quick Start

Serve the project with your preferred PHP runtime (built-in server shown for local development):

```bash
php -S localhost:8000
```

Or with Docker Compose if a `docker-compose.yml` is provided:

```bash
docker compose up
```




## Architecture

```
www/
├── nda-wzor
├── email-notifications
├── propozycje
├── polityka-prywatnosci
├── config-editor
├── nda-form
├── regulamin
├── config-api
├── project
    ├── index
├── index
├── app
```

## API Overview

### Functions

- `generateProposalEmail()` — —
- `sendProposalEmail()` — —
- `generateAccessToken()` — —
- `verifyAccessToken()` — —
- `parseSelection()` — —
- `h()` — —
- `loadConfig()` — —
- `saveConfig()` — —
- `getNestedValue()` — —
- `getRiskLevel()` — —
- `fetchCompanyData()` — —
- `h()` — —
- `generateNDAText()` — —
- `validateConfig()` — —
- `getHistory()` — —
- `redactSecrets()` — —
- `load_env()` — —
- `env()` — —
- `h()` — —
- `csrf_token()` — —
- `check_rate_limit()` — —
- `send_notification()` — —
- `send_notification_smtp()` — —
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


## Project Structure

📄 `app` (14 functions)
📄 `blog.index`
📄 `config-api` (3 functions)
📄 `config-editor` (4 functions)
📄 `email-notifications` (4 functions)
📄 `index` (7 functions)
📄 `nda-form` (3 functions)
📄 `nda-wzor`
📄 `polityka-prywatnosci`
📄 `project`
📄 `propozycje` (2 functions)
📄 `regulamin`

## Requirements

- phpmailer/phpmailer ^6.9

## Contributing

**Contributors:**
- Tom Sapletta

We welcome contributions! Open an issue or pull request to get started.
### Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd www

# Install dependencies
composer install

# Run tests
vendor/bin/phpunit
```


<!-- code2docs:end -->