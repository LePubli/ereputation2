# syntax=docker/dockerfile:1.7
###############################################################################
# B2B Prospector — Backend Dockerfile (Production-Ready)
# Stack : Python 3.11 + FastAPI + Uvicorn + Loguru + Redis + PostgreSQL
# Build : multi-stage (builder + runtime), non-root, image slim
# Cible : Coolify (Docker 29.x) sur Ubuntu 24 LTS
###############################################################################

# ----- STAGE 1 : BUILDER (compile wheels, build deps) ------------------------
FROM python:3.11-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /build

# Build deps pour wheels natifs (lxml, psycopg2, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libpq-dev \
        libxml2-dev \
        libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dans un préfixe isolé qu'on copiera dans le runtime stage
# Cache mount BuildKit : énorme gain sur builds incrémentaux
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --user --no-warn-script-location -r requirements.txt && \
    # Ajout PostgreSQL driver async (manquant dans requirements.txt)
    pip install --user --no-warn-script-location 'asyncpg>=0.29.0' 'psycopg2-binary>=2.9.9'

# ----- STAGE 2 : RUNTIME (image finale, slim) --------------------------------
FROM python:3.11-slim-bookworm AS production

# Métadonnées OCI
LABEL org.opencontainers.image.title="b2b-prospector-backend" \
      org.opencontainers.image.description="Copilote Commercial B2B - API FastAPI" \
      org.opencontainers.image.vendor="Epok" \
      org.opencontainers.image.licenses="Proprietary"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH=/home/appuser/.local/bin:$PATH \
    PIP_NO_CACHE_DIR=1

# Runtime deps uniquement (pas de build tools dans l'image finale)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        tini \
        libpq5 \
        libxml2 \
        libxslt1.1 \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    # User non-root
    && groupadd --system --gid 1000 appuser \
    && useradd --system --uid 1000 --gid 1000 --create-home --shell /bin/bash appuser

WORKDIR /app

# Récupère les paquets Python du stage builder
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Code applicatif (le .dockerignore fait le ménage)
COPY --chown=appuser:appuser core/         ./core/
COPY --chown=appuser:appuser plugins/      ./plugins/
COPY --chown=appuser:appuser models/       ./models/
COPY --chown=appuser:appuser services/     ./services/
COPY --chown=appuser:appuser utils/        ./utils/
COPY --chown=appuser:appuser repositories/ ./repositories/
COPY --chown=appuser:appuser main.py       ./

# Crée les dossiers writables avant de basculer en non-root
RUN mkdir -p /app/logs /app/data /app/tmp && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Healthcheck sans proxy env : socket HTTP direct vers /health.
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=5 \
    CMD python -c "import socket,sys; s=socket.create_connection(('127.0.0.1',8000),5); s.sendall(b'GET /health HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n'); data=s.recv(128); s.close(); sys.exit(0 if b' 200 ' in data else 1)"

# tini = init PID 1 (gestion des signaux, reaping zombies)
ENTRYPOINT ["/usr/bin/tini", "--"]

# Production : pas de --reload, plusieurs workers, access log via Loguru
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*", \
     "--no-access-log"]
