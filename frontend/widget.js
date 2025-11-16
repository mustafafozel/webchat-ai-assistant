(function (global) {
  const CURRENT_SCRIPT = document.currentScript;
  const DEFAULT_API_BASE = (() => {
    try {
      if (CURRENT_SCRIPT) {
        const url = new URL(CURRENT_SCRIPT.src);
        return url.origin;
      }
    } catch (error) {
      console.warn("WebChatAI: API origin belirlenemedi, window.location kullanılacak", error);
    }
    return window.location.origin;
  })();
  const SESSION_STORAGE_KEY = "webchatai-session-id";
  const TYPING_TEXT = "Asistan yazıyor...";

  let webSocket = null;
  let config = {};
  let isPanelOpen = false;

  function createWidget() {
    // CSS'i dinamik olarak yükle (Eğer index.html'e eklenmediyse)
    if (!document.querySelector('link[href*="widget.css"]')) {
        const cssLink = document.createElement('link');
        cssLink.rel = 'stylesheet';
        cssLink.href = buildAssetUrl('/static/widget.css');
        document.head.appendChild(cssLink);
    }

    // Toggle button
    const toggle = document.createElement('button');
    toggle.id = 'webchatai-toggle';
    toggle.innerHTML = '💬';
    toggle.title = 'WebChat AI';
    document.body.appendChild(toggle);

    // Panel
    const panel = document.createElement('div');
    panel.id = 'webchatai-panel';
    panel.innerHTML = `
      <div class="webchatai-header">
        <span>WebChat AI</span>
        <button id="webchatai-close">✕</button>
      </div>
      <div class="webchatai-body" id="webchatai-body">
        <div class="webchatai-msg assistant">Merhaba! Size nasıl yardımcı olabilirim?</div>
      </div>
      <div class="webchatai-input">
        <input id="webchatai-input" type="text" placeholder="Mesajınızı yazın..." />
        <button id="webchatai-send">Gönder</button>
      </div>
    `;
    document.body.appendChild(panel);
  }

  function addMessage(type, text) {
    const body = document.getElementById('webchatai-body');
    if (!body) return;

    const typingMsg = document.getElementById('webchatai-typing');
    if (typingMsg) {
      typingMsg.remove();
    }

    if (type === 'assistant' && text === TYPING_TEXT) {
      const msg = document.createElement('div');
      msg.className = 'webchatai-msg assistant typing';
      msg.id = 'webchatai-typing';
      msg.innerHTML = `
        <span class="webchatai-typing-dot"></span>
        <span class="webchatai-typing-dot"></span>
        <span class="webchatai-typing-dot"></span>
        <span class="webchatai-typing-label">${text}</span>
      `;
      body.appendChild(msg);
    } else {
      const msg = document.createElement('div');
      msg.className = 'webchatai-msg ' + type;
      msg.textContent = text;
      body.appendChild(msg);
    }
    body.scrollTop = body.scrollHeight;
  }

  function showTypingIndicator() {
    if (document.getElementById('webchatai-typing')) {
      return;
    }
    addMessage('assistant', TYPING_TEXT);
  }

  function buildAssetUrl(path) {
    try {
      return new URL(path, config.apiBase).toString();
    } catch (error) {
      console.warn("WebChatAI: asset URL oluşturulamadı", error);
      return path;
    }
  }

  function getWebSocketUrl() {
    try {
      const base = new URL(config.apiBase);
      const protocol = base.protocol === 'https:' ? 'wss:' : 'ws:';
      return `${protocol}//${base.host}/ws?session_id=${encodeURIComponent(config.sessionId)}`;
    } catch (error) {
      console.warn('WebChatAI: WS URL oluşturulamadı, window.location kullanılacak', error);
      const fallbackProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      return `${fallbackProtocol}//${window.location.host}/ws?session_id=${encodeURIComponent(config.sessionId)}`;
    }
  }

  function connectWebSocket() {
    const wsUrl = getWebSocketUrl();
    
    console.log('WebSocket bağlantısı kuruluyor:', wsUrl);
    
    webSocket = new WebSocket(wsUrl);

    webSocket.onopen = () => {
      console.log('WebSocket bağlantısı açıldı.');
      addMessage('system', 'Bağlantı kuruldu.');
    };

    webSocket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === 'response') {
          addMessage('assistant', payload.response);
          if (payload.metadata && payload.metadata.kb_results && payload.metadata.kb_results.length) {
            addMessage('system', `📚 Bilgi kaynağı: ${payload.metadata.kb_results[0]}`);
          }
        } else if (payload.type === 'error') {
          addMessage('system', payload.error || 'Bilinmeyen hata.');
        } else {
          addMessage('assistant', event.data);
        }
      } catch (error) {
        addMessage('assistant', event.data);
      }
    };

    webSocket.onclose = () => {
      console.log('WebSocket bağlantısı kapandı.');
      addMessage('system', 'Bağlantı kesildi. Yeniden bağlanılıyor...');
      // 3 saniye sonra yeniden bağlanmayı dene
      setTimeout(connectWebSocket, 3000); 
    };

    webSocket.onerror = (error) => {
      console.error('WebSocket hatası:', error);
      addMessage('system', 'Bağlantı hatası.');
      webSocket.close();
    };
  }

  function handleSend() {
    const input = document.getElementById('webchatai-input');
    const message = input.value.trim();
    if (!message) return;
    
    if (!webSocket || webSocket.readyState !== WebSocket.OPEN) {
      addMessage('system', 'Bağlantı kuruluyor... Lütfen bekleyin.');
      connectWebSocket();
      return;
    }
    
    // Kullanıcı mesajını ekrana bas
    addMessage('user', message);
    showTypingIndicator();
    
    const payload = {
      message,
      session_id: config.sessionId,
    };

    // Mesajı WebSocket üzerinden sunucuya JSON olarak gönder
    webSocket.send(JSON.stringify(payload));

    input.value = '';
  }

  function init(options = {}) {
    const providedBase = options.apiUrl || options.apiBase || DEFAULT_API_BASE;
    config.apiBase = (providedBase || window.location.origin).replace(/\/$/, '');
    config.sessionId = resolveSessionId(options.sessionId);

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', setup);
    } else {
      setup();
    }
  }

  function resolveSessionId(customSessionId) {
    const normalized = typeof customSessionId === 'string' ? customSessionId.trim() : '';
    if (normalized) {
      persistSessionId(normalized);
      return normalized;
    }

    try {
      const stored = localStorage.getItem(SESSION_STORAGE_KEY);
      if (stored) {
        return stored;
      }
    } catch (error) {
      console.warn('WebChatAI: localStorage okunamadı', error);
    }

    const generated = 'session-' + Math.random().toString(36).substr(2, 9);
    persistSessionId(generated);
    return generated;
  }

  function persistSessionId(value) {
    try {
      localStorage.setItem(SESSION_STORAGE_KEY, value);
    } catch (error) {
      console.warn('WebChatAI: session id saklanamadı', error);
    }
  }

  function setup() {
    createWidget();
    
    const toggle = document.getElementById('webchatai-toggle');
    const panel = document.getElementById('webchatai-panel');
    const closeBtn = document.getElementById('webchatai-close');
    const input = document.getElementById('webchatai-input');
    const sendBtn = document.getElementById('webchatai-send');

    if (!toggle || !panel) return;

    toggle.addEventListener('click', () => {
      isPanelOpen = !isPanelOpen;
      panel.style.display = isPanelOpen ? 'flex' : 'none';
      
      // Panel açıldığında WebSocket bağlantısını kur
      if (isPanelOpen && (!webSocket || webSocket.readyState === WebSocket.CLOSED)) {
        connectWebSocket();
      }
    });

    if (closeBtn) closeBtn.addEventListener('click', () => {
      isPanelOpen = false;
      panel.style.display = 'none';
      // Panel kapandığında bağlantıyı kes (opsiyonel)
      if (webSocket && webSocket.readyState === WebSocket.OPEN) {
        webSocket.close();
      }
    });
    
    if (sendBtn) sendBtn.addEventListener('click', handleSend);
    if (input) input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') handleSend();
    });
  }

  global.WebChatAI = { init };
})(window);
