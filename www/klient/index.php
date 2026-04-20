<?php
/**
 * REDSL — Panel Klienta (po zalogowaniu przez GitHub)
 * 
 * Wymagana zalogowana sesja github_user (ustawiana przez index.php).
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
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0; padding: 0; background: #f4efe6; color: #2a1a0e; min-height: 100vh;
        }
        
        header.topbar {
            background: #2a1a0e; color: #f4efe6; padding: 16px 32px;
            display: flex; justify-content: space-between; align-items: center;
        }
        .logo { font-weight: 900; font-size: 20px; color: #c8442d; }
        .topbar-nav { display: flex; gap: 24px; align-items: center; }
        .topbar-nav a { color: #f4efe6; text-decoration: none; font-size: 14px; }
        .topbar-nav a:hover { color: #c8442d; }
        
        .user-chip {
            display: flex; align-items: center; gap: 12px;
            background: #3a2a1a; padding: 6px 12px; border-radius: 24px;
        }
        .user-chip img { width: 28px; height: 28px; border-radius: 50%; }
        .user-chip .username { font-size: 13px; font-weight: 600; }
        .logout { color: #c8442d; font-size: 12px; margin-left: 8px; text-decoration: none; }
        
        .container { max-width: 1000px; margin: 40px auto; padding: 0 24px; }
        
        .welcome { margin-bottom: 32px; }
        .welcome h1 { font-size: 32px; margin: 0 0 8px 0; color: #2a1a0e; }
        .welcome p { color: #6b5b4e; font-size: 16px; margin: 0; }
        
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 32px; }
        
        .card {
            background: white; padding: 24px; border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #e5dcc9;
        }
        .card h2 { font-size: 18px; margin: 0 0 16px 0; color: #2a1a0e; }
        
        dl { margin: 0; display: grid; grid-template-columns: 120px 1fr; gap: 10px 16px; }
        dt { color: #6b5b4e; font-size: 13px; }
        dd { margin: 0; font-weight: 500; font-size: 14px; }
        
        .alert {
            background: #c8442d; color: #f4efe6; padding: 16px 20px;
            border-radius: 8px; margin-bottom: 24px; display: flex;
            align-items: center; gap: 12px;
        }
        .alert.success { background: #2d7a3a; }
        
        .btn {
            display: inline-block; padding: 10px 20px; border-radius: 6px;
            text-decoration: none; font-weight: 600; font-size: 14px;
            background: #c8442d; color: white; border: none; cursor: pointer;
        }
        .btn:hover { background: #a5361f; }
        .btn.secondary { background: transparent; color: #2a1a0e; border: 1px solid #2a1a0e; }
        
        .steps { list-style: none; padding: 0; margin: 16px 0 0 0; }
        .steps li {
            padding: 12px 0 12px 40px; position: relative; border-bottom: 1px solid #f4efe6;
            font-size: 14px; color: #2a1a0e;
        }
        .steps li:last-child { border: none; }
        .steps li::before {
            content: attr(data-n); position: absolute; left: 0; top: 8px;
            width: 28px; height: 28px; border-radius: 50%; background: #c8442d;
            color: white; display: flex; align-items: center; justify-content: center;
            font-weight: 700; font-size: 13px;
        }
        .steps li.done::before { background: #2d7a3a; content: '✓'; }
        
        .stat { text-align: center; padding: 20px; }
        .stat-num { font-size: 32px; font-weight: 900; color: #c8442d; line-height: 1; }
        .stat-label { font-size: 12px; text-transform: uppercase; color: #6b5b4e; margin-top: 6px; }
        
        @media (max-width: 700px) {
            .grid { grid-template-columns: 1fr; }
            dl { grid-template-columns: 1fr; gap: 4px 0; }
            dt { margin-top: 12px; }
        }
    </style>
</head>
<body>

<header class="topbar">
    <a href="/" class="logo">R REDSL</a>
    <nav class="topbar-nav">
        <a href="/">Strona główna</a>
        <a href="/propozycje.php">Propozycje</a>
        <div class="user-chip">
            <?php if ($user['avatar_url']): ?>
                <img src="<?= h($user['avatar_url']) ?>" alt="">
            <?php endif; ?>
            <span class="username">@<?= h($user['login']) ?></span>
            <a href="?action=logout" class="logout">Wyloguj</a>
        </div>
    </nav>
</header>

<main class="container">
    <div class="alert success">
        <span>✓</span>
        <span>Zalogowano pomyślnie przez GitHub jako <strong>@<?= h($user['login']) ?></strong></span>
    </div>
    
    <section class="welcome">
        <h1>Witaj<?= $user['name'] ? ', ' . h(explode(' ', $user['name'])[0]) : '' ?>!</h1>
        <p>Tutaj zobaczysz status swoich skanów, propozycje refaktoryzacji i historię płatności.</p>
    </section>
    
    <div class="grid">
        <div class="card">
            <h2>👤 Twój profil GitHub</h2>
            <dl>
                <dt>Login</dt>
                <dd>@<?= h($user['login']) ?></dd>
                
                <?php if ($user['name']): ?>
                <dt>Imię i nazwisko</dt>
                <dd><?= h($user['name']) ?></dd>
                <?php endif; ?>
                
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
            <p style="margin-top: 16px;">
                <a href="<?= h($user['html_url']) ?>" target="_blank" rel="noopener" class="btn secondary">
                    Zobacz profil GitHub →
                </a>
            </p>
        </div>
        
        <div class="card">
            <h2>📊 Status</h2>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                <div class="stat">
                    <div class="stat-num">0</div>
                    <div class="stat-label">Skany</div>
                </div>
                <div class="stat">
                    <div class="stat-num">0</div>
                    <div class="stat-label">Tickety</div>
                </div>
                <div class="stat">
                    <div class="stat-num">0</div>
                    <div class="stat-label">PR-y</div>
                </div>
                <div class="stat">
                    <div class="stat-num">0 zł</div>
                    <div class="stat-label">Zafakturowane</div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="card" style="margin-bottom: 32px;">
        <h2>🚀 Co dalej?</h2>
        <ol class="steps">
            <li data-n="1" class="done">Zalogowałeś się przez GitHub</li>
            <li data-n="2">Uruchomimy automatyczny skan 3 Twoich repo (w ciągu 24h)</li>
            <li data-n="3">Otrzymasz raport z propozycjami refaktoryzacji na <?= h($user['email'] ?: 'Twój email') ?></li>
            <li data-n="4">Wybierasz które propozycje zaakceptować (cena: 10-100 zł/ticket)</li>
            <li data-n="5">My tworzymy PR-y, Ty akceptujesz i mergujemy do main</li>
            <li data-n="6">Miesięcznie dostajesz fakturę za zmergeowane tickety</li>
        </ol>
    </div>
    
    <div style="text-align: center; padding: 24px; color: #6b5b4e;">
        <p>Masz pytania? <a href="mailto:kontakt@redsl.io" style="color: #c8442d;">kontakt@redsl.io</a></p>
        <p style="font-size: 13px;">
            <a href="?action=logout" style="color: #6b5b4e;">Wyloguj się</a> · 
            <a href="/" style="color: #6b5b4e;">Strona główna</a>
        </p>
    </div>
</main>

</body>
</html>
