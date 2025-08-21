import os
import json
import logging
import asyncio
import aiohttp
import websockets
import time
import re
import uuid
from enum import Enum
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Response
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import requests
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
load_dotenv() 

# 导入系统配置
from system_config import (
    ENVIRONMENTAL_DATA,
    get_comprehensive_system_prompt,
    extract_iot_commands_enhanced,
    determine_expression_enhanced,
    get_scene_actions,
    update_sensor_data,
    get_all_sensors_data,
    SCENE_MODES
)
from llm_iot_extractor import LLMIoTExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API Mode Enum
class APIMode(Enum):
    LOCAL_OLLAMA = "local"
    REMOTE_API = "api"

# Default configuration (will be overridden by config file if exists)
DEFAULT_API_MODE = "api"  # Default mode if no config file exists
DEFAULT_LOCAL_MODEL = "llama3.2:3b"
DEFAULT_REMOTE_MODEL = "llama3.2:3b"

# Local Ollama configuration
OLLAMA_HOST = "ollama"
OLLAMA_PORT = "11434"
OLLAMA_SCHEME = "http"

# Remote API configuration (protected by .env)
REMOTE_API_URL = "https://chat.cetools.org/api/chat/completions"
REMOTE_API_KEY = os.getenv("REMOTE_API_KEY", "")  # Must be set in .env

# Other services configuration
STT_HOST = "stt-service"
STT_PORT = "8000"
TTS_HOST = "tts-service"
TTS_PORT = "8001"
TTS_VOICE = "en-US-AriaNeural"
IOT_HOST = "iot-control"
IOT_PORT = "8002"

# Early configuration loading function
def load_early_config():
    """Load configuration from file early in the startup process"""
    config_file = "/app/config/model_preferences.json"
    
    # Default values
    api_mode = DEFAULT_API_MODE
    default_model = DEFAULT_REMOTE_MODEL if DEFAULT_API_MODE == "api" else DEFAULT_LOCAL_MODEL
    
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                preferences = json.load(f)
            
            # Get mode from config file
            saved_mode = preferences.get("current_mode")
            if saved_mode and saved_mode in ["local", "api"]:
                # Check if API key is available for API mode
                if saved_mode == "api" and not REMOTE_API_KEY:
                    logger.warning("⚠️ Config requests API mode but REMOTE_API_KEY not set, falling back to default")
                    api_mode = DEFAULT_API_MODE
                else:
                    api_mode = saved_mode
                    logger.info(f"📂 Loaded API mode from config: {api_mode}")
                    
                    # Also load the saved model for this mode
                    saved_model = preferences.get("current_model")
                    if saved_model:
                        default_model = saved_model
                        logger.info(f"📂 Loaded default model from config: {default_model}")
        else:
            logger.info(f"📄 No config file found, using default API mode: {api_mode}")
            
    except Exception as e:
        logger.error(f"❌ Error loading early config: {str(e)}, using defaults")
    
    return api_mode, default_model

# Load configuration early
API_MODE, INITIAL_MODEL = load_early_config()
OLLAMA_MODEL = INITIAL_MODEL if API_MODE == "local" else DEFAULT_LOCAL_MODEL
REMOTE_API_MODEL = INITIAL_MODEL if API_MODE == "api" else DEFAULT_REMOTE_MODEL

# Build endpoint based on mode
if API_MODE == "api":
    OLLAMA_ENDPOINT = REMOTE_API_URL
    if not REMOTE_API_KEY:
        logger.warning("⚠️ REMOTE_API_KEY not set in environment. API mode may not work properly.")
else:
    if OLLAMA_PORT:
        OLLAMA_ENDPOINT = f"{OLLAMA_SCHEME}://{OLLAMA_HOST}:{OLLAMA_PORT}"
    else:
        OLLAMA_ENDPOINT = f"{OLLAMA_SCHEME}://{OLLAMA_HOST}"

logger.info(f"🚀 Starting in {API_MODE} mode with endpoint: {OLLAMA_ENDPOINT}")

