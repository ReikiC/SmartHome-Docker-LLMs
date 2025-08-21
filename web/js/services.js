// Service status check module - Fixed version

// Check service status with improved error handling
async function checkServiceStatus(service) {
    const outputArea = document.getElementById('status-output');
    const serviceName = SERVICE_NAMES[service] || service;
    const statusIndicator = document.getElementById(`${service}-status`);
    
    if (outputArea) {
        const currentContent = outputArea.innerHTML;
        outputArea.innerHTML = `${currentContent}<div>Checking ${serviceName} service status...</div>`;
    }
    
    try {
        console.log(`Checking ${service} at: ${API_URLS[service]}`);
        
        const response = await fetch(API_URLS[service], {
            method: 'GET',
            headers: {
                'Accept': 'application/json, text/plain, */*'
            }
        });
        
        let data;
        let responseText = '';
        
        // Get response text first
        responseText = await response.text();
        console.log(`${service} response text:`, responseText);
        
        // Try to parse as JSON, fallback to text
        try {
            data = JSON.parse(responseText);
            console.log(`${service} parsed JSON:`, data);
        } catch (jsonError) {
            console.log(`${service} response is not JSON, treating as text:`, responseText);
            // Create a JSON-like object for non-JSON responses
            data = {
                message: responseText,
                status: 'text_response',
                service: service
            };
        }
        
        if (response.ok) {
            if (statusIndicator) {
                statusIndicator.className = 'status-indicator status-online';
            }
            
            let displayText;
            if (typeof data === 'object' && data !== null) {
                displayText = JSON.stringify(data, null, 2);
            } else {
                displayText = String(data);
            }
            
            if (outputArea) {
                const messageToReplace = `<div>Checking ${serviceName} service status...</div>`;
                const newContent = outputArea.innerHTML.replace(messageToReplace, '');
                outputArea.innerHTML = `${newContent}<div class="console-output success">${serviceName} service: <span class="success">Online</span><br>Response: <pre>${displayText}</pre></div>`;
            }
        } else {
            // Handle HTTP error status
            if (statusIndicator) {
                statusIndicator.className = 'status-indicator status-warning';
            }
            
            if (outputArea) {
                const messageToReplace = `<div>Checking ${serviceName} service status...</div>`;
                const newContent = outputArea.innerHTML.replace(messageToReplace, '');
                outputArea.innerHTML = `${newContent}<div class="console-output error">${serviceName} service: <span class="error">HTTP ${response.status}</span><br>Response: ${responseText}</div>`;
            }
        }
        
    } catch (error) {
        console.error(`Error checking ${service}:`, error);
        
        if (statusIndicator) {
            statusIndicator.className = 'status-indicator status-offline';
        }
        
        if (outputArea) {
            const messageToReplace = `<div>Checking ${serviceName} service status...</div>`;
            const newContent = outputArea.innerHTML.replace(messageToReplace, '');
            outputArea.innerHTML = `${newContent}<div class="console-output error">${serviceName} service: <span class="error">Offline</span><br>Error: ${error.message}</div>`;
        }
    }
}

// Check all services status with better error handling
async function checkAllServicesStatus() {
    const services = ['coordinator', 'stt', 'tts', 'iot', 'ollama'];
    const outputArea = document.getElementById('status-output');
    
    if (outputArea) {
        outputArea.innerHTML = '<div class="console-output">Checking all services...</div>';
    }
    
    console.log('Starting service status check for all services');
    
    // Check services with staggered timing to avoid overwhelming
    for (let i = 0; i < services.length; i++) {
        const service = services[i];
        console.log(`Checking service ${i + 1}/${services.length}: ${service}`);
        
        try {
            await checkServiceStatus(service);
            // Small delay between requests
            if (i < services.length - 1) {
                await new Promise(resolve => setTimeout(resolve, 300));
            }
        } catch (error) {
            console.error(`Failed to check ${service}:`, error);
        }
    }
    
    console.log('Completed checking all services');
}

