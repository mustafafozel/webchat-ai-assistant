"""LangGraph powered conversation flow for the WebChat AI Assistant."""

from __future__ import annotations

import re
import unicodedata
from typing import Annotated, Dict, List, Literal, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from backend.config import settings
from backend.database import SessionLocal
from backend.models import Conversation, Message as MessageModel
from backend.rag_setup import load_knowledge_base, mini_rag_search
from backend.tools import (
    TOOL_REGISTRY,
    calculate_shipping,
    check_order_status,
    policy_lookup,
)

try:  # Optional Groq LLM integration
    if settings.GROQ_API_KEY:
        from langchain_groq import ChatGroq

        _llm = ChatGroq(model=settings.GROQ_MODEL, api_key=settings.GROQ_API_KEY, temperature=0.2)
        LLM_WITH_TOOLS = _llm.bind_tools(TOOL_REGISTRY)
    else:
        LLM_WITH_TOOLS = None
except Exception:
    LLM_WITH_TOOLS = None

KNOWLEDGE_BASE = load_knowledge_base(settings.KNOWLEDGE_BASE_PATH)


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    intent: Literal["faq", "tool", "general"]
    context: Dict[str, str]
    next: Literal["retriever", "tool_caller", "response_builder", str]


def _normalize_text(text: str) -> str:
    """Case-fold and strip diacritics for robust intent detection."""
    folded = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in folded if not unicodedata.combining(char))


FAQ_KEYWORDS = [_normalize_text(word) for word in ["iade", "kargo", "ödeme", "policy", "faq"]]
TOOL_KEYWORDS = [_normalize_text(word) for word in ["sipariş", "order", "takip", "kargo ücret"]]


def intent_router_node(state: AgentState) -> AgentState:
    """Route incoming message to the appropriate node."""
    last_message = _normalize_text(state["messages"][-1].content)
    state["intent"] = "general"
    state["next"] = "response_builder"

    if any(keyword in last_message for keyword in FAQ_KEYWORDS):
        state["intent"] = "faq"
        state["next"] = "retriever"
    elif any(keyword in last_message for keyword in TOOL_KEYWORDS):
        state["intent"] = "tool"
        state["next"] = "tool_caller"

    return state


def retriever_node(state: AgentState) -> AgentState:
    """Fetch FAQ snippets via the lightweight RAG helper."""
    last_message = state["messages"][-1].content
    kb_results = mini_rag_search(last_message, KNOWLEDGE_BASE, k=2)
    if kb_results:
        state.setdefault("context", {})["kb"] = kb_results
    state["next"] = "response_builder"
    return state


def _extract_order_id(text: str) -> str:
    match = re.search(r"(\d{4,})", text)
    return match.group(1) if match else "12345"


def tool_caller_node(state: AgentState) -> AgentState:
    """Execute mock tools without waiting for LLM function calls."""
    raw_message = state["messages"][-1].content
    message = _normalize_text(raw_message)
    context = state.setdefault("context", {})

    if "sipariş" in message or re.search(r"\d{4,}", raw_message):
        order_id = _extract_order_id(raw_message)
        context["tool_name"] = "check_order_status"
        context["tool_result"] = check_order_status(order_id)
    elif "kargo" in message and ("hesap" in message or "ücret" in message):
        city_match = re.search(r"(istanbul|ankara|izmir|antalya)", message)
        city = city_match.group(1) if city_match else "İstanbul"
        context["tool_name"] = "calculate_shipping"
        context["tool_result"] = calculate_shipping(city)
    else:
        if "iade" in message:
            topic = "iade"
        elif "kargo" in message:
            topic = "kargo"
        elif "odeme" in message or "ödeme" in message:
            topic = "ödeme"
        else:
            topic = "kargo"
        context["tool_name"] = "policy_lookup"
        context["tool_result"] = policy_lookup(topic)

    state["next"] = "response_builder"
    return state


