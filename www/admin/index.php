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
    <title>REDSL Panel — Dashboard</title>
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0; 
            padding: 20px; 
            background: #f5f5f5;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { 
            background: #1a1a2e; 
            color: white; 
            padding: 20px; 
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .header h1 { margin: 0; font-size: 24px; }
        .header .nav { margin-top: 10px; }
        .header .nav a { 
            color: #64b5f6; 
            text-decoration: none; 
            margin-right: 20px;
        }
        .header .nav a:hover { text-decoration: underline; }
        
        .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { 
            background: white; 
            padding: 20px; 
            border-radius: 8px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .card .number { font-size: 36px; font-weight: bold; color: #1a1a2e; }
        .card .label { color: #666; font-size: 14px; margin-top: 5px; }
        .card.active .number { color: #4caf50; }
        .card.pending .number { color: #ff9800; }
        .card.lead .number { color: #2196f3; }
        
        .section { 
            background: white; 
            padding: 20px; 
            border-radius: 8px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .section h2 { margin-top: 0; font-size: 18px; border-bottom: 2px solid #eee; padding-bottom: 10px; }
        
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { font-weight: 600; color: #666; font-size: 12px; text-transform: uppercase; }
        tr:hover { background: #f9f9f9; }
        .badge { 
            padding: 4px 12px; 
            border-radius: 12px; 
            font-size: 12px; 
            font-weight: 500;
        }
        .badge.active { background: #e8f5e9; color: #2e7d32; }
        .badge.lead { background: #e3f2fd; color: #1565c0; }
        .badge.suspended { background: #ffebee; color: #c62828; }
        
        .btn { 
            display: inline-block; 
            padding: 10px 20px; 
            background: #1a1a2e; 
            color: white; 
            text-decoration: none; 
            border-radius: 4px; 
            font-size: 14px;
        }
        .btn:hover { background: #2a2a4e; }
        
        .empty-state { text-align: center; padding: 40px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>REDSL Panel</h1>
            <div class="nav">
                <a href="index.php">Dashboard</a>
                <a href="clients.php">Klienci</a>
                <a href="contracts.php">Umowy</a>
                <a href="projects.php">Projekty</a>
                <a href="scans.php">Skany</a>
                <a href="invoices.php">Faktury</a>
            </div>
        </div>
        
        <div class="cards">
            <div class="card">
                <div class="number"><?= htmlspecialchars((string)$totalClients) ?></div>
                <div class="label">Wszystkich klientów</div>
            </div>
            <div class="card active">
                <div class="number"><?= htmlspecialchars((string)($clientCounts['active'] ?? 0)) ?></div>
                <div class="label">Aktywnych</div>
            </div>
            <div class="card lead">
                <div class="number"><?= htmlspecialchars((string)($clientCounts['lead'] ?? 0)) ?></div>
                <div class="label">Leadów</div>
            </div>
            <div class="card pending">
                <div class="number">0</div>
                <div class="label">Oczekujących skanów</div>
            </div>
        </div>
        
        <div class="section">
            <h2>Ostatni klienci</h2>
            <?php if (empty($recentClients)): ?>
                <div class="empty-state">
                    <p>Brak klientów w systemie.</p>
                    <a href="clients.php?action=new" class="btn">Dodaj pierwszego klienta</a>
                </div>
            <?php else: ?>
                <table>
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
                            <td><?= htmlspecialchars($client['company_name']) ?></td>
                            <td><?= htmlspecialchars($client['contact_email']) ?></td>
                            <td><span class="badge <?= htmlspecialchars($client['status']) ?>"><?= htmlspecialchars($client['status']) ?></span></td>
                            <td><?= htmlspecialchars($client['created_at']) ?></td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
                <p style="margin-top: 15px;"><a href="clients.php" class="btn">Zobacz wszystkich</a></p>
            <?php endif; ?>
        </div>
        
        <div class="section">
            <h2>Szybkie akcje</h2>
            <p>
                <a href="clients.php?action=new" class="btn">+ Nowy klient</a>
                <a href="projects.php?action=new" class="btn">+ Nowy projekt</a>
                <a href="../lib/Migration/run.php" class="btn" style="background: #4caf50;">Uruchom migracje</a>
            </p>
        </div>
    </div>
</body>
</html>
