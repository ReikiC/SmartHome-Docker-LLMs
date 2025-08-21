// AI chat interaction module

// Send text to AI
async function sendTextToAI() {
    const userInput = document.getElementById('user-input').value.trim();
    const chatHistory = document.getElementById('chat-history');
    
    if (!userInput) return;
    
    // Add user message to chat history
    addMessageToChat('user', userInput);
    
    // Clear input box
    document.getElementById('user-input').value = '';
    
    // Add AI thinking message
    const thinkingId = addMessageToChat('ai', 'Thinking...');
    
    try {
        const response = await fetch(`${API_URLS.coordinator}/process_text`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text: userInput })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Replace thinking message
            updateChatMessage(thinkingId, data.ai_response);
            
            // Show IoT command information (if any)
            if (data.iot_commands && data.iot_commands.length > 0) {
                let iotInfo = 'Sent the following IoT commands:<br>';
                data.iot_commands.forEach(cmd => {
                    iotInfo += `- ${cmd.device} (${cmd.location}): ${cmd.action}<br>`;
                });
                addMessageToChat('system', iotInfo);
            }
            
            // Show expression information
            if (data.expression) {
                addMessageToChat('system', `Expression: ${data.expression}`);
            }
            
            // Handle audio playback
            if (data.audio_path) {
                // Create complete audio URL
                const audioServer = API_URLS.tts;
                const audioFilename = data.audio_path.split('/').pop();
                const audioUrl = `${audioServer}/audio/${audioFilename}`;
                
                // Set audio player
                const audioPlayer = document.getElementById('audio-player');
                audioPlayer.src = audioUrl;
                document.getElementById('audio-player-container').style.display = 'block';
                
                // Auto play
                audioPlayer.play().catch(err => {
                    console.error('Auto-play failed:', err);
                    addMessageToChat('system', 'Note: Due to browser policy, you need to manually click the play button to play audio.');
                });
            }
        } else {
            updateChatMessage(thinkingId, `Processing failed: ${data.error || 'Unknown error'}`);
        }
    } catch (error) {
        updateChatMessage(thinkingId, `Request error: ${error.message}`);
    }
}

// Add message to chat history
function addMessageToChat(type, text) {
    const chatHistory = document.getElementById('chat-history');
    const messageId = 'msg-' + Date.now();
    
    const messageDiv = document.createElement('div');
    messageDiv.id = messageId;
    messageDiv.className = `chat-message ${type}`;
    
    const messageP = document.createElement('p');
    
    // System messages can contain HTML
    if (type === 'system') {
        messageP.innerHTML = text;
    } else {
        messageP.textContent = text;
    }
    
    messageDiv.appendChild(messageP);
    chatHistory.appendChild(messageDiv);
    
    // Scroll to bottom
    chatHistory.scrollTop = chatHistory.scrollHeight;
    
    return messageId;
}

// Update chat message
function updateChatMessage(messageId, text) {
    const messageElement = document.getElementById(messageId);
    if (messageElement) {
        messageElement.querySelector('p').textContent = text;
        
        // Scroll to bottom
        const chatHistory = document.getElementById('chat-history');
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
}

// Clear chat history
function clearChat() {
    document.getElementById('chat-history').innerHTML = '';
    document.getElementById('audio-player-container').style.display = 'none';
    document.getElementById('audio-player').src = '';
}