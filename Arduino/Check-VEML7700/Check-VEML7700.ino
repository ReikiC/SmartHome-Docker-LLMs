#include <Wire.h>

// VEML7700 I2C地址和所有寄存器
#define VEML7700_ADDR 0x10
#define VEML7700_CONF_REG     0x00
#define VEML7700_THD_HIGH_REG 0x01
#define VEML7700_THD_LOW_REG  0x02
#define VEML7700_PSM_REG      0x03
#define VEML7700_ALS_REG      0x04
#define VEML7700_WHITE_REG    0x05
#define VEML7700_ALS_INT_REG  0x06

void setup() {
  Serial.begin(115200);
  Wire.begin();
  delay(2000);
  
  Serial.println("=== VEML7700 完整硬件诊断 ===");
  Serial.println();
  
  // 完整的诊断流程
  performCompleteHardwareDiagnostic();
}

void loop() {
  // 持续监控模式
  Serial.println("\n=== 实时监控模式 ===");
  
  // 连续读取所有寄存器
  readAllRegisters();
  
  // 测试不同的I2C时钟速度
  testDifferentI2CSpeeds();
  
  delay(3000);
}

void performCompleteHardwareDiagnostic() {
  Serial.println("1. I2C总线诊断");
  testI2CBus();
  
  Serial.println("\n2. VEML7700设备检测");
  testVEML7700Detection();
  
  Serial.println("\n3. 寄存器访问测试");
  testRegisterAccess();
  
  Serial.println("\n4. 配置寄存器写入测试");
  testConfigurationWrite();
  
  Serial.println("\n5. 数据寄存器持续读取测试");
  testContinuousReading();
  
  Serial.println("\n6. 电源复位测试");
  testPowerReset();
}

void testI2CBus() {
  Serial.println("扫描I2C总线上的所有设备:");
  
  int deviceCount = 0;
  for (uint8_t addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    uint8_t error = Wire.endTransmission();
    
    if (error == 0) {
      Serial.print("  发现设备: 0x");
      if (addr < 16) Serial.print("0");
      Serial.print(addr, HEX);
      
      if (addr == VEML7700_ADDR) {
        Serial.print(" <- VEML7700");
      }
      Serial.println();
      deviceCount++;
    }
  }
  
  Serial.print("总共发现 ");
  Serial.print(deviceCount);
  Serial.println(" 个I2C设备");
  
  if (deviceCount == 0) {
    Serial.println("⚠️ 警告: 没有发现任何I2C设备！");
    Serial.println("请检查:");
    Serial.println("  - SDA/SCL接线");
    Serial.println("  - 上拉电阻");
    Serial.println("  - 电源供电");
  }
}

void testVEML7700Detection() {
  for (int attempt = 1; attempt <= 5; attempt++) {
    Serial.print("尝试 ");
    Serial.print(attempt);
    Serial.print(": ");
    
    Wire.beginTransmission(VEML7700_ADDR);
    uint8_t error = Wire.endTransmission();
    
    Serial.print("错误代码 = ");
    Serial.print(error);
    Serial.print(" (");
    
    switch (error) {
      case 0: Serial.print("成功"); break;
      case 1: Serial.print("数据太长"); break;
      case 2: Serial.print("接收到NACK(地址)"); break;
      case 3: Serial.print("接收到NACK(数据)"); break;
      case 4: Serial.print("其他错误"); break;
      default: Serial.print("未知错误");
    }
    Serial.println(")");
    
    delay(200);
  }
}

void testRegisterAccess() {
  uint8_t registers[] = {0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06};
  String regNames[] = {"CONF", "THD_HIGH", "THD_LOW", "PSM", "ALS", "WHITE", "ALS_INT"};
  
  for (int i = 0; i < 7; i++) {
    Serial.print("寄存器 ");
    Serial.print(regNames[i]);
    Serial.print(" (0x");
    if (registers[i] < 16) Serial.print("0");
    Serial.print(registers[i], HEX);
    Serial.print("): ");
    
    uint16_t value = 0;
    bool success = readRegister16Bit(registers[i], value);
    
    if (success) {
      Serial.print("0x");
      if (value < 0x1000) Serial.print("0");
      if (value < 0x100) Serial.print("0");
      if (value < 0x10) Serial.print("0");
      Serial.print(value, HEX);
      Serial.print(" (");
      Serial.print(value);
      Serial.println(")");
    } else {
      Serial.println("读取失败");
    }
    
    delay(50);
  }
}

void testConfigurationWrite() {
  Serial.println("测试配置寄存器写入:");
  
  // 测试配置1: 正常模式
  uint16_t testConfigs[] = {0x0000, 0x0001, 0x0800, 0x1000};
  String configDesc[] = {"正常模式", "关闭模式", "增益2x", "积分50ms"};
  
  for (int i = 0; i < 4; i++) {
    Serial.print("  写入配置 ");
    Serial.print(configDesc[i]);
    Serial.print(" (0x");
    Serial.print(testConfigs[i], HEX);
    Serial.print("): ");
    
    // 写入配置
    bool writeSuccess = writeRegister16Bit(VEML7700_CONF_REG, testConfigs[i]);
    if (!writeSuccess) {
      Serial.println("写入失败");
      continue;
    }
    
    delay(100);
    
    // 读回验证
    uint16_t readBack = 0;
    bool readSuccess = readRegister16Bit(VEML7700_CONF_REG, readBack);
    
    if (readSuccess) {
      if (readBack == testConfigs[i]) {
        Serial.println("✓ 写入成功，验证通过");
      } else {
        Serial.print("✗ 写入失败，期望 0x");
        Serial.print(testConfigs[i], HEX);
        Serial.print("，实际 0x");
        Serial.println(readBack, HEX);
      }
    } else {
      Serial.println("读回失败");
    }
  }
}

