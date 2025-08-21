# AI 语音助手 + IoT 控制系统

这是一个基于Docker的AI语音助手系统，使用Ollama作为核心LLM，集成语音识别、语音合成和IoT设备控制功能。系统设计用于低算力设备（ESP32）与PC端Docker容器的协作，实现语音交互、表情显示和IoT设备控制。

## 系统架构

系统由5个Docker容器组成，各自负责不同的功能：

1. **Ollama服务**：提供LLM（大型语言模型）能力，处理自然语言理解和生成
2. **STT服务**：负责语音识别（Speech-to-Text），将ESP32上传的语音转换为文本
3. **TTS服务**：负责语音合成（Text-to-Speech），将AI回复转换为ESP32可播放的音频
4. **IoT控制服务**：管理各种智能设备的状态和控制命令
5. **协调服务**：作为中央控制器，协调各服务之间的通信

## 环境要求

- Docker和Docker Compose
- Mac mini (M4) 或其他运行Docker的计算设备
- ESP32开发板（用于语音采集和播放）
- 可选：第二个ESP32开发板（用于LCD显示表情）

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/ai-voice-assistant-iot.git
cd ai-voice-assistant-iot
```

### 2. 创建目录结构

```bash
mkdir -p data/audio
mkdir -p data/ollama
mkdir -p services/coordinator
mkdir -p services/stt
mkdir -p services/tts
mkdir -p services/iot
mkdir -p esp32
```

### 3. 复制配置文件

将所有代码文件复制到相应目录：

- `docker-compose.yml` → 项目根目录
- 各服务的Python文件和Dockerfile → 对应服务目录
- ESP32代码 → esp32目录

### 4. 构建并启动Docker容器

```bash
docker-compose up --build
```

首次启动时，系统将下载相关镜像并构建容器，可能需要一些时间。

### 5. 配置并烧录ESP32

1. 修改ESP32代码中的WiFi配置和服务器IP地址
2. 使用Arduino IDE或PlatformIO将代码烧录到ESP32
3. 如果使用两个ESP32，还需要设置LCD显示的ESP32通信方式

## 使用方法

系统启动后，可以通过以下方式使用：

1. **语音交互**：按下ESP32上的按钮开始录音，录音完成后自动发送到服务器处理
2. **查看服务状态**：访问http://localhost:8080查看协调服务状态
3. **手动测试**：使用Postman或curl向各服务API发送请求进行测试

## 服务API说明

### 协调服务 (8080端口)

- `GET /` - 检查服务状态
- `POST /process_audio` - 处理音频并返回AI响应
- `POST /process_text` - 处理文本并返回AI响应
- `WebSocket /ws` - WebSocket连接端点

### STT服务 (8000端口)

- `GET /` - 检查服务状态
- `POST /transcribe` - 转录指定路径的音频文件
- `POST /upload` - 上传音频文件并转录
- UDP 8000端口 - 接收ESP32发送的音频数据

### TTS服务 (8001端口)

- `GET /` - 检查服务状态
- `GET /voices` - 列出所有可用的语音
- `POST /synthesize` - 合成语音并返回音频文件路径
- `GET /audio/{filename}` - 获取合成的音频文件
- `POST /stream` - 流式合成音频

### IoT控制服务 (8002端口)

- `GET /` - 检查服务状态
- `GET /devices` - 获取所有设备状态
- `GET /device/{device_type}/{location}` - 获取特定设备的状态
- `POST /control` - 控制IoT设备
- `WebSocket /ws` - WebSocket连接端点，用于设备状态更新

## Ollama模型配置

系统默认使用`llama3`模型，你可以通过以下方式下载并配置模型：

```bash
# 在宿主机上安装Ollama（如果还没有安装）
curl -fsSL https://ollama.com/install.sh | sh

# 下载llama3模型
ollama pull llama3

# 或者使用其他模型
ollama pull llama3:8b
```

你也可以在`docker-compose.yml`文件中修改`OLLAMA_MODEL`环境变量来使用不同的模型。

# 拉取指定的模型
curl -X POST http://localhost:11434/api/pull -d '{"name": "llama3"}'

# 拉取特定大小的模型
curl -X POST http://localhost:11434/api/pull -d '{"name": "llama3:8b"}'

## 自定义和扩展

### 添加新的IoT设备类型

1. 在`services/iot/app.py`的`device_states`字典中添加新设备类型
2. 在`extract_iot_commands`和`execute_command`函数中添加对应的处理逻辑
3. 更新ESP32代码中的`controlIoTDevice`函数以支持新设备

### 使用不同的TTS引擎

当前系统使用微软Edge TTS作为语音合成引擎。如果需要使用其他引擎：

1. 修改`services/tts/app.py`，替换Edge TTS相关代码
2. 更新`services/tts/requirements.txt`添加所需依赖
3. 重新构建TTS服务容器

### 优化STT模型

Whisper模型大小会影响识别质量和速度。可以通过修改环境变量`WHISPER_MODEL`来调整：
- `tiny` - 最小模型，速度最快但精度较低
- `base` - 默认模型，平衡速度和精度
- `small` - 较大模型，精度更高但速度较慢
- `medium` - 大型模型，精度高但需要更多计算资源
- `large` - 最大模型，精度最高但速度最慢

## 故障排除

### 1. ESP32无法连接到服务器

- 检查WiFi连接和网络配置
- 确保ESP32和Docker主机在同一网络
- 检查防火墙设置，确保UDP端口8000和WebSocket端口8080未被阻止

### 2. 语音识别不工作

- 检查麦克风连接和I2S配置
- 查看STT服务日志，确认音频数据是否正常接收
- 尝试调整录音音量或降噪设置

### 3. 语音合成没有声音

- 检查扬声器连接和I2S配置
- 确认音频文件路径是否正确
- 检查是否正确收到TTS服务响应

### 4. Ollama模型加载失败

- 确保有足够的磁盘空间和内存
- 检查Ollama服务日志以获取详细错误信息
- 尝试使用较小的模型（如`llama3:8b`）

## 注意事项

- 系统配置为内部网络使用，不建议直接暴露到公网
- 默认无安全认证，如需公网访问，请添加适当的认证机制
- ESP32的电源供应应稳定，以避免录音或播放中断
- Docker容器间通信依赖Docker网络，请确保容器名称解析正常

## 许可证

本项目采用MIT许可证。