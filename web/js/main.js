// Main program entry point - Refactored for dual mode support

// Global variables
let currentMode = 'user'; // Default mode

// Detect current mode based on URL
function detectCurrentMode() {
    if (window.location.pathname.includes('developer.html')) {
        currentMode = 'developer';
        return 'developer';
    } else {
        currentMode = 'user';
        return 'user';
    }
}

// User mode initialization
function initUserMode() {
    console.log('Initializing User Mode...');
    
    // Initialize environment monitoring
    if (typeof updateEnvironmentStatus === 'function') {
        updateEnvironmentStatus();
        // Auto-refresh environment status every 30 seconds
        setInterval(updateEnvironmentStatus, 30000);
    }
    
    // Initialize device grid if present
    if (typeof updateDeviceGrid === 'function') {
        updateDeviceGrid();
    }
    
    // Set default room
    if (typeof selectRoom === 'function') {
        selectRoom('living_room');
    }
    
    console.log('User Mode initialized successfully');
}

// Developer mode initialization
function initDeveloperMode() {
    console.log('Initializing Developer Mode...');
    
    // Set up event listeners for developer mode
    setupDeveloperEventListeners();
    
    // Initialize IoT device actions dropdown
    if (typeof updateActionDropdown === 'function') {
        updateActionDropdown();
    }
    
    // Auto-check all services status after a short delay
    setTimeout(() => {
        if (typeof checkAllServicesStatus === 'function') {
            checkAllServicesStatus();
        }
    }, 1000);
    
    console.log('Developer Mode initialized successfully');
}

// Setup event listeners for developer mode
function setupDeveloperEventListeners() {
    // Ollama model management
    const checkModelsBtn = document.getElementById('check-models');
    const pullModelBtn = document.getElementById('pull-model');
    
    if (checkModelsBtn && typeof checkOllamaModels === 'function') {
        checkModelsBtn.addEventListener('click', checkOllamaModels);
    }
    
    if (pullModelBtn && typeof pullOllamaModel === 'function') {
        pullModelBtn.addEventListener('click', pullOllamaModel);
    }
    
    // Service status checks
    const serviceButtons = [
        { id: 'check-coordinator', service: 'coordinator' },
        { id: 'check-stt', service: 'stt' },
        { id: 'check-tts', service: 'tts' },
        { id: 'check-iot', service: 'iot' },
        { id: 'check-ollama', service: 'ollama' }
    ];
    
    serviceButtons.forEach(({ id, service }) => {
        const button = document.getElementById(id);
        if (button && typeof checkServiceStatus === 'function') {
            button.addEventListener('click', () => checkServiceStatus(service));
        }
    });
    
    // Check all services button
    const checkAllBtn = document.getElementById('check-all-services');
    if (checkAllBtn && typeof checkAllServicesStatus === 'function') {
        checkAllBtn.addEventListener('click', checkAllServicesStatus);
    }
    
    // AI interaction
    const sendTextBtn = document.getElementById('send-text');
    const clearChatBtn = document.getElementById('clear-chat');
    const userInput = document.getElementById('user-input');
    
    if (sendTextBtn && typeof sendTextToAI === 'function') {
        sendTextBtn.addEventListener('click', sendTextToAI);
    }
    
    if (clearChatBtn && typeof clearChat === 'function') {
        clearChatBtn.addEventListener('click', clearChat);
    }
    
    if (userInput && typeof sendTextToAI === 'function') {
        userInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendTextToAI();
            }
        });
    }
    
    // IoT device control
    const sendCommandBtn = document.getElementById('send-command');
    const getDevicesBtn = document.getElementById('get-devices');
    const deviceTypeSelect = document.getElementById('device-type');
    
    if (sendCommandBtn && typeof sendIoTCommand === 'function') {
        sendCommandBtn.addEventListener('click', sendIoTCommand);
    }
    
    if (getDevicesBtn && typeof getAllDevices === 'function') {
        getDevicesBtn.addEventListener('click', getAllDevices);
    }
    
    if (deviceTypeSelect && typeof updateActionDropdown === 'function') {
        deviceTypeSelect.addEventListener('change', updateActionDropdown);
    }
    
    // Text-to-speech
    const synthesizeSpeechBtn = document.getElementById('synthesize-speech');
    const getVoicesBtn = document.getElementById('get-voices');
    
    if (synthesizeSpeechBtn && typeof synthesizeSpeech === 'function') {
        synthesizeSpeechBtn.addEventListener('click', synthesizeSpeech);
    }
    
    if (getVoicesBtn && typeof getAvailableVoices === 'function') {
        getVoicesBtn.addEventListener('click', getAvailableVoices);
    }
    
    // WebSocket interaction
    const wsConnectBtn = document.getElementById('ws-connect');
    const wsDisconnectBtn = document.getElementById('ws-disconnect');
    const wsSendBtn = document.getElementById('ws-send');
    const wsMessage = document.getElementById('ws-message');
    
    if (wsConnectBtn && typeof connectWebSocket === 'function') {
        wsConnectBtn.addEventListener('click', connectWebSocket);
    }
    
    if (wsDisconnectBtn && typeof disconnectWebSocket === 'function') {
        wsDisconnectBtn.addEventListener('click', disconnectWebSocket);
    }
    
    if (wsSendBtn && typeof sendWebSocketMessage === 'function') {
        wsSendBtn.addEventListener('click', sendWebSocketMessage);
    }
    
    if (wsMessage && typeof sendWebSocketMessage === 'function') {
        wsMessage.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendWebSocketMessage();
            }
        });
    }
}

