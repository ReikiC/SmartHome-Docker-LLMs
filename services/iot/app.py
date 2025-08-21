import os
import logging
import json
import time
import asyncio
import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables
CONFIG_PATH = os.getenv("CONFIG_PATH", "/app/config/devices.json")
MQTT_ENABLED = os.getenv("MQTT_ENABLED", "false").lower() == "true"
MQTT_BROKER = os.getenv("MQTT_BROKER", "mqtt_broker")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER = os.getenv("MQTT_USER", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")

# Create FastAPI application
app = FastAPI(title="IoT Control Service")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connected ESP32 devices
connected_devices = {}

# Timer management for timed devices
active_timers = {}

# Enhanced device states - 对应Week 1设计
device_states = {
    # 天花板灯 - 支持调光和色温
    "ceiling_light": {
        "living_room": {"status": "off", "brightness": 100, "color_temp": 4000},
        "bedroom": {"status": "off", "brightness": 80, "color_temp": 3000},
        "kitchen": {"status": "off", "brightness": 80, "color_temp": 5000},
        "study": {"status": "off", "brightness": 90, "color_temp": 4500},
        "bathroom": {"status": "off", "brightness": 70, "color_temp": 4000}
    },
    
    # 台灯 - 支持调光和色温
    "desk_lamp": {
        "bedroom": {"status": "off", "brightness": 90, "color_temp": 2700},
        "study": {"status": "off", "brightness": 80, "color_temp": 4000}
    },
    
    # 风扇 - 支持多档速度和摆动
    "fan": {
        "living_room": {"status": "off", "speed": 1, "oscillation": False},
        "bedroom": {"status": "off", "speed": 1, "oscillation": False},
        "study": {"status": "off", "speed": 1, "oscillation": False}
    },
    
    # 排气扇 - 厨房和浴室
    "exhaust_fan": {
        "kitchen": {"status": "off", "speed": 2, "timer": 0},
        "bathroom": {"status": "off", "speed": 2, "timer": 0}
    },
    
    # 空调 - 原有基础上增加风速
    "ac": {
        "living_room": {"status": "off", "temperature": 26, "mode": "cool", "fan_speed": "auto"},
        "bedroom": {"status": "off", "temperature": 25, "mode": "cool", "fan_speed": "auto"}
    },
    
    # 窗帘 - 增加开启程度控制
    "curtain": {
        "living_room": {"status": "closed", "position": 0},
        "bedroom": {"status": "closed", "position": 0},
        "study": {"status": "closed", "position": 0},
        "bathroom": {"status": "closed", "position": 0}
    },
    
    # 传感器数据 - 只读设备，模拟真实环境数据
    "sensors": {
        "living_room": {
            "temperature": 23.5,
            "humidity": 55,
            "co2": 420,
            "voc": 15,
            "motion": False,
            "light_level": 300,
            "last_update": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "real_data": False,
            "last_real_update": None,
            "source": None,
            "device_id": None
        },
        "bedroom": {
            "temperature": 22.8,
            "humidity": 58,
            "co2": 450,
            "voc": 12,
            "motion": False,
            "light_level": 150,
            "last_update": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "real_data": False,
            "last_real_update": None,
            "source": None,
            "device_id": None
        },
        "kitchen": {
            "temperature": 24.2,
            "humidity": 62,
            "co2": 480,
            "voc": 25,
            "motion": False,
            "light_level": 400,
            "last_update": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "real_data": False,
            "last_real_update": None,
            "source": None,
            "device_id": None
        },
        "study": {
            "temperature": 23.1,
            "humidity": 52,
            "co2": 430,
            "voc": 18,
            "motion": False,
            "light_level": 350,
            "last_update": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "real_data": False,
            "last_real_update": None,
            "source": None,
            "device_id": None
        },
        "bathroom": {
            "temperature": 24.8,
            "humidity": 70,
            "co2": 400,
            "voc": 20,
            "motion": False,
            "light_level": 200,
            "last_update": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "real_data": False,
            "last_real_update": None,
            "source": None,
            "device_id": None
        }
    }
}

class IoTCommand(BaseModel):
    device: str
    action: str
    location: str
    parameters: Optional[Dict[str, Any]] = None

class IoTControlRequest(BaseModel):
    commands: List[dict]

class SceneRequest(BaseModel):
    scene_name: str
    location: Optional[str] = None

# Helper functions defined first to avoid undefined variable errors

async def broadcast_device_update(device, location):
    """Broadcast device state update to all connected WebSocket clients"""
    if not connected_devices:
        return
    
    message = {
        "type": "device_update",
        "device": device,
        "location": location,
        "state": device_states[device][location],
        "timestamp": time.time()
    }
    
    disconnected_clients = []
    for client_id, websocket in connected_devices.items():
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"WebSocket send failed for client {client_id}: {str(e)}")
            disconnected_clients.append(client_id)
    
    # Remove disconnected clients
    for client_id in disconnected_clients:
        del connected_devices[client_id]