void testContinuousReading() {
  Serial.println("连续读取ALS寄存器 (10次):");
  
  // 先设置为正常模式
  writeRegister16Bit(VEML7700_CONF_REG, 0x0000);
  delay(200);
  
  for (int i = 0; i < 10; i++) {
    uint16_t alsValue = 0;
    bool success = readRegister16Bit(VEML7700_ALS_REG, alsValue);
    
    Serial.print("  读取 ");
    Serial.print(i + 1);
    Serial.print(": ");
    
    if (success) {
      Serial.print("0x");
      if (alsValue < 0x1000) Serial.print("0");
      if (alsValue < 0x100) Serial.print("0");
      if (alsValue < 0x10) Serial.print("0");
      Serial.print(alsValue, HEX);
      Serial.print(" (");
      Serial.print(alsValue);
      Serial.println(")");
    } else {
      Serial.println("失败");
    }
    
    delay(300);
  }
}

void testPowerReset() {
  Serial.println("电源复位测试:");
  
  // 读取复位前的配置
  uint16_t beforeReset = 0;
  readRegister16Bit(VEML7700_CONF_REG, beforeReset);
  Serial.print("  复位前配置: 0x");
  Serial.println(beforeReset, HEX);
  
  // 写入特殊配置
  writeRegister16Bit(VEML7700_CONF_REG, 0xABCD);
  delay(100);
  
  uint16_t afterWrite = 0;
  readRegister16Bit(VEML7700_CONF_REG, afterWrite);
  Serial.print("  写入后配置: 0x");
  Serial.println(afterWrite, HEX);
  
  // 软件复位 (关闭再开启)
  writeRegister16Bit(VEML7700_CONF_REG, 0x0001); // 关闭
  delay(100);
  writeRegister16Bit(VEML7700_CONF_REG, 0x0000); // 开启
  delay(100);
  
  uint16_t afterReset = 0;
  readRegister16Bit(VEML7700_CONF_REG, afterReset);
  Serial.print("  复位后配置: 0x");
  Serial.println(afterReset, HEX);
}

void readAllRegisters() {
  Serial.println("所有寄存器当前值:");
  
  uint8_t registers[] = {0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06};
  String regNames[] = {"CONF", "THD_H", "THD_L", "PSM", "ALS", "WHITE", "INT"};
  
  for (int i = 0; i < 7; i++) {
    uint16_t value = 0;
    bool success = readRegister16Bit(registers[i], value);
    
    Serial.print("  ");
    Serial.print(regNames[i]);
    Serial.print(": ");
    
    if (success) {
      Serial.print("0x");
      if (value < 0x1000) Serial.print("0");
      if (value < 0x100) Serial.print("0");  
      if (value < 0x10) Serial.print("0");
      Serial.print(value, HEX);
      
      if (i == 4 || i == 5) { // ALS或WHITE寄存器
        Serial.print(" (");
        Serial.print(value);
        Serial.print(")");
      }
    } else {
      Serial.print("ERROR");
    }
    
    Serial.println();
  }
}

void testDifferentI2CSpeeds() {
  Serial.println("\n测试不同I2C速度:");
  
  // 测试不同的I2C时钟频率
  uint32_t speeds[] = {100000, 400000, 50000};
  String speedNames[] = {"100kHz", "400kHz", "50kHz"};
  
  for (int i = 0; i < 3; i++) {
    Serial.print("  测试 ");
    Serial.print(speedNames[i]);
    Serial.print(": ");
    
    Wire.setClock(speeds[i]);
    delay(10);
    
    uint16_t value = 0;
    bool success = readRegister16Bit(VEML7700_ALS_REG, value);
    
    if (success) {
      Serial.print("成功 (ALS=");
      Serial.print(value);
      Serial.println(")");
    } else {
      Serial.println("失败");
    }
  }
  
  // 恢复默认速度
  Wire.setClock(100000);
}

bool readRegister16Bit(uint8_t reg, uint16_t &value) {
  Wire.beginTransmission(VEML7700_ADDR);
  Wire.write(reg);
  
  if (Wire.endTransmission() != 0) {
    return false;
  }
  
  Wire.requestFrom(VEML7700_ADDR, 2);
  if (Wire.available() == 2) {
    uint8_t low = Wire.read();
    uint8_t high = Wire.read();
    value = (high << 8) | low;
    return true;
  }
  
  return false;
}

bool writeRegister16Bit(uint8_t reg, uint16_t value) {
  Wire.beginTransmission(VEML7700_ADDR);
  Wire.write(reg);
  Wire.write(value & 0xFF);        // Low byte
  Wire.write((value >> 8) & 0xFF); // High byte
  
  return (Wire.endTransmission() == 0);
}