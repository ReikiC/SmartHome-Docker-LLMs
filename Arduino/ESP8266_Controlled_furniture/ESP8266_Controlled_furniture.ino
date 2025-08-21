#include <ESP8266WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_NeoPixel.h>

// ===== 家具配置宏 =====
#define ENABLE_DESK_LAMP true      // 台灯
#define ENABLE_CEILING_LIGHT true  // WS2812顶灯
#define ENABLE_FAN true            // 风扇

// ===== 硬件引脚配置 =====
#define DESK_LAMP_PIN 5    // GPIO5 (D1)
#define FAN_PIN 12         // GPIO12 (D6) 
#define WS2812_PIN 4       // GPIO4 (D2)
#define WS2812_COUNT 60            // WS2812 LED数量

// ===== 网络配置 =====
const char* ssid = "CE-Dankao";
const char* password = "CELAB2025";

// 服务器配置
const char* server_host = "192.168.153.177";
const int server_port = 8002;
const char* server_path = "/ws";

// 房间配置
const char* TARGET_ROOM = "living_room";  // 修改这里指定目标房间

// WebSocket客户端
WebSocketsClient webSocket;

// 状态变量
bool wifiConnected = false;
bool wsConnected = false;

// ===== 设备状态 =====
struct DeviceState {
  bool status;
  int brightness;
  int color_temp;
};

#if ENABLE_DESK_LAMP
DeviceState desk_lamp = {false, 50, 3000};
#endif

#if ENABLE_CEILING_LIGHT
DeviceState ceiling_light = {false, 50, 4000};
Adafruit_NeoPixel strip(WS2812_COUNT, WS2812_PIN, NEO_GRB + NEO_KHZ800);
#endif

#if ENABLE_FAN
bool fan_status = false;  // 风扇只需要开关状态
#endif

// ===== WiFi连接函数 =====
void connectWiFi() {
  Serial.printf("📶 Connecting to: %s\n", ssid);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(1000);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    Serial.println("\n✅ WiFi Connected!");
    Serial.printf("📍 ESP8266 IP: %s\n", WiFi.localIP().toString().c_str());
    Serial.printf("📡 Signal: %d dBm\n", WiFi.RSSI());
  } else {
    wifiConnected = false;
    Serial.println("\n❌ WiFi failed!");
  }
}

// ===== WS2812控制函数 =====
#if ENABLE_CEILING_LIGHT
void updateCeilingLight() {
  if (ceiling_light.status) {
    // 根据色温和亮度计算RGB值
    int brightness = map(ceiling_light.brightness, 0, 100, 0, 255);
    
    // 简化的色温转换（2700K暖白 - 6500K冷白）
    int warmth = map(ceiling_light.color_temp, 2700, 6500, 255, 0);
    int r = brightness;
    int g = (brightness * (255 - warmth / 2)) / 255;
    int b = (brightness * warmth) / 255;
    
    // 设置所有LED
    for(int i = 0; i < WS2812_COUNT; i++) {
      strip.setPixelColor(i, strip.Color(r, g, b));
    }
  } else {
    // 关闭所有LED
    for(int i = 0; i < WS2812_COUNT; i++) {
      strip.setPixelColor(i, strip.Color(0, 0, 0));
    }
  }
  strip.show();
}
#endif

// ===== 台灯控制函数 =====
#if ENABLE_DESK_LAMP
void updateDeskLamp() {
  if (desk_lamp.status) {
    // PWM控制亮度
    int pwmValue = map(desk_lamp.brightness, 0, 100, 0, 1023);
    analogWrite(DESK_LAMP_PIN, pwmValue);
  } else {
    digitalWrite(DESK_LAMP_PIN, LOW);
  }
}
#endif

// ===== 风扇控制函数 =====
#if ENABLE_FAN
void updateFan() {
  digitalWrite(FAN_PIN, fan_status ? HIGH : LOW);
}
#endif

