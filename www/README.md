# REDSL Landing Page — Deployment

Landing page z panelem SaaS: `index.php` + `style.css` + `app.js` + panel konfiguracji + NDA + wybór propozycji + panel admina + baza MySQL. Działa na shared hostingu (PHP 8.1+) i przez Docker.

## Szybki start (lokalnie bez DB)

```bash
cd www
cp .env.example .env
# Edytuj .env — na razie wystarczy CONTACT_EMAIL
php -S localhost:8000
```

Otwórz `http://localhost:8000`. Formularz kontaktowy użyje lokalnego `mail()` — na komputerze prawdopodobnie nie wyśle nic, ale strona się wyrenderuje.

## Docker (zalecany)

### Produkcja

```bash
cd www
cp .env.example .env
# Uzupełnij .env — szczególnie DB_PASS, ENCRYPTION_KEY, CONTACT_EMAIL, GITHUB_*
docker compose up -d
```

Serwisy:
- **`app`** — PHP 8.3 / Apache na `http://localhost:8080`
- **`db`** — MySQL 8.0 (dane w named volume `db_data`, init z `./migrations/`)

### Dev z mock-GitHub OAuth

```bash
docker compose --profile dev up -d
```

Dodaje serwis **`mock-github`** na `http://localhost:8181` — symuluje GitHub OAuth bez prawdziwych credentiali. W `.env` ustaw:

```env
GITHUB_OAUTH_BASE=http://mock-github
GITHUB_API_BASE=http://mock-github

# opcjonalnie: API MCP do odsprzedaży subskrypcji miesięcznej
MCP_API_URL=http://mcp-api:9000
MCP_API_KEY=your-mcp-api-key
```

### Przebudowanie po zmianach kodu

```bash
docker compose build app && docker compose up -d app
```

### Logi

```bash
docker compose logs -f app
docker compose logs -f db
```

## Produkcja — shared hosting (np. polskie home.pl, cyberfolks, hekko)

1. **Wrzuć pliki przez FTP/SFTP** do katalogu public. Lista plików:
   - `index.php` — landing page
   - `style.css`, `app.js` — assets
   - `config-editor.php`, `config-api.php` — edytor + API konfiguracji
   - `proposals.php` — wybór ticketów (EN)
   - `propozycje.php` — wybór ticketów (PL)
   - `nda-form.php` — automatyczne NDA
   - `email-notifications.php` — wysyłka powiadomień
   - `polityka-prywatnosci.php`, `regulamin.php` — strony prawne
   - `admin/` — panel admina (chroniony Basic Auth)
   - `klient/` — panel klienta
   - `migrations/` — schemat bazy MySQL
   - `cron/` — zadania cykliczne
   - `.htaccess` — rewrite rules
   - `.env` *(stworzony z `.env.example`)*
2. **Uprawnienia na `.env`**: `chmod 600 .env` (tylko właściciel czyta).
3. **Sprawdź że `.env` nie jest widoczny** — odwiedź `https://twojadomena.pl/.env` — powinno być 403. Jeśli 200, twój hosting ignoruje `.htaccess` i musisz użyć innej metody (wynieść `.env` poza public lub rename).
4. **Email** — jeśli hosting wspiera `mail()` z twojej domeny, formularz będzie działać. Jeśli maile lądują w spamie, skonfiguruj SPF + DKIM w panelu DNS.
5. **HTTPS** — każdy nowoczesny hosting oferuje Let's Encrypt w panelu. Włącz i odkomentuj `Strict-Transport-Security` oraz blok "Force HTTPS" w `.htaccess`.

## Produkcja — własny VPS (nginx + PHP-FPM)

