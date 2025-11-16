<<<<<<< ours
# 📐 WebChat AI Assistant - Technical Architecture

## System Overview

WebChat AI Assistant, müşteri web sitelerine entegre edilebilen AI destekli chat sistemidir. LangGraph tabanlı agent akışı, RAG (Retrieval-Augmented Generation), Tool Calling ve WebSocket desteği ile gerçek zamanlı müşteri hizmetleri sunar.

## 🏗️ High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (JS Widget)   │◄──►│   (FastAPI)     │◄──►│  (PostgreSQL)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         └──────────────┤   AI Services   │──────────────┘
                        │ (LangGraph+RAG) │
                        └─────────────────┘
```

### Core Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend Widget** | Vanilla JavaScript | Embeddable chat interface |
| **API Gateway** | FastAPI + Uvicorn | HTTP/WebSocket endpoints |
| **AI Agent** | LangGraph + LangChain | Conversation orchestration |
| **Knowledge Base** | FAISS + Embeddings | RAG implementation |
| **Database** | PostgreSQL | Session & conversation storage |
| **Cache Layer** | Redis | Performance optimization |
| **Container** | Docker + Docker Compose | Cross-platform deployment |

## 🎯 Layered Architecture

### 1. Presentation Layer

**Location**: `frontend/`
**Technologies**: HTML5, CSS3, Vanilla JavaScript, WebSocket API

```javascript
// Widget initialization
window.WebChatAI.init({
    apiUrl: 'http://localhost:8000',
    sessionId: generateSessionId(),
    theme: 'light',
    position: 'bottom-right'
});
```

**Responsibilities**:
- Chat interface rendering
- WebSocket connection management  
- User interaction handling
- Real-time message display
- Error state management

### 2. API Gateway Layer

**Location**: `backend/main.py`
**Technologies**: FastAPI, Uvicorn, WebSockets

**Endpoints**:
```python
# HTTP Endpoints
POST /api/chat          # Fallback chat endpoint
GET  /api/health        # Health check
GET  /api/metrics       # System metrics

# WebSocket Endpoint  
WS   /ws?session_id=    # Real-time chat
```

**Responsibilities**:
- Request routing and validation
- WebSocket connection management
- CORS policy enforcement
- Authentication/authorization
- Rate limiting and throttling

### 3. Business Logic Layer

#### 3.1 LangGraph Agent Flow

**Location**: `backend/agent.py`
**Technologies**: LangGraph, LangChain

```python
from langgraph import StateGraph, END

def create_agent_graph():
    workflow = StateGraph(AgentState)
    
    # Define nodes
    workflow.add_node("intent_router", intent_router_node)
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("tool_caller", tool_caller_node)
    workflow.add_node("response_builder", response_builder_node)
    workflow.add_node("memory_manager", memory_manager_node)
    
    # Define edges
    workflow.set_entry_point("intent_router")
    
    workflow.add_conditional_edges(
        "intent_router",
        route_decision,
        {
            "faq": "retriever",
            "tool": "tool_caller",
            "general": "response_builder"
        }
    )
    
    workflow.add_edge("retriever", "response_builder")
    workflow.add_edge("tool_caller", "response_builder")
    workflow.add_edge("response_builder", "memory_manager")
    workflow.add_edge("memory_manager", END)
    
    return workflow.compile()
```

#### 3.2 Tool Calling System

**Location**: `backend/tools.py`

```python
from langchain.tools import tool
from typing import Dict, Any

@tool
def check_order_status(order_id: str) -> str:
    """Sipariş durumunu kontrol eder"""
    # Mock implementation
    statuses = ["Hazırlanıyor", "Kargoya verildi", "Teslim edildi"]
    return f"Sipariş {order_id} durumu: {random.choice(statuses)}"

@tool  
def calculate_shipping(city: str) -> str:
    """Kargo ücretini hesaplar"""
    # Mock implementation
    prices = {"İstanbul": 15, "Ankara": 18, "İzmir": 20}
    price = prices.get(city, 25)
    return f"{city} için kargo ücreti: {price} TL"

@tool
def policy_lookup(topic: str) -> str:
    """Politika bilgisi arar"""
    policies = {
        "iade": "14 gün içinde iade hakkınız bulunmaktadır.",
        "kargo": "Ortalama teslimat süresi 2-4 iş günüdür.",
        "ödeme": "Kredi kartı ve kapıda ödeme kabul edilir."
    }
    return policies.get(topic.lower(), "Bu konu hakkında bilgi bulunamadı.")
```

### 4. Data Access Layer

#### 4.1 Database Schema

**Location**: `backend/models.py`

```python
from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"))
    sender = Column(String(50), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, server_default=func.now())
