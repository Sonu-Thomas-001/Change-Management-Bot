document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatBox = document.getElementById('chat-box');
    const micBtn = document.getElementById('mic-btn');
    const clearBtn = document.getElementById('clear-btn');
    const exportPdfBtn = document.getElementById('export-pdf-btn');

    // --- Clear Chat ---
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            if (confirm("Are you sure you want to delete all chat history?")) {
                localStorage.removeItem('chatHistory');
                location.reload();
            }
        });
    }

    // --- PDF Export ---
    if (exportPdfBtn) {
        exportPdfBtn.addEventListener('click', () => {
            const element = document.getElementById('chat-box');
            const opt = {
                margin: 10,
                filename: 'ChangeAssistant_ChatHistory.pdf',
                image: { type: 'jpeg', quality: 0.98 },
                html2canvas: { scale: 2, logging: true },
                jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
            };
            html2pdf().set(opt).from(element).save();
        });
    }

    // --- Load History ---
    let chatHistory = [];
    try { chatHistory = JSON.parse(localStorage.getItem('chatHistory')) || []; } catch (e) { chatHistory = []; }

    if (chatHistory.length > 0) {
        chatBox.innerHTML = '';
        chatHistory.forEach(msg => {
            if (msg.type === 'chart') {
                addMessage(msg.content.text, 'bot', false, false);
                // Pass the chart type from history
                addChartMessage(msg.content.chart_data, msg.content.chart_type);
            } else {
                const sender = msg.type === 'human' ? 'user' : 'bot';
                const isHTML = msg.isHTML || false;
                addMessage(msg.content, sender, false, false, isHTML);
            }
        });
    } else {
        chatBox.innerHTML = `
            <div class="message-wrapper bot">
                <div class="chat-message bot">
                    <div class="message-content"><p>Hello! I'm your Change Assistant. How can I help you navigate the transition today?</p></div>
                </div>
            </div>`;
    }

    function saveToLocalStorage() {
        localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
    }

    // --- Voice ---
    try {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;

            micBtn.addEventListener('click', () => {
                if (micBtn.classList.contains('recording')) recognition.stop();
                else recognition.start();
            });
            recognition.onstart = () => micBtn.classList.add('recording');
            recognition.onend = () => micBtn.classList.remove('recording');
            recognition.onresult = (e) => { userInput.value = e.results[0][0].transcript; userInput.focus(); };
        } else { if (micBtn) micBtn.style.display = 'none'; }
    } catch (e) { console.error(e); }

    // --- Chat Submission ---
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = userInput.value.trim();
        if (!message) return;

        addMessage(message, 'user', false, true);
        userInput.value = '';

        // Use HTML Dots for Loading
        const loadingHTML = '<div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>';
        const loadingWrapper = addMessage(loadingHTML, 'bot', true, false);

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: message, chat_history: chatHistory })
            });

            const data = await response.json();

            if (data.error) throw new Error(data.error);

            loadingWrapper.remove();

            // --- HANDLE CHART RESPONSE ---
            if (data.type === 'chart') {
                addMessage(data.text, 'bot', false, false);
                addChartMessage(data.chart_data, data.chart_type);

                chatHistory.push({ type: 'chart', content: data });
            } else {
                // Normal Text Response
                const finalWrapper = addMessage(data.answer, 'bot', false, false, data.disable_copy);

                if (!data.disable_copy) {
                    addCopyButton(finalWrapper.querySelector('.chat-message'), data.answer);
                }

                addFeedbackButtons(finalWrapper, data.answer);

                // Check for low confidence
                if (data.low_confidence) {
                    addEscalationButton(finalWrapper, data.answer, "Low Confidence Bot Response");
                }

                chatHistory.push({ type: 'ai', content: data.answer, isHTML: data.disable_copy });
            }
            saveToLocalStorage();
        } catch (error) {
            loadingWrapper.querySelector('.message-content').innerHTML = `<span style="color:red;">⚠️ Error: ${error.message}</span>`;
        }
    });

    // --- Helper: Render Messages ---
    function addMessage(text, sender, isLoading = false, save = true, isHTML = false) {
        if (save && sender === 'user') {
            chatHistory.push({ type: 'human', content: text });
            saveToLocalStorage();
        }

        const wrapper = document.createElement('div');
        wrapper.classList.add('message-wrapper', sender);

        const bubble = document.createElement('div');
        bubble.classList.add('chat-message', sender);

        const contentDiv = document.createElement('div');
        contentDiv.classList.add('message-content');

        if (sender === 'user') contentDiv.textContent = text;
        else contentDiv.innerHTML = isLoading ? text : (isHTML ? text : marked.parse(text));

        bubble.appendChild(contentDiv);

        if (sender === 'user') {
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'message-actions';
            const editBtn = document.createElement('button');
            editBtn.className = 'action-btn';
            editBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>`;
            editBtn.onclick = () => { userInput.value = text; userInput.focus(); };
            actionsDiv.appendChild(editBtn);
            bubble.appendChild(actionsDiv);
        }

        if (sender === 'bot' && !isLoading) {
            addCopyButton(bubble, text);
        }

        wrapper.appendChild(bubble);

        if (sender === 'bot' && !isLoading) {
            addFeedbackButtons(wrapper, text);
        }

        chatBox.appendChild(wrapper);
        chatBox.scrollTop = chatBox.scrollHeight;
        return wrapper;
    }

    // --- Helper: Render Dynamic Charts ---
    function addChartMessage(chartData, chartType = 'bar') {
        const wrapper = document.createElement('div');
        wrapper.classList.add('message-wrapper', 'bot');

        const bubble = document.createElement('div');
        bubble.classList.add('chat-message', 'bot');
        bubble.style.width = '100%';

        const canvasContainer = document.createElement('div');
        canvasContainer.style.position = 'relative';
        canvasContainer.style.height = '300px';
        canvasContainer.style.width = '100%';

        const canvas = document.createElement('canvas');
        canvasContainer.appendChild(canvas);
        bubble.appendChild(canvasContainer);
        wrapper.appendChild(bubble);

        chatBox.appendChild(wrapper);
        chatBox.scrollTop = chatBox.scrollHeight;

        // Configure Chart Options based on Type
        const showScales = chartType === 'bar';

        new Chart(canvas, {
            type: chartType,
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true, display: showScales },
                    x: { display: showScales }
                },
                plugins: {
                    // Show legend only for Pie/Doughnut
                    legend: { display: !showScales }
                }
            }
        });
    }

    function addCopyButton(bubbleDiv, rawText) {
        let actionsDiv = bubbleDiv.querySelector('.message-actions');
        if (!actionsDiv) {
            actionsDiv = document.createElement('div');
            actionsDiv.className = 'message-actions';
            bubbleDiv.appendChild(actionsDiv);
        }
        if (actionsDiv.querySelector('.copy-btn')) return;

        const copyBtn = document.createElement('button');
        copyBtn.className = 'action-btn copy-btn';
        copyBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>`;

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

    function addFeedbackButtons(wrapperDiv, content) {
        if (wrapperDiv.querySelector('.feedback-actions')) return;
        const fbDiv = document.createElement('div');
        fbDiv.className = 'feedback-actions';

        const upBtn = document.createElement('button');
        upBtn.className = 'feedback-btn';
        upBtn.innerHTML = '👍';
        upBtn.onclick = () => sendFeedback('thumbs_up', content, upBtn);

        const downBtn = document.createElement('button');
        downBtn.className = 'feedback-btn';
        downBtn.innerHTML = '👎';
        downBtn.onclick = () => sendFeedback('thumbs_down', content, downBtn);

        fbDiv.appendChild(upBtn);
        fbDiv.appendChild(downBtn);
        wrapperDiv.appendChild(fbDiv);
    }

    async function sendFeedback(type, content, btnElement) {
        const parent = btnElement.parentElement;
        Array.from(parent.children).forEach(b => b.disabled = true);
        btnElement.classList.add('active');
        try {
            await fetch('/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type: type, content: content })
            });

            // If Thumbs Down, offer escalation
            if (type === 'thumbs_down') {
                addEscalationButton(parent.parentElement, content, "User Feedback (Thumbs Down)");
            }

        } catch (e) { console.error(e); }
    }

    function addEscalationButton(wrapperDiv, content, reason) {
        if (wrapperDiv.querySelector('.escalation-actions')) return;

        const escDiv = document.createElement('div');
        escDiv.className = 'escalation-actions';
        escDiv.style.marginTop = '10px';

        const escBtn = document.createElement('button');
        escBtn.className = 'action-btn';
        escBtn.style.backgroundColor = '#dc3545'; // Red color
        escBtn.style.color = 'white';
        escBtn.style.border = 'none';
        escBtn.style.padding = '5px 10px';
        escBtn.style.borderRadius = '4px';
        escBtn.style.cursor = 'pointer';
        escBtn.innerHTML = '⚠️ Escalate to Change Manager';

        escBtn.onclick = () => escalateChat(escBtn, reason);

        escDiv.appendChild(escBtn);
        wrapperDiv.appendChild(escDiv);
    }

    async function escalateChat(btnElement, reason) {
        const originalText = btnElement.innerHTML;
        btnElement.innerHTML = 'Sending...';
        btnElement.disabled = true;

        try {
            const response = await fetch('/escalate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ chat_history: chatHistory, reason: reason })
            });
            const data = await response.json();

            if (data.status === 'success') {
                btnElement.innerHTML = '✅ Request sent to Change Manager';
                btnElement.style.backgroundColor = '#28a745'; // Green
            } else {
                btnElement.innerHTML = '❌ Failed. Try again.';
                btnElement.disabled = false;
            }
        } catch (e) {
            console.error(e);
            btnElement.innerHTML = '❌ Error. Try again.';
            btnElement.disabled = false;
        }
    }
});