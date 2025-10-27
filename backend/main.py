from fastapi import FastAPI, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from backend.database import engine, get_db, Base
from backend.models import Message, Conversation
from backend.websocket import websocket_endpoint
from backend.agent import run_agent
from backend.config import settings

# Tabloları oluştur
Base.metadata.create_all(bind=engine)

app = FastAPI(title="WebChat AI Assistant")

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static dosyalar
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def read_root():
    return {"message": "WebChat AI Assistant API"}

@app.post("/api/chat")
async def chat_endpoint(request: dict, db: Session = Depends(get_db)):
    """HTTP fallback chat endpoint."""
    user_input = request.get("message", "")
    session_id = request.get("session_id", "default")
    
    response = run_agent(user_input, session_id)
    
    return JSONResponse(content={"response": response})

@app.websocket("/ws")
async def websocket_route(websocket: WebSocket, session_id: str = "default"):
    """WebSocket endpoint."""
    await websocket_endpoint(websocket, session_id)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "webchat-ai"}

@app.get("/api/metrics")
def metrics(db: Session = Depends(get_db)):
    total_messages = db.query(Message).count()
    total_conversations = db.query(Conversation).count()
    return {
        "total_messages": total_messages,
        "total_conversations": total_conversations
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