async def broadcast_sensor_update(location):
    """Broadcast sensor data update"""
    if not connected_devices:
        return
    
    sensors = device_states.get("sensors", {}).get(location, {})
    message = {
        "type": "sensor_update",
        "location": location,
        "sensors": sensors,
        "timestamp": time.time()
    }
    
    disconnected_clients = []
    for client_id, websocket in connected_devices.items():
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Sensor update failed for client {client_id}: {str(e)}")
            disconnected_clients.append(client_id)
    
    # Remove disconnected clients
    for client_id in disconnected_clients:
        del connected_devices[client_id]

async def update_environmental_impact(device, action, location, current_state):
    """Update environmental sensors based on device changes (simulation)"""
    sensors = device_states.get("sensors", {}).get(location, {})
    if not sensors:
        return
    
    # Skip environmental impact if we have real sensor data
    if sensors.get("real_data", False):
        last_real_update = sensors.get("last_real_update", 0)
        time_since_update = time.time() - last_real_update
        if time_since_update < 300:  # 5 minutes
            return
    
    # Simulate environmental changes based on device operations
    if device == "ceiling_light" or device == "desk_lamp":
        if action == "on" or current_state.get("status") == "on":
            # Lights generate heat and affect light level
            brightness = current_state.get("brightness", 50)
            sensors["light_level"] = min(1000, sensors.get("light_level", 0) + brightness * 5)
            sensors["temperature"] = min(35, sensors.get("temperature", 23) + brightness * 0.01)
        else:
            # Lights off reduce light level
            sensors["light_level"] = max(0, sensors.get("light_level", 300) - 200)
    
    elif device == "ac":
        if current_state.get("status") == "on":
            target_temp = current_state.get("temperature", 25)
            current_temp = sensors.get("temperature", 23)
            # Gradually adjust towards target temperature
            if current_temp > target_temp:
                sensors["temperature"] = max(target_temp, current_temp - 0.5)
            elif current_temp < target_temp:
                sensors["temperature"] = min(target_temp, current_temp + 0.5)
    
    elif device == "exhaust_fan":
        if current_state.get("status") == "on":
            # Exhaust fans reduce humidity and VOC
            sensors["humidity"] = max(30, sensors.get("humidity", 55) - 5)
            sensors["voc"] = max(5, sensors.get("voc", 15) - 3)
            sensors["co2"] = max(350, sensors.get("co2", 420) - 20)
    
    elif device == "fan":
        if current_state.get("status") == "on":
            # Fans help with air circulation, slight cooling effect
            speed = current_state.get("speed", 1)
            sensors["temperature"] = max(16, sensors.get("temperature", 23) - speed * 0.3)
    
    elif device == "curtain":
        position = current_state.get("position", 0)
        # Curtains affect light level
        if position > 50:
            sensors["light_level"] = max(sensors.get("light_level", 300) - 100, 50)
        else:
            sensors["light_level"] = min(sensors.get("light_level", 300) + 150, 800)
    
    # Update timestamp
    sensors["last_update"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    
    # Broadcast sensor updates
    await broadcast_sensor_update(location)

def set_device_timer(device, location, minutes):
    """Set a timer for a device"""
    timer_id = f"{device}_{location}_{int(time.time())}"
    active_timers[timer_id] = {
        "device": device,
        "location": location,
        "expire_time": time.time() + (minutes * 60),
        "duration": minutes
    }
    return timer_id

# API Routes

@app.get("/")
async def root():
    return {"message": "IoT Control Service is running"}

@app.get("/devices")
async def get_devices():
    """Get all device states"""
    return {"devices": device_states}

@app.get("/device/{device_type}/{location}")
async def get_device_status(device_type: str, location: str):
    """Get specific device status"""
    if device_type not in device_states or location not in device_states[device_type]:
        return JSONResponse(
            status_code=404,
            content={"error": f"Device does not exist: {device_type} at {location}"}
        )
    
    return {
        "device": device_type,
        "location": location,
        "state": device_states[device_type][location]
    }

@app.get("/sensors")
async def get_all_sensors():
    """Get all sensor data"""
    return {"sensors": device_states.get("sensors", {})}

@app.get("/sensors/{location}")
async def get_sensor_data(location: str):
    """Get sensor data for specific location"""
    sensors = device_states.get("sensors", {})
    if location not in sensors:
        return JSONResponse(
            status_code=404,
            content={"error": f"No sensors found for location: {location}"}
        )
    
    return {
        "location": location,
        "sensors": sensors[location]
    }

@app.get("/sensors/{location}/info")
async def get_sensor_info(location: str):
    """Get detailed sensor information including data source"""
    sensors = device_states.get("sensors", {})
    if location not in sensors:
        return JSONResponse(
            status_code=404,
            content={"error": f"No sensors found for location: {location}"}
        )
    
    sensor_data = sensors[location].copy()
    
    # 添加额外的信息
    info = {
        "location": location,
        "data": sensor_data,
        "data_source": "real" if sensor_data.get("real_data", False) else "simulated",
        "last_real_update": sensor_data.get("last_real_update"),
        "time_since_real_update": time.time() - sensor_data.get("last_real_update", 0) if sensor_data.get("last_real_update") else None,
        "source_device": sensor_data.get("source"),
        "device_id": sensor_data.get("device_id")
    }
    
    return info

@app.post("/sensors/{location}/reset_simulation")
async def reset_sensor_simulation(location: str):
    """Reset sensor to simulation mode (for testing)"""
    sensors = device_states.get("sensors", {})
    if location not in sensors:
        return JSONResponse(
            status_code=404,
            content={"error": f"No sensors found for location: {location}"}
        )
    
    # 重置为模拟模式
    sensors[location]["real_data"] = False
    sensors[location].pop("last_real_update", None)
    sensors[location].pop("source", None)
    sensors[location].pop("device_id", None)
    
    logger.info(f"Sensor simulation reset for {location}")
    
    return {
        "message": f"Sensor simulation reset for {location}",
        "location": location
    }

@app.post("/control")
async def control_devices(request: IoTControlRequest):
    """Control IoT devices with enhanced support"""
    results = []
    
    for cmd in request.commands:
        try:
            device = cmd.get("device")
            action = cmd.get("action")
            location = cmd.get("location")
            parameters = cmd.get("parameters", {})
            
            if not all([device, action, location]):
                results.append({
                    "status": "error",
                    "message": "Missing required parameters",
                    "command": cmd
                })
                continue
            
            # Special case for sensors - check if location exists
            if device == "sensors":
                if location not in device_states.get("sensors", {}):
                    results.append({
                        "status": "error",
                        "message": f"Sensor location does not exist: {location}",
                        "command": cmd
                    })
                    continue
            else:
                # Check if device exists for non-sensor devices
                if device not in device_states or location not in device_states[device]:
                    results.append({
                        "status": "error",
                        "message": f"Device does not exist: {device} at {location}",
                        "command": cmd
                    })
                    continue
            
            # Execute enhanced control command
            result = await execute_enhanced_command(device, action, location, parameters)
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            results.append({
                "status": "error",
                "message": f"Error executing command: {str(e)}",
                "command": cmd
            })
    
    return {"results": results}

@app.post("/execute_scene")
async def execute_scene(request: SceneRequest):
    """Execute predefined scene mode"""
    try:
        results = await execute_scene_mode(request.scene_name, request.location)
        return {
            "scene": request.scene_name,
            "location": request.location,
            "results": results,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error executing scene: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error executing scene: {str(e)}"}
        )

async def execute_enhanced_command(device, action, location, parameters):
    """Enhanced device control with full parameter support"""
    try:
        # 特殊处理：传感器数据更新
        if device == "sensors" and action == "data_update":
            # 更新传感器数据而不是设备状态
            if location in device_states.get("sensors", {}):
                # 更新传感器数据
                sensor_data = device_states["sensors"][location]
                
                # 更新所有传感器参数
                if "temperature" in parameters:
                    sensor_data["temperature"] = round(float(parameters["temperature"]), 1)
                if "humidity" in parameters:
                    sensor_data["humidity"] = round(float(parameters["humidity"]), 1)
                if "co2" in parameters:
                    sensor_data["co2"] = int(parameters["co2"])
                if "voc" in parameters:
                    sensor_data["voc"] = int(parameters["voc"])
                if "light_level" in parameters:
                    sensor_data["light_level"] = int(parameters["light_level"])
                if "motion" in parameters:
                    sensor_data["motion"] = bool(parameters["motion"])
                
                # 更新时间戳和来源信息
                sensor_data["last_update"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                sensor_data["source"] = parameters.get("source", "unknown")
                sensor_data["device_id"] = parameters.get("device_id", "unknown")
                
                # 标记为真实数据，避免被模拟数据覆盖
                sensor_data["real_data"] = True
                sensor_data["last_real_update"] = time.time()
                
                logger.info(f"✅ Updated REAL sensor data for {location}: temp={parameters.get('temperature')}°C, humidity={parameters.get('humidity')}%, CO2={parameters.get('co2')}ppm, VOC={parameters.get('voc')}ppb")
                
                # 广播传感器更新
                await broadcast_sensor_update(location)
                
                return {
                    "status": "success",
                    "device": device,
                    "location": location,
                    "action": action,
                    "parameters": parameters,
                    "current_state": sensor_data
                }
            else:
                return {
                    "status": "error",
                    "message": f"Sensor location not found: {location}",
                    "device": device,
                    "location": location,
                    "action": action
                }
    
        # 原有的设备控制逻辑（保持不变）
        current_state = device_states[device][location].copy()
        
        # Execute different operations based on device type and action
        if device == "ceiling_light" or device == "light":
            if action == "on":
                current_state["status"] = "on"
            elif action == "off":
                current_state["status"] = "off"
            elif action == "toggle":
                current_state["status"] = "off" if current_state["status"] == "on" else "on"
            elif action == "brighten":
                current_state["brightness"] = min(100, current_state["brightness"] + 20)
                current_state["status"] = "on"
            elif action == "dim":
                current_state["brightness"] = max(0, current_state["brightness"] - 20)
                if current_state["brightness"] == 0:
                    current_state["status"] = "off"
                else:
                    current_state["status"] = "on"
            elif action == "set_brightness" and "brightness" in parameters:
                current_state["brightness"] = max(0, min(100, parameters["brightness"]))
                current_state["status"] = "on" if parameters["brightness"] > 0 else "off"
            elif action == "set_color_temp" and "color_temp" in parameters:
                current_state["color_temp"] = max(2700, min(6500, parameters["color_temp"]))
                current_state["status"] = "on"
        
        elif device == "desk_lamp":
            if action == "on":
                current_state["status"] = "on"
            elif action == "off":
                current_state["status"] = "off"
            elif action == "toggle":
                current_state["status"] = "off" if current_state["status"] == "on" else "on"
            elif action == "set_brightness" and "brightness" in parameters:
                current_state["brightness"] = max(0, min(100, parameters["brightness"]))
                current_state["status"] = "on" if parameters["brightness"] > 0 else "off"
        
        elif device == "fan":
            if action == "on":
                current_state["status"] = "on"
            elif action == "off":
                current_state["status"] = "off"
            elif action == "toggle":
                current_state["status"] = "off" if current_state["status"] == "on" else "on"
            elif action == "set_speed" and "speed" in parameters:
                current_state["speed"] = max(1, min(5, parameters["speed"]))
                current_state["status"] = "on"
            elif action == "toggle_oscillation":
                current_state["oscillation"] = not current_state["oscillation"]
        
        elif device == "ac":
            if action == "on":
                current_state["status"] = "on"
            elif action == "off":
                current_state["status"] = "off"
            elif action == "toggle":
                current_state["status"] = "off" if current_state["status"] == "on" else "on"
            elif action == "set_temperature" and "temperature" in parameters:
                current_state["temperature"] = max(16, min(32, parameters["temperature"]))
                current_state["status"] = "on"
        
        elif device == "curtain":
            if action == "open":
                current_state["status"] = "open"
                current_state["position"] = 100
            elif action == "close":
                current_state["status"] = "closed"
                current_state["position"] = 0
            elif action == "set_position" and "position" in parameters:
                position = max(0, min(100, parameters["position"]))
                current_state["position"] = position
                current_state["status"] = "open" if position > 0 else "closed"
        
        # Update device state
        device_states[device][location] = current_state
        
        # Broadcast update to connected devices
        await broadcast_device_update(device, location)
        
        # Update related sensor data (simulate environmental impact)
        await update_environmental_impact(device, action, location, current_state)
        
        return {
            "status": "success",
            "device": device,
            "location": location,
            "action": action,
            "parameters": parameters,
            "current_state": current_state
        }
    
    except Exception as e:
        logger.error(f"Error executing enhanced command: {str(e)}")
        return {
            "status": "error",
            "message": f"Error executing command: {str(e)}",
            "device": device,
            "location": location,
            "action": action
        }

async def execute_scene_mode(scene_name, location=None):
    """Execute predefined scene modes"""
    scene_commands = []
    
    if scene_name == "home_mode":
        scene_commands = [
            {"device": "ceiling_light", "action": "on", "location": "living_room", "parameters": {"brightness": 70}},
            {"device": "ac", "action": "on", "location": "living_room", "parameters": {"temperature": 25}},
        ]
    elif scene_name == "sleep_mode":
        scene_commands = [
            {"device": "ceiling_light", "action": "off", "location": "bedroom"},
            {"device": "desk_lamp", "action": "off", "location": "bedroom"},
        ]
    elif scene_name == "work_mode":
        scene_commands = [
            {"device": "ceiling_light", "action": "on", "location": "study", "parameters": {"brightness": 90}},
            {"device": "desk_lamp", "action": "on", "location": "study", "parameters": {"brightness": 80}},
        ]
    
    # Execute scene commands
    results = []
    for cmd in scene_commands:
        try:
            device = cmd["device"]
            action = cmd["action"]
            location = cmd["location"]
            parameters = cmd.get("parameters", {})
            
            result = await execute_enhanced_command(device, action, location, parameters)
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error in scene command: {str(e)}")
            results.append({
                "status": "error",
                "message": str(e),
                "command": cmd
            })
    
    return results

async def manage_device_timers():
    """Manage device timers in background"""
    while True:
        try:
            current_time = time.time()
            expired_timers = []
            
            for timer_id, timer_info in active_timers.items():
                if current_time >= timer_info["expire_time"]:
                    device = timer_info["device"]
                    location = timer_info["location"]
                    
                    if device in device_states and location in device_states[device]:
                        device_states[device][location]["status"] = "off"
                        device_states[device][location]["timer"] = 0
                        
                        await broadcast_device_update(device, location)
                        logger.info(f"Timer expired: {device} at {location} turned off")
                    
                    expired_timers.append(timer_id)
            
            for timer_id in expired_timers:
                del active_timers[timer_id]
            
            await asyncio.sleep(10)
            
        except Exception as e:
            logger.error(f"Error in timer management: {str(e)}")
            await asyncio.sleep(30)

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await websocket.accept()
    client_id = str(uuid.uuid4())
    connected_devices[client_id] = websocket
    
    logger.info(f"WebSocket client {client_id} connected")
    
    try:
        # Send initial state to new client
        await websocket.send_json({
            "type": "init",
            "devices": device_states,
            "timestamp": time.time(),
            "message": "Connected to IoT Control Service"
        })
        
        # Handle incoming messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            try:
                command_type = message.get("type")
                logger.info(f"Received WebSocket command: {command_type} from {client_id}")
                
                if command_type == "control":
                    commands = message.get("commands", [])
                    results = []
                    
                    for cmd in commands:
                        device = cmd.get("device")
                        action = cmd.get("action")
                        location = cmd.get("location")
                        parameters = cmd.get("parameters", {})
                        
                        if all([device, action, location]):
                            result = await execute_enhanced_command(device, action, location, parameters)
                            results.append(result)
                    
                    await websocket.send_json({
                        "type": "control_results",
                        "results": results,
                        "timestamp": time.time()
                    })
                
                elif command_type == "get_sensors":
                    location = message.get("location")
                    if location:
                        sensors = device_states.get("sensors", {}).get(location, {})
                        await websocket.send_json({
                            "type": "sensor_data",
                            "location": location,
                            "sensors": sensors,
                            "timestamp": time.time()
                        })
                    else:
                        await websocket.send_json({
                            "type": "all_sensors",
                            "sensors": device_states.get("sensors", {}),
                            "timestamp": time.time()
                        })
                
                elif command_type == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": time.time()
                    })
                
                elif command_type == "get_status":
                    await websocket.send_json({
                        "type": "status_response",
                        "devices": device_states,
                        "sensors": device_states.get("sensors", {}),
                        "connected_clients": len(connected_devices),
                        "timestamp": time.time()
                    })
                
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown command type: {command_type}"
                    })
            
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket client {client_id} disconnected")
    
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {str(e)}")
    
    finally:
        if client_id in connected_devices:
            del connected_devices[client_id]

