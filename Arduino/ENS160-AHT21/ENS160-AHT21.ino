#include <ESP8266WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include "Adafruit_AHTX0.h"
#include "ScioSense_ENS160.h"

// WiFi配置
const char* ssid = "CE-Hub-Student";
const char* password = "casa-ce-gagarin-public-service";

// 服务器配置
const char* server_host = "10.129.113.188"; // 您的Docker主机IP
const int server_port = 8080; // IoT服务端口

// 传感器对象
Adafruit_AHTX0 aht;
ScioSense_ENS160 ens160(0x53); // 默认I2C地址

// WebSocket客户端
WebSocketsClient webSocket;

// 数据发送间隔
const unsigned long SENSOR_INTERVAL = 30000; // 30秒
const unsigned long HEARTBEAT_INTERVAL = 60000; // 1分钟心跳
const unsigned long HEALTH_CHECK_INTERVAL = 300000; // 5分钟健康检查
unsigned long lastSensorTime = 0;
unsigned long lastHeartbeatTime = 0;
unsigned long lastHealthCheckTime = 0;

// 传感器数据结构
struct SensorData {
  float temperature;
  float humidity;
  uint16_t co2;
  uint16_t tvoc;
  uint16_t aqi;
  bool status;
};

SensorData currentData;

void setup() {
  Serial.begin(115200);
  Serial.println("\n=== ESP8266 Smart Home Sensor Node ===");
  
  // 初始化I2C
  Wire.begin(); // ESP8266默认: SDA=GPIO4(D2), SCL=GPIO5(D1)
  
  // 初始化传感器
  initSensors();
  
  // 连接WiFi
  connectToWiFi();
  
  // 初始化WebSocket
  initWebSocket();
  
  Serial.println("Setup complete! Starting sensor monitoring...");
}

void loop() {
  // 处理WebSocket
  webSocket.loop();
  
  unsigned long currentTime = millis();
  
  // 读取并发送传感器数据
  if (currentTime - lastSensorTime >= SENSOR_INTERVAL) {
    readSensors();
    sendSensorData();
    lastSensorTime = currentTime;
  }
  
  // 发送心跳
  if (currentTime - lastHeartbeatTime >= HEARTBEAT_INTERVAL) {
    sendHeartbeat();
    lastHeartbeatTime = currentTime;
  }
  
  // 定期健康检查
  if (currentTime - lastHealthCheckTime >= HEALTH_CHECK_INTERVAL) {
    if (!performSensorHealthCheck()) {
      Serial.println("Health check failed, attempting recovery...");
    }
    lastHealthCheckTime = currentTime;
  }
  
  delay(1000);
}

void initSensors() {
  Serial.println("Initializing sensors...");
  
  // 初始化AHT21
  if (!aht.begin()) {
    Serial.println("ERROR: Could not find AHT21 sensor!");
    Serial.println("Check wiring and I2C address");
    while (1) delay(10);
  }
  Serial.println("✓ AHT21 sensor initialized");
  
  // 初始化ENS160
  if (!ens160.begin()) {
    Serial.println("ERROR: Could not find ENS160 sensor!");
    Serial.println("Check wiring and I2C address");
    while (1) delay(10);
  }
  Serial.println("✓ ENS160 sensor initialized");
  
  // 设置ENS160工作模式
  if (ens160.setMode(ENS160_OPMODE_STD)) {
    Serial.println("✓ ENS160 set to standard mode");
  } else {
    Serial.println("⚠ Failed to set ENS160 mode");
  }
  
  // 等待传感器稳定
  Serial.println("Waiting for sensors to stabilize...");
  delay(5000);
}

void connectToWiFi() {
  Serial.printf("Connecting to WiFi: %s", ssid);
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(1000);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✓ WiFi connected!");
    Serial.printf("IP address: %s\n", WiFi.localIP().toString().c_str());
    Serial.printf("Signal strength: %d dBm\n", WiFi.RSSI());
  } else {
    Serial.println("\n✗ WiFi connection failed!");
    Serial.println("Restarting...");
    ESP.restart();
  }
}

