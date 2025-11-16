# WebChat AI Assistant – Architecture

Bu doküman Etkin.ai teknik isterlerine göre hazırlanmış WebChat AI Assistant projesinin bileşenlerini ve veri akışını özetler.

## 1. Genel Bakış

Sistem iki ana parçadan oluşur:

1. **Frontend widget** (`frontend/widget.js`, `frontend/widget.css`, `frontend/index.html`)
   - Herhangi bir web sitesine `<script>` ile eklenebilen yüzen panel.
   - WebSocket üzerinden gerçek zamanlı sohbet eder, gerektiğinde HTTP `POST /api/chat` fallback'ini kullanır.
   - Oturum kimliği `localStorage`/konfig üzerinden korunur ve otomatik yeniden bağlanma yapılır.
2. **Backend API** (`backend/main.py`)
   - FastAPI uygulaması; HTTP + WebSocket endpoint'lerini, sağlık ve metrik servislerini barındırır.
   - LangGraph tabanlı ajan akışı `backend/graph.py` içerisinde tanımlıdır.
   - SQLAlchemy üzerinden PostgreSQL/SQLite kalıcılığı (`backend/database.py`, `backend/models.py`).

Aşağıdaki diyagram yüksek seviyede veri akışını gösterir:

```
Kullanıcı Tarayıcısı (widget.js)
        │
        │  WebSocket / HTTP
        ▼
FastAPI (backend/main.py) ──▶ LangGraph Agent (backend/graph.py)
        │                             │
        │                             ├─▶ Mini RAG (backend/rag_setup.py + knowledge/kb.json)
        │                             └─▶ Mock Tools (backend/tools.py)
        ▼
SQLAlchemy ORM (backend/models.py)  ──▶ PostgreSQL / SQLite
```

## 2. API Katmanı

| Endpoint | Açıklama | Dosya |
|----------|----------|-------|
| `GET /api/health` | Servis sağlığı | `backend/main.py` |
| `GET /api/metrics` | Oturum, mesaj ve tool kullanımı istatistikleri | `backend/main.py` |
| `POST /api/chat` | WebSocket fallback HTTP endpoint'i | `backend/main.py` |
| `WS /ws?session_id=` | Gerçek zamanlı sohbet | `backend/main.py` |
| `GET /` ve `/static/*` | Demo sayfası + widget statikleri | `backend/main.py` + `frontend/` |

FastAPI başlangıcında `backend.database.init_db()` çağrılır, böylece `conversations` ve `messages` tabloları otomatik oluşturulur.

## 3. LangGraph Ajan Akışı

`backend/graph.py` dosyasında `StateGraph` kullanılarak aşağıdaki düğümler tanımlanır:

1. **Intent Router** – Mesajı `faq`, `tool` veya `general` olarak sınıflandırır.
2. **Retriever** – `knowledge/kb.json` içeriğini `mini_rag_search()` ile tarar ve en fazla iki sonuç döndürür.
3. **Tool Caller** – `check_order_status`, `calculate_shipping`, `policy_lookup` fonksiyonlarını çağırır.
4. **Response Builder** – Groq LLM mevcutsa araçları bağlayarak yanıt üretir, aksi halde kural tabanlı yanıt döner.

Her döngü sonunda `_persist_messages()` fonksiyonu aracılığıyla kullanıcı ve asistan mesajları veritabanına yazılır.

### Çalışma Zamanı Durumu

- **State nesnesi**: `AgentState` `messages`, `intent`, `context` ve `next` alanlarını içerir.
- **LLM entegrasyonu**: `.env` üzerinden Groq anahtarı sağlanırsa `ChatGroq` modeli tool çağrıları ile çalışır.
- **Mini RAG**: JSON tabanlı KB satırları `backend/rag_setup.py` içindeki normalize edilmiş eşleşme skoru ile aranır.

## 4. Veri Katmanı

- **Modeller**: `backend/models.py` içinde `Conversation` ve `Message` sınıfları vardır. `metadata_json` alanı intent/tool gibi bilgileri saklar.
- **Depolama**: Varsayılan olarak SQLite (`webchat_ai.db`) kullanılır, `.env` üzerinden `DATABASE_URL` ayarlanarak PostgreSQL'e geçilebilir.
- **Oturumlar**: FastAPI bağımlılıkları için asenkron `AsyncSessionLocal`, LangGraph çalışması sırasında senkron `SessionLocal` kullanılır.

### Veritabanı Şeması

| Tablo | Alanlar |
|-------|---------|
| `conversations` | `id (UUID)`, `session_id (unique)`, `created_at` |
| `messages` | `id (UUID)`, `conversation_id (FK)`, `sender`, `content`, `metadata`, `created_at` |

## 5. Knowledge Base ve Tool'lar

- `knowledge/kb.json` mini SSS içeriğini tutar.
- `backend/rag_setup.py` dosyası JSON'u yükler ve kelime kesişimi skoruyla ilk `k` sonucu döner.
- `backend/tools.py` içindeki fonksiyonlar Etkin.ai isterlerinde belirtilen sahte servisleri bire bir uygular ve LangChain `StructuredTool` registry'sine eklenir.

## 6. Gözlemlenebilirlik

- `MetricsState` sınıfı (`backend/main.py`) her mesajı sayar, aktif oturumları ve tool kullanımlarını `/api/metrics` üzerinden raporlar.
- Docker imajı `HEALTHCHECK` komutuyla `/api/health` endpoint'ini periyodik kontrol eder.
- Testler `pytest` altında unit ve integration olarak ayrılmıştır (`tests/unit`, `tests/integration`).

## 7. Dağıtım ve Operasyon

- **Docker Compose**: `docker-compose.yml` FastAPI uygulaması ve PostgreSQL servisini ayağa kaldırır.
- **Production Override**: `docker-compose.prod.yml` minimal prod yapılandırması sağlar.
- **Ortam değişkenleri**: `backend/config.py` Pydantic tabanlı `Settings` sınıfı ile yönetilir.

Bu mimari, Etkin.ai gereksinim setindeki WebSocket widget, LangGraph ajan akışı, PostgreSQL kalıcılığı ve gözlemlenebilirlik maddelerini doğrudan adresler.
