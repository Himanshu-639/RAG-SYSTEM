document.addEventListener('DOMContentLoaded', () => {
    const chatBox = document.getElementById('chat-box');
    const queryInput = document.getElementById('query-input');
    const sendBtn = document.getElementById('send-btn');

    function addMessage(content, sender) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        msgDiv.appendChild(contentDiv);
        chatBox.appendChild(msgDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
        return contentDiv;
    }

    async function sendMessage() {
        const query = queryInput.value.trim();
        if (!query) return;

        addMessage(query, 'user');
        queryInput.value = '';
        sendBtn.disabled = true;

        const responseContent = addMessage('...', 'system');

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query })
            });

            if (!response.ok) {
                responseContent.textContent = 'Error: Failed to fetch response.';
                sendBtn.disabled = false;
                return;
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            responseContent.textContent = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value, { stream: true });
                responseContent.textContent += chunk;
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        } catch (error) {
            responseContent.textContent = 'Error: Connection failed.';
        } finally {
            sendBtn.disabled = false;
            queryInput.focus();
        }
    }

    sendBtn.addEventListener('click', sendMessage);
    queryInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
});