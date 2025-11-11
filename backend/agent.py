# backend/agent.py
from typing import Literal, Dict, Any
from langgraph.graph import StateGraph, END
from pydantic import BaseModel
from .tools import check_order_status, calculate_shipping, policy_lookup
from .rag_setup import mini_rag_search  # rag_setup.py içinde küçük bir arama fonksiyonu varsayalım

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
    elif any(k in m for k in ["sipariş","kargo ücreti","order","shipping","ücret"]):
        state.intent = "tool"
    else:
        state.intent = "general"
    return state

def retriever_node(state: AgentState) -> AgentState:
    hits = mini_rag_search(state.user_message)  # ['...', '...']
    state.context["kb"] = hits
    return state

def tool_caller_node(state: AgentState) -> AgentState:
    m = state.user_message.lower()
    if "sipariş" in m:
        state.context["tool"] = check_order_status("ABC123")
    elif "kargo" in m and "ücret" in m:
        state.context["tool"] = calculate_shipping("İstanbul")
    else:
        # Basit politika lookup örneği
        topic = "iade" if "iade" in m else ("kargo" if "kargo" in m else "ödeme")
        state.context["tool"] = policy_lookup(topic)
    return state

def response_builder_node(state: AgentState) -> AgentState:
    if state.intent == "faq":
        kb = state.context.get("kb") or []
        state.answer = kb[0] if kb else "Bu konuda temel bilgiyi bulamadım."
    elif state.intent == "tool":
        state.answer = str(state.context.get("tool"))
    else:
        state.answer = "Sorunuzu aldım, nasıl yardımcı olabilirim?"
    return state

# Memory Manager: burada sadece cevabı döndürüyoruz; DB kayıt main.py içinde yapılıyor.
def memory_manager_node(state: AgentState) -> AgentState:
    return state

def compile_graph():
    g = StateGraph(AgentState)
    g.add_node("intent_router", intent_router_node)
    g.add_node("retriever", retriever_node)
    g.add_node("tool_caller", tool_caller_node)
    g.add_node("response_builder", response_builder_node)
    g.add_node("memory_manager", memory_manager_node)

    g.set_entry_point("intent_router")
    def route_decision(state: AgentState):
        return state.intent or "general"

    g.add_conditional_edges("intent_router", route_decision,
        {"faq":"retriever","tool":"tool_caller","general":"response_builder"})
    g.add_edge("retriever","response_builder")
    g.add_edge("tool_caller","response_builder")
    g.add_edge("response_builder","memory_manager")
    g.add_edge("memory_manager", END)
    return g.compile()

graph = compile_graph()

def run_agent(session_id: str, message: str) -> str:
    out = graph.invoke(AgentState(session_id=session_id, user_message=message))
    return out.answer or "Bir cevap üretemedim."

