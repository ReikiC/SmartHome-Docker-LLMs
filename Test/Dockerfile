# Test/Dockerfile.test
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
RUN pip install --no-cache-dir \
    requests \
    pandas \
    numpy \
    matplotlib \
    pytest \
    pytest-asyncio \
    pytest-cov

# 创建必要的目录
RUN mkdir -p /app/test_cases /app/results

# 设置Python环境变量
ENV PYTHONPATH=/app:$PYTHONPATH
ENV PYTHONUNBUFFERED=1

# 默认命令
CMD ["bash"]