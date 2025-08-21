// API Client module - shared functions for both user and developer modes

// Global WebSocket connection
let wsConnection = null;

// Shared chat functions
function addMessageToChat(type, text, chatHistoryId = 'chat-history') {
    const chatHistory = document.getElementById(chatHistoryId);
    const messageId = 'msg-' + Date.now() + '-' + Math.random();
    
    const messageDiv = document.createElement('div');
    messageDiv.id = messageId;
    messageDiv.className = `chat-message ${type}`;
    
    const messageP = document.createElement('p');
    
    if (type === 'system') {
        messageP.innerHTML = text;
    } else {
        messageP.textContent = text;
    }
    
    messageDiv.appendChild(messageP);
    chatHistory.appendChild(messageDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    
    return messageId;
}

function updateChatMessage(messageId, text) {
    const messageElement = document.getElementById(messageId);
    if (messageElement) {
        messageElement.querySelector('p').textContent = text;
        const chatHistory = messageElement.parentElement;
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
}

// Service status check
async function checkServiceStatus(service) {
    const outputArea = document.getElementById('status-output');
    const serviceName = SERVICE_NAMES[service] || service;
    const statusIndicator = document.getElementById(`${service}-status`);
    
    if (outputArea) {
        outputArea.innerHTML += `<div>Checking ${serviceName} service status...</div>`;
    }
    
    try {
        const response = await fetch(API_URLS[service]);
        const data = await response.json();
        
        if (response.ok) {
            if (statusIndicator) {
                statusIndicator.className = 'status-indicator status-online';
            }
            if (outputArea) {
                outputArea.innerHTML += `<div class="console-output success">${serviceName} service: <span class="success">Online</span><br>Response: ${JSON.stringify(data)}</div>`;
            }
        } else {
            if (statusIndicator) {
                statusIndicator.className = 'status-indicator status-warning';
            }
            if (outputArea) {
                outputArea.innerHTML += `<div class="console-output error">${serviceName} service: <span class="error">Error</span><br>Response: ${JSON.stringify(data)}</div>`;
            }
        }
    } catch (error) {
        if (statusIndicator) {
            statusIndicator.className = 'status-indicator status-offline';
        }
        if (outputArea) {
            outputArea.innerHTML += `<div class="console-output error">${serviceName} service: <span class="error">Offline</span><br>Error: ${error.message}</div>`;
        }
    }
}

// Text-to-AI processing
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
                    if (cmd.type === 'scene') {
                        iotInfo += `- Scene: ${cmd.scene}<br>`;
                    } else {
                        iotInfo += `- ${cmd.device} (${cmd.location}): ${cmd.action}<br>`;
                    }
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

// Clear chat history
function clearChat() {
    document.getElementById('chat-history').innerHTML = '';
    const audioContainer = document.getElementById('audio-player-container');
    if (audioContainer) {
        audioContainer.style.display = 'none';
    }
    const audioPlayer = document.getElementById('audio-player');
    if (audioPlayer) {
        audioPlayer.src = '';
    }
}

// WebSocket functions
function connectWebSocket() {
    if (wsConnection) {
        return;
    }
    
    const wsUrl = `ws://${window.location.hostname}:8080/ws`;
    wsConnection = new WebSocket(wsUrl);
    
    const statusElement = document.getElementById('ws-status');
    statusElement.textContent = 'Connecting...';
    statusElement.className = 'ms-3 badge bg-warning';
    
    const outputArea = document.getElementById('ws-output');
    
    // Connection established
    wsConnection.onopen = function() {
        statusElement.textContent = 'Connected';
        statusElement.className = 'ms-3 badge bg-success';
        
        document.getElementById('ws-connect').disabled = true;
        document.getElementById('ws-disconnect').disabled = false;
        const sendButton = document.getElementById('ws-send');
        if (sendButton) {
            sendButton.disabled = false;
        }
        
        outputArea.innerHTML += '<div class="console-output success">WebSocket connection established</div>';
    };
    
    // Message received
    wsConnection.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            outputArea.innerHTML += `<div class="console-output">Message received:<br><pre>${JSON.stringify(data, null, 2)}</pre></div>`;
            
            // If there's an audio path, display audio player
            if (data.audio_path) {
                const audioServer = API_URLS.tts;
                const audioFilename = data.audio_path.split('/').pop();
                const audioUrl = `${audioServer}/audio/${audioFilename}`;
                
                const audioElement = document.createElement('audio');
                audioElement.controls = true;
                audioElement.src = audioUrl;
                audioElement.style.width = '100%';
                audioElement.style.marginTop = '10px';
                
                const audioContainer = document.createElement('div');
                audioContainer.className = 'console-output';
                audioContainer.innerHTML = '<strong>Audio response received:</strong><br>';
                audioContainer.appendChild(audioElement);
                
                outputArea.appendChild(audioContainer);
                
                // Auto play
                audioElement.play().catch(() => {});
            }
        } catch (e) {
            outputArea.innerHTML += `<div class="console-output">Message received: ${event.data}</div>`;
        }
        
        // Scroll to bottom
        outputArea.scrollTop = outputArea.scrollHeight;
    };
    
    // Connection closed
    wsConnection.onclose = function() {
        statusElement.textContent = 'Disconnected';
        statusElement.className = 'ms-3 badge bg-secondary';
        
        document.getElementById('ws-connect').disabled = false;
        document.getElementById('ws-disconnect').disabled = true;
        const sendButton = document.getElementById('ws-send');
        if (sendButton) {
            sendButton.disabled = true;
        }
        
        outputArea.innerHTML += '<div class="console-output">WebSocket connection closed</div>';
        wsConnection = null;
    };
    
    // Connection error
    wsConnection.onerror = function(error) {
        statusElement.textContent = 'Connection Error';
        statusElement.className = 'ms-3 badge bg-danger';
        
        outputArea.innerHTML += `<div class="console-output error">WebSocket error: ${error.message || 'Unknown error'}</div>`;
    };
}

