<?php
/**
 * ReDSL — Refactoring Proposals (SaaS Panel)
 *
 * User receives an email with a link to this page.
 * They can select which proposals (tickets) they want to implement.
 *
 * Selection format: "1, 3, 7, 12-15, 24" or "all" or "everything under 15"
 */

declare(strict_types=1);

session_start();

require __DIR__ . '/bootstrap.php';

// Re-bind page-specific helpers (bootstrap loaded Logger + i18n)
$_i18n       = I18n::getInstance();
$t           = fn(string $k, array $p = []): string => $_i18n->t($k, $p);
$th          = fn(string $k, array $p = []): string => $_i18n->th($k, $p);
$lang        = $_i18n->getLang();
$getLangUrls = fn(): array => $_i18n->getLangUrls();
$getLangName = fn(string $l): string => $_i18n->getLangName($l);
$formatPrice = fn(float $usd, bool $sym = true): string => $_i18n->formatPrice($usd, $sym);
$getPricing  = fn(string $k, bool $sym = true): string => $_i18n->getPricing($k, $sym);
$getCurrencyConfig = fn(): array => $_i18n->getCurrencyConfig();

// Demo data — in production loaded from database/API
$proposals = [
    ['id' => 1, 'title' => 'UserService class refactoring', 'file' => 'src/services/UserService.php', 'effort' => 'M', 'lines' => 150, 'price' => 10, 'priority' => 1, 'redsl_min' => 8],
    ['id' => 2, 'title' => 'Method extraction in PaymentController', 'file' => 'src/controllers/PaymentController.php', 'effort' => 'S', 'lines' => 80, 'price' => 10, 'priority' => 2, 'redsl_min' => 4],
    ['id' => 3, 'title' => 'Cyclomatic complexity reduction', 'file' => 'src/utils/Calculator.php', 'effort' => 'L', 'lines' => 320, 'price' => 10, 'priority' => 1, 'redsl_min' => 15],
    ['id' => 4, 'title' => 'Remove code duplication in validators', 'file' => 'src/validators/', 'effort' => 'M', 'lines' => 200, 'price' => 10, 'priority' => 2, 'redsl_min' => 10],
    ['id' => 5, 'title' => 'Improve naming and conventions', 'file' => 'src/models/', 'effort' => 'S', 'lines' => 120, 'price' => 10, 'priority' => 3, 'redsl_min' => 3],
    ['id' => 6, 'title' => 'Repository pattern refactoring', 'file' => 'src/repositories/', 'effort' => 'L', 'lines' => 450, 'price' => 10, 'priority' => 1, 'redsl_min' => 20],
    ['id' => 7, 'title' => 'Interface extraction', 'file' => 'src/contracts/', 'effort' => 'M', 'lines' => 180, 'price' => 10, 'priority' => 2, 'redsl_min' => 9],
    ['id' => 8, 'title' => 'Remove dead code', 'file' => 'src/legacy/', 'effort' => 'S', 'lines' => 90, 'price' => 10, 'priority' => 3, 'redsl_min' => 3],
];

// Handle form submission
$message = '';
$selectedIds = [];
$totalPrice = 0;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $selection = $_POST['selection'] ?? '';
    $customInput = trim($_POST['custom_input'] ?? '');

    // Parse selection
    $ticketPriceUsd = 10.0;
    if ($selection === 'all') {
        $selectedIds = array_column($proposals, 'id');
        $totalPriceUsd = count($proposals) * $ticketPriceUsd;
    } elseif ($selection === 'under_15') {
        // All under threshold — all are same price
        $selectedIds = array_column($proposals, 'id');
        $totalPriceUsd = count($proposals) * $ticketPriceUsd;
    } elseif ($selection === 'custom' && $customInput) {
        // Parse "1, 3, 7, 12-15, 24"
        $selectedIds = parseSelection($customInput);
        $totalPriceUsd = count($selectedIds) * $ticketPriceUsd;
    }

    if (!empty($selectedIds)) {
        $totalPriceFormatted = $formatPrice($totalPriceUsd);
        $message = sprintf(
            $t('proposals.success'),
            (int)count($selectedIds),
            $totalPriceFormatted
        );
        // In production: save to database, send confirmation email
    }
}

