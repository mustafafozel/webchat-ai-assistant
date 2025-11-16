# Demo Senaryoları

Aşağıdaki akışlar Etkin.ai teslim maddelerindeki **canlı demo** beklentilerini karşılamak üzere hazırlanmıştır.

## Senaryo 1 – Widget üzerinden sipariş takibi

1. Tarayıcıda `http://localhost:8000` adresini açın ve widget butonuna tıklayın.
2. Açılan panelde "Sipariş durumumu öğrenmek istiyorum" mesajını gönderin.
3. WebSocket üzerinden aşağıdaki olaylar beklenir:
   - Sistem mesajı: "Bağlantı kuruldu".
   - Kullanıcı mesajı kayıt altına alınır (`/api/metrics` `total_messages` artar).
   - Agent "check_order_status" aracını çağırır, `/api/metrics` içinde `tool_usage.check_order_status` +1 olur.
4. Yanıt olarak mock sipariş durumunu belirten mesaj döner ve `frontend/widget.js` sistemi panelde gösterir.

**Başarı Kriterleri**
- `/api/metrics` endpoint'i aktif oturumda artan mesaj ve tool sayılarını gösterir.
- Veritabanında `messages` tablosuna kullanıcı ve asistan girdisi eklenir (ör. `SELECT * FROM messages ORDER BY created_at DESC LIMIT 2`).

## Senaryo 2 – HTTP fallback ile SSS yanıtı

1. Terminalden aşağıdaki cURL komutunu çalıştırın:
   ```bash
   curl -X POST http://localhost:8000/api/chat \
        -H "Content-Type: application/json" \
        -d '{"message":"İade politikası nedir?","session_id":"demo-http"}'
   ```
2. LangGraph intent router mesajı `faq` olarak sınıflandırır ve `mini_rag_search` ile bilgi tabanından sonuç döner.
3. Yanıt olarak "İade politikası" maddesinden gelen bilgi JSON cevabındaki `response` alanında görünür.
4. `/api/metrics` çağrısında `sessions` listesinde `demo-http` oturumunun `message_count` değeri artmıştır.

**Başarı Kriterleri**
- HTTP yanıtı `200` döner ve `metadata.kb_results` alanında en az bir satır bulunur.
- `knowledge/kb.json` içeriği değişmeden kullanılabildiğini göstermek için `metadata.intent` değeri `faq` olmalıdır.

## Senaryo 3 – Politika bilgisi için tool fallback

1. Widget açıkken "Kargo politikası hakkında bilgi" yazın.
2. Intent router mesajı `tool` olarak işaretleyemezse bile `tool_caller_node` `policy_lookup` aracını seçer.
3. Dönen yanıt "policy_lookup" çıktısını içerir ve `/api/metrics` içinde `tool_usage.policy_lookup` artar.

**Başarı Kriterleri**
- Yanıt metninde "politika" vurgusu ve araç adı `metadata.tool` alanında `policy_lookup` olarak görünür.
- Aynı oturumda yeni mesaj gönderildiğinde widget otomatik yeniden bağlanma özelliği sayesinde WebSocket bağlantısı korunur.
