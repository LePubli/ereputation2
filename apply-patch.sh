#!/usr/bin/env bash
# =================================================================
# B2B Prospector — Script d'application du PATCH PHASE 1
# =================================================================
# Applique tous les fichiers du patch sur un clone du repo existant.
#
# Usage :
#   1. Cloner le repo cible :
#      git clone https://github.com/LePubli/ereputation2.git
#      cd ereputation2
#      git checkout -b patch-phase-1
#
#   2. Décompresser le patch et copier ce script à la racine :
#      cp -r patch-phase-1/. ./
#      bash apply-patch.sh
#
#   3. Vérifier puis pousser :
#      git status
#      git add -A
#      git commit -m "feat(phase-1): stabilisation, scrapers, frontend"
#      git push origin patch-phase-1
# =================================================================
set -euo pipefail

REPO_ROOT="$(pwd)"
PATCH_DIR="${PATCH_DIR:-$REPO_ROOT/patch-phase-1}"

if [ ! -d "$PATCH_DIR" ]; then
    echo "❌ Dossier patch introuvable : $PATCH_DIR"
    exit 1
fi

echo "🔧 Application du PATCH PHASE 1 dans : $REPO_ROOT"

# -----------------------------------------------------------------
# 1. Backup .env si existant
# -----------------------------------------------------------------
if [ -f .env ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo "   ✓ .env existant sauvegardé"
fi

# -----------------------------------------------------------------
# 2. Copie des fichiers (avec écrasement pour ce qui doit être mis à jour)
# -----------------------------------------------------------------
echo "📁 Copie des fichiers backend..."
cp -rf "$PATCH_DIR/core" .
cp -rf "$PATCH_DIR/models" .
cp -rf "$PATCH_DIR/plugins" .
cp -rf "$PATCH_DIR/services" .
cp -rf "$PATCH_DIR/scripts" .
cp -rf "$PATCH_DIR/alembic" .
cp -f  "$PATCH_DIR/alembic.ini" .
cp -f  "$PATCH_DIR/main.py" .
cp -f  "$PATCH_DIR/requirements.txt" .
cp -f  "$PATCH_DIR/Dockerfile" .

# .env.example mis à jour (sans toucher au .env existant)
cp -f "$PATCH_DIR/.env.example" .

echo "📁 Copie des fichiers frontend..."
mkdir -p frontend/src
cp -rf "$PATCH_DIR/frontend/src/api" frontend/src/
cp -rf "$PATCH_DIR/frontend/src/components" frontend/src/
cp -rf "$PATCH_DIR/frontend/src/hooks" frontend/src/
cp -rf "$PATCH_DIR/frontend/src/lib" frontend/src/
cp -rf "$PATCH_DIR/frontend/src/pages" frontend/src/
cp -rf "$PATCH_DIR/frontend/src/types" frontend/src/
cp -f  "$PATCH_DIR/frontend/src/App.tsx" frontend/src/
cp -f  "$PATCH_DIR/frontend/src/main.tsx" frontend/src/
cp -f  "$PATCH_DIR/frontend/src/styles.css" frontend/src/
cp -f  "$PATCH_DIR/frontend/package.json" frontend/
cp -f  "$PATCH_DIR/frontend/vite.config.ts" frontend/
cp -f  "$PATCH_DIR/frontend/tsconfig.json" frontend/
cp -f  "$PATCH_DIR/frontend/tailwind.config.js" frontend/
cp -f  "$PATCH_DIR/frontend/postcss.config.js" frontend/
cp -f  "$PATCH_DIR/frontend/index.html" frontend/
cp -f  "$PATCH_DIR/frontend/Dockerfile" frontend/
cp -f  "$PATCH_DIR/frontend/nginx.conf" frontend/

echo "📁 Copie de docker-compose..."
cp -f "$PATCH_DIR/docker-compose.coolify.yml" .

echo "📁 Copie de la documentation..."
mkdir -p docs
cp -rf "$PATCH_DIR/docs/." docs/
cp -f  "$PATCH_DIR/README-PATCH-PHASE-1.md" .

# -----------------------------------------------------------------
# 3. Permissions exécutables
# -----------------------------------------------------------------
chmod +x scripts/migrate.sh

# -----------------------------------------------------------------
# 4. Récap
# -----------------------------------------------------------------
echo ""
echo "✅ Patch appliqué avec succès."
echo ""
echo "📋 Étapes suivantes :"
echo "   1. Vérifier le diff :  git diff --stat"
echo "   2. Compléter .env (depuis .env.example si nouveau)"
echo "   3. Tester en local :   docker compose -f docker-compose.coolify.yml up --build"
echo "   4. Commit + push :     git add -A && git commit -m 'feat(phase-1): patch'"
echo ""
echo "🚀 Sur Coolify : redéployer la branche après push."
