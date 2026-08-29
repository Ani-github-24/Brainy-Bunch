(function() {
    window.addEventListener('DOMContentLoaded', () => {
        const recordingSection = document.getElementById('recording-section');
        if (!recordingSection) return;

        const chatContainer = document.createElement('div');
        chatContainer.style.marginTop = '20px';
        chatContainer.style.padding = '20px';
        chatContainer.style.border = '1px solid var(--border-color)';
        chatContainer.style.borderRadius = '12px';
        chatContainer.style.background = 'var(--surface-color)';
        chatContainer.innerHTML = `
            <h3>AI Assistant</h3>
            <div id="ai-chat-history" style="max-height: 200px; overflow-y: auto; margin-bottom: 10px;"></div>
            <div class="form-group" style="display: flex; gap: 10px;">
                <input type="text" id="ai-chat-input" placeholder="Ask AI a question about the lecture..." style="flex-grow: 1;">
                <button id="ai-chat-submit" style="padding: 10px 20px;">Ask</button>
            </div>
        `;
        recordingSection.appendChild(chatContainer);

        const chatInput = document.getElementById('ai-chat-input');
        const chatSubmit = document.getElementById('ai-chat-submit');
        const chatHistory = document.getElementById('ai-chat-history');

        chatSubmit.addEventListener('click', async () => {
            const question = chatInput.value.trim();
            if (!question) return;
            if (typeof activeSessionId === 'undefined' || !activeSessionId) {
                alert('Session not active yet.');
                return;
            }

            chatInput.disabled = true;
            chatSubmit.disabled = true;
            
            const userMsg = document.createElement('div');
            userMsg.style.marginBottom = '10px';
            userMsg.innerHTML = `<strong>You:</strong> ${question}`;
            chatHistory.appendChild(userMsg);
            
            try {
                const res = await fetch(`/sessions/${activeSessionId}/chat`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ question })
                });
                if (res.ok) {
                    const data = await res.json();
                    
                    const aiMsg = document.createElement('div');
                    aiMsg.style.marginBottom = '15px';
                    aiMsg.style.padding = '10px';
                    aiMsg.style.background = 'rgba(99, 102, 241, 0.1)';
                    aiMsg.style.borderRadius = '8px';
                    aiMsg.innerHTML = `
                        <strong>AI:</strong> ${data.answer}
                        <div style="margin-top: 10px; display: flex; gap: 10px;">
                            <button class="btn-understood" style="background: var(--bg-color); border: 1px solid var(--border-color); color: white; padding: 5px 10px; border-radius: 5px; cursor: pointer;">Understood</button>
                            <button class="btn-ask-teacher" style="background: var(--primary-color); border: none; color: white; padding: 5px 10px; border-radius: 5px; cursor: pointer;">Ask Teacher</button>
                        </div>
                    `;
                    chatHistory.appendChild(aiMsg);
                    chatHistory.scrollTop = chatHistory.scrollHeight;

                    const btnUnderstood = aiMsg.querySelector('.btn-understood');
                    const btnAskTeacher = aiMsg.querySelector('.btn-ask-teacher');

                    btnUnderstood.addEventListener('click', () => {
                        aiMsg.style.opacity = '0.5';
                        btnUnderstood.disabled = true;
                        btnAskTeacher.disabled = true;
                    });

                    btnAskTeacher.addEventListener('click', async () => {
                        btnUnderstood.disabled = true;
                        btnAskTeacher.disabled = true;
                        btnAskTeacher.textContent = 'Flagging...';
                        try {
                            const flagRes = await fetch(`/sessions/${activeSessionId}/flag-question`, {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({ question_text: question })
                            });
                            if (flagRes.ok) {
                                btnAskTeacher.textContent = 'Flagged!';
                                btnAskTeacher.style.background = '#10b981';
                            } else {
                                btnAskTeacher.textContent = 'Failed';
                            }
                        } catch (e) {
                            btnAskTeacher.textContent = 'Error';
                        }
                    });
                }
            } catch (e) {
                console.error("AI chat failed", e);
                const errMsg = document.createElement('div');
                errMsg.style.color = 'red';
                errMsg.textContent = 'Error contacting AI.';
                chatHistory.appendChild(errMsg);
            } finally {
                chatInput.value = '';
                chatInput.disabled = false;
                chatSubmit.disabled = false;
                chatInput.focus();
            }
        });

        // Add Enter key listener
        chatInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                chatSubmit.click();
            }
        });
    });
})();
