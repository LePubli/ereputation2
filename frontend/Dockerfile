# syntax=docker/dockerfile:1.7
###############################################################################
# B2B Prospector — Frontend Dockerfile (Production-Ready) — v5
# Stack : React 18 + Vite 5 + TypeScript + Tailwind + Nginx
# Build : multi-stage, BuildKit, layer caching, non-root user
# Cible : Coolify (Docker 29.x) sur Ubuntu 24 LTS
#
# Compatibilité runtime :
#   - USER nginx (uid 101) — non-root
#   - read_only: true accepté (tmpfs sur /tmp seulement)
#   - aucun chown runtime nécessaire (tout est /tmp/nginx/* writable)
###############################################################################

# ----- STAGE 1 : DEPENDENCIES (cache npm dédié) ------------------------------
FROM node:20-alpine AS deps
WORKDIR /app

RUN apk add --no-cache libc6-compat && \
    rm -rf /var/cache/apk/*

COPY package.json package-lock.json* ./

RUN --mount=type=cache,target=/root/.npm \
    if [ -f package-lock.json ]; then \
        npm ci --no-audit --no-fund --prefer-offline \
        || (echo "WARN: npm ci a echoue, fallback sur npm install --legacy-peer-deps" \
            && rm -rf node_modules \
            && npm install --no-audit --no-fund --legacy-peer-deps); \
    else \
        npm install --no-audit --no-fund --legacy-peer-deps; \
    fi && \
    # Nettoyage post-install pour réduire la taille
    rm -rf /root/.npm/_cacache

# ----- STAGE 2 : BUILDER (compilation Vite) ----------------------------------
FROM node:20-alpine AS builder
WORKDIR /app

ARG VITE_API_BASE_URL=/api
ARG VITE_APP_NAME="B2B Prospector"
ARG VITE_APP_VERSION=1.0.0
ARG VITE_SENTRY_DSN=""

# Cache-buster : valeur unique injectée par Coolify (commit SHA, build timestamp...))
# Force le rebuild même si rien d'autre n'a changé. Coolify l'injecte automatiquement
# via COOLIFY_BUILD_SECRETS_HASH ou un argument équivalent.
ARG CACHEBUST=1

ENV VITE_API_BASE_URL=${VITE_API_BASE_URL} \
    VITE_APP_NAME=${VITE_APP_NAME} \
    VITE_APP_VERSION=${VITE_APP_VERSION} \
    VITE_SENTRY_DSN=${VITE_SENTRY_DSN} \
    NODE_ENV=production

COPY --from=deps /app/node_modules ./node_modules

# IMPORTANT : Nettoyage agressif pour éviter les conflits de cache BuildKit
# On supprime dist AVANT de copier le reste du code source
RUN rm -rf /app/dist 2>/dev/null || true

COPY . .

# Second nettoyage après copie pour garantir un état propre
RUN rm -rf /app/dist 2>/dev/null || true

# Build Vite + sanity checks renforcés avec debug complet
RUN echo "===> Build for cachebust=${CACHEBUST}" && \
    echo "===> Node version: $(node -v)" && \
    echo "===> NPM version: $(npm -v)" && \
    echo "===> Mémoire disponible:" && free -m 2>/dev/null || cat /proc/meminfo | head -5 && \
    echo "===> Espace disque:" && df -h / && \
    echo "===> Contenu du dossier /app:" && ls -la /app/ && \
    echo "===> Démarrage du build Vite..." && \
    echo "===> Variables d'environnement Vite:" && \
    env | grep VITE_ && \
    echo "===> Toutes les variables d'environnement:" && \
    env | sort && \
    echo "===> Exécution de npm run build avec NODE_OPTIONS=--max-old-space-size=4096" && \
    export NODE_OPTIONS="--max-old-space-size=4096" && \
    echo "=== DEBUT OUTPUT NPM RUN BUILD ===" && \
    if ! npm run build > /tmp/build_stdout.log 2> /tmp/build_stderr.log; then \
        BUILD_EXIT=$?; \
        echo "" && \
        echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" && \
        echo "ERREUR CRITIQUE: npm run build a échoué avec code $BUILD_EXIT !" && \
        echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" && \
        echo "" && \
        echo "=== STDOUT (sortie standard) ===" && \
        cat /tmp/build_stdout.log && \
        echo "" && \
        echo "=== STDERR (sortie d'erreur) ===" && \
        cat /tmp/build_stderr.log && \
        echo "" && \
        echo "=== Informations complémentaires ===" && \
        echo "Contenu de node_modules (premiers 30):" && \
        ls node_modules 2>/dev/null | head -30 && \
        echo "" && \
        echo "Package.json:" && \
        cat package.json && \
        echo "" && \
        echo "Espace disque après échec:" && df -h / && \
        echo "" && \
        echo "Mémoire après échec:" && free -m 2>/dev/null || cat /proc/meminfo | head -5 && \
        exit $BUILD_EXIT; \
    fi && \
    echo "=== FIN OUTPUT NPM RUN BUILD ===" && \
    echo "===> Vérification des artifacts..." && \
    if [ ! -d /app/dist ]; then \
        echo "ERREUR: le dossier dist/ n'existe pas !" && \
        echo "Contenu de /app:" && ls -la /app/ && \
        exit 1; \
    fi && \
    if [ ! -f /app/dist/index.html ]; then \
        echo "ERREUR: dist/index.html n'existe pas !" && \
        echo "Contenu de /app/dist:" && ls -la /app/dist/ && \
        exit 1; \
    fi && \
    if ! grep -q '<script type="module" crossorigin src="/assets/' /app/dist/index.html; then \
        echo "ERREUR: dist/index.html ne contient pas les scripts buildés !" && \
        echo "--- contenu de dist/index.html ---" && \
        cat /app/dist/index.html && \
        exit 1; \
    fi && \
    echo "===> Build artifacts:" && \
    ls -la /app/dist/ && \
    echo "===> Assets:" && \
    ls -la /app/dist/assets/ | head -20

# ----- STAGE 3 : RUNTIME (Nginx Alpine, non-root) ----------------------------
FROM nginx:1.27-alpine AS production

LABEL org.opencontainers.image.title="b2b-prospector-frontend" \
      org.opencontainers.image.description="Copilote Commercial B2B - Frontend React/Vite" \
      org.opencontainers.image.vendor="Epok" \
      org.opencontainers.image.source="https://github.com/LePubli/ereputation2" \
      org.opencontainers.image.licenses="Proprietary"

RUN apk add --no-cache curl tini tzdata

# Remplacement complet du nginx.conf principal
RUN rm -f /etc/nginx/nginx.conf /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/nginx.conf

# Copie des assets buildés (NB : si dist/ contient un dossier public/ avec
# vite.svg, etc., il est aussi copié → résoud le 404 sur /vite.svg)
COPY --from=builder /app/dist /usr/share/nginx/html

# Préparation /tmp/nginx pour mode non-root + read-only
RUN mkdir -p /tmp/nginx \
             /tmp/nginx/client_temp \
             /tmp/nginx/proxy_temp \
             /tmp/nginx/fastcgi_temp \
             /tmp/nginx/uwsgi_temp \
             /tmp/nginx/scgi_temp && \
    chown -R nginx:nginx /tmp/nginx /usr/share/nginx/html && \
    chmod -R 755 /tmp/nginx

COPY --chmod=755 docker-entrypoint.sh /docker-entrypoint.sh

USER nginx

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8080/healthz || exit 1

ENTRYPOINT ["/sbin/tini", "--", "/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
