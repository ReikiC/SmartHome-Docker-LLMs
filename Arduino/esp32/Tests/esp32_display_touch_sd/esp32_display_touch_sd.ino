#include <Arduino.h>
#include <TFT_eSPI.h>      // 显示屏库
#include <SPI.h>
#include <SD.h>            // SD卡库
#include <PNGdec.h>        // PNG解码器库
#include <JPEGDecoder.h>   // 可选：JPEG解码
#include <FS.h>
#include <SPIFFS.h>

// 显示屏配置 - 要在User_Setup.h中正确配置TFT_eSPI
TFT_eSPI tft = TFT_eSPI();
TFT_eSprite sprite = TFT_eSprite(&tft); // 用于双缓冲

// 触摸配置
#define TOUCH_THRESHOLD 40 // 触摸阈值，根据你的屏幕调整

// SD卡配置
#define SD_CS 5            // SD卡CS引脚，根据接线修改
#define SD_SCK 18          // SD卡SCK引脚
#define SD_MISO 19         // SD卡MISO引脚
#define SD_MOSI 23         // SD卡MOSI引脚

// UART配置（与主ESP32通信）
#define RX_PIN 16          // UART RX引脚
#define TX_PIN 17          // UART TX引脚
#define UART_BAUD 115200   // 波特率

// 显示屏分辨率
#define SCREEN_WIDTH 320   // 显示屏宽度
#define SCREEN_HEIGHT 480  // 显示屏高度

// PNG图片缩放
#define ORIGINAL_WIDTH 400   // 原始图片宽度
#define ORIGINAL_HEIGHT 400  // 原始图片高度
#define SCALED_WIDTH 320     // 缩放后宽度
#define SCALED_HEIGHT 320    // 缩放后高度

// 定义表情路径
#define MAX_IMAGES 7         // 最大图片数量
String imagePaths[MAX_IMAGES] = {
  "/neutral.png",
  "/smile.png",
  "/thinking.png",
  "/sad.png",
  "/surprised.png",
  "/happy.png",
  "/confused.png"
};

// PNG解码器
PNG png;

// 当前图片索引
int currentImage = 0;

// UART命令缓冲区
String commandBuffer = "";

// 用于PNG解码的缓冲区
#define PNG_BUFFER_SIZE 32768  // 根据需要调整大小
uint8_t pngBuffer[PNG_BUFFER_SIZE];

// PNG绘制回调函数
void PNGDraw(PNGDRAW *pDraw) {
  uint16_t lineBuffer[SCREEN_WIDTH];
  
  // 计算缩放因子
  float scaleX = (float)SCALED_WIDTH / ORIGINAL_WIDTH;
  float scaleY = (float)SCALED_HEIGHT / ORIGINAL_HEIGHT;

  // 检查是否在显示屏范围内
  if (pDraw->y * scaleY < SCREEN_HEIGHT) {
    png.getLineAsRGB565(pDraw, lineBuffer, PNG_RGB565_LITTLE_ENDIAN, 0xffffffff);
    
    // 绘制缩放后的行
    for (int x = 0; x < SCALED_WIDTH; x++) {
      // 计算原始图像中对应的像素位置
      int srcX = (int)(x / scaleX);
      if (srcX < pDraw->iWidth) {
        tft.drawPixel(x + (SCREEN_WIDTH - SCALED_WIDTH) / 2, 
                      pDraw->y * scaleY + (SCREEN_HEIGHT - SCALED_HEIGHT) / 2, 
                      lineBuffer[srcX]);
      }
    }
  }
}

// SD卡文件读取函数
void * PNGOpenFile(const char *filename, int32_t *size) {
  File pngFile = SD.open(filename, "r");
  if (!pngFile) {
    Serial.print("打开PNG文件失败: ");
    Serial.println(filename);
    return NULL;
  }
  
  *size = pngFile.size();
  
  if (*size > PNG_BUFFER_SIZE) {
    Serial.println("PNG文件太大，无法放入缓冲区");
    pngFile.close();
    return NULL;
  }
  
  pngFile.read(pngBuffer, *size);
  pngFile.close();
  
  return pngBuffer;
}

