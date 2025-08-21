/*
 * 完整的ESP32-S3音频系统测试
 * 使用GPIO6作为CODEC_3V3使能控制
 */

#include <Wire.h>
#include <driver/i2s.h>

// 关键引脚定义
#define CODEC_ENABLE_PIN  6   // PREP_VCC_CTL = GPIO6 (使能CODEC_3V3)

// I2C配置
#define I2C_SCL_PIN       1   // GPIO1 = SCL
#define I2C_SDA_PIN       2   // GPIO2 = SDA
#define ES8311_I2C_ADDR   0x18
#define BMI270_I2C_ADDR   0x68

// I2S配置
#define I2S_BCK_PIN       41
#define I2S_WS_PIN        42
#define I2S_DATA_OUT_PIN  16
#define I2S_DATA_IN_PIN   15

// 控制引脚
#define PA_CTRL_PIN       10  // 功放控制
#define LED_PIN           11  // 状态LED
#define KEY_PIN           0   // 用户按键

// 音频参数
#define SAMPLE_RATE       16000

// 测试结果
struct TestResults {
  bool codec_power_ok = false;
  bool es8311_ok = false;
  bool bmi270_ok = false;
  bool i2s_ok = false;
  bool audio_test_ok = false;
} results;

void setup() {
  Serial.begin(115200);
  delay(2000);
  
  Serial.println("\n" + String('=', 60));
  Serial.println("ESP32-S3 完整音频系统测试");
  Serial.println("CODEC使能引脚: GPIO6");
  Serial.println(String('=', 60));
  
  // 初始化基础GPIO
  initBasicGPIO();
  
  // 测试CODEC电源控制
  testCodecPowerControl();
  
  // 测试所有硬件模块
  testAllHardware();
  
  // 显示测试结果
  showTestResults();
  
  // 如果基础硬件正常，准备音频功能
  if (results.codec_power_ok && results.es8311_ok && results.i2s_ok) {
    Serial.println("\n🎉 系统就绪！按按键测试音频功能");
  } else {
    Serial.println("\n⚠️ 部分硬件有问题，请检查连接");
  }
}

void loop() {
  // 按键处理
  handleKeyPress();
  
  // 状态LED
  updateStatusLED();
  
  // 定期状态检查
  static unsigned long lastCheck = 0;
  if (millis() - lastCheck > 10000) {  // 每10秒
    Serial.println("\n--- 系统状态检查 ---");
    quickStatusCheck();
    lastCheck = millis();
  }
  
  delay(50);
}