# Enhanced ModelManager with API mode support
class EnhancedModelManager:
    def __init__(self):
        # Use the early-loaded configuration
        self.current_mode = APIMode(API_MODE)
        self.current_model = REMOTE_API_MODEL if self.current_mode == APIMode.REMOTE_API else OLLAMA_MODEL
        self.available_models = []
        self.model_info = {}
        self.last_model_check = 0
        self.model_check_interval = 30  # 30秒检查一次可用模型
        
        # API headers for remote mode
        self.api_headers = {}
        if self.current_mode == APIMode.REMOTE_API and REMOTE_API_KEY:
            self.api_headers = {
                "Authorization": f"Bearer {REMOTE_API_KEY}",
                "Content-Type": "application/json"
            }
        
        # 配置文件路径
        self.config_dir = "/app/config"
        self.config_file = os.path.join(self.config_dir, "model_preferences.json")
        
        # 验证配置文件中的设置是否与当前设置一致
        self._validate_config_consistency()
    
    def _validate_config_consistency(self):
        """验证配置文件与当前运行状态的一致性"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    preferences = json.load(f)
                
                saved_mode = preferences.get("current_mode")
                saved_model = preferences.get("current_model")
                
                # 如果配置文件中的模式与当前模式不一致，更新配置文件
                if saved_mode != self.current_mode.value:
                    logger.info(f"🔄 Updating config file mode from {saved_mode} to {self.current_mode.value}")
                    self._save_preferences_to_file()
                
                # 确保模型设置正确
                if saved_model and saved_model != self.current_model:
                    logger.info(f"🔄 Model mismatch detected, using: {self.current_model}")
        
        except Exception as e:
            logger.error(f"❌ Error validating config consistency: {str(e)}")
    
    def get_current_mode(self):
        return self.current_mode.value
    
    def switch_mode(self, mode: str):
        """Switch between local and API mode"""
        if mode not in ["local", "api"]:
            raise ValueError("Mode must be 'local' or 'api'")
        
        # Check API key for API mode
        if mode == "api" and not REMOTE_API_KEY:
            raise ValueError("Cannot switch to API mode: REMOTE_API_KEY not configured")
        
        self.current_mode = APIMode.LOCAL_OLLAMA if mode == "local" else APIMode.REMOTE_API
        
        # Update model and headers based on mode
        if self.current_mode == APIMode.REMOTE_API:
            self.current_model = REMOTE_API_MODEL
            self.api_headers = {
                "Authorization": f"Bearer {REMOTE_API_KEY}",
                "Content-Type": "application/json"
            }
        else:
            self.current_model = OLLAMA_MODEL
            self.api_headers = {}

        # 更新全局 llm_extractor 的配置（如果已初始化）
        global llm_extractor
        if llm_extractor is not None:
            llm_extractor.model_name = self.current_model
            llm_extractor.api_headers = self.api_headers
            llm_extractor.ollama_endpoint = OLLAMA_ENDPOINT
            logger.info(f"✅ Updated LLM extractor for {mode} mode")
        
        # Save mode preference
        self._save_preferences_to_file()
        
        logger.info(f"✅ Switched to {mode} mode with model {self.current_model}")
        return True
    
    def _ensure_config_directory(self):
        """确保配置目录存在"""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create config directory: {str(e)}")
            return False
    
    def _save_preferences_to_file(self):
        """自动保存模型偏好设置到配置文件"""
        try:
            if not self._ensure_config_directory():
                return False
            
            # 构建配置数据
            preferences = {
                "current_mode": self.current_mode.value,
                "current_model": self.current_model,
                "available_models": [
                    {
                        "name": model_name,
                        "info": self.model_info.get(model_name, {})
                    }
                    for model_name in self.available_models
                ],
                "last_updated": time.time(),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            }
            
            # 写入文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(preferences, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Model preferences saved to {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save preferences: {str(e)}")
            return False
    
    async def get_available_models(self, force_refresh=False):
        """获取可用的模型列表 - 支持两种模式"""
        current_time = time.time()
        
        # 检查是否需要刷新模型列表
        if not force_refresh and self.available_models and \
           (current_time - self.last_model_check) < self.model_check_interval:
            return self.available_models
        
        try:
            if self.current_mode == APIMode.REMOTE_API:
                # API模式：返回预定义的模型列表
                self.available_models = ["llama3.2:3b", "llama3.1:70b", "gemma2:latest", "gemma3:latest","llama3:8b"]
                
                # 设置模型信息
                for model in self.available_models:
                    self.model_info[model] = {
                        "name": model,
                        "modified_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "size": 0,  # API模式不显示大小
                        "details": {"format": "api", "family": model.split(":")[0]}
                    }
                
                logger.info(f"📋 Available API models: {self.available_models}")
                
            else:
                # 本地模式：从Ollama获取模型列表
                response = requests.get(f"{OLLAMA_ENDPOINT}/api/tags", timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])
                    
                    self.available_models = []
                    for model in models:
                        model_name = model.get("name", "")
                        if model_name:
                            self.available_models.append(model_name)
                            self.model_info[model_name] = {
                                "name": model_name,
                                "modified_at": model.get("modified_at", ""),
                                "size": model.get("size", 0),
                                "details": model.get("details", {})
                            }
                    
                    logger.info(f"📋 Found {len(self.available_models)} local models")
                else:
                    logger.error(f"❌ Failed to get models from Ollama: HTTP {response.status_code}")
                    
        except Exception as e:
            logger.error(f"❌ Error getting available models: {str(e)}")
        
        self.last_model_check = current_time
        self._save_preferences_to_file()
        
        return self.available_models
    
    def get_current_model(self):
        """获取当前使用的模型"""
        return self.current_model
    
    def set_current_model(self, model_name):
        """设置当前使用的模型"""
        self.current_model = model_name
        self._save_preferences_to_file()
        logger.info(f"✅ Current model set to: {model_name}")
        return True
    
    def get_model_info(self, model_name):
        """获取模型详细信息"""
        return self.model_info.get(model_name, {})
    
    def get_config_status(self):
        """获取配置文件状态"""
        config_exists = os.path.exists(self.config_file)
        config_info = {
            "config_exists": config_exists,
            "config_file_path": self.config_file,
            "config_dir": self.config_dir,
            "config_size_bytes": 0,
            "config_modified": None,
            "total_available_models": len(self.available_models),
            "current_model": self.current_model,
            "current_mode": self.current_mode.value
        }
        
        if config_exists:
            try:
                stat = os.stat(self.config_file)
                config_info["config_size_bytes"] = stat.st_size
                config_info["config_modified"] = time.strftime(
                    "%Y-%m-%d %H:%M:%S", 
                    time.localtime(stat.st_mtime)
                )
            except Exception as e:
                logger.error(f"Error getting config file stats: {str(e)}")
        
        return config_info
    
    def reset_preferences(self):
        """重置偏好设置到默认值"""
        try:
            # 删除配置文件
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
                logger.info(f"🗑️ Removed config file: {self.config_file}")
            
            # 重置为默认值
            self.current_mode = APIMode(DEFAULT_API_MODE)
            self.current_model = DEFAULT_REMOTE_MODEL if self.current_mode == APIMode.REMOTE_API else DEFAULT_LOCAL_MODEL
            self.available_models = []
            self.model_info = {}
            
            logger.info("✅ Preferences reset to defaults")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to reset preferences: {str(e)}")
            return False

# Initialize model manager
model_manager = EnhancedModelManager()

# 在 EnhancedModelManager 初始化后添加
llm_extractor = LLMIoTExtractor(
    ollama_endpoint=OLLAMA_ENDPOINT,
    model_name=model_manager.current_model,
    api_headers=model_manager.api_headers
)

# Global variables
startup_time = time.time()
environmental_data = ENVIRONMENTAL_DATA  # 使用导入的数据

# Create FastAPI application
app = FastAPI(title="AI Voice Assistant Coordinator Service - Enhanced with API Mode")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connected clients and devices
connected_clients = {}
registered_devices = {}
user_contexts = {}

# Request models
class AudioRequest(BaseModel):
    audio_path: str

# 1. 修改 TextRequest 模型，添加 device_id 字段
class TextRequest(BaseModel):
    text: str
    device_id: Optional[str] = None  # 新增字段
    source: Optional[str] = None     # 新增字段
    location: Optional[str] = "living_room"
    timestamp: Optional[float] = None

class ModelSwitchRequest(BaseModel):
    model_name: str

class ModelPullRequest(BaseModel):
    model_name: str

class ContextualRequest(BaseModel):
    text: str
    user_context: Optional[Dict[str, Any]] = None
    location: str = "living_room"
    device_id: Optional[str] = None

class SceneRequest(BaseModel):
    scene_name: str
    location: Optional[str] = None

class DeviceRegistration(BaseModel):
    device_info: Dict[str, Any]
    capabilities: List[str]

class ConfigResetRequest(BaseModel):
    confirm: bool = False

class ConfigExportRequest(BaseModel):
    export_path: Optional[str] = None

class ModeSwitchRequest(BaseModel):
    mode: str  # "local" or "api"

async def process_with_llm(text_input: str, context: Dict = None, location: str = "living_room"):
    """Process text with LLM based on current mode"""
    try:
        # 获取所有房间的实时状态并添加到上下文
        enhanced_context = context or {}
        
        # 尝试从IoT服务获取所有传感器的最新数据
        try:
            sensors_response = requests.get(f"http://{IOT_HOST}:{IOT_PORT}/sensors", timeout=2)
            if sensors_response.status_code == 200:
                all_sensors = sensors_response.json().get("sensors", {})
                # 更新本地的ENVIRONMENTAL_DATA
                ENVIRONMENTAL_DATA["sensors"].update(all_sensors)
                enhanced_context["real_time_sensors"] = all_sensors
        except Exception as e:
            logger.warning(f"Could not fetch real-time sensor data: {e}")
        
        # 获取所有设备状态
        try:
            devices_response = requests.get(f"http://{IOT_HOST}:{IOT_PORT}/devices", timeout=2)
            if devices_response.status_code == 200:
                all_devices = devices_response.json().get("devices", {})
                enhanced_context["device_states"] = all_devices
        except Exception as e:
            logger.warning(f"Could not fetch device states: {e}")
        
        # 生成包含所有房间信息的系统提示词
        system_prompt = get_comprehensive_system_prompt(enhanced_context, location)
        
        # 继续原有的处理逻辑...
        if model_manager.current_mode == APIMode.REMOTE_API:
            # Use OpenAI-compatible API format
            payload = {
                "model": model_manager.current_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text_input}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            response = requests.post(
                OLLAMA_ENDPOINT,
                json=payload,
                headers=model_manager.api_headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                return "I apologize, I couldn't process your request."
                
        else:
            # Use original Ollama format
            payload = {
                "model": model_manager.current_model,
                "prompt": f"{system_prompt}\n\nUser: {text_input}\n\nAssistant:",
                "stream": False
            }
            
            response = requests.post(
                f"{OLLAMA_ENDPOINT}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get("response", "I apologize, I couldn't process your request.")
            else:
                logger.error(f"Ollama request failed: {response.status_code}")
                return "I apologize, I couldn't process your request."
                
    except Exception as e:
        logger.error(f"Error processing with LLM: {str(e)}")
        return "I apologize, an error occurred while processing your request."

def is_valid_action(device_type: str, action: str) -> bool:
    """检查动作是否适用于设备类型"""
    valid_actions = {
        "light": ["on", "off", "brighten", "dim"],
        "fan": ["on", "off", "speed_up", "speed_down"],
        "ac": ["on", "off", "temp_up", "temp_down"],
        "curtain": ["on", "off"]  # on=open, off=close
    }
    
    return action in valid_actions.get(device_type, [])

# 2. 修改 process_text_with_enhanced_llm 函数签名
async def process_text_with_enhanced_llm(
    text_input: str,
    user_context: str = None,
    location: str = "living_room",
    device_id: str = None  # 新增参数
):
    """Enhanced text processing with current model and all features"""
    
    # Get current model
    current_model = model_manager.get_current_model()
    
    # 1. Generate system prompt
    system_prompt = get_comprehensive_system_prompt(user_context, location)
    
    # 2. Extract IoT commands
    # iot_commands = extract_iot_commands_enhanced(text_input, location) # Old version
    # 确保使用最新的模型配置
    llm_extractor.model_name = model_manager.current_model
    llm_extractor.api_headers = model_manager.api_headers
    llm_extractor.ollama_endpoint = OLLAMA_ENDPOINT
    
    try:
        iot_commands = llm_extractor.extract_iot_commands_with_llm(text_input, location)
        logger.info(f"🤖 LLM extracted {len(iot_commands)} IoT commands")
    except Exception as e:
        logger.error(f"LLM extraction failed: {e}, using empty command list")
        iot_commands = []
    
    # 3. Execute IoT commands
    iot_results = []
    if iot_commands:
        try:
            iot_url = f"http://{IOT_HOST}:{IOT_PORT}/control"
            # 正确格式：将所有命令放在commands数组中
            iot_response = requests.post(iot_url, json={"commands": iot_commands})
            
            if iot_response.status_code == 200:
                iot_results = iot_response.json().get("results", [])
            else:
                iot_results = [{"error": f"IoT command failed: {iot_response.text}"}]
        except Exception as e:
            iot_results = [{"error": f"IoT service error: {str(e)}"}]
    
    # 4. Generate AI response using current model
    # 创建增强的上下文，包含IoT执行结果
    enhanced_context = {
        "iot_commands": iot_commands,  # 执行的命令
        "iot_results": iot_results,     # 执行结果
    }

    # 如果有user_context，合并进去
    if user_context:
        if isinstance(user_context, dict):
            enhanced_context.update(user_context)
        else:
            enhanced_context["user_info"] = user_context

    ai_response = await process_with_llm(text_input, enhanced_context, location)

    # 4.5 清理AI响应中的markdown标记（新增）
    # 去除所有的markdown格式符号，让TTS读起来更自然
    cleaned_response = ai_response
    # 去除加粗标记
    cleaned_response = cleaned_response.replace("**", "")
    # 去除斜体标记
    cleaned_response = cleaned_response.replace("*", "")
    
    # 5. Determine expression/emotion
    expression = determine_expression_enhanced(text_input, cleaned_response, iot_commands)
    
    # 6. Generate TTS
    audio_url = None
    audio_path = None
    audio_id = None  # 新增字段用于ESP32
    
    try:
        # 根据是否有 device_id 选择不同的端点
        if device_id:
            # ESP32设备：使用专门的端点
            tts_url = f"http://{TTS_HOST}:{TTS_PORT}/esp32/synthesize"
            tts_payload = {
                "text": cleaned_response,
                "voice": TTS_VOICE,
                "format": "pcm"  # ESP32使用PCM格式
            }
            headers = {
                "X-Device-ID": device_id
            }
            
            logger.info(f"🔊 Requesting TTS for ESP32 device {device_id}: {cleaned_response[:50]}...")
            tts_response = requests.post(tts_url, json=tts_payload, headers=headers, timeout=10)
            
            if tts_response.status_code == 200:
                response_data = tts_response.json()
                audio_id = response_data.get("audio_id")
                logger.info(f"✅ TTS task created for ESP32: {audio_id}")
        else:
            # Web客户端：使用原有端点
            tts_url = f"http://{TTS_HOST}:{TTS_PORT}/synthesize"
            tts_payload = {
                "text": cleaned_response,
                "voice": TTS_VOICE,
                "format": "mp3"
            }
            
            logger.info(f"🔊 Requesting TTS for web client: {cleaned_response[:50]}...")
            tts_response = requests.post(tts_url, json=tts_payload, timeout=10)
            
            if tts_response.status_code == 200:
                audio_data = tts_response.json()
                audio_path = audio_data.get("audio_path", "")
                
                if audio_path:
                    audio_filename = audio_path.split('/')[-1]
                    audio_url = f"http://{TTS_HOST}:{TTS_PORT}/audio/{audio_filename}"
                    logger.info(f"✅ TTS generated successfully: {audio_url}")
                else:
                    logger.warning("TTS response missing audio_path")
        
        if tts_response.status_code != 200:
            logger.error(f"TTS request failed with status {tts_response.status_code}")
            logger.error(f"TTS error response: {tts_response.text}")
            
    except requests.exceptions.Timeout:
        logger.error("TTS request timeout")
    except Exception as e:
        logger.error(f"TTS generation error: {str(e)}")
    
    # 7. 保存配置
    config_info = model_manager.get_config_status()
    
    # 构建返回结果
    result = {
        "input_text": text_input,
        "ai_response": cleaned_response,
        "expression": expression,
        "iot_commands": iot_commands,
        "iot_results": iot_results,
        "location": location,
        "user_context": user_context,
        "model_used": current_model,
        "model_info": model_manager.get_model_info(current_model),
        "config_file_info": {
            "config_updated": config_info["config_exists"],
            "config_file_path": config_info["config_file_path"]
        }
    }
    
    # 根据设备类型添加不同的音频信息
    if device_id:
        result["device_id"] = device_id
        result["audio_id"] = audio_id
        result["audio_format"] = "pcm"
    else:
        result["audio_path"] = audio_path
        result["audio_url"] = audio_url
        result["audio_format"] = "mp3"
    
    return result

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with API mode info"""
    return {
        "service": "AI Voice Assistant Coordinator - Enhanced",
        "version": "3.0",
        "mode": model_manager.get_current_mode(),
        "model": model_manager.current_model,
        "features": [
            "Voice recognition (STT)",
            "Text-to-Speech (TTS)", 
            "IoT device control",
            "Natural language processing",
            "Multi-language support",
            "API mode switching"
        ],
        "api_mode": {
            "current": model_manager.get_current_mode(),
            "available": ["local", "api"],
            "endpoint": OLLAMA_ENDPOINT if model_manager.current_mode == APIMode.REMOTE_API else f"{OLLAMA_SCHEME}://{OLLAMA_HOST}:{OLLAMA_PORT}"
        }
    }

