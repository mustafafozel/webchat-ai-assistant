import logging
<<<<<<< HEAD
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
from backend.database import init_db
from backend.config import settings
from groq import Groq

app = FastAPI(title="WebChat AI Assistant (LangGraph + WebSocket)")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend.main")

# GROQ istemcisi
groq_client = Groq(api_key=settings.GROQ_API_KEY)

# Uygulama başlatıldığında veritabanını hazırlıyoruz
@app.on_event("startup")
async def on_startup():
    logger.info("Uygulama başlıyor...")
    logger.info("Veritabanı tabloları kontrol ediliyor/oluşturuluyor...")
    await init_db()
    logger.info("✅ Veritabanı hazır.")
    logger.info("✅ Uygulama başarıyla başlatıldı.")

# Basit test endpointi
@app.get("/", response_class=HTMLResponse)
async def home():
    """Ana sayfa (chat widget HTML)"""
    index_path = Path(__file__).resolve().parent.parent / "frontend" / "index.html"
    return FileResponse(index_path)

# WebSocket bağlantısı
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = websocket.query_params.get("session_id")
    logger.info(f"WebSocket bağlandı: {session_id}")

    try:
        while True:
            msg = await websocket.receive_text()
            logger.info(f"WebSocket Mesaj alındı: {session_id} -> {msg}")

            try:
                response = await process_message(msg)
                await websocket.send_text(response)
            except Exception as e:
                logger.error(f"WebSocket Hatası ({session_id}): {e}")
                await websocket.send_text(f"Hata oluştu: {e}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket bağlantısı kesildi: {session_id}")
    finally:
        await websocket.close()

# Asenkron Groq yanıtı oluşturucu
async def process_message(message: str) -> str:
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": message}],
            temperature=0.7,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Hata oluştu: {str(e)}"

=======
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from pydantic import BaseModel

from backend.database import init_db
from backend.config import settings
from backend.graph import run_agent

app = FastAPI(title="WebChat AI Assistant")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Startup ===
@app.on_event("startup")
async def on_startup():
    logger.info("🚀 Uygulama başlatılıyor...")
    await init_db()
    logger.info("✅ Veritabanı hazır")

# === Routes ===
@app.get("/", response_class=HTMLResponse)
async def home():
    """Ana sayfa"""
    index_path = Path(__file__).resolve().parent.parent / "frontend" / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="index.html bulunamadı")
    return FileResponse(index_path)

@app.get("/api/health")
async def health_check():
    """Sağlık kontrolü"""
    return {"status": "healthy", "service": "WebChat AI"}

# === WebSocket ===
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = websocket.query_params.get("session_id", "unknown")
    logger.info(f"🔌 WebSocket bağlandı: {session_id}")
    
    try:
        while True:
            message = await websocket.receive_text()
            logger.info(f"📨 Mesaj alındı ({session_id}): {message}")
            
            try:
                # LangGraph agent'ı çalıştır
                response = run_agent(session_id=session_id, user_input=message)
                await websocket.send_json({
                    "type": "response",
                    "response": response,
                    "session_id": session_id
                })
            except Exception as e:
                logger.error(f"❌ Agent hatası: {e}")
                await websocket.send_json({
                    "type": "error",
                    "error": str(e),
                    "session_id": session_id
                })
    
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket kesildi: {session_id}")

# === HTTP Chat API (Fallback) ===
class ChatRequest(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    response: str
    session_id: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    HTTP fallback endpoint
    """
    try:
        response_text = run_agent(
            session_id=request.session_id,
            user_input=request.message
        )
        
        return ChatResponse(
            response=response_text,
            session_id=request.session_id
        )
    
    except Exception as e:
        logger.error(f"❌ /api/chat hatası: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"AI asistan hatası: {str(e)}"
        )

>>>>>>> 65eb5aa (feat: major update - LangGraph ReAct agent implementation)
