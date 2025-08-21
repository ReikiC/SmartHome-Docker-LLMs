#include <ESP8266WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>

// WiFi配置
const char* ssid = "CE-Hub-Student";
const char* password = "casa-ce-gagarin-public-service";

// 服务器配置
const char* server_host = "10.129.113.188";
const int server_port = 8080;
const char* server_path = "/ws";

// WebSocket客户端
WebSocketsClient webSocket;

// 状态管理
bool wifiConnected = false;
bool wsConnected = false;
bool messageReceived = false;
unsigned long lastConnectionAttempt = 0;
unsigned long lastPingTime = 0;
int connectionAttempts = 0;

void setup() {
  Serial.begin(115200);
  delay(2000);
  
  Serial.println("\n==================================================");
  Serial.println("🔧 ESP8266 Basic Connection Test");
  Serial.println("==================================================");
  
  // 连接WiFi
  connectToWiFi();
  
  if (wifiConnected) {
    delay(2000); // 给网络连接一些稳定时间
    initWebSocket();
  }
}

void loop() {
  // 检查WiFi状态
  if (WiFi.status() != WL_CONNECTED) {
    handleWiFiDisconnection();
    return;
  }
  
  // 处理WebSocket
  webSocket.loop();
  
  // WebSocket重连逻辑
  if (!wsConnected && (millis() - lastConnectionAttempt > 10000)) {
    if (connectionAttempts < 5) {
      reconnectWebSocket();
    } else {
      Serial.println("💀 Max attempts reached, restarting ESP8266...");
      ESP.restart();
    }
  }
  
  // 定期发送ping（每60秒）
  if (wsConnected && (millis() - lastPingTime > 60000)) {
    sendPing();
    lastPingTime = millis();
  }
  
  delay(1000);
}

void connectToWiFi() {
  Serial.printf("📶 Connecting to WiFi: %s\n", ssid);
  
  // 断开之前的连接
  WiFi.disconnect();
  delay(1000);
  
  // 设置WiFi模式
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(1000);
    Serial.print(".");
    attempts++;
    
    if (attempts % 10 == 0) {
      Serial.printf(" (%d/30)\n", attempts);
    }
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    Serial.println("\n✅ WiFi Connected!");
    printNetworkInfo();
    
    // 测试基本连通性
    testBasicConnectivity();
  } else {
    wifiConnected = false;
    Serial.println("\n❌ WiFi connection failed!");
    
    // 扫描网络
    scanNetworks();
  }
}

void printNetworkInfo() {
  Serial.printf("📍 ESP8266 IP: %s\n", WiFi.localIP().toString().c_str());
  Serial.printf("🌐 Gateway: %s\n", WiFi.gatewayIP().toString().c_str());
  Serial.printf("🔍 DNS: %s\n", WiFi.dnsIP().toString().c_str());
  Serial.printf("📡 RSSI: %d dBm\n", WiFi.RSSI());
  Serial.printf("🏷️ MAC: %s\n", WiFi.macAddress().c_str());
  Serial.printf("📊 Channel: %d\n", WiFi.channel());
}

void scanNetworks() {
  Serial.println("📡 Scanning for WiFi networks...");
  int n = WiFi.scanNetworks();
  
  Serial.printf("Found %d networks:\n", n);
  for (int i = 0; i < n; i++) {
    bool isTargetNetwork = (WiFi.SSID(i) == ssid);
    Serial.printf("  %s %s (%d dBm) %s\n", 
      isTargetNetwork ? "🎯" : "  ",
      WiFi.SSID(i).c_str(), 
      WiFi.RSSI(i),
      WiFi.encryptionType(i) == ENC_TYPE_NONE ? "Open" : "Encrypted"
    );
  }
}

void testBasicConnectivity() {
  Serial.printf("🔗 Testing connectivity to %s:%d\n", server_host, server_port);
  
  WiFiClient client;
  
  if (client.connect(server_host, server_port)) {
    Serial.println("✅ TCP connection successful!");
    
    // 发送HTTP GET请求
    client.printf("GET / HTTP/1.1\r\nHost: %s:%d\r\nConnection: close\r\n\r\n", 
                  server_host, server_port);
    
    // 等待响应
    unsigned long timeout = millis() + 5000;
    String response = "";
    
    while (millis() < timeout) {
      if (client.available()) {
        response += client.readString();
        break;
      }
      delay(10);
    }
    
    if (response.length() > 0) {
      Serial.printf("📥 HTTP Response received (%d bytes)\n", response.length());
      
      if (response.indexOf("200 OK") >= 0) {
        Serial.println("✅ HTTP server responding correctly!");
      } else {
        Serial.println("⚠️ Unexpected HTTP response");
      }
    }
    
    client.stop();
  } else {
    Serial.println("❌ TCP connection failed!");
    Serial.println("Please check:");
    Serial.println("  - Docker services are running");
    Serial.println("  - IP address is correct");
    Serial.println("  - No firewall blocking");
  }
}

