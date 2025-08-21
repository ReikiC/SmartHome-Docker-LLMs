// WiFi配置
// const char* ssid = "CE-Hub-Student";
// const char* password = "casa-ce-gagarin-public-service";
// const char* ssid = "CE-Dankao";
// const char* password = "CELAB2025";
const char* ssid = "CE-Wlan-Helper";
const char* password = "ThanksDankao";

// 服务器配置
// const char* server_host = "10.129.113.188";
const char* server_host = "192.168.8.194";
const int server_port = 8002; // IoT服务端口
const char* server_path = "/ws";

// 房间配置 - 只处理指定房间的数据
const char* TARGET_ROOM = "living_room";  // 修改这里指定目标房间
// const char* TARGET_ROOM = "bedroom";     // 卧室
// const char* TARGET_ROOM = "kitchen";     // 厨房
// const char* TARGET_ROOM = "study";       // 书房
// const char* TARGET_ROOM = "bathroom";    // 浴室

// WebSocket客户端
WebSocketsClient webSocket;

// 状态
bool wifiConnected = false;
bool wsConnected = false;

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

void sendSensorData() {
  if (!wsConnected) {
    Serial.println("⚠️ Cannot send sensor data - not connected");
    return;
  }
  
  // 使用真实传感器数据，如果数据无效则使用备用值
  float temperature, humidity;
  int co2, voc, light_level;
  bool motion;
  
  if (g_sensor_data_valid && isSensorDataValid()) {
    // 使用真实传感器数据
    temperature = g_temperature;
    humidity = g_humidity;
    co2 = g_co2;
    voc = g_voc;
    light_level = g_light_level;
    motion = g_motion;
    
    Serial.printf("📊 Using REAL sensor data for room: %s\n", TARGET_ROOM);
    Serial.printf("   🌡️ 真实温度: %.1f°C, 湿度: %.1f%%\n", temperature, humidity);
    Serial.printf("   🌬️ 真实CO2: %dppm, VOC: %dppb, 光照: %dlux\n", co2, voc, light_level);
  } else {
    // 使用模拟数据作为备用
    temperature = 23.5 + random(-50, 50) / 100.0; // 23.0-24.0°C
    humidity = 55.0 + random(-200, 200) / 100.0;  // 53.0-57.0%
    co2 = 420 + random(-50, 80);                  // 370-500 ppm
    voc = 15 + random(-10, 25);                   // 5-40 ppb
    light_level = 300 + random(-100, 300);        // 200-600 lux
    motion = (random(0, 100) < 10);               // 10% 概率有人
    
    Serial.printf("⚠️ Using SIMULATED data for room: %s (real sensor data not available)\n", TARGET_ROOM);
    Serial.printf("   🎲 模拟温度: %.1f°C, 湿度: %.1f%%\n", temperature, humidity);
    Serial.printf("   🎲 模拟CO2: %dppm, VOC: %dppb, 光照: %dlux\n", co2, voc, light_level);
  }

  // 只发送指定房间的传感器数据
  DynamicJsonDocument doc(1024);
  doc["type"] = "control";
  
  JsonArray commands = doc.createNestedArray("commands");
  JsonObject sensorCmd = commands.createNestedObject();
  sensorCmd["device"] = "sensors";
  sensorCmd["action"] = "data_update";
  sensorCmd["location"] = TARGET_ROOM;  // 使用指定的房间
  
  JsonObject params = sensorCmd.createNestedObject("parameters");
  params["temperature"] = temperature;
  params["humidity"] = humidity;
  params["co2"] = co2;
  params["voc"] = voc;
  params["light_level"] = light_level;
  params["motion"] = motion;
  params["device_id"] = WiFi.macAddress();
  params["source"] = g_sensor_data_valid ? "esp8266_real_sensors" : "esp8266_simulated";
  params["data_type"] = g_sensor_data_valid ? "real" : "simulated";
  params["timestamp"] = millis();
  
  String message;
  serializeJson(doc, message);
  
  Serial.printf("📤 准备上传传感器数据到房间: %s\n", TARGET_ROOM);
  Serial.printf("📊 数据类型: %s\n", g_sensor_data_valid ? "真实传感器数据" : "模拟数据");
  Serial.printf("📤 发送消息: %s\n", message.c_str());
  
  bool result = webSocket.sendTXT(message);
  Serial.printf("📤 上传结果: %s\n", result ? "成功" : "失败");
  
  // 如果是真实数据，额外打印确认信息
  if (g_sensor_data_valid && isSensorDataValid()) {
    Serial.printf("✅ 成功上传真实传感器数据到服务器！\n");
  }
}

