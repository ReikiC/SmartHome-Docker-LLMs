// 传感器启用配置
#define ENABLE_VEML7700 false  // I2C光照传感器
#define ENABLE_GL5539 true     // 模拟光敏电阻传感器 (与VEML7700二选一)
#define ENABLE_ENS160 true     // 空气质量传感器
#define ENABLE_AHT21 true      // 温湿度传感器

// 光照传感器二选一检查
#if ENABLE_VEML7700 && ENABLE_GL5539
#error "只能启用一个光照传感器：VEML7700或GL5539，请设置其中一个为false"
#endif

// 传感器I2C地址
#define VEML7700_ADDR 0x10
#define ENS160_ADDR 0x53
#define AHT21_ADDR 0x38

// GL5539光敏电阻配置
#define GL5539_ANALOG_PIN A0    // ESP8266的模拟输入引脚
#define GL5539_VCC 3.3          // 供电电压
#define GL5539_R_PULLUP 10000   // 上拉电阻值 (10kΩ)
#define GL5539_ADC_MAX 1024     // ESP8266 ADC最大值

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

// 全局传感器数据变量
float g_temperature = 23.5;    // 温度 (°C)
float g_humidity = 55.0;       // 湿度 (%)
int g_co2 = 420;              // CO2 (ppm)
int g_voc = 15;               // VOC (ppb)
int g_light_level = 300;      // 光照强度 (lux)
bool g_motion = false;        // 运动检测
bool g_sensor_data_valid = false;  // 数据有效性标志

// 数据更新时间戳
unsigned long g_last_sensor_update = 0;

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
    g_sensor_data_valid = false;
  } else {
    Serial.print("发现 ");
    Serial.print(deviceCount);
    Serial.println(" 个I2C设备");
  }
  Serial.println();
}


#if ENABLE_AHT21
bool readAHT21() {
  // 发送测量命令
  Wire.beginTransmission(AHT21_ADDR);
  Wire.write(AHT21_MEASURE_CMD);
  Wire.write(0x33);
  Wire.write(0x00);
  byte error = Wire.endTransmission();
  
  if (error != 0) {
    Serial.println("❌ AHT21 发送命令失败");
    return false;
  }
  
  delay(80); // 等待测量完成
  
  // 读取数据
  Wire.requestFrom(AHT21_ADDR, 6);
  if (Wire.available() >= 6) {
    uint8_t data[6];
    for (int i = 0; i < 6; i++) {
      data[i] = Wire.read();
    }
    
    // 检查状态位
    if (data[0] & 0x80) {
      Serial.println("⚠️ AHT21 设备忙碌，稍后重试");
      return false;
    }
    
    // 计算湿度
    uint32_t humidity_raw = ((uint32_t)data[1] << 12) | ((uint32_t)data[2] << 4) | (data[3] >> 4);
    float humidity = (humidity_raw * 100.0) / 1048576.0;
    
    // 计算温度
    uint32_t temperature_raw = (((uint32_t)data[3] & 0x0F) << 16) | ((uint32_t)data[4] << 8) | data[5];
    float temperature = (temperature_raw * 200.0) / 1048576.0 - 50.0;
    
    // 数据有效性检查
    if (temperature > -40 && temperature < 85 && humidity >= 0 && humidity <= 100) {
      // 更新全局变量
      g_temperature = temperature;
      g_humidity = humidity;
      
      Serial.print("✅ AHT21 - 温度: ");
      Serial.print(temperature, 1);
      Serial.print("°C, 湿度: ");
      Serial.print(humidity, 1);
      Serial.println("%");
      
      return true;
    } else {
      Serial.println("❌ AHT21 数据超出正常范围");
      return false;
    }
  } else {
    Serial.println("❌ AHT21 读取数据失败");
    return false;
  }
}
#endif

