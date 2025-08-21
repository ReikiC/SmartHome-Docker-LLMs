#include <ESP8266WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include "sensor.h"
#include "network.h"

// 传感器数据读取频率控制
#define SENSOR_READ_INTERVAL 15000  // 15秒读取一次传感器
unsigned long lastSensorReadTime = 0;

#define SENSOR_INTERVAL 15000 // 15秒发送一次
unsigned long lastSensorTime = 0;

void setup() {
  Serial.begin(115200);
  delay(200);
  
  Serial.println("============================================================");
  Serial.printf("🌡️ ESP8266 IoT Sensor Node - Room: %s Only\n", TARGET_ROOM);
  Serial.println("============================================================");

  // 初始化I2C和传感器
  Wire.begin();
  
  Serial.println("\n=== ESP8266 传感器初始化 ===");
  
  // 扫描I2C设备
  scanI2CDevices();
  
  // 初始化传感器
  initSensors();
  
  // 首次读取传感器数据
  Serial.println("📊 首次读取传感器数据...");
  bool initialRead = readAllSensors();
  
  if (initialRead) {
    Serial.println("✅ 传感器初始化成功，将使用真实传感器数据");
    printAllSensorData();
  } else {
    Serial.println("⚠️ 传感器初始化失败，将使用模拟数据作为备用");
  }
  
  Serial.println("\n=== 网络连接 ===");
  
  // 连接WiFi
  connectWiFi();
  
  if (wifiConnected) {
    Serial.println("⏳ 等待3秒后初始化WebSocket连接...");
    delay(3000);
    initWebSocket();
  } else {
    Serial.println("❌ WiFi连接失败，无法上传数据");
  }
  
  Serial.println("\n=== 初始化完成 ===");
  Serial.printf("📍 目标房间: %s\n", TARGET_ROOM);
  Serial.printf("🌡️ 传感器状态: %s\n", g_sensor_data_valid ? "真实数据可用" : "仅模拟数据");
  Serial.printf("📶 网络状态: %s\n", wifiConnected ? "已连接" : "未连接");
  Serial.println("============================================================\n");
}

void loop() {
  // 检查WiFi连接状态
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("❌ WiFi lost, reconnecting...");
    connectWiFi();
    return;
  }
  
  // 处理WebSocket通信
  webSocket.loop();

  // 定期读取传感器数据（每5秒一次）
  if (millis() - lastSensorReadTime >= SENSOR_READ_INTERVAL) {
    Serial.println("\n📊 ===== 定期传感器读取 =====");
    
    bool readSuccess = readAllSensors();
    
    if (readSuccess) {
      Serial.println("✅ 传感器读取成功");
      printAllSensorData();
    } else {
      Serial.println("⚠️ 传感器读取失败，保持上次数据");
    }
    
    lastSensorReadTime = millis();
    Serial.println("================================\n");
  }

  // 定期发送传感器数据到服务器（每30秒一次）
  if (wsConnected && (millis() - lastSensorTime >= SENSOR_INTERVAL)) {
    Serial.println("\n📤 ===== 数据上传周期 =====");
    
    // 发送传感器数据
    sendSensorData();
    lastSensorTime = millis();
    
    Serial.println("============================\n");
  }

  // 每10秒发送一次ping来维持连接
  static unsigned long lastPingTime = 0;
  if (wsConnected && (millis() - lastPingTime >= 10000)) {
    sendPing();
    lastPingTime = millis();
  }

  delay(100);
}