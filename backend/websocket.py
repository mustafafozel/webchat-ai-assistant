# WebSocket connection manager for real-time chat

from fastapi import WebSocket, WebSocketDisconnect
from backend.agent import run_agent
from backend.database import SessionLocal
from backend.models import Conversation, Message
from datetime import datetime

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_message(self, message: str, session_id: str):
        websocket = self.active_connections.get(session_id)
        if websocket:
            await websocket.send_text(message)

manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    db = SessionLocal()
    
    # Conversation oluştur veya bul
    conversation = db.query(Conversation).filter_by(session_id=session_id).first()
    if not conversation:
        conversation = Conversation(session_id=session_id)
        db.add(conversation)
        db.commit()
    
    try:
        while True:
            data = await websocket.receive_text()
            
            # Kullanıcı mesajını kaydet
            user_msg = Message(
                conversation_id=conversation.id,
                sender="user",
                content=data,
		message_metadata=None,
                created_at=datetime.utcnow()
            )
            db.add(user_msg)
            db.commit()
            
            # Agent'ten yanıt al
            response = run_agent(data, session_id)
            
            # Asistan mesajını kaydet
            assistant_msg = Message(
                conversation_id=conversation.id,
                sender="assistant",
		message_metadata=None,
		content=response,
                created_at=datetime.utcnow()
            )
            db.add(assistant_msg)
            db.commit()
            
            # Yanıtı gönder
            await manager.send_message(response, session_id)
            
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    finally:
        db.close()
