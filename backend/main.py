"""FastAPI application exposing the WebChat AI Assistant endpoints."""

from __future__ import annotations

import json
import logging
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.config import settings
from backend.database import init_db
from backend.graph import run_agent

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title=settings.APP_NAME)

frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MetricsState:
    def __init__(self) -> None:
        self.started_at = datetime.utcnow()
        self.total_messages = 0
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.tool_usage: Counter[str] = Counter()

    def register_session(self, session_id: str) -> None:
        self.sessions.setdefault(session_id, {"message_count": 0, "last_message_at": None})

    def record_message(self, session_id: str, metadata: Dict[str, Any]) -> None:
        self.register_session(session_id)
        session = self.sessions[session_id]
        session["message_count"] += 1
        session["last_message_at"] = datetime.utcnow().isoformat()
        self.total_messages += 1

        tool_name = metadata.get("tool")
        if tool_name:
            self.tool_usage[tool_name] += 1

    def close_session(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)

    def snapshot(self) -> Dict[str, Any]:
        uptime = (datetime.utcnow() - self.started_at).total_seconds()
        return {
            "uptime_seconds": uptime,
            "total_messages": self.total_messages,
            "active_sessions": len(self.sessions),
            "tool_usage": dict(self.tool_usage),
            "sessions": [
                {"session_id": sid, **info}
                for sid, info in sorted(self.sessions.items())
            ],
        }


metrics_state = MetricsState()


class ChatRequest(BaseModel):
    message: str
    session_id: str


class ChatResponse(BaseModel):
    response: str
    session_id: str
    metadata: Dict[str, Any] | None = None


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("🚀 Uygulama başlatılıyor...")
    await init_db()
    logger.info("✅ Veritabanı hazır")


@app.get("/", response_class=HTMLResponse)
async def home() -> HTMLResponse:
    index_path = frontend_dir / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="index.html bulunamadı")
    return FileResponse(index_path)


@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    return {"status": "healthy", "service": settings.APP_NAME}


@app.get("/api/metrics")
async def metrics() -> Dict[str, Any]:
    return metrics_state.snapshot()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    session_id = websocket.query_params.get("session_id") or f"session-{uuid4().hex}"
    await websocket.accept()
    metrics_state.register_session(session_id)
    logger.info("🔌 WebSocket bağlandı: %s", session_id)

    try:
        while True:
            raw_message = await websocket.receive_text()
            payload_session_id = None
            message_text = raw_message

            try:
                parsed = json.loads(raw_message)
            except json.JSONDecodeError:
                parsed = None

            if isinstance(parsed, dict):
                message_text = str(parsed.get("message", "")).strip()
                payload_session_id = parsed.get("session_id")
            else:
                message_text = str(raw_message).strip()

            if payload_session_id:
                session_id = str(payload_session_id)
                metrics_state.register_session(session_id)

            if not message_text:
                await websocket.send_json(
                    {
                        "type": "error",
                        "error": "Mesaj alanı boş olamaz",
                        "session_id": session_id,
                    }
                )
                continue

            logger.info("📨 Mesaj alındı (%s): %s", session_id, message_text)

            result = run_agent(session_id=session_id, user_input=message_text)
            metrics_state.record_message(session_id, result.get("metadata", {}))

            await websocket.send_json(
                {
                    "type": "response",
                    "response": result["response"],
                    "session_id": session_id,
                    "metadata": result.get("metadata", {}),
                }
            )
    except WebSocketDisconnect:
        logger.info("🔌 WebSocket kesildi: %s", session_id)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("WebSocket hatası: %s", exc)
        await websocket.send_json(
            {"type": "error", "error": "Sunucu hatası", "session_id": session_id}
        )
    finally:
        metrics_state.close_session(session_id)
        try:
            await websocket.close()
        except RuntimeError:
            pass


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    if not request.message:
        raise HTTPException(status_code=422, detail="Mesaj alanı boş bırakılamaz")

    metrics_state.register_session(request.session_id)
    result = run_agent(session_id=request.session_id, user_input=request.message)
    metrics_state.record_message(request.session_id, result.get("metadata", {}))

    return ChatResponse(
        response=result["response"],
        session_id=request.session_id,
        metadata=result.get("metadata", {}),
    )
