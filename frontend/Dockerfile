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

# Cache mount BuildKit pour npm (gain x3 sur builds incrémentaux)
RUN --mount=type=cache,target=/root/.npm \
    if [ -f package-lock.json ]; then \
        npm ci --no-audit --no-fund --prefer-offline; \
    else \
        npm install --no-audit --no-fund --legacy-peer-deps; \
    fi

# ----- STAGE 2 : BUILDER (compilation Vite) ----------------------------------
FROM node:20-alpine AS builder
WORKDIR /app

# Args injectés par Coolify au build (visibles dans le bundle final)
# ⚠️ NE JAMAIS injecter de secret runtime ici — le bundle JS est public.
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

# Build Vite (tsc + vite build)
RUN npm run build && \
    # Sanity check : on s'assure que le build a bien généré dist/
    test -d /app/dist && test -f /app/dist/index.html

# ----- STAGE 3 : RUNTIME (Nginx Alpine, non-root) ----------------------------
FROM nginx:1.27-alpine AS production

# Métadonnées OCI (utiles pour Coolify, Trivy, audits)
LABEL org.opencontainers.image.title="b2b-prospector-frontend" \
      org.opencontainers.image.description="Copilote Commercial B2B - Frontend React/Vite" \
      org.opencontainers.image.vendor="Epok" \
      org.opencontainers.image.source="https://github.com/epok/ereputation2" \
      org.opencontainers.image.licenses="Proprietary"

# Outils utiles : curl pour healthcheck, tini comme init PID 1, tzdata pour logs
RUN apk add --no-cache curl tini tzdata && \
    # Nettoyage configuration nginx par défaut
    rm -f /etc/nginx/conf.d/default.conf

# Copie de la conf nginx custom (SPA + proxy API + headers sécurité)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copie des assets buildés
COPY --from=builder --chown=nginx:nginx /app/dist /usr/share/nginx/html

# Préparation pour exécution non-root :
#  - nginx Alpine écoute par défaut sur 80 (privilégié) → on bascule sur 8080
#  - on fixe les permissions des dossiers nécessaires à nginx
RUN sed -i 's/listen       80;/listen       8080;/g' /etc/nginx/conf.d/default.conf 2>/dev/null || true && \
    chown -R nginx:nginx /usr/share/nginx/html /var/cache/nginx /var/log/nginx /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown nginx:nginx /var/run/nginx.pid

# Bascule en utilisateur non-privilégié
USER nginx

# Port non-privilégié (Coolify route via Traefik/Caddy de toute façon)
EXPOSE 8080

# Healthcheck : endpoint dédié plutôt que / (évite de servir index.html à chaque check)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8080/healthz || exit 1

# tini = reaper PID 1 → gestion propre des SIGTERM (Coolify graceful shutdown)
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["nginx", "-g", "daemon off;"]
