<?php
/**
 * ReDSL Marketing Hub - Cold Email & LinkedIn Outreach Generator
 * 
 * Features:
 * - Repo scan via ReDSL API
 * - Personalized cold email generation for 3 buyer types
 * - LinkedIn post templates
 * - GitHub outreach templates
 * - Follow-up sequences
 */

declare(strict_types=1);

// Configuration
$REDSL_API = getenv('REDSL_API_URL') ?: 'http://localhost:8001';

// Helper function to call ReDSL API
function callRedslApi(string $endpoint, array $payload): array {
    global $REDSL_API;
    
    $url = $REDSL_API . $endpoint;
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 120,
        CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => json_encode($payload),
        CURLOPT_FAILONERROR => false,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_SSL_VERIFYHOST => 0,
    ]);
    $resp = curl_exec($ch);
    $curlError = curl_error($ch);
    $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($resp === false) {
        return [
            'ok' => false, 
            'code' => 0, 
            'data' => ['error' => 'CURL Error: ' . $curlError, 'url' => $url],
            'curl_error' => $curlError
        ];
    }
    
    $decoded = json_decode($resp ?: '{}', true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        return [
            'ok' => false, 
            'code' => $code, 
            'data' => ['error' => 'JSON decode error: ' . json_last_error_msg(), 'response' => substr($resp, 0, 500)],
            'raw_response' => $resp
        ];
    }
    
    return ['ok' => $code >= 200 && $code < 300, 'code' => $code, 'data' => $decoded];
}

// Template definitions
$BUYER_TEMPLATES = [
    'tech_lead' => [
        'title' => 'Tech Lead - Code Review Bottleneck',
        'subject' => 'Znalazlem 3 rzeczy w [repo] ktore spowalniaja Wasz development',
        'body' => "Czesc [imie],

Przejrzalem Wasz projekt [repo-link].
Znalazlem kilka rzeczy, ktore prawdopodobnie kosztuja Was czas przy kazdej zmianie:

{issues}

Moge naprawic kazda z tych rzeczy jako osobny PR.
Placisz tylko za te, ktore zaakceptujesz i zmergeujesz. Odrzucony PR = 0 zl.

Jesli chcesz zobaczyc konkretne propozycje - napisz, przygotuje w 24h.

[imie]"
    ],
    'ceo' => [
        'title' => 'CEO/Founder - Team Productivity',
        'subject' => 'Wasz projekt [nazwa] - znalazlem cos co spowalnia Wasz team',
        'body' => "Czesc [imie],

Przejrzalem Wasz kod na GitHubie.
Mam wrazenie, ze Wasi deweloperzy traca sporo czasu na sprzatanie zamiast budowania nowych funkcji.

Dostarczam PR-y ktore to naprawiaja. Placicie tylko za zmergowane - zero ryzyka.

Moge zaczac od darmowego skanu i pokazac Wam co znalazlem.

Chcecie?

[imie]"
    ],
    'pm_agency' => [
        'title' => 'PM Agencji - Klient Reporting',
        'subject' => 'Jak pokazujecie klientom postep w jakosci kodu?',
        'body' => "Czesc [imie],

Prowadzicie projekty dla klientow - prawdopodobnie znacie ten moment: klient pyta o postep, developer mowi 'to legacy, trudno powiedziec ile zajmie'.

Mamy narzedzie ktore to zmienia:
- Kazda zmiana ma metryki przed i po
- Trend jakosci widoczny dla klienta
- PR-y z dokumentacja

PM moze powiedziec: 'dlug techniczny z poprzednich 2 lat zmniejszyl sie o 40%, tempo deliverables wzrosnie w Q3' - i poprzec to liczbami.

Czy to cos czego szukacie?
Moge przygotowac przykladowy raport z jednego Waszego projektu - za 0 zl.

[imie]"
    ]
];