def _compose_response(state: AgentState) -> str:
    context = state.get("context", {})
    intent = state.get("intent", "general")
    user_text = state["messages"][-1].content

    if intent == "faq" and context.get("kb"):
        kb_text = context["kb"][0]
        return f"Bulduğum bilgilere göre: {kb_text}"

    if intent == "tool" and context.get("tool_result"):
        return context["tool_result"]

    if context.get("kb"):
        return f"İlgili dokümanlardan öne çıkan bilgi: {context['kb'][0]}"

    return f"'{user_text}' mesajınızı aldım. Size nasıl yardımcı olabilirim?"


def response_builder_node(state: AgentState) -> AgentState:
    """Return an AI message using Groq when available, otherwise rule-based text."""
    system_prompt = (
        "Sen Etkin.ai WebChat asistanısın. Profesyonel, net ve yardımsever bir üslupla cevap ver."
    )

    context_messages: List[BaseMessage] = []
    context = state.get("context", {})
    if context.get("kb"):
        kb_text = "\n".join(context["kb"])
        context_messages.append(SystemMessage(content=f"Bilgi bankası sonucu:\n{kb_text}"))
    if context.get("tool_result"):
        context_messages.append(
            SystemMessage(
                content=f"Araç çıktısı ({context.get('tool_name')}): {context['tool_result']}"
            )
        )

    if LLM_WITH_TOOLS:
        messages = [SystemMessage(content=system_prompt), *context_messages, *state["messages"]]
        ai_message = LLM_WITH_TOOLS.invoke(messages)
        response_text = ai_message.content
    else:
        response_text = _compose_response(state)
        ai_message = AIMessage(content=response_text)

    state["messages"].append(ai_message)
    state["next"] = END
    return state


workflow = StateGraph(AgentState)
workflow.add_node("intent_router", intent_router_node)
workflow.add_node("retriever", retriever_node)
workflow.add_node("tool_caller", tool_caller_node)
workflow.add_node("response_builder", response_builder_node)
workflow.set_entry_point("intent_router")
workflow.add_conditional_edges(
    "intent_router",
    lambda current_state: current_state["next"],
    {
        "retriever": "retriever",
        "tool_caller": "tool_caller",
        "response_builder": "response_builder",
    },
)
workflow.add_edge("retriever", "response_builder")
workflow.add_edge("tool_caller", "response_builder")

graph_app = workflow.compile()


def _persist_messages(session_id: str, user_message: str, ai_message: str, metadata: Dict[str, object]):
    db = SessionLocal()
    try:
        conversation = db.query(Conversation).filter_by(session_id=session_id).first()
        if not conversation:
            conversation = Conversation(session_id=session_id)
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        db.add(
            MessageModel(
                conversation_id=conversation.id,
                sender="user",
                content=user_message,
                metadata_json={"intent": metadata.get("intent")},
            )
        )
        db.add(
            MessageModel(
                conversation_id=conversation.id,
                sender="assistant",
                content=ai_message,
                metadata_json=metadata,
            )
        )
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def run_agent(session_id: str, user_input: str) -> Dict[str, object]:
    """Execute the LangGraph workflow and persist conversation history."""
    if not graph_app:
        return {"response": "Agent başlatılamadı", "metadata": {"intent": "error"}}

    initial_state: AgentState = {
        "messages": [HumanMessage(content=user_input)],
        "intent": "general",
        "context": {},
        "next": "response_builder",
    }

    final_state = graph_app.invoke(initial_state, config={"configurable": {"thread_id": session_id}})
    response_message = final_state["messages"][-1].content
    metadata = {
        "intent": final_state.get("intent"),
        "kb_results": final_state.get("context", {}).get("kb", []),
        "tool": final_state.get("context", {}).get("tool_name"),
        "tool_result": final_state.get("context", {}).get("tool_result"),
    }

    _persist_messages(session_id, user_input, response_message, metadata)
    return {"response": response_message, "metadata": metadata}