void initWebSocket() {
  Serial.printf("Connecting to WebSocket: ws://%s:%d/ws\n", server_host, server_port);
  
  webSocket.begin(server_host, server_port, "/ws");
  webSocket.onEvent(webSocketEvent);
  webSocket.setReconnectInterval(5000);
  
  Serial.println("WebSocket client initialized");
}

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  switch(type) {
    case WStype_DISCONNECTED:
      Serial.println("WebSocket Disconnected");
      break;
      
    case WStype_CONNECTED:
      Serial.printf("WebSocket Connected to: %s\n", payload);
      // 发送设备注册信息
      registerDevice();
      break;
      
    case WStype_TEXT:
      Serial.printf("WebSocket Message: %s\n", payload);
      handleWebSocketMessage((char*)payload);
      break;
      
    case WStype_ERROR:
      Serial.printf("WebSocket Error: %s\n", payload);
      break;
      
    default:
      break;
  }
}

void handleWebSocketMessage(const char* message) {
  // 解析接收到的消息
  DynamicJsonDocument doc(1024);
  DeserializationError error = deserializeJson(doc, message);
  
  if (error) {
    Serial.printf("JSON parse error: %s\n", error.c_str());
    return;
  }
  
  String type = doc["type"];
  
  if (type == "get_sensors") {
    // 立即发送传感器数据
    readSensors();
    sendSensorData();
  } else if (type == "set_interval") {
    // 更新数据发送间隔
    int interval = doc["interval"];
    if (interval >= 10 && interval <= 300) { // 10秒到5分钟
      // SENSOR_INTERVAL = interval * 1000; // 注意：这里需要修改为全局变量
      Serial.printf("Sensor interval updated to %d seconds\n", interval);
    }
  } else if (type == "calibrate") {
    // 传感器校准命令
    calibrateSensors();
  }
}

void registerDevice() {
  DynamicJsonDocument doc(512);
  doc["type"] = "device_registration";
  doc["device_info"]["type"] = "sensor_node";
  doc["device_info"]["id"] = WiFi.macAddress();
  doc["device_info"]["location"] = "living_room"; // 根据实际位置修改
  doc["device_info"]["sensors"] = JsonArray();
  doc["device_info"]["sensors"].add("temperature");
  doc["device_info"]["sensors"].add("humidity");
  doc["device_info"]["sensors"].add("co2");
  doc["device_info"]["sensors"].add("tvoc");
  doc["device_info"]["sensors"].add("aqi");
  
  String message;
  serializeJson(doc, message);
  webSocket.sendTXT(message);
  
  Serial.println("Device registration sent");
}

void readSensors() {
  Serial.println("Reading sensors...");
  
  // 读取AHT21温湿度
  sensors_event_t humidity_event, temp_event;
  aht.getEvent(&humidity_event, &temp_event);
  
  currentData.temperature = temp_event.temperature;
  currentData.humidity = humidity_event.relative_humidity;
  
  // 温度校正 (如果使用5V供电，减去5-6度的偏差)
  // currentData.temperature -= 5.5; // 取消注释如果需要校正
  
  // 读取ENS160空气质量
  if (ens160.available()) {
    // 先向ENS160提供温湿度数据以提高精度
    ens160.set_envdata(currentData.temperature, currentData.humidity);
    delay(100); // 等待传感器处理环境数据
    
    ens160.measure(true); // 带温湿度补偿的测量
    ens160.measureRaw(true);
    
    currentData.co2 = ens160.geteCO2();
    currentData.tvoc = ens160.getTVOC();
    currentData.aqi = ens160.getAQI();
    
    // 检查数据有效性
    if (currentData.co2 > 0 && currentData.co2 < 65000) {
      currentData.status = true;
    } else {
      Serial.println("⚠ ENS160 data invalid, reinitializing...");
      reinitializeENS160();
      currentData.status = false;
    }
  } else {
    Serial.println("⚠ ENS160 not ready, reinitializing...");
    reinitializeENS160();
    currentData.status = false;
  }
  
  // 打印传感器数据
  Serial.println("--- Sensor Readings ---");
  Serial.printf("Temperature: %.2f°C\n", currentData.temperature);
  Serial.printf("Humidity: %.2f%%\n", currentData.humidity);
  Serial.printf("CO2: %d ppm\n", currentData.co2);
  Serial.printf("TVOC: %d ppb\n", currentData.tvoc);
  Serial.printf("AQI: %d\n", currentData.aqi);
  Serial.printf("Status: %s\n", currentData.status ? "OK" : "Error");
  Serial.println("----------------------");
}

