/*
 * 修正的ESP32-S3音频测试
 * 考虑到WS2812的VCC_LED由CODEC_3V3控制的情况
 */

#include <Wire.h>
#include <driver/i2s.h>

// 引脚定义
#define CODEC_ENABLE_PIN  6   // PREP_VCC_CTL = GPIO6
#define I2C_SCL_PIN       1
#define I2C_SDA_PIN       2
#define ES8311_I2C_ADDR   0x18
#define BMI270_I2C_ADDR   0x68

#define I2S_BCK_PIN       41
#define I2S_WS_PIN        42
#define I2S_DATA_OUT_PIN  16
#define I2S_DATA_IN_PIN   15

#define PA_CTRL_PIN       10
#define WS2812_PIN        11
#define KEY_PIN           0

// 测试状态
struct TestResults {
  bool codec_power_control_ok = false;
  bool es8311_detected = false;
  bool es8311_configured = false;
  bool bmi270_ok = false;
  bool i2s_ok = false;
  bool audio_test_ok = false;
} results;

void setup() {
  Serial.begin(115200);
  delay(2000);
  
  Serial.println("\n" + String('=', 60));
  Serial.println("ESP32-S3 修正版音频测试");
  Serial.println("考虑WS2812受CODEC_3V3控制的情况");
  Serial.println(String('=', 60));
  
  // 基础GPIO初始化（不包括WS2812）
  initBasicGPIO();
  
  // 测试CODEC电源控制（通过I2C设备检测）
  testCodecPowerControl();
  
  // 确保CODEC电源开启后再测试其他功能
  digitalWrite(CODEC_ENABLE_PIN, HIGH);
  delay(200);
  
  // 初始化WS2812（现在CODEC电源已开启）
  if (results.codec_power_control_ok) {
    initWS2812();
    setWS2812Color(0x000020);  // 蓝色表示开始测试
  }
  
  // 测试所有模块
  testAllModules();
  
  // 显示结果
  showResults();
  
  Serial.println("\n按按键进行音频测试...");
}

void loop() {
  handleKeyPress();
  updateStatusDisplay();
  delay(50);
}

void initBasicGPIO() {
  Serial.println("\n🔧 初始化基础GPIO...");
  
  pinMode(CODEC_ENABLE_PIN, OUTPUT);
  pinMode(PA_CTRL_PIN, OUTPUT);
  pinMode(WS2812_PIN, OUTPUT);
  pinMode(KEY_PIN, INPUT_PULLUP);
  
  // 初始状态
  digitalWrite(CODEC_ENABLE_PIN, LOW);   // 先关闭CODEC电源
  digitalWrite(PA_CTRL_PIN, LOW);        // 关闭功放
  digitalWrite(WS2812_PIN, LOW);         // WS2812也会无电
  
  Serial.println("✅ 基础GPIO初始化完成");
}

void testCodecPowerControl() {
  Serial.println("\n🔋 测试CODEC电源控制...");
  Serial.println("注意：WS2812的VCC_LED由CODEC_3V3控制");
  
  // 初始化I2C
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
  delay(100);
  
  Serial.println("\n1. CODEC电源关闭状态:");
  digitalWrite(CODEC_ENABLE_PIN, LOW);
  delay(200);
  
  bool bmi270_off = checkDevice(BMI270_I2C_ADDR);
  bool es8311_off = checkDevice(ES8311_I2C_ADDR);
  
  Serial.printf("   BMI270: %s (应该在线，不受CODEC_3V3影响)\n", bmi270_off ? "在线" : "离线");
  Serial.printf("   ES8311: %s (应该离线)\n", es8311_off ? "在线" : "离线");
  
  Serial.println("\n2. CODEC电源开启状态:");
  digitalWrite(CODEC_ENABLE_PIN, HIGH);
  delay(200);
  
  bool bmi270_on = checkDevice(BMI270_I2C_ADDR);
  bool es8311_on = checkDevice(ES8311_I2C_ADDR);
  
  Serial.printf("   BMI270: %s (应该仍在线)\n", bmi270_on ? "在线" : "离线");
  Serial.printf("   ES8311: %s (现在应该在线)\n", es8311_on ? "在线" : "离线");
  
  // 判断电源控制是否正常
  if (bmi270_off && bmi270_on && !es8311_off && es8311_on) {
    results.codec_power_control_ok = true;
    Serial.println("✅ CODEC电源控制正常工作");
  } else {
    Serial.println("❌ CODEC电源控制异常");
    Serial.println("   检查项目:");
    Serial.println("   1. GPIO6是否正确连接到PREP_VCC_CTL");
    Serial.println("   2. CODEC_3V3电源电路是否正常");
    Serial.println("   3. ES8311是否正确连接");
  }
  
  Serial.println("\n3. WS2812 LED电源测试:");
  Serial.println("   关闭CODEC电源，WS2812应该无法工作...");
  digitalWrite(CODEC_ENABLE_PIN, LOW);
  delay(100);
  
  // 尝试控制WS2812（应该无效）
  attemptWS2812Control(false);
  
  Serial.println("   开启CODEC电源，WS2812应该可以工作...");
  digitalWrite(CODEC_ENABLE_PIN, HIGH);
  delay(100);
  
  // 尝试控制WS2812（应该有效）
  attemptWS2812Control(true);
}

