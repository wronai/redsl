<?php
declare(strict_types=1);

/**
 * ReDSL API proxy
 *
 * Forwards requests from the www frontend to the redsl-api service.
 * Endpoints:
 *   GET  /api/redsl.php?action=health
 *   GET  /api/redsl.php?action=mcp_health
 *   POST /api/redsl.php?action=scan      body: {"project": "goal"}
 *   POST /api/redsl.php?action=refactor  body: {"project": "goal", "dry_run": true, "max_actions": 5}
 *   POST /api/redsl.php?action=analyze   body: {"project": "goal"}
 *   POST /api/redsl.php?action=mcp_subscription body: {"client_email": "...", "plan": "starter"}
 */

// ── Config ───────────────────────────────────────────────────────
$REDSL_API = getenv('REDSL_API_URL') ?: 'http://redsl-api:8000';
$WORKSPACE = getenv('WORKSPACE_ROOT') ?: '/workspace';
$API_SECRET = getenv('REDSL_API_SECRET') ?: '';
$MCP_API = getenv('MCP_API_URL') ?: '';
$MCP_API_KEY = getenv('MCP_API_KEY') ?: '';

header('Content-Type: application/json; charset=UTF-8');
header('X-Content-Type-Options: nosniff');

// ── Auth (optional shared secret) ────────────────────────────────
if ($API_SECRET !== '') {
    $given = $_SERVER['HTTP_X_REDSL_SECRET'] ?? '';
    if (!hash_equals($API_SECRET, $given)) {
        http_response_code(401);
        echo json_encode(['error' => 'Unauthorized']);
        exit;
    }
}

// ── Helpers ───────────────────────────────────────────────────────
function redsl_curl(string $method, string $url, ?array $body = null, array $headers = []): array {
    $httpHeaders = array_merge(
        ['Content-Type: application/json', 'Accept: application/json'],
        $headers
    );

    $ch = curl_init($url);
    $opts = [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 120,
        CURLOPT_HTTPHEADER     => $httpHeaders,
    ];
    if ($method === 'POST') {
        $opts[CURLOPT_POST]       = true;
        $opts[CURLOPT_POSTFIELDS] = $body !== null ? json_encode($body) : '{}';
    }
    curl_setopt_array($ch, $opts);
    $resp     = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $err      = curl_error($ch);
    curl_close($ch);

    if ($err) {
        return ['ok' => false, 'code' => 0, 'body' => null, 'error' => $err];
    }
    $decoded = json_decode($resp ?: '{}', true);
    return ['ok' => $httpCode >= 200 && $httpCode < 300, 'code' => $httpCode, 'body' => $decoded, 'error' => null];
}

