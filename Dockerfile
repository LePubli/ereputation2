# ====================================
# B2B Prospector — Backend Dockerfile
# Python 3.11 + Playwright (Chromium)
# ====================================

FROM python:3.11-slim AS base

# Variables d'env
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Dépendances système (Playwright + libs scraping)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libpq-dev \
    gcc \
    g++ \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    zlib1g-dev \
    # Playwright Chromium runtime
    libnss3 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libgtk-3-0 \
    fonts-liberation \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Chromium pour Playwright
RUN python -m playwright install chromium && \
    python -m playwright install-deps chromium || true

# Copie du code applicatif
COPY core/ ./core/
COPY models/ ./models/
COPY plugins/ ./plugins/
COPY services/ ./services/
COPY scripts/ ./scripts/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY main.py ./

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -fsS http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--proxy-headers"]