# Simulate realistic environmental changes
async def simulate_environmental_changes():
    """Simulate realistic environmental sensor changes - but preserve real data"""
    while True:
        await asyncio.sleep(30)  # Update every 30 seconds
        
        for location, sensors in device_states.get("sensors", {}).items():
            # 检查是否有真实数据，如果有且是最近的（5分钟内），则不覆盖
            if sensors.get("real_data", False):
                last_real_update = sensors.get("last_real_update", 0)
                time_since_update = time.time() - last_real_update
                
                # 如果真实数据是5分钟内的，跳过模拟更新
                if time_since_update < 300:  # 5分钟 = 300秒
                    logger.info(f"🔒 Preserving REAL sensor data for {location} (updated {time_since_update:.0f}s ago)")
                    continue
                else:
                    # 超过5分钟没有真实数据，恢复模拟
                    logger.info(f"⏰ Real data for {location} is old ({time_since_update:.0f}s), resuming simulation")
                    sensors["real_data"] = False
            
            # 执行原有的模拟逻辑
            current_temp = sensors.get("temperature", 23)
            
            # 基于时间的温度变化
            hour = time.localtime().tm_hour
            if 6 <= hour <= 18:  # 白天
                target_temp = 24 + random.uniform(-1, 2)
            else:  # 夜间
                target_temp = 22 + random.uniform(-1, 1)
            
            # 渐进式温度变化
            temp_diff = target_temp - current_temp
            sensors["temperature"] = round(current_temp + temp_diff * 0.1, 1)
            
            # 自然湿度变化
            sensors["humidity"] = max(40, min(80, 
                sensors.get("humidity", 55) + random.uniform(-2, 2)))
            
            # CO2自然变化，带有基于时间的模式
            base_co2 = 400 if 22 <= hour or hour <= 6 else 450  # 夜间较低
            sensors["co2"] = max(350, min(1000,
                base_co2 + random.uniform(-20, 40)))
            
            # VOC轻微变化
            sensors["voc"] = max(5, min(50,
                sensors.get("voc", 15) + random.uniform(-2, 3)))
            
            # 基于时间和天气模拟的光照级别
            if 6 <= hour <= 8:  # 早晨
                sensors["light_level"] = 200 + hour * 50 + random.uniform(-50, 50)
            elif 8 <= hour <= 17:  # 白天
                base_light = 500 + random.uniform(-100, 200)
                # 模拟多云/晴天天气
                weather_factor = random.choice([0.7, 0.8, 0.9, 1.0, 1.1])
                sensors["light_level"] = int(base_light * weather_factor)
            elif 17 <= hour <= 20:  # 傍晚
                sensors["light_level"] = max(50, 400 - (hour - 17) * 80 + random.uniform(-30, 30))
            else:  # 夜间
                sensors["light_level"] = max(10, 50 + random.uniform(-20, 20))
            
            # 偶尔的运动检测模拟
            if random.random() < 0.1:  # 10% 概率
                sensors["motion"] = True
                # 运动检测持续2分钟
                asyncio.create_task(reset_motion_detection(location))
            
            # 更新时间戳
            sensors["last_update"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        
        # 广播传感器更新
        for location in device_states.get("sensors", {}):
            await broadcast_sensor_update(location)

async def reset_motion_detection(location):
    """Reset motion detection after 2 minutes"""
    await asyncio.sleep(120)  # 2 minutes
    if location in device_states.get("sensors", {}):
        device_states["sensors"][location]["motion"] = False
        await broadcast_sensor_update(location)

@app.on_event("startup")
async def startup_event():
    """Event handler for application startup"""
    logger.info("🚀 IoT Control Service starting up...")
    
    # Start environmental simulation
    asyncio.create_task(simulate_environmental_changes())
    
    # Start timer management
    asyncio.create_task(manage_device_timers())
    
    # Initialize device states
    logger.info(f"📊 Initialized {len(device_states)} device categories")
    for device_type, locations in device_states.items():
        if device_type != "sensors":
            logger.info(f"  {device_type}: {len(locations)} locations")
        else:
            logger.info(f"  sensors: {len(locations)} locations")
    
    logger.info("✅ IoT Control Service startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Event handler for application shutdown"""
    logger.info("🛑 IoT Control Service shutting down...")
    
    # Cancel all active timers
    active_timers.clear()
    
    # Close all WebSocket connections
    for client_id, websocket in connected_devices.items():
        try:
            await websocket.close()
        except:
            pass
    
    connected_devices.clear()
    
    logger.info("✅ IoT Control Service shutdown complete")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8002, reload=False)