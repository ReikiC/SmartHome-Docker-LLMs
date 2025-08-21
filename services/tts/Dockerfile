FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 创建音频目录
RUN mkdir -p /app/audio

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8001

# 启动应用
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]