# REDSL Panel — Wdrożenie na Plesk / VPS

Przewodnik krok po kroku jak zainstalować REDSL Panel na serwerze Plesk w folderze konkretnej domeny.

## Wymagania serwera

| Komponent | Minimum | Zalecane |
|-----------|---------|----------|
| PHP | 8.1 | 8.3 |
| Rozszerzenia PHP | `pdo_mysql`, `curl`, `json`, `mbstring`, `openssl`, `session` | + `sodium`, `yaml` |
| MySQL / MariaDB | 5.7 / 10.3 | 8.0 / 10.6 |
| Apache | 2.4 + `mod_rewrite` | + `mod_headers`, `mod_ssl` |
| SSH dostęp | tak (do uruchomienia install.sh) | + Composer |

## Tryby działania

Aplikacja wspiera **2 tryby**:

### Tryb DEV (lokalnie / Docker)

- **Mock GitHub OAuth** - symulator w `www/mock-github/` działa bez prawdziwego konta GitHub
- Dowolny username - wybierasz w formularzu consent
- Nie wymaga GitHub OAuth App

```env
GITHUB_OAUTH_BASE=http://localhost:8080/mock-github
GITHUB_API_BASE=http://localhost/mock-github
```

### Tryb PROD (VPS / Plesk)

- **Prawdziwy GitHub OAuth** - redirect do `https://github.com/login/oauth/authorize`
- Wymaga utworzonej GitHub OAuth App
- `mock-github/` **musi być usunięte** z serwera (robi to `install-plesk.sh`)

```env
# GITHUB_OAUTH_BASE=   # zakomentowane - używa github.com
# GITHUB_API_BASE=     # zakomentowane - używa api.github.com
```

## Instalacja na Plesk — krok po kroku

### 1. Przygotowanie w Plesk Panel

**a) Utwórz domenę** (np. `redsl.twojadomena.pl`)

**b) PHP 8.3** - `Domeny → redsl.twojadomena.pl → Ustawienia PHP`:
- Wersja PHP: `8.3`
- Handler: `FPM` (zalecane) lub `Apache Module`

**c) Baza danych** - `Bazy danych → Dodaj bazę`:
- Nazwa: `redsl_panel`
- Użytkownik: `redsl_user`
- Hasło: (zapisz!)