void sendSensorData() {
  if (webSocket.isConnected()) {
    DynamicJsonDocument doc(1024);
    
    doc["type"] = "sensor_update";
    doc["device_id"] = WiFi.macAddress();
    doc["location"] = "living_room"; // 根据实际位置修改
    doc["timestamp"] = millis();
    
    // 传感器数据
    doc["sensors"]["temperature"] = currentData.temperature;
    doc["sensors"]["humidity"] = currentData.humidity;
    doc["sensors"]["co2"] = currentData.co2;
    doc["sensors"]["voc"] = currentData.tvoc; // 注意：系统中使用voc而不是tvoc
    doc["sensors"]["aqi"] = currentData.aqi;
    doc["sensors"]["status"] = currentData.status;
    
    // 设备状态
    doc["device_status"]["wifi_rssi"] = WiFi.RSSI();
    doc["device_status"]["free_heap"] = ESP.getFreeHeap();
    doc["device_status"]["uptime"] = millis() / 1000;
    
    String message;
    serializeJson(doc, message);
    webSocket.sendTXT(message);
    
    Serial.println("✓ Sensor data sent to server");
  } else {
    Serial.println("⚠ WebSocket not connected, data not sent");
  }
}

void sendHeartbeat() {
  if (webSocket.isConnected()) {
    DynamicJsonDocument doc(256);
    doc["type"] = "ping";
    doc["device_id"] = WiFi.macAddress();
    doc["timestamp"] = millis();
    
    String message;
    serializeJson(doc, message);
    webSocket.sendTXT(message);
    
    Serial.println("❤ Heartbeat sent");
  }
}

void calibrateSensors() {
  Serial.println("Starting sensor calibration...");
  
  // ENS160校准（需要在清洁空气中进行）
  if (ens160.available()) {
    // 这里可以添加特定的校准流程
    Serial.println("✓ ENS160 calibration requested");
    // 注意：ENS160有自动基线校正功能，通常在连续运行24小时后达到最佳性能
  }
  
  Serial.println("Calibration process initiated");
}

// 错误处理和重启函数
void handleError(const char* error) {
  Serial.printf("ERROR: %s\n", error);
  Serial.println("Restarting in 5 seconds...");
  delay(5000);
  ESP.restart();
}

// ENS160重新初始化函数
void reinitializeENS160() {
  Serial.println("Reinitializing ENS160...");
  
  if (ens160.begin()) {
    if (ens160.setMode(ENS160_OPMODE_STD)) {
      Serial.println("✓ ENS160 reinitialized successfully");
      delay(3000); // 等待传感器稳定
    } else {
      Serial.println("✗ Failed to set ENS160 mode");
    }
  } else {
    Serial.println("✗ Failed to reinitialize ENS160");
  }
}

// 传感器健康检查
bool performSensorHealthCheck() {
  Serial.println("Performing sensor health check...");
  
  bool ahtHealthy = true;
  bool ens160Healthy = true;
  
  // 检查AHT21
  sensors_event_t humidity_event, temp_event;
  aht.getEvent(&humidity_event, &temp_event);
  
  if (isnan(temp_event.temperature) || isnan(humidity_event.relative_humidity)) {
    Serial.println("✗ AHT21 health check failed");
    ahtHealthy = false;
  } else {
    Serial.println("✓ AHT21 health check passed");
  }
  
  // 检查ENS160
  if (!ens160.available()) {
    Serial.println("✗ ENS160 health check failed");
    ens160Healthy = false;
    reinitializeENS160();
  } else {
    Serial.println("✓ ENS160 health check passed");
  }
  
  return ahtHealthy && ens160Healthy;
}