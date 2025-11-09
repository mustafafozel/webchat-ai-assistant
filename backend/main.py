import logging
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