```

#### 4.2 RAG Knowledge Base

**Location**: `backend/rag.py`
**Technologies**: FAISS, Sentence Transformers, OpenAI Embeddings

```python
import faiss
from sentence_transformers import SentenceTransformer
from langchain.embeddings import OpenAIEmbeddings

class RAGKnowledgeBase:
    def __init__(self, embedding_model="text-embedding-ada-002"):
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self.index = None
        self.documents = []
        
    def build_index(self, documents: list):
        """FAISS index oluşturur"""
        embeddings = self.embeddings.embed_documents(documents)
        
        dimension = len(embeddings[0])
        self.index = faiss.IndexFlatL2(dimension)
        
        import numpy as np
        embeddings_array = np.array(embeddings).astype('float32')
        self.index.add(embeddings_array)
        
        self.documents = documents
        
    def search(self, query: str, k: int = 3):
        """Benzer dokümanları arar"""
        query_embedding = self.embeddings.embed_query(query)
        
        import numpy as np
        query_array = np.array([query_embedding]).astype('float32')
        
        scores, indices = self.index.search(query_array, k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.documents):
                results.append({
                    'content': self.documents[idx],
                    'score': float(score),
                    'index': int(idx)
                })
        
        return results
```

## 🔄 Data Flow & Message Processing

### Complete Message Lifecycle

```
1. User Input (Frontend)
   │ JavaScript widget captures message
   │ Validates input and session
   │
   ▼
2. WebSocket/HTTP Transmission
   │ Real-time: WebSocket connection
   │ Fallback: HTTP POST request
   │
   ▼
3. API Gateway Processing
   │ Route to appropriate handler
   │ Session validation
   │ Rate limiting check
   │
   ▼
4. LangGraph Agent Orchestration
   │
   ├─► Intent Router Node
   │   │ Analyzes user intent
   │   │ Routes to appropriate flow
   │   │
   │   ├─► FAQ Flow
   │   │   └─► Retriever Node (RAG)
   │   │
   │   ├─► Tool Flow  
   │   │   └─► Tool Caller Node
   │   │
   │   └─► General Flow
   │       └─► Direct to Response Builder
   │
   ▼
5. Response Builder Node
   │ Aggregates context from previous nodes
   │ Formats final response
   │ Applies conversation tone
   │
   ▼
6. Memory Manager Node
   │ Saves user message to PostgreSQL
   │ Saves assistant response
   │ Updates conversation metadata
   │
   ▼
7. Response Transmission
   │ Send via WebSocket (real-time)
   │ Or HTTP response (fallback)
   │
   ▼
8. Frontend Update
   │ Display response in chat
   │ Update UI state
   │ Handle typing indicators
```

## 🌐 WebSocket Architecture

### Connection Management

**Location**: `backend/websocket.py`

```python
from fastapi import WebSocket
from typing import Dict, Set
import json
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_metadata: Dict[str, Dict] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.session_metadata[session_id] = {
            'connected_at': time.time(),
            'message_count': 0
        }
        
        await self.send_personal_message(session_id, {
            'type': 'connection',
            'status': 'connected',
            'message': 'WebChat AI'ya hoş geldiniz!'
        })
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.session_metadata:
            del self.session_metadata[session_id]
    
    async def send_personal_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                await websocket.send_text(json.dumps(message))
            except:
                self.disconnect(session_id)
    
    async def broadcast(self, message: dict):
        disconnected = []
        for session_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except:
                disconnected.append(session_id)
        
        for session_id in disconnected:
            self.disconnect(session_id)

manager = ConnectionManager()
```

### Message Protocol

```javascript
// Client -> Server
{
    "type": "message",
    "message": "Siparişimi takip etmek istiyorum",
    "session_id": "user-abc123",
    "metadata": {
        "timestamp": "2025-10-31T21:00:00Z",
        "client_info": {
            "browser": "Chrome",
            "os": "Windows"
        }
    }
}

// Server -> Client  
{
    "type": "response",
    "response": "Tabii ki! Sipariş numaranızı paylaşır mısınız?",
    "session_id": "user-abc123",
    "metadata": {
        "timestamp": "2025-10-31T21:00:01Z",
        "processing_time": 0.85,
        "tokens_used": 12,
        "intent": "order_tracking",
        "tools_used": []
    }
}