void initWebSocket() {
  Serial.printf("🔌 Initializing WebSocket: ws://%s:%d%s\n", 
                server_host, server_port, server_path);
  
  // 配置WebSocket
  webSocket.begin(server_host, server_port, server_path);
  webSocket.onEvent(webSocketEvent);
  
  // 重要：配置WebSocket参数
  webSocket.setReconnectInterval(5000);
  webSocket.enableHeartbeat(15000, 3000, 2);
  
  // 设置更长的超时时间
  webSocket.setExtraHeaders("Origin: http://esp8266");
  
  wsConnected = false;
  messageReceived = false;
  lastConnectionAttempt = millis();
  
  Serial.println("⚙️ WebSocket configured, attempting connection...");
}

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  String timestamp = String(millis() / 1000) + "s";
  
  switch(type) {
    case WStype_DISCONNECTED:
      wsConnected = false;
      messageReceived = false;
      Serial.printf("[%s] 🔴 WebSocket Disconnected\n", timestamp.c_str());
      break;
      
    case WStype_CONNECTED:
      wsConnected = true;
      messageReceived = false;
      connectionAttempts = 0;
      Serial.printf("[%s] 🟢 WebSocket Connected to: %s\n", timestamp.c_str(), payload);
      
      // 连接成功后等待一下再发送消息
      delay(2000);
      sendInitialMessage();
      break;
      
    case WStype_TEXT:
      messageReceived = true;
      Serial.printf("[%s] 📨 Message received (%d bytes): %s\n", 
                    timestamp.c_str(), length, payload);
      handleMessage((char*)payload);
      break;
      
    case WStype_BIN:
      Serial.printf("[%s] 📦 Binary data received (%d bytes)\n", 
                    timestamp.c_str(), length);
      break;
      
    case WStype_ERROR:
      wsConnected = false;
      Serial.printf("[%s] ❌ WebSocket Error: %s\n", timestamp.c_str(), payload);
      break;
      
    case WStype_FRAGMENT_TEXT_START:
      Serial.printf("[%s] 📝 Fragment text start\n", timestamp.c_str());
      break;
      
    case WStype_FRAGMENT_BIN_START:
      Serial.printf("[%s] 📝 Fragment binary start\n", timestamp.c_str());
      break;
      
    case WStype_FRAGMENT:
      Serial.printf("[%s] 📝 Fragment\n", timestamp.c_str());
      break;
      
    case WStype_FRAGMENT_FIN:
      Serial.printf("[%s] 📝 Fragment finished\n", timestamp.c_str());
      break;
      
    case WStype_PING:
      Serial.printf("[%s] 🏓 Ping received\n", timestamp.c_str());
      break;
      
    case WStype_PONG:
      Serial.printf("[%s] 🏓 Pong received\n", timestamp.c_str());
      break;
      
    default:
      Serial.printf("[%s] 🔶 Unknown event type: %d\n", timestamp.c_str(), type);
      break;
  }
}

void sendInitialMessage() {
  if (!wsConnected) {
    Serial.println("⚠️ Cannot send message - WebSocket not connected");
    return;
  }
  
  Serial.println("📤 Sending initial message...");
  
  // 创建简单的JSON消息
  DynamicJsonDocument doc(512);
  doc["type"] = "device_registration";
  doc["device_info"]["type"] = "esp8266_sensor";
  doc["device_info"]["id"] = WiFi.macAddress();
  doc["device_info"]["ip"] = WiFi.localIP().toString();
  doc["device_info"]["location"] = "test_location";
  doc["timestamp"] = millis();
  
  String message;
  serializeJson(doc, message);
  
  Serial.printf("📝 Message content: %s\n", message.c_str());
  Serial.printf("📏 Message length: %d bytes\n", message.length());
  
  bool sent = webSocket.sendTXT(message);
  Serial.printf("📤 Send result: %s\n", sent ? "SUCCESS" : "FAILED");
}

void sendPing() {
  if (!wsConnected) return;
  
  DynamicJsonDocument doc(256);
  doc["type"] = "ping";
  doc["device_id"] = WiFi.macAddress();
  doc["timestamp"] = millis();
  doc["uptime"] = millis() / 1000;
  
  String message;
  serializeJson(doc, message);
  
  Serial.printf("🏓 Sending ping: %s\n", message.c_str());
  webSocket.sendTXT(message);
}

void handleMessage(const char* message) {
  Serial.printf("🔍 Processing message: %s\n", message);
  
  DynamicJsonDocument doc(1024);
  DeserializationError error = deserializeJson(doc, message);
  
  if (error) {
    Serial.printf("❌ JSON parse error: %s\n", error.c_str());
    return;
  }
  
  String type = doc["type"].as<String>();
  Serial.printf("📋 Message type: %s\n", type.c_str());
  
  if (type == "pong") {
    Serial.println("🏓 Pong response received - connection is alive!");
  } else if (type == "registration_result") {
    String status = doc["status"].as<String>();
    Serial.printf("📝 Registration result: %s\n", status.c_str());
    
    if (status == "registered") {
      Serial.println("✅ Successfully registered with server!");
    }
  } else {
    Serial.printf("ℹ️ Unhandled message type: %s\n", type.c_str());
  }
}

void reconnectWebSocket() {
  connectionAttempts++;
  Serial.printf("🔄 WebSocket reconnection attempt %d/5\n", connectionAttempts);
  
  // 断开现有连接
  webSocket.disconnect();
  delay(2000);
  
  // 重新初始化
  initWebSocket();
  lastConnectionAttempt = millis();
}

void handleWiFiDisconnection() {
  wifiConnected = false;
  wsConnected = false;
  
  Serial.println("📶 WiFi disconnected! Attempting reconnection...");
  connectToWiFi();
  
  if (wifiConnected) {
    delay(2000);
    initWebSocket();
  }
}

// 调试函数
void printSystemStatus() {
  Serial.println("📊 System Status:");
  Serial.printf("   WiFi: %s\n", wifiConnected ? "✅ Connected" : "❌ Disconnected");
  Serial.printf("   WebSocket: %s\n", wsConnected ? "✅ Connected" : "❌ Disconnected");
  Serial.printf("   Messages: %s\n", messageReceived ? "✅ Received" : "❌ None");
  Serial.printf("   Free Heap: %d bytes\n", ESP.getFreeHeap());
  Serial.printf("   Uptime: %lu seconds\n", millis() / 1000);
}