```nginx
server {
    listen 443 ssl http2;
    server_name twojadomena.pl;

    root /var/www/redsl-landing;
    index index.php;

    # Block .env and other sensitive files
    location ~ /\.(env|git|htaccess) {
        deny all;
        return 404;
    }

    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    location ~ \.php$ {
        include fastcgi_params;
        fastcgi_pass unix:/run/php/php8.2-fpm.sock;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
    }

    # Static assets cache
    location ~* \.(css|js|svg|png|jpg|woff2)$ {
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    ssl_certificate     /etc/letsencrypt/live/twojadomena.pl/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/twojadomena.pl/privkey.pem;

    # Security headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}

server {
    listen 80;
    server_name twojadomena.pl;
    return 301 https://$host$request_uri;
}
```

## Konfiguracja GitHub OAuth

Bez tego przycisk "Zaloguj przez GitHub" pokaże komunikat "OAuth jeszcze nie skonfigurowany" — formularz kontaktowy działa niezależnie, więc nie jest to blocker do uruchomienia strony.

### Kroki

1. Idź na https://github.com/settings/developers
2. **New OAuth App**
3. Wypełnij:
   - **Application name**: `REDSL Landing`
   - **Homepage URL**: `https://twojadomena.pl`
   - **Authorization callback URL**: `https://twojadomena.pl/`
     (to samo co `GITHUB_REDIRECT_URI` w `.env` — GitHub sam dopisze `?code=...&state=...`, `index.php` to wykryje)
4. **Register application**
5. Skopiuj **Client ID** → wklej w `.env` jako `GITHUB_CLIENT_ID`
6. **Generate a new client secret** → skopiuj → wklej jako `GITHUB_CLIENT_SECRET`
7. Restart PHP-FPM (VPS) lub wystarczy poczekać 1 minutę (shared hosting cache)

### Co dostaje strona po OAuth

- Login GitHub użytkownika
- Imię (jeśli ustawione publicznie)
- Email (jeśli publiczny lub w scope `user:email`)
- Firma (jeśli ustawiona)
- Liczba publicznych repo

Wysyłane na `CONTACT_EMAIL` jako notyfikacja. To jest lead — teraz twoja kolej skontaktować się z nimi i zeskanować ich top repo.

## Bezpieczeństwo — checklist przed publikacją

- [ ] `.env` ma `chmod 600` (shared hosting) lub montowany `:ro` (Docker)
- [ ] `.env` NIE jest w repo (`.gitignore` zawiera `.env`)
- [ ] Odwiedzenie `/.env` zwraca 403 lub 404
- [ ] `ENCRYPTION_KEY` wygenerowany: `php -r "echo bin2hex(random_bytes(32));"` i zapisany w menedżerze haseł
- [ ] `ADMIN_PASS_HASH` ustawiony: `php -r "echo password_hash('haslo', PASSWORD_BCRYPT);"`
- [ ] `DB_PASS` zmienione z domyślnego
- [ ] HTTPS włączone, redirect 80→443 działa
- [ ] `CONTACT_EMAIL` ustawiony i otrzymuje testowe maile z formularza
- [ ] GitHub OAuth app ma dokładnie ten sam `Authorization callback URL` co `.env`
- [ ] CSP w `.htaccess` nie blokuje żadnych krytycznych zasobów (sprawdź konsolę przeglądarki)

## Testowanie

### Formularz kontaktowy
1. Wypełnij formularz z prawidłowym emailem
2. Sprawdź skrzynkę `CONTACT_EMAIL`
3. Sprawdź że dwukrotne submit w ciągu 60s zwraca "Zaczekaj chwilę"

### OAuth flow
1. Kliknij "Zaloguj przez GitHub"
2. Autoryzuj
3. Powinieneś wrócić na stronę z zielonym bannerem "Cześć @twój-login"
4. Sprawdź że dostałeś notyfikację na `CONTACT_EMAIL`

### Honeypot anty-spam
Formularz ma ukryte pole `website`. Boty które scrape'ują HTML często je wypełniają. Jeśli jest wypełnione, strona pokazuje success ale nic nie wysyła.

## Customizacja

