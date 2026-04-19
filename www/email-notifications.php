<?php
/**
 * ReDSL — System powiadomień email (Backend)
 * 
 * Generuje i wysyła email z propozycjami refaktoryzacji.
 * Link w emailu prowadzi do /propozycje.php z tokenem dostępu.
 */

declare(strict_types=1);

/**
 * Generuje treść emailu z linkiem do wyboru propozycji.
 */
function generateProposalEmail(string $projectName, array $proposals, string $token): string {
    $baseUrl = $_ENV['APP_URL'] ?? 'https://redsl.io';
    $link = $baseUrl . '/propozycje.php?token=' . urlencode($token);
    $count = count($proposals);
    $total = $count * 10;
    
    $proposalList = '';
    foreach (array_slice($proposals, 0, 5) as $p) {
        $proposalList .= sprintf(
            "[%d] %s (%s, ~%d LOC)\n",
            $p['id'],
            $p['title'],
            $p['effort'],
            $p['lines']
        );
    }
    if ($count > 5) {
        $proposalList .= sprintf("\n...i %d więcej\n", $count - 5);
    }
    
    return <<<EMAIL
ReDSL — Analiza kodu gotowa: {$projectName}

Zidentyfikowaliśmy {$count} obszarów do refaktoryzacji.

{$proposalList}

CENA: 10 zł za ticket (do 500 LOC, po zmergeowaniu PR)
RAZEM: {$total} zł za wszystkie

WYBIERZ KTÓRE CHCESZ:
{$link}

Jak wybrać?
• "wszystkie" — cała lista
• "1, 3, 7" — konkretne numery
• "12-15" — zakres
• "wszystko pod 15" — filtr ceny

Bezpieczeństwo:
• NDA podpisujemy przed skanem
• Dostęp read-only, kod nie wychodzi z Twojej infrastruktury
• Płacisz dopiero po akceptacji PR

---
ReDSL · Refaktoryzacja za 10 zł
https://redsl.io
EMAIL;
}

/**
 * Wysyła email (w produkcji: użyć Mailgun, SendGrid, etc.)
 */
function sendProposalEmail(string $to, string $subject, string $body): bool {
    $from = $_ENV['MAIL_FROM'] ?? 'kontakt@redsl.io';
    $headers = [
        'From: ' . $from,
        'Reply-To: ' . $from,
        'Content-Type: text/plain; charset=UTF-8',
    ];
    
    // W produkcji: integracja z API mailowym
    // Na teraz: logujemy do pliku
    $log = date('c') . " | TO: {$to} | SUBJECT: {$subject}\n";
    file_put_contents(__DIR__ . '/email-log.txt', $log, FILE_APPEND | LOCK_EX);
    
    return mail($to, $subject, $body, implode("\r\n", $headers));
}

/**
 * Generuje unikalny token dostępu (w produkcji: JWT lub signed URL)
 */
function generateAccessToken(string $projectId, string $email): string {
    $data = json_encode(['project' => $projectId, 'email' => $email, 'exp' => time() + 86400]);
    $secret = $_ENV['TOKEN_SECRET'] ?? bin2hex(random_bytes(16));
    $signature = hash_hmac('sha256', $data, $secret);
    return base64_encode($data) . '.' . $signature;
}

/**
 * Weryfikuje token (w produkcji: pełna walidacja JWT)
 */
function verifyAccessToken(string $token): ?array {
    $parts = explode('.', $token);
    if (count($parts) !== 2) return null;
    
    $data = json_decode(base64_decode($parts[0]), true);
    if (!$data || ($data['exp'] ?? 0) < time()) return null;
    
    return $data;
}

// Demo endpoint — w produkcji: webhook z systemu analizy kodu
if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_GET['demo'] ?? '') === 'send') {
    $email = $_POST['email'] ?? 'test@example.com';
    $project = $_POST['project'] ?? 'Demo Project';
    
    $token = generateAccessToken('demo-123', $email);
    
    $proposals = [
        ['id' => 1, 'title' => 'Refaktoryzacja klasy UserService', 'effort' => 'M', 'lines' => 150],
        ['id' => 2, 'title' => 'Ekstrakcja metod w PaymentController', 'effort' => 'S', 'lines' => 80],
        ['id' => 3, 'title' => 'Redukcja złożoności cyclomatycznej', 'effort' => 'L', 'lines' => 320],
    ];
    
    $body = generateProposalEmail($project, $proposals, $token);
    $sent = sendProposalEmail($email, "ReDSL — Propozycje refaktoryzacji: {$project}", $body);
    
    header('Content-Type: application/json');
    echo json_encode(['sent' => $sent, 'token' => $token, 'preview' => $body]);
    exit;
}
