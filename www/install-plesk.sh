#!/usr/bin/env bash
# ============================================================================
# REDSL Panel - Installation script for Plesk hosting
# ============================================================================
#
# USAGE (on Plesk server, SSH):
#   1. Upload files: scp -r www/* user@plesk:/var/www/vhosts/DOMAIN.com/httpdocs/
#   2. SSH in: ssh user@plesk
#   3. cd /var/www/vhosts/DOMAIN.com/httpdocs
#   4. bash install-plesk.sh DOMAIN.com
#
# Supports:
#   - PHP 8.1+ (uses phpXY_CLI if available)
#   - MySQL/MariaDB (via Plesk database panel)
#   - Apache + mod_rewrite (.htaccess)
# ============================================================================

set -euo pipefail

DOMAIN="${1:-}"
if [[ -z "$DOMAIN" ]]; then
    echo "Usage: bash install-plesk.sh <domain.com>"
    exit 1
fi

# Plesk typical path
PLESK_DOC_ROOT="/var/www/vhosts/$DOMAIN/httpdocs"

# Fallback: use current directory
if [[ ! -d "$PLESK_DOC_ROOT" ]]; then
    echo "⚠ Plesk vhost directory not found at $PLESK_DOC_ROOT"
    echo "  Using current directory: $(pwd)"
    PLESK_DOC_ROOT="$(pwd)"
fi

# Color helpers
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; BLUE='\033[0;34m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }
err()  { echo -e "${RED}✗${NC} $1" >&2; }
info() { echo -e "${BLUE}ℹ${NC} $1"; }

echo "=============================================================="
echo " REDSL Panel - Plesk Installation"
echo " Domain:   $DOMAIN"
echo " Doc root: $PLESK_DOC_ROOT"
echo "=============================================================="

# ---------------------------------------------------------------------------
# 1. PHP version check
# ---------------------------------------------------------------------------
info "Checking PHP version..."
PHP_VERSION=$(php -r 'echo PHP_VERSION;' 2>/dev/null || echo "none")
if [[ "$PHP_VERSION" == "none" ]]; then
    err "PHP not found in PATH. Install PHP 8.1+ via Plesk > Tools > PHP Settings."
    exit 1
fi

MAJOR=$(echo "$PHP_VERSION" | cut -d. -f1)
MINOR=$(echo "$PHP_VERSION" | cut -d. -f2)
if [[ "$MAJOR" -lt 8 ]] || [[ "$MAJOR" -eq 8 && "$MINOR" -lt 1 ]]; then
    err "PHP $PHP_VERSION is too old. Need 8.1+."
    exit 1
fi
ok "PHP $PHP_VERSION OK"

# ---------------------------------------------------------------------------
# 2. Required PHP extensions
# ---------------------------------------------------------------------------
info "Checking PHP extensions..."
REQUIRED_EXT=(pdo_mysql curl json mbstring openssl session)
MISSING=()
for ext in "${REQUIRED_EXT[@]}"; do
    if ! php -m 2>/dev/null | grep -qi "^$ext$"; then
        MISSING+=("$ext")
    fi
done

