import os
import logging
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from collections import deque
from fastapi import FastAPI, HTTPException, Header, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
import edge_tts
from pydub import AudioSegment
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables
AUDIO_DIR = os.getenv("AUDIO_DIR", "/app/audio")
TTS_VOICE = os.getenv("TTS_VOICE", "en-US-AriaNeural")
OUTPUT_FORMAT = os.getenv("OUTPUT_FORMAT", "mp3")

# Create audio directory
os.makedirs(AUDIO_DIR, exist_ok=True)

# Create FastAPI application
app = FastAPI(title="Text-to-Speech Service with ESP32 Support")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TTSRequest(BaseModel):
    text: str
    voice: str = TTS_VOICE
    format: str = OUTPUT_FORMAT

# ESP32设备管理
class ESP32DeviceManager:
    def __init__(self):
        self.devices: Dict[str, dict] = {}
        self.pending_tasks: Dict[str, deque] = {}
        self.active_connections: Dict[str, WebSocket] = {}
        self.polling_events: Dict[str, asyncio.Event] = {}
        
    def register_device(self, device_id: str):
        """注册ESP32设备"""
        if device_id not in self.devices:
            self.devices[device_id] = {
                "last_seen": time.time(),
                "status": "online"
            }
            self.pending_tasks[device_id] = deque(maxlen=10)
            self.polling_events[device_id] = asyncio.Event()
            logger.info(f"Registered ESP32 device: {device_id}")
    
    def add_task(self, device_id: str, task: dict):
        """添加TTS任务到设备队列"""
        if device_id not in self.devices:
            self.register_device(device_id)
        
        self.pending_tasks[device_id].append(task)
        
        # 触发轮询事件
        if device_id in self.polling_events:
            self.polling_events[device_id].set()
        
        logger.info(f"Added TTS task for device {device_id}: {task['text'][:50]}...")
        
    def get_next_task(self, device_id: str) -> Optional[dict]:
        """获取设备的下一个任务"""
        if device_id in self.pending_tasks and self.pending_tasks[device_id]:
            return self.pending_tasks[device_id].popleft()
        return None
    
    async def wait_for_task(self, device_id: str, timeout: float = 25.0) -> Optional[dict]:
        """等待新任务（用于长轮询）"""
        if device_id not in self.polling_events:
            self.register_device(device_id)
        
        # 首先检查是否已有待处理任务
        task = self.get_next_task(device_id)
        if task:
            return task
        
        # 等待新任务
        try:
            await asyncio.wait_for(
                self.polling_events[device_id].wait(),
                timeout=timeout
            )
            self.polling_events[device_id].clear()
            return self.get_next_task(device_id)
        except asyncio.TimeoutError:
            return None

device_manager = ESP32DeviceManager()

@app.get("/")
async def root():
    return {"message": "TTS Service with ESP32 Support is running"}

@app.get("/voices")
async def list_voices():
    """List all available voices"""
    try:
        voices = await edge_tts.list_voices()
        return {"voices": voices}
    except Exception as e:
        logger.error(f"Error getting voice list: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error getting voice list: {str(e)}"}
        )

@app.post("/synthesize")
async def synthesize_speech(request: TTSRequest):
    """Synthesize speech and return audio file path"""
    try:
        timestamp = int(time.time())
        filename = f"tts_{timestamp}.{request.format}"
        file_path = os.path.join(AUDIO_DIR, filename)
        
        communicate = edge_tts.Communicate(request.text, request.voice)
        await communicate.save(file_path)
        
        logger.info(f"Speech synthesized: {file_path}")
        
        return {
            "audio_path": file_path,
            "format": request.format,
            "voice": request.voice
        }
    
    except Exception as e:
        logger.error(f"Speech synthesis error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Speech synthesis error: {str(e)}"}
        )

@app.post("/esp32/synthesize")
async def esp32_synthesize(request: TTSRequest, device_id: str = Header(None, alias="X-Device-ID")):
    """合成语音并通知ESP32设备"""
    try:
        if not device_id:
            device_id = "ESP32_DEFAULT"
        
        # 生成音频
        timestamp = int(time.time())
        audio_id = f"audio_{timestamp}_{hash(request.text) % 10000}"
        
        # 合成语音
        temp_file = f"/tmp/tts_{timestamp}.mp3"
        communicate = edge_tts.Communicate(request.text, request.voice)
        await communicate.save(temp_file)
        
        # 转换为PCM
        audio = AudioSegment.from_mp3(temp_file)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        
        # 保存PCM数据
        pcm_file = os.path.join(AUDIO_DIR, f"{audio_id}.pcm")
        with open(pcm_file, 'wb') as f:
            f.write(audio.raw_data)
        
        os.remove(temp_file)
        
        # 创建任务信息
        task = {
            "audio_id": audio_id,
            "text": request.text,
            "voice": request.voice,
            "duration": len(audio) / 1000.0,
            "size": len(audio.raw_data),
            "timestamp": time.time()
        }
        
        # 添加到设备队列
        device_manager.add_task(device_id, task)
        
        logger.info(f"TTS task created for device {device_id}: {audio_id}")
        
        return {
            "status": "success",
            "audio_id": audio_id,
            "message": "Audio synthesized and queued for device"
        }
        
    except Exception as e:
        logger.error(f"ESP32 synthesis error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Synthesis error: {str(e)}"}
        )

