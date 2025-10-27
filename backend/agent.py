import json
import os
from backend.tools import tools

class AgentState(dict):
    """Agent state container"""
    pass

def intent_router(state: AgentState):
    """Kullanıcı niyetini belirler."""
    user_input = state.get("user_input", "").lower()
    keywords = ["sipariş", "siparis", "kargo", "iade", "ödeme", "odeme", "politika", "garanti"]
    
    for keyword in keywords:
        if keyword in user_input:
            state["intent"] = "tool"
            return state
    
    state["intent"] = "faq"
    return state

def retriever(state: AgentState):
    """Knowledge base'den bilgi çeker."""
    kb_paths = [
        "knowledge/kb.json",
        os.path.join(os.path.dirname(__file__), "..", "knowledge", "kb.json")
    ]
    
    kb = None
    for path in kb_paths:
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    kb = json.load(f)
                break
        except (FileNotFoundError, json.JSONDecodeError):
            continue
    
    if kb is None:
        # Default knowledge base
        kb = {
            "iade": "İade politikası: Ürünlerinizi 14 gün içinde iade edebilirsiniz.",
            "kargo": "Kargo süresi: Ortalama 2-4 iş günü içinde teslim edilir.",
            "ödeme": "Ödeme seçenekleri: Kredi kartı, banka kartı veya kapıda ödeme.",
            "odeme": "Ödeme seçenekleri: Kredi kartı, banka kartı veya kapıda ödeme.",
            "politika": "Tüm politikalarımız müşteri memnuniyeti odaklıdır.",
            "garanti": "Ürünlerimiz 2 yıl garanti kapsamındadır."
        }
    
    user_input = state.get("user_input", "").lower()
    for key in kb.keys():
        if key in user_input:
            state["kb_result"] = kb[key]
            return state
    
    state["kb_result"] = "İlgili bilgi bulunamadı. Lütfen daha spesifik bir soru sorun."
    return state

def tool_caller(state: AgentState):
    """Tool çağrısı yapar."""
    user_input = state.get("user_input", "").lower()
    
    # Sipariş sorgusu
    if "sipariş" in user_input or "siparis" in user_input:
        import re
        order_match = re.search(r'\d{5}', user_input)
        order_id = order_match.group(0) if order_match else "12345"
        result = tools[0].invoke({"order_id": order_id})
    
    # Kargo sorgusu
    elif "kargo" in user_input:
        cities = ["istanbul", "ankara", "izmir", "antalya", "bursa"]
        city = next((c for c in cities if c in user_input), "istanbul")
        result = tools[1].invoke({"city": city})
    
    # Politika sorgusu
    elif any(keyword in user_input for keyword in ["iade", "politika", "ödeme", "odeme", "garanti"]):
        topics = ["iade", "kargo", "ödeme", "odeme", "politika", "garanti"]
        topic = next((t for t in topics if t in user_input), "politika")
        result = tools[2].invoke({"topic": topic})
    
    else:
        result = "Bu konuda size yardımcı olabilecek bir araç bulunamadı."
    
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

def run_agent(user_input: str, session_id: str):
    """
    Agent'i çalıştırır.
    Basit pipeline implementasyonu: intent routing -> retrieval -> tool calling -> response
    """
    state = {"user_input": user_input, "session_id": session_id}
    
    # Pipeline
    state = intent_router(state)
    state = retriever(state)
    state = tool_caller(state)
    state = response_builder(state)
    
    return state.get("response", "Yanıt üretilemedi.")
