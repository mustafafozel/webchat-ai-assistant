import json
import uuid
import os
from typing import TypedDict, Annotated, List, Literal
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph_community.checkpoints.sqlalchemy import SqlAlchemyCheckpoint
from sqlalchemy.orm import sessionmaker
from backend.database import engine
from backend.config import settings
from backend.models import Conversation, Message as MessageModel
from sqlalchemy.orm import Session
from backend.database import SessionLocal

# --- 1. Araç (Tool) Tanımları ---
# İş dökümanında istenen mock tool'lar
# (backend/tools.py'den kopyalamak yerine LangChain standardında tanımlayalım)

@tool
def check_order_status(order_id: str) -> str:
    """Sipariş durumunu kontrol eder."""
    print(f"--- TOOL ÇAĞRISI: check_order_status (ID: {order_id}) ---")
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
    print(f"--- TOOL ÇAĞRISI: calculate_shipping (Şehir: {city}) ---")
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
    """Politika bilgilerini (iade, kargo, ödeme) KB'den arar."""
    # Bu tool RAG retriever'ını tetikler.
    # Bu aslında bir placeholder, asıl işi 'retriever' node'u yapacak.
    print(f"--- TOOL ÇAĞRISI: policy_lookup (Konu: {topic}) ---")
    return f"Politika araması için '{topic}' konusu RAG modülüne yönlendiriliyor."

tools = [check_order_status, calculate_shipping, policy_lookup]

