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

## 🚀 Hızlı Başlangıç

### Sistem Gereksinimleri

| Platform | Minimum Gereksinimler |
|----------|---------------------|
| **Windows** | Windows 10/11, Docker Desktop |
| **macOS** | macOS 10.15+, Docker Desktop |
| **Linux** | Ubuntu 20.04+, Docker Engine |

### 1️⃣ Projeyi İndirin

```bash
git clone https://github.com/mustafafozel/webchat-ai-assistant.git
cd webchat-ai-assistant
```

### 2️⃣ Environment Ayarları

```bash
# .env dosyasını oluşturun
cp .env.example .env

# OpenAI API key'inizi ekleyin
nano .env  # veya code .env
```

`.env` dosyasında şunu güncelleyin:
```env
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
```

### 3️⃣ Docker ile Başlatın

#### Windows (PowerShell/CMD)
```cmd
docker-compose up -d
```

#### macOS/Linux (Terminal)
```bash
docker-compose up -d
```

### 4️⃣ Test Edin

Tarayıcıda açın: **http://localhost:8000**

API durumu: **http://localhost:8000/api/health**

```bash
# Terminal'den test
curl http://localhost:8000/api/health
```

**Başarılı response:**
```json
{"status": "healthy", "service": "webchat-ai"}
```

## 📋 Platform-Specific Kurulum

### Windows Kurulumu

1. **Docker Desktop** kurun: https://www.docker.com/products/docker-desktop/
2. **Git for Windows** kurun: https://git-scm.com/download/win
3. PowerShell'i **Administrator** olarak açın:

```powershell
# Projeyi klonlayın
git clone https://github.com/mustafafozel/webchat-ai-assistant.git
cd webchat-ai-assistant

# Environment dosyası
copy .env.example .env
notepad .env  # API key'i güncelleyin

# Docker ile başlatın
docker-compose up -d

# Test edin
Invoke-WebRequest -Uri http://localhost:8000/api/health
```

### macOS Kurulumu

1. **Docker Desktop** kurun: https://www.docker.com/products/docker-desktop/
2. **Homebrew** ile git kurun (opsiyonel):

```bash
# Homebrew kurulumu (eğer yoksa)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Git kurulumu
brew install git

# Projeyi klonlayın
git clone https://github.com/mustafafozel/webchat-ai-assistant.git
cd webchat-ai-assistant

# Environment ayarları
cp .env.example .env
open -a TextEdit .env  # API key'i güncelleyin

# Docker ile başlatın
docker-compose up -d

# Test edin
curl http://localhost:8000/api/health
```

### Linux (Ubuntu/Debian) Kurulumu

```bash
# Docker kurulumu
sudo apt update
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Docker Compose kurulumu
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Kullanıcıyı docker grubuna ekleyin
sudo usermod -aG docker $USER
newgrp docker

# Projeyi klonlayın
git clone https://github.com/mustafafozel/webchat-ai-assistant.git
cd webchat-ai-assistant

# Environment ayarları
cp .env.example .env
nano .env  # API key'i güncelleyin

# Docker ile başlatın
docker-compose up -d

# Test edin
curl http://localhost:8000/api/health
```

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