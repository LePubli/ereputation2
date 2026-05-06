#!/bin/bash
# Script de migration - Lance migrations + seed

set -e

echo "🚀 Lancement des migrations..."

# Lancer migrations Alembic
alembic upgrade head

echo "✅ Migrations terminées"

# Lancer seed
echo "🌱 Lancement du seed..."
python scripts/seed.py

echo "✅ Seed terminé"

# Activer plugins
echo "🔌 Activation des plugins..."
python scripts/activate_plugins.py

echo "✅ Plugins activés"

echo ""
echo "🎉 Installation Phase 1 terminée avec succès!"
