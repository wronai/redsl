<?php
/**
 * ReDSL — Propozycje refaktoryzacji (SaaS Panel)
 * 
 * Użytkownik otrzymuje email z linkiem do tej strony.
 * Może wybrać które propozycje (tickety) chce zrealizować.
 * 
 * Format wyboru: "1, 3, 7, 12-15, 24" lub "wszystkie" lub "wszystko pod 15"
 */

declare(strict_types=1);

session_start();

// Demo data — w produkcji ładowane z bazy/API
$proposals = [
    ['id' => 1, 'title' => 'Refaktoryzacja klasy UserService', 'file' => 'src/services/UserService.php', 'effort' => 'M', 'lines' => 150, 'price' => 10, 'priority' => 1],
    ['id' => 2, 'title' => 'Ekstrakcja metod w PaymentController', 'file' => 'src/controllers/PaymentController.php', 'effort' => 'S', 'lines' => 80, 'price' => 10, 'priority' => 2],
    ['id' => 3, 'title' => 'Redukcja złożoności cyclomatycznej', 'file' => 'src/utils/Calculator.php', 'effort' => 'L', 'lines' => 320, 'price' => 10, 'priority' => 1],
    ['id' => 4, 'title' => 'Usunięcie duplikacji kodu w walidacjach', 'file' => 'src/validators/', 'effort' => 'M', 'lines' => 200, 'price' => 10, 'priority' => 2],
    ['id' => 5, 'title' => 'Poprawa nazewnictwa i konwencji', 'file' => 'src/models/', 'effort' => 'S', 'lines' => 120, 'price' => 10, 'priority' => 3],
    ['id' => 6, 'title' => 'Refaktoryzacja repository pattern', 'file' => 'src/repositories/', 'effort' => 'L', 'lines' => 450, 'price' => 10, 'priority' => 1],
    ['id' => 7, 'title' => 'Ekstrakcja interfejsów', 'file' => 'src/contracts/', 'effort' => 'M', 'lines' => 180, 'price' => 10, 'priority' => 2],
    ['id' => 8, 'title' => 'Usunięcie martwego kodu', 'file' => 'src/legacy/', 'effort' => 'S', 'lines' => 90, 'price' => 10, 'priority' => 3],
];

// Handle form submission
$message = '';
$selectedIds = [];
$totalPrice = 0;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $selection = $_POST['selection'] ?? '';
    $customInput = trim($_POST['custom_input'] ?? '');
    
    // Parse selection
    if ($selection === 'all') {
        $selectedIds = array_column($proposals, 'id');
        $totalPrice = count($proposals) * 10;
    } elseif ($selection === 'under_15') {
        // All under 15 PLN — all are 10 PLN so same as all
        $selectedIds = array_column($proposals, 'id');
        $totalPrice = count($proposals) * 10;
    } elseif ($selection === 'custom' && $customInput) {
        // Parse "1, 3, 7, 12-15, 24"
        $selectedIds = parseSelection($customInput);
        $totalPrice = count($selectedIds) * 10;
    }
    
    if (!empty($selectedIds)) {
        $message = sprintf(
            "Wybrano %d ticketów. Razem: %d zł. Potwierdzenie wysłano na email.",
            count($selectedIds),
            $totalPrice
        );
        // W produkcji: zapis do bazy, wysłanie email potwierdzającego
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
$effortLabel = ['S' => 'S (~2h)', 'M' => 'M (~4h)', 'L' => 'L (~8h)'];
?>
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Propozycje refaktoryzacji — ReDSL</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        header {
            background: white;
            border-radius: 12px;
            padding: 24px 32px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        h1 {
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
            grid-template-columns: 40px 1fr 100px 80px 60px;
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
        
        .btn {
            padding: 14px 32px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-primary {
            background: #3b82f6;
            color: white;
        }
        .btn-primary:hover {
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
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Propozycje refaktoryzacji</h1>
            <p class="subtitle">Projekt: <strong>my-app</strong> · Otrzymano: 19 kwietnia 2026</p>
        </header>
        
        <?php if ($message): ?>
        <div class="alert"><?= h($message) ?></div>
        <?php endif; ?>
        
        <form method="post">
            <div class="instructions">
                <strong>Jak wybrać:</strong>
                <ul style="margin: 8px 0; padding-left: 20px;">
                    <li><code>1, 3, 7</code> — wybierz konkretne numery (oddziel przecinkami)</li>
                    <li><code>12-15</code> — zakres od 12 do 15 włącznie</li>
                    <li><code>wszystkie</code> — cała lista</li>
                    <li><code>wszystko pod 15</code> — wszystkie tickety (każdy po 10 zł)</li>
                </ul>
            </div>
            
            <div class="selection-panel">
                <div class="selection-title">Wybierz opcje</div>
                
                <label class="option-row">
                    <input type="radio" name="selection" value="all" checked>
                    <span class="option-label">Wszystkie propozycje</span>
                    <span class="option-price"><?= count($proposals) * 10 ?> zł</span>
                </label>
                
                <label class="option-row">
                    <input type="radio" name="selection" value="under_15">
                    <span class="option-label">Wszystko poniżej 15 zł (czyli wszystkie)</span>
                    <span class="option-price"><?= count($proposals) * 10 ?> zł</span>
                </label>
                
                <label class="option-row" style="flex-wrap: wrap;">
                    <input type="radio" name="selection" value="custom">
                    <span class="option-label" style="flex: 0 0 auto;">Własny wybór:</span>
                    <input type="text" name="custom_input" class="custom-input" placeholder="np. 1, 3, 7, 12-15, 24" style="flex: 1; min-width: 200px;">
                </label>
                <p class="hint">Każdy ticket: <strong>10 zł</strong> (do 500 LOC, mergowane PR-y)</p>
            </div>
            
            <div class="proposals-list">
                <div class="proposal-item" style="background: #fafafa; font-weight: 600; color: #666;">
                    <div class="prop-id">ID</div>
                    <div class="prop-title">Tytuł / Plik</div>
                    <div class="prop-effort">Wysiłek</div>
                    <div class="prop-lines">Linie</div>
                    <div class="prop-price">Cena</div>
                </div>
                <?php foreach ($proposals as $p): ?>
                <div class="proposal-item">
                    <div class="prop-id"><?= $p['id'] ?></div>
                    <div>
                        <div class="prop-title"><?= h($p['title']) ?></div>
                        <div class="prop-file"><?= h($p['file']) ?></div>
                    </div>
                    <div class="prop-effort" title="S=~2h, M=~4h, L=~8h"><?= $effortLabel[$p['effort']] ?></div>
                    <div class="prop-lines">~<?= $p['lines'] ?></div>
                    <div class="prop-price"><?= $p['price'] ?> zł</div>
                </div>
                <?php endforeach; ?>
            </div>
            
            <div class="summary-bar">
                <div>
                    <div class="summary-text">Wybierz opcje powyżej</div>
                    <div class="summary-note">Płatność po zmergeowaniu PR. NDA podpisujemy przed skanem.</div>
                </div>
                <button type="submit" class="btn btn-primary">Potwierdź wybór →</button>
            </div>
        </form>
        
        <p style="text-align: center; margin-top: 30px; font-size: 13px; color: #888;">
            Masz pytania? <a href="/#kontakt" style="color: #3b82f6;">Napisz do nas</a> lub 
            <a href="mailto:kontakt@redsl.io" style="color: #3b82f6;">kontakt@redsl.io</a>
        </p>
    </div>
</body>
</html>