void initBasicGPIO() {
  Serial.println("\n🔧 初始化基础GPIO...");
  
  // 控制引脚
  pinMode(CODEC_ENABLE_PIN, OUTPUT);
  pinMode(PA_CTRL_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  pinMode(KEY_PIN, INPUT_PULLUP);
  
  // 初始状态
  digitalWrite(CODEC_ENABLE_PIN, LOW);  // 先关闭CODEC电源
  digitalWrite(PA_CTRL_PIN, LOW);       // 关闭功放
  digitalWrite(LED_PIN, HIGH);          // 点亮LED表示启动
  
  Serial.println("✅ 基础GPIO初始化完成");
}

void testCodecPowerControl() {
  Serial.println("\n🔋 测试CODEC电源控制...");
  
  // 初始化I2C
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
  delay(100);
  
  Serial.println("1. CODEC电源关闭状态测试:");
  digitalWrite(CODEC_ENABLE_PIN, LOW);
  delay(200);
  scanI2CDevices();
  
  Serial.println("\n2. CODEC电源开启状态测试:");
  digitalWrite(CODEC_ENABLE_PIN, HIGH);
  delay(200);
  scanI2CDevices();
  
  // 再次测试开关控制
  Serial.println("\n3. 验证电源开关控制:");
  for (int i = 0; i < 3; i++) {
    digitalWrite(CODEC_ENABLE_PIN, LOW);
    delay(100);
    bool es8311_off = !checkDevice(ES8311_I2C_ADDR);
    
    digitalWrite(CODEC_ENABLE_PIN, HIGH);
    delay(100);
    bool es8311_on = checkDevice(ES8311_I2C_ADDR);
    
    Serial.printf("   测试%d: 关闭=%s, 开启=%s\n", i+1, 
                  es8311_off ? "✓" : "✗", es8311_on ? "✓" : "✗");
    
    if (es8311_off && es8311_on) {
      results.codec_power_ok = true;
    }
  }
  
  // 保持使能状态
  digitalWrite(CODEC_ENABLE_PIN, HIGH);
  delay(100);
  
  if (results.codec_power_ok) {
    Serial.println("✅ CODEC电源控制正常");
  } else {
    Serial.println("❌ CODEC电源控制异常");
  }
}

void testAllHardware() {
  Serial.println("\n🔍 测试所有硬件模块...");
  
  // 确保CODEC电源开启
  digitalWrite(CODEC_ENABLE_PIN, HIGH);
  delay(100);
  
  // 测试BMI270
  testBMI270();
  
  // 测试ES8311
  testES8311();
  
  // 测试I2S
  testI2S();
}

void testBMI270() {
  Serial.println("\n🏃 测试BMI270 IMU...");
  
  if (checkDevice(BMI270_I2C_ADDR)) {
    Serial.println("✅ BMI270响应正常");
    
    // 读取Chip ID
    Wire.beginTransmission(BMI270_I2C_ADDR);
    Wire.write(0x00);
    Wire.endTransmission(false);
    Wire.requestFrom(BMI270_I2C_ADDR, 1);
    
    if (Wire.available()) {
      uint8_t chipId = Wire.read();
      Serial.printf("   Chip ID: 0x%02X\n", chipId);
      
      if (chipId == 0x24) {
        results.bmi270_ok = true;
        Serial.println("✅ BMI270确认正常");
      } else {
        Serial.printf("⚠️ Chip ID不匹配 (期望:0x24)\n");
      }
    }
  } else {
    Serial.println("❌ BMI270无响应");
  }
}

void testES8311() {
  Serial.println("\n🎵 测试ES8311音频编解码器...");
  
  if (checkDevice(ES8311_I2C_ADDR)) {
    Serial.println("✅ ES8311响应正常");
    
    // 读取一些寄存器
    Serial.println("   读取寄存器:");
    for (uint8_t reg = 0x00; reg <= 0x02; reg++) {
      uint8_t value = readES8311Register(reg);
      Serial.printf("     0x%02X: 0x%02X\n", reg, value);
    }
    
    // 尝试基本配置
    if (configureES8311()) {
      results.es8311_ok = true;
      Serial.println("✅ ES8311配置成功");
    } else {
      Serial.println("⚠️ ES8311配置失败");
    }
  } else {
    Serial.println("❌ ES8311无响应");
  }
}

bool configureES8311() {
  Serial.println("   配置ES8311...");
  
  struct {
    uint8_t reg;
    uint8_t value;
    const char* desc;
  } config[] = {
    {0x45, 0x00, "软复位"},
    {0x01, 0x30, "时钟管理"},
    {0x02, 0x10, "模拟配置"},
    {0x16, 0x24, "ADC配置"},
    {0x17, 0x20, "DAC配置"},
    {0x09, 0x01, "I2S格式"},
    {0x0A, 0x01, "I2S配置"},
  };
  
  for (int i = 0; i < 7; i++) {
    if (!writeES8311Register(config[i].reg, config[i].value)) {
      Serial.printf("     ❌ %s失败\n", config[i].desc);
      return false;
    }
    delay(10);
  }
  
  // 最后使能芯片
  writeES8311Register(0x00, 0x80);
  delay(50);
  
  return true;
}

void testI2S() {
  Serial.println("\n🎧 测试I2S音频接口...");
  
  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX | I2S_MODE_RX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 6,
    .dma_buf_len = 512,
    .use_apll = true,
    .tx_desc_auto_clear = true
  };
  
  i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_BCK_PIN,
    .ws_io_num = I2S_WS_PIN,
    .data_out_num = I2S_DATA_OUT_PIN,
    .data_in_num = I2S_DATA_IN_PIN
  };
  
  esp_err_t err = i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
  if (err == ESP_OK) {
    err = i2s_set_pin(I2S_NUM_0, &pin_config);
    if (err == ESP_OK) {
      results.i2s_ok = true;
      Serial.println("✅ I2S初始化成功");
    } else {
      Serial.printf("❌ I2S引脚配置失败: %s\n", esp_err_to_name(err));
    }
  } else {
    Serial.printf("❌ I2S驱动安装失败: %s\n", esp_err_to_name(err));
  }
}

void showTestResults() {
  Serial.println("\n" + String('=', 60));
  Serial.println("硬件测试结果汇总");
  Serial.println(String('=', 60));
  
  Serial.printf("CODEC电源控制:     %s\n", results.codec_power_ok ? "✅ 正常" : "❌ 失败");
  Serial.printf("ES8311音频编解码器: %s\n", results.es8311_ok ? "✅ 正常" : "❌ 失败");
  Serial.printf("BMI270 IMU传感器:  %s\n", results.bmi270_ok ? "✅ 正常" : "❌ 失败");
  Serial.printf("I2S音频接口:       %s\n", results.i2s_ok ? "✅ 正常" : "❌ 失败");
  
  int passed = 0;
  if (results.codec_power_ok) passed++;
  if (results.es8311_ok) passed++;
  if (results.bmi270_ok) passed++;
  if (results.i2s_ok) passed++;
  
  Serial.printf("\n总体结果: %d/4 项测试通过\n", passed);
  
  if (passed >= 3) {
    Serial.println("🎉 系统基本正常，可以进行音频测试！");
  } else {
    Serial.println("⚠️ 多个硬件模块有问题，需要检查");
  }
  
  Serial.println(String('=', 60));
}