$LINKEDIN_TEMPLATES = [
    'pain_hook' => [
        'title' => 'Hook na bol - Policz to uczciwie',
        'content' => "Policz to uczciwie.

Ile godzin Twoj senior spedzil w tym tygodniu naprawiajac to, co LLM lub junior narobil - zamiast budowac nowe funkcje?

Pomnoz przez jego stawke godzinowa.
To jest miesieczny koszt nieuporzadkowanego kodu.

W wiekszosci malych firm IT: 5 000-15 000 zl miesiecznie.
Nikt tego nie liczy. Wszyscy to czuja.

---

My robimy to inaczej: dostarczamy PR-y ktore ten czas odzyskuja. Placisz tylko za zmergowane. ~200 zl miesiecznie.

Jesli chcesz zobaczyc jak to wyglada na Twoim repo - napisz w komentarzu lub DM."
    ],
    'ai_contrarian' => [
        'title' => 'Kontrintuicja o AI - LLM to gaz',
        'content' => "Uzywasz GitHub Copilot? Cursor? ChatGPT do kodu?

Dobra wiadomosc: piszecie szybciej niz kiedykolwiek.
Zla wiadomosc: nikt nie widzi calosci.

LLM generuje kod lokalnie - na podstawie promptu, bez kontekstu calego projektu. Duplikaty powstaja w roznych plikach. Zaleznosci rosna. Funkcje puchna.

Przez rok takie tempo to 3x wiecej kodu i 2x wiecej czasu na kazda zmiane.

---

LLM to gaz. Ktos musi pilnowac ukladu hamulcowego.

Tym kims moze byc system, nie czlowiek.
Robimy to dla malych firm IT - od 200 zl miesiecznie."
    ],
    'case_study' => [
        'title' => 'Case Study Format - Przed/Po',
        'content' => "Co sie dzieje z projektem po 2 latach bez refaktoryzacji:

[PLIK] plik server.py: 800 linii, funkcja z CC=19
[MODUL] modul api.py: importowany w 23 miejscach
[BLOK] senior mowi: 'tego nie ruszaj, nie wiadomo co wybuchnie'
[BLAD] junior boi sie commitowac
[CZAS] code review trwa 3h zamiast 30min

Znasz to?

---

W zeszlym miesiacu pracowalismy z projektem dokladnie w tym stanie.

6 tygodni, 24 PR-y, zadnej zmiany logiki biznesowej.

Efekt:
[OK] CC srednie: 14 -> 9
[OK] code review: 3h -> 50min  
[OK] funkcje ktorych 'nie ruszamy': 3 -> 0
[PLN] Koszt: 240 zl.

---

Jesli masz projekt ktory wyglada podobnie - napisz. Zrobimy darmowy skan i pokazemy co znalezlismy."
    ]
];

$GITHUB_TEMPLATE = [
    'title' => 'GitHub Cold Outreach - OSS Project',
    'issue_title' => 'Found some complexity issues that could slow down future contributions',
    'body' => "Hi,

I was going through the codebase and noticed a few things that might make future contributions harder:

{issues}

I can prepare 2-3 PRs that address these without touching any business logic.
No cost - I'm building tooling around automated refactoring and use OSS projects for validation.

If you're interested, let me know and I'll open draft PRs for review."
];

$FOLLOW_UP_TEMPLATE = [
    'subject' => 'Re: [poprzedni temat]',
    'body' => "Czesc [imie],

Krotko - masz 2 minuty?

Przygotowalem wstepna liste 5 rzeczy w [repo] ktore mozna naprawic bez ryzyka i bez zmiany logiki biznesowej.

Wrzucam jesli chcesz zobaczyc. Jesli nie - zaden problem.

[imie]"
];

// Helper functions
function formatIssuesForEmail(array $analysis): string {
    $lines = [];
    $alerts = array_slice($analysis['alerts'] ?? [], 0, 3);
    
    foreach ($alerts as $alert) {
        if ($alert['type'] === 'cc_exceeded') {
            $lines[] = "• Funkcja `{$alert['name']}` ma zlozonosc CC={$alert['value']} (norma to max 10) - kazda zmiana to ryzyko";
        }
    }
    
    // Add file count line
    $files = $analysis['total_files'] ?? 0;
    $lines[] = "• Projekt ma {$files} plikow - typowy bottleneck przy code review";
    
    return implode("\n", $lines);
}