// ===== 处理IoT控制消息 =====
void handleControlMessage(JsonObject& command) {
  String device = command["device"].as<String>();
  String action = command["action"].as<String>();
  String location = command["location"].as<String>();
  
  // 只处理目标房间的命令
  if (location != TARGET_ROOM) {
    Serial.printf("🚫 Ignoring command for room: %s\n", location.c_str());
    return;
  }
  
  JsonObject params = command["parameters"];
  
  Serial.printf("🎮 Processing command - Device: %s, Action: %s\n", 
                device.c_str(), action.c_str());
  
  // 处理顶灯命令
  #if ENABLE_CEILING_LIGHT
  if (device == "ceiling_light") {
    if (action == "on") {
      ceiling_light.status = true;
    } else if (action == "off") {
      ceiling_light.status = false;
    } else if (action == "toggle") {
      ceiling_light.status = !ceiling_light.status;
    } else if (action == "set_brightness" && params.containsKey("brightness")) {
      ceiling_light.brightness = params["brightness"];
      ceiling_light.status = (ceiling_light.brightness > 0);
    } else if (action == "set_color_temp" && params.containsKey("color_temp")) {
      ceiling_light.color_temp = params["color_temp"];
    }
    updateCeilingLight();
    Serial.printf("💡 Ceiling light - Status: %s, Brightness: %d%%, Color temp: %dK\n", 
                  ceiling_light.status ? "ON" : "OFF", 
                  ceiling_light.brightness, 
                  ceiling_light.color_temp);
  }
  #endif
  
  // 处理台灯命令
  #if ENABLE_DESK_LAMP
  if (device == "desk_lamp") {
    if (action == "on") {
      desk_lamp.status = true;
    } else if (action == "off") {
      desk_lamp.status = false;
    } else if (action == "toggle") {
      desk_lamp.status = !desk_lamp.status;
    } else if (action == "set_brightness" && params.containsKey("brightness")) {
      desk_lamp.brightness = params["brightness"];
      desk_lamp.status = (desk_lamp.brightness > 0);
    }
    updateDeskLamp();
    Serial.printf("🛋️ Desk lamp - Status: %s, Brightness: %d%%\n", 
                  desk_lamp.status ? "ON" : "OFF", 
                  desk_lamp.brightness);
  }
  #endif
  
  // 处理风扇命令
  #if ENABLE_FAN
  if (device == "fan") {
    if (action == "on") {
      fan_status = true;
    } else if (action == "off") {
      fan_status = false;
    } else if (action == "toggle") {
      fan_status = !fan_status;
    }
    updateFan();
    Serial.printf("🌀 Fan - Status: %s\n", 
                  fan_status ? "ON" : "OFF");
  }
  #endif
}

// ===== WebSocket消息处理 =====
void handleMessage(const char* message) {
  DynamicJsonDocument doc(1024);
  DeserializationError error = deserializeJson(doc, message);
  
  if (error) {
    Serial.printf("❌ JSON parse error: %s\n", error.c_str());
    return;
  }
  
  String type = doc["type"].as<String>();
  
  Serial.printf("📨 Message type: %s\n", type.c_str());
  
  if (type == "control") {
    // 处理控制命令
    if (doc["commands"].is<JsonArray>()) {
      JsonArray commands = doc["commands"];
      for (JsonObject command : commands) {
        handleControlMessage(command);
      }
    }
  } else if (type == "control_results") {
    // 处理控制结果反馈
    Serial.println("✅ Control command acknowledged by server");
  } else if (type == "init") {
    Serial.println("🏠 IoT Service initialized");
    sendDeviceStatus();
  }
}

// ===== 发送设备状态 =====
void sendDeviceStatus() {
  if (!wsConnected) return;
  
  DynamicJsonDocument doc(512);
  doc["type"] = "device_status";
  doc["device_id"] = WiFi.macAddress();
  doc["location"] = TARGET_ROOM;
  
  JsonObject devices = doc.createNestedObject("devices");
  
  #if ENABLE_CEILING_LIGHT
  JsonObject cl = devices.createNestedObject("ceiling_light");
  cl["status"] = ceiling_light.status ? "on" : "off";
  cl["brightness"] = ceiling_light.brightness;
  cl["color_temp"] = ceiling_light.color_temp;
  #endif
  
  #if ENABLE_DESK_LAMP
  JsonObject dl = devices.createNestedObject("desk_lamp");
  dl["status"] = desk_lamp.status ? "on" : "off";
  dl["brightness"] = desk_lamp.brightness;
  #endif
  
  #if ENABLE_FAN
  JsonObject f = devices.createNestedObject("fan");
  f["status"] = fan_status ? "on" : "off";
  #endif
  
  String message;
  serializeJson(doc, message);
  webSocket.sendTXT(message);
  
  Serial.println("📤 Device status sent");
}

