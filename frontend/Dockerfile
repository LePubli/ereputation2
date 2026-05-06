# syntax=docker/dockerfile:1.7
###############################################################################
# B2B Prospector — Frontend Dockerfile (Production-Ready)
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

# Stratégie d'install résiliente :
#   1. lock présent → tente `npm ci` (rapide, déterministe)
#   2. `npm ci` échoue (lock désync / peer-deps) → fallback `npm install --legacy-peer-deps`
#   3. pas de lock → directement `npm install`
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

ENV VITE_API_BASE_URL=${VITE_API_BASE_URL} \
    VITE_APP_NAME=${VITE_APP_NAME} \
    VITE_APP_VERSION=${VITE_APP_VERSION} \
    VITE_SENTRY_DSN=${VITE_SENTRY_DSN} \
    NODE_ENV=production

COPY --from=deps /app/node_modules ./node_modules
COPY . .

RUN npm run build && \
    test -d /app/dist && test -f /app/dist/index.html

# ----- STAGE 3 : RUNTIME (Nginx Alpine, non-root) ----------------------------
FROM nginx:1.27-alpine AS production

LABEL org.opencontainers.image.title="b2b-prospector-frontend" \
      org.opencontainers.image.description="Copilote Commercial B2B - Frontend React/Vite" \
      org.opencontainers.image.vendor="Epok" \
      org.opencontainers.image.source="https://github.com/LePubli/ereputation2" \
      org.opencontainers.image.licenses="Proprietary"

# Outils runtime : curl pour healthcheck, tini pour PID 1, tzdata pour logs
RUN apk add --no-cache curl tini tzdata

# ---- REMPLACEMENT COMPLET du nginx.conf ------------------------------------
# La conf custom redirige les `*_temp_path` et le `pid` vers /tmp/nginx
# pour rester compatible avec un filesystem read-only en runtime.
RUN rm -f /etc/nginx/nginx.conf /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/nginx.conf

# Assets buildés
COPY --from=builder /app/dist /usr/share/nginx/html

# ---- Préparation runtime non-root + read-only-friendly --------------------
# /tmp/nginx est créé au build avec les bonnes permissions, mais nginx
# le recréera de toute façon à chaque démarrage si /tmp est un tmpfs.
# On crée aussi un wrapper d'entrée qui s'assure que la structure existe.
RUN mkdir -p /tmp/nginx \
             /tmp/nginx/client_temp \
             /tmp/nginx/proxy_temp \
             /tmp/nginx/fastcgi_temp \
             /tmp/nginx/uwsgi_temp \
             /tmp/nginx/scgi_temp && \
    chown -R nginx:nginx /tmp/nginx /usr/share/nginx/html && \
    chmod -R 755 /tmp/nginx

# ---- Wrapper qui (re)crée /tmp/nginx au démarrage si tmpfs vide -----------
# Coolify monte tmpfs:/tmp → vide à chaque restart. Sans ce script, nginx
# planterait sur le 1er démarrage avec read_only:true.
COPY --chmod=755 docker-entrypoint.sh /docker-entrypoint.sh

USER nginx

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8080/healthz || exit 1

ENTRYPOINT ["/sbin/tini", "--", "/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
