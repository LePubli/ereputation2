# syntax=docker/dockerfile:1.7
###############################################################################
# B2B Prospector — Frontend Dockerfile (Production-Ready)
# Stack : React 18 + Vite 5 + TypeScript + Tailwind + Nginx
# Build : multi-stage, BuildKit, layer caching, non-root user
# Cible : Coolify (Docker 29.x) sur Ubuntu 24 LTS
###############################################################################

# ----- STAGE 1 : DEPENDENCIES (cache npm dédié) ------------------------------
FROM node:20-alpine AS deps
WORKDIR /app

# Outils nécessaires à certaines deps natives (sharp, esbuild, etc.)
RUN apk add --no-cache libc6-compat

# Copie uniquement les manifests pour maximiser le cache Docker
COPY package.json package-lock.json* ./

# Cache mount BuildKit pour npm (gain x3 sur builds incrémentaux).
# Stratégie d'install résiliente :
#   1. Si lock présent → tente `npm ci` (rapide, déterministe)
#   2. Si `npm ci` échoue (lock désynchronisé / conflits peer-deps) →
#      fallback `npm install --legacy-peer-deps` qui régénère un tree cohérent
#   3. Si pas de lock → directement `npm install`
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

# Args injectés par Coolify au build (visibles dans le bundle final)
# /!\ NE JAMAIS injecter de secret runtime ici — le bundle JS est public.
ARG VITE_API_BASE_URL=/api
ARG VITE_APP_NAME="B2B Prospector"
ARG VITE_APP_VERSION=1.0.0
ARG VITE_SENTRY_DSN=""

ENV VITE_API_BASE_URL=${VITE_API_BASE_URL} \
    VITE_APP_NAME=${VITE_APP_NAME} \
    VITE_APP_VERSION=${VITE_APP_VERSION} \
    VITE_SENTRY_DSN=${VITE_SENTRY_DSN} \
    NODE_ENV=production

# Récupère les deps installées dans le stage précédent
COPY --from=deps /app/node_modules ./node_modules

# Copie le code source (le .dockerignore exclut ce qui ne sert pas)
COPY . .

# Build Vite (script 'build' = vite build seul, tsc separe via 'typecheck')
RUN npm run build && \
    test -d /app/dist && test -f /app/dist/index.html

# ----- STAGE 3 : RUNTIME (Nginx Alpine, non-root) ----------------------------
FROM nginx:1.27-alpine AS production

# Metadonnees OCI
LABEL org.opencontainers.image.title="b2b-prospector-frontend" \
      org.opencontainers.image.description="Copilote Commercial B2B - Frontend React/Vite" \
      org.opencontainers.image.vendor="Epok" \
      org.opencontainers.image.source="https://github.com/LePubli/ereputation2" \
      org.opencontainers.image.licenses="Proprietary"

# Outils : curl pour healthcheck, tini comme init PID 1, tzdata pour logs
RUN apk add --no-cache curl tini tzdata && \
    rm -f /etc/nginx/conf.d/default.conf

# Copie de la conf nginx custom (SPA + proxy API + headers securite)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copie des assets buildes
COPY --from=builder --chown=nginx:nginx /app/dist /usr/share/nginx/html

# Preparation pour execution non-root (port non privilegie 8080)
RUN sed -i 's/listen       80;/listen       8080;/g' /etc/nginx/conf.d/default.conf 2>/dev/null || true
RUN mkdir -p /var/cache/nginx/client_temp /var/cache/nginx/proxy_temp /var/cache/nginx/fastcgi_temp /var/cache/nginx/uwsgi_temp /var/cache/nginx/scgi_temp
RUN chown -R nginx:nginx /usr/share/nginx/html /var/cache/nginx /var/log/nginx /etc/nginx/conf.d

USER nginx

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8080/healthz || exit 1

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["nginx", "-g", "daemon off;"]
