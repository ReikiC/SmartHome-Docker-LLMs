# services/coordinator/system_config.py
"""
系统配置文件 - 包含所有提示词、传感器状态和系统行为定义
"""

import json
from typing import Dict, Any, Optional, List

# ==================== 环境数据和传感器状态 ====================
ENVIRONMENTAL_DATA = {
    "sensors": {
        "living_room": {
            "temperature": 22.5,
            "humidity": 45,
            "co2": 480,
            "voc": 25,
            "motion": False,
            "light_level": 300,
            "last_update": "2025-06-03T10:30:00"
        },
        "bedroom": {
            "temperature": 21.8,
            "humidity": 48,
            "co2": 420,
            "voc": 15,
            "motion": False,
            "light_level": 150,
            "last_update": "2025-06-03T10:30:00"
        },
        "kitchen": {
            "temperature": 23.5,
            "humidity": 55,
            "co2": 550,
            "voc": 35,
            "motion": True,
            "light_level": 400,
            "last_update": "2025-06-03T10:30:00"
        },
        "study": {
            "temperature": 23.1,
            "humidity": 52,
            "co2": 430,
            "voc": 18,
            "motion": False,
            "light_level": 350,
            "last_update": "2025-06-03T10:30:00"
        },
        "bathroom": {
            "temperature": 24.8,
            "humidity": 70,
            "co2": 400,
            "voc": 20,
            "motion": False,
            "light_level": 200,
            "last_update": "2025-06-03T10:30:00"
        }
    }
}

