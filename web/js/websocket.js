// WebSocket communication module

// WebSocket connection
let wsConnection = null;

// Connect WebSocket
function connectWebSocket() {
    if (wsConnection) {
        // Already connected
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
        document.getElementById('ws-send').disabled = false;
        
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
        document.getElementById('ws-send').disabled = true;
        
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
    if (!wsConnection || wsConnection.readyState !== WebSocket.OPEN) {
        document.getElementById('ws-output').innerHTML += '<div class="console-output error">WebSocket not connected</div>';
        return;
    }
    
    const message = document.getElementById('ws-message').value.trim();
    
    if (!message) {
        return;
    }
    
    // Create message object
    const messageObj = {
        type: 'text',
        text: message
    };
    
    // Send message
    wsConnection.send(JSON.stringify(messageObj));
    
    // Display sent message
    document.getElementById('ws-output').innerHTML += `<div class="console-output">Message sent: ${message}</div>`;
    
    // Clear input box
    document.getElementById('ws-message').value = '';
}