<?php
/**
 * Tests for environment variable configuration and docker-compose consistency.
 *
 * Standalone runner — does NOT require PHPUnit:
 *   php tests/EnvConfigTest.php
 */

// ── helpers ──────────────────────────────────────────────────────

function assertTrue(bool $condition, string $message): void
{
    if (!$condition) {
        throw new AssertionError("FAIL: $message");
    }
}

function assertArrayHasKey(string|int $key, array $array, string $message = ''): void
{
    if (!array_key_exists($key, $array)) {
        throw new AssertionError("FAIL: Key '$key' missing. " . ($message ?: 'Expected key to exist'));
    }
}

function assertIsNumeric(mixed $value, string $message = ''): void
{
    if (!is_numeric($value)) {
        throw new AssertionError("FAIL: Value is not numeric. " . $message);
    }
}

function assertStringContainsString(string $needle, string $haystack, string $message = ''): void
{
    if (!str_contains($haystack, $needle)) {
        throw new AssertionError("FAIL: String does not contain '$needle'. " . $message);
    }
}

function assertGreaterThanOrEqual(int $expected, int $actual, string $message = ''): void
{
    if ($actual < $expected) {
        throw new AssertionError("FAIL: Expected >= $expected, got $actual. " . $message);
    }
}

// ── load .env file ───────────────────────────────────────────────

$envVars = [];
$envPath = __DIR__ . '/../.env';
if (file_exists($envPath)) {
    $content = file_get_contents($envPath);
    preg_match_all('/^(\w+)=(.*)$/m', $content, $matches, PREG_SET_ORDER);
    foreach ($matches as $m) {
        $envVars[$m[1]] = trim($m[2]);
    }
}

// ── load docker-compose.yml ──────────────────────────────────────

$composePath = __DIR__ . '/../docker-compose.yml';
$composeRaw = file_exists($composePath) ? file_get_contents($composePath) : '';

function extractServiceBlock(string $yaml, string $serviceName): string
{
    // A new top-level service starts with exactly 2 spaces + word + colon.
    // Properties inside a service have 4+ spaces, so "  condition:" is NOT a new service.
    preg_match('/\n  ' . preg_quote($serviceName, '/') . ':(.*?)(?=\n  [a-zA-Z_][a-zA-Z0-9_-]*:|\nvolumes:|\z)/s', $yaml, $m);
    return $m[1] ?? '';
}

// ── tests ────────────────────────────────────────────────────────

$pass = 0;
$fail = 0;

function runTest(callable $fn, string $name): void
{
    global $pass, $fail;
    try {
        $fn();
        echo "  ✓ $name\n";
        $pass++;
    } catch (Throwable $e) {
        echo "  ✗ $name\n    → {$e->getMessage()}\n";
        $fail++;
    }
}

echo "EnvConfigTest — standalone runner\n";
echo str_repeat("=", 50) . "\n";

// .env presence
runTest(fn() => assertArrayHasKey('DB_HOST', $envVars, 'DB_HOST must be defined in .env for docker-compose'),
    'DB_HOST is defined in .env');

runTest(fn() => assertArrayHasKey('DB_PORT', $envVars), 'DB_PORT is defined in .env');
runTest(fn() => assertIsNumeric($envVars['DB_PORT'] ?? null, 'DB_PORT must be numeric'), 'DB_PORT is numeric');

runTest(fn() => assertArrayHasKey('DB_NAME', $envVars), 'DB_NAME is defined in .env');
runTest(fn() => assertArrayHasKey('DB_USER', $envVars), 'DB_USER is defined in .env');
runTest(fn() => assertArrayHasKey('DB_PASS', $envVars), 'DB_PASS is defined in .env');

runTest(fn() => assertArrayHasKey('REDSL_API_URL', $envVars,
    'REDSL_API_URL must be defined for /api/redsl.php proxy'), 'REDSL_API_URL is defined in .env');

runTest(fn() => assertArrayHasKey('WORKSPACE_ROOT', $envVars), 'WORKSPACE_ROOT is defined in .env');
runTest(fn() => assertArrayHasKey('ADMIN_USER', $envVars), 'ADMIN_USER is defined in .env');
runTest(fn() => assertArrayHasKey('ADMIN_PASS_HASH', $envVars), 'ADMIN_PASS_HASH is defined in .env');
runTest(fn() => assertArrayHasKey('ENCRYPTION_KEY', $envVars,
    'ENCRYPTION_KEY must be defined (can be empty in dev)'), 'ENCRYPTION_KEY is defined in .env');
runTest(fn() => assertArrayHasKey('INVOICE_PREFIX', $envVars), 'INVOICE_PREFIX is defined in .env');

// docker-compose.yml structure
runTest(fn() => assertStringContainsString('x-env:', $composeRaw, 'docker-compose should define x-env anchor'),
    'docker-compose.yml defines x-env anchor');

runTest(fn() => assertStringContainsString('env_file:', $composeRaw, 'docker-compose should define env_file'),
    'docker-compose.yml defines env_file');

$anchorUses = substr_count($composeRaw, '*default-env');
runTest(fn() => assertGreaterThanOrEqual(3, $anchorUses,
    'x-env anchor should be used in at least 3 services'),
    "x-env anchor used $anchorUses times (>=3)");

// Per-service checks — env_file either inline or via <<: *default-env anchor
foreach (['app', 'db', 'redsl-api'] as $svc) {
    runTest(
        function() use ($composeRaw, $svc) {
            $block = extractServiceBlock($composeRaw, $svc);
            $hasInline = str_contains($block, 'env_file:');
            $hasAnchor = str_contains($block, '*default-env');
            assertTrue($hasInline || $hasAnchor,
                "$svc service must have env_file (inline or via x-env anchor)");
        },
        "$svc service has env_file"
    );
}

runTest(function() use ($composeRaw) {
    $dbSection = extractServiceBlock($composeRaw, 'db');
    assertStringContainsString('${DB_NAME', $dbSection, 'db service should use ${DB_NAME} env var');
    assertStringContainsString('${DB_USER', $dbSection, 'db service should use ${DB_USER} env var');
    assertStringContainsString('${DB_PASS', $dbSection, 'db service should use ${DB_PASS} env var');
}, 'db service uses DB_* env vars');

runTest(function() use ($composeRaw) {
    $appSection = extractServiceBlock($composeRaw, 'app');
    assertStringContainsString('./.env', $appSection, 'app service should mount ./.env');
}, 'app service mounts ./.env');

runTest(function() use ($composeRaw) {
    $apiSection = extractServiceBlock($composeRaw, 'redsl-api');
    assertStringContainsString('8000:8000', $apiSection, 'redsl-api should expose port 8000');
}, 'redsl-api exposes port 8000');

runTest(function() use ($composeRaw) {
    $appSection = extractServiceBlock($composeRaw, 'app');
    assertStringContainsString('depends_on:', $appSection, 'app should have depends_on');
    assertStringContainsString('db:', $appSection, 'app should depend on db');
}, 'app service depends_on db');

// ── summary ───────────────────────────────────────────────────────

echo str_repeat("=", 50) . "\n";
echo "Results: $pass passed, $fail failed\n";

exit($fail > 0 ? 1 : 0);

