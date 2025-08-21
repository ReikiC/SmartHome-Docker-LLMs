// Ollama model management module

// Check available Ollama models
async function checkOllamaModels() {
    const outputArea = document.getElementById('models-output');
    outputArea.innerHTML = 'Getting model list...';
    
    try {
        const response = await fetch(`${API_URLS.ollama}/api/tags`);
        const data = await response.json();
        
        if (response.ok) {
            let output = '<div class="console-output"><strong>Available Models:</strong><br>';
            
            if (data.models && data.models.length > 0) {
                data.models.forEach((model, index) => {
                    output += `${index + 1}. <span class="success">${model.name}</span>`;
                    if (model.size) {
                        const sizeMB = (model.size / (1024 * 1024)).toFixed(2);
                        output += ` (${sizeMB} MB)`;
                    }
                    output += '<br>';
                });
            } else {
                output += '<span class="error">No models found</span><br>';
            }
            
            output += '</div>';
            outputArea.innerHTML = output;
        } else {
            outputArea.innerHTML = `<div class="console-output error">Failed to get models: ${data.error || 'Unknown error'}</div>`;
        }
    } catch (error) {
        outputArea.innerHTML = `<div class="console-output error">Request error: ${error.message}</div>`;
    }
}

// Pull Ollama model
async function pullOllamaModel() {
    const modelName = document.getElementById('model-name').value.trim();
    const outputArea = document.getElementById('models-output');
    
    if (!modelName) {
        outputArea.innerHTML = '<div class="console-output error">Please enter a model name</div>';
        return;
    }
    
    outputArea.innerHTML = `<div class="console-output">Pulling model <strong>${modelName}</strong>...<br>This may take several minutes, please be patient...</div>`;
    
    try {
        const response = await fetch(`${API_URLS.ollama}/api/pull`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name: modelName })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            outputArea.innerHTML = `<div class="console-output success">Model <strong>${modelName}</strong> has been successfully pulled!</div>`;
            // Refresh model list
            setTimeout(checkOllamaModels, 1000);
        } else {
            outputArea.innerHTML = `<div class="console-output error">Failed to pull model: ${data.error || 'Unknown error'}</div>`;
        }
    } catch (error) {
        outputArea.innerHTML = `<div class="console-output error">Request error: ${error.message}</div>`;
    }
}