# ==================== 系统提示词 ====================
BASE_SYSTEM_PROMPT = """

# You are an intelligent AI assistant for a smart home system.

# IMPORTANT: You are in the RESPONSE GENERATION phase, NOT the intent extraction phase.
# - User intents have ALREADY been extracted and executed by the system
# - Your role is to RESPOND to the user naturally, acknowledging any actions taken
# - DO NOT extract commands or parse intents - just respond conversationally

# Additional context:
# - Dankao is the only developer of this system (also Dankao's dissertation), major in Connected Environments
# - This project is supervised by Steve

# Technical Details about this Smart Home System:
# - Architecture: Microservices-based system with Docker containers
# - Core Services:
#   * STT Service: Speech-to-text using OpenAI Whisper
#   * TTS Service: Text-to-speech with multiple voice options
#   * IoT Control: Device management/monitor
#   * Coordinator: Central orchestration, Coordinate the collaborative work of services such as STT, TTS, IoT Control, and Ollama (LLM).
#   * Ollama: Local/Remote LLM model for intent extraction (users can choose run AI locally or use Ollama API on the web, also users can choose different LLM models like Llama3, gemma3, etc.)
# - Communication: RESTful APIs and WebSocket for real-time updates
# - LLM Integration: Supports both local Ollama and remote API modes, the remote API is generted from Steve's powerfull server (which is also located in the UCL CAMPUS, but not in the same room as the edge server running this Smart Home System。The Remote mode requires public network access and uses API keys to verify identity information. Therefore, this mode cannot run in an environment without an Internet connection. However, you can still use this system in local mode.)
# - Audio Formats: MP3 for web clients, PCM for ESP32 devices
# - Intro: Integrated with ESP32 hardware for audio processing and ESP8266 for environmental monitoring, it supports multi-language commands (English/Chinese) and scene-based automation. Unlike traditional rule-based systems, this framework leverages LLM-powered intent extraction for superior accuracy and user experience while ensuring privacy through complete local processing.
# - Semantic understanding and user intent extraction: Utilising an innovative dual LLM architecture, the first LLM understands user intent and extracts IoT commands, while the second LLM generates natural dialogue after executing the operation. This ensures control accuracy while enabling natural human-machine interaction, allowing users to control home appliances using everyday language.
# - Realtime environmental monitoring: This system continuously monitors indoor air quality, temperature, humidity, and other environmental parameters through a network of sensors and upload data to websocket. Before each AI response, this data is automatically pulled down by the coordinator microservice on the edge server (for example MAC or Jetson) and added to the system prompt to provide context for the response.
# - Web: User can choose User/ Developer Mode, Local/ Remote API Mode, Easily Pull down LLM models with Multiple LLM Support. It also has Real-time Monitoring, Real-time Control
# - Reiki (Smart Home AI assistant hardware): This device "Reiki" is a custom-designed ESP32 development board (micro-controller) consisting of a main board and a sub-board. The main board integrates the ESP32N16R8 chip along with components such as a CODEC, gyroscope, and microphone. The sub-board is primarily used for power management, speaker amplification, and code burning (using the esp-idf framework). The device communicates with the system in real-time via WebSocket. Users can interact with the Smart Home AI assistant via voice commands and control home appliances.
# - Framework: Smart Home AI assistant hardware running on ESP32 (Reiki), smart furnitures/sensors running on ESP8266, a edge server (Mac or Jetson) running the coordinator microservice, and a web client for user interaction. 


You are an intelligent AI assistant for a smart home system.

IMPORTANT: You are in the RESPONSE GENERATION phase, NOT the intent extraction phase.
- User intents have ALREADY been extracted and executed by the system
- Your role is to RESPOND to the user naturally, acknowledging any actions taken
- DO NOT extract commands or parse intents - just respond conversationally

Additional context:
- The project creator Dankao is the only developer of this system (also Dankao's dissertation), he is major in Connected Environments
- This project is supervised by Steve

Technical Details about this Smart Home System:

1. ARCHITECTURE:
   - Microservices-based system with Docker containers
   - Edge computing on Mac or Jetson Nano
   - Real-time WebSocket communication
   - RESTful APIs for service integration

2. CORE SERVICES:
   * STT Service: Speech-to-text using OpenAI Whisper
   * TTS Service: Text-to-speech with multiple voice options
   * IoT Control: Device management and monitoring
   * Coordinator: Central orchestration, coordinates the collaborative work of services such as STT, TTS, IoT Control, and Ollama (LLM)
   * Ollama: Local/Remote LLM model for intent extraction (users can choose run AI locally or use Ollama API on the web, also users can choose different LLM models like Llama3, gemma3, etc.)

3. COMMUNICATION & INTEGRATION:
   - RESTful APIs and WebSocket for real-time updates
   - LLM Integration: Supports both local Ollama and remote API modes
   - Remote API is generated from Steve's powerful server (located in UCL campus, but not in the same room as the edge server)
   - Remote mode requires public network access and uses API keys for identity verification
   - Cannot run in remote mode without Internet connection, but local mode works offline. Besides, user can only use the samrt home system under the same network as the edge server (which means you cannot control the system outside your home since the web interface can not acessed by public network rightnow due to the time limitation), but this issue would be fixed easliy in the future.
   - Audio Formats: MP3 for web clients, PCM for ESP32 devices

4. KEY FEATURES:
   - Integrated with ESP32 hardware for audio processing and ESP8266 for environmental monitoring
   - Supports multi-language commands (English/Chinese) and scene-based automation
   - Unlike traditional rule-based systems, leverages LLM-powered intent extraction for superior accuracy
   - Ensures privacy through complete local processing option

5. SEMANTIC UNDERSTANDING & USER INTENT EXTRACTION:
   - Innovative dual LLM architecture:
     * First LLM understands user intent and extracts IoT commands 
     * Second LLM generates natural dialogue after executing the operation. 
     * This ensures control accuracy while enabling natural human-machine interaction, allowing users to control home appliances using everyday language.
   - Ensures control accuracy while enabling natural human-machine interaction
   - Allows users to control home appliances using everyday language

6. REAL-TIME ENVIRONMENTAL MONITORING:
   - Continuously monitors indoor air quality, temperature, humidity, and other environmental parameters
   - Network of sensors upload data to WebSocket
   - Before each AI response, data is automatically pulled by the coordinator microservice
   - Environmental data is added to the system prompt to provide context

7. WEB INTERFACE:
   - User can choose between User/Developer Mode
   - Switch between Local/Remote API Mode
   - Easy LLM model management with pull-down functionality
   - Multiple LLM model support
   - Real-time monitoring and control capabilities

8. REIKI (SMART HOME AI ASSISTANT Mobile HARDWARE):
   - Custom-designed ESP32 development board (microcontroller)
   - Architecture:
     * Main board: ESP32N16R8 chip, CODEC, gyroscope, and microphone
     * Sub-board: Power management, speaker amplification, and code burning
   - Uses esp-idf framework
   - Communicates with system in real-time via WebSocket
   - Enables voice interaction for home appliance control

9. SYSTEM FRAMEWORK:
   - Smart Home AI assistant Mobile hardware running on ESP32 (Reiki)
   - Smart furniture/sensors running on ESP8266
   - Edge server (Mac or Jetson) running the coordinator microservice
   - Web client for user interaction


Current environment:"""

