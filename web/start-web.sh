#!/bin/bash

# 设置服务器端口
PORT=1145

# 设置颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
  echo -e "${2}${1}${NC}"
}

# 检查Node.js是否已安装
if ! command -v node &> /dev/null; then
  print_message "Node.js未安装。请先安装Node.js: https://nodejs.org/" "$RED"
  exit 1
fi

# 检查http-server是否已安装
if ! command -v http-server &> /dev/null; then
  print_message "http-server未安装。正在为你安装..." "$YELLOW"
  npm install -g http-server
  
  # 检查安装是否成功
  if ! command -v http-server &> /dev/null; then
    print_message "http-server安装失败。请尝试手动安装: npm install -g http-server" "$RED"
    exit 1
  fi
  
  print_message "http-server安装成功!" "$GREEN"
fi

# 获取当前目录
CURRENT_DIR=$(pwd)
print_message "启动网页服务器于目录: $CURRENT_DIR" "$BLUE"

# 启动http-server
print_message "网页服务器启动在: http://localhost:$PORT" "$GREEN"
print_message "按 Ctrl+C 停止服务器" "$YELLOW"
print_message "------------------------" "$BLUE"

# 启动服务器，禁用缓存以确保始终加载最新文件
http-server -p $PORT -c-1

# 脚本不会自然到达这里，因为http-server会持续运行
# 但如果http-server失败，将显示以下消息
print_message "服务器意外停止！" "$RED"
