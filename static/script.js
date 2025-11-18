document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatBox = document.getElementById('chat-box');
    const micBtn = document.getElementById('mic-btn');
    const clearBtn = document.getElementById('clear-btn');
    
    let chatHistory = [];

    // --- 1. Voice Interaction (Speech to Text) ---
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;

        micBtn.addEventListener('click', () => {
            if (micBtn.classList.contains('recording')) {
                recognition.stop();
            } else {
                recognition.start();
            }
        });

        recognition.onstart = () => { micBtn.classList.add('recording'); };
        recognition.onend = () => { micBtn.classList.remove('recording'); };
        
        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            userInput.value = transcript;
            userInput.focus();
        };
    } else {
        micBtn.style.display = 'none';
        console.log("Web Speech API not supported.");
    }

    // --- 2. Clear Chat ---
    clearBtn.addEventListener('click', () => {
        if(confirm("Clear conversation history?")) {
            chatBox.innerHTML = `
                <div class="chat-message bot">
                    <div class="message-content"><p>Chat cleared. How can I help you now?</p></div>
                </div>
            `;
            chatHistory = [];
        }
    });

    // --- 3. Chat Submission Logic ---
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = userInput.value.trim();
        if (!message) return;

        // Add User Message
        addMessage(message, 'user');
        chatHistory.push({ type: 'human', content: message });
        userInput.value = '';

        // Add Loading Spinner
        const loadingDiv = addMessage('Thinking...', 'bot', true); // true = is loading
        
        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: message, chat_history: chatHistory.slice(0, -1) })
            });
            
            const data = await response.json();
            
            // Render Markdown in the content div
            const contentDiv = loadingDiv.querySelector('.message-content');
            contentDiv.innerHTML = marked.parse(data.answer || "Error occurred.");
            
            // Add Action Buttons to final response
            addCopyButton(loadingDiv, data.answer);
            addFeedbackButtons(loadingDiv, data.answer);

            chatHistory.push({ type: 'ai', content: data.answer });
            
        } catch (error) {
            const contentDiv = loadingDiv.querySelector('.message-content');
            contentDiv.textContent = "Sorry, I'm having trouble connecting.";
        }
    });

    // --- 4. Message Rendering Helper ---
    function addMessage(text, sender, isLoading = false) {
        const div = document.createElement('div');
        div.classList.add('chat-message', sender);
        
        // Wrapper for text content
        const contentDiv = document.createElement('div');
        contentDiv.classList.add('message-content');
        
        if (sender === 'user') {
            contentDiv.textContent = text;
        } else {
            // For bot, if loading show text, else parse markdown later
            contentDiv.innerHTML = isLoading ? text : marked.parse(text);
        }
        div.appendChild(contentDiv);

        // Wrapper for Action Buttons (Copy/Edit)
        const actionsDiv = document.createElement('div');
        actionsDiv.classList.add('message-actions');

        // -> EDIT Button (User only)
        if (sender === 'user') {
            const editBtn = document.createElement('button');
            editBtn.className = 'action-btn';
            editBtn.title = "Edit query";
            editBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>`;
            
            editBtn.onclick = () => {
                userInput.value = text; // Load text back to input
                userInput.focus();
            };
            actionsDiv.appendChild(editBtn);
        }

        // -> COPY Button (Bot only - for static messages like welcome)
        if (sender === 'bot' && !isLoading) {
             addCopyButton(div, text);
        }

        div.appendChild(actionsDiv);
        chatBox.appendChild(div);
        chatBox.scrollTop = chatBox.scrollHeight;
        
        return div; 
    }

    // --- 5. Copy Button Logic ---
    function addCopyButton(messageDiv, rawText) {
        // Find or create actions div
        let actionsDiv = messageDiv.querySelector('.message-actions');
        if (!actionsDiv) {
            actionsDiv = document.createElement('div');
            actionsDiv.className = 'message-actions';
            messageDiv.appendChild(actionsDiv);
        }

        const copyBtn = document.createElement('button');
        copyBtn.className = 'action-btn';
        copyBtn.title = "Copy response";
        copyBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>`;
        
        // "Copied!" Tooltip
        const feedbackSpan = document.createElement('span');
        feedbackSpan.className = 'copy-feedback';
        feedbackSpan.textContent = "Copied!";
        actionsDiv.appendChild(feedbackSpan);

        copyBtn.onclick = () => {
            navigator.clipboard.writeText(rawText).then(() => {
                feedbackSpan.classList.add('show');
                setTimeout(() => feedbackSpan.classList.remove('show'), 2000);
            });
        };

        actionsDiv.appendChild(copyBtn);
    }

    // --- 6. Feedback Buttons Logic ---
    function addFeedbackButtons(messageDiv, content) {
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'feedback-actions';
        
        const upBtn = document.createElement('button');
        upBtn.className = 'feedback-btn';
        upBtn.innerHTML = '👍';
        upBtn.title = "Helpful";
        upBtn.onclick = () => sendFeedback('thumbs_up', content, upBtn);

        const downBtn = document.createElement('button');
        downBtn.className = 'feedback-btn';
        downBtn.innerHTML = '👎';
        downBtn.title = "Not Helpful";
        downBtn.onclick = () => sendFeedback('thumbs_down', content, downBtn);

        actionsDiv.appendChild(upBtn);
        actionsDiv.appendChild(downBtn);
        messageDiv.appendChild(actionsDiv);
    }

    async function sendFeedback(type, content, btnElement) {
        const parent = btnElement.parentElement;
        // Disable buttons after voting
        Array.from(parent.children).forEach(b => b.disabled = true);
        btnElement.classList.add('active');

        try {
            await fetch('/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type: type, content: content })
            });
        } catch (e) {
            console.error("Feedback failed", e);
        }
    }
});