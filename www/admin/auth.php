<?php
declare(strict_types=1);

/**
 * REDSL Panel — Admin Authentication Gate
 * 
 * Include this at the top of every admin page:
 *   require __DIR__ . '/auth.php';
 * 
 * Configured via environment variables:
 *   ADMIN_USER=admin
 *   ADMIN_PASS_HASH=$2y$10$... (bcrypt)
 */

// Load environment
$envPath = __DIR__ . '/../.env';
if (file_exists($envPath)) {
    foreach (file($envPath, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
        if (str_starts_with($line, '#') || !str_contains($line, '=')) continue;
        putenv($line);
    }
}

$adminUser = getenv('ADMIN_USER') ?: 'admin';
$adminPassHash = getenv('ADMIN_PASS_HASH') ?: '';

// If no password hash configured, show setup instructions
if (empty($adminPassHash)) {
    http_response_code(500);
    echo '<h1>Admin Not Configured</h1>';
    echo '<p>Set ADMIN_USER and ADMIN_PASS_HASH in .env</p>';
    echo '<p>Generate hash: <code>php -r "echo password_hash(\'yourpassword\', PASSWORD_BCRYPT);"</code></p>';
    exit(1);
}

// HTTP Basic Authentication
$providedUser = $_SERVER['PHP_AUTH_USER'] ?? '';
$providedPass = $_SERVER['PHP_AUTH_PW'] ?? '';

$authenticated = false;
if ($providedUser === $adminUser && password_verify($providedPass, $adminPassHash)) {
    $authenticated = true;
}

if (!$authenticated) {
    header('WWW-Authenticate: Basic realm="REDSL Panel"');
    header('HTTP/1.0 401 Unauthorized');
    echo '<h1>401 Unauthorized</h1>';
    echo '<p>Access denied. Please provide valid credentials.</p>';
    exit(0);
}

// Start session for CSRF protection
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

// Generate CSRF token if not exists
if (empty($_SESSION['csrf_token'])) {
    $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
}

// CSRF validation helper
function validateCsrfToken(): void {
    $token = $_POST['csrf_token'] ?? $_SERVER['HTTP_X_CSRF_TOKEN'] ?? '';
    if (!hash_equals($_SESSION['csrf_token'] ?? '', $token)) {
        http_response_code(403);
        echo '<h1>403 Forbidden</h1><p>Invalid CSRF token</p>';
        exit(1);
    }
}

// Safe to proceed - admin is authenticated