void handleKeyPress() {
  static bool lastKeyState = HIGH;
  bool currentKeyState = digitalRead(KEY_PIN);
  
  if (lastKeyState == HIGH && currentKeyState == LOW) {
    Serial.println("\n🔵 按键按下 - 开始音频测试");
    
    if (results.es8311_ok && results.i2s_ok) {
      performAudioTest();
    } else {
      Serial.println("⚠️ 音频硬件未就绪");
    }
  }
  
  lastKeyState = currentKeyState;
}

void performAudioTest() {
  Serial.println("🎤 开始音频测试...");
  
  // 使能功放
  digitalWrite(PA_CTRL_PIN, HIGH);
  digitalWrite(LED_PIN, HIGH);
  delay(100);
  
  const int bufferSize = 256;
  int16_t buffer[bufferSize];
  int maxAmplitude = 0;
  int sampleCount = 0;
  
  Serial.println("录音并播放3秒...");
  unsigned long startTime = millis();
  
  while (millis() - startTime < 3000) {
    size_t bytesRead = 0;
    
    // 录音
    esp_err_t result = i2s_read(I2S_NUM_0, buffer, sizeof(buffer), &bytesRead, pdMS_TO_TICKS(100));
    
    if (result == ESP_OK && bytesRead > 0) {
      int samples = bytesRead / sizeof(int16_t);
      sampleCount += samples;
      
      // 分析音频信号
      for (int i = 0; i < samples; i++) {
        int amplitude = abs(buffer[i]);
        if (amplitude > maxAmplitude) {
          maxAmplitude = amplitude;
        }
      }
      
      // 立即播放（环回测试）
      size_t bytesWritten = 0;
      i2s_write(I2S_NUM_0, buffer, bytesRead, &bytesWritten, pdMS_TO_TICKS(10));
    }
  }
  
  // 关闭功放
  digitalWrite(PA_CTRL_PIN, LOW);
  digitalWrite(LED_PIN, LOW);
  
  // 显示结果
  Serial.printf("🎵 音频测试完成:\n");
  Serial.printf("   总采样数: %d\n", sampleCount);
  Serial.printf("   最大振幅: %d (满量程: 32767)\n", maxAmplitude);
  Serial.printf("   信号强度: %.1f%%\n", (maxAmplitude / 32767.0) * 100);
  
  if (maxAmplitude > 1000) {
    Serial.println("✅ 检测到有效音频信号！");
    results.audio_test_ok = true;
  } else {
    Serial.println("⚠️ 音频信号较弱，请检查麦克风连接");
  }
}

void updateStatusLED() {
  static unsigned long lastBlink = 0;
  static bool ledState = false;
  
  // 根据系统状态调整LED闪烁频率
  int blinkInterval = 1000;  // 默认1秒
  
  if (results.codec_power_ok && results.es8311_ok && results.i2s_ok) {
    blinkInterval = 2000;  // 系统正常时慢闪
  } else {
    blinkInterval = 500;   // 有问题时快闪
  }
  
  if (millis() - lastBlink > blinkInterval) {
    ledState = !ledState;
    digitalWrite(LED_PIN, ledState);
    lastBlink = millis();
  }
}

void quickStatusCheck() {
  Serial.printf("CODEC电源: %s, ", isCodecPowerEnabled() ? "开" : "关");
  Serial.printf("ES8311: %s, ", checkDevice(ES8311_I2C_ADDR) ? "在线" : "离线");
  Serial.printf("BMI270: %s\n", checkDevice(BMI270_I2C_ADDR) ? "在线" : "离线");
}

// ========== 辅助函数 ==========
bool isCodecPowerEnabled() {
  return digitalRead(CODEC_ENABLE_PIN) == HIGH;
}

bool checkDevice(uint8_t address) {
  Wire.beginTransmission(address);
  return Wire.endTransmission() == 0;
}

bool writeES8311Register(uint8_t reg, uint8_t value) {
  Wire.beginTransmission(ES8311_I2C_ADDR);
  Wire.write(reg);
  Wire.write(value);
  return Wire.endTransmission() == 0;
}

uint8_t readES8311Register(uint8_t reg) {
  Wire.beginTransmission(ES8311_I2C_ADDR);
  Wire.write(reg);
  Wire.endTransmission(false);
  Wire.requestFrom(ES8311_I2C_ADDR, 1);
  return Wire.available() ? Wire.read() : 0xFF;
}

void scanI2CDevices() {
  int deviceCount = 0;
  
  for (byte address = 8; address < 120; address++) {
    Wire.beginTransmission(address);
    byte result = Wire.endTransmission();
    
    if (result == 0) {
      Serial.printf("   设备: 0x%02X", address);
      
      if (address == 0x18) Serial.print(" (ES8311)");
      else if (address == 0x68) Serial.print(" (BMI270)");
      
      Serial.println();
      deviceCount++;
    }
  }
  
  Serial.printf("   总计: %d 个设备\n", deviceCount);
}