// Common initialization for both modes
function initCommon() {
    console.log('Initializing common components...');
    
    // Check if API URLs are properly configured
    if (typeof API_URLS === 'undefined') {
        console.error('API_URLS not defined. Make sure config.js is loaded.');
        return false;
    }
    
    // Set up global error handlers
    window.addEventListener('error', function(e) {
        console.error('Global error:', e.error);
        if (typeof showNotification === 'function') {
            showNotification('An unexpected error occurred', 'danger');
        }
    });
    
    // Set up unhandled promise rejection handler
    window.addEventListener('unhandledrejection', function(e) {
        console.error('Unhandled promise rejection:', e.reason);
        if (typeof showNotification === 'function') {
            showNotification('Network or API error occurred', 'warning');
        }
    });
    
    return true;
}

// Mode switching helper
function switchMode(targetMode) {
    if (targetMode === 'user' && currentMode !== 'user') {
        window.location.href = 'index.html';
    } else if (targetMode === 'developer' && currentMode !== 'developer') {
        window.location.href = 'developer.html';
    }
}

// Utility function to check if element exists
function elementExists(id) {
    return document.getElementById(id) !== null;
}

// Utility function to safely call function if it exists
function safeCall(functionName, ...args) {
    if (typeof window[functionName] === 'function') {
        try {
            return window[functionName](...args);
        } catch (error) {
            console.error(`Error calling ${functionName}:`, error);
            return null;
        }
    } else {
        console.warn(`Function ${functionName} not found`);
        return null;
    }
}

// Health check for critical functions
function performHealthCheck() {
    console.log('Performing health check...');
    
    const criticalFunctions = {
        common: ['apiRequest', 'handleApiError'],
        user: ['updateEnvironmentStatus', 'executeScene', 'quickControl'],
        developer: ['checkOllamaModels', 'checkServiceStatus', 'sendTextToAI']
    };
    
    const issues = [];
    
    // Check common functions
    criticalFunctions.common.forEach(func => {
        if (typeof window[func] !== 'function') {
            issues.push(`Missing common function: ${func}`);
        }
    });
    
    // Check mode-specific functions
    if (currentMode === 'user') {
        criticalFunctions.user.forEach(func => {
            if (typeof window[func] !== 'function') {
                issues.push(`Missing user mode function: ${func}`);
            }
        });
    } else if (currentMode === 'developer') {
        criticalFunctions.developer.forEach(func => {
            if (typeof window[func] !== 'function') {
                issues.push(`Missing developer mode function: ${func}`);
            }
        });
    }
    
    if (issues.length > 0) {
        console.warn('Health check found issues:', issues);
        return false;
    } else {
        console.log('Health check passed successfully');
        return true;
    }
}

// Main DOM loaded event handler
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, starting initialization...');
    
    // Detect current mode
    const mode = detectCurrentMode();
    console.log(`Detected mode: ${mode}`);
    
    // Initialize common components
    if (!initCommon()) {
        console.error('Failed to initialize common components');
        return;
    }
    
    // Perform health check
    setTimeout(() => {
        performHealthCheck();
    }, 100);
    
    // Initialize based on current mode
    if (mode === 'developer') {
        // Wait a bit for all modules to load
        setTimeout(initDeveloperMode, 200);
    } else {
        // User mode initialization
        setTimeout(initUserMode, 200);
    }
    
    console.log('Smart Home Interface initialization complete');
});

// Export mode detection for other modules
window.getCurrentMode = function() {
    return currentMode;
};

// Export mode switching function
window.switchToMode = switchMode;

// Export safe function calling utility
window.safeCall = safeCall;