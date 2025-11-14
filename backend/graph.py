import json
import uuid
<<<<<<< HEAD
import os
from typing import TypedDict, Annotated, List, Literal
=======
from typing import TypedDict, Annotated, List, Literal

>>>>>>> 65eb5aa (feat: major update - LangGraph ReAct agent implementation)
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
<<<<<<< HEAD
from langgraph_community.checkpoints.sqlalchemy import SqlAlchemyCheckpoint
from sqlalchemy.orm import sessionmaker
from backend.database import engine
=======

from sqlalchemy.orm import Session
# from backend.database import Base, get_db, SessionLocal
>>>>>>> 65eb5aa (feat: major update - LangGraph ReAct agent implementation)
from backend.config import settings
from backend.models import Conversation, Message as MessageModel

# --- 1. Tool Tanımları ---
@tool
def check_order_status(order_id: str) -> str:
    """Sipariş durumunu kontrol eder."""
    print(f"🔧 TOOL: check_order_status({order_id})")
    mock_data = {
        "12345": "Siparişiniz kargoya verildi.",
        "67890": "Siparişiniz hazırlanıyor.",
        "11111": "Siparişiniz teslim edildi."
    }
    status = mock_data.get(order_id, f"{order_id} numaralı sipariş bulunamadı.")
    return json.dumps({"order_id": order_id, "status": status})

@tool
def calculate_shipping(city: str) -> str:
    """Bir şehir için kargo ücretini hesaplar."""
    print(f"🔧 TOOL: calculate_shipping({city})")
    prices = {
        "istanbul": 25,
        "ankara": 30,
        "izmir": 28,
        "antalya": 35
    }
    price = prices.get(city.lower(), 40)
    return json.dumps({"city": city, "shipping_cost": price})

@tool
def policy_lookup(topic: str) -> str:
    """Politika bilgilerini arar."""
    print(f"🔧 TOOL: policy_lookup({topic})")
    return f"'{topic}' konusu hakkında bilgi bulundu."

tools = [check_order_status, calculate_shipping, policy_lookup]

# --- 2. RAG Setup (ŞİMDİLİK KAPALI) ---
retriever_tool = None
print("⚠️ RAG (FAISS) şimdilik kapalı")

# --- 3. LangGraph State ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]
    next: Literal["tool_caller", "response_builder", END]

# --- 4. Memory (ŞİMDİLİK YOK) ---
memory = None
print("⚠️ Memory şimdilik kapalı")

# --- 5. LLM Setup ---
llm = ChatGroq(
    model="llama3-70b-8192",
    api_key=settings.GROQ_API_KEY,
    temperature=0
)
llm_with_tools = llm.bind_tools(tools)

# --- 6. Node Functions ---
def intent_router_node(state: AgentState):
<<<<<<< HEAD
    """
    İş Dökümanı İsteri: Intent Router
    Gelen son mesaja bakar ve FAQ (RAG) mi yoksa Tool mü olduğuna karar verir.
    """
    print("--- NODE: Intent Router ---")
    last_message = state['messages'][-1].content

    # Çok basit bir yönlendirme
    if "sipariş" in last_message or "kargo hesapla" in last_message:
        print("Karar: Tool Çağrısı")
=======
    """Mesajı analiz edip uygun node'a yönlendirir."""
    print("🧭 NODE: Intent Router")
    last_message = state['messages'][-1].content.lower()
    
    if "sipariş" in last_message or "kargo" in last_message:
        print("   → Tool Caller")
>>>>>>> 65eb5aa (feat: major update - LangGraph ReAct agent implementation)
        state['next'] = "tool_caller"
    else:
        print("   → Response Builder")
        state['next'] = "response_builder"
    
    return state

def tool_caller_node(state: AgentState):
    """LLM'den gelen tool call'ları çalıştırır."""
    print("🔧 NODE: Tool Caller")
    
    last_message = state['messages'][-1]
    
    if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
        print("   ⚠️ Tool call yok, response builder'a yönlendiriliyor")
        state['next'] = "response_builder"
        return state
    
    tool_call = last_message.tool_calls[0]
    tool_name = tool_call['name']
    tool_args = tool_call['args']
<<<<<<< HEAD

    selected_tool = None
    for tool in tools:
        if tool.name == tool_name:
            selected_tool = tool
            break

=======
    
    selected_tool = next((t for t in tools if t.name == tool_name), None)
    
>>>>>>> 65eb5aa (feat: major update - LangGraph ReAct agent implementation)
    if selected_tool:
        result = selected_tool.invoke(tool_args)
        state['messages'].append(
            ToolMessage(content=result, tool_call_id=tool_call['id'])
        )
    else:
<<<<<<< HEAD
        state['messages'].append(ToolMessage(content="Hata: Araç bulunamadı.", tool_call_id=tool_call['id']))

    state['next'] = "response_builder"
    return state

