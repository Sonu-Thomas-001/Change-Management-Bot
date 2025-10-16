document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatBox = document.getElementById('chat-box');

    // Array to store the chat history
    let chatHistory = [];

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const userMessage = userInput.value.trim();
        if (userMessage === '') return;

        // Display user's message and add to history
        addMessage(userMessage, 'user');
        chatHistory.push({ type: 'human', content: userMessage });
        userInput.value = '';

        // Show loading indicator
        const loadingIndicator = addMessage('', 'loading');

        try {
            // Send message AND history to the backend
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question: userMessage,
                    chat_history: chatHistory.slice(0, -1) // Send history *before* the current question
                }),
            });

            // Remove loading indicator
            chatBox.removeChild(loadingIndicator);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Network response was not ok');
            }

            const data = await response.json();
            
            // Display bot's message and add to history
            addMessage(data.answer, 'bot');
            chatHistory.push({ type: 'ai', content: data.answer });

        } catch (error) {
            console.error('Error:', error);
            addMessage(`Sorry, something went wrong: ${error.message}`, 'bot');
        }
    });

    function addMessage(message, type) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-message', type);

        if (type === 'loading') {
            messageElement.innerHTML = '<span></span><span></span><span></span>';
        } else {
            const p = document.createElement('p');
            // Convert markdown to HTML before displaying
            p.innerHTML = marked.parse(message);
            messageElement.appendChild(p);
        }

        chatBox.appendChild(messageElement);
        // Scroll to the bottom
        chatBox.scrollTop = chatBox.scrollHeight;
        return messageElement;
    }
});