#!/bin/bash
# Script d'application du Patch Phase 1
# Usage: ./apply-patch.sh

set -e

echo "🔧 Application du Patch Phase 1 - B2B Prospector"
echo "================================================"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Vérifier qu'on est dans le bon dossier
if [ ! -f "main.py" ] && [ ! -d "patch-phase-1" ]; then
    echo -e "${RED}Erreur: Ce script doit être exécuté depuis la racine du projet${NC}"
    exit 1
fi

# Si on est dans patch-phase-1, remonter
if [ -f "README-PATCH-PHASE-1.md" ]; then
    cd ..
fi

echo -e "${YELLOW}Étape 1/5: Copie des fichiers de configuration...${NC}"
cp -n patch-phase-1/.env.example .env 2>/dev/null || echo "  .env existe déjà"
cp patch-phase-1/alembic.ini . 2>/dev/null || true
cp patch-phase-1/requirements.txt . 2>/dev/null || true

echo -e "${YELLOW}Étape 2/5: Installation des dépendances Python...${NC}"
pip install -r requirements.txt --quiet

echo -e "${YELLOW}Étape 3/5: Exécution des migrations Alembic...${NC}"
cd patch-phase-1
python -m alembic upgrade head
cd ..

echo -e "${YELLOW}Étape 4/5: Seeding de la base de données...${NC}"
python scripts/seed.py

echo -e "${YELLOW}Étape 5/5: Activation des plugins...${NC}"
python scripts/activate_plugins.py

echo -e "${GREEN}✅ Patch Phase 1 appliqué avec succès!${NC}"
echo ""
echo "Prochaines étapes:"
echo "  1. Modifier .env avec vos paramètres (SMTP PlanetHoster)"
echo "  2. Redémarrer les conteneurs: docker-compose -f docker-compose.coolify.yml up -d"
echo "  3. Accéder à l'application: http://localhost:8080"
echo ""
echo "📖 Consultez README-PATCH-PHASE-1.md pour plus de détails"
