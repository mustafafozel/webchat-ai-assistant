import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
from backend.database import init_db, get_db
from backend.graph import run_agent # YENİ LANGGRAPH AGENT'İ
from sqlalchemy.orm import Session
from backend.models import Conversation, Message # DB Modelleri

# Loglama ayarı
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Uygulama Ömrü (Lifecycle) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Uygulama başlarken
    logger.info("Uygulama başlıyor...")
    logger.info("Veritabanı tabloları kontrol ediliyor/oluşturuluyor...")
    # Veritabanı tablolarını oluştur (models.py'e göre)
    init_db()
    logger.info("✅ Veritabanı hazır.")
    logger.info("✅ Uygulama başarıyla başlatıldı.")
    yield
    # Uygulama kapanırken
    logger.info("Uygulama kapanıyor...")

app = FastAPI(
    title="WebChat AI Assistant (LangGraph + WebSocket)",
    description="İş dökümanı isterlerine göre güncellenmiş mimari.",
    lifespan=lifespan
)

# --- CORS Ayarları (Frontend'in erişebilmesi için) ---
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Veya frontend adresiniz
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Modeller ---
class ChatMessage(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    response: str
    session_id: str
    
class Metrics(BaseModel):
    total_conversations: int
    total_messages: int

# --- WebSocket Bağlantı Yöneticisi ---
# (backend/websocket.py yerine direkt main.py içinde yönetelim)
class ConnectionManager:
    def __init__(self):
        # Aktif bağlantıları session_id ile sakla
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket bağlandı: {session_id}")

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket bağlantısı kesildi: {session_id}")

    async def send_message(self, message: str, session_id: str):
        websocket = self.active_connections.get(session_id)
        if websocket:
            await websocket.send_text(message)

manager = ConnectionManager()

# --- API ENDPOINTS (İş Dökümanı İsterleri) ---

@app.get("/api/health")
def health_check():
    """İş Dökümanı İsteri: GET /api/health - Sağlık kontrolü"""
    return {"status": "healthy", "architecture": "LangGraph_WebSocket_PostgreSQL"}

@app.get("/api/metrics", response_model=Metrics)
def get_metrics(db: Session = Depends(get_db)):
    """İş Dökümanı İsteri: GET /api/metrics - Basit metrikler"""
    try:
        total_conv = db.query(Conversation).count()
        total_msg = db.query(Message).count()
        return {"total_conversations": total_conv, "total_messages": total_msg}
    except Exception as e:
        logger.error(f"Metrik alınırken hata: {e}")
        return {"total_conversations": -1, "total_messages": -1}

@app.post("/api/chat", response_model=ChatResponse)
async def chat_http_fallback(chat_message: ChatMessage):
    """
    İş Dökümanı İsteri: POST /api/chat
    WebSocket çalışmazsa diye HTTP fallback endpoint'i.
    """
    logger.info(f"HTTP Chat (Fallback) alındı: {chat_message.session_id}")
    
    # Agent'i çalıştır (LangGraph + DB Memory)
    response_text = run_agent(chat_message.session_id, chat_message.message)
    
    return ChatResponse(response=response_text, session_id=chat_message.session_id)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    İş Dökümanı İsteri: GET /ws?session_id=
    Gerçek zamanlı mesajlaşma için WebSocket endpoint'i.
    """
    await manager.connect(websocket, session_id)
    try:
        while True:
            # Kullanıcıdan mesaj bekle
            data = await websocket.receive_text()
            
            logger.info(f"WebSocket Mesaj alındı: {session_id} -> {data}")
            
            # "yazıyor..." göstergesi için ara mesaj
            await manager.send_message("Asistan yazıyor...", session_id)
            
            # Agent'i çalıştır (LangGraph + DB Memory)
            response_text = run_agent(session_id, data)
            
            # AI yanıtını kullanıcıya gönder
            await manager.send_message(response_text, session_id)
            
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket Hatası ({session_id}): {e}")
        await manager.send_message(f"Hata oluştu: {e}", session_id)
        manager.disconnect(session_id)

# --- Demo Arayüz (Test için) ---
@app.get("/", response_class=HTMLResponse)
def get_demo_page(request: Request):
    """
    Localhost'ta test etmek için basit demo sayfası.
    Bu, frontend/index.html'e benzer ama WebSocket'i test eder.
    """
    # frontend/index.html dosyasını okuyup döndür
    try:
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Demo dosyası (frontend/index.html) bulunamadı.</h1>")
