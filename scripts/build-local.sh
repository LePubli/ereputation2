#!/usr/bin/env bash
# ============================================================================
# build-local.sh — Test du build Docker en local avant push Coolify
# ----------------------------------------------------------------------------
# Prérequis : Docker 24+ avec BuildKit + Buildx (déjà inclus sur Docker 29.x)
# Usage     : ./scripts/build-local.sh [frontend|backend|all]
# ============================================================================

set -euo pipefail

# Couleurs
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

log()   { echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} $*"; }
ok()    { echo -e "${GREEN}✔${NC} $*"; }
warn()  { echo -e "${YELLOW}⚠${NC} $*"; }
err()   { echo -e "${RED}✖${NC} $*" >&2; }

# Working dir = racine du projet (parent de scripts/)
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

TARGET="${1:-all}"
PLATFORM="${PLATFORM:-linux/amd64}"
TAG="${TAG:-test}"

# Activer BuildKit (déjà par défaut sur Docker 23+, mais on s'assure)
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# ----- Vérifications préalables ----------------------------------------------
if ! command -v docker &>/dev/null; then
    err "Docker n'est pas installé"
    exit 1
fi

if ! docker buildx version &>/dev/null; then
    err "Docker Buildx requis (Docker 24+ ou plugin buildx)"
    exit 1
fi

# Builder dédié (création idempotente)
if ! docker buildx inspect ereputation-builder &>/dev/null; then
    log "Création du builder Buildx 'ereputation-builder'..."
    docker buildx create --name ereputation-builder --use --bootstrap
else
    docker buildx use ereputation-builder
fi

# ----- BUILD FRONTEND --------------------------------------------------------
build_frontend() {
    log "🏗️  Build frontend (platform=$PLATFORM, tag=$TAG)..."
    docker buildx build \
        --platform "$PLATFORM" \
        --build-arg VITE_API_BASE_URL="/api" \
        --build-arg VITE_APP_NAME="B2B Prospector" \
        --build-arg VITE_APP_VERSION="1.0.0" \
        --build-arg VITE_SENTRY_DSN="" \
        --tag "ereputation2-frontend:${TAG}" \
        --load \
        --progress=plain \
        ./frontend
    ok "Frontend buildé : ereputation2-frontend:${TAG}"
    docker images "ereputation2-frontend:${TAG}" --format "  Size: {{.Size}}"
}

# ----- BUILD BACKEND ---------------------------------------------------------
build_backend() {
    log "🏗️  Build backend (platform=$PLATFORM, tag=$TAG)..."
    docker buildx build \
        --platform "$PLATFORM" \
        --tag "ereputation2-backend:${TAG}" \
        --load \
        --progress=plain \
        .
    ok "Backend buildé : ereputation2-backend:${TAG}"
    docker images "ereputation2-backend:${TAG}" --format "  Size: {{.Size}}"
}

# ----- TEST RUN (smoke test) -------------------------------------------------
smoke_test() {
    log "🧪 Smoke test des images..."

    # Frontend
    if docker images "ereputation2-frontend:${TAG}" -q | grep -q .; then
        log "  → Démarrage frontend sur :18080..."
        docker rm -f ereputation2-frontend-smoke 2>/dev/null || true
        docker run -d --name ereputation2-frontend-smoke -p 18080:8080 \
            "ereputation2-frontend:${TAG}" >/dev/null
        sleep 3
        if curl -fsS http://localhost:18080/healthz >/dev/null; then
            ok "  Frontend répond sur /healthz"
        else
            err "  Frontend ne répond pas"
            docker logs ereputation2-frontend-smoke
        fi
        docker rm -f ereputation2-frontend-smoke >/dev/null
    fi

    # Backend (sans dépendances DB/Redis, donc /health peut échouer)
    if docker images "ereputation2-backend:${TAG}" -q | grep -q .; then
        log "  → Vérification de l'image backend..."
        docker run --rm "ereputation2-backend:${TAG}" python -c "import main; print('✓ Import OK')" \
            && ok "  Backend imports valides" \
            || warn "  Backend imports échouent (vérifier requirements)"
    fi
}

# ----- DISPATCH --------------------------------------------------------------
case "$TARGET" in
    frontend) build_frontend ;;
    backend)  build_backend  ;;
    all)      build_frontend && build_backend && smoke_test ;;
    *)        err "Usage: $0 [frontend|backend|all]"; exit 1 ;;
esac

ok "Build terminé."
echo ""
echo "Étapes suivantes :"
echo "  - Tester en stack complète : docker compose -f docker-compose.coolify.yml up"
echo "  - Push sur Git → Coolify déploiera automatiquement"