#if ENABLE_ENS160
bool readENS160() {
  // 读取数据状态
  Wire.beginTransmission(ENS160_ADDR);
  Wire.write(ENS160_DATA_STATUS);
  byte error = Wire.endTransmission();
  
  if (error != 0) {
    Serial.println("❌ ENS160 通信失败");
    return false;
  }
  
  Wire.requestFrom(ENS160_ADDR, 1);
  
  if (Wire.available()) {
    uint8_t status = Wire.read();
    if (status & 0x02) { // 数据准备就绪
      
      // 读取AQI
      Wire.beginTransmission(ENS160_ADDR);
      Wire.write(ENS160_DATA_AQI);
      Wire.endTransmission();
      Wire.requestFrom(ENS160_ADDR, 1);
      uint8_t aqi = Wire.available() ? Wire.read() : 0;
      
      // 读取TVOC
      Wire.beginTransmission(ENS160_ADDR);
      Wire.write(ENS160_DATA_TVOC);
      Wire.endTransmission();
      Wire.requestFrom(ENS160_ADDR, 2);
      uint16_t tvoc = 0;
      if (Wire.available() >= 2) {
        tvoc = Wire.read() | (Wire.read() << 8);
      }
      
      // 读取CO2
      Wire.beginTransmission(ENS160_ADDR);
      Wire.write(ENS160_DATA_ECO2);
      Wire.endTransmission();
      Wire.requestFrom(ENS160_ADDR, 2);
      uint16_t co2 = 400; // 默认值
      if (Wire.available() >= 2) {
        co2 = Wire.read() | (Wire.read() << 8);
      }
      
      // 数据有效性检查
      if (co2 > 300 && co2 < 5000 && tvoc < 10000) {
        // 更新全局变量
        g_co2 = co2;
        g_voc = tvoc;
        
        Serial.print("✅ ENS160 - AQI: ");
        Serial.print(aqi);
        Serial.print(", TVOC: ");
        Serial.print(tvoc);
        Serial.print(" ppb, CO2: ");
        Serial.print(co2);
        Serial.println(" ppm");
        
        return true;
      } else {
        Serial.println("❌ ENS160 数据超出正常范围");
        return false;
      }
    } else {
      Serial.println("⚠️ ENS160 数据未准备就绪");
      return false;
    }
  } else {
    Serial.println("❌ ENS160 读取状态失败");
    return false;
  }
}
#endif

#if ENABLE_GL5539
bool readGL5539() {
  // 读取ADC值
  int adcValue = analogRead(GL5539_ANALOG_PIN);
  
  // 计算光敏电阻的电阻值
  // 电路：VCC -- R_pullup -- ADC_pin -- LDR -- GND
  // ADC电压 = VCC * ADC_value / ADC_max
  // LDR电阻 = R_pullup * ADC_value / (ADC_max - ADC_value)
  
  if (adcValue >= GL5539_ADC_MAX - 1) {
    // 防止除零错误，ADC值接近最大值时LDR电阻非常大（很暗）
    Serial.println("❌ GL5539 读取失败：环境过暗或传感器故障");
    return false;
  }
  
  // 计算光敏电阻值
  float ldrResistance = (float)GL5539_R_PULLUP * adcValue / (GL5539_ADC_MAX - adcValue);
  
  // 将电阻值转换为光照强度 (lux)
  // GL5539典型特性：10lux时约10kΩ，100lux时约1kΩ
  // 使用经验公式：lux = A / (resistance^B)，其中A和B是校准常数
  float lux;
  
  if (ldrResistance > 50000) {
    // 电阻很大，环境很暗
    lux = 1.0;
  } else if (ldrResistance < 100) {
    // 电阻很小，环境很亮
    lux = 2000.0;
  } else {
    // 使用校准公式计算
    // 基于GL5539典型特性曲线的近似公式
    lux = 12500000.0 / pow(ldrResistance, 1.4);
  }
  
  // 数据有效性检查
  if (lux >= 0 && lux <= 10000 && adcValue >= 10) {
    // 更新全局变量
    g_light_level = (int)lux;
    
    Serial.print("✅ GL5539 - ADC: ");
    Serial.print(adcValue);
    Serial.print(", 电阻: ");
    Serial.print(ldrResistance, 0);
    Serial.print(" Ω, 光照强度: ");
    Serial.print(lux, 1);
    Serial.println(" lux");
    
    return true;
  } else {
    Serial.printf("❌ GL5539 数据异常 - ADC: %d, 电阻: %.0fΩ, Lux: %.1f\n", 
                  adcValue, ldrResistance, lux);
    return false;
  }
}
#endif

#if ENABLE_VEML7700
bool readVEML7700() {
  // 读取环境光数据
  Wire.beginTransmission(VEML7700_ADDR);
  Wire.write(0x04); // ALS寄存器
  byte error = Wire.endTransmission();
  
  if (error != 0) {
    Serial.println("❌ VEML7700 通信失败");
    return false;
  }
  
  Wire.requestFrom(VEML7700_ADDR, 2);
  if (Wire.available() >= 2) {
    uint16_t raw_data = Wire.read() | (Wire.read() << 8);
    float lux = raw_data * 0.0576; // 转换为lux
    
    // 数据有效性检查
    if (lux >= 0 && lux < 120000) {
      // 更新全局变量
      g_light_level = (int)lux;
      
      Serial.print("✅ VEML7700 - 光照强度: ");
      Serial.print(lux, 2);
      Serial.println(" lux");
      
      return true;
    } else {
      Serial.println("❌ VEML7700 数据超出正常范围");
      return false;
    }
  } else {
    Serial.println("❌ VEML7700 读取数据失败");
    return false;
  }
}
#endif

