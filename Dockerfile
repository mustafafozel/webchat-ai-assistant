<<<<<<< HEAD
# ======================
# 1. BASE (Builder) aşaması
# ======================
FROM python:3.11-slim AS builder

WORKDIR /app

# Sistem bağımlılıkları (yalnızca ihtiyaç duyulanlar)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Gereksiz rebuild’leri önlemek için requirements.txt'yi ayrı kopyala
COPY requirements.txt .

# Pip cache kullanımı: requirements değişmediği sürece katman sabit kalır
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# ======================
# 2. RUNNER aşaması
# ======================
FROM python:3.11-slim

WORKDIR /app

# Bağımlılıkları builder'dan kopyala (daha az disk kullanımı)
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin

# Uygulama kodu
COPY . .

# Ortam değişkenleri
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Varsayılan port
EXPOSE 8000

# Uygulama çalıştırma
=======
# === Builder Stage ===
FROM python:3.11-slim as builder

WORKDIR /app

# Sistem bağımlılıkları (PostgreSQL için)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python bağımlılıkları
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --user --no-cache-dir -r requirements.txt

# === Runtime Stage ===
FROM python:3.11-slim

WORKDIR /app

# PostgreSQL client kütüphanesi
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Python paketlerini builder'dan kopyala
COPY --from=builder /root/.local /root/.local

# Uygulama kodunu kopyala
COPY . .

# PATH'e ekle
ENV PATH=/root/.local/bin:$PATH

# Port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/health')" || exit 1

# Uygulama başlat
>>>>>>> 65eb5aa (feat: major update - LangGraph ReAct agent implementation)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

