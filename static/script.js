document.addEventListener('DOMContentLoaded', () => {
    const chatBox = document.getElementById('chat-box');
    const queryInput = document.getElementById('query-input');
    const sendBtn = document.getElementById('send-btn');
    const fileUpload = document.getElementById('file-upload');
    const uploadBtn = document.getElementById('upload-btn');

    function addMessage(content, sender) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Render content as HTML using marked if it's the system
        if (typeof marked !== 'undefined') {
            contentDiv.innerHTML = marked.parse(content);
        } else {
            contentDiv.textContent = content;
        }
        
        msgDiv.appendChild(contentDiv);
        chatBox.appendChild(msgDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
        return contentDiv;
    }

    async function handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        const uploadMsg = addMessage(`<div class="loading-text"><div class="spinner"></div>Uploading ${file.name}...</div>`, 'system');
        uploadBtn.disabled = true;

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                uploadMsg.innerHTML = marked.parse(`✅ Success: ${data.message}`);
            } else {
                const errorData = await response.json();
                uploadMsg.innerHTML = marked.parse(`❌ Error: ${errorData.detail || 'Upload failed'}`);
            }
        } catch (error) {
            uploadMsg.innerHTML = marked.parse('❌ Error: Connection failed during upload.');
        } finally {
            uploadBtn.disabled = false;
            fileUpload.value = ''; // Reset input
        }
    }

    uploadBtn.addEventListener('click', () => fileUpload.click());
    fileUpload.addEventListener('change', handleFileUpload);

    async function sendMessage() {
        const query = queryInput.value.trim();
        if (!query) return;

        addMessage(query, 'user');
        queryInput.value = '';
        sendBtn.disabled = true;

        const responseContent = addMessage('<div class="loading-text"><div class="spinner"></div>Thinking...</div>', 'system');

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query })
            });

            if (!response.ok) {
                responseContent.innerHTML = '❌ Error: Failed to fetch response.';
                sendBtn.disabled = false;
                return;
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let fullText = '';
            // responseContent.innerHTML = ''; // Removed to wait for first chunk

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value, { stream: true });
                
                // Clear the spinner on the first incoming chunk
                if (fullText === '') responseContent.innerHTML = '';
                
                fullText += chunk;
                responseContent.innerHTML = marked.parse(fullText);
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