# ==================== 场景模式定义 ====================
SCENE_MODES = {
    "home_mode": {
        "name": "Home Mode",
        "description": "Welcome home lighting and comfort settings",
        "actions": [
            {"device": "lights", "room": "living_room", "action": "on", "brightness": 80},
            {"device": "lights", "room": "hallway", "action": "on", "brightness": 60},
            {"device": "ac", "room": "living_room", "action": "on", "temperature": 24}
        ]
    },
    "sleep_mode": {
        "name": "Sleep Mode", 
        "description": "Optimal settings for sleep",
        "actions": [
            {"device": "lights", "room": "all", "action": "off"},
            {"device": "ac", "room": "bedroom", "action": "on", "temperature": 23},
            {"device": "curtains", "room": "bedroom", "action": "close"}
        ]
    },
    "work_mode": {
        "name": "Work Mode",
        "description": "Focused work environment",
        "actions": [
            {"device": "lights", "room": "study", "action": "on", "brightness": 100},
            {"device": "ac", "room": "study", "action": "on", "temperature": 24},
            {"device": "fan", "room": "study", "action": "on", "speed": 2}
        ]
    },
    "movie_mode": {
        "name": "Movie Mode",
        "description": "Theater-like experience",
        "actions": [
            {"device": "lights", "room": "living_room", "action": "dim", "brightness": 20},
            {"device": "curtains", "room": "living_room", "action": "close"},
            {"device": "ac", "room": "living_room", "action": "on", "temperature": 22}
        ]
    },
    "cooking_mode": {
        "name": "Cooking Mode",
        "description": "Kitchen optimized for cooking",
        "actions": [
            {"device": "lights", "room": "kitchen", "action": "on", "brightness": 100},
            {"device": "exhaust_fan", "room": "kitchen", "action": "on"},
            {"device": "fan", "room": "kitchen", "action": "on", "speed": 3}
        ]
    },
    "away_mode": {
        "name": "Away Mode",
        "description": "Energy saving and security",
        "actions": [
            {"device": "lights", "room": "all", "action": "off"},
            {"device": "ac", "room": "all", "action": "off"},
            {"device": "curtains", "room": "all", "action": "close"}
        ]
    }
}

# ==================== IoT命令关键词映射 ====================
IOT_COMMAND_KEYWORDS = {
    "lights": {
        "on": ["turn on", "open", "打开", "开", "light up", "亮"],
        "off": ["turn off", "close", "关闭", "关", "shut"],
        "dim": ["dim", "dimmer", "darker", "调暗", "暗一点"],
        "bright": ["bright", "brighter", "调亮", "亮一点"]
    },
    "ac": {
        "on": ["turn on ac", "air conditioner on", "开空调", "打开空调"],
        "off": ["turn off ac", "air conditioner off", "关空调", "关闭空调"],
        "temperature": ["set temperature", "temperature to", "温度调到", "设置温度"]
    },
    "fan": {
        "on": ["turn on fan", "fan on", "开风扇", "打开风扇"],
        "off": ["turn off fan", "fan off", "关风扇", "关闭风扇"],
        "speed": ["fan speed", "风扇速度", "调节风速"]
    },
    "curtains": {
        "open": ["open curtains", "curtains open", "拉开窗帘", "打开窗帘"],
        "close": ["close curtains", "curtains close", "拉上窗帘", "关闭窗帘"],
        "half": ["half open", "halfway", "开一半", "半开"]
    }
}

# ==================== 房间名称映射 ====================
ROOM_MAPPINGS = {
    "living room": "living_room",
    "客厅": "living_room",
    "bedroom": "bedroom", 
    "卧室": "bedroom",
    "kitchen": "kitchen",
    "厨房": "kitchen",
    "study": "study",
    "书房": "study",
    "bathroom": "bathroom",
    "浴室": "bathroom",
    "洗手间": "bathroom"
}

# ==================== 表情/情绪判断关键词 ====================
EMOTION_KEYWORDS = {
    "positive": ["good", "great", "nice", "perfect", "excellent", "wonderful", 
                 "好", "很好", "不错", "完美", "棒", "太好了"],
    "negative": ["bad", "terrible", "wrong", "error", "fail", "problem",
                 "糟糕", "不好", "错误", "失败", "问题"],
    "question": ["what", "how", "why", "when", "where", "who",
                 "什么", "怎么", "为什么", "哪里", "谁"]
}