void attemptWS2812Control(bool expectWorking) {
  // 尝试发送红色信号到WS2812
  uint32_t testColor = 0x100000;  // 红色
  
  uint8_t red = (testColor >> 16) & 0xFF;
  uint8_t green = (testColor >> 8) & 0xFF;
  uint8_t blue = testColor & 0xFF;
  uint32_t grbColor = (green << 16) | (red << 8) | blue;
  
  noInterrupts();
  for (int bit = 23; bit >= 0; bit--) {
    if (grbColor & (1 << bit)) {
      digitalWrite(WS2812_PIN, HIGH);
      delayMicroseconds(1);
      digitalWrite(WS2812_PIN, LOW);
      delayMicroseconds(1);
    } else {
      digitalWrite(WS2812_PIN, HIGH);
      delayMicroseconds(1);
      digitalWrite(WS2812_PIN, LOW);
      delayMicroseconds(2);
    }
  }
  interrupts();
  
  digitalWrite(WS2812_PIN, LOW);
  delayMicroseconds(300);
  
  if (expectWorking) {
    Serial.println("   如果看到红色LED，则VCC_LED电源正常");
  } else {
    Serial.println("   应该看不到LED亮起（VCC_LED断电）");
  }
  
  delay(1000);
}

void testAllModules() {
  Serial.println("\n🔍 测试所有模块（CODEC电源已开启）...");
  
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
    Wire.beginTransmission(BMI270_I2C_ADDR);
    Wire.write(0x00);
    Wire.endTransmission(false);
    Wire.requestFrom(BMI270_I2C_ADDR, 1);
    
    if (Wire.available()) {
      uint8_t chipId = Wire.read();
      Serial.printf("   Chip ID: 0x%02X\n", chipId);
      
      if (chipId == 0x24) {
        results.bmi270_ok = true;
        Serial.println("✅ BMI270正常");
      }
    }
  } else {
    Serial.println("❌ BMI270无响应");
  }
}

void testES8311() {
  Serial.println("\n🎵 测试ES8311音频编解码器...");
  
  if (checkDevice(ES8311_I2C_ADDR)) {
    results.es8311_detected = true;
    Serial.println("✅ ES8311检测成功");
    
    // 读取当前寄存器状态
    Serial.println("   当前寄存器状态:");
    uint8_t regs[] = {0x00, 0x01, 0x02, 0x16, 0x17};
    for (int i = 0; i < 5; i++) {
      uint8_t value = readES8311Register(regs[i]);
      Serial.printf("     0x%02X: 0x%02X\n", regs[i], value);
    }
    
    // 配置ES8311
    if (configureES8311()) {
      results.es8311_configured = true;
      Serial.println("✅ ES8311配置成功");
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
    {0x03, 0x10, "MIC偏置"},
    {0x16, 0x3C, "ADC配置"},
    {0x17, 0x18, "DAC配置"},
    {0x09, 0x01, "I2S格式"},
    {0x0A, 0x01, "I2S配置"},
    {0x0D, 0x14, "系统配置"},
    {0x00, 0x80, "芯片启用"},
  };
  
  for (int i = 0; i < 10; i++) {
    if (!writeES8311Register(config[i].reg, config[i].value)) {
      Serial.printf("     ❌ %s失败\n", config[i].desc);
      return false;
    }
    delay(10);
  }
  
  return true;
}

void testI2S() {
  Serial.println("\n🎧 测试I2S接口...");
  
  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX | I2S_MODE_RX),
    .sample_rate = 16000,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 4,
    .dma_buf_len = 256,
    .use_apll = false,
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
    }
  }
}

void showResults() {
  Serial.println("\n" + String('=', 60));
  Serial.println("测试结果汇总");
  Serial.println(String('=', 60));
  
  Serial.printf("CODEC电源控制:     %s\n", results.codec_power_control_ok ? "✅ 正常" : "❌ 失败");
  Serial.printf("ES8311设备检测:    %s\n", results.es8311_detected ? "✅ 正常" : "❌ 失败");
  Serial.printf("ES8311配置:        %s\n", results.es8311_configured ? "✅ 正常" : "❌ 失败");
  Serial.printf("BMI270 IMU:        %s\n", results.bmi270_ok ? "✅ 正常" : "❌ 失败");
  Serial.printf("I2S接口:           %s\n", results.i2s_ok ? "✅ 正常" : "❌ 失败");
  
  // 设置相应的LED颜色
  if (results.codec_power_control_ok && results.es8311_configured && results.i2s_ok) {
    setWS2812Color(0x001000);  // 绿色 - 全部正常
    Serial.println("\n🎉 系统完全正常，可以进行音频测试！");
  } else if (results.codec_power_control_ok) {
    setWS2812Color(0x101000);  // 黄色 - 部分正常
    Serial.println("\n⚠️ 部分功能正常，可以尝试音频测试");
  } else {
    setWS2812Color(0x100000);  // 红色 - 主要问题
    Serial.println("\n❌ 主要功能异常，需要检查硬件");
  }
  
  Serial.println(String('=', 60));
}

