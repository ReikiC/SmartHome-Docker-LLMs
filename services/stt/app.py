import os
import logging
import asyncio
import socket
import time
import wave
import requests
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import uvicorn
from pydantic import BaseModel
import whisper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
AUDIO_DIR = os.getenv("AUDIO_DIR", "/app/audio")
UDP_PORT = int(os.getenv("UDP_PORT", 8000))
SAMPLE_RATE = 16000  # ESP32 recording sample rate

# Coordinator service configuration
COORDINATOR_HOST = os.getenv("COORDINATOR_HOST", "coordinator")
COORDINATOR_PORT = os.getenv("COORDINATOR_PORT", "8080")

# Create audio directory
os.makedirs(AUDIO_DIR, exist_ok=True)

# Initialize Whisper model
logger.info(f"Loading Whisper model: {WHISPER_MODEL}")
model = whisper.load_model(WHISPER_MODEL)
logger.info("Whisper model loaded")

# Create FastAPI application
app = FastAPI(title="Speech Recognition Service")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AudioRequest(BaseModel):
    audio_path: str

@app.get("/")
async def root():
    return {"message": "Speech Recognition Service is running"}

@app.post("/transcribe")
async def transcribe_audio(request: AudioRequest):
    """Transcribe audio file at specified path"""
    try:
        audio_path = request.audio_path
        
        if not os.path.exists(audio_path):
            return JSONResponse(
                status_code=404,
                content={"error": f"Audio file does not exist: {audio_path}"}
            )
        
        # Use Whisper for transcription
        logger.info(f"Starting transcription: {audio_path}")
        result = model.transcribe(audio_path)
        transcription = result["text"]
        logger.info(f"Transcription complete: {transcription}")
        
        return {"text": transcription}
    
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Transcription error: {str(e)}"}
        )

@app.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    """Upload audio file and transcribe"""
    try:
        # Save uploaded file
        filename = f"upload_{int(time.time())}.wav"
        file_path = os.path.join(AUDIO_DIR, filename)
        
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # Use Whisper for transcription
        result = model.transcribe(file_path)
        transcription = result["text"]
        
        return {
            "text": transcription,
            "audio_path": file_path
        }
    
    except Exception as e:
        logger.error(f"Error processing uploaded audio: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Processing error: {str(e)}"}
        )

#!/usr/bin/env python3
"""
STT服务的device_id提取逻辑修复
修改 services/stt/app.py 中的 upload_pcm 函数
"""

# 在 services/stt/app.py 中，找到 upload_pcm 函数并修改 device_id 提取部分：

@app.post("/upload_pcm")
async def upload_pcm_audio(
    file: UploadFile = File(...),
    sample_rate: int = 16000,
    channels: int = 1,
    sample_width: int = 2,
    device_id: str = None
):
    """Upload PCM audio data and transcribe
    
    This endpoint is specifically for ESP32 devices that send raw PCM data.
    Default parameters match ESP32 recording settings.
    """
    try:
        # Read PCM data
        pcm_data = await file.read()
        logger.info(f"Received PCM data: {len(pcm_data)} bytes")
        
        # Extract device_id from filename if provided
        if not device_id and file.filename:
            # 改进的device_id提取逻辑
            # 文件名格式: "esp32_ESP32_VOICE_01_123456.pcm"
            if file.filename.startswith("esp32_") and file.filename.endswith(".pcm"):
                # 移除前缀 "esp32_" 和后缀 ".pcm"
                filename_core = file.filename[6:-4]  # 从第6个字符开始，去掉最后4个字符(.pcm)
                
                # 找到最后一个下划线的位置（时间戳之前）
                last_underscore = filename_core.rfind('_')
                
                if last_underscore > 0:
                    # 提取设备ID（时间戳之前的所有内容）
                    device_id = filename_core[:last_underscore]
                    timestamp = filename_core[last_underscore + 1:]
                    
                    logger.info(f"Extracted device_id: {device_id}, timestamp: {timestamp}")
                else:
                    # 如果没有找到时间戳分隔符，使用整个核心部分作为device_id
                    device_id = filename_core
                    logger.info(f"Extracted device_id: {device_id} (no timestamp found)")
            else:
                # 兼容旧格式：尝试简单的分割
                parts = file.filename.split('_')
                if len(parts) >= 2 and parts[0] == "esp32":
                    # 对于旧格式，组合所有非时间戳部分
                    # 假设最后一部分（去掉.pcm）是时间戳
                    if parts[-1].endswith('.pcm'):
                        parts[-1] = parts[-1][:-4]  # 去掉.pcm
                    
                    # 如果最后一部分看起来像时间戳（全是数字），则排除它
                    if parts[-1].isdigit():
                        device_id = '_'.join(parts[1:-1])
                    else:
                        device_id = '_'.join(parts[1:])
                    
                    logger.info(f"Extracted device_id (legacy format): {device_id}")
        
        # 记录提取的或传入的device_id
        if device_id:
            logger.info(f"Using device_id: {device_id}")
        else:
            logger.warning("No device_id found in filename or parameters")
        
        # Save as WAV file for Whisper
        timestamp = int(time.time())
        filename = f"pcm_upload_{timestamp}.wav"
        file_path = os.path.join(AUDIO_DIR, filename)
        
        # Convert PCM to WAV
        with wave.open(file_path, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm_data)
        
        logger.info(f"Saved PCM as WAV: {file_path}")
        
        # Use Whisper for transcription
        result = model.transcribe(file_path)
        transcription = result["text"].strip()
        
        logger.info(f"Transcription: {transcription}")
        
        # Send to Coordinator for processing if transcription is not empty
        if transcription and transcription.lower() not in ["", " ", "blank"]:
            await send_to_coordinator(transcription, device_id)
        
        return {
            "text": transcription,
            "audio_path": file_path,
            "device_id": device_id  # 返回识别到的device_id
        }
    
    except Exception as e:
        logger.error(f"Error processing PCM audio: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Processing error: {str(e)}"}
        )