if [[ ${#MISSING[@]} -gt 0 ]]; then
    err "Missing PHP extensions: ${MISSING[*]}"
    echo "  Enable them via: Plesk > Domains > $DOMAIN > PHP Settings"
    exit 1
fi
ok "All PHP extensions present"

# Optional
for opt_ext in yaml sodium; do
    if php -m 2>/dev/null | grep -qi "^$opt_ext$"; then
        ok "Optional extension: $opt_ext"
    else
        warn "Optional extension missing: $opt_ext (some features disabled)"
    fi
done

# ---------------------------------------------------------------------------
# 3. Directory structure
# ---------------------------------------------------------------------------
info "Creating runtime directories..."
mkdir -p "$PLESK_DOC_ROOT/var/logs"
mkdir -p "$PLESK_DOC_ROOT/var/scans"
mkdir -p "$PLESK_DOC_ROOT/var/invoices"
mkdir -p "$PLESK_DOC_ROOT/var/contracts"
mkdir -p "$PLESK_DOC_ROOT/var/repos"
mkdir -p "$PLESK_DOC_ROOT/var/cache"

chmod 755 "$PLESK_DOC_ROOT/var"
chmod 775 "$PLESK_DOC_ROOT/var/logs"
chmod 775 "$PLESK_DOC_ROOT/var/cache"
chmod 775 "$PLESK_DOC_ROOT/var/scans"
chmod 775 "$PLESK_DOC_ROOT/var/invoices"
chmod 775 "$PLESK_DOC_ROOT/var/contracts"
chmod 700 "$PLESK_DOC_ROOT/var/repos"
ok "Runtime directories created"

# Ownership - try to use Plesk's user:psacln
if id "${USER:-www-data}" &>/dev/null && getent group psacln &>/dev/null; then
    chown -R "$USER":psacln "$PLESK_DOC_ROOT/var/" 2>/dev/null || true
    ok "Ownership set to $USER:psacln"
fi

# ---------------------------------------------------------------------------
# 4. .env file
# ---------------------------------------------------------------------------
info "Configuring .env..."
ENV_FILE="$PLESK_DOC_ROOT/.env"
ENV_EXAMPLE="$PLESK_DOC_ROOT/.env.example"

if [[ ! -f "$ENV_FILE" ]]; then
    if [[ -f "$ENV_EXAMPLE" ]]; then
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        ok ".env created from .env.example"
    else
        warn ".env and .env.example not found - creating minimal .env"
        cat > "$ENV_FILE" <<EOF
# REDSL Panel - Production Environment
APP_ENV=production
APP_DEBUG=0

# Database (fill in Plesk credentials)
DB_HOST=localhost
DB_PORT=3306
DB_NAME=
DB_USER=
DB_PASS=

# Admin auth (generate hash: php -r "echo password_hash('your-password', PASSWORD_DEFAULT);")
ADMIN_USER=admin
ADMIN_PASS_HASH=

# Encryption (generate: openssl rand -hex 32)
ENCRYPTION_KEY=

# GitHub OAuth (production)
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GITHUB_REDIRECT_URI=https://$DOMAIN/

# Leave empty in PRODUCTION to use real github.com
# GITHUB_OAUTH_BASE=
# GITHUB_API_BASE=

# Email
CONTACT_EMAIL=kontakt@$DOMAIN
MAIL_FROM=no-reply@$DOMAIN
EOF
    fi
    chmod 600 "$ENV_FILE"
    ok ".env created with secure permissions (600)"
else
    warn ".env already exists - not overwriting"
fi

# ---------------------------------------------------------------------------
# 5. .htaccess - block .env, add rewrite for mock-github if exists
# ---------------------------------------------------------------------------
info "Configuring .htaccess..."
HTACCESS="$PLESK_DOC_ROOT/.htaccess"
if [[ ! -f "$HTACCESS" ]] || ! grep -q "REDSL-GEN" "$HTACCESS" 2>/dev/null; then
    cat >> "$HTACCESS" <<'EOF'
# REDSL-GEN (generated by install-plesk.sh)
<FilesMatch "^\.env">
    Require all denied
</FilesMatch>
<FilesMatch "\.(log|sql|md|sh|yml|yaml)$">
    Require all denied
</FilesMatch>
<Files "composer.json">
    Require all denied
</Files>
<Files "composer.lock">
    Require all denied
</Files>
RewriteEngine On

# Block direct access to lib/, migrations/, tests/, cron/
RewriteRule ^(lib|migrations|tests|cron)/ - [F,L]

# Block var/ except public assets
RewriteRule ^var/logs/ - [F,L]
RewriteRule ^var/repos/ - [F,L]
RewriteRule ^var/cache/ - [F,L]
# REDSL-GEN-END
EOF
    ok ".htaccess configured"
else
    ok ".htaccess already has REDSL rules"
fi

# ---------------------------------------------------------------------------
# 6. Remove mock-github in production!
# ---------------------------------------------------------------------------
if [[ -d "$PLESK_DOC_ROOT/mock-github" ]]; then
    warn "mock-github/ directory exists - REMOVING in production"
    rm -rf "$PLESK_DOC_ROOT/mock-github"
    ok "mock-github/ removed"
fi

# Remove mock settings from .env if present
if grep -q "^GITHUB_OAUTH_BASE=http://localhost" "$ENV_FILE" 2>/dev/null; then
    warn "Mock OAuth URLs detected in .env - commenting out"
    sed -i.bak 's|^GITHUB_OAUTH_BASE=http://localhost|# GITHUB_OAUTH_BASE=http://localhost|g' "$ENV_FILE"
    sed -i.bak 's|^GITHUB_API_BASE=http://localhost|# GITHUB_API_BASE=http://localhost|g' "$ENV_FILE"
    rm -f "$ENV_FILE.bak"
    ok "Mock OAuth URLs disabled (now uses real github.com)"
fi

# ---------------------------------------------------------------------------
# 7. Database migration (if DB_NAME set)
# ---------------------------------------------------------------------------
info "Checking database..."
DB_NAME=$(grep '^DB_NAME=' "$ENV_FILE" 2>/dev/null | cut -d= -f2 | tr -d '"')
DB_USER=$(grep '^DB_USER=' "$ENV_FILE" 2>/dev/null | cut -d= -f2 | tr -d '"')
DB_PASS=$(grep '^DB_PASS=' "$ENV_FILE" 2>/dev/null | cut -d= -f2 | tr -d '"')
DB_HOST=$(grep '^DB_HOST=' "$ENV_FILE" 2>/dev/null | cut -d= -f2 | tr -d '"')

if [[ -n "$DB_NAME" && -n "$DB_USER" && -n "$DB_PASS" ]]; then
    MIGR_DIR="$PLESK_DOC_ROOT/migrations"
    if [[ -d "$MIGR_DIR" ]]; then
        info "Running migrations from $MIGR_DIR..."
        for sql in "$MIGR_DIR"/*.sql; do
            [[ -f "$sql" ]] || continue
            info "  Applying $(basename "$sql")..."
            mysql -h "${DB_HOST:-localhost}" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" < "$sql" \
                && ok "  ✓ $(basename "$sql")" \
                || err "  ✗ $(basename "$sql") - check logs"
        done
    fi
else
    warn "DB credentials incomplete - skipping migrations"
    warn "  Fill DB_NAME, DB_USER, DB_PASS in .env and re-run to migrate"
fi

# ---------------------------------------------------------------------------
# 8. PHP syntax check
# ---------------------------------------------------------------------------
info "Running PHP syntax check..."
ERRORS=0
for f in "$PLESK_DOC_ROOT"/*.php "$PLESK_DOC_ROOT"/admin/*.php "$PLESK_DOC_ROOT"/lib/**/*.php; do
    [[ -f "$f" ]] || continue
    if ! php -l "$f" > /dev/null 2>&1; then
        err "Syntax error in $f"
        ERRORS=$((ERRORS + 1))
    fi
done

if [[ $ERRORS -eq 0 ]]; then
    ok "All PHP files syntax OK"
else
    err "$ERRORS PHP files have syntax errors"
    exit 1
fi

# ---------------------------------------------------------------------------
# 9. Cron setup instructions
# ---------------------------------------------------------------------------
echo
echo "=============================================================="
info "CRON JOBS (add via Plesk > Scheduled Tasks):"
echo "=============================================================="
echo "  # Scan worker (every 15 min)"
echo "  */15 * * * * php $PLESK_DOC_ROOT/cron/scan-worker.php >> $PLESK_DOC_ROOT/var/logs/cron.log 2>&1"
echo
echo "  # Invoice generator (1st of month, 02:00)"
echo "  0 2 1 * * php $PLESK_DOC_ROOT/cron/invoice-generator.php >> $PLESK_DOC_ROOT/var/logs/cron.log 2>&1"
echo

# ---------------------------------------------------------------------------
# 10. Final summary
# ---------------------------------------------------------------------------
echo "=============================================================="
ok "Installation complete!"
echo "=============================================================="
echo
echo "NEXT STEPS:"
echo
echo "  1. Fill in .env:"
echo "     nano $ENV_FILE"
echo
echo "     Required:"
echo "       - DB_NAME, DB_USER, DB_PASS (create DB via Plesk > Databases)"
echo "       - ADMIN_USER + ADMIN_PASS_HASH (generate hash with:"
echo "           php -r \"echo password_hash('SECRET', PASSWORD_DEFAULT);\")"
echo "       - ENCRYPTION_KEY (generate with: openssl rand -hex 32)"
echo "       - GITHUB_CLIENT_ID + GITHUB_CLIENT_SECRET (from github.com/settings/developers)"
echo "       - GITHUB_REDIRECT_URI=https://$DOMAIN/"
echo
echo "  2. GitHub OAuth App settings:"
echo "       Homepage URL:     https://$DOMAIN"
echo "       Callback URL:     https://$DOMAIN/"
echo "       (must match GITHUB_REDIRECT_URI EXACTLY)"
echo
echo "  3. Re-run migrations if DB credentials were added:"
echo "       bash install-plesk.sh $DOMAIN"
echo
echo "  4. Test installation:"
echo "       bash test-plesk.sh https://$DOMAIN"
echo
echo "  5. Add cron jobs (see above)"
echo
echo "  6. Monitor logs:"
echo "       tail -f $PLESK_DOC_ROOT/var/logs/error.log"
echo "       Or in browser: https://$DOMAIN/admin/logs.php"
echo