void handleKeyPress() {
  static bool lastKeyState = HIGH;
  bool currentKeyState = digitalRead(KEY_PIN);
  
  if (lastKeyState == HIGH && currentKeyState == LOW) {
    if (results.es8311_configured && results.i2s_ok) {
      performAudioTest();
    } else {
      Serial.println("⚠️ 音频硬件未就绪");
      setWS2812Color(0x100000);  // 红色警告
      delay(500);
    }
  }
  
  lastKeyState = currentKeyState;
}

void performAudioTest() {
  Serial.println("\n🎤 开始音频测试...");
  
  setWS2812Color(0x101010);  // 白色 - 测试中
  digitalWrite(PA_CTRL_PIN, HIGH);
  delay(100);
  
  const int bufferSize = 256;
  int16_t buffer[bufferSize];
  int maxAmplitude = 0;
  int totalSamples = 0;
  
  unsigned long startTime = millis();
  while (millis() - startTime < 3000) {
    size_t bytesRead = 0;
    esp_err_t result = i2s_read(I2S_NUM_0, buffer, sizeof(buffer), &bytesRead, pdMS_TO_TICKS(100));
    
    if (result == ESP_OK && bytesRead > 0) {
      int samples = bytesRead / sizeof(int16_t);
      totalSamples += samples;
      
      for (int i = 0; i < samples; i++) {
        int amplitude = abs(buffer[i]);
        if (amplitude > maxAmplitude) {
          maxAmplitude = amplitude;
        }
      }
      
      // 环回播放
      size_t bytesWritten = 0;
      i2s_write(I2S_NUM_0, buffer, bytesRead, &bytesWritten, pdMS_TO_TICKS(10));
    }
  }
  
  digitalWrite(PA_CTRL_PIN, LOW);
  
  Serial.printf("🎵 音频测试完成:\n");
  Serial.printf("   总采样数: %d\n", totalSamples);
  Serial.printf("   最大振幅: %d\n", maxAmplitude);
  Serial.printf("   信号强度: %.1f%%\n", (maxAmplitude / 32767.0) * 100);
  
  if (maxAmplitude > 1000) {
    results.audio_test_ok = true;
    setWS2812Color(0x001000);  // 绿色 - 成功
    Serial.println("✅ 音频测试成功！");
  } else {
    setWS2812Color(0x100000);  // 红色 - 失败
    Serial.println("⚠️ 音频信号微弱，检查麦克风连接");
  }
}

void updateStatusDisplay() {
  static unsigned long lastUpdate = 0;
  static int breathStep = 0;
  
  if (millis() - lastUpdate > 200) {
    if (results.codec_power_control_ok) {
      // 如果基本功能正常，显示呼吸效果
      breathStep = (breathStep + 1) % 20;
      int brightness = (breathStep < 10) ? breathStep * 2 : (19 - breathStep) * 2;
      
      if (results.es8311_configured && results.i2s_ok) {
        setWS2812Color(brightness << 8);  // 绿色呼吸
      } else {
        setWS2812Color((brightness << 12) | (brightness << 8));  // 黄色呼吸
      }
    }
    lastUpdate = millis();
  }
}

// ========== 辅助函数 ==========

void initWS2812() {
  pinMode(WS2812_PIN, OUTPUT);
  digitalWrite(WS2812_PIN, LOW);
  delayMicroseconds(300);
}

void setWS2812Color(uint32_t color) {
  uint8_t red = (color >> 16) & 0xFF;
  uint8_t green = (color >> 8) & 0xFF;
  uint8_t blue = color & 0xFF;
  uint32_t grbColor = (green << 16) | (red << 8) | blue;
  
  noInterrupts();
  for (int bit = 23; bit >= 0; bit--) {
    if (grbColor & (1 << bit)) {
      digitalWrite(WS2812_PIN, HIGH);
      delayMicroseconds(1);
      digitalWrite(WS2812_PIN, LOW);
      delayMicroseconds(1);
    } else {
      digitalWrite(WS2812_PIN, HIGH);
      delayMicroseconds(1);
      digitalWrite(WS2812_PIN, LOW);
      delayMicroseconds(2);
    }
  }
  interrupts();
  
  digitalWrite(WS2812_PIN, LOW);
  delayMicroseconds(300);
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