@app.get("/health")
async def health_check():
    """Enhanced health check with mode info"""
    return {
        "status": "healthy",
        "mode": model_manager.get_current_mode(),
        "model": model_manager.current_model,
        "services": {
            "stt": "connected",
            "tts": "connected",
            "iot": "connected",
            "llm": model_manager.get_current_mode()
        },
        "uptime": time.time() - startup_time,
        "timestamp": time.time()
    }

# API Mode Management Endpoints

@app.get("/api/mode")
async def get_api_mode():
    """Get current API mode"""
    return {
        "mode": model_manager.get_current_mode(),
        "model": model_manager.current_model,
        "endpoint": OLLAMA_ENDPOINT if model_manager.current_mode == APIMode.REMOTE_API else f"{OLLAMA_SCHEME}://{OLLAMA_HOST}:{OLLAMA_PORT}",
        "available_modes": ["local", "api"],
        "api_key_configured": bool(REMOTE_API_KEY) if model_manager.current_mode == APIMode.REMOTE_API else None
    }

@app.post("/api/mode/switch")
async def switch_api_mode(request: ModeSwitchRequest):
    """Switch between local and API mode - requires service restart"""
    try:
        mode = request.mode
        if not mode:
            return JSONResponse(
                status_code=400,
                content={"error": "Mode parameter required"}
            )
        
        # Check if mode is actually changing
        current_mode = model_manager.get_current_mode()
        if mode == current_mode:
            return {
                "success": False,
                "mode": current_mode,
                "message": f"Already in {mode} mode, no restart needed"
            }
        
        success = model_manager.switch_mode(mode)
        
        if success:
            # Save configuration before restart
            logger.info(f"🔄 Mode switch successful, preparing to restart service...")
            
            # Give a response before restarting
            response_data = {
                "success": True,
                "mode": mode,
                "model": model_manager.current_model,
                "message": f"Switched to {mode} mode. Service will restart in 2 seconds...",
                "restart_required": True,
                "endpoint": REMOTE_API_URL if mode == "api" else f"{OLLAMA_SCHEME}://{OLLAMA_HOST}:{OLLAMA_PORT}"
            }
            
            # Schedule restart after response is sent
            async def delayed_restart():
                await asyncio.sleep(2)  # Give time for response to be sent
                logger.info("🔄 Restarting service to apply mode change...")
                
                # Different restart methods based on environment
                import os
                import sys
                import signal
                
                # Method 1: For Docker containers - exit and let Docker restart
                if os.environ.get('DOCKER_CONTAINER'):
                    logger.info("🐳 Docker environment detected, exiting for container restart...")
                    os._exit(0)  # Exit cleanly, Docker will restart
                
                # Method 2: For standalone Python - restart the process
                else:
                    logger.info("🔄 Standalone environment, restarting Python process...")
                    try:
                        # Flush all outputs
                        sys.stdout.flush()
                        sys.stderr.flush()
                        
                        # Replace current process with new one
                        os.execv(sys.executable, ['python'] + sys.argv)
                    except Exception as e:
                        logger.error(f"Failed to restart: {e}")
                        # Fallback: just exit
                        sys.exit(0)
            
            # Start restart task in background
            asyncio.create_task(delayed_restart())
            
            return response_data
            
        else:
            return JSONResponse(
                status_code=500,
                content={"error": "Failed to switch mode"}
            )
            
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )
    except Exception as e:
        logger.error(f"Error switching mode: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Internal error: {str(e)}"}
        )

