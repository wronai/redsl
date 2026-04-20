#!/usr/bin/env bash
# ============================================================================
# REDSL Panel - Production smoke test (Plesk/VPS)
# ============================================================================
# 
# USAGE:
#   bash test-plesk.sh https://yourdomain.com
#
# Tests:
#   - Landing page loads
#   - GitHub OAuth initiates redirect to github.com (NOT localhost!)
#   - Mock endpoints are NOT exposed in production
#   - Admin panel requires auth
#   - Sensitive files are blocked (.env, *.log, *.sql)
#   - No PHP errors exposed
# ============================================================================

set -uo pipefail

URL="${1:-}"
if [[ -z "$URL" ]]; then
    echo "Usage: bash test-plesk.sh https://yourdomain.com"
    exit 1
fi
URL="${URL%/}"  # strip trailing slash

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; NC='\033[0m'
PASS=0; FAIL=0; WARN=0

pass() { echo -e "${GREEN}✓${NC} $1"; PASS=$((PASS+1)); }
fail() { echo -e "${RED}✗${NC} $1"; FAIL=$((FAIL+1)); }
warn() { echo -e "${YELLOW}⚠${NC} $1"; WARN=$((WARN+1)); }

# Helper: check HTTP status
check_status() {
    local expected="$1" path="$2" desc="$3"
    local got
    got=$(curl -s -o /dev/null -w "%{http_code}" "$URL$path" --max-time 10)
    if [[ "$got" == "$expected" ]]; then
        pass "$desc ($path → $got)"
    else
        fail "$desc ($path → expected $expected, got $got)"
    fi
}

# Helper: check content contains
check_contains() {
    local path="$1" pattern="$2" desc="$3"
    local body
    body=$(curl -sL "$URL$path" --max-time 10)
    if echo "$body" | grep -qi "$pattern"; then
        pass "$desc"
    else
        fail "$desc (pattern '$pattern' not found in $path)"
    fi
}

# Helper: check content does NOT contain
check_not_contains() {
    local path="$1" pattern="$2" desc="$3"
    local body
    body=$(curl -sL "$URL$path" --max-time 10)
    if echo "$body" | grep -qi "$pattern"; then
        fail "$desc (found forbidden '$pattern' in $path)"
    else
        pass "$desc"
    fi
}

echo "=============================================================="
echo " REDSL Panel - Production Smoke Test"
echo " URL: $URL"
echo "=============================================================="

# ---------------------------------------------------------------------------
# 1. Landing page
# ---------------------------------------------------------------------------
echo
echo "── Landing page ──────────────────────────────────────────────"
check_status 200 "/" "Landing returns 200"
check_contains "/" "REDSL" "Landing has REDSL branding"
check_contains "/" "github-login" "Landing has GitHub login button"
check_not_contains "/" "Fatal error" "No PHP errors on landing"
check_not_contains "/" "Warning:" "No PHP warnings on landing"
check_not_contains "/" "Notice:" "No PHP notices on landing"

# ---------------------------------------------------------------------------
# 2. GitHub OAuth redirect (MUST go to github.com, NOT localhost)
# ---------------------------------------------------------------------------
echo
echo "── GitHub OAuth ──────────────────────────────────────────────"
OAUTH_LOC=$(curl -s -I "$URL/?action=github-login" --max-time 10 | grep -i '^location:' | cut -d' ' -f2 | tr -d '\r')

if [[ -z "$OAUTH_LOC" ]]; then
    warn "OAuth: no redirect - check if GITHUB_CLIENT_ID is set in .env"
elif echo "$OAUTH_LOC" | grep -q "localhost"; then
    fail "OAuth redirects to localhost: $OAUTH_LOC (mock mode leaked to prod!)"
elif echo "$OAUTH_LOC" | grep -q "github.com/login/oauth/authorize"; then
    pass "OAuth redirects to github.com (production mode)"
    
    if echo "$OAUTH_LOC" | grep -q "client_id="; then
        pass "OAuth URL has client_id"
    else
        fail "OAuth URL missing client_id"
    fi
    
    if echo "$OAUTH_LOC" | grep -q "state="; then
        pass "OAuth URL has state (CSRF protection)"
    else
        fail "OAuth URL missing state"
    fi
elif echo "$OAUTH_LOC" | grep -q "oauth_not_configured"; then
    warn "OAuth not configured in .env (fill GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET)"
else
    fail "OAuth redirects to unexpected URL: $OAUTH_LOC"
fi

