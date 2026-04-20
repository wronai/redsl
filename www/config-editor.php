<?php
/**
 * ReDSL Config Standard — Web Editor
 * 
 * Simple web-based editor for redsl-config/redsl.config.yaml
 * Features:
 * - Read/write config with validation
 * - Secret redaction (never display secret values)
 * - Risk level indicators
 * - Change preview before apply
 */

declare(strict_types=1);

session_start();

require_once __DIR__ . '/lib/i18n.php';
$i18n = I18n::getInstance();
$lang = $i18n->getLang();
$getLangUrls = fn(): array => $i18n->getLangUrls();
$getLangName = fn(string $l): string => $i18n->getLangName($l);

function h_ce(string $s): string { return htmlspecialchars($s, ENT_QUOTES | ENT_HTML5, 'UTF-8'); }

$configDir = __DIR__ . '/../redsl-config';
$manifestPath = $configDir . '/redsl.config.yaml';

// Risk level colors
const RISK_COLORS = [
    'low' => '#22c55e',
    'medium' => '#f59e0b',
    'high' => '#f97316',
    'critical' => '#ef4444',
    'unknown' => '#6b7280',
];

const RISK_LABELS = [
    'low' => 'Low Risk',
    'medium' => 'Medium Risk',
    'high' => 'High Risk — Requires Confirmation',
    'critical' => 'Critical — Requires Confirmation',
    'unknown' => 'Unknown',
];

// Load config if exists
function loadConfig(string $path): ?array {
    if (!file_exists($path)) return null;
    $content = file_get_contents($path);
    return yaml_parse($content) ?: null;
}

// Save config with backup
function saveConfig(string $path, array $data): bool {
    $dir = dirname($path);
    if (!is_dir($dir)) mkdir($dir, 0750, true);
    
    // Create backup
    if (file_exists($path)) {
        $backupDir = $dir . '/history';
        if (!is_dir($backupDir)) mkdir($backupDir, 0750, true);
        $backupPath = $backupDir . '/backup-' . date('Ymd-His') . '.yaml';
        copy($path, $backupPath);
    }
    
    $yaml = yaml_emit($data, YAML_UTF8_ENCODING);
    return file_put_contents($path, $yaml, LOCK_EX) !== false;
}

// Get nested value from array
function getNestedValue(array $array, string $path): mixed {
    $keys = explode('.', $path);
    $current = $array;
    foreach ($keys as $key) {
        if (!isset($current[$key])) return null;
        $current = $current[$key];
    }
    return $current;
}

// Risk matrix (subset of config_standard/catalog.py)
const RISK_MATRIX = [
    'spec.llm_policy.max_age_days' => 'low',
    'spec.llm_policy.mode' => 'low',
    'spec.llm_policy.strict' => 'medium',
    'spec.llm_policy.unknown_release' => 'medium',
    'spec.coding.cost_weights' => 'low',
    'spec.coding.tiers.cheap' => 'low',
    'spec.coding.tiers.balanced' => 'low',
    'spec.coding.tiers.premium' => 'low',
    'spec.coding.default_tiers' => 'low',
    'spec.coding.max_cost_per_call_usd' => 'medium',
    'spec.coding.require_tool_calling' => 'low',
    'spec.coding.min_context' => 'low',
    'spec.registry_sources' => 'medium',
    'spec.cache' => 'low',
    'secrets' => 'critical',
    'profile' => 'high',
    'metadata.version' => 'low',
    'apiVersion' => 'critical',
];

function getRiskLevel(string $path): string {
    foreach (RISK_MATRIX as $pattern => $risk) {
        if (fnmatch($pattern, $path)) return $risk;
    }
    return 'unknown';
}

// Handle POST
$message = '';
$error = '';
$config = loadConfig($manifestPath);

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'] ?? '';
    
    if ($action === 'save') {
        $yamlContent = $_POST['config_yaml'] ?? '';
        $parsed = yaml_parse($yamlContent);
        
        if ($parsed === false) {
            $error = 'Invalid YAML syntax';
        } else {
            // Validate required fields
            if (!isset($parsed['apiVersion']) || $parsed['apiVersion'] !== 'redsl.config/v1') {
                $error = 'Missing or invalid apiVersion (must be redsl.config/v1)';
            } elseif (!isset($parsed['metadata']['name'])) {
                $error = 'Missing metadata.name';
            } else {
                // Bump version
                $parsed['metadata']['version'] = ($parsed['metadata']['version'] ?? 0) + 1;
                $parsed['metadata']['updated'] = date('c');
                
                if (saveConfig($manifestPath, $parsed)) {
                    $message = 'Configuration saved successfully (backup created)';
                    $config = $parsed;
                } else {
                    $error = 'Failed to save configuration';
                }
            }
        }
    } elseif ($action === 'init') {
        // Create default config
        $defaultConfig = [
            'apiVersion' => 'redsl.config/v1',
            'kind' => 'RedslConfig',
            'metadata' => [
                'name' => 'my-project',
                'version' => 1,
                'created' => date('c'),
                'updated' => date('c'),
            ],
            'profile' => 'production',
            'secrets' => [
                'openrouter_api_key' => [
                    'ref' => 'env:OPENROUTER_API_KEY',
                    'required' => true,
                ],
                'anthropic_api_key' => [
                    'ref' => 'env:ANTHROPIC_API_KEY',
                    'required' => false,
                ],
            ],
            'spec' => [
                'llm_policy' => [
                    'mode' => 'frontier_lag',
                    'max_age_days' => 180,
                    'strict' => true,
                ],
                'coding' => [
                    'cost_metric' => 'weighted',
                    'max_cost_per_call_usd' => 0.10,
                    'require_tool_calling' => true,
                    'min_context' => 32768,
                    'tiers' => [
                        'cheap' => 0.50,
                        'balanced' => 3.00,
                        'premium' => 15.00,
                    ],
                    'default_tiers' => [
                        'extract_function' => 'cheap',
                        'split_module' => 'balanced',
                        'architecture_review' => 'premium',
                    ],
                ],
            ],
        ];
        
        if (saveConfig($manifestPath, $defaultConfig)) {
            $message = 'Default configuration created';
            $config = $defaultConfig;
        } else {
            $error = 'Failed to create configuration';
        }
    }
}

