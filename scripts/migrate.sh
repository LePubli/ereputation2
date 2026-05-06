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