**d) SSL (Let's Encrypt)** - `SSL/TLS Certyfikaty → Zainstaluj Let's Encrypt`

**e) SSH** - `Użytkownicy Web Hosting → Twój user → zezwól na SSH`

### 2. Utwórz GitHub OAuth App

1. Wejdź na https://github.com/settings/developers
2. **New OAuth App**:
   - **Application name**: `REDSL Panel`
   - **Homepage URL**: `https://redsl.twojadomena.pl`
   - **Authorization callback URL**: `https://redsl.twojadomena.pl/`  ⚠️ **DOKŁADNIE** ten URL!
3. Po utworzeniu zapisz:
   - `Client ID` (jawny)
   - `Client Secret` (kliknij "Generate a new client secret")

### 3. Upload plików na serwer

**Opcja A - SCP (z lokalnego):**

```bash
# Z maszyny developerskiej:
cd /home/tom/github/semcod/redsl/www
scp -r ./* user@plesk-server:/var/www/vhosts/redsl.twojadomena.pl/httpdocs/
```

**Opcja B - Git (na serwerze):**

```bash
ssh user@plesk-server
cd /var/www/vhosts/redsl.twojadomena.pl/httpdocs
git clone https://github.com/YOUR_ORG/redsl.git .
# Lub, jeśli www/ jest pod-katalogiem:
git clone https://github.com/YOUR_ORG/redsl.git /tmp/redsl
cp -r /tmp/redsl/www/* .
```

**Opcja C - Plesk File Manager:**

1. Domain → File Manager
2. Przejdź do `httpdocs/`
3. Upload → przeciągnij cały folder `www/` jako zip, rozpakuj

### 4. Uruchom skrypt instalacyjny

```bash
ssh user@plesk-server
cd /var/www/vhosts/redsl.twojadomena.pl/httpdocs
bash install-plesk.sh redsl.twojadomena.pl
```

Skrypt wykonuje:

- ✅ Sprawdza wersję PHP i rozszerzenia
- ✅ Tworzy katalogi `var/{logs,scans,invoices,contracts,repos,cache}`
- ✅ Ustawia permisje (755/775/600)
- ✅ Kopiuje `.env.example` → `.env` (jeśli nie istnieje)
- ✅ Dodaje reguły do `.htaccess` (blokada `.env`, `*.log`, `*.sql`)
- ✅ **Usuwa `mock-github/`** (tryb prod)
- ✅ **Komentuje `GITHUB_OAUTH_BASE`/`GITHUB_API_BASE`** w `.env`
- ✅ Uruchamia migracje DB (jeśli credentials w `.env`)
- ✅ Sprawdza składnię wszystkich plików PHP

### 5. Wypełnij `.env`

```bash
nano /var/www/vhosts/redsl.twojadomena.pl/httpdocs/.env
```

```env
APP_ENV=production
APP_DEBUG=0

# Baza (z Plesk → Bazy danych)
DB_HOST=localhost
DB_PORT=3306
DB_NAME=redsl_panel
DB_USER=redsl_user
DB_PASS=twoje_haslo_db

# Admin (wygeneruj hash!)
ADMIN_USER=admin
ADMIN_PASS_HASH=$2y$10$...  # php -r "echo password_hash('HASLO', PASSWORD_DEFAULT);"

# Klucz szyfrowania (32 bajty hex)
ENCRYPTION_KEY=abcd...  # openssl rand -hex 32

# GitHub OAuth (z kroku 2)
GITHUB_CLIENT_ID=Ov23li...
GITHUB_CLIENT_SECRET=ghs_...
GITHUB_REDIRECT_URI=https://redsl.twojadomena.pl/

# Email
CONTACT_EMAIL=kontakt@twojadomena.pl
MAIL_FROM=no-reply@twojadomena.pl

# ⚠️ NIE odkomentowuj w produkcji!
# GITHUB_OAUTH_BASE=http://localhost:8080/mock-github
# GITHUB_API_BASE=http://localhost/mock-github
```

**Wygeneruj hash hasła admin:**

```bash
php -r "echo password_hash('WybierzSilneHaslo', PASSWORD_DEFAULT);"
```

**Wygeneruj klucz szyfrowania:**

```bash
openssl rand -hex 32
```

### 6. Uruchom migracje (po wypełnieniu DB)

```bash
bash install-plesk.sh redsl.twojadomena.pl  # drugi raz - wykryje DB i zmigruje
```

Lub ręcznie:

```bash
mysql -u redsl_user -p redsl_panel < migrations/001_core_schema.sql
```

### 7. Dodaj cron jobs

`Plesk → Narzędzia i ustawienia → Zaplanowane zadania`:

| Harmonogram | Komenda |
|-------------|---------|
| `*/15 * * * *` | `php /var/www/vhosts/redsl.twojadomena.pl/httpdocs/cron/scan-worker.php >> /var/www/vhosts/redsl.twojadomena.pl/httpdocs/var/logs/cron.log 2>&1` |
| `0 2 1 * *` | `php /var/www/vhosts/redsl.twojadomena.pl/httpdocs/cron/invoice-generator.php >> /var/www/vhosts/redsl.twojadomena.pl/httpdocs/var/logs/cron.log 2>&1` |

### 8. Test produkcji

```bash
bash test-plesk.sh https://redsl.twojadomena.pl
```

Sprawdzi:

- ✅ Landing strony (HTTP 200, brak PHP errors)
- ✅ OAuth redirect → `github.com` (NIE `localhost`!)
- ✅ `mock-github/` niewystawiony (404)
- ✅ `.env`, `*.log`, `*.sql` zablokowane
- ✅ `/admin/` wymaga auth
- ✅ HTTPS + SSL cert
- ✅ Security headers

### 9. Monitoring logów

**W przeglądarce:** https://redsl.twojadomena.pl/admin/logs.php

**Z konsoli:**

```bash
cd /var/www/vhosts/redsl.twojadomena.pl/httpdocs/var/logs

tail -f error.log      # tylko błędy
tail -f warning.log    # ostrzeżenia
tail -f info.log       # wszystkie akcje (login, OAuth, etc.)
tail -f all.log        # wszystko razem

# Błędy OAuth w ostatniej godzinie:
grep "\[oauth\]" error.log | grep "$(date '+%Y-%m-%d %H')"
```

### Pliki logów (osobno per level)

| Plik | Co zawiera |
|------|------------|
| `var/logs/info.log` | INFO + DEBUG - normalne akcje (logowanie, OAuth init, skany) |
| `var/logs/warning.log` | WARNING - nieoczekiwane ale nie krytyczne (state mismatch, rate limit) |
| `var/logs/error.log` | ERROR + CRITICAL - błędy wymagające uwagi (token exchange fail, DB errors) |
| `var/logs/all.log` | wszystko razem, chronologicznie |

Każdy wpis ma format:

```
[2026-04-20 10:15:32] [ERROR] [192.168.1.1] [oauth] Token exchange failed {"http_code":401,"response_error":"bad_verification_code","hint":"Sprawdź GITHUB_CLIENT_SECRET"}
```

## Troubleshooting

### Błąd: "Nie udało się uzyskać tokenu z GitHub"

1. Sprawdź log: `tail /var/www/vhosts/.../var/logs/error.log`
2. Najczęstsze przyczyny:
   - ❌ `GITHUB_CLIENT_SECRET` zły lub pusty
   - ❌ `GITHUB_REDIRECT_URI` nie zgadza się z Callback URL w GitHub OAuth App
   - ❌ `GITHUB_OAUTH_BASE=http://localhost...` zostawiony z devu (uruchom `install-plesk.sh`)
3. Weryfikacja: `bash test-plesk.sh https://twoja-domena.pl`

### Admin pokazuje "Admin Not Configured"

Brakuje `ADMIN_USER` lub `ADMIN_PASS_HASH` w `.env`. Wygeneruj hash:

```bash
php -r "echo password_hash('HASLO', PASSWORD_DEFAULT);"
```

### 500 Internal Server Error

```bash
tail /var/www/vhosts/.../logs/error_log            # Apache error log
tail /var/www/vhosts/.../httpdocs/var/logs/error.log  # REDSL log
```

Najczęściej:
- Brak `pdo_mysql` extension
- Zła wersja PHP (< 8.1)
- `var/` nie ma praw zapisu

### `mock-github/` widoczne w produkcji

```bash
rm -rf /var/www/vhosts/.../httpdocs/mock-github
# Zakomentuj w .env:
sed -i 's|^GITHUB_OAUTH_BASE=|# GITHUB_OAUTH_BASE=|' .env
sed -i 's|^GITHUB_API_BASE=|# GITHUB_API_BASE=|' .env
```

Albo ponownie uruchom `install-plesk.sh` - zrobi to automatycznie.

## Różnice DEV vs PROD

| Aspekt | DEV (Docker) | PROD (Plesk) |
|--------|--------------|--------------|
| GitHub OAuth | Mock w `mock-github/` | Prawdziwe `github.com` |
| Username | Dowolny (w formularzu) | Faktyczne konto GitHub |
| DB | Docker MySQL | Plesk MySQL/MariaDB |
| Logi | `var/logs/` w kontenerze | `var/logs/` na dysku |
| HTTPS | Nie (port 8080) | Tak (Let's Encrypt) |
| Debug | `APP_DEBUG=1` | `APP_DEBUG=0` |
| Callback URL | `http://localhost:8080/` | `https://twoja-domena.pl/` |

## Aktualizacja (deploy nowej wersji)

```bash
ssh user@plesk-server
cd /var/www/vhosts/redsl.twojadomena.pl/httpdocs

# Backup .env + var/
cp .env /tmp/redsl.env.backup
tar czf /tmp/redsl-var.tar.gz var/

# Pull nowy kod
git pull                    # jeśli git
# LUB: scp -r user@local:.../www/* ./

# Reinstall (zachowa .env)
bash install-plesk.sh redsl.twojadomena.pl

# Uruchom migracje (jeśli nowe)
for m in migrations/*.sql; do
    mysql -u redsl_user -p redsl_panel < "$m"
done

# Test
bash test-plesk.sh https://redsl.twojadomena.pl
```
