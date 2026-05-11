#!/usr/bin/env bash
# Lance les migrations Alembic puis le seed initial.
# Usage : bash scripts/migrate.sh
set -euo pipefail

cd "$(dirname "$0")/.."

# Construire DATABASE_URL avec asyncpg si nécessaire
DB_URL="${DATABASE_URL:-}"
if [ -z "$DB_URL" ]; then
    DB_URL="postgresql://${POSTGRES_USER:-prospector}:${POSTGRES_PASSWORD:-prospector}@${POSTGRES_HOST:-db}:${POSTGRES_PORT:-5432}/${POSTGRES_DB:-prospector}"
fi
# Remplacer postgresql:// par postgresql+asyncpg:// si nécessaire
if [[ "$DB_URL" == postgresql://* ]]; then
    DB_URL="${DB_URL/postgresql:\/\//postgresql+asyncpg://}"
fi

echo "🔄 [1/3] Application des migrations Alembic..."
export DATABASE_URL="$DB_URL"
python -c "from alembic.config import Config; from alembic import command; cfg = Config('alembic.ini'); command.upgrade(cfg, 'head')"

echo "🌱 [2/3] Seed des données initiales..."
python -m scripts.seed

echo "🔌 [3/3] Activation des plugins..."
python -m scripts.activate_plugins

echo "✅ Migrations + seed terminés."