// Disconnect WebSocket
function disconnectWebSocket() {
    if (wsConnection) {
        wsConnection.close();
        // onclose event will handle UI updates
    }
}

// Send WebSocket message
function sendWebSocketMessage() {
    if (!wsConnection) {
        const outputArea = document.getElementById('ws-output');
        if (outputArea) {
            outputArea.innerHTML += '<div class="console-output error">❌ WebSocket not connected</div>';
            outputArea.scrollTop = outputArea.scrollHeight;
        }
        return;
    }
    
    if (wsConnection.readyState !== WebSocket.OPEN) {
        const outputArea = document.getElementById('ws-output');
        if (outputArea) {
            outputArea.innerHTML += '<div class="console-output error">❌ WebSocket not ready</div>';
            outputArea.scrollTop = outputArea.scrollHeight;
        }
        return;
    }
    
    const messageInput = document.getElementById('ws-message');
    if (!messageInput) {
        console.error('Message input element not found');
        return;
    }
    
    const message = messageInput.value.trim();
    if (!message) {
        return;
    }
    
    try {
        // 创建安全的消息对象
        const messageObj = {
            type: 'text',
            text: message,
            timestamp: Date.now()
        };
        
        // 发送消息
        wsConnection.send(JSON.stringify(messageObj));
        
        // 显示发送的消息
        const outputArea = document.getElementById('ws-output');
        if (outputArea) {
            outputArea.innerHTML += `<div class="console-output">📤 Sent: ${message}</div>`;
            outputArea.scrollTop = outputArea.scrollHeight;
        }
        
        // 清空输入框
        messageInput.value = '';
        
    } catch (error) {
        console.error('Error sending WebSocket message:', error);
        const outputArea = document.getElementById('ws-output');
        if (outputArea) {
            outputArea.innerHTML += `<div class="console-output error">❌ Send error: ${error.message}</div>`;
            outputArea.scrollTop = outputArea.scrollHeight;
        }
    }
}

// Utility functions
function formatTimestamp() {
    return new Date().toISOString();
}

function showNotification(message, type = 'info') {
    // Simple notification system
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.top = '100px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

// Error handling wrapper
function handleApiError(error, context = '') {
    console.error(`API Error ${context}:`, error);
    const message = error.message || 'Unknown error occurred';
    showNotification(`Error ${context}: ${message}`, 'danger');
    return message;
}

// API request wrapper with error handling
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        throw new Error(`Request failed: ${error.message}`);
    }
}