<?php
declare(strict_types=1);

/**
 * REDSL Panel — Synchronous Bootstrap Loader with Validation Logging
 *
 * Loads core components in strict order, validates each step,
 * and logs every phase for operational observability.
 */

// ── Phase 0: micro-timer ──
$bootstrapStart = hrtime(true);

// ── Phase 1: environment ──
$envFile = __DIR__ . '/.env';
$envLoaded = false;
if (is_readable($envFile)) {
    foreach (file($envFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
        $line = trim($line);
        if ($line === '' || str_starts_with($line, '#')) continue;
        if (!str_contains($line, '=')) continue;
        [$k, $v] = array_map('trim', explode('=', $line, 2));
        $v = trim($v, "\"'");
        $_ENV[$k] = $v;
    }
    $envLoaded = true;
}

// ── Phase 2: helper functions (needed before Logger) ──
if (!function_exists('env')) {
    function env(string $key, string $default = ''): string {
        return (string)($_ENV[$key] ?? getenv($key) ?: $default);
    }
}

// ── Phase 3: Logger ──
$loggerFile = __DIR__ . '/lib/Logger.php';
$loggerLoaded = false;
if (is_readable($loggerFile)) {
    require_once $loggerFile;
    if (class_exists('Logger', false)) {
        Logger::setLogDir(__DIR__ . '/var/logs');
        Logger::enableDebug(env('APP_DEBUG') === '1' || env('APP_ENV') === 'dev');
        $loggerLoaded = true;
    }
}

// Fallback error_log until Logger is up
function _bootstrap_log(string $phase, string $status, array $ctx = []): void {
    if (class_exists('Logger', false)) {
        Logger::info('bootstrap', "[$phase] $status", $ctx);
    } else {
        error_log("[BOOTSTRAP] [$phase] $status " . json_encode($ctx));
    }
}

_bootstrap_log('env', $envLoaded ? 'loaded' : 'missing', ['file' => $envFile, 'exists' => is_readable($envFile)]);
_bootstrap_log('logger', $loggerLoaded ? 'loaded' : 'missing', ['file' => $loggerFile, 'exists' => is_readable($loggerFile)]);

// ── Phase 4: i18n ──
$i18nFile = __DIR__ . '/lib/i18n.php';
$i18nLoaded = false;
$i18nKeys = [];
if (is_readable($i18nFile)) {
    $i18n = require $i18nFile;
    if (is_array($i18n)) {
        $i18nKeys = array_keys($i18n);
        $requiredKeys = ['t', 'lang', 'getLangUrls', 'getLangName', 'formatPrice', 'getPricing', 'th'];
        $missing = array_diff($requiredKeys, $i18nKeys);
        if (empty($missing)) {
            $i18nLoaded = true;
            // Extract closures into current scope for landing page compatibility
            $t = $i18n['t'];
            $lang = ($i18n['lang'])();
            $getLangUrls = $i18n['getLangUrls'];
            $getLangName = $i18n['getLangName'];
            $formatPrice = $i18n['formatPrice'];
            $getPricing = $i18n['getPricing'];
            $th = $i18n['th'];
        } else {
            _bootstrap_log('i18n', 'invalid_structure', ['missing_keys' => $missing, 'found_keys' => $i18nKeys]);
        }
    } else {
        _bootstrap_log('i18n', 'bad_return_type', ['type' => gettype($i18n)]);
    }
} else {
    _bootstrap_log('i18n', 'file_not_readable', ['file' => $i18nFile]);
}
_bootstrap_log('i18n', $i18nLoaded ? 'loaded' : 'failed', [
    'file' => $i18nFile,
    'keys_found' => $i18nKeys,
    'lang' => is_callable($lang ?? null) ? ($lang)() : 'unknown',
]);

// ── Phase 5: Database (lazy, but log availability) ──
$dbFile = __DIR__ . '/lib/Database.php';
$dbAvailable = is_readable($dbFile);
_bootstrap_log('database', $dbAvailable ? 'available' : 'missing', ['file' => $dbFile]);

// ── Phase 6: Encryption ──
$encFile = __DIR__ . '/lib/Encryption.php';
$encAvailable = is_readable($encFile);
_bootstrap_log('encryption', $encAvailable ? 'available' : 'missing', ['file' => $encFile]);

// ── Phase 7: timing summary ──
$elapsedMs = (hrtime(true) - $bootstrapStart) / 1e6;
_bootstrap_log('bootstrap', 'complete', [
    'elapsed_ms' => round($elapsedMs, 3),
    'env' => $envLoaded,
    'logger' => $loggerLoaded,
    'i18n' => $i18nLoaded,
    'db_available' => $dbAvailable,
    'enc_available' => $encAvailable,
]);

// ── Validation: abort if critical components missing ──
$criticalMissing = [];
if (!$envLoaded) $criticalMissing[] = 'env';
if (!$loggerLoaded) $criticalMissing[] = 'logger';
if (!$i18nLoaded) $criticalMissing[] = 'i18n';

if (!empty($criticalMissing)) {
    _bootstrap_log('bootstrap', 'critical_failure', ['missing' => $criticalMissing]);
    http_response_code(500);
    header('Content-Type: text/plain; charset=utf-8');
    echo "CRITICAL BOOTSTRAP FAILURE\n";
    echo "Missing components: " . implode(', ', $criticalMissing) . "\n";
    echo "Check var/logs/all.log or error_log for details.\n";
    exit(1);
}

// Compatibility: expose helper functions if not already defined
if (!function_exists('h')) {
    function h(string $s): string { return htmlspecialchars($s, ENT_QUOTES | ENT_HTML5, 'UTF-8'); }
}
if (!function_exists('csrf_token')) {
    function csrf_token(): string {
        if (empty($_SESSION['csrf'])) $_SESSION['csrf'] = bin2hex(random_bytes(16));
        return $_SESSION['csrf'];
    }
}
if (!function_exists('check_rate_limit')) {
    function check_rate_limit(): bool {
        $now = time();
        $last = $_SESSION['last_submit'] ?? 0;
        if ($now - (int)$last < 60) return false;
        $_SESSION['last_submit'] = $now;
        return true;
    }
}