// System Messages
{
    "type": "system",
    "event": "typing_start|typing_stop|connection_lost|reconnected",
    "session_id": "user-abc123"
}
```

## 🔧 Configuration Management

### Environment-Based Settings

**Location**: `backend/config.py`

```python
from pydantic import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    # Application
    DEBUG: bool = False
    SECRET_KEY: str
    LOG_LEVEL: str = "info"
    
    # Database
    DATABASE_URL: str
    REDIS_URL: Optional[str] = None
    
    # AI Configuration
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_TOKENS: int = 150
    
    # Embeddings
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    
    # WebSocket
    WEBSOCKET_MAX_CONNECTIONS: int = 100
    WEBSOCKET_HEARTBEAT_INTERVAL: int = 30
    
    # Security
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    RATE_LIMIT_PER_MINUTE: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

## 🔒 Security Architecture

### Authentication & Session Management

```python
from fastapi import HTTPException, Depends
import jwt
from datetime import datetime, timedelta

class SecurityManager:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.algorithm = "HS256"
    
    def create_session_token(self, session_id: str) -> str:
        payload = {
            "session_id": session_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def validate_session(self, token: str) -> str:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload["session_id"]
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Session expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid session")
```

### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/chat")
@limiter.limit("60/minute")
async def chat_endpoint(request: Request, ...):
    # Implementation
    pass
```

## 📊 Monitoring & Observability

### Metrics Collection

```python
from prometheus_client import Counter, Histogram, Gauge

