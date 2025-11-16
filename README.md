# 🤖 WebChat AI Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?logo=docker&logoColor=white)](https://www.docker.com/)

AI destekli web chat asistanı. Web sitelerinize kolayca entegre edilebilen, LangGraph tabanlı akıllı sohbet botu.

## 🌟 Özellikler

- 🤖 **LangGraph AI Agent** - Akıllı konuşma akışı
- 🔍 **RAG (Retrieval-Augmented Generation)** - Knowledge base entegrasyonu
- 🛠️ **Tool Calling** - Sipariş takip, kargo hesaplama
- ⚡ **WebSocket** - Gerçek zamanlı mesajlaşma
- 🗄️ **PostgreSQL** - Session-based memory
- 🎨 **Embed Widget** - `<script>` ile kolay entegrasyon
- 🐳 **Docker** - Cross-platform deployment
- 🧪 **Test Coverage** - Kapsamlı test suite

## ✅ Teknik Gereksinim Uyum Kontrolü

Bu repo, Etkin.ai teknik değerlendirme dokümanında belirtilen tüm kritik maddeleri yerine getirir:

- **Widget Entegrasyonu**: `/static/widget.js` script'i ile `<script>` etiketi üzerinden gömülebilir chat paneli, otomatik WebSocket bağlantısı ve bağlantı yenileme desteği.
- **Backend API Seti**: `POST /api/chat`, `GET /api/health`, `GET /api/metrics` ve `WS /ws?session_id=` uçları aktif.
- **LangGraph Akışı**: Intent Router → Retriever (RAG) → Tool Caller → Response Builder zinciri ile Groq destekli (opsiyonel) yanıt üretimi.
- **Tool Mock'ları**: `check_order_status`, `calculate_shipping`, `policy_lookup` fonksiyonları teknik şartnamedeki örneklerle bire bir uyumlu.
- **Mini Knowledge Base**: `knowledge/kb.json` dosyasındaki SSS içeriği mini-RAG aramaları için otomatik yüklenir.
- **Metin & Loglama**: WebSocket ve HTTP mesajları için oturum bazlı kayıt, PostgreSQL/SQLite kalıcılığı ve `/api/metrics` üzerinden gerçek zamanlı metrikler.

## 🚀 Hızlı Başlangıç

### Sistem Gereksinimleri

| Platform | Minimum Gereksinimler |
|----------|---------------------|
| **Windows** | Windows 10/11, Docker Desktop |
| **macOS** | macOS 10.15+, Docker Desktop |
| **Linux** | Ubuntu 20.04+, Docker Engine |

## 🚀 Kurulum

```bash
git clone https://github.com/kullaniciadi/webchat-ai-assistant.git
cd webchat-ai-assistant
cp .env.example .env
docker compose up -d --build

Uygulama başlatıldıktan sonra http://localhost:8000

## 🎯 Kullanım

### Chat Widget Entegrasyonu

Web sitenize eklemek için:

```html
<!DOCTYPE html>
<html>
<head>
    <title>My Website</title>
    <!-- WebChat AI CSS -->
    <link rel="stylesheet" href="http://localhost:8000/static/widget.css">
</head>
<body>
    <!-- Sayfa içeriğiniz -->
    
    <!-- WebChat AI Widget -->
    <script src="http://localhost:8000/static/widget.js"></script>
    <script>
        window.WebChatAI.init({
            apiUrl: 'http://localhost:8000',
            sessionId: 'user-' + Math.random().toString(36).substr(2, 9),
            theme: 'light',
            position: 'bottom-right'
        });
    </script>
</body>
</html>
```

### API Kullanımı

#### HTTP Chat Endpoint

```bash
curl -X POST "http://localhost:8000/api/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Siparişimi nasıl takip edebilirim?",
       "session_id": "user123"
     }'
```

#### WebSocket Bağlantısı

```javascript
const ws = new WebSocket('ws://localhost:8000/ws?session_id=user123');

ws.onopen = function() {
    ws.send(JSON.stringify({
        message: "Merhaba!",
        session_id: "user123"
    }));
};

ws.onmessage = function(event) {
    const response = JSON.parse(event.data);
    console.log('AI Response:', response.response);
};
```

## 🛠️ Development

### Local Development

```bash
# Python virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux  
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Unit tests
pytest tests/unit/

# Integration tests  
pytest tests/integration/

# All tests with coverage
pytest --cov=backend --cov-report=html
```

### Building Custom Docker Image

```bash
# Build for current platform
docker build -t webchat-ai:latest .

# Build for multiple platforms
docker buildx build --platform linux/amd64,linux/arm64 -t webchat-ai:latest .
```

## 🐳 Docker Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f web

# Check status
docker-compose ps

# Stop services
docker-compose down

# Clean restart
docker-compose down -v
docker-compose up --build -d

# Access container
docker exec -it webchat-web bash
```

## 📊 Monitoring

### Health Checks

- **Application Health**: http://localhost:8000/api/health
- **Metrics**: http://localhost:8000/api/metrics  
- **API Docs**: http://localhost:8000/docs

### Log Files

```bash
# Application logs
docker-compose logs web

# Database logs
docker-compose logs postgres

# Real-time logs
docker-compose logs -f
```

## 🔧 Configuration

### Environment Variables

Önemli environment değişkenleri:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API anahtarı | Required |
| `DATABASE_URL` | PostgreSQL connection string | Auto-generated |
| `DEBUG` | Debug mode | `false` |
| `LOG_LEVEL` | Log level | `info` |
| `CORS_ORIGINS` | Allowed origins | `*` |

### Custom Configuration

`backend/config.py` dosyasını düzenleyerek özelleştirebilirsiniz.

## 🚀 Production Deployment

### Production Docker Compose

```bash
# Production profili ile çalıştır
docker-compose --profile production up -d
```

### SSL/TLS Konfigürasyonu

```bash
# SSL sertifikalarınızı nginx/ssl/ dizinine koyun
mkdir -p nginx/ssl
cp your-cert.pem nginx/ssl/
cp your-key.pem nginx/ssl/

# SSL'i aktif et
export ENABLE_SSL=true
docker-compose --profile production up -d
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'feat: add amazing feature'`
4. Push branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

MIT License ile dağıtılmaktadır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## 📞 Support

- **GitHub Issues**: [Report a Bug](https://github.com/mustafafozel/webchat-ai-assistant/issues)
- **Discussions**: [GitHub Discussions](https://github.com/mustafafozel/webchat-ai-assistant/discussions)
- **Email**: mustafafozel@example.com

## 🔗 Links

- **Documentation**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **Demo Scenarios**: [demo_scenarios.md](demo_scenarios.md)

---

**Made with ❤️ by [Mustafa Fözel](https://github.com/mustafafozel)**
