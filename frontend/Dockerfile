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

RUN apk add --no-cache libc6-compat

COPY package.json package-lock.json* ./

RUN --mount=type=cache,target=/root/.npm \
    if [ -f package-lock.json ]; then \
        npm ci --no-audit --no-fund --prefer-offline \
        || (echo "WARN: npm ci a echoue, fallback sur npm install --legacy-peer-deps" \
            && rm -rf node_modules \
            && npm install --no-audit --no-fund --legacy-peer-deps); \
    else \
        npm install --no-audit --no-fund --legacy-peer-deps; \
    fi

# ----- STAGE 2 : BUILDER (compilation Vite) ----------------------------------
FROM node:20-alpine AS builder
WORKDIR /app

ARG VITE_API_BASE_URL=/api
ARG VITE_APP_NAME="B2B Prospector"
ARG VITE_APP_VERSION=1.0.0
ARG VITE_SENTRY_DSN=""

# Cache-buster : valeur unique injectée par Coolify (commit SHA, build timestamp...)
# Force le rebuild même si rien d'autre n'a changé. Coolify l'injecte automatiquement
# via COOLIFY_BUILD_SECRETS_HASH ou un argument équivalent.
ARG CACHEBUST=1

ENV VITE_API_BASE_URL=${VITE_API_BASE_URL} \
    VITE_APP_NAME=${VITE_APP_NAME} \
    VITE_APP_VERSION=${VITE_APP_VERSION} \
    VITE_SENTRY_DSN=${VITE_SENTRY_DSN} \
    NODE_ENV=production

COPY --from=deps /app/node_modules ./node_modules

# IMPORTANT : on supprime tout dist/ éventuellement présent dans le contexte
# avant de copier, puis on supprime aussi un dist/ qui aurait été copié, pour
# forcer un build neuf (évite les builds Coolify qui réutilisent un vieux dist/).
COPY . .
RUN rm -rf /app/dist

# Build Vite + sanity checks renforcés
RUN echo "===> Build for cachebust=${CACHEBUST}" && \
    npm run build && \
    test -d /app/dist && test -f /app/dist/index.html && \
    # Vérifie que index.html contient bien les balises <script> injectées par Vite
    # (sinon le HTML est resté à la version source, l'app ne démarrera pas)
    grep -q '<script type="module" crossorigin src="/assets/' /app/dist/index.html \
        || (echo "ERREUR: dist/index.html ne contient pas les scripts buildés !" && \
            echo "--- contenu de dist/index.html ---" && \
            cat /app/dist/index.html && \
            exit 1) && \
    # Affiche les hash des assets pour faciliter le diagnostic
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