// 显示PNG图片
bool displayPNG(const char *filename) {
  Serial.print("显示PNG图片: ");
  Serial.println(filename);
  
  int32_t fileSize = 0;
  void *pngData = PNGOpenFile(filename, &fileSize);
  
  if (!pngData) {
    return false;
  }
  
  // 清除屏幕中央区域
  tft.fillRect((SCREEN_WIDTH - SCALED_WIDTH) / 2, 
               (SCREEN_HEIGHT - SCALED_HEIGHT) / 2, 
               SCALED_WIDTH, SCALED_HEIGHT, TFT_BLACK);
  
  int rc = png.openRAM((uint8_t *)pngData, fileSize, PNGDraw);
  if (rc != PNG_SUCCESS) {
    Serial.print("打开PNG数据失败: ");
    Serial.println(rc);
    return false;
  }
  
  Serial.printf("PNG图片大小: %d x %d, 缩放至: %d x %d\n", 
                png.getWidth(), png.getHeight(), SCALED_WIDTH, SCALED_HEIGHT);
  
  rc = png.decode(NULL, 0);
  png.close();
  
  return (rc == PNG_SUCCESS);
}

// 处理表情命令
void processExpressionCommand(String command) {
  command.trim();  // 删除空格
  
  int expressionIndex = -1;
  
  if (command == "neutral")
    expressionIndex = 0;
  else if (command == "smile")
    expressionIndex = 1;
  else if (command == "thinking")
    expressionIndex = 2;
  else if (command == "sad")
    expressionIndex = 3;
  else if (command == "surprised")
    expressionIndex = 4;
  else if (command == "happy")
    expressionIndex = 5;
  else if (command == "confused")
    expressionIndex = 6;
  else
    Serial.println("未知表情命令: " + command);
  
  if (expressionIndex >= 0 && expressionIndex < MAX_IMAGES) {
    currentImage = expressionIndex;
    if (displayPNG(imagePaths[currentImage].c_str())) {
      Serial.println("表情显示成功");
    } else {
      Serial.println("表情显示失败");
    }
  }
}

// 处理UART命令
void processCommand(String command) {
  if (command.startsWith("EXPR:")) {
    // 提取表情部分
    String expression = command.substring(5);
    processExpressionCommand(expression);
  } else {
    Serial.print("未知命令: ");
    Serial.println(command);
  }
}

// 处理触摸事件
void handleTouch() {
  uint16_t touchX, touchY;
  uint8_t touchZ;
  
  // 检测触摸
  bool touched = tft.getTouch(&touchX, &touchY, &touchZ);
  
  if (touched && touchZ > TOUCH_THRESHOLD) {
    Serial.print("触摸检测: X=");
    Serial.print(touchX);
    Serial.print(", Y=");
    Serial.print(touchY);
    Serial.print(", Z=");
    Serial.println(touchZ);
    
    // 简单的触摸响应 - 切换到下一个图片
    currentImage = (currentImage + 1) % MAX_IMAGES;
    displayPNG(imagePaths[currentImage].c_str());
    
    // 通知主ESP32触摸事件
    Serial2.print("TOUCH:");
    Serial2.print(touchX);
    Serial2.print(",");
    Serial2.println(touchY);
    
    // 防抖动延迟
    delay(300);
  }
}

// 绘制状态栏
void drawStatusBar() {
  tft.fillRect(0, 0, SCREEN_WIDTH, 30, TFT_NAVY);
  tft.setTextColor(TFT_WHITE);
  tft.setTextSize(1);
  tft.setCursor(10, 10);
  tft.print("AI语音助手 - 表情: ");
  tft.print(imagePaths[currentImage].substring(1, imagePaths[currentImage].length() - 4));
}

// 绘制底部控制栏
void drawControlBar() {
  tft.fillRect(0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40, TFT_DARKGREY);
  
  // 绘制控制按钮
  // 上一个表情
  tft.fillRoundRect(20, SCREEN_HEIGHT - 35, 80, 30, 5, TFT_BLUE);
  tft.setTextColor(TFT_WHITE);
  tft.setTextSize(2);
  tft.setCursor(30, SCREEN_HEIGHT - 30);
  tft.print("上一个");
  
  // 下一个表情
  tft.fillRoundRect(SCREEN_WIDTH - 100, SCREEN_HEIGHT - 35, 80, 30, 5, TFT_BLUE);
  tft.setCursor(SCREEN_WIDTH - 90, SCREEN_HEIGHT - 30);
  tft.print("下一个");
}

