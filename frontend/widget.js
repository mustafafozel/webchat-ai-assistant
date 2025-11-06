(function (global) {
  let webSocket = null;
  let config = {};
  let isPanelOpen = false;

  function createWidget() {
    // CSS'i dinamik olarak yükle (Eğer index.html'e eklenmediyse)
    if (!document.querySelector('link[href*="widget.css"]')) {
        const cssLink = document.createElement('link');
        cssLink.rel = 'stylesheet';
        cssLink.href = '/static/widget.css'; // CSS dosyanızın yolu
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
    
    // "yazıyor..." mesajını kaldır
    const typingMsg = document.getElementById('webchatai-typing');
    if (typingMsg) {
      typingMsg.remove();
    }

    // "yazıyor..." mesajı geldiyse ve tip 'user' değilse, göster
    if (type === 'assistant' && text === 'Asistan yazıyor...') {
      const msg = document.createElement('div');
      msg.className = 'webchatai-msg assistant typing'; // 'typing' sınıfı ekleyebiliriz
      msg.id = 'webchatai-typing';
      msg.textContent = text;
      body.appendChild(msg);
    } else {
      // Normal mesaj
      const msg = document.createElement('div');
      msg.className = 'webchatai-msg ' + type;
      msg.textContent = text;
      body.appendChild(msg);
    }
    body.scrollTop = body.scrollHeight;
  }

  function connectWebSocket() {
    // HTTP/HTTPS adresini WS/WSS adresine çevir
    const wsProtocol = config.apiBase.startsWith('https:') ? 'wss://' : 'ws://';
    // 'http://localhost:8000' -> 'ws://localhost:8000/ws?session_id=...'
    const wsUrl = `${wsProtocol}${config.apiBase.replace(/^https?:\/\//, '')}/ws?session_id=${config.sessionId}`;
    
    console.log('WebSocket bağlantısı kuruluyor:', wsUrl);
    
    webSocket = new WebSocket(wsUrl);

    webSocket.onopen = () => {
      console.log('WebSocket bağlantısı açıldı.');
      addMessage('system', 'Bağlantı kuruldu.');
    };

    webSocket.onmessage = (event) => {
      // Sunucudan gelen AI yanıtı
      const messageText = event.data;
      addMessage('assistant', messageText);
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
    
    // Mesajı WebSocket üzerinden sunucuya gönder
    webSocket.send(message);
    
    input.value = '';
  }

  function init(options = {}) {
    config.apiBase = options.apiBase || window.location.origin;
    config.sessionId = options.sessionId || 'session-' + Math.random().toString(36).substr(2, 9);

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', setup);
    } else {
      setup();
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