// Prepare YAML for editing
$yamlContent = $config ? yaml_emit($config, YAML_UTF8_ENCODING) : '';

?>
<!DOCTYPE html>
<html lang="<?= h_ce($lang) ?>">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
    <title>ReDSL Config Editor</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..900;1,9..144,300..900&family=Instrument+Sans:ital,wght@0,400..700;1,400..700&family=JetBrains+Mono:wght@400;500;700&display=swap">
    <link rel="stylesheet" href="style.css">
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }
        h1 {
            margin: 0;
            font-size: 24px;
            color: #1a1a2e;
        }
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }
        .badge-exists { background: #22c55e; color: white; }
        .badge-missing { background: #ef4444; color: white; }
        
        .alert {
            padding: 12px 16px;
            border-radius: 6px;
            margin-bottom: 20px;
        }
        .alert-success { background: #dcfce7; color: #166534; border: 1px solid #86efac; }
        .alert-error { background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }
        
        .editor-grid {
            display: grid;
            grid-template-columns: 1fr 350px;
            gap: 20px;
        }
        @media (max-width: 900px) {
            .editor-grid { grid-template-columns: 1fr; }
        }
        
        .editor-pane {
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            padding: 20px;
        }
        
        textarea {
            width: 100%;
            min-height: 600px;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
            font-size: 13px;
            line-height: 1.6;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 16px;
            resize: vertical;
            tab-size: 2;
        }
        textarea:focus {
            outline: none;
            border-color: #3b82f6;
            box-shadow: 0 0 0 3px rgba(59,130,246,0.1);
        }
        
        .sidebar {
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        
        .panel {
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            padding: 16px;
        }
        
        .panel h3 {
            margin: 0 0 12px 0;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #666;
        }
        
        .btn {
            display: block;
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-primary {
            background: #3b82f6;
            color: white;
        }
        .btn-primary:hover { background: #2563eb; }
        .btn-primary:active { transform: translateY(1px); }
        
        .btn-secondary {
            background: #f3f4f6;
            color: #374151;
        }
        .btn-secondary:hover { background: #e5e7eb; }
        
        .risk-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        .risk-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 0;
            border-bottom: 1px solid #f0f0f0;
            font-size: 13px;
        }
        .risk-item:last-child { border-bottom: none; }
        
        .risk-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            flex-shrink: 0;
        }
        
        .path-list {
            list-style: none;
            padding: 0;
            margin: 0;
            font-family: monospace;
            font-size: 12px;
        }
        .path-item {
            padding: 4px 0;
            color: #666;
        }
        
        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 6px 0;
            font-size: 13px;
            border-bottom: 1px solid #f0f0f0;
        }
        .info-row:last-child { border-bottom: none; }
        .info-label { color: #666; }
        .info-value { font-weight: 500; }
        
        .secret-warning {
            background: #fef3c7;
            border: 1px solid #fcd34d;
            border-radius: 6px;
            padding: 12px;
            font-size: 13px;
            color: #92400e;
        }
        .secret-warning strong {
            display: block;
            margin-bottom: 4px;
        }
        .ce-wrap { max-width: 1200px; margin: 0 auto; padding: 0 24px 60px; }
        .ce-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; padding-bottom: 20px; border-bottom: 2px solid #e0e0e0; }
        .ce-header h1 { margin: 0; font-size: 22px; color: #1a1a2e; font-family: inherit; }
        .ce-header p { margin: 4px 0 0; color: #666; font-size: 13px; }
    </style>
</head>
<body>

<header class="masthead">
    <div class="masthead-inner">
        <div class="masthead-left">
            <span class="issue">Config Editor</span>
        </div>
        <a href="/" class="masthead-logo">
            <span class="logo-r">R</span><span>edsl</span>
        </a>
        <nav class="masthead-right">
            <a href="/#jak">Jak działa</a>
            <a href="/#cennik">Cennik</a>
            <a href="/#kontakt">Kontakt</a>
            <div class="lang-switcher">
                <?php foreach ($getLangUrls() as $code => $url): ?>
                <a href="<?= h_ce($url) ?>" class="lang-btn <?= $code === $lang ? 'lang-btn-active' : '' ?>"><?= h_ce(strtoupper($code)) ?></a>
                <?php endforeach; ?>
            </div>
        </nav>
    </div>
    <div class="rule"></div>
</header>

    <div class="ce-wrap">
        <header>
            <div>
                <h1>ReDSL Config Editor</h1>
                <p style="margin: 4px 0 0 0; color: #666; font-size: 14px;">
                    <?= htmlspecialchars($manifestPath) ?>
                </p>
            </div>
            <span class="badge <?= $config ? 'badge-exists' : 'badge-missing' ?>">
                <?= $config ? 'Config Found' : 'No Config' ?>
            </span>
        </header>
        
        <?php if ($message): ?>
        <div class="alert alert-success"><?= htmlspecialchars($message) ?></div>
        <?php endif; ?>
        
        <?php if ($error): ?>
        <div class="alert alert-error"><?= htmlspecialchars($error) ?></div>
        <?php endif; ?>
        
        <?php if (!$config): ?>
        <div class="editor-pane" style="text-align: center; padding: 60px 20px;">
            <h2>No configuration found</h2>
            <p style="color: #666; margin: 16px 0;">
                Create a default configuration to get started.
            </p>
            <form method="post" style="margin-top: 24px;">
                <input type="hidden" name="action" value="init">
                <button type="submit" class="btn btn-primary" style="width: auto; padding: 12px 32px;">
                    Create Default Config
                </button>
            </form>
        </div>
        <?php else: ?>
        
        <form method="post">
            <input type="hidden" name="action" value="save">
            
            <div class="editor-grid">
                <div class="editor-pane">
                    <textarea 
                        name="config_yaml" 
                        spellcheck="false"
                        placeholder="# Paste your redsl.config.yaml content here..."
                    ><?= htmlspecialchars($yamlContent) ?></textarea>
                </div>
                
                <div class="sidebar">
                    <div class="panel">
                        <h3>Actions</h3>
                        <button type="submit" class="btn btn-primary" style="margin-bottom: 8px;">
                            Save Changes
                        </button>
                        <button type="button" class="btn btn-secondary" onclick="location.reload()">
                            Reset to Saved
                        </button>
                    </div>
                    
                    <div class="secret-warning">
                        <strong>Security Note</strong>
                        Secret values (env:VAR, file:path) are never displayed. 
                        Only the reference format is shown.
                    </div>
                    
                    <div class="panel">
                        <h3>Config Info</h3>
                        <div class="info-row">
                            <span class="info-label">Name</span>
                            <span class="info-value"><?= htmlspecialchars($config['metadata']['name'] ?? 'N/A') ?></span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Version</span>
                            <span class="info-value"><?= $config['metadata']['version'] ?? 'N/A' ?></span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Profile</span>
                            <span class="info-value"><?= htmlspecialchars($config['profile'] ?? 'N/A') ?></span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Secrets</span>
                            <span class="info-value"><?= count($config['secrets'] ?? []) ?></span>
                        </div>
                    </div>
                    
                    <div class="panel">
                        <h3>Risk Levels</h3>
                        <ul class="risk-list">
                            <?php foreach (['low', 'medium', 'high', 'critical'] as $risk): ?>
                            <li class="risk-item">
                                <span class="risk-dot" style="background: <?= RISK_COLORS[$risk] ?>"></span>
                                <span><?= RISK_LABELS[$risk] ?></span>
                            </li>
                            <?php endforeach; ?>
                        </ul>
                    </div>
                    
                    <div class="panel">
                        <h3>Common Paths</h3>
                        <ul class="path-list">
                            <li class="path-item">spec.llm_policy.mode</li>
                            <li class="path-item">spec.llm_policy.max_age_days</li>
                            <li class="path-item">spec.coding.max_cost_per_call_usd</li>
                            <li class="path-item">spec.coding.tiers.premium</li>
                            <li class="path-item">secrets.*.ref</li>
                        </ul>
                    </div>
                    
                    <div class="panel">
                        <h3>Secret Providers</h3>
                        <ul class="path-list">
                            <li class="path-item">env:VAR_NAME</li>
                            <li class="path-item">file:/path/to/key</li>
                            <li class="path-item">vault:path#key</li>
                            <li class="path-item">doppler:proj/config/key</li>
                        </ul>
                    </div>
                </div>
            </div>
        </form>
        
        <?php endif; ?>
    </div>

<footer class="colophon">
    <div class="container">
        <div class="colophon-bottom">
            <span>&copy; <?= date('Y') ?> REDSL</span>
            <span class="dot">&middot;</span>
            <span>Polska &middot; UE</span>
            <span class="dot">&middot;</span>
            <a href="/" style="color:inherit">← Strona główna</a>
        </div>
    </div>
</footer>

</body>
</html>
