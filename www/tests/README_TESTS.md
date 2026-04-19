# GUI Tests for ReDSL Web Interface

## Test Structure

```
www/tests/
├── ConfigEditorTest.php          # PHPUnit: Config editor backend
├── ProposalSelectionTest.php   # PHPUnit: Proposal parser logic
├── NdaFormTest.php              # PHPUnit: NDA form validation
├── ConfigApiTest.php            # PHPUnit: API endpoints
├── e2e/
│   ├── playwright.config.js     # Playwright configuration
│   ├── config-editor.spec.js    # E2E: Config editor
│   ├── proposals.spec.js        # E2E: Proposal selection
│   └── nda-form.spec.js         # E2E: NDA form
└── README_TESTS.md              # This file
```

## PHPUnit Tests (Backend Logic)

### Installation

```bash
cd www
composer install
```

### Run All Tests

```bash
composer test
# or
./vendor/bin/phpunit tests/
```

### Run GUI-specific Tests

```bash
composer test:gui
# or
./vendor/bin/phpunit tests/ --filter 'ConfigEditor|ProposalSelection|NdaForm|ConfigApi'
```

### Run Individual Test Classes

```bash
./vendor/bin/phpunit tests/ConfigEditorTest.php
./vendor/bin/phpunit tests/ProposalSelectionTest.php
./vendor/bin/phpunit tests/NdaFormTest.php
./vendor/bin/phpunit tests/ConfigApiTest.php
```

### Test Coverage

**ConfigEditorTest.php** (7 tests)
- ✅ Config editor returns valid HTML
- ✅ Config initialization creates default config
- ✅ Secret redaction in display
- ✅ Risk level colors defined
- ✅ YAML validation
- ✅ Backup creation on save

**ProposalSelectionTest.php** (9 tests)
- ✅ Proposal list rendering
- ✅ Selection parser - single items
- ✅ Selection parser - ranges
- ✅ Selection parser - mixed format
- ✅ Selection parser - empty
- ✅ Price calculation
- ✅ Effort labels
- ✅ Form submission
- ✅ "All" and "under 15" selections

**NdaFormTest.php** (9 tests)
- ✅ NIP validation - valid format
- ✅ NIP validation - invalid format
- ✅ NIP cleaning (spaces, dashes)
- ✅ Company data fetching (mock)
- ✅ NDA text generation
- ✅ Form data validation
- ✅ Session data storage
- ✅ Step progression logic
- ✅ HTML sanitization

**ConfigApiTest.php** (9 tests)
- ✅ Config validation - valid config
- ✅ Config validation - missing apiVersion
- ✅ Config validation - invalid apiVersion
- ✅ Config validation - invalid secret ref
- ✅ Secret redaction in API response
- ✅ Fingerprint generation
- ✅ History listing
- ✅ Diff calculation
- ✅ JSON response format

## E2E Tests with Playwright

### Installation

```bash
# Install Playwright globally
npm install -g @playwright/test

# Install browser binaries
npx playwright install
```

### Run E2E Tests

```bash
# All E2E tests
composer test:e2e

# Specific browser
npx playwright test --project=chromium

# UI mode (interactive)
composer test:e2e:ui

# Debug mode
composer test:e2e:debug

# Specific test file
npx playwright test e2e/config-editor.spec.js
```

### E2E Test Coverage

**config-editor.spec.js**
- Display config editor page
- Show "No configuration" when config does not exist
- Create default config on button click
- Display risk levels in sidebar
- Redact secrets in display
- Allow editing and saving config
- Show common paths in sidebar
- Validate YAML syntax on save
- Display config info in sidebar
- Mobile responsiveness

**proposals.spec.js**
- Display proposal selection page
- Display proposal list
- Allow selecting "all" option
- Allow selecting "custom" option
- Display effort labels
- Display price for each proposal
- Show instructions
- Submit form with selection
- Parse single numbers correctly
- Parse ranges correctly
- Parse mixed format correctly
- Mobile responsiveness

**nda-form.spec.js**
- Display NDA form page
- Show step indicators
- Start at step 1
- Accept valid NIP
- Clean NIP from spaces and dashes
- Proceed to step 2 with demo NIP
- Show company data prefilled
- Require all fields in step 2
- Proceed to step 3 after filling form
- Show generated NDA text
- Have download button
- Have upload zone
- Validate email format
- Mobile responsiveness

### Environment Variables

```bash
# Custom base URL
BASE_URL=http://localhost:3000 npx playwright test

# CI mode (no UI, headless)
CI=true npx playwright test
```

## Quick Test Commands Summary

| Command | Purpose |
|---------|---------|
| `composer test` | Run all PHPUnit tests |
| `composer test:gui` | Run GUI-specific PHPUnit tests |
| `composer test:e2e` | Run all Playwright E2E tests |
| `composer test:e2e:ui` | Run E2E tests in UI mode |
| `composer test:e2e:debug` | Run E2E tests in debug mode |
| `npx playwright test --ui` | Interactive test runner |

## Adding New Tests

### PHPUnit Test

```php
<?php
use PHPUnit\Framework\TestCase;

class MyNewTest extends TestCase
{
    public function testSomething(): void
    {
        $this->assertTrue(true);
    }
}
```

### Playwright E2E Test

```javascript
const { test, expect } = require('@playwright/test');

test('should do something', async ({ page }) => {
  await page.goto('/my-page.php');
  await expect(page.locator('h1')).toContainText('My Page');
});
```

## CI/CD Integration

```yaml
# .github/workflows/gui-tests.yml
name: GUI Tests

on: [push, pull_request]

jobs:
  phpunit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: php-actions/composer@v6
        with:
          working_dir: www
      - run: cd www && ./vendor/bin/phpunit tests/

  playwright:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: cd www/tests/e2e && npx playwright install
      - run: cd www/tests/e2e && npx playwright test
```

## Troubleshooting

### PHP Extension: yaml

If tests fail with "yaml_parse() not found":
```bash
# Ubuntu/Debian
sudo apt-get install php-yaml

# Or use PECL
pecl install yaml
```

### Playwright: Missing browsers

```bash
npx playwright install
```

### Port conflicts

If port 8080 is in use, change in `playwright.config.js`:
```javascript
webServer: {
  command: 'php -S localhost:8081 -t ..',
  port: 8081,
}
```

## Test Status

| Test Suite | Status | Count |
|------------|--------|-------|
| PHPUnit (GUI) | ✅ Ready | 34 tests |
| Playwright E2E | ✅ Ready | 40+ tests |
| Total | ✅ Ready | 74+ tests |
