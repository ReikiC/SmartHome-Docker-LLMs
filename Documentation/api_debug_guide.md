# Smart Home Assistant - API Debug & Testing Guide

🔧 **Complete API Documentation and Testing Suite**

This document provides comprehensive information for debugging, testing, and interacting with all Smart Home Assistant APIs.

---

## 📋 Table of Contents

- [Service Overview](#-service-overview)
- [Quick Health Check](#-quick-health-check)
- [Coordinator Service APIs](#-coordinator-service-apis)
- [STT Service APIs](#-stt-service-apis)
- [TTS Service APIs](#-tts-service-apis)
- [IoT Control APIs](#-iot-control-apis)
- [Ollama Service APIs](#-ollama-service-apis)
- [WebSocket APIs](#-websocket-apis)
- [Testing Scripts](#-testing-scripts)
- [Troubleshooting](#-troubleshooting)

---

## 🌐 Service Overview

| Service | Port | Base URL | Purpose |
|---------|------|----------|---------|
| **Coordinator** | 8080 | `http://localhost:8080` | Central orchestration & AI processing |
| **STT** | 8000 | `http://localhost:8000` | Speech-to-Text conversion |
| **TTS** | 8001 | `http://localhost:8001` | Text-to-Speech synthesis |
| **IoT Control** | 8002 | `http://localhost:8002` | Device management |
| **Ollama** | 11434 | `http://localhost:11434` | LLM processing |

---

## ⚡ Quick Health Check

### Bash Script - Check All Services
```bash
#!/bin/bash
echo "🔍 Smart Home Assistant - Health Check"
echo "======================================"

services=("coordinator:8080" "stt:8000" "tts:8001" "iot:8002" "ollama:11434")

for service in "${services[@]}"; do
    name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)
    
    echo -n "Checking $name... "
    
    if curl -s --max-time 5 "http://localhost:$port" > /dev/null; then
        echo "✅ Online"
    else
        echo "❌ Offline"
    fi
done

echo "======================================"
echo "✨ Health check complete!"
```

### PowerShell Script - Windows
```powershell
Write-Host "🔍 Smart Home Assistant - Health Check" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

$services = @(
    @{Name="Coordinator"; Port=8080},
    @{Name="STT"; Port=8000},
    @{Name="TTS"; Port=8001},
    @{Name="IoT"; Port=8002},
    @{Name="Ollama"; Port=11434}
)

foreach ($service in $services) {
    Write-Host "Checking $($service.Name)... " -NoNewline
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$($service.Port)" -TimeoutSec 5 -UseBasicParsing
        Write-Host "✅ Online" -ForegroundColor Green
    } catch {
        Write-Host "❌ Offline" -ForegroundColor Red
    }
}
```

---

## 🎯 Coordinator Service APIs

**Base URL**: `http://localhost:8080`

### 1. Health Check
```bash
curl -X GET http://localhost:8080/
```

**Expected Response**:
```json
{
  "message": "AI Voice Assistant Coordinator Service is running"
}
```

### 2. Process Text Input
```bash
curl -X POST http://localhost:8080/process_text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Turn on the living room lights"
  }'
```

**Response**:
```json
{
  "input_text": "Turn on the living room lights",
  "ai_response": "I'll turn on the living room lights for you.",
  "audio_path": "/app/audio/tts_1234567890.mp3",
  "expression": "neutral",
  "iot_commands": [
    {
      "device": "ceiling_light",
      "action": "on",
      "location": "living_room",
      "parameters": {}
    }
  ],
  "iot_results": [...],
  "location": "living_room"
}
```

### 3. Process Audio Input
```bash
curl -X POST http://localhost:8080/process_audio \
  -H "Content-Type: application/json" \
  -d '{
    "audio_path": "/app/audio/recording.wav"
  }'
```

### 4. Execute Scene Mode
```bash
curl -X POST http://localhost:8080/execute_scene \
  -H "Content-Type: application/json" \
  -d '{
    "scene_name": "sleep_mode",
    "location": "bedroom"
  }'
```

### 5. Get Room Status
```bash
curl -X GET http://localhost:8080/room_status/living_room
```

### 6. Voice with Context (Advanced)
```bash
curl -X POST http://localhost:8080/process_voice_with_context \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Make it warmer",
    "user_context": {
      "activity": "sleeping",
      "time_of_day": "night"
    },
    "location": "bedroom",
    "device_id": "mobile_123"
  }'
```

---

## 🎤 STT Service APIs

**Base URL**: `http://localhost:8000`

### 1. Health Check
```bash
curl -X GET http://localhost:8000/
```

### 2. Upload Audio File for Transcription
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@/path/to/audio.wav"
```

**Response**:
```json
{
  "text": "Turn on the lights please",
  "audio_path": "/app/audio/upload_1234567890.wav"
}
```

### 3. Transcribe Existing Audio File
```bash
curl -X POST http://localhost:8000/transcribe \
  -H "Content-Type: application/json" \
  -d '{
    "audio_path": "/app/audio/existing_file.wav"
  }'
```

### 4. Test with JavaScript (Browser)
```javascript
// Record audio and send to STT
async function testSTT() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream);
    const chunks = [];
    
    mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
    mediaRecorder.onstop = async () => {
        const blob = new Blob(chunks, { type: 'audio/wav' });
        const formData = new FormData();
        formData.append('file', blob, 'test.wav');
        
        const response = await fetch('http://localhost:8000/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        console.log('Transcription:', result.text);
    };
    
    mediaRecorder.start();
    setTimeout(() => mediaRecorder.stop(), 5000); // Record for 5 seconds
}
```

---

## 🔊 TTS Service APIs

**Base URL**: `http://localhost:8001`

### 1. Health Check
```bash
curl -X GET http://localhost:8001/
```

### 2. Get Available Voices
```bash
curl -X GET http://localhost:8001/voices
```

**Response**:
```json
{
  "voices": [
    {
      "Name": "en-US-AriaNeural",
      "Gender": "Female",
      "Locale": "en-US"
    },
    ...
  ]
}
```

### 3. Synthesize Speech
```bash
curl -X POST http://localhost:8001/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, welcome to your smart home!",
    "voice": "en-US-AriaNeural",
    "format": "mp3"
  }'
```

**Response**:
```json
{
  "audio_path": "/app/audio/tts_1234567890.mp3",
  "format": "mp3",
  "voice": "en-US-AriaNeural"
}
```

### 4. Get Generated Audio File
```bash
curl -X GET http://localhost:8001/audio/tts_1234567890.mp3 \
  --output audio_response.mp3
```

### 5. Stream Audio (Real-time)
```bash
curl -X POST http://localhost:8001/stream \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is a streaming audio test",
    "voice": "en-US-GuyNeural"
  }'
```

### 6. Test Different Languages
```bash
# English
curl -X POST http://localhost:8001/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Good morning! How can I help you today?",
    "voice": "en-US-AriaNeural"
  }'

# Chinese (if supported)
curl -X POST http://localhost:8001/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "早上好！今天我可以为您做些什么？",
    "voice": "zh-CN-XiaoxiaoNeural"
  }'
```

---

## 🏠 IoT Control APIs

**Base URL**: `http://localhost:8002`

### 1. Health Check
```bash
curl -X GET http://localhost:8002/
```

### 2. Get All Device Status
```bash
curl -X GET http://localhost:8002/devices
```

**Response**:
```json
{
  "devices": {
    "ceiling_light": {
      "living_room": {
        "status": "off",
        "brightness": 50,
        "color_temp": 4000
      },
      "bedroom": {...}
    },
    "ac": {...},
    "fan": {...}
  }
}
```

### 3. Get Specific Device Status
```bash
curl -X GET http://localhost:8002/device/ceiling_light/living_room
```

### 4. Control Single Device
```bash
curl -X POST http://localhost:8002/control \
  -H "Content-Type: application/json" \
  -d '{
    "commands": [
      {
        "device": "ceiling_light",
        "action": "on",
        "location": "living_room",
        "parameters": {
          "brightness": 75
        }
      }
    ]
  }'
```

### 5. Control Multiple Devices
```bash
curl -X POST http://localhost:8002/control \
  -H "Content-Type: application/json" \
  -d '{
    "commands": [
      {
        "device": "ceiling_light",
        "action": "on",
        "location": "living_room"
      },
      {
        "device": "ac",
        "action": "set_temperature",
        "location": "living_room",
        "parameters": {
          "temperature": 24
        }
      },
      {
        "device": "curtain",
        "action": "set_position",
        "location": "living_room",
        "parameters": {
          "position": 50
        }
      }
    ]
  }'
```

### 6. Execute Scene Mode
```bash
curl -X POST http://localhost:8002/execute_scene \
  -H "Content-Type: application/json" \
  -d '{
    "scene_name": "movie_mode",
    "location": "living_room"
  }'
```

### 7. Get Sensor Data
```bash
# All sensors
curl -X GET http://localhost:8002/sensors

# Specific room sensors
curl -X GET http://localhost:8002/sensors/living_room
```

**Response**:
```json
{
  "location": "living_room",
  "sensors": {
    "temperature": 23.5,
    "humidity": 55,
    "co2": 420,
    "voc": 15,
    "motion": false,
    "light_level": 300,
    "last_update": "2025-06-12T10:30:00"
  }
}
```

### 8. Device Control Examples by Type

#### Lighting Control
```bash
# Turn on with specific brightness and color temperature
curl -X POST http://localhost:8002/control \
  -H "Content-Type: application/json" \
  -d '{
    "commands": [
      {
        "device": "ceiling_light",
        "action": "set_brightness",
        "location": "study",
        "parameters": {
          "brightness": 80,
          "color_temp": 4500
        }
      }
    ]
  }'
```

#### Air Conditioner Control
```bash
# Set AC mode and temperature
curl -X POST http://localhost:8002/control \
  -H "Content-Type: application/json" \
  -d '{
    "commands": [
      {
        "device": "ac",
        "action": "set_temperature",
        "location": "bedroom",
        "parameters": {
          "temperature": 22,
          "mode": "cool",
          "fan_speed": "medium"
        }
      }
    ]
  }'
```

#### Fan Control
```bash
# Control fan speed and oscillation
curl -X POST http://localhost:8002/control \
  -H "Content-Type: application/json" \
  -d '{
    "commands": [
      {
        "device": "fan",
        "action": "set_speed",
        "location": "living_room",
        "parameters": {
          "speed": 3,
          "oscillation": true
        }
      }
    ]
  }'
```

#### Curtain Control
```bash
# Set curtain position
curl -X POST http://localhost:8002/control \
  -H "Content-Type: application/json" \
  -d '{
    "commands": [
      {
        "device": "curtain",
        "action": "set_position",
        "location": "bedroom",
        "parameters": {
          "position": 75
        }
      }
    ]
  }'
```

---

## 🧠 Ollama Service APIs

**Base URL**: `http://localhost:11434`

### 1. Health Check
```bash
curl -X GET http://localhost:11434/
```

### 2. List Available Models
```bash
curl -X GET http://localhost:11434/api/tags
```

**Response**:
```json
{
  "models": [
    {
      "name": "llama3:8b",
      "modified_at": "2025-06-12T10:30:00Z",
      "size": 4661224676
    }
  ]
}
```

### 3. Pull New Model
```bash
curl -X POST http://localhost:11434/api/pull \
  -H "Content-Type: application/json" \
  -d '{
    "name": "llama3:8b"
  }'
```

### 4. Generate Text Response
```bash
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3:8b",
    "prompt": "Explain how smart homes work in simple terms.",
    "stream": false
  }'
```

### 5. Chat with Model (Conversation Mode)
```bash
curl -X POST http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3:8b",
    "messages": [
      {
        "role": "user",
        "content": "What are the benefits of edge computing in smart homes?"
      }
    ],
    "stream": false
  }'
```

### 6. Model Information
```bash
curl -X POST http://localhost:11434/api/show \
  -H "Content-Type: application/json" \
  -d '{
    "name": "llama3:8b"
  }'
```

---

## 🔌 WebSocket APIs

### Coordinator WebSocket

**URL**: `ws://localhost:8080/ws`

#### Connection Test (JavaScript)
```javascript
const ws = new WebSocket('ws://localhost:8080/ws');

ws.onopen = () => {
    console.log('✅ Connected to Coordinator WebSocket');
    
    // Test ping
    ws.send(JSON.stringify({
        type: 'ping'
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('📨 Received:', data);
};

ws.onerror = (error) => {
    console.error('❌ WebSocket error:', error);
};
```

#### Send Text Message
```javascript
ws.send(JSON.stringify({
    type: 'text',
    text: 'Turn on all lights in the house',
    user_context: {
        activity: 'working',
        time_of_day: 'evening'
    },
    location: 'study'
}));
```

#### Execute Scene via WebSocket
```javascript
ws.send(JSON.stringify({
    type: 'scene_command',
    scene: 'sleep_mode',
    location: 'bedroom'
}));
```

#### Register Device
```javascript
ws.send(JSON.stringify({
    type: 'device_registration',
    device_info: {
        type: 'mobile_app',
        platform: 'web',
        capabilities: ['voice', 'text', 'notifications']
    },
    capabilities: ['audio_input', 'audio_output', 'display']
}));
```

### IoT WebSocket

**URL**: `ws://localhost:8002/ws`

#### Real-time Device Monitoring
```javascript
const iotWs = new WebSocket('ws://localhost:8002/ws');

iotWs.onopen = () => {
    console.log('✅ Connected to IoT WebSocket');
    
    // Request all sensors data
    iotWs.send(JSON.stringify({
        type: 'get_sensors'
    }));
};

iotWs.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'sensor_update') {
        console.log(`🌡️ ${data.location} sensors updated:`, data.sensors);
    } else if (data.type === 'device_update') {
        console.log(`🔌 ${data.device} in ${data.location} updated:`, data.state);
    }
};
```

#### Control Device via WebSocket
```javascript
iotWs.send(JSON.stringify({
    type: 'control',
    commands: [
        {
            device: 'ceiling_light',
            action: 'on',
            location: 'kitchen',
            parameters: { brightness: 90 }
        }
    ]
}));
```

---

## 🧪 Testing Scripts

### Python Test Suite
```python
#!/usr/bin/env python3
"""
Smart Home Assistant - Comprehensive API Test Suite
"""
import requests
import json
import time
import websocket
import threading

class SmartHomeAPITester:
    def __init__(self):
        self.base_urls = {
            'coordinator': 'http://localhost:8080',
            'stt': 'http://localhost:8000',
            'tts': 'http://localhost:8001',
            'iot': 'http://localhost:8002',
            'ollama': 'http://localhost:11434'
        }
        
    def test_health_checks(self):
        """Test all service health endpoints"""
        print("🔍 Testing Health Checks...")
        
        for service, url in self.base_urls.items():
            try:
                response = requests.get(url, timeout=5)
                status = "✅ Online" if response.status_code == 200 else f"⚠️ HTTP {response.status_code}"
                print(f"  {service}: {status}")
            except Exception as e:
                print(f"  {service}: ❌ Offline ({e})")
    
    def test_text_processing(self):
        """Test text processing pipeline"""
        print("\n💬 Testing Text Processing...")
        
        test_commands = [
            "Turn on the living room lights",
            "Set bedroom temperature to 22 degrees",
            "Execute sleep mode",
            "What's the temperature in the kitchen?"
        ]
        
        for command in test_commands:
            try:
                response = requests.post(
                    f"{self.base_urls['coordinator']}/process_text",
                    json={"text": command},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"  ✅ '{command}' -> '{data.get('ai_response', 'No response')[:50]}...'")
                else:
                    print(f"  ❌ '{command}' -> HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ '{command}' -> Error: {e}")
    
    def test_iot_control(self):
        """Test IoT device control"""
        print("\n🏠 Testing IoT Control...")
        
        test_commands = [
            {
                "device": "ceiling_light",
                "action": "on",
                "location": "living_room",
                "parameters": {"brightness": 75}
            },
            {
                "device": "ac",
                "action": "set_temperature",
                "location": "bedroom",
                "parameters": {"temperature": 24}
            }
        ]
        
        for cmd in test_commands:
            try:
                response = requests.post(
                    f"{self.base_urls['iot']}/control",
                    json={"commands": [cmd]},
                    timeout=5
                )
                
                if response.status_code == 200:
                    print(f"  ✅ {cmd['device']} {cmd['action']} in {cmd['location']}")
                else:
                    print(f"  ❌ {cmd['device']} -> HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ {cmd['device']} -> Error: {e}")
    
    def test_tts(self):
        """Test Text-to-Speech"""
        print("\n🔊 Testing TTS...")
        
        try:
            response = requests.post(
                f"{self.base_urls['tts']}/synthesize",
                json={
                    "text": "Testing smart home voice synthesis",
                    "voice": "en-US-AriaNeural",
                    "format": "mp3"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ Audio generated: {data.get('audio_path', 'Unknown path')}")
            else:
                print(f"  ❌ TTS failed -> HTTP {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ TTS Error: {e}")
    
    def test_scenes(self):
        """Test scene execution"""
        print("\n🎬 Testing Scene Modes...")
        
        scenes = ["home_mode", "sleep_mode", "work_mode", "movie_mode"]
        
        for scene in scenes:
            try:
                response = requests.post(
                    f"{self.base_urls['coordinator']}/execute_scene",
                    json={"scene_name": scene, "location": "living_room"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    print(f"  ✅ Scene '{scene}' executed successfully")
                else:
                    print(f"  ❌ Scene '{scene}' -> HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Scene '{scene}' -> Error: {e}")
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Smart Home Assistant - API Test Suite")
        print("=" * 50)
        
        self.test_health_checks()
        self.test_text_processing()
        self.test_iot_control()
        self.test_tts()
        self.test_scenes()
        
        print("\n" + "=" * 50)
        print("✨ Test suite completed!")

if __name__ == "__main__":
    tester = SmartHomeAPITester()
    tester.run_all_tests()
```

### Node.js WebSocket Tester
```javascript
// websocket-test.js
const WebSocket = require('ws');

class WebSocketTester {
    constructor() {
        this.coordinatorWs = null;
        this.iotWs = null;
    }
    
    async testCoordinatorWebSocket() {
        console.log('🔌 Testing Coordinator WebSocket...');
        
        return new Promise((resolve) => {
            this.coordinatorWs = new WebSocket('ws://localhost:8080/ws');
            
            this.coordinatorWs.on('open', () => {
                console.log('  ✅ Connected to Coordinator WebSocket');
                
                // Test ping
                this.coordinatorWs.send(JSON.stringify({ type: 'ping' }));
                
                // Test text processing
                setTimeout(() => {
                    this.coordinatorWs.send(JSON.stringify({
                        type: 'text',
                        text: 'Turn on kitchen lights'
                    }));
                }, 1000);
            });
            
            this.coordinatorWs.on('message', (data) => {
                const message = JSON.parse(data);
                console.log('  📨 Received:', message.type);
                
                if (message.type === 'pong') {
                    console.log('  ✅ Ping/Pong test successful');
                }
            });
            
            this.coordinatorWs.on('error', (error) => {
                console.log('  ❌ WebSocket error:', error.message);
            });
            
            setTimeout(() => {
                this.coordinatorWs.close();
                resolve();
            }, 5000);
        });
    }
    
    async testIoTWebSocket() {
        console.log('\n🏠 Testing IoT WebSocket...');
        
        return new Promise((resolve) => {
            this.iotWs = new WebSocket('ws://localhost:8002/ws');
            
            this.iotWs.on('open', () => {
                console.log('  ✅ Connected to IoT WebSocket');
                
                // Request sensor data
                this.iotWs.send(JSON.stringify({ type: 'get_sensors' }));
                
                // Test device control
                setTimeout(() => {
                    this.iotWs.send(JSON.stringify({
                        type: 'control',
                        commands: [{
                            device: 'ceiling_light',
                            action: 'toggle',
                            location: 'living_room'
                        }]
                    }));
                }, 1000);
            });
            
            this.iotWs.on('message', (data) => {
                const message = JSON.parse(data);
                console.log('  📨 Received:', message.type);
                
                if (message.type === 'sensor_data') {
                    console.log('  🌡️ Sensor data received');
                } else if (message.type === 'device_update') {
                    console.log('  🔌 Device update received');
                }
            });
            
            this.iotWs.on('error', (error) => {
                console.log('  ❌ WebSocket error:', error.message);
            });
            
            setTimeout(() => {
                this.iotWs.close();
                resolve();
            }, 5000);
        });
    }
    
    async runTests() {
        console.log('🚀 WebSocket Test Suite');
        console.log('=' .repeat(30));
        
        await this.testCoordinatorWebSocket();
        await this.testIoTWebSocket();
        
        console.log('\n✨ WebSocket tests completed!');
    }
}

const tester = new WebSocketTester();
tester.runTests().catch(console.error);
```

---

## 🔍 Troubleshooting

### Common Issues & Solutions

#### 1. Service Connection Issues
```bash
# Check if services are running
docker-compose ps

# View service logs
docker-compose logs coordinator
docker-compose logs stt-service

# Restart specific service
docker-compose restart coordinator
```

#### 2. Audio Processing Issues
```bash
# Check STT service health
curl http://localhost:8000/

# Test with sample audio file
curl -X POST http://localhost:8000/upload \
  -F "file=@test_audio.wav"

# Check supported audio formats
curl http://localhost:8000/ | grep -i "supported"
```

#### 3. Model Loading Issues
```bash
# Check available models
curl http://localhost:11434/api/tags

# Pull missing model
curl -X POST http://localhost:11434/api/pull \
  -H "Content-Type: application/json" \
  -d '{"name": "llama3:8b"}'

# Check Ollama logs
docker-compose logs ollama
```

#### 4. IoT Control Issues
```bash
# Check device states
curl http://localhost:8002/devices | jq

# Test simple device control
curl -X POST http://localhost:8002/control \
  -H "Content-Type: application/json" \
  -d '{
    "commands": [{
      "device": "ceiling_light",
      "action": "on",
      "location": "living_room"
    }]
  }'
```

#### 5. WebSocket Connection Issues
```bash
# Test WebSocket endpoints
wscat -c ws://localhost:8080/ws
wscat -c ws://localhost:8002/ws

# Check for port conflicts
netstat -tlnp | grep :8080
```

### Performance Monitoring
```bash
# Monitor resource usage
docker stats

# Check API response times
time curl http://localhost:8080/

# Monitor WebSocket connections
ss -tulpn | grep :8080
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Restart with debug mode
docker-compose down
docker-compose up --build
```

---

## 📊 API Response Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| **200** | Success | Request processed successfully |
| **400** | Bad Request | Invalid JSON, missing parameters |
| **404** | Not Found | Invalid endpoint, device not found |
| **422** | Unprocessable Entity | Valid JSON but invalid data |
| **500** | Internal Server Error | Service crashed, model not loaded |
| **503** | Service Unavailable | Service starting up or overloaded |
| **504** | Gateway Timeout | Request took too long to process |

---

## 📈 Performance Benchmarking

### Load Testing Script
```bash
#!/bin/bash
# load-test.sh - Performance testing for Smart Home APIs

echo "🚀 Starting Performance Tests..."

# Test Coordinator API load
echo "Testing Coordinator API throughput..."
ab -n 100 -c 10 -H "Content-Type: application/json" \
   -p test_data.json http://localhost:8080/process_text

# Test IoT Control API load
echo "Testing IoT Control API throughput..."
ab -n 50 -c 5 -H "Content-Type: application/json" \
   -p iot_test.json http://localhost:8002/control

# Test TTS API load
echo "Testing TTS API throughput..."
ab -n 20 -c 2 -H "Content-Type: application/json" \
   -p tts_test.json http://localhost:8001/synthesize

echo "✅ Performance tests completed!"
```

### Stress Test Data Files

**test_data.json**:
```json
{
  "text": "Turn on all lights and set temperature to 22 degrees"
}
```

**iot_test.json**:
```json
{
  "commands": [
    {
      "device": "ceiling_light",
      "action": "toggle",
      "location": "living_room"
    }
  ]
}
```

**tts_test.json**:
```json
{
  "text": "Performance test audio generation",
  "voice": "en-US-AriaNeural"
}
```

### Python Performance Monitor
```python
#!/usr/bin/env python3
"""
Real-time performance monitoring for Smart Home APIs
"""
import requests
import time
import json
import threading
from datetime import datetime
import statistics

class PerformanceMonitor:
    def __init__(self):
        self.results = []
        self.running = True
        
    def test_endpoint(self, name, url, method='GET', data=None, headers=None):
        """Test single endpoint performance"""
        try:
            start_time = time.time()
            
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            else:
                response = requests.post(url, json=data, headers=headers, timeout=10)
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            result = {
                'timestamp': datetime.now().isoformat(),
                'endpoint': name,
                'response_time': response_time,
                'status_code': response.status_code,
                'success': response.status_code == 200
            }
            
            self.results.append(result)
            return result
            
        except Exception as e:
            result = {
                'timestamp': datetime.now().isoformat(),
                'endpoint': name,
                'response_time': None,
                'status_code': None,
                'success': False,
                'error': str(e)
            }
            self.results.append(result)
            return result
    
    def continuous_monitoring(self):
        """Run continuous performance monitoring"""
        print("🔍 Starting continuous performance monitoring...")
        print("=" * 60)
        
        test_configs = [
            {
                'name': 'Coordinator Health',
                'url': 'http://localhost:8080/',
                'method': 'GET'
            },
            {
                'name': 'Text Processing',
                'url': 'http://localhost:8080/process_text',
                'method': 'POST',
                'data': {'text': 'Performance test command'}
            },
            {
                'name': 'IoT Status',
                'url': 'http://localhost:8002/devices',
                'method': 'GET'
            },
            {
                'name': 'Sensor Data',
                'url': 'http://localhost:8002/sensors/living_room',
                'method': 'GET'
            }
        ]
        
        while self.running:
            for config in test_configs:
                result = self.test_endpoint(
                    config['name'],
                    config['url'],
                    config.get('method', 'GET'),
                    config.get('data'),
                    {'Content-Type': 'application/json'}
                )
                
                status = "✅" if result['success'] else "❌"
                response_time = f"{result['response_time']:.2f}ms" if result['response_time'] else "TIMEOUT"
                
                print(f"{status} {config['name']}: {response_time}")
            
            print("-" * 60)
            time.sleep(30)  # Test every 30 seconds
    
    def generate_report(self):
        """Generate performance report"""
        if not self.results:
            print("No performance data available")
            return
        
        print("\n📊 Performance Report")
        print("=" * 60)
        
        # Group results by endpoint
        endpoints = {}
        for result in self.results:
            endpoint = result['endpoint']
            if endpoint not in endpoints:
                endpoints[endpoint] = []
            if result['response_time'] is not None:
                endpoints[endpoint].append(result['response_time'])
        
        for endpoint, times in endpoints.items():
            if times:
                avg_time = statistics.mean(times)
                min_time = min(times)
                max_time = max(times)
                median_time = statistics.median(times)
                
                print(f"\n🎯 {endpoint}:")
                print(f"  Average: {avg_time:.2f}ms")
                print(f"  Median:  {median_time:.2f}ms")
                print(f"  Min:     {min_time:.2f}ms")
                print(f"  Max:     {max_time:.2f}ms")
                print(f"  Samples: {len(times)}")
        
        # Success rate
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r['success'])
        success_rate = (successful_tests / total_tests) * 100
        
        print(f"\n📈 Overall Success Rate: {success_rate:.1f}% ({successful_tests}/{total_tests})")

if __name__ == "__main__":
    monitor = PerformanceMonitor()
    
    try:
        # Run monitoring in background
        monitor_thread = threading.Thread(target=monitor.continuous_monitoring)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        print("Performance monitoring started. Press Ctrl+C to stop and generate report.")
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Stopping performance monitoring...")
        monitor.running = False
        time.sleep(2)  # Give time for last tests to complete
        monitor.generate_report()
```

---

## 🛠️ Development & Testing Tools

### API Collection for Postman
```json
{
  "info": {
    "name": "Smart Home Assistant API",
    "description": "Complete API collection for testing Smart Home Assistant",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Coordinator Service",
      "item": [
        {
          "name": "Health Check",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{coordinator_url}}/",
              "host": ["{{coordinator_url}}"],
              "path": [""]
            }
          }
        },
        {
          "name": "Process Text",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"text\": \"Turn on the living room lights and set temperature to 24 degrees\"\n}"
            },
            "url": {
              "raw": "{{coordinator_url}}/process_text",
              "host": ["{{coordinator_url}}"],
              "path": ["process_text"]
            }
          }
        },
        {
          "name": "Execute Scene",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"scene_name\": \"sleep_mode\",\n  \"location\": \"bedroom\"\n}"
            },
            "url": {
              "raw": "{{coordinator_url}}/execute_scene",
              "host": ["{{coordinator_url}}"],
              "path": ["execute_scene"]
            }
          }
        }
      ]
    },
    {
      "name": "IoT Control Service",
      "item": [
        {
          "name": "Get All Devices",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{iot_url}}/devices",
              "host": ["{{iot_url}}"],
              "path": ["devices"]
            }
          }
        },
        {
          "name": "Control Device",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"commands\": [\n    {\n      \"device\": \"ceiling_light\",\n      \"action\": \"on\",\n      \"location\": \"living_room\",\n      \"parameters\": {\n        \"brightness\": 75\n      }\n    }\n  ]\n}"
            },
            "url": {
              "raw": "{{iot_url}}/control",
              "host": ["{{iot_url}}"],
              "path": ["control"]
            }
          }
        }
      ]
    }
  ],
  "variable": [
    {
      "key": "coordinator_url",
      "value": "http://localhost:8080"
    },
    {
      "key": "stt_url",
      "value": "http://localhost:8000"
    },
    {
      "key": "tts_url",
      "value": "http://localhost:8001"
    },
    {
      "key": "iot_url",
      "value": "http://localhost:8002"
    },
    {
      "key": "ollama_url",
      "value": "http://localhost:11434"
    }
  ]
}
```

### Environment Configuration
```bash
# .env file for testing
COORDINATOR_URL=http://localhost:8080
STT_URL=http://localhost:8000
TTS_URL=http://localhost:8001
IOT_URL=http://localhost:8002
OLLAMA_URL=http://localhost:11434

# Test timeouts
API_TIMEOUT=30
VOICE_TIMEOUT=10
TTS_TIMEOUT=15

# Test data
TEST_AUDIO_PATH=./test_data/sample_audio.wav
TEST_VOICE_COMMAND="Turn on all lights"
TEST_ROOM=living_room
```

### Docker Health Check Script
```bash
#!/bin/bash
# docker-health-check.sh

echo "🐳 Docker Container Health Check"
echo "================================"

containers=("ai-assistant-coordinator" "ai-assistant-stt" "ai-assistant-tts" "ai-assistant-iot" "ai-assistant-ollama")

for container in "${containers[@]}"; do
    echo -n "Checking $container... "
    
    if docker ps --format "table {{.Names}}" | grep -q "$container"; then
        status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null)
        
        if [ "$status" = "healthy" ]; then
            echo "✅ Healthy"
        elif [ "$status" = "unhealthy" ]; then
            echo "❌ Unhealthy"
        elif [ "$status" = "starting" ]; then
            echo "🔄 Starting"
        else
            echo "⚪ No health check"
        fi
    else
        echo "❌ Not running"
    fi
done

echo ""
echo "📊 Resource Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

---

## 🎯 Advanced Testing Scenarios

### End-to-End Voice Pipeline Test
```python
#!/usr/bin/env python3
"""
End-to-end voice pipeline testing
"""
import requests
import time
import tempfile
import wave
import numpy as np

def generate_test_audio(text_content, duration=3):
    """Generate synthetic audio for testing"""
    sample_rate = 16000
    frequency = 440  # A4 note
    
    # Generate sine wave
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = np.sin(2 * np.pi * frequency * t) * 0.3
    
    # Convert to 16-bit PCM
    audio_data = (audio_data * 32767).astype(np.int16)
    
    # Save as WAV file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        with wave.open(f.name, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        return f.name

def test_voice_pipeline():
    """Test complete voice processing pipeline"""
    print("🎤 Testing End-to-End Voice Pipeline")
    print("=" * 40)
    
    # Step 1: Generate test audio
    print("1. Generating test audio...")
    audio_file = generate_test_audio("test command")
    
    # Step 2: Send to STT service
    print("2. Processing with STT...")
    with open(audio_file, 'rb') as f:
        files = {'file': f}
        stt_response = requests.post(
            'http://localhost:8000/upload',
            files=files,
            timeout=30
        )
    
    if stt_response.status_code != 200:
        print(f"❌ STT failed: {stt_response.status_code}")
        return
    
    stt_data = stt_response.json()
    recognized_text = stt_data.get('text', '')
    print(f"   Recognized: '{recognized_text}'")
    
    # Step 3: Process with Coordinator
    print("3. Processing with AI Coordinator...")
    coord_response = requests.post(
        'http://localhost:8080/process_text',
        json={'text': recognized_text or 'turn on lights'},
        timeout=30
    )
    
    if coord_response.status_code != 200:
        print(f"❌ Coordinator failed: {coord_response.status_code}")
        return
    
    coord_data = coord_response.json()
    ai_response = coord_data.get('ai_response', '')
    print(f"   AI Response: '{ai_response}'")
    
    # Step 4: Check IoT commands
    iot_commands = coord_data.get('iot_commands', [])
    if iot_commands:
        print(f"   IoT Commands: {len(iot_commands)} executed")
        for cmd in iot_commands:
            print(f"     - {cmd.get('device', 'unknown')} {cmd.get('action', 'unknown')}")
    
    # Step 5: Check TTS audio
    audio_path = coord_data.get('audio_path', '')
    if audio_path:
        print(f"   TTS Audio: {audio_path}")
        
        # Try to download the audio
        audio_filename = audio_path.split('/')[-1]
        audio_url = f"http://localhost:8001/audio/{audio_filename}"
        
        audio_response = requests.get(audio_url, timeout=10)
        if audio_response.status_code == 200:
            print(f"   ✅ Audio file accessible ({len(audio_response.content)} bytes)")
        else:
            print(f"   ⚠️ Audio file not accessible: {audio_response.status_code}")
    
    print("\n✅ Voice pipeline test completed!")

if __name__ == "__main__":
    test_voice_pipeline()
```

### Multi-Room Scene Test
```python
#!/usr/bin/env python3
"""
Multi-room scene testing
"""
import requests
import time
import json

def test_multi_room_scenes():
    """Test scene execution across multiple rooms"""
    print("🏠 Testing Multi-Room Scene Execution")
    print("=" * 40)
    
    scenes = [
        {"name": "home_mode", "description": "Welcome home"},
        {"name": "sleep_mode", "description": "Good night"},
        {"name": "work_mode", "description": "Focus time"},
        {"name": "movie_mode", "description": "Entertainment"},
        {"name": "away_mode", "description": "Leaving home"}
    ]
    
    rooms = ["living_room", "bedroom", "kitchen", "study", "bathroom"]
    
    for scene in scenes:
        print(f"\n🎬 Testing {scene['name']} ({scene['description']})...")
        
        for room in rooms:
            print(f"  Testing in {room}... ", end="")
            
            try:
                response = requests.post(
                    'http://localhost:8080/execute_scene',
                    json={
                        "scene_name": scene['name'],
                        "location": room
                    },
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    success_count = sum(1 for r in results if r.get('status') == 'success')
                    print(f"✅ {success_count}/{len(results)} commands")
                else:
                    print(f"❌ HTTP {response.status_code}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
            
            time.sleep(1)  # Brief pause between tests
    
    print("\n✅ Multi-room scene testing completed!")

if __name__ == "__main__":
    test_multi_room_scenes()
```

---

## 📋 API Testing Checklist

### Pre-Test Setup
- [ ] All Docker containers running
- [ ] Services responding to health checks
- [ ] Ollama model loaded (llama3:8b)
- [ ] Network connectivity verified
- [ ] Test data files prepared

### Basic Functionality Tests
- [ ] Health check endpoints (all services)
- [ ] Text processing pipeline
- [ ] Voice processing (STT → Coordinator → TTS)
- [ ] IoT device control (individual devices)
- [ ] Scene mode execution
- [ ] Sensor data retrieval
- [ ] WebSocket connections

### Advanced Feature Tests
- [ ] Multi-language voice commands
- [ ] Complex scene combinations
- [ ] Real-time sensor monitoring
- [ ] Concurrent request handling
- [ ] Error handling and recovery
- [ ] Performance under load

### Integration Tests
- [ ] End-to-end voice pipeline
- [ ] Multi-room scene execution
- [ ] Cross-service communication
- [ ] WebSocket real-time updates
- [ ] ESP32 device simulation
- [ ] Mobile app compatibility

### Performance Tests
- [ ] Response time measurements
- [ ] Throughput testing
- [ ] Resource usage monitoring
- [ ] Concurrent user simulation
- [ ] Memory leak detection
- [ ] CPU usage optimization

---

## 🔧 Quick Reference Commands

### Service Management
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f coordinator

# Restart service
docker-compose restart stt-service

# Stop all services
docker-compose down
```

### API Quick Tests
```bash
# Test all health endpoints
for port in 8080 8000 8001 8002 11434; do
  echo "Testing localhost:$port"
  curl -s http://localhost:$port | head -1
done

# Quick voice command test
curl -X POST http://localhost:8080/process_text \
  -H "Content-Type: application/json" \
  -d '{"text": "turn on all lights"}'

# Quick device control
curl -X POST http://localhost:8002/control \
  -H "Content-Type: application/json" \
  -d '{"commands": [{"device": "ceiling_light", "action": "toggle", "location": "living_room"}]}'
```

### Monitoring Commands
```bash
# Watch container resources
watch docker stats

# Monitor API requests
tail -f /var/log/nginx/access.log | grep -E "(8080|8000|8001|8002)"

# Check network connections
netstat -tulpn | grep -E "(8080|8000|8001|8002|11434)"
```

---

**🎉 Happy Testing!** 

This comprehensive guide covers all aspects of API debugging and testing for the Smart Home Assistant system. Use the appropriate sections based on your testing needs, and don't hesitate to modify the scripts for your specific requirements.