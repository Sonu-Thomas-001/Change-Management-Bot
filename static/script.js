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

        recognition.onstart = () => {
            micBtn.classList.add('recording');
        };

        recognition.onend = () => {
            micBtn.classList.remove('recording');
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            userInput.value = transcript;
            // Optional: Auto-submit after speaking
            // chatForm.dispatchEvent(new Event('submit')); 
        };
    } else {
        micBtn.style.display = 'none'; // Hide if browser doesn't support
        console.log("Web Speech API not supported in this browser.");
    }

    // --- 2. Clear Chat ---
    clearBtn.addEventListener('click', () => {
        if(confirm("Clear conversation history?")) {
            chatBox.innerHTML = `
                <div class="chat-message bot">
                    <p>Chat cleared. How can I help you now?</p>
                </div>
            `;
            chatHistory = [];
        }
    });

    // --- 3. Chat Logic ---
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = userInput.value.trim();
        if (!message) return;

        addMessage(message, 'user');
        chatHistory.push({ type: 'human', content: message });
        userInput.value = '';

        const loadingDiv = addMessage('Thinking...', 'bot');
        
        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: message, chat_history: chatHistory.slice(0, -1) })
            });
            
            const data = await response.json();
            
            // Render Markdown
            const formattedAnswer = marked.parse(data.answer || "Error occurred.");
            loadingDiv.innerHTML = formattedAnswer;
            
            // Append Feedback Buttons to this bot message
            addFeedbackButtons(loadingDiv, data.answer);

            chatHistory.push({ type: 'ai', content: data.answer });
            
        } catch (error) {
            loadingDiv.textContent = "Sorry, I'm having trouble connecting.";
        }
    });

    function addMessage(text, sender) {
        const div = document.createElement('div');
        div.classList.add('chat-message', sender);
        div.innerHTML = text; 
        chatBox.appendChild(div);
        chatBox.scrollTop = chatBox.scrollHeight;
        return div;
    }

    // --- 4. Feedback Mechanism ---
    function addFeedbackButtons(messageDiv, content) {
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'feedback-actions';
        
        const upBtn = document.createElement('button');
        upBtn.className = 'feedback-btn';
        upBtn.innerHTML = '👍';
        upBtn.onclick = () => sendFeedback('thumbs_up', content, upBtn);

        const downBtn = document.createElement('button');
        downBtn.className = 'feedback-btn';
        downBtn.innerHTML = '👎';
        downBtn.onclick = () => sendFeedback('thumbs_down', content, downBtn);

        actionsDiv.appendChild(upBtn);
        actionsDiv.appendChild(downBtn);
        messageDiv.appendChild(actionsDiv);
    }

    async function sendFeedback(type, content, btnElement) {
        // Visual feedback
        const parent = btnElement.parentElement;
        Array.from(parent.children).forEach(b => b.disabled = true); // Disable buttons
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