# ---------------------------------------------------------------------------
# 3. Mock endpoints MUST NOT be exposed in production
# ---------------------------------------------------------------------------
echo
echo "── Mock endpoints (must be 404 in production) ────────────────"
MOCK_AUTH=$(curl -s -o /dev/null -w "%{http_code}" "$URL/mock-github/login/oauth/authorize" --max-time 10)
if [[ "$MOCK_AUTH" == "404" || "$MOCK_AUTH" == "403" ]]; then
    pass "Mock /mock-github/ not exposed (HTTP $MOCK_AUTH)"
else
    fail "Mock endpoints exposed! HTTP $MOCK_AUTH - DELETE www/mock-github/ in production"
fi

# ---------------------------------------------------------------------------
# 4. Sensitive files blocked
# ---------------------------------------------------------------------------
echo
echo "── Sensitive files protection ────────────────────────────────"
for file in ".env" ".env.example" "composer.json" "install-plesk.sh" \
            "redsl-panel-plan-mysql-2026-04.md" "var/logs/error.log" \
            "migrations/001_core_schema.sql" "lib/Database.php"; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$URL/$file" --max-time 5)
    if [[ "$STATUS" == "403" || "$STATUS" == "404" ]]; then
        pass "Blocked: /$file ($STATUS)"
    else
        fail "EXPOSED: /$file (HTTP $STATUS) - add to .htaccess deny rules!"
    fi
done

# ---------------------------------------------------------------------------
# 5. Admin panel requires auth
# ---------------------------------------------------------------------------
echo
echo "── Admin panel auth ──────────────────────────────────────────"
ADMIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$URL/admin/" --max-time 10)
if [[ "$ADMIN_STATUS" == "401" ]]; then
    pass "Admin requires auth (HTTP 401)"
elif [[ "$ADMIN_STATUS" == "500" ]]; then
    warn "Admin returns 500 - probably admin not configured (set ADMIN_USER/PASS_HASH in .env)"
elif [[ "$ADMIN_STATUS" == "200" ]]; then
    # Check if it's a setup page, not actual admin
    BODY=$(curl -sL "$URL/admin/" --max-time 10)
    if echo "$BODY" | grep -qi "Admin Not Configured"; then
        warn "Admin shows 'Not Configured' page - set ADMIN_USER/PASS_HASH in .env"
    else
        fail "Admin panel accessible WITHOUT auth!"
    fi
else
    fail "Admin unexpected status: $ADMIN_STATUS"
fi

# ---------------------------------------------------------------------------
# 6. HTTPS enforcement (production should use HTTPS)
# ---------------------------------------------------------------------------
echo
echo "── HTTPS / SSL ───────────────────────────────────────────────"
if [[ "$URL" =~ ^https:// ]]; then
    pass "Using HTTPS"
    
    # Check cert validity
    CERT_OK=$(curl -s -o /dev/null -w "%{ssl_verify_result}" "$URL" --max-time 10)
    if [[ "$CERT_OK" == "0" ]]; then
        pass "SSL certificate valid"
    else
        fail "SSL certificate issue (code: $CERT_OK)"
    fi
else
    warn "Not using HTTPS - enable Let's Encrypt in Plesk for security"
fi

# ---------------------------------------------------------------------------
# 7. Security headers
# ---------------------------------------------------------------------------
echo
echo "── Security headers ──────────────────────────────────────────"
HEADERS=$(curl -sI "$URL/" --max-time 10)

if echo "$HEADERS" | grep -qi "X-Frame-Options\|content-security-policy"; then
    pass "Clickjacking protection (X-Frame-Options / CSP)"
else
    warn "No X-Frame-Options - add to .htaccess"
fi

if echo "$HEADERS" | grep -qi "Strict-Transport-Security"; then
    pass "HSTS enabled"
elif [[ "$URL" =~ ^https:// ]]; then
    warn "HTTPS but no HSTS - add Strict-Transport-Security header"
fi

# ---------------------------------------------------------------------------
# 8. Other pages
# ---------------------------------------------------------------------------
echo
echo "── Other endpoints ───────────────────────────────────────────"
check_status 200 "/propozycje.php" "propozycje.php loads"
check_status 200 "/config-editor.php" "config-editor.php loads"

# 404 for non-existent page
check_status 404 "/this-does-not-exist-12345.php" "404 for missing pages"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo
echo "=============================================================="
echo " Summary"
echo "=============================================================="
echo -e "  ${GREEN}Passed:${NC}  $PASS"
echo -e "  ${RED}Failed:${NC}  $FAIL"
echo -e "  ${YELLOW}Warning:${NC} $WARN"
echo

if [[ $FAIL -gt 0 ]]; then
    echo -e "${RED}❌ Production check FAILED - fix issues above${NC}"
    exit 1
elif [[ $WARN -gt 0 ]]; then
    echo -e "${YELLOW}⚠ Production check passed with warnings${NC}"
    exit 0
else
    echo -e "${GREEN}✅ Production check PASSED${NC}"
    exit 0
fi
