#!/usr/bin/env bash
set -e

echo "🚀 Gelişmiş Docker port düzeltme başlatılıyor..."
echo "------------------------------------------------"

# 🔍 5557 portunu hangi süreç tutuyor?
PID=$(sudo lsof -t -i:5557 || true)
if [ -n "$PID" ]; then
  echo "⚠️ Port 5557 şu PID tarafından tutuluyor: $PID"
  echo "🔧 Süreç sonlandırılıyor..."
  sudo kill -9 $PID || true
  sleep 1
else
  echo "✅ Port 5557 boşta."
fi

# 🔍 Eski rootlesskit süreçleri
echo ""
echo "🧹 RootlessKit süreçleri temizleniyor..."
ps aux | grep rootlesskit | grep -v grep | awk '{print $2}' | xargs -r sudo kill -9 || true

# 🔍 Tüm container ve ağları kaldır
echo ""
echo "🧹 Eski konteynerler ve ağlar temizleniyor..."
docker ps -aq | xargs -r docker rm -f || true
docker network prune -f || true
docker volume prune -f || true

# 🔧 Eğer 5557 dolu kalırsa otomatik 5433'e geç
if ss -ltn | grep -q ":5557"; then
    echo "⚠️ Port 5557 hâlâ meşgul. docker-compose.yml içinde portu 5433:5432 olarak değiştiriliyor..."
    sed -i 's/5557:5432/5433:5432/' docker-compose.yml || true
else
    echo "✅ Port 5557 kullanılabilir durumda."
fi

# 🧼 Gereksiz sistem artıkları
echo ""
echo "🧽 Sistem artıkları temizleniyor..."
docker system prune -af --volumes || true

# 🔁 Docker yeniden başlat
echo ""
echo "🔁 Docker yeniden başlatılıyor..."
systemctl --user restart docker || true

# 🚀 Uygulamayı yeniden başlat
echo ""
echo "🚀 Servisler başlatılıyor..."
docker compose up -d

echo ""
echo "✅ Her şey temiz! Durum kontrolü:"
docker ps

