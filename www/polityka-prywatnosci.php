<?php
/**
 * ReDSL — Privacy Policy / Polityka Prywatności
 * i18n-aware, uses main site styling
 */
declare(strict_types=1);

require_once __DIR__ . '/lib/i18n.php';
$_i18n       = I18n::getInstance();
$t           = fn(string $k, array $p = []): string => $_i18n->t($k, $p);
$lang        = $_i18n->getLang();
$getLangUrls = fn(): array => $_i18n->getLangUrls();
$getLangName = fn(string $l): string => $_i18n->getLangName($l);

function h_pp(string $s): string { return htmlspecialchars($s, ENT_QUOTES | ENT_HTML5, 'UTF-8'); }

$year  = date('Y');
$issue = date('Y.m');
?>
<!DOCTYPE html>
<html lang="<?=h_pp($lang)?>">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title><?=h_pp($t('privacy.page_title'))?></title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..900;1,9..144,300..900&family=Instrument+Sans:ital,wght@0,400..700;1,400..700&family=JetBrains+Mono:wght@400;500;700&display=swap">
<link rel="stylesheet" href="style.css">
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' fill='%23c8442d'/%3E%3Ctext x='50%25' y='58%25' font-family='serif' font-size='22' fill='%23f4efe6' text-anchor='middle' font-weight='900'%3ER%3C/text%3E%3C/svg%3E">
<style>
    .terms-container { max-width: 780px; margin: 0 auto; padding: 60px 20px 80px; }
    .terms-header { margin-bottom: 48px; }
    .terms-header h1 {
        font-family: var(--font-display);
        font-size: clamp(28px, 4vw, 40px);
        font-weight: 800;
        margin: 0 0 8px;
        color: var(--ink);
    }
    .terms-meta { font-size: 14px; color: var(--muted); }
    .terms-section { margin-bottom: 36px; }
    .terms-section h2 {
        font-family: var(--font-display);
        font-size: 22px;
        font-weight: 700;
        color: var(--ink);
        margin: 0 0 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid var(--rule);
    }
    .terms-section p { color: var(--ink-soft); margin: 0 0 8px; }
    .terms-back { margin-top: 48px; padding-top: 24px; border-top: 1px solid var(--rule); }
    .terms-back a { color: var(--red); text-decoration: none; font-weight: 500; }
    .terms-back a:hover { text-decoration: underline; }
</style>
</head>
<body>

<header class="masthead">
    <div class="masthead-inner">
        <div class="masthead-left">
            <span class="issue"><?=h_pp($t('meta.issue'))?> <?=h_pp($issue)?></span>
            <span class="dot">·</span>
            <span class="date"><?=h_pp(date('j F Y'))?></span>
        </div>
        <a href="/" class="logo">
            <span class="logo-r">R</span><span>edsl</span>
        </a>
        <nav class="masthead-right">
            <a href="/#jak"><?=h_pp($t('nav.how_it_works'))?></a>
            <a href="/#cennik"><?=h_pp($t('nav.pricing'))?></a>
            <a href="/#kontakt"><?=h_pp($t('nav.contact'))?></a>
            <div class="lang-switcher">
                <?php foreach ($getLangUrls() as $code => $url): ?>
                    <a href="<?=h_pp($url)?>" class="lang-btn <?= $code === $lang ? 'lang-btn-active' : '' ?>" title="<?=h_pp($getLangName($code))?>"><?=h_pp(strtoupper($code))?></a>
                <?php endforeach; ?>
            </div>
        </nav>
    </div>
    <div class="rule"></div>
</header>

<div class="terms-container">
    <div class="terms-header">
        <h1><?=h_pp($t('privacy.heading'))?></h1>
        <p class="terms-meta"><?=h_pp($t('privacy.updated'))?>: <?=h_pp(date('j F Y'))?></p>
    </div>

    <div class="terms-section">
        <h2><?=h_pp($t('privacy.s1_title'))?></h2>
        <p><?=h_pp($t('privacy.s1_text'))?></p>
    </div>

    <div class="terms-section">
        <h2><?=h_pp($t('privacy.s2_title'))?></h2>
        <p><?=h_pp($t('privacy.s2_text'))?></p>
    </div>

    <div class="terms-section">
        <h2><?=h_pp($t('privacy.s3_title'))?></h2>
        <p><?=h_pp($t('privacy.s3_text'))?></p>
    </div>

    <div class="terms-section">
        <h2><?=h_pp($t('privacy.s4_title'))?></h2>
        <p><?=h_pp($t('privacy.s4_text'))?></p>
    </div>

    <div class="terms-section">
        <h2><?=h_pp($t('privacy.s5_title'))?></h2>
        <p><?=h_pp($t('privacy.s5_text'))?></p>
    </div>

    <div class="terms-back">
        <a href="/"><?=h_pp($t('privacy.back'))?></a>
    </div>
</div>

<footer class="colophon">
    <div class="container">
        <div class="colophon-bottom">
            <span>&copy; <?=h_pp((string)$year)?> REDSL &middot; <?=h_pp($t('meta.issue'))?> <?=h_pp($issue)?></span>
            <span class="dot">&middot;</span>
            <span>Polska &middot; UE</span>
        </div>
    </div>
</footer>

</body>
</html>