# Model Management Endpoints

@app.get("/models")
async def get_available_models():
    """获取所有可用的模型 - 支持两种模式"""
    try:
        models = await model_manager.get_available_models(force_refresh=True)
        current_model = model_manager.get_current_model()
        config_status = model_manager.get_config_status()
        
        model_list = []
        for model_name in models:
            model_info = model_manager.get_model_info(model_name)
            model_list.append({
                "name": model_name,
                "size": model_info.get("size", 0),
                "size_mb": round(model_info.get("size", 0) / (1024 * 1024), 1) if model_info.get("size", 0) > 0 else 0,
                "modified_at": model_info.get("modified_at", ""),
                "is_current": model_name == current_model,
                "details": model_info.get("details", {})
            })
        
        return {
            "current_model": current_model,
            "current_mode": model_manager.get_current_mode(),
            "available_models": model_list,
            "total_models": len(models),
            "config_file_info": {
                "exists": config_status["config_exists"],
                "path": config_status["config_file_path"],
                "size_bytes": config_status["config_size_bytes"],
                "last_modified": config_status["config_modified"]
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting models: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error getting models: {str(e)}"}
        )

@app.get("/models/current")
async def get_current_model():
    """获取当前使用的模型"""
    return {
        "current_model": model_manager.get_current_model(),
        "mode": model_manager.get_current_mode()
    }

@app.post("/models/switch")
async def switch_model(request: ModelSwitchRequest):
    """切换当前使用的模型"""
    try:
        logger.info(f"🔄 Attempting to switch to model: {request.model_name}")
        
        # 先获取最新的模型列表
        available_models = await model_manager.get_available_models(force_refresh=True)
        
        if request.model_name not in available_models:
            return JSONResponse(
                status_code=404,
                content={
                    "error": f"Model not found: {request.model_name}",
                    "available_models": available_models
                }
            )
        
        # 获取切换前的状态
        old_model = model_manager.get_current_model()
        config_status_before = model_manager.get_config_status()
        
        # 切换模型（会自动保存配置文件）
        success = model_manager.set_current_model(request.model_name)
        
        if success:
            # 获取切换后的配置状态
            config_status_after = model_manager.get_config_status()
            
            # 测试新模型是否正常工作
            test_result = await test_model_functionality(request.model_name)
            
            if test_result["success"]:
                # 广播模型切换事件到所有连接的客户端
                await broadcast_model_switch(request.model_name)
                
                logger.info(f"✅ Successfully switched from {old_model} to {request.model_name}")
                
                return {
                    "success": True,
                    "message": f"Successfully switched to model: {request.model_name}",
                    "old_model": old_model,
                    "current_model": request.model_name,
                    "test_result": test_result,
                    "config_file_info": {
                        "config_updated": True,
                        "config_file_path": config_status_after["config_file_path"],
                        "before_switch": config_status_before,
                        "after_switch": config_status_after
                    }
                }
            else:
                # 如果测试失败，回滚到原模型
                model_manager.set_current_model(old_model)
                
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": f"Model test failed: {test_result.get('error', 'Unknown error')}",
                        "model_name": request.model_name,
                        "reverted_to": old_model
                    }
                )
        else:
            return JSONResponse(
                status_code=500,
                content={"error": f"Failed to switch model to {request.model_name}"}
            )
            
    except Exception as e:
        logger.error(f"Error switching model: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error switching model: {str(e)}"}
        )

