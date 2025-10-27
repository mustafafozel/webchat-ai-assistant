(function() {
    // Widget container oluştur
    const widgetContainer = document.createElement('div');
    widgetContainer.id = 'webchat-widget';
    widgetContainer.innerHTML = `
        <div id="chat-header">AI Asistan</div>
        <div id="chat-messages"></div>
        <div id="typing-indicator" style="display:none;">Yazıyor...</div>
        <div id="chat-input-container">
            <input type="text" id="chat-input" placeholder="Mesajınızı yazın...">
            <button id="send-btn">Gönder</button>
        </div>
    `;
    document.body.appendChild(widgetContainer);

    // CSS ekle
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = '/static/widget.css';
    document.head.appendChild(link);

    // WebSocket bağlantısı
    const sessionId = 'session_' + Math.random().toString(36).substr(2, 9);
    const ws = new WebSocket(`ws://localhost:8000/ws?session_id=${sessionId}`);

    const messagesDiv = document.getElementById('chat-messages');
    const inputField = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const typingIndicator = document.getElementById('typing-indicator');

    ws.onopen = function() {
        console.log('WebSocket bağlantısı kuruldu');
    };

    ws.onmessage = function(event) {
        typingIndicator.style.display = 'none';
        addMessage('assistant', event.data);
    };

    ws.onerror = function(error) {
        alert('Bağlantı hatası: ' + error.message);
    };

    ws.onclose = function() {
        alert('Bağlantı koptu. Lütfen sayfayı yenileyin.');
    };

    function sendMessage() {
        const message = inputField.value.trim();
        if (message && ws.readyState === WebSocket.OPEN) {
            addMessage('user', message);
            ws.send(message);
            inputField.value = '';
            typingIndicator.style.display = 'block';
        }
    }

    function addMessage(sender, content) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;
        msgDiv.textContent = content;
        messagesDiv.appendChild(msgDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    sendBtn.onclick = sendMessage;
    inputField.onkeypress = function(e) {
        if (e.key === 'Enter') sendMessage();
    };
})();
