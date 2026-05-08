# ====================================
# B2B Prospector — Frontend Dockerfile
# Vite build → Nginx static
# ====================================

# ---------- Build stage ----------
FROM node:20-alpine AS build

WORKDIR /app

# Outils requis pour certaines deps natives
RUN apk add --no-cache python3 make g++

COPY package.json package-lock.json* ./
# --legacy-peer-deps pour éviter les conflits de peer dependencies
RUN npm install --no-audit --no-fund --legacy-peer-deps

COPY . .

ARG VITE_API_URL=/api/v1
ARG VITE_APP_NAME="B2B Prospector"
ARG VITE_APP_VERSION=1.1.0

ENV VITE_API_URL=$VITE_API_URL \
    VITE_APP_NAME=$VITE_APP_NAME \
    VITE_APP_VERSION=$VITE_APP_VERSION \
    NODE_ENV=production

RUN npm run build

# ---------- Runtime stage ----------
FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://localhost:8080/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