@app.get("/esp32/poll")
async def esp32_poll(device_id: str = Header(None, alias="X-Device-ID")):
    """ESP32长轮询端点 - 等待新的TTS任务"""
    try:
        if not device_id:
            return JSONResponse(
                status_code=400,
                content={"error": "Device ID required"}
            )
        
        logger.debug(f"Device {device_id} polling for tasks")
        
        # 等待任务（最长25秒）
        task = await device_manager.wait_for_task(device_id, timeout=25.0)
        
        if task:
            logger.info(f"Returning task to device {device_id}: {task['audio_id']}")
            return {
                "has_audio": True,
                "audio_id": task["audio_id"],
                "text": task["text"][:100],  # 前100个字符
                "voice": task["voice"],
                "duration": task["duration"],
                "size": task["size"],
                "timestamp": task["timestamp"]
            }
        else:
            # 没有任务，返回204 No Content
            return Response(status_code=204)
            
    except Exception as e:
        logger.error(f"Polling error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Polling error: {str(e)}"}
        )

@app.post("/esp32/pcm")
async def esp32_pcm_direct(request: TTSRequest):
    """直接生成并返回PCM数据（向后兼容）"""
    try:
        timestamp = int(time.time())
        temp_file = f"/tmp/tts_{timestamp}.mp3"
        
        communicate = edge_tts.Communicate(request.text, request.voice)
        await communicate.save(temp_file)
        
        # 转换为PCM
        audio = AudioSegment.from_mp3(temp_file)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        
        pcm_data = audio.raw_data
        os.remove(temp_file)
        
        logger.info(f"Direct PCM stream: {len(pcm_data)} bytes")
        
        return Response(
            content=pcm_data,
            media_type="audio/pcm",
            headers={
                "Content-Length": str(len(pcm_data)),
                "X-Sample-Rate": "16000",
                "X-Channels": "1",
                "X-Bits-Per-Sample": "16"
            }
        )
        
    except Exception as e:
        logger.error(f"PCM generation error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"PCM generation error: {str(e)}"}
        )

@app.get("/esp32/audio/{audio_id}")
async def get_esp32_audio(audio_id: str):
    """获取指定ID的PCM音频数据"""
    try:
        pcm_file = os.path.join(AUDIO_DIR, f"{audio_id}.pcm")
        
        if not os.path.exists(pcm_file):
            raise HTTPException(status_code=404, detail="Audio not found")
        
        with open(pcm_file, 'rb') as f:
            pcm_data = f.read()
        
        # 可选：删除已发送的文件
        # os.remove(pcm_file)
        
        return Response(
            content=pcm_data,
            media_type="audio/pcm",
            headers={
                "Content-Length": str(len(pcm_data)),
                "X-Sample-Rate": "16000",
                "X-Channels": "1",
                "X-Bits-Per-Sample": "16",
                "X-Audio-ID": audio_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving audio {audio_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error retrieving audio: {str(e)}"}
        )

@app.websocket("/ws/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: str):
    """WebSocket端点（可选功能）"""
    await websocket.accept()
    device_manager.active_connections[device_id] = websocket
    logger.info(f"WebSocket connected: {device_id}")
    
    try:
        while True:
            data = await websocket.receive_text()
            
            if data == "ping":
                await websocket.send_text("pong")
            
    except WebSocketDisconnect:
        if device_id in device_manager.active_connections:
            del device_manager.active_connections[device_id]
        logger.info(f"WebSocket disconnected: {device_id}")

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    """获取音频文件（向后兼容）"""
    file_path = os.path.join(AUDIO_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file does not exist")
    
    return FileResponse(file_path)

# 清理旧文件的后台任务
async def cleanup_old_files():
    """定期清理旧的音频文件"""
    while True:
        try:
            current_time = time.time()
            for filename in os.listdir(AUDIO_DIR):
                file_path = os.path.join(AUDIO_DIR, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > 3600:  # 1小时
                        os.remove(file_path)
                        logger.debug(f"Removed old file: {filename}")
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")
        
        await asyncio.sleep(600)  # 每10分钟运行一次

@app.on_event("startup")
async def startup_event():
    """启动时运行的任务"""
    asyncio.create_task(cleanup_old_files())
    logger.info("TTS Service started with ESP32 support")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=False)