// Specialized function for Ollama service
async function checkOllamaSpecifically() {
    const outputArea = document.getElementById('status-output');
    const statusIndicator = document.getElementById('ollama-status');
    
    if (outputArea) {
        outputArea.innerHTML += '<div>Checking Ollama service specifically...</div>';
    }
    
    try {
        console.log('Checking Ollama at:', API_URLS.ollama);
        
        // Try the main endpoint first
        let response = await fetch(API_URLS.ollama);
        let responseText = await response.text();
        
        console.log('Ollama main endpoint response:', responseText);
        
        if (response.ok) {
            // Ollama is running, now try to get more detailed info
            try {
                const modelsResponse = await fetch(`${API_URLS.ollama}/api/tags`);
                const modelsData = await modelsResponse.json();
                
                if (statusIndicator) {
                    statusIndicator.className = 'status-indicator status-online';
                }
                
                if (outputArea) {
                    outputArea.innerHTML += `<div class="console-output success">Ollama service: <span class="success">Online</span><br>Status: ${responseText}<br>Available models: ${modelsData.models ? modelsData.models.length : 'Unknown'}</div>`;
                }
                
            } catch (modelsError) {
                console.log('Could not fetch models, but Ollama is running:', modelsError);
                
                if (statusIndicator) {
                    statusIndicator.className = 'status-indicator status-warning';
                }
                
                if (outputArea) {
                    outputArea.innerHTML += `<div class="console-output">Ollama service: <span class="success">Running</span><br>Status: ${responseText}<br>Note: Could not fetch models list</div>`;
                }
            }
        } else {
            throw new Error(`HTTP ${response.status}: ${responseText}`);
        }
        
    } catch (error) {
        console.error('Ollama check failed:', error);
        
        if (statusIndicator) {
            statusIndicator.className = 'status-indicator status-offline';
        }
        
        if (outputArea) {
            outputArea.innerHTML += `<div class="console-output error">Ollama service: <span class="error">Offline</span><br>Error: ${error.message}</div>`;
        }
    }
}

// Debug function to test individual service
async function debugService(serviceName) {
    console.log(`=== Debugging ${serviceName} ===`);
    
    const url = API_URLS[serviceName];
    console.log(`URL: ${url}`);
    
    try {
        // Test with different methods and headers
        const testConfigs = [
            { method: 'GET', headers: { 'Accept': 'application/json' } },
            { method: 'GET', headers: { 'Accept': 'text/plain' } },
            { method: 'GET', headers: { 'Accept': '*/*' } },
        ];
        
        for (let i = 0; i < testConfigs.length; i++) {
            const config = testConfigs[i];
            console.log(`Test ${i + 1}:`, config);
            
            try {
                const response = await fetch(url, config);
                const text = await response.text();
                
                console.log(`Response status: ${response.status}`);
                console.log(`Response headers:`, Object.fromEntries(response.headers.entries()));
                console.log(`Response text:`, text);
                
                // Try to parse as JSON
                try {
                    const json = JSON.parse(text);
                    console.log(`Parsed JSON:`, json);
                } catch (e) {
                    console.log(`Not valid JSON:`, e.message);
                }
                
                console.log('---');
                
            } catch (fetchError) {
                console.error(`Fetch error in test ${i + 1}:`, fetchError);
            }
        }
        
    } catch (error) {
        console.error(`Debug failed for ${serviceName}:`, error);
    }
}

// Enhanced service health check
async function performServiceHealthCheck() {
    console.log('=== Service Health Check ===');
    
    const services = Object.keys(API_URLS);
    const results = {};
    
    for (const service of services) {
        console.log(`Health checking: ${service}`);
        
        try {
            const startTime = Date.now();
            const response = await fetch(API_URLS[service], {
                method: 'GET',
                headers: { 'Accept': '*/*' }
            });
            const endTime = Date.now();
            const responseTime = endTime - startTime;
            
            const text = await response.text();
            
            results[service] = {
                status: response.ok ? 'healthy' : 'unhealthy',
                httpStatus: response.status,
                responseTime: responseTime,
                responseLength: text.length,
                contentType: response.headers.get('content-type'),
                isJson: false
            };
            
            try {
                JSON.parse(text);
                results[service].isJson = true;
            } catch (e) {
                results[service].isJson = false;
            }
            
        } catch (error) {
            results[service] = {
                status: 'error',
                error: error.message
            };
        }
    }
    
    console.log('Health check results:', results);
    return results;
}

// Export debug functions for console use
window.debugService = debugService;
window.performServiceHealthCheck = performServiceHealthCheck;
window.checkOllamaSpecifically = checkOllamaSpecifically;