# --- 2. RAG Yükleyici ---
# Diske kaydettiğimiz FAISS indexini yükle
try:
    embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL_NAME)
    vector_store = FAISS.load_local(settings.RAG_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
    retriever_tool = vector_store.as_retriever(search_kwargs={"k": 2})
    print("✅ FAISS RAG indeksi başarıyla yüklendi.")
except Exception as e:
    print(f"UYARI: FAISS RAG indeksi yüklenemedi. 'rag_setup.py' çalıştırıldı mı? Hata: {e}")
    retriever_tool = None

# --- 3. LangGraph State (Durum) Tanımı ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]
    # 'next' alanı bir sonraki adımın ne olacağını belirler
    next: Literal["retriever", "tool_caller", "response_builder", END]

# --- 4. PostgreSQL Hafıza Yönetimi (İş Dökümanı İsteri) ---
# LangGraph'in konuşma geçmişini PostgreSQL'e kaydetmesini sağlar.
memory = SqlAlchemyCheckpoint(
    engine=engine,
    metadata=Base.metadata, # models.py'den
    # Konuşmaları 'conversations' tablosuna bağla
    conversation_table=Conversation.__table__ 
)

# --- 5. LLM (Model) Tanımı ---
# Groq (hızlı ve ücretsiz limitleri var)
llm = ChatGroq(
    model="llama3-70b-8192", 
    api_key=settings.GROQ_API_KEY,
    temperature=0
)
# Araçları LLM'e bağla
llm_with_tools = llm.bind_tools(tools)

# --- 6. LangGraph Düğümleri (Nodes) ---

def intent_router_node(state: AgentState):
    """
    İş Dökümanı İsteri: Intent Router
    Gelen son mesaja bakar ve FAQ (RAG) mi yoksa Tool mü olduğuna karar verir.
    """
    print("--- NODE: Intent Router ---")
    last_message = state['messages'][-1].content

    # Çok basit bir yönlendirme
    if "sipariş" in last_message or "kargo hesapla" in last_message:
        print("Karar: Tool Çağrısı")
        state['next'] = "tool_caller"
    elif "iade" in last_message or "politika" in last_message or "ödeme" in last_message or "kargo süresi" in last_message:
        print("Karar: FAQ (RAG Retriever)")
        state['next'] = "retriever"
    else:
        print("Karar: Genel Yanıt")
        state['next'] = "response_builder" # Direkt LLM'e gitsin
    return state

def tool_caller_node(state: AgentState):
    """
    İş Dökümanı İsteri: Tool Caller
    LLM'den gelen araç çağırma isteğini çalıştırır.
    """
    print("--- NODE: Tool Caller ---")
    tool_call = state['messages'][-1].tool_calls[0]
    tool_name = tool_call['name']
    tool_args = tool_call['args']

    selected_tool = None
    for tool in tools:
        if tool.name == tool_name:
            selected_tool = tool
            break

    if selected_tool:
        result = selected_tool.invoke(tool_args)
        state['messages'].append(ToolMessage(content=result, tool_call_id=tool_call['id']))
    else:
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

    state['next'] = "response_builder"
    return state

def response_builder_node(state: AgentState):
    """
    İş Dökümanı İsteri: Response Builder
    Tüm geçmişi (tool sonuçları, RAG sonuçları) LLM'e gönderip son yanıtı alır.
    """
    print("--- NODE: Response Builder ---")
    # 'system' mesajı ekleyerek LLM'e talimat ver
    system_prompt = (
        "Sen Etkin.ai WebChat asistanısın. Türkçe, profesyonel ve yardımsever bir dil kullan. "
        "Sana 'Bilgi bankasından bulunan ilgili içerik:' ile başlayan bir bilgi verilirse, "
        "o bilgiyi kullanarak yanıt ver. "
        "Sana 'tool_result' verilirse, o JSON sonucunu kullanıcıya güzel bir cümle ile açıkla."
    )

    # State'deki mesajların başına system prompt'u ekle
    messages_with_system_prompt = [SystemMessage(content=system_prompt)] + state['messages']

    # LLM'i çağır
    response = llm_with_tools.invoke(messages_with_system_prompt)

    # LLM'in yanıtını state'e ekle
    state['messages'].append(response)
    state['next'] = END # Akış sonlandı
    return state

# --- 7. Graph (Grafik) Oluşturma ---
workflow = StateGraph(AgentState)

# Düğümleri ekle
workflow.add_node("intent_router", intent_router_node)
workflow.add_node("tool_caller", tool_caller_node)
workflow.add_node("retriever", retriever_node)
workflow.add_node("response_builder", response_builder_node)

# Başlangıç noktasını belirle
workflow.set_entry_point("intent_router")

# Koşullu kenarlar (Router'dan sonra nereye gidilecek?)
workflow.add_conditional_edges(
    "intent_router",
    lambda state: state['next'], # 'next' alanındaki değere göre yönlendir
    {
        "tool_caller": "tool_caller",
        "retriever": "retriever",
        "response_builder": "response_builder"
    }
)

# Diğer kenarlar
workflow.add_edge("tool_caller", "response_builder")
workflow.add_edge("retriever", "response_builder")

# Grafiği derle
# 'checkpointer=memory' ile her adımı PostgreSQL'e kaydet
try:
    graph_app = workflow.compile(checkpointer=memory)
    print("✅ LangGraph grafiği başarıyla derlendi ve PostgreSQL'e bağlandı.")
except Exception as e:
    print(f"HATA: LangGraph derlenemedi: {e}")
    graph_app = None

# --- 8. Agent'i Çalıştırmak İçin Arayüz ---
def run_agent(session_id: str, user_input: str) -> str:
    """
    WebSocket veya HTTP'den gelen mesajı alır,
    LangGraph'i çalıştırır ve son yanıtı döner.
    """
    if not graph_app:
        return "Hata: AI Agent (LangGraph) başlatılamadı."

    # Konuşma ID'si (thread_id)
    config = {"configurable": {"thread_id": session_id}}

    # Mesajı bir listeye koy (graph 'messages' listesi bekler)
    input_messages = [HumanMessage(content=user_input)]

    try:
        # Agent'i çalıştır
        # 'stream' yerine 'invoke' kullanarak son yanıtı direkt al
        final_state = graph_app.invoke({"messages": input_messages}, config=config)

        # Son mesaj (AI yanıtı)
        response_message = final_state['messages'][-1].content

        # PostgreSQL'e manuel kayıt (LangGraph checkpoint bazen gecikebilir)
        # Memory Manager (İş Dökümanı İsteri) - checkpoint'e ek olarak
        try:
            db: Session = next(get_db())
            # Konuşmayı bul veya oluştur
            conversation = db.query(Conversation).filter_by(session_id=session_id).first()
            if not conversation:
                conversation = Conversation(session_id=session_id)
                db.add(conversation)
                db.commit()
                db.refresh(conversation)

            # Kullanıcı mesajını kaydet
            db.add(MessageModel(conversation_id=conversation.id, sender="user", content=user_input))
            # AI mesajını kaydet
            db.add(MessageModel(conversation_id=conversation.id, sender="assistant", content=response_message))
            db.commit()
            print(f"--- DB: Mesajlar session_id {session_id} için PostgreSQL'e kaydedildi ---")
        except Exception as db_e:
            print(f"UYARI: PostgreSQL'e manuel kayıt başarısız: {db_e}")
        finally:
            db.close()

        return response_message

    except Exception as e:
        print(f"HATA: Agent çalıştırılırken hata oluştu: {e}")
        return "Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin."
