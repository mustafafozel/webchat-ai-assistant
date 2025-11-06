# Demo Senaryoları

Bu döküman, WebChat AI Assistant'ın temel fonksiyonlarını test etmek için senaryoları içerir.

## Senaryo 1: Genel Sohbet (RAG/FAQ karşılama)

1.  **Kullanıcı:** Merhaba, nasılsın?
2.  **AI:** (Genel bir selamlama yanıtı verir)
3.  **Kullanıcı:** İade politikası nedir?
4.  **AI (RAG):** (FAISS vektör aramasından "14 gün içinde iade hakkı vardır..." bilgisini içeren bir yanıt verir)
5.  **Kullanıcı:** Ödeme seçenekleri neler?
6.  **AI (RAG):** (FAISS'ten "Kredi kartı veya kapıda ödeme..." yanıtını verir)

## Senaryo 2: Tool Kullanımı (Sipariş Takip)

1.  **Kullanıcı:** 12345 numaralı siparişim nerede?
2.  **AI:** (LangGraph -> Tool Caller -> `check_order_status` tetiklenir) "12345 numaralı siparişiniz kargoya verildi."
3.  **Kullanıcı:** 67890 numaralı siparişimin durumu nedir?
4.  **AI:** (Tool -> `check_order_status`) "67890 numaralı siparişiniz hazırlanıyor."

## Senaryo 3: Tool Kullanımı (Kargo Hesaplama)

1.  **Kullanıcı:** Ankara için kargo hesaplar mısın?
2.  **AI:** (LangGraph -> Tool Caller -> `calculate_shipping` tetiklenir) "Ankara için kargo ücreti 30 TL'dir."
3.  **Kullanıcı:** İzmir kargo ne kadar?
4.  **AI:** (Tool -> `calculate_shipping`) "İzmir için kargo ücreti 28 TL'dir."

## Senaryo 4: Hafıza (Session Memory)

1.  **Kullanıcı:** Merhaba, adım Mustafa.
2.  **AI:** Merhaba Mustafa, size nasıl yardımcı olabilirim?
3.  **Kullanıcı:** Adım neydi?
4.  **AI:** (PostgreSQL hafızasından hatırlar) Adınız Mustafa.
