# Multi-Agent Backend Dockerfile (GCP Cloud Run ready)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=8000

WORKDIR /app

# System deps (Postgres client libs + vision/OCR tooling used by agents)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libsqlite3-dev \
    curl \
    git \
    libopencv-dev \
    python3-opencv \
    tesseract-ocr \
    libtesseract-dev \
    ffmpeg \
    libsm6 \
    libxext6 \
    libfontconfig1 \
    libxrender1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/media /app/staticfiles /app/logs \
    && sed -i 's/\r$//' /app/entrypoint.sh \
    && chmod +x /app/manage.py /app/entrypoint.sh

# collectstatic at build time (no real secrets required)
ENV DEBUG=False \
    SECRET_KEY=build-time-only-secret-key-not-used-at-runtime-60chars \
    ALLOWED_HOSTS=localhost \
    REDIS_URL=redis://127.0.0.1:6379/0 \
    DATABASE_URL=sqlite:///build.sqlite3 \
    LOG_TO_FILE=False \
    SECURE_SSL_REDIRECT=False

RUN python manage.py collectstatic --noinput --clear

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f "http://localhost:${PORT:-8000}/health/live/" || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