void initSensors() {
  #if ENABLE_AHT21
  // 初始化AHT21
  Wire.beginTransmission(AHT21_ADDR);
  Wire.write(AHT21_INIT_CMD);
  Wire.write(0x08);
  Wire.write(0x00);
  byte error = Wire.endTransmission();
  if (error == 0) {
    Serial.println("✅ AHT21 初始化完成");
  } else {
    Serial.println("❌ AHT21 初始化失败");
  }
  delay(10);
  #endif
  
  #if ENABLE_ENS160
  // 初始化ENS160
  Wire.beginTransmission(ENS160_ADDR);
  Wire.write(ENS160_OPMODE);
  Wire.write(0x02); // 标准操作模式
  byte error2 = Wire.endTransmission();
  if (error2 == 0) {
    Serial.println("✅ ENS160 初始化完成");
  } else {
    Serial.println("❌ ENS160 初始化失败");
  }
  delay(100);
  #endif
  
  #if ENABLE_GL5539
  // 初始化GL5539光敏电阻 (模拟引脚，无需特殊初始化)
  pinMode(GL5539_ANALOG_PIN, INPUT);
  Serial.println("✅ GL5539 光敏电阻初始化完成");
  Serial.printf("   - 使用引脚: A%d\n", GL5539_ANALOG_PIN);
  Serial.printf("   - 上拉电阻: %d Ω\n", GL5539_R_PULLUP);
  #endif
  
  #if ENABLE_VEML7700
  Serial.println("✅ VEML7700 I2C光照传感器已启用");
  #endif
}

bool readAllSensors() {
  bool anyDataRead = false;
  
  Serial.println("📊 读取所有传感器数据...");
  
  #if ENABLE_AHT21
  if (readAHT21()) {
    anyDataRead = true;
  }
  #endif
  
  #if ENABLE_ENS160
  if (readENS160()) {
    anyDataRead = true;
  }
  #endif
  
  #if ENABLE_VEML7700
  if (readVEML7700()) {
    anyDataRead = true;
  }
  #endif
  
  #if ENABLE_GL5539
  if (readGL5539()) {
    anyDataRead = true;
  }
  #endif
  
  // 模拟运动检测（可以替换为真实的PIR传感器）
  g_motion = (random(0, 100) < 5); // 5% 概率检测到运动
  
  if (anyDataRead) {
    g_sensor_data_valid = true;
    g_last_sensor_update = millis();
    
    Serial.println("✅ 传感器数据更新完成");
    Serial.printf("🌡️ 当前数据汇总 - 温度: %.1f°C, 湿度: %.1f%%, CO2: %dppm, VOC: %dppb, 光照: %dlux, 运动: %s\n", 
                  g_temperature, g_humidity, g_co2, g_voc, g_light_level, g_motion ? "是" : "否");
  } else {
    Serial.println("⚠️ 没有成功读取到任何传感器数据");
  }
  
  return anyDataRead;
}

// 获取传感器数据是否有效
bool isSensorDataValid() {
  return g_sensor_data_valid && (millis() - g_last_sensor_update < 60000); // 1分钟内的数据认为有效
}

// 打印当前所有传感器数据
void printAllSensorData() {
  Serial.println("📊 当前传感器数据状态:");
  Serial.printf("   🌡️ 温度: %.1f°C\n", g_temperature);
  Serial.printf("   💧 湿度: %.1f%%\n", g_humidity);
  Serial.printf("   🌬️ CO2: %d ppm\n", g_co2);
  Serial.printf("   ☁️ VOC: %d ppb\n", g_voc);
  Serial.printf("   ☀️ 光照: %d lux\n", g_light_level);
  Serial.printf("   🚶 运动: %s\n", g_motion ? "检测到" : "无");
  Serial.printf("   ✅ 数据有效: %s\n", isSensorDataValid() ? "是" : "否");
  Serial.printf("   🕐 上次更新: %lu ms前\n", millis() - g_last_sensor_update);
}