function parseSelection(string $input): array {
    $ids = [];
    $parts = array_map('trim', explode(',', $input));

    foreach ($parts as $part) {
        if (strpos($part, '-') !== false) {
            // Range like "12-15"
            [$start, $end] = array_map('intval', explode('-', $part));
            for ($i = $start; $i <= $end; $i++) {
                $ids[] = $i;
            }
        } else {
            $ids[] = intval($part);
        }
    }

    return array_unique(array_filter($ids));
}

function h(string $s): string {
    return htmlspecialchars($s, ENT_QUOTES | ENT_HTML5, 'UTF-8');
}

$priorityEmoji = [1 => '🔴', 2 => '🟠', 3 => '🟡'];
$humanHours = ['S' => '~2h', 'M' => '~4h', 'L' => '~8h'];
$ticketPrice = $formatPrice(10.0);

$year = date('Y');
$issue = date('Y.m');
?>
<!DOCTYPE html>
<html lang="<?=h($lang)?>">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Refactoring Proposals — ReDSL</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..900;1,9..144,300..900&family=Instrument+Sans:ital,wght@0,400..700;1,400..700&family=JetBrains+Mono:wght@400;500;700&display=swap">
    <link rel="stylesheet" href="style.css">
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' fill='%23c8442d'/%3E%3Ctext x='50%25' y='58%25' font-family='serif' font-size='22' fill='%23f4efe6' text-anchor='middle' font-weight='900'%3ER%3C/text%3E%3C/svg%3E">
    <style>
        * { box-sizing: border-box; }

        .lang-switch {
            text-align: right;
            margin-bottom: 8px;
            font-size: 12px;
        }
        .lang-switch a { color: #888; text-decoration: none; }
        .lang-switch a:hover { color: #c8442d; }
        .lang-switch .active { color: #1a1a2e; font-weight: 600; }

        .proposals-container {
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }

        .page-header {
            background: white;
            border-radius: 12px;
            padding: 24px 32px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .page-header h1 {
            margin: 0 0 8px 0;
            font-size: 24px;
            color: #1a1a2e;
        }
        .subtitle {
            color: #666;
            font-size: 14px;
        }

        .alert {
            background: #dcfce7;
            border: 1px solid #86efac;
            color: #166534;
            padding: 16px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }

        .selection-panel {
            background: white;
            border-radius: 12px;
            padding: 24px 32px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .selection-title {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 16px;
            color: #333;
        }

        .option-row {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            margin-bottom: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .option-row:hover {
            border-color: #3b82f6;
            background: #f8fafc;
        }
        .option-row input[type="radio"] {
            width: 20px;
            height: 20px;
            margin: 0;
        }
        .option-label {
            flex: 1;
            font-size: 14px;
        }
        .option-price {
            font-weight: 600;
            color: #c8442d;
        }

        .custom-input {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            font-size: 14px;
            font-family: 'SF Mono', Monaco, monospace;
            margin-top: 8px;
        }
        .custom-input:focus {
            outline: none;
            border-color: #3b82f6;
        }
        .hint {
            font-size: 12px;
            color: #666;
            margin-top: 6px;
        }

        .proposals-list {
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .proposal-item {
            display: grid;
            grid-template-columns: 40px 1fr 80px 80px 70px 60px;
            gap: 16px;
            align-items: center;
            padding: 16px 24px;
            border-bottom: 1px solid #f0f0f0;
        }
        .proposal-item:last-child {
            border-bottom: none;
        }
        .proposal-item:hover {
            background: #fafafa;
        }
        .prop-id {
            font-family: monospace;
            font-size: 13px;
            color: #666;
        }
        .prop-title {
            font-size: 14px;
            font-weight: 500;
        }
        .prop-file {
            font-size: 12px;
            color: #888;
            margin-top: 2px;
        }
        .prop-effort {
            font-size: 12px;
            color: #666;
            text-align: center;
        }
        .prop-lines {
            font-size: 12px;
            color: #666;
            text-align: right;
        }
        .prop-price {
            font-weight: 600;
            color: #c8442d;
            text-align: right;
        }

        .summary-bar {
            background: #1a1a2e;
            color: white;
            padding: 20px 32px;
            border-radius: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 20px;
        }
        .summary-text {
            font-size: 16px;
        }
        .summary-price {
            font-size: 28px;
            font-weight: 700;
        }
        .summary-note {
            font-size: 12px;
            opacity: 0.8;
            margin-top: 4px;
        }

        .btn-submit {
            padding: 14px 32px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            background: #3b82f6;
            color: white;
        }
        .btn-submit:hover {
            background: #2563eb;
        }

        .instructions {
            background: #fef3c7;
            border: 1px solid #fcd34d;
            border-radius: 8px;
            padding: 16px 20px;
            margin-bottom: 20px;
            font-size: 14px;
        }
        .instructions strong {
            color: #92400e;
        }
        .instructions code {
            background: rgba(0,0,0,0.1);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: monospace;
        }

        .help-text {
            text-align: center;
            margin-top: 30px;
            font-size: 13px;
            color: #888;
        }
        .help-text a {
            color: #3b82f6;
        }
    </style>
</head>
<body>

<!-- ============ MASTHEAD ============ -->
<header class="masthead">
    <div class="masthead-inner">
        <div class="masthead-left">
            <span class="issue">Issue <?=h($issue)?></span>
            <span class="dot">·</span>
            <span class="date"><?=h(date('j F Y'))?></span>
        </div>
        <a href="/" class="logo">
            <span class="logo-r">R</span><span>edsl</span>
        </a>
        <nav class="masthead-right">
            <a href="/#how">How it works</a>
            <a href="/#pricing">Pricing</a>
            <a href="/config-editor.php">Config</a>
            <a href="/proposals">Proposals</a>
            <a href="/#contact">Contact</a>
            <div class="lang-switcher">
                <?php foreach ($getLangUrls() as $code => $url): ?>
                <a href="<?=h($url)?>" class="lang-btn <?= $code === $lang ? 'lang-btn-active' : '' ?>"><?=h(strtoupper($code))?></a>
                <?php endforeach; ?>
            </div>
        </nav>
    </div>
    <div class="rule"></div>
</header>

<main class="proposals-container">
    <div class="page-header">
        <h1><?=h($t('proposals.title'))?></h1>
        <p class="subtitle"><?=h($t('proposals.project'))?>: <strong>my-app</strong> · <?=h($t('proposals.received'))?>: <?=h(date('j F Y'))?></p>
    </div>

    <?php if ($message): ?>
    <div class="alert"><?= h($message) ?></div>
    <?php endif; ?>

    <form method="post">
        <div class="instructions">
            <strong><?=h($t('proposals.how_to'))?></strong>
            <ul style="margin: 8px 0; padding-left: 20px;">
                <li><code>1, 3, 7</code> — <?=h($t('proposals.how_1'))?></li>
                <li><code>12-15</code> — <?=h($t('proposals.how_2'))?></li>
                <li><code>all</code> — <?=h($t('proposals.how_3'))?></li>
                <li><code>everything under 15</code> — <?=h($t('proposals.how_4'))?></li>
            </ul>
        </div>

        <div class="selection-panel">
            <div class="selection-title"><?=h($t('proposals.select_options'))?></div>

            <label class="option-row">
                <input type="radio" name="selection" value="all" checked>
                <span class="option-label"><?=h($t('proposals.all_proposals'))?></span>
                <span class="option-price"><?=h($formatPrice(count($proposals) * 10.0))?></span>
            </label>

            <label class="option-row">
                <input type="radio" name="selection" value="under_15">
                <span class="option-label"><?=h($t('proposals.under_15'))?></span>
                <span class="option-price"><?=h($formatPrice(count($proposals) * 10.0))?></span>
            </label>

            <label class="option-row" style="flex-wrap: wrap;">
                <input type="radio" name="selection" value="custom">
                <span class="option-label" style="flex: 0 0 auto;"><?=h($t('proposals.custom'))?></span>
                <input type="text" name="custom_input" class="custom-input" placeholder="<?=h($t('proposals.placeholder'))?>" style="flex: 1; min-width: 200px;">
            </label>
            <p class="hint"><?=$th('proposals.hint')?></p>
        </div>

        <div class="proposals-list">
            <div class="proposal-item" style="background: #fafafa; font-weight: 600; color: #666;">
                <div class="prop-id"><?=h($t('proposals.table_id'))?></div>
                <div class="prop-title"><?=h($t('proposals.table_title'))?></div>
                <div class="prop-effort" style="text-align:center"><?=h($t('proposals.table_redsl'))?></div>
                <div class="prop-effort" style="text-align:center"><?=h($t('proposals.table_human'))?></div>
                <div class="prop-lines"><?=h($t('proposals.table_lines'))?></div>
                <div class="prop-price"><?=h($t('proposals.table_price'))?></div>
            </div>
            <?php foreach ($proposals as $p): ?>
            <div class="proposal-item">
                <div class="prop-id"><?= $p['id'] ?></div>
                <div>
                    <div class="prop-title"><?= h($p['title']) ?></div>
                    <div class="prop-file"><?= h($p['file']) ?></div>
                </div>
                <div class="prop-effort" style="text-align:center" title="<?=h($t('proposals.redsl_tooltip'))?>"><?= $p['redsl_min'] ?> min</div>
                <div class="prop-effort" style="text-align:center; color:#888" title="<?=h($t('proposals.human_tooltip'))?>"><?= $humanHours[$p['effort']] ?></div>
                <div class="prop-lines">~<?= $p['lines'] ?></div>
                <div class="prop-price"><?=h($formatPrice($p['price']))?></div>
            </div>
            <?php endforeach; ?>
        </div>

        <div class="summary-bar">
            <div>
                <div class="summary-text"><?=h($t('proposals.summary_select'))?></div>
                <div class="summary-note"><?=h($t('proposals.summary_note'))?></div>
            </div>
            <button type="submit" class="btn-submit"><?=h($t('proposals.confirm'))?></button>
        </div>
    </form>

    <p class="help-text">
        <?=h($t('proposals.questions'))?> <a href="/#contact">Contact</a> ·
        <a href="mailto:contact@redsl.io">contact@redsl.io</a>
    </p>
</main>

<!-- ============ FOOTER / KOLOPHON ============ -->
<footer class="colophon">
    <div class="container">
        <div class="colophon-grid">
            <div>
                <div class="footer-logo"><span class="logo-r">R</span>edsl</div>
                <p class="footer-sub">Refactor · DSL · Self-Learning</p>
            </div>
            <div>
                <h5><?=h($t('footer.product'))?></h5>
                <ul>
                    <li><a href="/#how">How it works</a></li>
                    <li><a href="/#pricing">Pricing</a></li>
                    <li><a href="/#contact">Contact</a></li>
                </ul>
            </div>
            <div>
                <h5><?=h($t('footer.resources'))?></h5>
                <ul>
                    <li><a href="https://github.com/wronai/redsl" rel="noopener">GitHub</a></li>
                    <li><a href="https://github.com/wronai/redsl/tree/main/docs" rel="noopener">Documentation</a></li>
                    <li><a href="/blog/">Blog</a></li>
                </ul>
            </div>
            <div>
                <h5><?=h($t('footer.legal'))?></h5>
                <ul>
                    <li><a href="/nda-wzor"><?=h($t('footer.nda'))?></a></li>
                    <li><a href="/polityka-prywatnosci"><?=h($t('footer.privacy'))?></a></li>
                    <li><a href="/regulamin"><?=h($t('footer.terms'))?></a></li>
                </ul>
            </div>
        </div>
        <div class="colophon-bottom">
            <span>© <?=h((string)$year)?> ReDSL · Issue <?=h($issue)?></span>
            <span class="dot">·</span>
            <span>Poland · EU</span>
            <span class="dot">·</span>
            <span><?=h($t('footer.copyright'))?></span>
        </div>
    </div>
</footer>

<script src="app.js" defer></script>
</body>
</html>