// ===== WebSocket事件处理 =====
void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  switch(type) {
    case WStype_DISCONNECTED:
      wsConnected = false;
      Serial.println("🔴 Disconnected from IoT Service");
      break;
      
    case WStype_CONNECTED:
      wsConnected = true;
      Serial.printf("🟢 Connected to IoT Service: %s\n", payload);
      
      // 发送初始化消息
      sendDeviceStatus();
      break;
      
    case WStype_TEXT:
      Serial.printf("📨 Received: %s\n", payload);
      handleMessage((char*)payload);
      break;
      
    case WStype_ERROR:
      Serial.printf("❌ Error: %s\n", payload);
      break;
  }
}

// ===== 初始化WebSocket =====
void initWebSocket() {
  Serial.printf("🔌 Connecting to WebSocket: ws://%s:%d%s\n", 
                server_host, server_port, server_path);
  
  webSocket.begin(server_host, server_port, server_path);
  webSocket.onEvent(webSocketEvent);
  webSocket.setReconnectInterval(5000);
}

// ===== Setup函数 =====
void setup() {
  Serial.begin(115200);
  delay(1000);  // 增加延迟等待串口稳定
  
  // 清除串口缓冲区
  while(Serial.available()) {
    Serial.read();
  }
  
  // 输出一些空行来分隔乱码
  Serial.println("\n\n\n");
  
  Serial.println("============================================================");
  Serial.printf("🏠 ESP8266 IoT Furniture Controller - Room: %s\n", TARGET_ROOM);
  Serial.println("============================================================");
  
  // 显示启用的设备
  Serial.println("\n📋 Enabled devices:");
  #if ENABLE_DESK_LAMP
  Serial.println("   ✅ Desk Lamp");
  #endif
  #if ENABLE_CEILING_LIGHT
  Serial.println("   ✅ Ceiling Light (WS2812)");
  #endif
  #if ENABLE_FAN
  Serial.println("   ✅ Fan");
  #endif
  
  // 初始化硬件引脚
  Serial.println("\n🔧 Initializing hardware...");
  
  #if ENABLE_DESK_LAMP
  pinMode(DESK_LAMP_PIN, OUTPUT);
  digitalWrite(DESK_LAMP_PIN, LOW);
  Serial.println("   ✅ Desk lamp pin configured");
  #endif
  
  #if ENABLE_CEILING_LIGHT
  strip.begin();
  strip.show(); // 初始化所有LED为关闭状态
  Serial.printf("   ✅ WS2812 initialized with %d LEDs\n", WS2812_COUNT);
  #endif
  
  #if ENABLE_FAN
  pinMode(FAN_PIN, OUTPUT);
  digitalWrite(FAN_PIN, LOW);
  Serial.println("   ✅ Fan pin configured");
  #endif
  
  // 连接WiFi
  Serial.println("\n📶 Connecting to network...");
  connectWiFi();
  
  if (wifiConnected) {
    delay(2000);
    initWebSocket();
  } else {
    Serial.println("❌ Cannot proceed without WiFi connection");
  }
  
  Serial.println("\n✅ Setup complete!");
  Serial.println("============================================================\n");
}

// ===== 主循环 =====
void loop() {
  // 检查WiFi连接
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("❌ WiFi lost, reconnecting...");
    connectWiFi();
    if (wifiConnected) {
      initWebSocket();
    }
    return;
  }
  
  // 处理WebSocket
  webSocket.loop();
  
  // 定期发送心跳/状态更新（每30秒）
  static unsigned long lastStatusUpdate = 0;
  if (wsConnected && (millis() - lastStatusUpdate >= 30000)) {
    sendDeviceStatus();
    lastStatusUpdate = millis();
  }
  
  // 添加看门狗喂狗
  yield();
  delay(10);
}