--- scripts/migrate.sh (原始)
#!/usr/bin/env bash
# Lance les migrations Alembic puis le seed initial.
# Usage : bash scripts/migrate.sh
set -euo pipefail

cd "$(dirname "$0")/.."

echo "🔄 [1/3] Application des migrations Alembic..."
alembic upgrade head

echo "🌱 [2/3] Seed des données initiales..."
python -m scripts.seed

echo "🔌 [3/3] Activation des plugins..."
python -m scripts.activate_plugins

echo "✅ Migrations + seed terminés."

+++ scripts/migrate.sh (修改后)
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
echo "   DATABASE_URL=$DB_URL"
python -c "
from alembic.config import Config
from alembic import command
import sys
try:
    cfg = Config('alembic.ini')
    command.upgrade(cfg, 'head')
    print('✓ Migrations appliquées avec succès')
except Exception as e:
    print(f'✗ Erreur migrations: {e}', file=sys.stderr)
    sys.exit(1)
" || { echo "❌ Échec des migrations"; exit 1; }

echo "🌱 [2/3] Seed des données initiales..."
python -m scripts.seed || { echo "❌ Échec du seed"; exit 1; }

echo "🔌 [3/3] Activation des plugins..."
python -m scripts.activate_plugins || { echo "❌ Échec activation plugins"; exit 1; }

echo "✅ Migrations + seed terminés."