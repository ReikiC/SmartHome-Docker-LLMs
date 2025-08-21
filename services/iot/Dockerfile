FROM python:3.10-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 创建配置目录
RUN mkdir -p /app/config

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8002

# 启动应用
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8002"]