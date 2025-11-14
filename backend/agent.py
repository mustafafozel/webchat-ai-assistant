# backend/agent.py
from typing import Literal, Dict, Any
from pydantic import BaseModel
# from langgraph import StateGraph, END  # Bu satırı kaldır/kapat
from .tools import check_order_status, calculate_shipping, policy_lookup
from .rag_setup import mini_rag_search

class AgentState(BaseModel):
    session_id: str
    user_message: str
    intent: Literal["faq", "tool", "general"] | None = None
    context: Dict[str, Any] = {}
    answer: str | None = None

def intent_router_node(state: AgentState) -> AgentState:
    m = state.user_message.lower()
    if any(k in m for k in ["iade","kargo","ödeme","policy","faq"]):
        state.intent = "faq"
    elif any(k in m for k in ["sipariş","order","shipping","ücret"]):
        state.intent = "tool"
    else:
        state.intent = "general"
    return state

def retriever_node(state: AgentState) -> AgentState:
    state.context["kb"] = mini_rag_search(state.user_message)
    return state

def tool_caller_node(state: AgentState) -> AgentState:
    m = state.user_message.lower()
    if "sipariş" in m:
        state.context["tool"] = check_order_status("ABC123")
    elif "kargo" in m and "ücret" in m:
        state.context["tool"] = calculate_shipping("İstanbul")
    else:
        topic = "iade" if "iade" in m else ("kargo" if "kargo" in m else "ödeme")
        state.context["tool"] = policy_lookup(topic)
    return state

def response_builder_node(state: AgentState) -> AgentState:
    if state.intent == "faq":
        kb = state.context.get("kb") or []
        state.answer = kb[0] if kb else "Bu konuda bilgi bulamadım."
    elif state.intent == "tool":
        state.answer = str(state.context.get("tool"))
    else:
        state.answer = "Sorunuzu aldım, nasıl yardımcı olabilirim?"
    return state

def run_agent(session_id: str, message: str) -> str:
    state = AgentState(session_id=session_id, user_message=message)
    state = intent_router_node(state)
    if state.intent == "faq":
        state = retriever_node(state)
    elif state.intent == "tool":
        state = tool_caller_node(state)
    state = response_builder_node(state)
    # memory manager vs. DB kayıt zaten main.py içinde varsa çalışır
    return state.answer or "Bir cevap üretemedim."