def retriever_node(state: AgentState):
    """
    İş Dökümanı İsteri: Retriever (RAG)
    FAISS vektör veritabanında arama yapar.
    """
    print("--- NODE: Retriever (RAG) ---")
    if not retriever_tool:
        result = "Hata: RAG (FAISS) modülü yüklenemedi."
    else:
        last_message = state['messages'][-1].content
        # Vektör araması yap
        docs = retriever_tool.invoke(last_message)
        # Aramadan gelen içeriği birleştir
        context = "\n\n".join([doc.page_content for doc in docs])
        result = f"Bilgi bankasından bulunan ilgili içerik:\n{context}"

    # RAG sonucunu ToolMessage olarak ekle (LLM'in bunu context olarak kullanması için)
    # 'policy_lookup' tool'u çağırılmış gibi davranıyoruz
    fake_tool_call_id = f"tool_{uuid.uuid4()}"
    state['messages'].append(ToolMessage(content=result, tool_call_id=fake_tool_call_id))

=======
        state['messages'].append(
            ToolMessage(
                content=f"Hata: '{tool_name}' aracı bulunamadı.",
                tool_call_id=tool_call['id']
            )
        )
    
>>>>>>> 65eb5aa (feat: major update - LangGraph ReAct agent implementation)
    state['next'] = "response_builder"
    return state

def response_builder_node(state: AgentState):
    """Nihai yanıtı oluşturur."""
    print("💬 NODE: Response Builder")
    
    system_prompt = (
        "Sen Etkin.ai WebChat asistanısın. Türkçe, profesyonel ve yardımsever konuş."
    )
<<<<<<< HEAD

    # State'deki mesajların başına system prompt'u ekle
    messages_with_system_prompt = [SystemMessage(content=system_prompt)] + state['messages']

    # LLM'i çağır
    response = llm_with_tools.invoke(messages_with_system_prompt)

    # LLM'in yanıtını state'e ekle
=======
    
    messages = [SystemMessage(content=system_prompt)] + state['messages']
    response = llm_with_tools.invoke(messages)
    
>>>>>>> 65eb5aa (feat: major update - LangGraph ReAct agent implementation)
    state['messages'].append(response)
    state['next'] = END
    return state

# --- 7. Graph Build ---
workflow = StateGraph(AgentState)

workflow.add_node("intent_router", intent_router_node)
workflow.add_node("tool_caller", tool_caller_node)
workflow.add_node("response_builder", response_builder_node)

workflow.set_entry_point("intent_router")

workflow.add_conditional_edges(
    "intent_router",
    lambda state: state['next'],
    {
        "tool_caller": "tool_caller",
        "response_builder": "response_builder"
    }
)

workflow.add_edge("tool_caller", "response_builder")

try:
    graph_app = workflow.compile()  # Memory olmadan
    print("✅ LangGraph başarıyla derlendi (minimal version)")
except Exception as e:
    print(f"❌ LangGraph derlenemedi: {e}")
    graph_app = None

# --- 8. Main Interface ---
def run_agent(session_id: str, user_input: str) -> str:
    """WebSocket/HTTP'den gelen mesajı işler."""
    if not graph_app:
<<<<<<< HEAD
        return "Hata: AI Agent (LangGraph) başlatılamadı."

    # Konuşma ID'si (thread_id)
    config = {"configurable": {"thread_id": session_id}}

    # Mesajı bir listeye koy (graph 'messages' listesi bekler)
=======
        return "❌ AI Agent başlatılamadı."
    
    config = {"configurable": {"thread_id": session_id}}
>>>>>>> 65eb5aa (feat: major update - LangGraph ReAct agent implementation)
    input_messages = [HumanMessage(content=user_input)]

    try:
        final_state = graph_app.invoke({"messages": input_messages}, config=config)
<<<<<<< HEAD

        # Son mesaj (AI yanıtı)
        response_message = final_state['messages'][-1].content

        # PostgreSQL'e manuel kayıt (LangGraph checkpoint bazen gecikebilir)
        # Memory Manager (İş Dökümanı İsteri) - checkpoint'e ek olarak
=======
        response_message = final_state['messages'][-1].content
        
        # PostgreSQL'e kaydet
        db = SessionLocal()
>>>>>>> 65eb5aa (feat: major update - LangGraph ReAct agent implementation)
        try:
            conversation = db.query(Conversation).filter_by(session_id=session_id).first()
            if not conversation:
                conversation = Conversation(session_id=session_id)
                db.add(conversation)
                db.commit()
                db.refresh(conversation)
<<<<<<< HEAD

            # Kullanıcı mesajını kaydet
            db.add(MessageModel(conversation_id=conversation.id, sender="user", content=user_input))
            # AI mesajını kaydet
            db.add(MessageModel(conversation_id=conversation.id, sender="assistant", content=response_message))
=======
            
            db.add(MessageModel(
                conversation_id=conversation.id,
                sender="user",
                content=user_input
            ))
            db.add(MessageModel(
                conversation_id=conversation.id,
                sender="assistant",
                content=response_message
            ))
>>>>>>> 65eb5aa (feat: major update - LangGraph ReAct agent implementation)
            db.commit()
            print(f"✅ DB: Mesajlar kaydedildi (session: {session_id})")
        except Exception as db_e:
            print(f"⚠️ DB kayıt hatası: {db_e}")
            db.rollback()
        finally:
            db.close()
<<<<<<< HEAD

        return response_message

=======
        
        return response_message
    
>>>>>>> 65eb5aa (feat: major update - LangGraph ReAct agent implementation)
    except Exception as e:
        print(f"❌ Agent hatası: {e}")
        return "Üzgünüm, bir hata oluştu."