# WebSocket endpoint for real-time audio streaming (future feature)
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time audio streaming"""
    await websocket.accept()
    logger.info("WebSocket client connected")
    
    try:
        while True:
            # Receive audio data
            data = await websocket.receive_bytes()
            
            # Process audio chunk (placeholder for future implementation)
            # For now, just echo back a message
            await websocket.send_text("Audio chunk received")
            
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")

# UDP server for real-time audio (alternative to WebSocket)
async def udp_server():
    """UDP server for receiving audio streams"""
    loop = asyncio.get_event_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: UDPServerProtocol(),
        local_addr=('0.0.0.0', UDP_PORT)
    )
    
    logger.info(f"UDP server listening on port {UDP_PORT}")
    
    try:
        await asyncio.sleep(3600)  # Run for 1 hour
    finally:
        transport.close()

class UDPServerProtocol:
    def connection_made(self, transport):
        self.transport = transport
    
    def datagram_received(self, data, addr):
        # Process received audio data
        logger.debug(f"Received {len(data)} bytes from {addr}")
        # TODO: Implement audio processing

# Send transcribed text to Coordinator
async def send_to_coordinator(text: str, device_id: str = None):
    """Send transcribed text to coordinator for processing"""
    try:
        coordinator_url = f"http://{COORDINATOR_HOST}:{COORDINATOR_PORT}/process_text"
        
        payload = {
            "text": text,
            "source": "stt_service",
            "timestamp": time.time()
        }
        
        # Add device_id if provided
        if device_id:
            payload["device_id"] = device_id
            payload["location"] = "living_room"  # Default location
        
        logger.info(f"Sending to coordinator: {text[:50]}...")
        
        response = requests.post(coordinator_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Coordinator processed successfully")
            
            # If there's an audio_id in the response, it means TTS was generated
            if "audio_id" in result:
                logger.info(f"TTS audio generated: {result['audio_id']}")
        else:
            logger.warning(f"Coordinator returned status {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error sending to coordinator: {str(e)}")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("STT Service started")
    logger.info(f"Whisper model: {WHISPER_MODEL}")
    logger.info(f"Audio directory: {AUDIO_DIR}")
    logger.info(f"Coordinator: http://{COORDINATOR_HOST}:{COORDINATOR_PORT}")
    
    # Start UDP server in background (optional)
    # asyncio.create_task(udp_server())

# Cleanup old audio files
async def cleanup_old_files():
    """Remove audio files older than 1 hour"""
    while True:
        try:
            current_time = time.time()
            for filename in os.listdir(AUDIO_DIR):
                file_path = os.path.join(AUDIO_DIR, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > 3600:  # 1 hour
                        os.remove(file_path)
                        logger.debug(f"Removed old file: {filename}")
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")
        
        await asyncio.sleep(600)  # Run every 10 minutes

# Start cleanup task
@app.on_event("startup")
async def start_cleanup():
    asyncio.create_task(cleanup_old_files())

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)