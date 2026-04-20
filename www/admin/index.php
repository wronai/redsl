<?php
declare(strict_types=1);

require __DIR__ . '/auth.php';
require __DIR__ . '/../lib/Database.php';
require __DIR__ . '/../lib/Repository/ClientRepository.php';

$db = Database::connection();
$clientsRepo = new ClientRepository($db);

// Get counts
$clientCounts = $clientsRepo->countByStatus();
$totalClients = array_sum($clientCounts);

// Get recent clients
$recentClients = $clientsRepo->list(limit: 5);

?>
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard — REDSL Admin</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,500;0,9..144,900;1,9..144,400;1,9..144,500&family=Instrument+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/panel.css">
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' fill='%23c8442d'/%3E%3Ctext x='50%25' y='58%25' font-family='serif' font-size='22' fill='%23f4efe6' text-anchor='middle' font-weight='900'%3ER%3C/text%3E%3C/svg%3E">
</head>
<body>

<header class="topbar">
    <a href="/admin/" class="topbar-brand">
        <span class="topbar-logo"><span class="logo-r">R</span>edsl</span>
        <span class="topbar-label">Admin</span>
    </a>
    <div class="topbar-right">
        <a href="/">Strona główna</a>
        <a href="logs.php">Logi</a>
    </div>
</header>

<div class="panel-layout">
    <nav class="sidebar">
        <div class="sidebar-section">
            <span class="sidebar-section-label">Panel</span>
            <ul class="sidebar-nav">
                <li><a href="index.php" class="active"><span class="nav-icon">◈</span> Dashboard</a></li>
                <li><a href="clients.php"><span class="nav-icon">◉</span> Klienci</a></li>
                <li><a href="contracts.php"><span class="nav-icon">◎</span> Umowy</a></li>
                <li><a href="projects.php"><span class="nav-icon">⬡</span> Projekty</a></li>
                <li><a href="scans.php"><span class="nav-icon">⟳</span> Skany</a></li>
                <li><a href="tickets.php"><span class="nav-icon">✦</span> Tickety</a></li>
                <li><a href="invoices.php"><span class="nav-icon">◈</span> Faktury</a></li>
            </ul>
        </div>
        <div class="sidebar-section">
            <span class="sidebar-section-label">System</span>
            <ul class="sidebar-nav">
                <li><a href="logs.php"><span class="nav-icon">⌘</span> Logi</a></li>
                <li><a href="../lib/Migration/run.php"><span class="nav-icon">↻</span> Migracje</a></li>
            </ul>
        </div>
    </nav>

    <main class="panel-main">
        <div class="page-header">
            <h1 class="page-title">Dashboard</h1>
            <div class="page-header-actions">
                <a href="clients.php?action=new" class="btn btn-sm">+ Nowy klient</a>
                <a href="projects.php?action=new" class="btn btn-sm btn-ghost">+ Nowy projekt</a>
            </div>
        </div>

        <div class="stats-row">
            <div class="stat-card">
                <div class="stat-num"><?= htmlspecialchars((string)$totalClients) ?></div>
                <div class="stat-label">Klientów</div>
            </div>
            <div class="stat-card green">
                <div class="stat-num"><?= htmlspecialchars((string)($clientCounts['active'] ?? 0)) ?></div>
                <div class="stat-label">Aktywnych</div>
            </div>
            <div class="stat-card accent">
                <div class="stat-num"><?= htmlspecialchars((string)($clientCounts['lead'] ?? 0)) ?></div>
                <div class="stat-label">Leadów</div>
            </div>
            <div class="stat-card yellow">
                <div class="stat-num">0</div>
                <div class="stat-label">Oczekujących skanów</div>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <h2 class="card-title">Ostatni klienci</h2>
                <a href="clients.php" class="btn btn-sm btn-ghost">Zobacz wszystkich →</a>
            </div>
            <?php if (empty($recentClients)): ?>
                <div class="empty-state">
                    <div class="empty-state-icon">◎</div>
                    <p>Brak klientów w systemie.</p>
                    <a href="clients.php?action=new" class="btn">+ Dodaj pierwszego klienta</a>
                </div>
            <?php else: ?>
                <div class="table-wrap">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Firma</th>
                                <th>Email</th>
                                <th>Status</th>
                                <th>Data dodania</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($recentClients as $client): ?>
                            <tr>
                                <td><a href="clients.php?action=edit&id=<?= (int)$client['id'] ?>"><?= htmlspecialchars($client['company_name']) ?></a></td>
                                <td><?= htmlspecialchars($client['contact_email']) ?></td>
                                <td><span class="badge badge-<?= htmlspecialchars($client['status']) ?>"><?= htmlspecialchars($client['status']) ?></span></td>
                                <td><?= htmlspecialchars($client['created_at']) ?></td>
                            </tr>
                            <?php endforeach; ?>
                        </tbody>
                    </table>
                </div>
            <?php endif; ?>
        </div>
    </main>
</div>

</body>
</html>
