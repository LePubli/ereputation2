#!/usr/bin/env bash
# ============================================================================
# generate-secrets.sh — Génère un .env avec des secrets sécurisés
# ============================================================================
# Usage : ./scripts/generate-secrets.sh > .env
# ============================================================================

set -euo pipefail

if ! command -v openssl &>/dev/null; then
    echo "Erreur : openssl est requis" >&2
    exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXAMPLE="$ROOT_DIR/.env.example"

if [[ ! -f "$EXAMPLE" ]]; then
    echo "Erreur : .env.example introuvable à $EXAMPLE" >&2
    exit 1
fi

# Génération des secrets
SECRET_KEY="$(openssl rand -base64 48 | tr -d '\n')"
POSTGRES_PASSWORD="$(openssl rand -base64 32 | tr -d '\n/+=' | cut -c1-32)"
REDIS_PASSWORD="$(openssl rand -base64 32 | tr -d '\n/+=' | cut -c1-32)"

# Substitution
sed \
    -e "s|^SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|" \
    -e "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=${POSTGRES_PASSWORD}|" \
    -e "s|^REDIS_PASSWORD=.*|REDIS_PASSWORD=${REDIS_PASSWORD}|" \
    "$EXAMPLE"

echo "" >&2
echo "✔ Secrets générés. Redirige la sortie vers .env :" >&2
echo "  ./scripts/generate-secrets.sh > .env" >&2
