import json
import os
from backend.config import settings
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

def create_rag_index():
    """
    knowledge/kb.json dosyasını okur, vektörlere ayırır ve 
    FAISS index'ini diske kaydeder.
    """
    print("RAG indeksi oluşturuluyor...")
    
    # 1. Knowledge Base dosyasını yükle
    try:
        with open(settings.KNOWLEDGE_BASE_FILE, "r", encoding="utf-8") as f:
            kb_data = json.load(f)
        print(f"'{settings.KNOWLEDGE_BASE_FILE}' başarıyla yüklendi.")
    except Exception as e:
        print(f"HATA: Knowledge base dosyası okunamadı: {e}")
        return

    # 2. Veriyi LangChain 'Document' formatına çevir
    # İş dökümanındaki SSS formatına göre (Örn: "İade politikası: 14 gün...")
    # JSON formatımız: {"iade": "İade politikası: 14 gün...", "kargo": "..."}
    documents = []
    for topic, content in kb_data.items():
        # 'page_content' LangChain için zorunlu alandır.
        # 'metadata' arama sonrası kaynağı bilmemiz için önemlidir.
        doc = {"page_content": content, "metadata": {"source": topic}}
        documents.append(doc)
        
    # 3. Metinleri böl (RAG için önemli)
    # Bizim KB küçük olduğu için bu adım çok kritik değil, ama iyi bir pratiktir.
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    split_docs = text_splitter.create_documents(
        [d["page_content"] for d in documents],
        metadatas=[d["metadata"] for d in documents]
    )

    # 4. Embedding modelini yükle
    # (Groq/OpenAI ücretli olduğu için embedding'i lokal ve ücretsiz modelle yapalım)
    print(f"Embedding modeli yükleniyor: {settings.EMBEDDING_MODEL_NAME}")
    try:
        embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL_NAME)
    except Exception as e:
        print(f"HATA: Embedding modeli indirilemedi. İnternet bağlantınızı kontrol edin. Hata: {e}")
        return
        
    # 5. FAISS Vektör Veritabanını oluştur
    print("Vektör veritabanı (FAISS) oluşturuluyor...")
    try:
        vector_store = FAISS.from_documents(split_docs, embeddings)
    except Exception as e:
        print(f"HATA: FAISS indeksi oluşturulamadı: {e}")
        return

    # 6. Vektör veritabanını diske kaydet
    if not os.path.exists(settings.RAG_INDEX_PATH):
        os.makedirs(settings.RAG_INDEX_PATH)
        
    vector_store.save_local(settings.RAG_INDEX_PATH)
    print(f"✅ RAG indeksi başarıyla '{settings.RAG_INDEX_PATH}' dizinine kaydedildi.")

if __name__ == "__main__":
    create_rag_index()