**Zmiana kolorów** — `style.css` sekcja `:root`. Wszystko na zmiennych CSS. Najważniejsze:
- `--paper` = tło (kremowe)
- `--ink` = tekst główny
- `--red` = akcent (pieczątki, linie)

**Zmiana fontów** — `index.php` sekcja `<link>` (Google Fonts) + `style.css` zmienne `--font-*`.

**Zmiana copy / tłumaczenia** — system i18n z 3 językami (PL, EN, DE):
   - Pliki tłumaczeń w `i18n/` (`pl.json`, `en.json`, `de.json`)
   - Helper w `lib/i18n.php` - automatyczne wykrywanie języka (URL param > cookie > browser > default)
   - Użycie: `<?=h($t('key.subkey'))?>` w PHP templates
   - Przełącznik języków w prawym górnym rogu nawigacji
   - URL params: `?lang=pl`, `?lang=en`, `?lang=de`

**Zmiana cennika** — sekcja `.pricing` w `index.php`. Jeśli zmienisz liczby, pamiętaj zmienić też w sekcji FAQ i kontakt.

## System i18n (Internationalization)

Strona obsługuje 3 języki: Polski (PL), Angielski (EN), Niemiecki (DE).

### Struktura

```
www/
├── i18n/
│   ├── pl.json    # polskie tłumaczenia (domyślne)
│   ├── en.json    # angielskie tłumaczenia
│   └── de.json    # niemieckie tłumaczenia
└── lib/
    └── i18n.php   # helper functions
```

### Użycie w PHP

```php
// Inicjalizacja (na początku pliku)
$i18n = require __DIR__ . '/lib/i18n.php';
$t = $i18n['t'];
$lang = $i18n['lang'];
$getLangUrls = $i18n['getLangUrls'];
$getLangName = $i18n['getLangName'];

// Użycie w HTML
<?=h($t('nav.contact'))?>
<?=h($t('hero.kicker'))?>
```

### Priorytety wykrywania języka

1. **URL param** - `?lang=en` (najwyższy priorytet)
2. **Cookie** - `lang=pl` (zapamiętuje wybór)
3. **Browser** - `Accept-Language` header
4. **Domyślny** - `pl` (polski)

### Dodawanie nowych tłumaczeń

1. Dodaj klucz do wszystkich 3 plików JSON w `i18n/`
2. Użyj w PHP: `<?=h($t('sekcja.klucz'))?>`

### Testowanie

```bash
# Smoke test (bash)
cd www
./smoke-test.sh

# Playwright E2E tests
cd www/tests/e2e
npm install  # jeśli pierwszy raz
npx playwright install  # instalacja przeglądarek
npx playwright test  # uruchom wszystkie testy
npx playwright test --ui  # tryb UI z podglądem
```
php -r '
$_GET["lang"] = "en";
$i18n = require "lib/i18n.php";
$t = $i18n["t"];
$lang = $i18n["lang"];
echo "Lang: $lang\n";
echo "Nav contact: " . $t("nav.contact") . "\n";
'

# Test w przeglądarce
http://localhost:8080/?lang=en
http://localhost:8080/?lang=de
http://localhost:8080/?lang=pl
```

## Testy

### PHPUnit (backend logic)

```bash
cd www
composer install --ignore-platform-req=ext-dom --ignore-platform-req=ext-xml --ignore-platform-req=ext-xmlwriter
composer test              # wszystkie testy (35 unit + 1 skipped bez DB)
composer test:gui          # tylko testy GUI
```

Lub w Dockerze (wszystkie rozszerzenia dostępne):

```bash
docker exec redsl-www php vendor/bin/phpunit --testdox
```

### Playwright (E2E browser tests)

```bash
cd www/tests/e2e
npm install
npm run install:browsers
npm run test               # headless
npm run test:ui            # interaktywny tryb

# Scenariusz klienta end-to-end (repo -> NDA -> tickety -> subskrypcja)
npx playwright test client-commercial-flow.spec.js --project=chromium

