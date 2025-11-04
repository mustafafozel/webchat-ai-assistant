(function (global) {
  function createWidget() {
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
    const msg = document.createElement('div');
    msg.className = 'webchatai-msg ' + type;
    msg.textContent = text;
    body.appendChild(msg);
    body.scrollTop = body.scrollHeight;
  }

  async function sendMessage(apiBase, sessionId, message) {
    try {
      const response = await fetch(apiBase + '/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, session_id: sessionId })
      });
      const data = await response.json();
      return data.response || 'Yanıt alınamadı';
    } catch (error) {
      console.error('Error:', error);
      return 'Bir hata oluştu';
    }
  }

  function init(options = {}) {
    const apiBase = options.apiBase || window.location.origin;
    const sessionId = options.sessionId || 'session-' + Math.random().toString(36).substr(2, 9);

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', createWidget);
    } else {
      createWidget();
    }

    setTimeout(() => {
      const toggle = document.getElementById('webchatai-toggle');
      const panel = document.getElementById('webchatai-panel');
      const closeBtn = document.getElementById('webchatai-close');
      const input = document.getElementById('webchatai-input');
      const sendBtn = document.getElementById('webchatai-send');

      if (!toggle || !panel) return;

      toggle.addEventListener('click', () => {
        panel.style.display = panel.style.display === 'flex' ? 'none' : 'flex';
      });

      if (closeBtn) closeBtn.addEventListener('click', () => {
        panel.style.display = 'none';
      });

      async function handleSend() {
        const message = input.value.trim();
        if (!message) return;
        
        addMessage('user', message);
        input.value = '';
        
        const response = await sendMessage(apiBase, sessionId, message);
        addMessage('assistant', response);
      }

      if (sendBtn) sendBtn.addEventListener('click', handleSend);
      if (input) input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') handleSend();
      });
    }, 100);
  }

  global.WebChatAI = { init };
})(window);