@app.post("/models/pull")
async def pull_model(request: ModelPullRequest):
    """下载新模型 - 仅支持本地模式"""
    if model_manager.current_mode == APIMode.REMOTE_API:
        return JSONResponse(
            status_code=400,
            content={"error": "Model pulling is only available in local mode"}
        )
    
    try:
        model_name = request.model_name
        logger.info(f"📥 Starting to pull model: {model_name}")
        
        ollama_url = f"{OLLAMA_ENDPOINT}/api/pull"
        pull_payload = {"name": model_name}
        
        response = requests.post(
            ollama_url,
            json=pull_payload,
            timeout=600  # 10 minutes for large models
        )
        
        if response.status_code == 200:
            logger.info(f"✅ Successfully pulled model: {model_name}")
            
            # Refresh model list
            await model_manager.get_available_models(force_refresh=True)
            
            # Test the model works
            test_result = await test_model_functionality(model_name)
            
            return {
                "success": True,
                "message": f"Model {model_name} downloaded successfully",
                "model_name": model_name,
                "test_result": test_result
            }
        else:
            error_text = response.text
            logger.error(f"❌ Model pull failed: HTTP {response.status_code}")
            
            return JSONResponse(
                status_code=response.status_code,
                content={
                    "success": False,
                    "error": f"Failed to download model: {error_text}",
                    "model_name": model_name
                }
            )
            
    except requests.exceptions.Timeout:
        logger.error(f"❌ Timeout pulling model {model_name}")
        return JSONResponse(
            status_code=408,
            content={
                "success": False,
                "error": "Model download timeout (10 minutes exceeded)",
                "model_name": model_name
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Error pulling model {model_name}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "model_name": model_name
            }
        )

@app.get("/models/config/status")
async def get_config_status():
    """获取配置文件状态"""
    try:
        config_status = model_manager.get_config_status()
        
        return {
            "success": True,
            "config_status": config_status,
            "message": "Configuration status retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error getting config status: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error getting config status: {str(e)}"}
        )

@app.post("/models/config/save")
async def save_config():
    """手动保存当前配置"""
    try:
        model_manager._save_preferences_to_file()
        config_info = model_manager.get_config_status()
        
        return {
            "success": True,
            "message": "Configuration saved successfully",
            "config_info": config_info
        }
    except Exception as e:
        logger.error(f"Error saving config: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error saving config: {str(e)}"}
        )