# Metrics definitions
REQUEST_COUNT = Counter('webchat_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('webchat_request_duration_seconds', 'Request duration')
ACTIVE_CONNECTIONS = Gauge('webchat_active_websocket_connections', 'Active WebSocket connections')
AI_PROCESSING_TIME = Histogram('webchat_ai_processing_seconds', 'AI processing time')
TOOL_CALLS = Counter('webchat_tool_calls_total', 'Tool calls', ['tool_name', 'status'])

class MetricsCollector:
    @staticmethod
    def record_request(method: str, endpoint: str, duration: float):
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_DURATION.observe(duration)
    
    @staticmethod
    def record_websocket_connection(delta: int):
        ACTIVE_CONNECTIONS.inc(delta)
    
    @staticmethod
    def record_ai_processing(duration: float):
        AI_PROCESSING_TIME.observe(duration)
```

### Structured Logging

```python
import structlog
from datetime import datetime

logger = structlog.get_logger()

def log_chat_interaction(session_id: str, message: str, response: str, 
                        processing_time: float, intent: str, tools_used: list):
    logger.info(
        "chat_interaction",
        session_id=session_id,
        message_length=len(message),
        response_length=len(response),
        processing_time=processing_time,
        intent=intent,
        tools_used=tools_used,
        timestamp=datetime.utcnow().isoformat()
    )
```

## 🚀 Deployment Architecture

### Docker Multi-Stage Build

```dockerfile
# Production-ready multi-stage Dockerfile
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim as runtime

RUN groupadd --gid 1000 webchat && \
    useradd --uid 1000 --gid webchat --create-home webchat

WORKDIR /app
COPY --from=builder /root/.local /home/webchat/.local
COPY --chown=webchat:webchat . .

USER webchat
ENV PATH=/home/webchat/.local/bin:$PATH

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Docker Compose

```yaml
# Production configuration
version: '3.8'

services:
  web:
    build: .
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 📈 Performance Optimization

### Database Optimization

```sql
-- Performance indexes
CREATE INDEX CONCURRENTLY idx_messages_conversation_created 
ON messages(conversation_id, created_at DESC);

CREATE INDEX CONCURRENTLY idx_conversations_session_updated 
ON conversations(session_id, updated_at DESC);

-- Query optimization for conversation history
EXPLAIN ANALYZE 
SELECT m.sender, m.content, m.created_at
FROM messages m
JOIN conversations c ON m.conversation_id = c.id  
WHERE c.session_id = $1
ORDER BY m.created_at DESC
LIMIT 20;
```

### Caching Strategy

```python
import redis
from functools import wraps

redis_client = redis.Redis.from_url(settings.REDIS_URL)

def cache_result(ttl: int = 3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator

@cache_result(ttl=1800)  # 30 minutes
async def get_knowledge_base_results(query: str):
    # RAG search implementation
    pass
```

## 🧪 Testing Architecture

### Test Structure

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_openai():
    with patch('backend.agent.OpenAI') as mock:
        mock.return_value.chat.completions.create.return_value.choices[0].message.content = "Test response"
        yield mock

# tests/test_agent.py
@pytest.mark.asyncio
async def test_agent_intent_routing():
    agent = ChatAgent()
    
    # Test FAQ intent
    result = await agent.process_message("iade politikası nedir?", "test_session")
    assert "intent" in result.metadata
    assert result.metadata["intent"] == "faq"
    
    # Test tool intent
    result = await agent.process_message("123456 numaralı siparişimi takip et", "test_session")  
    assert result.metadata["intent"] == "tool"
    assert "check_order_status" in result.metadata["tools_used"]

# tests/test_websocket.py
def test_websocket_connection(client):
    with client.websocket_connect("/ws?session_id=test123") as websocket:
        # Test connection
        data = websocket.receive_json()
        assert data["type"] == "connection"
        
        # Test message
        websocket.send_json({
            "message": "Hello",
            "session_id": "test123"
        })
        
        response = websocket.receive_json()
        assert "response" in response
```

## 🔮 Future Enhancements

### Microservices Evolution

```yaml
# Future microservices architecture
services:
  api-gateway:
    image: nginx:alpine
    ports: ["80:80"]
    
  chat-service:
    build: ./services/chat
    environment:
      - DATABASE_URL=${CHAT_DB_URL}
      
  ai-service:  
    build: ./services/ai
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      
  knowledge-service:
    build: ./services/knowledge
    environment:
      - FAISS_INDEX_PATH=${FAISS_PATH}
```

### Advanced Features

- **Multi-tenant support**: Her müşteri için ayrı knowledge base
- **A/B testing**: Farklı AI model karşılaştırması  
- **Analytics dashboard**: Gerçek zamanlı chat metrikleri
- **Voice integration**: Ses tabanlı chat desteği
- **Mobile SDK**: Native mobile uygulamalar için SDK

---

**Architecture Version**: 1.0.0  
**Last Updated**: October 31, 2025  
**Status**: ✅ Production Ready
=======
# WebChat AI Assistant – Architecture

Bu doküman Etkin.ai teknik isterlerine göre hazırlanmış WebChat AI Assistant projesinin bileşenlerini özetler.

## 1. Genel Bakış

Sistem iki ana parçadan oluşur:

1. **Frontend widget** (`frontend/widget.js`, `frontend/widget.css`, `frontend/index.html`)
   - Herhangi bir web sitesine `<script>` ile eklenebilir yüzen panel.
   - WebSocket üzerinden gerçek zamanlı sohbet eder, gerektiğinde HTTP `POST /api/chat` fallback'i kullanır.
   - Oturum kimliği `localStorage`'da tutulur ve otomatik yeniden bağlanma yapılır.
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
2. **Retriever** – `knowledge/kb.json` içeriğini `mini_rag_search()` ile tarar.
3. **Tool Caller** – `check_order_status`, `calculate_shipping`, `policy_lookup` fonksiyonlarını çağırır.
4. **Response Builder** – Groq LLM mevcutsa araçları bağlayarak yanıt üretir, aksi halde kural tabanlı yanıt döner.

Her döngü sonunda `_persist_messages()` fonksiyonu aracılığıyla kullanıcı ve asistan mesajları veritabanına yazılır.

## 4. Veri Katmanı

- **Modeller**: `backend/models.py` içinde `Conversation` ve `Message` sınıfları vardır.
- **Depolama**: Varsayılan olarak SQLite (`webchat_ai.db`) kullanılır, `.env` üzerinden `DATABASE_URL` ayarlanarak PostgreSQL'e geçilebilir.
- **Oturumlar**: LangGraph çalışması sırasında `SessionLocal` kullanılarak senkron oturum açılır, FastAPI bağımlılığı için `AsyncSessionLocal` sağlanır.

## 5. Knowledge Base ve Tool'lar

- `knowledge/kb.json` mini SSS içeriğini tutar.
- `backend/rag_setup.py` dosyası JSON'u yükler ve basit bir tf-idf benzeri skorlayıcıyla (kelime kesişimi) ilk `k` sonucu döner.
- `backend/tools.py` içindeki fonksiyonlar Etkin.ai isterlerinde belirtilen sahte servisleri bire bir uygular ve LangChain `StructuredTool` registry'sine eklenir.

## 6. Gözlemlenebilirlik

- `MetricsState` sınıfı (`backend/main.py`) her mesajı sayar, aktif oturumları ve tool kullanımlarını `/api/metrics` üzerinden raporlar.
- Docker imajı `HEALTHCHECK` komutuyla `/api/health` endpoint'ini periyodik kontrol eder.

## 7. Test Stratejisi

- **Unit testleri**: `tests/unit/` klasörü LangGraph ajanını ve tool fonksiyonlarını doğrular.
- **Integration testleri**: `tests/integration/test_api.py` HTTP/WebSocket yüzeyini `fastapi.testclient` ile çalıştırır.
- `pytest` çalıştırmak için `make test` veya `pytest` komutları kullanılabilir.

Bu mimari, Etkin.ai gereksinim setindeki WebSocket widget, LangGraph ajan akışı, PostgreSQL kalıcılığı ve gözlemlenebilirlik maddelerini doğrudan adresler.
>>>>>>> theirs