# Kontrakt API (w tym MCP subscription)
npx playwright test api-mcp-subscription.spec.js --project=chromium
```

Szczegóły w [`tests/README_TESTS.md`](tests/README_TESTS.md).

## Panel SaaS — funkcje

| Strona | URL | Opis |
|--------|-----|------|
| **Config Editor** | `/config-editor.php` | Edytor YAML konfiguracji z walidacją i backupami |
| **Config API** | `/config-api.php` | REST API do walidacji, historii, diff |
| **ReDSL API Proxy** | `/api/redsl.php` | Proxy do redsl-api + endpointy MCP (`mcp_health`, `mcp_subscription`) |
| **Propozycje (PL)** | `/propozycje` | Panel wyboru ticketów — wersja polska |
| **Proposals (EN)** | `/proposals` | Panel wyboru ticketów — wersja angielska |
| **NDA** | `/nda-form.php` | Automatyczne generowanie umowy NDA (NIP → dane firmy) |
| **Panel admina** | `/admin/` | Zarządzanie klientami, kontraktami, rozliczeniami (Basic Auth) |
| **Panel klienta** | `/klient/` | Podgląd i akcje dla klienta |
| **Polityka prywatności** | `/polityka-prywatnosci` | Strona prawna |
| **Regulamin** | `/regulamin` | Strona prawna |

### Config Editor
- Edycja `redsl.config.yaml` z syntax highlighting
- Redakcja sekretów (nigdy nie pokazuje wartości)
- Automatyczne backupy przy zapisie
- Wskaźniki poziomów ryzyka
- Walidacja YAML + schema

### CQRS + Event Sourcing (inkrementalnie)
- Kontekst `Klienci` (`/admin/clients.php`) działa przez warstwę command/query (`lib/CQRS/Client/*`)
- Zdarzenia domenowe (`ClientCreated`, `ClientUpdated`, `ClientArchived`) są zapisywane append-only w `audit_log`
- Widok szczegółów klienta pokazuje historię eventów (event stream)
- Pozostałe moduły (`projekty`, `umowy`, `faktury`) mogą być migrowane etapowo tym samym wzorcem

### API MCP — subskrypcja miesięczna (reseller)
- Endpoint: `POST /api/redsl.php?action=mcp_subscription`
- Endpoint health: `GET /api/redsl.php?action=mcp_health`
- Domyślnie działa w trybie `dry_run` (bez wysyłki do zewnętrznego MCP)
- Aby wysłać do MCP, ustaw `MCP_API_URL` + opcjonalnie `MCP_API_KEY` i przekaż `dispatch_to_mcp=true`
- Kalkulacja miesięczna obejmuje plan, miejsca developerskie, kredyty ticketowe i opłatę MCP

### Wybór propozycji
- Klient otrzymuje email z linkiem
- Wybór format: `1, 3, 7, 12-15, 24` lub `wszystkie`
- Kalkulacja ceny: 10 zł / ticket
- Potwierdzenie → generowanie zleceń

### NDA Form
- Wprowadzenie NIP → auto-uzupełnienie danych (GUS REGON API)
- Generowanie PDF umowy
- Upload podpisanego dokumentu lub email

## Znane ograniczenia

- `mail()` — domyślna funkcja PHP często ląduje w spamie. Dla poważnego użytku podłącz SMTP (komentarze w `.env.example`).
- Rate limiting jest per-session, nie per-IP. Zdeterminowany bot może obejść czyszcząc cookies. Dla prostej strony wystarczy.
- Brak CAPTCHA — honeypot i rate-limit zazwyczaj wystarczą dla ~99% botów, ale jeśli będziesz miał problem ze spamem, dorzuć hCaptcha (darmowy, niekomercyjne ograniczenia dalekie od landing page skali).
- Brak analityki — celowo. Jeśli chcesz, dodaj Plausible lub Simple Analytics (nie Google Analytics — CSP tego nie przepuści bez zmian).

## Licencja

Kod landing page jest twój. Używaj jak chcesz.