@app.post("/models/config/reset")
async def reset_config(request: ConfigResetRequest):
    """重置配置到默认值"""
    try:
        if not request.confirm:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Configuration reset requires confirmation",
                    "message": "Set 'confirm' to true to proceed with reset"
                }
            )
        
        success = model_manager.reset_preferences()
        
        if success:
            # 重新获取可用模型
            await model_manager.get_available_models(force_refresh=True)
            
            return {
                "success": True,
                "message": "Configuration reset successfully",
                "current_model": model_manager.get_current_model(),
                "available_models": model_manager.available_models
            }
        else:
            return JSONResponse(
                status_code=500,
                content={"error": "Failed to reset configuration"}
            )
            
    except Exception as e:
        logger.error(f"Error resetting config: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error resetting config: {str(e)}"}
        )

# Main Processing Endpoints

# 3. 修改 process_text 端点
@app.post("/process_text")
async def process_text(request: TextRequest):
    """Process text input - 支持两种模式 + TTS"""
    try:
        # 传递 device_id 到处理函数
        result = await process_text_with_enhanced_llm(
            request.text,
            location=request.location or "living_room",
            device_id=request.device_id  # 传递 device_id
        )
        return result
        
    except Exception as e:
        logger.error(f"Error processing text: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error processing text: {str(e)}"}
        )

# 4. 修改 process_audio 端点（如果需要）
@app.post("/process_audio")
async def process_audio(request: AudioRequest):
    """Process audio input with TTS support"""
    try:
        audio_path = request.audio_path
        device_id = request.device_id if hasattr(request, 'device_id') else None
        logger.info(f"🎤 Processing audio: {audio_path}, device_id: {device_id}")
        
        # STT processing
        stt_url = f"http://{STT_HOST}:{STT_PORT}/transcribe"
        stt_response = requests.post(stt_url, json={"audio_path": audio_path})
        
        if stt_response.status_code != 200:
            raise HTTPException(status_code=500, detail="STT service error")
        
        text_result = stt_response.json().get("text", "")
        
        if not text_result:
            return JSONResponse(
                status_code=400,
                content={"error": "Unable to recognize audio content"}
            )
        
        # Process the transcribed text (包括TTS)
        result = await process_text_with_enhanced_llm(
            text_result,
            location="living_room",
            device_id=device_id  # 传递 device_id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error processing audio: {str(e)}"}
        )

@app.post("/process_contextual")
async def process_contextual(request: ContextualRequest):
    """Process text with context"""
    try:
        result = await process_text_with_enhanced_llm(
            request.text,
            request.user_context,
            request.location
        )
        return result
        
    except Exception as e:
        logger.error(f"Error processing contextual request: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error processing contextual request: {str(e)}"}
        )

# Scene and Device Control Endpoints

@app.post("/execute_scene")
async def execute_scene(request: SceneRequest):
    """执行场景模式"""
    try:
        scene_name = request.scene_name
        location = request.location
        
        logger.info(f"🎬 Executing scene: {scene_name} at {location}")
        
        # 调用 IoT 服务执行场景
        iot_url = f"http://{IOT_HOST}:{IOT_PORT}/execute_scene"
        iot_response = requests.post(iot_url, json={
            "scene_name": scene_name,
            "location": location
        })
        
        if iot_response.status_code == 200:
            results = iot_response.json()
            
            # 广播场景执行事件到所有 WebSocket 客户端
            message = {
                "type": "scene_executed",
                "scene": scene_name,
                "location": location,
                "results": results,
                "timestamp": time.time()
            }
            
            for client_id, ws in connected_clients.items():
                try:
                    await ws.send_json(message)
                except:
                    pass
            
            return results
        else:
            raise HTTPException(
                status_code=iot_response.status_code,
                detail="Failed to execute scene"
            )
            
    except Exception as e:
        logger.error(f"Error executing scene: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scenes")
async def get_available_scenes():
    """获取可用的场景列表"""
    scenes = {
        "sleep_mode": {
            "name": "Sleep Mode",
            "description": "Dim lights, optimal temperature for sleeping",
            "icon": "🌙"
        },
        "work_mode": {
            "name": "Work Mode", 
            "description": "Bright lights, focused environment",
            "icon": "💼"
        },
        "movie_mode": {
            "name": "Movie Mode",
            "description": "Ambient lighting, entertainment setup",
            "icon": "🎬"
        },
        "home_mode": {
            "name": "Home Mode",
            "description": "Welcome home comfort settings",
            "icon": "🏠"
        },
        "away_mode": {
            "name": "Away Mode",
            "description": "Energy saving and security",
            "icon": "🚗"
        },
        "cooking_mode": {
            "name": "Cooking Mode",
            "description": "Kitchen optimized settings",
            "icon": "👨‍🍳"
        }
    }
    return {"scenes": scenes}

@app.get("/devices")
async def get_all_devices():
    """获取所有设备状态"""
    try:
        iot_response = requests.get(f"http://{IOT_HOST}:{IOT_PORT}/devices")
        if iot_response.status_code == 200:
            return iot_response.json()
        else:
            return {"devices": {}, "error": "IoT service error"}
    except Exception as e:
        logger.error(f"Error getting devices: {str(e)}")
        return {"devices": {}, "error": str(e)}

