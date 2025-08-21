# AI Voice Assistant + IoT Control System

This is a Docker-based AI voice assistant system that uses Ollama as the core LLM, integrating speech recognition, speech synthesis, and IoT device control functionality. The system is designed for collaboration between low-computing-power devices (ESP32) and PC-side Docker containers, enabling voice interaction, emotion display, and IoT device control.

## System Architecture

The system consists of 5 Docker containers, each responsible for different functions:

1. **Ollama Service**: Provides LLM (Large Language Model) capabilities, handling natural language understanding and generation
2. **STT Service**: Responsible for speech recognition (Speech-to-Text), converting audio uploaded from ESP32 to text
3. **TTS Service**: Responsible for speech synthesis (Text-to-Speech), converting AI responses to audio playable by ESP32
4. **IoT Control Service**: Manages the status and control commands of various smart devices
5. **Coordinator Service**: Acts as the central controller, coordinating communication between services

## Requirements

- Docker and Docker Compose
- Mac mini (M4) or other computing devices running Docker
- ESP32 development board (for voice recording and playback)
- Optional: Second ESP32 development board (for LCD display of expressions)

## Quick Start

### 1. Clone the Project

```bash
git clone https://github.com/yourusername/ai-voice-assistant-iot.git
cd ai-voice-assistant-iot
```

### 2. Create Directory Structure

```bash
mkdir -p data/audio
mkdir -p data/ollama
mkdir -p services/coordinator
mkdir -p services/stt
mkdir -p services/tts
mkdir -p services/iot
mkdir -p esp32
```

### 3. Copy Configuration Files

Copy all code files to the appropriate directories:

- `docker-compose.yml` → Project root directory
- Python files and Dockerfile for each service → Corresponding service directories
- ESP32 code → esp32 directory

### 4. Build and Start Docker Containers

```bash
docker-compose up --build
```

When starting for the first time, the system will download relevant images and build containers, which may take some time.

### 5. Configure and Flash ESP32

1. Modify WiFi configuration and server IP address in the ESP32 code
2. Use Arduino IDE or PlatformIO to flash the code to ESP32
3. If using two ESP32s, you'll also need to set up the communication method for the LCD display ESP32

## Usage

After system startup, you can use it in the following ways:

1. **Voice Interaction**: Press the button on the ESP32 to start recording, which will be automatically sent to the server for processing after completion
2. **Check Service Status**: Visit http://localhost:8080 to check the coordinator service status
3. **Manual Testing**: Use Postman or curl to send requests to the various service APIs for testing

## Service API Documentation

### Coordinator Service (Port 8080)

- `GET /` - Check service status
- `POST /process_audio` - Process audio and return AI response
- `POST /process_text` - Process text and return AI response
- `WebSocket /ws` - WebSocket connection endpoint

### STT Service (Port 8000)

- `GET /` - Check service status
- `POST /transcribe` - Transcribe audio file at specified path
- `POST /upload` - Upload audio file and transcribe
- UDP Port 8000 - Receive audio data sent from ESP32

### TTS Service (Port 8001)

- `GET /` - Check service status
- `GET /voices` - List all available voices
- `POST /synthesize` - Synthesize speech and return audio file path
- `GET /audio/{filename}` - Get synthesized audio file
- `POST /stream` - Stream synthesized audio

### IoT Control Service (Port 8002)

- `GET /` - Check service status
- `GET /devices` - Get all device states
- `GET /device/{device_type}/{location}` - Get specific device status
- `POST /control` - Control IoT devices
- `WebSocket /ws` - WebSocket connection endpoint for device status updates

## Ollama Model Configuration

The system uses the `llama3` model by default. You can download and configure the model as follows:

```bash
# Install Ollama on the host (if not already installed)
curl -fsSL https://ollama.com/install.sh | sh

# Download llama3 model
ollama pull llama3

# Or use other models
ollama pull llama3:8b
```

You can also modify the `OLLAMA_MODEL` environment variable in the `docker-compose.yml` file to use different models.

# Pull a specific model
curl -X POST http://localhost:11434/api/pull -d '{"name": "llama3"}'

# Pull a specific size model
curl -X POST http://localhost:11434/api/pull -d '{"name": "llama3:8b"}'

## Customization and Extension

### Adding New IoT Device Types

1. Add new device types to the `device_states` dictionary in `services/iot/app.py`
2. Add corresponding processing logic to the `extract_iot_commands` and `execute_command` functions
3. Update the `controlIoTDevice` function in the ESP32 code to support new devices

### Using Different TTS Engines

The current system uses Microsoft Edge TTS as the speech synthesis engine. If you need to use other engines:

1. Modify `services/tts/app.py`, replacing Edge TTS related code
2. Update `services/tts/requirements.txt` to add necessary dependencies
3. Rebuild the TTS service container

### Optimizing the STT Model

The size of the Whisper model affects recognition quality and speed. You can adjust it by modifying the `WHISPER_MODEL` environment variable:
- `tiny` - Smallest model, fastest but lowest accuracy
- `base` - Default model, balanced speed and accuracy
- `small` - Larger model, higher accuracy but slower
- `medium` - Large model, high accuracy but requires more computing resources
- `large` - Largest model, highest accuracy but slowest

## Troubleshooting

### 1. ESP32 Cannot Connect to Server

- Check WiFi connection and network configuration
- Ensure ESP32 and Docker host are on the same network
- Check firewall settings to ensure UDP port 8000 and WebSocket port 8080 are not blocked

### 2. Speech Recognition Not Working

- Check microphone connection and I2S configuration
- Check STT service logs to confirm if audio data is being received normally
- Try adjusting recording volume or noise reduction settings

### 3. Speech Synthesis Has No Sound

- Check speaker connection and I2S configuration
- Confirm if the audio file path is correct
- Check if TTS service response is correctly received

### 4. Ollama Model Loading Failure

- Ensure sufficient disk space and memory
- Check Ollama service logs for detailed error information
- Try using a smaller model (like `llama3:8b`)

## Notes

- The system is configured for internal network use and is not recommended for direct exposure to the public internet
- There is no default security authentication; if public access is needed, please add appropriate authentication mechanisms
- ESP32 power supply should be stable to avoid interruption of recording or playback
- Communication between Docker containers depends on the Docker network; please ensure container name resolution is working properly

## License

This project is licensed under the MIT License.