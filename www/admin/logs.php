<?php
declare(strict_types=1);

/**
 * Admin - Podgląd logów (info/warning/error/all)
 */

require_once __DIR__ . '/auth.php';
require_once __DIR__ . '/../lib/Logger.php';

Logger::setLogDir(__DIR__ . '/../var/logs');

$level = $_GET['level'] ?? 'all';
$lines = max(10, min(1000, (int)($_GET['lines'] ?? 200)));
$search = trim($_GET['q'] ?? '');

// Clear log action (guarded by CSRF)
if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['action'] ?? '') === 'clear') {
    $toClear = $_POST['level'] ?? '';
    if (in_array($toClear, ['info', 'warning', 'error', 'all'], true)) {
        $path = __DIR__ . '/../var/logs/' . $toClear . '.log';
        if (file_exists($path)) {
            @file_put_contents($path, '');
        }
        header('Location: /admin/logs.php?level=' . urlencode($level));
        exit;
    }
}

$entries = Logger::tail($level, $lines);
if ($search !== '') {
    $entries = array_filter($entries, fn($e) => stripos($e, $search) !== false);
}
$stats = Logger::stats();

function h(string $s): string { return htmlspecialchars($s, ENT_QUOTES, 'UTF-8'); }

function classForLevel(string $line): string {
    if (str_contains($line, '[ERROR]') || str_contains($line, '[CRITICAL]')) return 'error';
    if (str_contains($line, '[WARNING]')) return 'warning';
    if (str_contains($line, '[DEBUG]')) return 'debug';
    return 'info';
}

function fmtSize(int $bytes): string {
    if ($bytes < 1024) return $bytes . ' B';
    if ($bytes < 1024 * 1024) return round($bytes / 1024, 1) . ' KB';
    return round($bytes / 1024 / 1024, 2) . ' MB';
}
?>
<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<title>Logi — Admin REDSL</title>
<style>
  body { font-family: -apple-system, sans-serif; margin: 0; background: #1a1a1a; color: #ccc; }
  header { background: #0d1117; padding: 16px 24px; border-bottom: 1px solid #30363d; }
  h1 { margin: 0; font-size: 20px; color: #e6edf3; }
  .nav { padding: 8px 24px; background: #161b22; border-bottom: 1px solid #30363d; display: flex; gap: 8px; flex-wrap: wrap; }
  .nav a { color: #8b949e; text-decoration: none; padding: 8px 12px; border-radius: 4px; font-size: 13px; }
  .nav a:hover, .nav a.active { background: #21262d; color: #58a6ff; }
  .stats { padding: 12px 24px; background: #0d1117; display: flex; gap: 24px; font-size: 12px; color: #8b949e; flex-wrap: wrap; }
  .stats span strong { color: #e6edf3; }
  form.search { padding: 12px 24px; background: #161b22; display: flex; gap: 8px; align-items: center; }
  form.search input[type="text"], form.search input[type="number"] {
    background: #0d1117; border: 1px solid #30363d; color: #e6edf3;
    padding: 6px 10px; border-radius: 4px; font-size: 13px;
  }
  form.search button {
    background: #238636; color: white; border: none; padding: 6px 14px;
    border-radius: 4px; cursor: pointer; font-size: 13px;
  }
  .clear-form { display: inline; margin-left: auto; }
  .clear-form button { background: #c8442d; }
  pre.logs {
    margin: 0; padding: 16px 24px; font-family: 'SF Mono', Consolas, monospace;
    font-size: 12px; line-height: 1.5; overflow-x: auto; white-space: pre-wrap;
    word-break: break-all; background: #0d1117;
  }
  .line { padding: 2px 0; border-left: 3px solid transparent; padding-left: 8px; }
  .line.error { border-left-color: #f85149; color: #ffa198; background: rgba(248,81,73,0.05); }
  .line.warning { border-left-color: #d29922; color: #e3b341; background: rgba(210,153,34,0.05); }
  .line.info { color: #79c0ff; }
  .line.debug { color: #8b949e; }
  .empty { padding: 40px; text-align: center; color: #6e7681; }
</style>
</head>
<body>
<header>
  <h1>📋 Logi systemowe</h1>
</header>

<div class="nav">
  <a href="?level=all" class="<?= $level === 'all' ? 'active' : '' ?>">Wszystkie</a>
  <a href="?level=info" class="<?= $level === 'info' ? 'active' : '' ?>">INFO</a>
  <a href="?level=warning" class="<?= $level === 'warning' ? 'active' : '' ?>">WARNING</a>
  <a href="?level=error" class="<?= $level === 'error' ? 'active' : '' ?>">ERROR</a>
  <a href="/admin/" style="margin-left: auto;">← Dashboard</a>
</div>

<div class="stats">
  <?php foreach ($stats as $lvl => $s): ?>
    <span>
      <strong><?= strtoupper($lvl) ?>:</strong>
      <?= $s['exists'] ? fmtSize($s['size']) : '—' ?>
      <?php if ($s['mtime']): ?>· <?= date('Y-m-d H:i:s', $s['mtime']) ?><?php endif; ?>
    </span>
  <?php endforeach; ?>
</div>

<form class="search" method="GET">
  <input type="hidden" name="level" value="<?= h($level) ?>">
  <input type="text" name="q" placeholder="🔍 Szukaj w logach..." value="<?= h($search) ?>" style="flex: 1;">
  <input type="number" name="lines" min="10" max="1000" value="<?= $lines ?>" style="width: 90px;">
  <button type="submit">Odśwież</button>
  
  <form class="clear-form" method="POST" onsubmit="return confirm('Wyczyścić log <?= h($level) ?>?')">
    <input type="hidden" name="action" value="clear">
    <input type="hidden" name="level" value="<?= h($level) ?>">
    <button type="submit">🗑 Wyczyść</button>
  </form>
</form>

<?php if (empty($entries)): ?>
  <div class="empty">
    📭 Brak wpisów w logu <strong><?= h($level) ?></strong>
    <?= $search ? 'pasujących do "' . h($search) . '"' : '' ?>
  </div>
<?php else: ?>
  <pre class="logs"><?php foreach ($entries as $line): ?><div class="line <?= classForLevel($line) ?>"><?= h($line) ?></div><?php endforeach; ?></pre>
<?php endif; ?>

</body>
</html>
