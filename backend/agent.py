from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor, ToolInvocation
from backend.tools import tools
from backend.config import settings
import json

llm = ChatOpenAI(model="gpt-3.5-turbo", openai_api_key=settings.OPENAI_API_KEY)
tool_executor = ToolExecutor(tools)

class AgentState(dict):
    pass

def intent_router(state: AgentState):
    """Kullanıcı niyetini belirler."""
    user_input = state.get("user_input", "")
    keywords = ["sipariş", "kargo", "iade", "ödeme", "politika"]
    
    for keyword in keywords:
        if keyword in user_input.lower():
            state["intent"] = "tool"
            return state
    
    state["intent"] = "faq"
    return state

def retriever(state: AgentState):
    """Knowledge base'den bilgi çeker."""
    with open("knowledge/kb.json", "r", encoding="utf-8") as f:
        kb = json.load(f)
    
    user_input = state.get("user_input", "").lower()
    for key in kb.keys():
        if key in user_input:
            state["kb_result"] = kb[key]
            return state
    
    state["kb_result"] = "İlgili bilgi bulunamadı."
    return state

def tool_caller(state: AgentState):
    """Tool çağrısı yapar."""
    user_input = state.get("user_input", "")
    
    if "sipariş" in user_input:
        result = tools[0].invoke({"order_id": "12345"})
    elif "kargo" in user_input:
        result = tools[1].invoke({"city": "istanbul"})
    else:
        result = "Tool bulunamadı."
    
    state["tool_result"] = result
    return state

def response_builder(state: AgentState):
    """Final yanıtı oluşturur."""
    if state.get("intent") == "faq":
        response = state.get("kb_result", "Üzgünüm, yardımcı olamadım.")
    else:
        response = state.get("tool_result", "İşlem tamamlanamadı.")
    
    state["response"] = response
    return state

# Graph oluştur
workflow = StateGraph(AgentState)
workflow.add_node("intent_router", intent_router)
workflow.add_node("retriever", retriever)
workflow.add_node("tool_caller", tool_caller)
workflow.add_node("response_builder", response_builder)

workflow.set_entry_point("intent_router")
workflow.add_edge("intent_router", "retriever")
workflow.add_edge("retriever", "tool_caller")
workflow.add_edge("tool_caller", "response_builder")
workflow.add_edge("response_builder", END)

agent_graph = workflow.compile()

def run_agent(user_input: str, session_id: str):
    """Agent'i çalıştırır."""
    state = {"user_input": user_input, "session_id": session_id}
    result = agent_graph.invoke(state)
    return result.get("response", "Yanıt üretilemedi.")
