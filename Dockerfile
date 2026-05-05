--- Dockerfile (原始)
# B2B Prospector - Dockerfile Production-Ready
FROM python:3.11-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY core/ ./core/
COPY plugins/ ./plugins/
COPY main.py .
COPY models/ ./models/
COPY services/ ./services/
COPY utils/ ./utils/

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

+++ Dockerfile (修改后)
     1	# B2B Prospector - Dockerfile Production-Ready
     2	FROM python:3.11-slim
     3	
     4	# Environment variables
     5	ENV PYTHONDONTWRITEBYTECODE=1 \
     6	    PYTHONUNBUFFERED=1 \
     7	    PIP_NO_CACHE_DIR=1 \
     8	    PIP_DISABLE_PIP_VERSION_CHECK=1
     9	
    10	# Working directory
    11	WORKDIR /app
    12	
    13	# Install system dependencies
    14	RUN apt-get update && apt-get install -y --no-install-recommends \
    15	    curl \
    16	    && rm -rf /var/lib/apt/lists/*
    17	
    18	# Copy requirements first for better caching
    19	COPY requirements.txt .
    20	
    21	# Install Python dependencies
    22	RUN pip install --no-cache-dir -r requirements.txt
    23	
    24	# Copy application code
    25	COPY core/ ./core/
    26	COPY plugins/ ./plugins/
    27	COPY main.py .
    28	COPY models/ ./models/
    29	COPY services/ ./services/
    30	COPY utils/ ./utils/
    31	
    32	# Create non-root user for security
    33	RUN useradd --create-home --shell /bin/bash appuser && \
    34	    chown -R appuser:appuser /app && \
    35	    mkdir -p /app/logs /app/data && \
    36	    chown -R appuser:appuser /app/logs /app/data
    37	USER appuser
    38	
    39	# Expose port
    40	EXPOSE 8000
    41	
    42	# Health check
    43	HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    44	    CMD curl -f http://localhost:8000/health || exit 1
    45	
    46	# Run the application
    47	CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
    48	