function json_out(int $code, mixed $data): never {
    http_response_code($code);
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

function resolve_project(string $name): string|false {
    global $WORKSPACE;
    $clean = preg_replace('/[^a-zA-Z0-9_\-]/', '', $name);
    if ($clean === '') return false;
    $path = $WORKSPACE . '/' . $clean;
    return $path;
}

function build_mcp_subscription_payload(array $body): array {
    $planPricing = [
        'starter' => 299.0,
        'pro' => 799.0,
        'enterprise' => 1899.0,
    ];

    $email = trim((string)($body['client_email'] ?? ''));
    if ($email === '' || filter_var($email, FILTER_VALIDATE_EMAIL) === false) {
        throw new InvalidArgumentException('Missing or invalid: client_email');
    }

    $clientName = trim((string)($body['client_name'] ?? ''));
    if ($clientName === '') {
        throw new InvalidArgumentException('Missing: client_name');
    }

    $plan = strtolower(trim((string)($body['plan'] ?? 'starter')));
    if (!isset($planPricing[$plan])) {
        throw new InvalidArgumentException('Invalid plan. Allowed: starter, pro, enterprise');
    }

    $seats = max(1, (int)($body['seats'] ?? 1));
    $ticketsPerMonth = max(0, (int)($body['tickets_per_month'] ?? 0));
    $ticketPricePln = max(1.0, (float)($body['ticket_price_pln'] ?? 39.0));
    $seatPricePln = max(0.0, (float)($body['seat_price_pln'] ?? 49.0));
    $mcpMarginPercent = max(0.0, (float)($body['mcp_margin_percent'] ?? 12.5));

    $basePlanPln = $planPricing[$plan];
    $subtotalPln = round($basePlanPln + ($seats * $seatPricePln) + ($ticketsPerMonth * $ticketPricePln), 2);
    $mcpFeePln = round($subtotalPln * ($mcpMarginPercent / 100), 2);
    $monthlyTotalPln = round($subtotalPln + $mcpFeePln, 2);

    return [
        'subscription_id' => 'sub_' . bin2hex(random_bytes(6)),
        'currency' => 'PLN',
        'billing_cycle' => 'monthly',
        'plan' => $plan,
        'client' => [
            'name' => $clientName,
            'email' => $email,
            'repo_url' => trim((string)($body['repo_url'] ?? '')),
        ],
        'line_items' => [
            ['code' => 'plan_' . $plan, 'label' => 'Plan miesięczny', 'qty' => 1, 'unit_price_pln' => $basePlanPln],
            ['code' => 'developer_seat', 'label' => 'Miejsce developerskie', 'qty' => $seats, 'unit_price_pln' => $seatPricePln],
            ['code' => 'ticket_credits', 'label' => 'Kredyty ticketowe / m-c', 'qty' => $ticketsPerMonth, 'unit_price_pln' => $ticketPricePln],
            ['code' => 'mcp_reseller_fee', 'label' => 'Opłata MCP reseller', 'qty' => 1, 'unit_price_pln' => $mcpFeePln],
        ],
        'pricing' => [
            'subtotal_pln' => $subtotalPln,
            'mcp_fee_pln' => $mcpFeePln,
            'monthly_total_pln' => $monthlyTotalPln,
        ],
    ];
}

// ── Router ────────────────────────────────────────────────────────
$action = $_GET['action'] ?? '';
$rawBody = file_get_contents('php://input');
$body = json_decode($rawBody ?: '{}', true) ?? [];

// ── GET /api/redsl.php?action=health ─────────────────────────────
if ($action === 'health') {
    $r = redsl_curl('GET', "$REDSL_API/health");
    if (!$r['ok']) {
        json_out(502, ['status' => 'redsl-api unreachable', 'error' => $r['error']]);
    }
    json_out(200, array_merge(['status' => 'ok'], $r['body'] ?? []));
}

// ── GET /api/redsl.php?action=mcp_health ─────────────────────────
if ($action === 'mcp_health') {
    if ($MCP_API === '') {
        json_out(200, [
            'status' => 'ok',
            'mcp' => [
                'configured' => false,
                'message' => 'MCP_API_URL not configured (dry-run only)',
            ],
        ]);
    }

    $mcpBase = rtrim($MCP_API, '/');
    $headers = [];
    if ($MCP_API_KEY !== '') {
        $headers[] = 'Authorization: Bearer ' . $MCP_API_KEY;
    }
    $r = redsl_curl('GET', "$mcpBase/health", null, $headers);
    if (!$r['ok']) {
        json_out(502, ['status' => 'mcp-api unreachable', 'error' => $r['error'], 'code' => $r['code']]);
    }
    json_out(200, ['status' => 'ok', 'mcp' => ['configured' => true], 'upstream' => $r['body'] ?? []]);
}

// ── POST /api/redsl.php?action=scan ──────────────────────────────
if ($action === 'scan' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $project = (string)($body['project'] ?? '');
    if ($project === '') {
        json_out(400, ['error' => 'Missing: project']);
    }
    $projectPath = resolve_project($project);
    if ($projectPath === false) {
        json_out(400, ['error' => 'Invalid project name']);
    }
    $r = redsl_curl('POST', "$REDSL_API/analyze", ['project_dir' => $projectPath]);
    json_out($r['ok'] ? 200 : 502, $r['body'] ?? ['error' => $r['error']]);
}

// ── POST /api/redsl.php?action=refactor ──────────────────────────
if ($action === 'refactor' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $project    = (string)($body['project'] ?? '');
    $dryRun     = (bool)($body['dry_run'] ?? true);
    $maxActions = min((int)($body['max_actions'] ?? 5), 20);

    if ($project === '') {
        json_out(400, ['error' => 'Missing: project']);
    }
    $projectPath = resolve_project($project);
    if ($projectPath === false) {
        json_out(400, ['error' => 'Invalid project name']);
    }

    $payload = [
        'project_dir' => $projectPath,
        'dry_run'     => $dryRun,
        'max_actions' => $maxActions,
    ];
    $r = redsl_curl('POST', "$REDSL_API/refactor", $payload);
    json_out($r['ok'] ? 200 : 502, $r['body'] ?? ['error' => $r['error']]);
}

// ── POST /api/redsl.php?action=batch ─────────────────────────────
if ($action === 'batch' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $maxActions = min((int)($body['max_actions'] ?? 5), 20);
    $r = redsl_curl('POST', "$REDSL_API/batch/semcod", [
        'semcod_root'  => $WORKSPACE,
        'max_actions'  => $maxActions,
    ]);
    json_out($r['ok'] ? 200 : 502, $r['body'] ?? ['error' => $r['error']]);
}

// ── POST /api/redsl.php?action=mcp_subscription ──────────────────
if ($action === 'mcp_subscription' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    try {
        $subscription = build_mcp_subscription_payload($body);
    } catch (InvalidArgumentException $e) {
        json_out(400, ['error' => $e->getMessage()]);
    }

    $dispatchToMcp = (bool)($body['dispatch_to_mcp'] ?? false);
    if (!$dispatchToMcp || $MCP_API === '') {
        json_out(200, [
            'status' => 'ok',
            'mode' => 'dry_run',
            'dispatch_possible' => $MCP_API !== '',
            'subscription' => $subscription,
        ]);
    }

    $mcpBase = rtrim($MCP_API, '/');
    $headers = ['X-MCP-Reseller: redsl'];
    if ($MCP_API_KEY !== '') {
        $headers[] = 'Authorization: Bearer ' . $MCP_API_KEY;
    }

    $r = redsl_curl('POST', "$mcpBase/subscriptions", ['subscription' => $subscription], $headers);
    if (!$r['ok']) {
        json_out(502, [
            'status' => 'mcp-api unreachable',
            'mode' => 'live',
            'error' => $r['error'],
            'code' => $r['code'],
            'subscription' => $subscription,
        ]);
    }

    json_out(200, [
        'status' => 'ok',
        'mode' => 'live',
        'subscription' => $subscription,
        'upstream' => $r['body'] ?? [],
    ]);
}

// ── Fallback ──────────────────────────────────────────────────────
json_out(400, [
    'error'   => 'Unknown action',
    'actions' => ['health', 'mcp_health', 'scan', 'refactor', 'batch', 'mcp_subscription'],
]);
