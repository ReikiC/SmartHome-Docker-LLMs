#include <ESP8266WiFi.h>
#include <WebSocketsClient.h>

// WiFi配置
const char* ssid = "CE-Hub-Student";
const char* password = "casa-ce-gagarin-public-service";

// 服务器配置
const char* server_host = "10.129.113.188";
const int server_port = 8002;

// WebSocket客户端
WebSocketsClient webSocket;

// 状态
bool wifiConnected = false;
bool wsConnected = false;
unsigned long connectionTime = 0;

void setup() {
  Serial.begin(115200);
  delay(2000);
  
  Serial.println("============================================================");
  Serial.println("🔌 ESP8266 Minimal WebSocket Test");
  Serial.println("============================================================");
  
  // 连接WiFi
  connectWiFi();
  
  if (wifiConnected) {
    delay(3000); // 给网络连接更多稳定时间
    initWebSocket();
  }
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("❌ WiFi lost, reconnecting...");
    connectWiFi();
    return;
  }
  
  webSocket.loop();
  
  // 每30秒显示状态
  static unsigned long lastStatus = 0;
  if (millis() - lastStatus > 30000) {
    printStatus();
    lastStatus = millis();
  }
  
  delay(100);
}

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

void initWebSocket() {
  Serial.printf("🔌 WebSocket: ws://%s:%d/ws\n", server_host, server_port);
  
  // 最简配置
  webSocket.begin(server_host, server_port, "/ws");
  webSocket.onEvent(webSocketEvent);
  
  // 简化的重连设置
  webSocket.setReconnectInterval(10000);
  
  // 不使用心跳，避免复杂性
  // webSocket.enableHeartbeat(15000, 3000, 2);
  
  Serial.println("⚙️ WebSocket configured");
  connectionTime = millis();
}

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  unsigned long elapsed = millis() - connectionTime;
  
  switch(type) {
    case WStype_DISCONNECTED:
      wsConnected = false;
      Serial.printf("[%lus] 🔴 Disconnected\n", elapsed/1000);
      
      // 显示断开原因的更多信息
      if (length > 0) {
        Serial.printf("     Reason: %s\n", (char*)payload);
      }
      break;
      
    case WStype_CONNECTED:
      wsConnected = true;
      Serial.printf("[%lus] 🟢 Connected: %s\n", elapsed/1000, payload);
      
      // 连接成功后等待5秒再发送第一条消息
      delay(5000);
      sendSimpleMessage();
      break;
      
    case WStype_TEXT:
      Serial.printf("[%lus] 📨 Text (%d bytes): %s\n", elapsed/1000, length, payload);
      break;
      
    case WStype_BIN:
      Serial.printf("[%lus] 📦 Binary (%d bytes)\n", elapsed/1000, length);
      break;
      
    case WStype_ERROR:
      Serial.printf("[%lus] ❌ Error: %s\n", elapsed/1000, payload);
      break;
      
    case WStype_FRAGMENT_TEXT_START:
    case WStype_FRAGMENT_BIN_START:
    case WStype_FRAGMENT:
    case WStype_FRAGMENT_FIN:
      Serial.printf("[%lus] 📝 Fragment event\n", elapsed/1000);
      break;
      
    case WStype_PING:
      Serial.printf("[%lus] 🏓 Ping\n", elapsed/1000);
      break;
      
    case WStype_PONG:
      Serial.printf("[%lus] 🏓 Pong\n", elapsed/1000);
      break;
      
    default:
      Serial.printf("[%lus] 🔶 Unknown type: %d\n", elapsed/1000, type);
      break;
  }
}

void sendSimpleMessage() {
  if (!wsConnected) {
    Serial.println("⚠️ Cannot send - not connected");
    return;
  }
  
  // 发送正确格式的注册消息
  String message = "{\"type\":\"device_registration\",\"device_info\":{\"type\":\"esp8266_sensor\",\"id\":\"" + WiFi.macAddress() + "\",\"location\":\"living_room\",\"ip\":\"" + WiFi.localIP().toString() + "\"}}";
  
  Serial.printf("📤 Sending registration: %s\n", message.c_str());
  
  bool result = webSocket.sendTXT(message);
  Serial.printf("📤 Send result: %s\n", result ? "SUCCESS" : "FAILED");
}

void printStatus() {
  Serial.println("================================================");
  Serial.printf("📊 Status Report (Uptime: %lu seconds)\n", millis()/1000);
  Serial.printf("   WiFi: %s (IP: %s)\n", 
    wifiConnected ? "✅ Connected" : "❌ Disconnected",
    WiFi.localIP().toString().c_str());
  Serial.printf("   WebSocket: %s\n", wsConnected ? "✅ Connected" : "❌ Disconnected");
  Serial.printf("   Free Heap: %d bytes\n", ESP.getFreeHeap());
  Serial.printf("   RSSI: %d dBm\n", WiFi.RSSI());
  
  if (wsConnected) {
    Serial.println("🔄 Sending device registration...");
    sendSimpleMessage();
    delay(2000);
    Serial.println("🔄 Sending sensor data...");
    sendSensorData();
  }
  
  Serial.println("================================================");
}

void sendSensorData() {
  if (!wsConnected) {
    Serial.println("⚠️ Cannot send sensor data - not connected");
    return;
  }
  
  // 使用正确的传感器数据格式（参考coordinator服务期望的格式）
  String message = "{\"type\":\"sensor_update\",\"device_id\":\"" + WiFi.macAddress() + 
                  "\",\"location\":\"living_room\",\"timestamp\":" + String(millis()) + 
                  ",\"sensors\":{\"temperature\":23.5,\"humidity\":55.2,\"co2\":420,\"voc\":15,\"aqi\":1,\"status\":true,\"last_update\":\"real-time\"}," +
                  "\"device_status\":{\"wifi_rssi\":" + String(WiFi.RSSI()) + ",\"free_heap\":" + String(ESP.getFreeHeap()) + ",\"uptime\":" + String(millis()/1000) + ",\"ip\":\"" + WiFi.localIP().toString() + "\"}}";
  
  Serial.printf("📤 Sending sensor data (%d bytes)\n", message.length());
  Serial.printf("📝 Data: %s\n", message.c_str());
  
  bool result = webSocket.sendTXT(message);
  Serial.printf("📤 Sensor send result: %s\n", result ? "SUCCESS" : "FAILED");
}