#!/bin/bash

# 设置服务器端口
PORT=1145

# 设置颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_message() {
  echo -e "${2}${1}${NC}"
}

# 获取当前目录
CURRENT_DIR=$(pwd)
print_message "启动网页服务器于目录: $CURRENT_DIR" "$BLUE"

# 检查 Python 3
if command -v python3 &> /dev/null; then
  print_message "使用 Python 3 启动服务器" "$GREEN"
  print_message "网页服务器启动在: http://localhost:$PORT" "$GREEN"
  print_message "可通过以下地址访问:" "$YELLOW"
  print_message "  - http://localhost:$PORT" "$YELLOW"
  print_message "  - http://127.0.0.1:$PORT" "$YELLOW"
  
  # 获取本机IP地址
  LOCAL_IP=$(hostname -I | awk '{print $1}')
  if [ ! -z "$LOCAL_IP" ]; then
    print_message "  - http://$LOCAL_IP:$PORT" "$YELLOW"
  fi
  
  print_message "按 Ctrl+C 停止服务器" "$YELLOW"
  print_message "------------------------" "$BLUE"
  
  # 启动 Python HTTP 服务器
  python3 -m http.server $PORT
  
elif command -v python &> /dev/null; then
  print_message "使用 Python 2 启动服务器" "$GREEN"
  print_message "网页服务器启动在: http://localhost:$PORT" "$GREEN"
  print_message "按 Ctrl+C 停止服务器" "$YELLOW"
  print_message "------------------------" "$BLUE"
  
  # 启动 Python 2 HTTP 服务器
  python -m SimpleHTTPServer $PORT
  
else
  print_message "Python 未安装。请安装 Python: sudo apt install python3" "$RED"
  exit 1
fi