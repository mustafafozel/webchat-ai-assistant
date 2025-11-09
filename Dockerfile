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
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