void handleMessage(const char* message) {
  DynamicJsonDocument doc(1024);
  DeserializationError error = deserializeJson(doc, message);
  
  if (error) {
    Serial.printf("❌ JSON parse error: %s\n", error.c_str());
    return;
  }
  
  String type = doc["type"].as<String>();
  String location = doc["location"].as<String>();
  
  // 只处理目标房间的消息，忽略其他房间的数据
  if (!location.isEmpty() && location != TARGET_ROOM) {
    Serial.printf("🚫 Ignoring message from room: %s (not our target room: %s)\n", 
                  location.c_str(), TARGET_ROOM);
    return;
  }
  
  Serial.printf("📋 Processing message type: %s for room: %s\n", type.c_str(), TARGET_ROOM);
  
  if (type == "init") {
    Serial.printf("✅ IoT Service initialization received for room: %s\n", TARGET_ROOM);
    
    // 只显示目标房间的设备状态
    if (doc["devices"].is<JsonObject>()) {
      Serial.printf("🏠 Available devices in %s:\n", TARGET_ROOM);
      for (JsonPair device : doc["devices"].as<JsonObject>()) {
        Serial.printf("   - %s\n", device.key().c_str());
      }
    }
    
  } else if (type == "control_results") {
    Serial.printf("✅ Control command results received for room: %s\n", TARGET_ROOM);
    
    if (doc["results"].is<JsonArray>()) {
      for (JsonObject result : doc["results"].as<JsonArray>()) {
        String status = result["status"].as<String>();
        String device = result["device"].as<String>();
        String action = result["action"].as<String>();
        String dataType = result["parameters"]["data_type"].as<String>();
        
        Serial.printf("   📋 %s %s: %s\n", device.c_str(), action.c_str(), status.c_str());
        
        if (status == "success") {
          if (dataType == "real") {
            Serial.printf("   ✅ 真实传感器数据成功上传到房间 %s！\n", TARGET_ROOM);
          } else {
            Serial.printf("   ⚠️ 模拟传感器数据已上传到房间 %s\n", TARGET_ROOM);
          }
        } else {
          Serial.printf("   ❌ Failed: %s\n", result["message"].as<String>().c_str());
        }
      }
    }
    
  } else if (type == "sensor_update") {
    // 只处理目标房间的传感器更新
    Serial.printf("📊 Sensor update from our room: %s\n", TARGET_ROOM);
    
    if (doc["sensors"].is<JsonObject>()) {
      JsonObject sensors = doc["sensors"];
      bool realData = sensors["real_data"].as<bool>();
      String source = sensors["source"].as<String>();
      
      Serial.printf("   🌡️ Current data - Temp: %.1f°C, Humidity: %.1f%%\n", 
                    sensors["temperature"].as<float>(), 
                    sensors["humidity"].as<float>());
      Serial.printf("   💨 CO2: %dppm, VOC: %dppb\n",
                    sensors["co2"].as<int>(),
                    sensors["voc"].as<int>());
      Serial.printf("   ☀️ Light: %dlux, Motion: %s\n",
                    sensors["light_level"].as<int>(),
                    sensors["motion"].as<bool>() ? "Detected" : "None");
      Serial.printf("   📊 Data source: %s (%s)\n", 
                    source.c_str(), 
                    realData ? "Real" : "Simulated");
    }
    
  } else if (type == "device_update") {
    String device = doc["device"].as<String>();
    Serial.printf("🔌 Device update in our room %s: %s\n", TARGET_ROOM, device.c_str());
    
  } else if (type == "error") {
    String error_msg = doc["message"].as<String>();
    Serial.printf("❌ Error from server for room %s: %s\n", TARGET_ROOM, error_msg.c_str());
    
  } else {
    Serial.printf("ℹ️ Other message type for room %s: %s\n", TARGET_ROOM, type.c_str());
  }
}

// 添加一个简单的ping功能，只针对目标房间
void sendPing() {
  if (!wsConnected) return;
  
  DynamicJsonDocument doc(256);
  doc["type"] = "ping";
  doc["device_id"] = WiFi.macAddress();
  doc["location"] = TARGET_ROOM;  // 指定房间
  doc["timestamp"] = millis();
  doc["sensor_status"] = g_sensor_data_valid ? "active" : "inactive";
  
  String message;
  serializeJson(doc, message);
  
  webSocket.sendTXT(message);
  Serial.printf("🏓 Ping sent for room: %s (sensors: %s)\n", 
                TARGET_ROOM, 
                g_sensor_data_valid ? "活跃" : "不活跃");
}

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  unsigned long elapsed = millis() / 1000;
  
  switch(type) {
    case WStype_DISCONNECTED:
      wsConnected = false;
      Serial.printf("[%lus] 🔴 Disconnected from IoT Service\n", elapsed);
      break;
      
    case WStype_CONNECTED:
      wsConnected = true;
      Serial.printf("[%lus] 🟢 Connected to IoT Service: %s\n", elapsed, payload);
      Serial.printf("[%lus] 📊 Sensor status: %s\n", elapsed, g_sensor_data_valid ? "真实传感器可用" : "仅模拟数据");
      
      // 连接成功后等待3秒再发送第一条消息
      delay(3000);
      break;
      
    case WStype_TEXT:
      Serial.printf("[%lus] 📨 Received (%d bytes): %s\n", elapsed, length, payload);
      handleMessage((char*)payload);
      break;
      
    case WStype_ERROR:
      Serial.printf("[%lus] ❌ Error: %s\n", elapsed, payload);
      break;
      
    case WStype_PING:
      Serial.printf("[%lus] 🏓 Ping\n", elapsed);
      break;
      
    case WStype_PONG:
      Serial.printf("[%lus] 🏓 Pong\n", elapsed);
      break;
      
    default:
      Serial.printf("[%lus] 🔶 Event type: %d\n", elapsed, type);
      break;
  }
}

void initWebSocket() {
  Serial.printf("🔌 WebSocket: ws://%s:%d%s\n", server_host, server_port, server_path);
  
  webSocket.begin(server_host, server_port, server_path);
  webSocket.onEvent(webSocketEvent);
  webSocket.setReconnectInterval(10000);
  
  Serial.printf("⚙️ WebSocket configured for room: %s\n", TARGET_ROOM);
  Serial.printf("📊 Sensor data source: %s\n", g_sensor_data_valid ? "真实传感器" : "模拟数据");
}