<?php
/**
 * REDSL — Client Panel (after GitHub login)
 *
 * Requires active github_user session (set by index.php).
 */

declare(strict_types=1);
session_start();

// Require authentication
if (empty($_SESSION['github_user']['login'])) {
    header('Location: /?err=login_required');
    exit;
}

// Handle logout
if (($_GET['action'] ?? '') === 'logout') {
    session_destroy();
    header('Location: /');
    exit;
}

$user = $_SESSION['github_user'];
$loginTime = date('Y-m-d H:i:s', $user['logged_at'] ?? time());

function h(string $s): string {
    return htmlspecialchars($s, ENT_QUOTES | ENT_HTML5, 'UTF-8');
}
?>
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Panel klienta — REDSL</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,500;0,9..144,900;1,9..144,400;1,9..144,500&family=Instrument+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/panel.css">
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' fill='%23c8442d'/%3E%3Ctext x='50%25' y='58%25' font-family='serif' font-size='22' fill='%23f4efe6' text-anchor='middle' font-weight='900'%3ER%3C/text%3E%3C/svg%3E">
    <style>
        .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
        @media (max-width: 640px) { .two-col { grid-template-columns: 1fr; } }
    </style>
</head>
<body>

<header class="topbar">
    <a href="/" class="topbar-brand">
        <span class="topbar-logo"><span class="logo-r">R</span>edsl</span>
        <span class="topbar-label">Panel klienta</span>
    </a>
    <div class="topbar-right">
        <a href="/">Strona główna</a>
        <a href="/propozycje">Propozycje</a>
        <div class="user-chip">
            <?php if ($user['avatar_url']): ?>
                <img src="<?= h($user['avatar_url']) ?>" alt="">
            <?php endif; ?>
            <span class="username">@<?= h($user['login']) ?></span>
        </div>
        <a href="?action=logout" class="topbar-logout">Wyloguj</a>
    </div>
</header>

<div class="panel-layout">
    <nav class="sidebar">
        <div class="sidebar-section">
            <span class="sidebar-section-label">Konto</span>
            <ul class="sidebar-nav">
                <li><a href="/client/" class="active"><span class="nav-icon">◈</span> Dashboard</a></li>
                <li><a href="/propozycje"><span class="nav-icon">↗</span> Propozycje</a></li>
            </ul>
        </div>
        <div class="sidebar-section">
            <span class="sidebar-section-label">Usługa</span>
            <ul class="sidebar-nav">
                <li><a href="/#jak"><span class="nav-icon">⚙</span> Jak to działa</a></li>
                <li><a href="/#cennik"><span class="nav-icon">◎</span> Cennik</a></li>
                <li><a href="mailto:kontakt@redsl.io"><span class="nav-icon">✉</span> Kontakt</a></li>
            </ul>
        </div>
    </nav>

    <main class="panel-main">
        <div class="alert alert-success">
            <span class="alert-icon">✓</span>
            <span>Zalogowano przez GitHub jako <strong>@<?= h($user['login']) ?></strong></span>
        </div>

        <div class="page-header">
            <h1 class="page-title">
                Witaj<?= $user['name'] ? ', <em>' . h(explode(' ', $user['name'])[0]) . '</em>' : '' ?>
            </h1>
        </div>

        <div class="stats-row">
            <div class="stat-card">
                <div class="stat-num">0</div>
                <div class="stat-label">Skany</div>
            </div>
            <div class="stat-card accent">
                <div class="stat-num">0</div>
                <div class="stat-label">Tickety</div>
            </div>
            <div class="stat-card green">
                <div class="stat-num">0</div>
                <div class="stat-label">PR-y</div>
            </div>
            <div class="stat-card">
                <div class="stat-num">0 zł</div>
                <div class="stat-label">Zafakturowane</div>
            </div>
        </div>

        <div class="two-col">
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">Profil GitHub</h2>
                    <a href="<?= h($user['html_url']) ?>" target="_blank" rel="noopener" class="btn btn-sm btn-ghost">github.com ↗</a>
                </div>
                <div class="card-body">
                    <?php if ($user['avatar_url']): ?>
                    <div class="profile-block">
                        <img src="<?= h($user['avatar_url']) ?>" alt="" class="profile-avatar">
                        <div>
                            <p class="profile-name"><?= h($user['name'] ?: $user['login']) ?></p>
                            <p class="profile-meta">@<?= h($user['login']) ?></p>
                        </div>
                    </div>
                    <?php endif; ?>
                    <dl class="kv">
                        <?php if ($user['email']): ?>
                        <dt>Email</dt>
                        <dd><?= h($user['email']) ?></dd>
                        <?php endif; ?>
                        <?php if ($user['company']): ?>
                        <dt>Firma</dt>
                        <dd><?= h($user['company']) ?></dd>
                        <?php endif; ?>
                        <dt>Repozytoria</dt>
                        <dd><?= (int)$user['public_repos'] ?> publicznych</dd>
                        <dt>Zalogowano</dt>
                        <dd><?= h($loginTime) ?></dd>
                    </dl>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">Co dalej?</h2>
                </div>
                <div class="card-body">
                    <ul class="steps-list">
                        <li class="done">
                            <span class="step-num">✓</span>
                            <span class="step-text">Zalogowałeś się przez GitHub</span>
                        </li>
                        <li>
                            <span class="step-num">2</span>
                            <span class="step-text">Uruchomimy automatyczny skan Twoich repo (w 24h)</span>
                        </li>
                        <li>
                            <span class="step-num">3</span>
                            <span class="step-text">Raport z propozycjami na <?= h($user['email'] ?: 'Twój email') ?></span>
                        </li>
                        <li>
                            <span class="step-num">4</span>
                            <span class="step-text">Wybierasz tickety (10–100 zł/szt.)</span>
                        </li>
                        <li>
                            <span class="step-num">5</span>
                            <span class="step-text">Tworzymy PR-y — Ty akceptujesz i mergujesz</span>
                        </li>
                        <li>
                            <span class="step-num">6</span>
                            <span class="step-text">Faktura miesięcznie za zmergowane tickety</span>
                        </li>
                    </ul>
                </div>
            </div>
        </div>

        <div style="padding: 20px 0; border-top: 1px solid var(--rule); font-family: var(--font-mono); font-size: 12px; color: var(--muted); display: flex; gap: 24px; flex-wrap: wrap;">
            <a href="mailto:kontakt@redsl.io">kontakt@redsl.io</a>
            <a href="?action=logout">Wyloguj się</a>
            <a href="/">Strona główna</a>
        </div>
    </main>
</div>

</body>
</html>