# ==================== 辅助函数 ====================
def get_comprehensive_system_prompt(user_context: Optional[Dict] = None, 
                                  location: str = "living_room") -> str:
    """生成包含所有房间信息的系统提示词"""
    prompt = BASE_SYSTEM_PROMPT
    
    # 添加所有房间的传感器数据
    prompt += "\n\nCurrent environment status across all rooms:"
    
    # 遍历所有房间
    for room_name, sensor_data in ENVIRONMENTAL_DATA["sensors"].items():
        room_display_name = room_name.replace('_', ' ').title()
        prompt += f"\n\n{room_display_name}:"
        prompt += f"\n- Temperature: {sensor_data['temperature']}°C"
        prompt += f"\n- Humidity: {sensor_data['humidity']}%"
        prompt += f"\n- CO2: {sensor_data['co2']} ppm"
        prompt += f"\n- VOC: {sensor_data['voc']}"
        prompt += f"\n- Motion detected: {sensor_data['motion']}"
        prompt += f"\n- Light level: {sensor_data['light_level']} lux"
    
    # 如果指定了当前位置，强调一下
    if location and location in ENVIRONMENTAL_DATA["sensors"]:
        prompt += f"\n\nUser is currently in: {location}"
    
    # ===== 核心修改部分开始 =====
    # ===== 核心修改部分 =====
    if user_context:
        if isinstance(user_context, dict):
            iot_commands = user_context.get("iot_commands", [])
            iot_results = user_context.get("iot_results", [])
            
            # 再次强调：这是响应阶段，不是意图提取阶段
            prompt += "\n\n=== RESPONSE CONTEXT ==="
            prompt += "\n**REMINDER: You are generating a RESPONSE, not extracting intents.**"
            
            if iot_commands:
                prompt += "\n\n**Actions Already Executed by System:**"
                for i, cmd in enumerate(iot_commands):
                    device_display = cmd['device'].replace('_', ' ')
                    prompt += f"\n✓ {cmd['action']} {device_display} in {cmd['location']}"
                    if cmd.get('parameters'):
                        for param, value in cmd['parameters'].items():
                            prompt += f" ({param}: {value})"
                    
                    if i < len(iot_results) and iot_results[i]:
                        if "error" in iot_results[i]:
                            prompt += f" [Failed: {iot_results[i]['error']}]"
                        else:
                            prompt += " [Success]"
                
                prompt += "\n\n**Your Task:** Acknowledge these completed actions naturally in your response."
            else:
                prompt += "\n\n**No Device Actions Taken** - This is a conversational interaction."
                prompt += "\n**Your Task:** Respond conversationally as a helpful smart home assistant."
        else:  
            prompt += "\n\n**User Context is not in the expected format.**"
    # ===== 核心修改部分结束 =====
    
    # 添加指导说明
    prompt += "\n\nImportant instructions:"
    prompt += "\n- Respond naturally in the language the user uses (English)"
    prompt += "\n\n**FINAL REMINDER:** Generate a natural RESPONSE to the user. Do NOT output JSON, commands, or intent analysis."
    
    return prompt

def extract_iot_commands_enhanced(text: str, location: str = "living_room") -> List[Dict]:
    """从文本中提取IoT控制命令"""
    commands = []
    text_lower = text.lower()
    
    # 检查每种设备类型
    for device_type, actions in IOT_COMMAND_KEYWORDS.items():
        for action, keywords in actions.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # 提取房间信息
                    target_room = location
                    for room_phrase, room_code in ROOM_MAPPINGS.items():
                        if room_phrase in text_lower:
                            target_room = room_code
                            break
                    
                    # 构建命令
                    command = {
                        "device": device_type,
                        "room": target_room,
                        "action": action
                    }
                    
                    # 特殊处理：温度设置
                    if device_type == "ac" and action == "temperature":
                        import re
                        temp_match = re.search(r'\d+', text)
                        if temp_match:
                            command["temperature"] = int(temp_match.group())
                    
                    # 特殊处理：亮度设置
                    if device_type == "lights" and action in ["dim", "bright"]:
                        if "dim" in text_lower or "暗" in text_lower:
                            command["brightness"] = 30
                        elif "bright" in text_lower or "亮" in text_lower:
                            command["brightness"] = 100
                    
                    commands.append(command)
                    break
    
    return commands

def determine_expression_enhanced(user_input: str, ai_response: str, 
                                iot_commands: List[Dict]) -> str:
    """根据对话内容判断表情/情绪"""
    user_lower = user_input.lower()
    
    # 根据关键词判断
    if any(keyword in user_lower for keyword in EMOTION_KEYWORDS["negative"]):
        return "sad"
    elif any(keyword in user_lower for keyword in EMOTION_KEYWORDS["positive"]):
        return "happy"
    elif any(keyword in user_lower for keyword in EMOTION_KEYWORDS["question"]):
        return "thinking"
    
    # 如果有IoT命令被执行，通常是积极的
    if iot_commands:
        return "happy"
    
    return "neutral"

def get_scene_actions(scene_name: str) -> List[Dict]:
    """获取场景模式的动作列表"""
    if scene_name in SCENE_MODES:
        return SCENE_MODES[scene_name]["actions"]
    return []

def update_sensor_data(room: str, sensor_type: str, value: Any) -> bool:
    """更新传感器数据"""
    if room in ENVIRONMENTAL_DATA["sensors"]:
        if sensor_type in ENVIRONMENTAL_DATA["sensors"][room]:
            ENVIRONMENTAL_DATA["sensors"][room][sensor_type] = value
            return True
    return False

def get_all_sensors_data() -> Dict:
    """获取所有传感器数据"""
    return ENVIRONMENTAL_DATA["sensors"].copy()