@app.post("/register_device")
async def register_device(request: DeviceRegistration):
    """注册新设备"""
    try:
        device_info = request.device_info
        device_id = device_info.get("device_id", str(uuid.uuid4()))
        
        registered_devices[device_id] = {
            "info": device_info,
            "capabilities": request.capabilities,
            "registered_at": time.time(),
            "last_seen": time.time()
        }
        
        logger.info(f"📱 Device registered: {device_id}")
        
        # 广播设备注册事件
        for client_id, ws in connected_clients.items():
            try:
                await ws.send_json({
                    "type": "device_registered",
                    "device_id": device_id,
                    "device_info": device_info
                })
            except:
                pass
        
        return {
            "success": True,
            "device_id": device_id,
            "message": "Device registered successfully"
        }
        
    except Exception as e:
        logger.error(f"Error registering device: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Environmental Data Endpoints

@app.get("/environment")
async def get_environment():
    """获取环境数据"""
    try:
        # 尝试从 IoT 服务获取最新数据
        iot_response = requests.get(f"http://{IOT_HOST}:{IOT_PORT}/sensors")
        if iot_response.status_code == 200:
            return {"sensors": iot_response.json().get("sensors", {})}
    except:
        pass
    
    # 返回本地数据作为备份
    return environmental_data

@app.get("/environment/{location}")
async def get_location_environment(location: str):
    """获取特定位置的环境数据"""
    try:
        # 尝试从 IoT 服务获取
        iot_response = requests.get(f"http://{IOT_HOST}:{IOT_PORT}/sensors/{location}")
        if iot_response.status_code == 200:
            return iot_response.json()
    except:
        pass
    
    # 使用本地数据
    sensors = environmental_data.get("sensors", {})
    if location in sensors:
        return {
            "location": location,
            "data": sensors[location]
        }
    else:
        raise HTTPException(status_code=404, detail=f"Location {location} not found")

# WebSocket for real-time communication

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint - 兼容前端期望的 /ws 路径"""
    await websocket.accept()
    client_id = str(id(websocket))  # 生成客户端ID
    connected_clients[client_id] = websocket
    
    logger.info(f"🔌 WebSocket client {client_id} connected")
    
    try:
        # 发送连接成功消息
        await websocket.send_json({
            "type": "connection_established",
            "client_id": client_id,
            "current_model": model_manager.get_current_model(),
            "available_models": model_manager.available_models,
            "mode": model_manager.get_current_mode(),
            "timestamp": time.time(),
            "message": "WebSocket connection established successfully"
        })
        
        # 处理消息循环
        while True:
            # 接收文本消息
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type", "")
                
                logger.info(f"📨 Received WebSocket message type: {message_type}")
                
                if message_type == "text":
                    # 处理文本消息
                    text_input = message.get("text", "")
                    user_context = message.get("user_context", {})
                    location = message.get("location", "living_room")
                    
                    # 处理文本（包括TTS）
                    result = await process_text_with_enhanced_llm(
                        text_input, 
                        user_context, 
                        location
                    )
                    
                    # 发送响应
                    await websocket.send_json({
                        "type": "text_response",
                        "response": result,
                        "client_id": client_id,
                        "timestamp": time.time()
                    })
                
                elif message_type == "audio_ready":
                    # 音频文件处理
                    audio_path = message.get("audio_path", "")
                    
                    # 发送音频到 STT 服务
                    stt_url = f"http://{STT_HOST}:{STT_PORT}/transcribe"
                    stt_response = requests.post(stt_url, json={"audio_path": audio_path})
                    
                    if stt_response.status_code == 200:
                        transcription = stt_response.json().get("text", "")
                        
                        # 处理转录的文本
                        result = await process_text_with_enhanced_llm(
                            transcription,
                            message.get("user_context", {}),
                            message.get("location", "living_room")
                        )
                        
                        await websocket.send_json({
                            "type": "audio_response",
                            "transcription": transcription,
                            "response": result,
                            "client_id": client_id
                        })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "error": "STT service error"
                        })
                
                elif message_type == "get_status":
                    # 获取完整的系统状态
                    
                    # 1. 获取设备状态
                    device_states = {}
                    try:
                        iot_response = requests.get(f"http://{IOT_HOST}:{IOT_PORT}/devices", timeout=2)
                        if iot_response.status_code == 200:
                            device_states = iot_response.json().get("devices", {})
                    except:
                        logger.warning("Failed to get device states from IoT service")
                    
                    # 2. 获取传感器数据
                    sensor_data = {}
                    try:
                        sensor_response = requests.get(f"http://{IOT_HOST}:{IOT_PORT}/sensors", timeout=2)
                        if sensor_response.status_code == 200:
                            sensor_data = sensor_response.json().get("sensors", {})
                    except:
                        sensor_data = environmental_data.get("sensors", {})
                    
                    # 3. 构建完整的状态响应
                    await websocket.send_json({
                        "type": "status_response",
                        "environmental_data": environmental_data,
                        "device_states": device_states,
                        "sensor_data": sensor_data,
                        "model_info": {
                            "current_model": model_manager.get_current_model(),
                            "available_models": model_manager.available_models,
                            "mode": model_manager.get_current_mode()
                        },
                        "connected_clients": len(connected_clients),
                        "registered_devices": len(registered_devices),
                        "system_uptime": time.time() - startup_time,
                        "timestamp": time.time()
                    })
                
                elif message_type == "execute_scene":
                    # 场景执行
                    scene_name = message.get("scene", "")
                    location = message.get("location", None)
                    
                    try:
                        # 调用场景执行
                        scene_response = requests.post(
                            f"http://{IOT_HOST}:{IOT_PORT}/execute_scene",
                            json={"scene_name": scene_name, "location": location}
                        )
                        
                        if scene_response.status_code == 200:
                            results = scene_response.json()
                            await websocket.send_json({
                                "type": "scene_executed",
                                "scene": scene_name,
                                "location": location,
                                "results": results,
                                "timestamp": time.time()
                            })
                        else:
                            await websocket.send_json({
                                "type": "error",
                                "error": f"Failed to execute scene: {scene_name}",
                                "details": scene_response.text
                            })
                    except Exception as e:
                        await websocket.send_json({
                            "type": "error",
                            "error": f"Scene execution error: {str(e)}"
                        })
                
                elif message_type == "device_control":
                    # 设备控制
                    device = message.get("device", "")
                    action = message.get("action", "")
                    location = message.get("location", "")
                    parameters = message.get("parameters", {})
                    
                    try:
                        # 执行设备控制
                        control_response = requests.post(
                            f"http://{IOT_HOST}:{IOT_PORT}/control",
                            json={
                                "commands": [{
                                    "device": device,
                                    "action": action,
                                    "location": location,
                                    "parameters": parameters
                                }]
                            }
                        )
                        
                        if control_response.status_code == 200:
                            results = control_response.json()
                            await websocket.send_json({
                                "type": "device_control_result",
                                "device": device,
                                "action": action,
                                "location": location,
                                "results": results,
                                "timestamp": time.time()
                            })
                        else:
                            await websocket.send_json({
                                "type": "error",
                                "error": "Device control failed",
                                "details": control_response.text
                            })
                    except Exception as e:
                        await websocket.send_json({
                            "type": "error",
                            "error": f"Device control error: {str(e)}"
                        })
                
                elif message_type == "get_sensors":
                    # 获取传感器数据
                    location = message.get("location", None)
                    
                    try:
                        if location:
                            sensor_response = requests.get(f"http://{IOT_HOST}:{IOT_PORT}/sensors/{location}")
                        else:
                            sensor_response = requests.get(f"http://{IOT_HOST}:{IOT_PORT}/sensors")
                        
                        if sensor_response.status_code == 200:
                            sensors = sensor_response.json()
                            await websocket.send_json({
                                "type": "sensor_data",
                                "sensors": sensors,
                                "location": location,
                                "timestamp": time.time()
                            })
                        else:
                            await websocket.send_json({
                                "type": "error",
                                "error": "Failed to get sensor data"
                            })
                    except Exception as e:
                        # 回退到本地数据
                        if location and location in environmental_data.get("sensors", {}):
                            await websocket.send_json({
                                "type": "sensor_data",
                                "sensors": environmental_data["sensors"][location],
                                "location": location,
                                "timestamp": time.time()
                            })
                        else:
                            await websocket.send_json({
                                "type": "sensor_data",
                                "sensors": environmental_data.get("sensors", {}),
                                "location": None,
                                "timestamp": time.time()
                            })
                
                elif message_type == "get_models":
                    # 获取模型列表
                    models = await model_manager.get_available_models()
                    await websocket.send_json({
                        "type": "models_list",
                        "available_models": models,
                        "current_model": model_manager.get_current_model(),
                        "timestamp": time.time()
                    })
                
                elif message_type == "register_device":
                    # 设备注册
                    device_info = message.get("device_info", {})
                    device_id = device_info.get("device_id", str(client_id))
                    
                    registered_devices[device_id] = {
                        "info": device_info,
                        "client_id": client_id,
                        "registered_at": time.time()
                    }
                    
                    await websocket.send_json({
                        "type": "device_registered",
                        "device_id": device_id,
                        "timestamp": time.time()
                    })
                    
                elif message_type == "ping":
                    # 响应 ping
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": time.time()
                    })
                    
                else:
                    # 未知消息类型
                    await websocket.send_json({
                        "type": "error",
                        "error": f"Unknown message type: {message_type}",
                        "timestamp": time.time()
                    })
                    
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "error": "Invalid JSON format",
                    "timestamp": time.time()
                })
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "error": f"Processing error: {str(e)}",
                    "timestamp": time.time()
                })
                
    except WebSocketDisconnect:
        logger.info(f"🔴 WebSocket client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {str(e)}")
    finally:
        # 清理断开的连接
        if client_id in connected_clients:
            del connected_clients[client_id]
        
        # 清理注册的设备
        devices_to_remove = [
            device_id for device_id, device in registered_devices.items()
            if device.get("client_id") == client_id
        ]
        for device_id in devices_to_remove:
            del registered_devices[device_id]
        
        logger.info(f"🧹 Cleaned up client {client_id}")

# Helper functions

async def test_model_functionality(model_name: str):
    """测试模型是否正常工作"""
    try:
        test_prompt = "Hello, this is a test message. Please respond with 'Model test successful' if you can understand this."
        
        if model_manager.current_mode == APIMode.REMOTE_API:
            # API mode test
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": test_prompt}
                ],
                "max_tokens": 50
            }
            
            response = requests.post(
                OLLAMA_ENDPOINT,
                json=payload,
                headers=model_manager.api_headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data["choices"][0]["message"]["content"].lower()
                
                if "test" in response_text or "successful" in response_text:
                    return {
                        "success": True,
                        "response": data["choices"][0]["message"]["content"],
                        "mode": "api"
                    }
        else:
            # Local mode test
            payload = {
                "model": model_name,
                "prompt": test_prompt,
                "stream": False
            }
            
            response = requests.post(
                f"{OLLAMA_ENDPOINT}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "").lower()
                
                if "test" in response_text or "successful" in response_text:
                    return {
                        "success": True,
                        "response": data.get("response", ""),
                        "eval_count": data.get("eval_count", 0),
                        "eval_duration": data.get("eval_duration", 0),
                        "mode": "local"
                    }
        
        return {
            "success": False,
            "error": "Model did not respond as expected"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def broadcast_model_switch(new_model: str):
    """广播模型切换事件到所有连接的客户端"""
    if not connected_clients:
        return
    
    message = {
        "type": "model_switch",
        "new_model": new_model,
        "timestamp": time.time(),
        "message": f"System switched to model: {new_model}"
    }
    
    disconnected_clients = []
    for client_id, websocket in connected_clients.items():
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to broadcast to client {client_id}: {str(e)}")
            disconnected_clients.append(client_id)
    
    # Remove disconnected clients
    for client_id in disconnected_clients:
        del connected_clients[client_id]

async def broadcast_mode_switch(new_mode: str):
    """广播模式切换事件到所有连接的客户端"""
    if not connected_clients:
        return
    
    message = {
        "type": "mode_switch",
        "new_mode": new_mode,
        "model": model_manager.current_model,
        "timestamp": time.time(),
        "message": f"System switched to {new_mode} mode"
    }
    
    disconnected_clients = []
    for client_id, websocket in connected_clients.items():
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to broadcast mode switch to client {client_id}: {str(e)}")
            disconnected_clients.append(client_id)
    
    # Remove disconnected clients
    for client_id in disconnected_clients:
        del connected_clients[client_id]

# Audio file serving (if needed)
@app.get("/audio/{filename}")
async def serve_audio(filename: str):
    """Serve TTS audio files"""
    try:
        # 代理到TTS服务
        tts_audio_url = f"http://{TTS_HOST}:{TTS_PORT}/audio/{filename}"
        
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(tts_audio_url)
            
            if response.status_code == 200:
                return Response(
                    content=response.content,
                    media_type=response.headers.get("content-type", "audio/mpeg"),
                    headers={
                        "Content-Disposition": f"inline; filename={filename}",
                        "Cache-Control": "public, max-age=3600"
                    }
                )
            else:
                raise HTTPException(status_code=404, detail="Audio file not found")
                
    except Exception as e:
        logger.error(f"Error serving audio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Startup event

@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    global startup_time
    startup_time = time.time()
    
    logger.info("🚀 Starting AI Voice Assistant Coordinator Service")
    logger.info(f"📍 Running in {model_manager.get_current_mode()} mode")
    logger.info(f"🤖 Default model: {model_manager.current_model}")
    
    # Check if API key is configured for API mode
    if model_manager.current_mode == APIMode.REMOTE_API and not REMOTE_API_KEY:
        logger.error("❌ WARNING: API mode selected but REMOTE_API_KEY not configured!")
    
    # Get initial model list
    await model_manager.get_available_models(force_refresh=True)
    
    logger.info("✅ Coordinator service started successfully")

# Run the application
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)