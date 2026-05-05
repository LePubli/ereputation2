#!/usr/bin/env bash
# ============================================================================
# healthcheck.sh — Vérifie l'état de tous les services de la stack
# ============================================================================
# Usage : ./scripts/healthcheck.sh [base_url]
# Ex.   : ./scripts/healthcheck.sh https://prospect.le-publicitaire.fr
# ============================================================================

set -euo pipefail

BASE_URL="${1:-http://localhost}"
EXIT_CODE=0

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'

check() {
    local name="$1" url="$2" expected="${3:-200}"
    local code
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" || echo "000")
    if [[ "$code" == "$expected" ]]; then
        echo -e "  ${GREEN}✔${NC} $name → HTTP $code"
    else
        echo -e "  ${RED}✖${NC} $name → HTTP $code (attendu $expected) - $url"
        EXIT_CODE=1
    fi
}

echo "Healthcheck de $BASE_URL"
echo "──────────────────────────────────────────────"
check "Frontend root"     "$BASE_URL/"           200
check "Frontend healthz"  "$BASE_URL/healthz"    200
check "Backend health"    "$BASE_URL/api/health" 200
check "Backend ready"     "$BASE_URL/api/ready"  200
check "API endpoints"     "$BASE_URL/api/v1/endpoints" 200
check "API plugins"       "$BASE_URL/api/v1/plugins"   200
echo "──────────────────────────────────────────────"

if [[ $EXIT_CODE -eq 0 ]]; then
    echo -e "${GREEN}✔ Tous les services sont opérationnels${NC}"
else
    echo -e "${RED}✖ Certains services échouent${NC}"
fi

exit $EXIT_CODE
