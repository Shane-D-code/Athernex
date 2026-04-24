# ============================================================
# Athernex Voice Order System — Production Dockerfile
# Multi-stage build for minimal final image
# ============================================================

# ---------- Stage 1: Build dependencies ----------
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build-essential for any compiled wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- Stage 2: Runtime ----------
FROM python:3.12-slim AS runtime

LABEL maintainer="Athernex Team"
LABEL description="Multilingual Voice Order System — local-first, GPU-accelerated"

WORKDIR /app

# Install runtime system deps (audio processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY src/ ./src/
COPY main.py .
COPY demo.html .
COPY requirements.txt .

# Set Python path so modules resolve
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Default environment variables
ENV WHISPER_BASE_URL=http://whisper:8000
ENV OLLAMA_BASE_URL=http://ollama:11434
ENV WHISPER_MODEL=medium
ENV OLLAMA_MODEL=llama3.1:8b-instruct-q4_K_M

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8100/health')" || exit 1

EXPOSE 8100

CMD ["python", "main.py"]