// 初始化SD卡
bool initSD() {
  SPI.begin(SD_SCK, SD_MISO, SD_MOSI);
  
  if (!SD.begin(SD_CS)) {
    Serial.println("SD卡初始化失败!");
    return false;
  }
  
  Serial.println("SD卡初始化成功!");
  
  // 列出根目录文件
  File root = SD.open("/");
  printDirectory(root, 0);
  
  return true;
}

// 递归打印目录内容
void printDirectory(File dir, int numTabs) {
  while (true) {
    File entry = dir.openNextFile();
    if (!entry) {
      // 没有更多文件
      break;
    }
    
    for (uint8_t i = 0; i < numTabs; i++) {
      Serial.print('\t');
    }
    
    Serial.print(entry.name());
    
    if (entry.isDirectory()) {
      Serial.println("/");
      printDirectory(entry, numTabs + 1);
    } else {
      // 文件，打印大小
      Serial.print("\t\t");
      Serial.println(entry.size(), DEC);
    }
    
    entry.close();
  }
}

void setup() {
  // 初始化串口通信
  Serial.begin(115200);
  Serial2.begin(UART_BAUD, SERIAL_8N1, RX_PIN, TX_PIN);
  
  Serial.println("\nESP32表情显示系统启动");
  
  // 初始化TFT显示屏
  tft.init();
  tft.setRotation(0); // 竖屏模式
  tft.fillScreen(TFT_BLACK);
  
  // 初始化触摸
  uint16_t calData[5] = {275, 3620, 264, 3532, 1};
  tft.setTouch(calData); // 使用预设的校准数据，或运行校准程序获取
  
  // 显示启动信息
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.setTextSize(2);
  tft.setCursor(20, 180);
  tft.println("AI语音助手");
  tft.setCursor(20, 210);
  tft.println("表情显示系统");
  tft.setCursor(20, 240);
  tft.println("正在初始化...");
  
  // 初始化SD卡
  if (!initSD()) {
    tft.setTextColor(TFT_RED);
    tft.setCursor(20, 270);
    tft.println("SD卡加载失败!");
    delay(3000);
  }
  
  // 绘制界面
  tft.fillScreen(TFT_BLACK);
  drawStatusBar();
  drawControlBar();
  
  // 显示默认表情
  displayPNG(imagePaths[currentImage].c_str());
  
  Serial.println("初始化完成，等待命令...");
}

void loop() {
  // 处理触摸事件
  handleTouch();
  
  // 接收UART命令
  while (Serial2.available()) {
    char c = Serial2.read();
    if (c == '\n') {
      // 处理完整命令
      if (commandBuffer.length() > 0) {
        Serial.print("收到命令: ");
        Serial.println(commandBuffer);
        processCommand(commandBuffer);
        commandBuffer = "";
      }
    } else if (c != '\r') {
      // 累积命令字符
      commandBuffer += c;
    }
  }
  
  // 检查底部控制栏的触摸
  uint16_t touchX, touchY;
  uint8_t touchZ;
  bool touched = tft.getTouch(&touchX, &touchY, &touchZ);
  
  if (touched && touchZ > TOUCH_THRESHOLD) {
    // 检查是否触摸了底部控制栏
    if (touchY > SCREEN_HEIGHT - 40) {
      if (touchX < SCREEN_WIDTH / 2) {
        // 上一个表情
        currentImage = (currentImage + MAX_IMAGES - 1) % MAX_IMAGES;
      } else {
        // 下一个表情
        currentImage = (currentImage + 1) % MAX_IMAGES;
      }
      
      displayPNG(imagePaths[currentImage].c_str());
      drawStatusBar(); // 更新状态栏
      
      // 防抖动延迟
      delay(300);
    }
  }
}