#include <Wire.h>
#include <ESP8266WiFi.h>

// 传感器启用配置
#define ENABLE_VEML7700 false  // 光照传感器
#define ENABLE_ENS160 true     // 空气质量传感器
#define ENABLE_AHT21 true      // 温湿度传感器

// 传感器I2C地址
#define VEML7700_ADDR 0x10
#define ENS160_ADDR 0x53
#define AHT21_ADDR 0x38

// ENS160寄存器地址
#define ENS160_PART_ID 0x00
#define ENS160_OPMODE 0x10
#define ENS160_CONFIG 0x11
#define ENS160_COMMAND 0x12
#define ENS160_TEMP_IN 0x13
#define ENS160_RH_IN 0x15
#define ENS160_DATA_STATUS 0x20
#define ENS160_DATA_AQI 0x21
#define ENS160_DATA_TVOC 0x22
#define ENS160_DATA_ECO2 0x24

// AHT21命令
#define AHT21_INIT_CMD 0xBE
#define AHT21_MEASURE_CMD 0xAC
#define AHT21_SOFT_RESET_CMD 0xBA

void setup() {
  Serial.begin(115200);
  Wire.begin();
  
  Serial.println("\n=== ESP8266 传感器测试 ===");
  
  // 扫描I2C设备
  scanI2CDevices();
  
  // 初始化传感器
  initSensors();
  
  Serial.println("初始化完成，开始读取传感器数据...\n");
}

void loop() {
  Serial.println("=== 传感器读数 ===");
  
  #if ENABLE_AHT21
  readAHT21();
  #endif
  
  #if ENABLE_ENS160
  readENS160();
  #endif
  
  #if ENABLE_VEML7700
  readVEML7700();
  #endif
  
  Serial.println();
  delay(5000); // 5秒读取一次
}

void scanI2CDevices() {
  Serial.println("扫描I2C设备...");
  byte error, address;
  int deviceCount = 0;
  
  for(address = 1; address < 127; address++) {
    Wire.beginTransmission(address);
    error = Wire.endTransmission();
    
    if (error == 0) {
      Serial.print("发现I2C设备，地址: 0x");
      if (address < 16) Serial.print("0");
      Serial.println(address, HEX);
      deviceCount++;
    }
  }
  
  if (deviceCount == 0) {
    Serial.println("未发现I2C设备");
  } else {
    Serial.print("发现 ");
    Serial.print(deviceCount);
    Serial.println(" 个I2C设备");
  }
  Serial.println();
}

void initSensors() {
  #if ENABLE_AHT21
  // 初始化AHT21
  Wire.beginTransmission(AHT21_ADDR);
  Wire.write(AHT21_INIT_CMD);
  Wire.write(0x08);
  Wire.write(0x00);
  Wire.endTransmission();
  delay(10);
  Serial.println("AHT21 初始化完成");
  #endif
  
  #if ENABLE_ENS160
  // 初始化ENS160
  Wire.beginTransmission(ENS160_ADDR);
  Wire.write(ENS160_OPMODE);
  Wire.write(0x02); // 标准操作模式
  Wire.endTransmission();
  delay(100);
  Serial.println("ENS160 初始化完成");
  #endif
}

#if ENABLE_AHT21
void readAHT21() {
  // 发送测量命令
  Wire.beginTransmission(AHT21_ADDR);
  Wire.write(AHT21_MEASURE_CMD);
  Wire.write(0x33);
  Wire.write(0x00);
  Wire.endTransmission();
  
  delay(80); // 等待测量完成
  
  // 读取数据
  Wire.requestFrom(AHT21_ADDR, 6);
  if (Wire.available() >= 6) {
    uint8_t data[6];
    for (int i = 0; i < 6; i++) {
      data[i] = Wire.read();
    }
    
    // 计算湿度
    uint32_t humidity_raw = ((uint32_t)data[1] << 12) | ((uint32_t)data[2] << 4) | (data[3] >> 4);
    float humidity = (humidity_raw * 100.0) / 1048576.0;
    
    // 计算温度
    uint32_t temperature_raw = (((uint32_t)data[3] & 0x0F) << 16) | ((uint32_t)data[4] << 8) | data[5];
    float temperature = (temperature_raw * 200.0) / 1048576.0 - 50.0;
    
    Serial.print("AHT21 - 温度: ");
    Serial.print(temperature, 1);
    Serial.print("°C, 湿度: ");
    Serial.print(humidity, 1);
    Serial.println("%");
  } else {
    Serial.println("AHT21 读取失败");
  }
}
#endif

#if ENABLE_ENS160
void readENS160() {
  // 读取数据状态
  Wire.beginTransmission(ENS160_ADDR);
  Wire.write(ENS160_DATA_STATUS);
  Wire.endTransmission();
  Wire.requestFrom(ENS160_ADDR, 1);
  
  if (Wire.available()) {
    uint8_t status = Wire.read();
    if (status & 0x02) { // 数据准备就绪
      
      // 读取AQI
      Wire.beginTransmission(ENS160_ADDR);
      Wire.write(ENS160_DATA_AQI);
      Wire.endTransmission();
      Wire.requestFrom(ENS160_ADDR, 1);
      uint8_t aqi = Wire.read();
      
      // 读取TVOC
      Wire.beginTransmission(ENS160_ADDR);
      Wire.write(ENS160_DATA_TVOC);
      Wire.endTransmission();
      Wire.requestFrom(ENS160_ADDR, 2);
      uint16_t tvoc = Wire.read() | (Wire.read() << 8);
      
      // 读取CO2
      Wire.beginTransmission(ENS160_ADDR);
      Wire.write(ENS160_DATA_ECO2);
      Wire.endTransmission();
      Wire.requestFrom(ENS160_ADDR, 2);
      uint16_t co2 = Wire.read() | (Wire.read() << 8);
      
      Serial.print("ENS160 - AQI: ");
      Serial.print(aqi);
      Serial.print(", TVOC: ");
      Serial.print(tvoc);
      Serial.print(" ppb, CO2: ");
      Serial.print(co2);
      Serial.println(" ppm");
    } else {
      Serial.println("ENS160 数据未准备就绪");
    }
  } else {
    Serial.println("ENS160 读取失败");
  }
}
#endif

#if ENABLE_VEML7700
void readVEML7700() {
  // 读取环境光数据
  Wire.beginTransmission(VEML7700_ADDR);
  Wire.write(0x04); // ALS寄存器
  Wire.endTransmission();
  
  Wire.requestFrom(VEML7700_ADDR, 2);
  if (Wire.available() >= 2) {
    uint16_t raw_data = Wire.read() | (Wire.read() << 8);
    float lux = raw_data * 0.0576; // 转换为lux
    
    Serial.print("VEML7700 - 光照强度: ");
    Serial.print(lux, 2);
    Serial.println(" lux");
  } else {
    Serial.println("VEML7700 读取失败");
  }
}
#endif