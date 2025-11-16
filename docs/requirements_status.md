# Etkin.ai Teknik Gereksinim Karşılaştırma Tablosu

Bu dosya, müşteri tarafından paylaşılan teknik gereksinim görsellerindeki maddelerin repodaki en güncel sürümde nasıl karşılandığını özetler.

| Gereksinim | Uygulama | İlgili Dosyalar |
| --- | --- | --- |
| LangGraph tabanlı akışta Intent Router → Retriever (mini-RAG) → Tool Caller → Response Builder zinciri | `backend/graph.py` dosyasında `StateGraph` ile dört düğümlü akış tanımlanır, Groq destekli LLM bağlandığı durumda tool çağrılarını kullanır. | `backend/graph.py` |
| Mock tool'lar (sipariş takibi, kargo ücreti, politika) | `backend/tools.py` üç fonksiyonu döner ve LangGraph `TOOL_REGISTRY`ne eklenir. | `backend/tools.py` |
| Mini knowledge base | `knowledge/kb.json` dosyasında 10+ maddelik SSS/politika içerikleri yer alır, `backend/rag_setup.py` JSON yükleyicisi ve `mini_rag_search` fonksiyonu ile kullanılır. | `knowledge/kb.json`, `backend/rag_setup.py` |
| WebSocket + HTTP API uçları, sağlık ve metrik servisi | FastAPI uygulaması `/api/health`, `/api/metrics`, `/api/chat` ve `/ws` uçlarını; oturum/metrik sayacını içerir. | `backend/main.py` |
| Oturum bazlı veri tabanı kalıcılığı | SQLAlchemy `Conversation`/`Message` modelleri ve `_persist_messages` fonksiyonu oturum geçmişini saklar. | `backend/models.py`, `backend/database.py`, `backend/graph.py` |
| Gömülebilir widget ve otomatik yeniden bağlanan WebSocket istemcisi | `frontend/widget.js` script'i CSS'i yükler, paneli oluşturur, WebSocket'i yönetir ve bağlantıyı yeniler. | `frontend/widget.js`, `frontend/widget.css` |
| Dokümantasyon ve entegrasyon talimatları | README teknik gereksinim checklist'i, kurulum, API kullanımı ve widget entegrasyon örneğini içerir. | `README.md` |
| Changelog ve teslimat kayıtları | GitHub teslim formatındaki "CHANGELOG" beklentisini karşılayan sürüm notları. | `CHANGELOG.md` |
| ARCHITECTURE & Demo senaryoları | Mimari açıklama ve kabul testi akışları ayrı dosyalarda listelendi. | `ARCHITECTURE.md`, `demo_scenarios.md` |

> Not: Otomatik testler, FastAPI bağımlılığı bu çalışma ortamında kurulu olmadığı için CI dışında başarısız olabilir. Gereksinim setini etkileyen bir eksik tespit edilmemiştir.
