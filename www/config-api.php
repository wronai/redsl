<?php
/**
 * ReDSL Config Standard — JSON API
 * 
 * REST API endpoints for config management:
 * - GET /validate — validate current config
 * - GET /history — list change history
 * - POST /apply — apply change proposal (with confirmation)
 */

declare(strict_types=1);

header('Content-Type: application/json');

$configDir = __DIR__ . '/../redsl-config';
$manifestPath = $configDir . '/redsl.config.yaml';

$method = $_SERVER['REQUEST_METHOD'];
$path = $_GET['path'] ?? '';

// Validate config
function _validateConfigHeader(array $config): array {
    $errors = [];
    if (!isset($config['apiVersion'])) {
        $errors[] = 'Missing apiVersion';
    } elseif ($config['apiVersion'] !== 'redsl.config/v1') {
        $errors[] = 'Invalid apiVersion (must be redsl.config/v1)';
    }
    if (!isset($config['kind']) || $config['kind'] !== 'RedslConfig') {
        $errors[] = 'Invalid or missing kind (must be RedslConfig)';
    }
    if (!isset($config['metadata']['name'])) {
        $errors[] = 'Missing metadata.name';
    }
    return $errors;
}

function _validateConfigSecrets(array $config): array {
    $errors = [];
    if (!isset($config['secrets']) || !is_array($config['secrets'])) {
        return $errors;
    }
    $validPrefixes = ['env:', 'file:', 'vault:', 'doppler:'];
    foreach ($config['secrets'] as $name => $spec) {
        if (!isset($spec['ref'])) {
            $errors[] = "Secret '$name' missing ref";
            continue;
        }
        $hasValidPrefix = array_reduce($validPrefixes, fn($carry, $p) => $carry || str_starts_with($spec['ref'], $p), false);
        if (!$hasValidPrefix) {
            $errors[] = "Secret '$name' has invalid ref format (must start with env:/file:/vault:/doppler:)";
        }
    }
    return $errors;
}

function _validateConfigSpec(array $config): array {
    $errors = [];
    if (isset($config['spec']['llm_policy']['mode'])) {
        $validModes = ['frontier_lag', 'frontier_only', 'bounded'];
        if (!in_array($config['spec']['llm_policy']['mode'], $validModes, true)) {
            $errors[] = 'Invalid llm_policy.mode (must be frontier_lag, frontier_only, or bounded)';
        }
    }
    if (isset($config['spec']['coding']['tiers'])) {
        foreach (['cheap', 'balanced', 'premium'] as $tier) {
            $val = $config['spec']['coding']['tiers'][$tier] ?? null;
            if ($val !== null && (!is_numeric($val) || $val < 0)) {
                $errors[] = "Invalid tier value for '$tier' (must be non-negative number)";
            }
        }
    }
    return $errors;
}

function validateConfig(array $config): array {
    return array_merge(
        _validateConfigHeader($config),
        _validateConfigSecrets($config),
        _validateConfigSpec($config)
    );
}

// Get history
function getHistory(string $configDir): array {
    $historyDir = $configDir . '/history';
    $entries = [];
    
    if (!is_dir($historyDir)) return $entries;
    
    $files = glob($historyDir . '/*.yaml');
    rsort($files); // Newest first
    
    foreach (array_slice($files, 0, 20) as $file) {
        $entries[] = [
            'file' => basename($file),
            'timestamp' => filemtime($file),
            'size' => filesize($file),
        ];
    }
    
    return $entries;
}

// Redact secrets for display
function redactSecrets(array $config): array {
    if (isset($config['secrets'])) {
        foreach ($config['secrets'] as $name => &$spec) {
            if (isset($spec['ref'])) {
                $spec['ref'] = preg_replace('/:(.+)$/', ':***REDACTED***', $spec['ref']);
            }
        }
    }
    return $config;
}

// Router
switch ($path) {
    case 'validate':
        if (!file_exists($manifestPath)) {
            http_response_code(404);
            echo json_encode(['error' => 'Config not found']);
            exit;
        }
        
        $content = file_get_contents($manifestPath);
        $config = yaml_parse($content);
        
        if ($config === false) {
            echo json_encode([
                'valid' => false,
                'errors' => ['Invalid YAML syntax'],
            ]);
            exit;
        }
        
        $errors = validateConfig($config);
        
        echo json_encode([
            'valid' => empty($errors),
            'errors' => $errors,
            'config' => redactSecrets($config),
        ]);
        break;
    
    case 'history':
        echo json_encode([
            'history' => getHistory($configDir),
        ]);
        break;
    
    case 'show':
        if (!file_exists($manifestPath)) {
            http_response_code(404);
            echo json_encode(['error' => 'Config not found']);
            exit;
        }
        
        $content = file_get_contents($manifestPath);
        $config = yaml_parse($content);
        
        if ($config === false) {
            http_response_code(400);
            echo json_encode(['error' => 'Invalid YAML']);
            exit;
        }
        
        // Add computed fingerprint
        $fingerprintPayload = $config;
        unset($fingerprintPayload['metadata']);
        $fingerprint = hash('sha256', json_encode($fingerprintPayload, JSON_UNESCAPED_UNICODE));
        
        echo json_encode([
            'config' => redactSecrets($config),
            'fingerprint' => 'sha256:' . $fingerprint,
            'path' => $manifestPath,
        ]);
        break;
    
    case 'diff':
        if (!file_exists($manifestPath)) {
            http_response_code(404);
            echo json_encode(['error' => 'Config not found']);
            exit;
        }
        
        // Get proposal from POST body
        $input = json_decode(file_get_contents('php://input'), true);
        $proposal = $input['proposal'] ?? null;
        
        if (!$proposal) {
            http_response_code(400);
            echo json_encode(['error' => 'Missing proposal']);
            exit;
        }
        
        $current = yaml_parse(file_get_contents($manifestPath));
        
        // Simple diff (full replacement for now)
        $diff = [
            'changes' => [],
            'risk_level' => 'medium',
        ];
        
        foreach ($proposal['changes'] ?? [] as $change) {
            $path = $change['path'] ?? 'unknown';
            $diff['changes'][] = [
                'path' => $path,
                'op' => $change['op'] ?? 'set',
                'old' => $current[$path] ?? null,
                'new' => $change['new_value'] ?? null,
            ];
        }
        
        echo json_encode($diff);
        break;
    
    default:
        http_response_code(404);
        echo json_encode([
            'error' => 'Unknown endpoint',
            'available' => ['validate', 'history', 'show', 'diff'],
        ]);
}
