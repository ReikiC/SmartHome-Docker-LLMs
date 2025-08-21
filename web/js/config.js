// API base URL configuration
const API_URLS = {
    coordinator: 'http://localhost:8080',
    stt: 'http://localhost:8000',
    tts: 'http://localhost:8001',
    iot: 'http://localhost:8002',
    ollama: 'http://localhost:11434'
};

// Service name mapping
const SERVICE_NAMES = {
    coordinator: 'Coordinator',
    stt: 'Speech Recognition',
    tts: 'Text-to-Speech',
    iot: 'IoT Control',
    ollama: 'Ollama'
};

// Device type action mapping
const DEVICE_ACTIONS = {
    light: [
        { value: 'on', text: 'Turn On' },
        { value: 'off', text: 'Turn Off' },
        { value: 'brighten', text: 'Brighten' },
        { value: 'dim', text: 'Dim' }
    ],
    fan: [
        { value: 'on', text: 'Turn On' },
        { value: 'off', text: 'Turn Off' },
        { value: 'speed_up', text: 'Speed Up' },
        { value: 'speed_down', text: 'Speed Down' }
    ],
    ac: [
        { value: 'on', text: 'Turn On' },
        { value: 'off', text: 'Turn Off' },
        { value: 'temp_up', text: 'Increase Temperature' },
        { value: 'temp_down', text: 'Decrease Temperature' }
    ],
    curtain: [
        { value: 'on', text: 'Open' },
        { value: 'off', text: 'Close' }
    ]
};