function formatIssuesForGitHub(array $analysis): string {
    $lines = [];
    $alerts = array_slice($analysis['alerts'] ?? [], 0, 3);
    
    foreach ($alerts as $alert) {
        if ($alert['type'] === 'cc_exceeded') {
            $lines[] = "- `{$alert['name']}` has cyclomatic complexity ~{$alert['value']} - hard to modify safely";
        }
    }
    
    $files = $analysis['total_files'] ?? 0;
    if ($files > 50) {
        $lines[] = "- {$files} files total - this often becomes a bottleneck in code review";
    }
    
    return implode("\n", $lines);
}

// Handle form submissions
$result = null;
$error = null;
$apiResult = null;
$generatedTemplates = [];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $repoUrl = $_POST['repo_url'] ?? '';
    $buyerType = $_POST['buyer_type'] ?? 'tech_lead';
    $contactName = $_POST['contact_name'] ?? 'Tam';
    $senderName = $_POST['sender_name'] ?? 'Tomek';
    
    if ($repoUrl) {
        // Use new /scan/remote endpoint
        $apiResult = callRedslApi('/scan/remote', [
            'repo_url' => $repoUrl,
            'branch' => 'main',
            'depth' => 1
        ]);
        
        if ($apiResult['ok']) {
            $scanResult = $apiResult['data'];
            
            // Convert to analysis format expected by templates
            $analysis = [
                'total_files' => $scanResult['total_files'] ?? 0,
                'total_lines' => $scanResult['total_lines'] ?? 0,
                'avg_cc' => $scanResult['avg_cc'] ?? 0,
                'critical_count' => $scanResult['critical_count'] ?? 0,
                'alerts' => $scanResult['alerts'] ?? [],
                'top_issues' => $scanResult['top_issues'] ?? [],
            ];
            
            // Generate templates using top_issues from API
            $issuesEmail = formatIssuesForEmail($analysis);
            $issuesGitHub = formatIssuesForGitHub($analysis);
            
            $repoName = basename(parse_url($repoUrl, PHP_URL_PATH) ?: 'repo');
            
            // Generate all templates
            foreach ($BUYER_TEMPLATES as $key => $template) {
                $body = str_replace(
                    ['[repo]', '[repo-link]', '[imie]', "{issues}"],
                    [$repoName, $repoUrl, $contactName, $issuesEmail],
                    $template['body']
                );
                $subject = str_replace(
                    ['[repo]', '[nazwa]'],
                    [$repoName, $repoName],
                    $template['subject']
                );
                
                $generatedTemplates['email_' . $key] = [
                    'title' => $template['title'],
                    'subject' => $subject,
                    'body' => $body
                ];
            }
            
            // LinkedIn templates
            foreach ($LINKEDIN_TEMPLATES as $key => $template) {
                $generatedTemplates['linkedin_' . $key] = [
                    'title' => $template['title'],
                    'content' => $template['content']
                ];
            }
            
            // GitHub template
            $githubBody = str_replace(
                "{issues}",
                $issuesGitHub,
                $GITHUB_TEMPLATE['body']
            );
            $generatedTemplates['github_oss'] = [
                'title' => $GITHUB_TEMPLATE['title'],
                'issue_title' => $GITHUB_TEMPLATE['issue_title'],
                'body' => $githubBody
            ];
            
            // Follow-up
            $followupBody = str_replace(
                ['[repo]', '[imie]'],
                [$repoName, $contactName],
                $FOLLOW_UP_TEMPLATE['body']
            );
            $generatedTemplates['follow_up'] = [
                'title' => 'Follow-up (po 5 dniach)',
                'subject' => 'Re: ' . $generatedTemplates['email_' . $buyerType]['subject'],
                'body' => $followupBody
            ];
            
            $result = [
                'repo' => $repoUrl,
                'analysis' => $analysis,
                'templates' => $generatedTemplates
            ];
        } else {
            $error = 'API Error: ' . ($apiResult['data']['detail'] ?? $apiResult['data']['error'] ?? 'Unknown error');
        }
    }
}
?>
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ReDSL Marketing Hub - Cold Email & LinkedIn Outreach</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f7fa;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
            margin-bottom: 30px;
            border-radius: 12px;
        }
        header h1 { font-size: 2.5em; margin-bottom: 10px; }
        header p { font-size: 1.2em; opacity: 0.9; }
        
        .card {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .card h2 {
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            font-weight: 600;
            margin-bottom: 8px;
            color: #555;
        }
        input[type="text"], input[type="url"], select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input[type="text"]:focus, input[type="url"]:focus, select:focus {
            outline: none;
            border-color: #667eea;
        }
        
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            font-size: 18px;
            border-radius: 8px;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .metric {
            background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .metric-label {
            color: #666;
            margin-top: 5px;
        }
        
        .template-card {
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 0 8px 8px 0;
        }
        .template-card h4 {
            color: #667eea;
            margin-bottom: 10px;
        }
        .template-subject {
            background: #e3f2fd;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 10px;
            font-weight: 600;
        }
        .template-body {
            background: white;
            padding: 15px;
            border-radius: 4px;
            white-space: pre-wrap;
            font-family: monospace;
            font-size: 14px;
            border: 1px solid #e0e0e0;
        }
        
        .copy-btn {
            background: #4caf50;
            padding: 8px 20px;
            font-size: 14px;
            margin-top: 10px;
        }
        .copy-btn:hover {
            box-shadow: 0 3px 10px rgba(76, 175, 80, 0.3);
        }
        
        .error {
            background: #ffebee;
            color: #c62828;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .success {
            background: #e8f5e9;
            color: #2e7d32;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .tab {
            background: #e0e0e0;
            padding: 10px 20px;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .tab.active {
            background: #667eea;
            color: white;
        }
        .tab:hover:not(.active) {
            background: #d0d0d0;
        }
        
        .alerts-list {
            max-height: 300px;
            overflow-y: auto;
        }
        .alert-item {
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 4px;
            font-size: 14px;
        }
        .alert-critical { background: #ffebee; border-left: 3px solid #c62828; }
        .alert-warning { background: #fff3e0; border-left: 3px solid #ef6c00; }
        .alert-info { background: #e3f2fd; border-left: 3px solid #1976d2; }
        
        .linkedin-content {
            background: white;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            white-space: pre-wrap;
            line-height: 1.8;
        }
        
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>ReDSL Marketing Hub</h1>
            <p>Cold Email & LinkedIn Outreach Generator - Skanuj repo, generuj personalizowane wiadomosci</p>
        </header>
        
        <!-- Input Form -->
        <div class="card">
            <h2>🔍 Skanuj Repozytorium</h2>
            <form method="POST" action="">
                <div class="form-group">
                    <label for="repo_url">URL Repozytorium (GitHub)</label>
                    <input type="url" id="repo_url" name="repo_url" required 
                           placeholder="https://github.com/owner/repo"
                           value="<?= htmlspecialchars($_POST['repo_url'] ?? '') ?>">
                </div>
                
                <div class="form-group">
                    <label for="buyer_type">Typ Odbiorcy (glowny)</label>
                    <select id="buyer_type" name="buyer_type">
                        <option value="tech_lead" <?= ($_POST['buyer_type'] ?? '') === 'tech_lead' ? 'selected' : '' ?>>
                            Tech Lead - Code Review Bottleneck
                        </option>
                        <option value="ceo" <?= ($_POST['buyer_type'] ?? '') === 'ceo' ? 'selected' : '' ?>>
                            CEO/Founder - Team Productivity
                        </option>
                        <option value="pm_agency" <?= ($_POST['buyer_type'] ?? '') === 'pm_agency' ? 'selected' : '' ?>>
                            PM Agencji - Klient Reporting
                        </option>
                    </select>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div class="form-group">
                        <label for="contact_name">Imie Odbiorcy</label>
                        <input type="text" id="contact_name" name="contact_name" 
                               placeholder="Janek"
                               value="<?= htmlspecialchars($_POST['contact_name'] ?? '') ?>">
                    </div>
                    <div class="form-group">
                        <label for="sender_name">Twoje Imie</label>
                        <input type="text" id="sender_name" name="sender_name" 
                               placeholder="Tomek"
                               value="<?= htmlspecialchars($_POST['sender_name'] ?? '') ?>">
                    </div>
                </div>
                
                <button type="submit">Generuj Szablony Outreach</button>
            </form>
        </div>
        
        <?php if ($error): ?>
            <div class="error">
                <strong><?= htmlspecialchars($error) ?></strong>
                <?php if (isset($apiResult['code']) && $apiResult['code'] > 0): ?>
                    <br><small>HTTP Code: <?= $apiResult['code'] ?></small>
                <?php endif; ?>
                <?php if (isset($apiResult['curl_error']) && $apiResult['curl_error']): ?>
                    <br><small>CURL Error: <?= htmlspecialchars($apiResult['curl_error']) ?></small>
                <?php endif; ?>
                <?php if (isset($apiResult['data']['url'])): ?>
                    <br><small>URL: <?= htmlspecialchars($apiResult['data']['url']) ?></small>
                <?php endif; ?>
                <?php if (isset($apiResult['raw_response'])): ?>
                    <br><small>Raw Response: <?= htmlspecialchars(substr($apiResult['raw_response'], 0, 200)) ?></small>
                <?php endif; ?>
                <br><small>API Endpoint: <?= htmlspecialchars($REDSL_API) ?></small>
            </div>
        <?php endif; ?>
        
        <?php if ($result): ?>
            <div class="success">
                OK Skan zakonczony! Znaleziono <?= $result['analysis']['total_files'] ?? 0 ?> plikow, 
                <?= $result['analysis']['critical_count'] ?? 0 ?> krytycznych problemow.
            </div>
            
            <!-- Analysis Metrics -->
            <div class="card">
                <h2>📊 Metryki Repozytorium</h2>
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-value"><?= $result['analysis']['total_files'] ?></div>
                        <div class="metric-label">Pliki</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value"><?= number_format($result['analysis']['total_lines'] / 1000, 1) ?>k</div>
                        <div class="metric-label">Linii kodu</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value"><?= number_format($result['analysis']['avg_cc'], 1) ?></div>
                        <div class="metric-label">Srednia CC</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value"><?= $result['analysis']['critical_count'] ?></div>
                        <div class="metric-label">Krytyczne</div>
                    </div>
                </div>
                
                <h3 style="margin-top: 20px;">🔴 Top Problemy (do wykorzystania w emailu)</h3>
                <div class="alerts-list">
                    <?php 
                    $alerts = array_slice($result['analysis']['alerts'] ?? [], 0, 5);
                    foreach ($alerts as $alert): 
                        $class = $alert['severity'] >= 3 ? 'alert-critical' : ($alert['severity'] >= 2 ? 'alert-warning' : 'alert-info');
                    ?>
                        <div class="alert-item <?= $class ?>">
                            <strong><?= htmlspecialchars($alert['name']) ?></strong>
                            (CC=<?= $alert['value'] ?>, limit=<?= $alert['limit'] ?>)
                        </div>
                    <?php endforeach; ?>
                </div>
            </div>
            
            <!-- Generated Templates -->
            <div class="card">
                <h2>📧 Wygenerowane Szablony</h2>
                
                <div class="tabs">
                    <div class="tab active" onclick="showTab('email')">Cold Email</div>
                    <div class="tab" onclick="showTab('linkedin')">LinkedIn</div>
                    <div class="tab" onclick="showTab('github')">GitHub</div>
                    <div class="tab" onclick="showTab('followup')">Follow-up</div>
                </div>
                
                <!-- Email Templates -->
                <div id="email" class="tab-content">
                    <?php foreach (['tech_lead', 'ceo', 'pm_agency'] as $type): 
                        if (isset($result['templates']['email_' . $type])):
                            $tpl = $result['templates']['email_' . $type];
                    ?>
                        <div class="template-card">
                            <h4><?= $tpl['title'] ?></h4>
                            <div class="template-subject">Temat: <?= htmlspecialchars($tpl['subject']) ?></div>
                            <div class="template-body" id="email-<?= $type ?>"><?= htmlspecialchars($tpl['body']) ?></div>
                            <button class="copy-btn" onclick="copyToClipboard('email-<?= $type ?>')">📋 Kopiuj</button>
                        </div>
                    <?php endif; endforeach; ?>
                </div>
                
                <!-- LinkedIn Templates -->
                <div id="linkedin" class="tab-content hidden">
                    <?php foreach (['pain_hook', 'ai_contrarian', 'case_study'] as $type): 
                        if (isset($result['templates']['linkedin_' . $type])):
                            $tpl = $result['templates']['linkedin_' . $type];
                    ?>
                        <div class="template-card">
                            <h4><?= $tpl['title'] ?></h4>
                            <div class="linkedin-content" id="linkedin-<?= $type ?>"><?= htmlspecialchars($tpl['content']) ?></div>
                            <button class="copy-btn" onclick="copyToClipboard('linkedin-<?= $type ?>')">📋 Kopiuj</button>
                        </div>
                    <?php endif; endforeach; ?>
                </div>
                
                <!-- GitHub Template -->
                <div id="github" class="tab-content hidden">
                    <?php if (isset($result['templates']['github_oss'])): 
                        $tpl = $result['templates']['github_oss'];
                    ?>
                        <div class="template-card">
                            <h4><?= $tpl['title'] ?></h4>
                            <div class="template-subject">Issue Title: <?= htmlspecialchars($tpl['issue_title']) ?></div>
                            <div class="template-body" id="github-body"><?= htmlspecialchars($tpl['body']) ?></div>
                            <button class="copy-btn" onclick="copyToClipboard('github-body')">📋 Kopiuj</button>
                        </div>
                    <?php endif; ?>
                </div>
                
                <!-- Follow-up Template -->
                <div id="followup" class="tab-content hidden">
                    <?php if (isset($result['templates']['follow_up'])): 
                        $tpl = $result['templates']['follow_up'];
                    ?>
                        <div class="template-card">
                            <h4><?= $tpl['title'] ?></h4>
                            <div class="template-subject">Temat: <?= htmlspecialchars($tpl['subject']) ?></div>
                            <div class="template-body" id="followup-body"><?= htmlspecialchars($tpl['body']) ?></div>
                            <button class="copy-btn" onclick="copyToClipboard('followup-body')">📋 Kopiuj</button>
                        </div>
                    <?php endif; ?>
                </div>
            </div>
            
            <!-- Outreach Sequence -->
            <div class="card">
                <h2>📅 Sekwencja Outreach (14 dni)</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="background: #f5f7fa;">
                        <th style="padding: 12px; text-align: left; border-bottom: 2px solid #ddd;">Dzien</th>
                        <th style="padding: 12px; text-align: left; border-bottom: 2px solid #ddd;">Akcja</th>
                        <th style="padding: 12px; text-align: left; border-bottom: 2px solid #ddd;">Kanal</th>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border-bottom: 1px solid #eee;">1</td>
                        <td style="padding: 12px; border-bottom: 1px solid #eee;">Cold email z konkretnymi obserwacjami</td>
                        <td style="padding: 12px; border-bottom: 1px solid #eee;">Email</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border-bottom: 1px solid #eee;">2-3</td>
                        <td style="padding: 12px; border-bottom: 1px solid #eee;">LinkedIn post (case study / hook)</td>
                        <td style="padding: 12px; border-bottom: 1px solid #eee;">LinkedIn</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border-bottom: 1px solid #eee;">6</td>
                        <td style="padding: 12px; border-bottom: 1px solid #eee;">Follow-up email</td>
                        <td style="padding: 12px; border-bottom: 1px solid #eee;">Email</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border-bottom: 1px solid #eee;">12</td>
                        <td style="padding: 12px; border-bottom: 1px solid #eee;">Ostatni kontakt - krotki, bez presji</td>
                        <td style="padding: 12px; border-bottom: 1px solid #eee;">Email</td>
                    </tr>
                </table>
            </div>
        <?php endif; ?>
    </div>
    
    <script>
        function showTab(tabName) {
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(el => {
                el.classList.add('hidden');
            });
            // Show selected
            document.getElementById(tabName).classList.remove('hidden');
            
            // Update tab styles
            document.querySelectorAll('.tab').forEach(el => {
                el.classList.remove('active');
            });
            event.target.classList.add('active');
        }
        
        function copyToClipboard(elementId) {
            const text = document.getElementById(elementId).innerText;
            navigator.clipboard.writeText(text).then(() => {
                const btn = event.target;
                const originalText = btn.innerText;
                btn.innerText = 'OK Skopiowano!';
                btn.style.background = '#2196f3';
                setTimeout(() => {
                    btn.innerText = originalText;
                    btn.style.background = '#4caf50';
                }, 2000);
            });
        }
    </script>
</body>
</html>
