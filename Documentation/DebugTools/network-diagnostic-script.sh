#!/bin/bash

echo "🌐 Smart Home Network Diagnostic"
echo "==============================="

# 获取系统信息
echo "📍 System Information:"
echo "OS: $(uname -s)"
echo "Architecture: $(uname -m)"

# 获取所有网络接口
echo -e "\n📡 Network Interfaces:"
if command -v ifconfig &> /dev/null; then
    ifconfig | grep -E "inet |ether "
elif command -v ip &> /dev/null; then
    ip addr show | grep -E "inet |link/ether"
else
    echo "⚠️ Neither ifconfig nor ip command found"
fi

# 获取默认路由
echo -e "\n🚏 Default Routes:"
if command -v route &> /dev/null; then
    route -n | grep '^0.0.0.0'
elif command -v ip &> /dev/null; then
    ip route | grep default
fi

# Docker网络信息
echo -e "\n🐳 Docker Network Information:"
echo "Docker networks:"
docker network ls

echo -e "\nBridge network details:"
docker network inspect bridge | grep -E '"Subnet"|"Gateway"|"IPAddress"' | head -10

# Docker容器IP地址
echo -e "\n📦 Container IP Addresses:"
containers=("ai-assistant-coordinator" "ai-assistant-stt" "ai-assistant-tts" "ai-assistant-iot" "ai-assistant-ollama")

for container in "${containers[@]}"; do
    if docker ps --format "table {{.Names}}" | grep -q "$container"; then
        ip=$(docker inspect "$container" | grep '"IPAddress"' | head -1 | cut -d'"' -f4)
        echo "$container: $ip"
    else
        echo "$container: NOT RUNNING"
    fi
done

# 端口绑定检查
echo -e "\n🔌 Port Bindings:"
echo "Listening ports on host:"
netstat -tulpn 2>/dev/null | grep -E ":(8080|8000|8001|8002|11434)" || \
lsof -i -P -n 2>/dev/null | grep -E ":(8080|8000|8001|8002|11434)"

# Docker端口映射
echo -e "\nDocker port mappings:"
for container in "${containers[@]}"; do
    if docker ps --format "table {{.Names}}" | grep -q "$container"; then
        echo -n "$container: "
        docker port "$container" 2>/dev/null || echo "No exposed ports"
    fi
done

# WiFi网络信息（如果是macOS）
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "\n📶 WiFi Information (macOS):"
    echo "Current WiFi network:"
    /System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I | grep -E "SSID|BSSID|Security"
    
    echo -e "\nWiFi IP address:"
    ifconfig en0 | grep "inet " | awk '{print $2}'
fi

# 防火墙状态
echo -e "\n🔥 Firewall Status:"
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "macOS Firewall:"
    sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate 2>/dev/null || echo "Cannot check firewall (need sudo)"
elif command -v ufw &> /dev/null; then
    echo "UFW status:"
    ufw status
elif command -v iptables &> /dev/null; then
    echo "iptables rules:"
    iptables -L -n | head -10
fi

# 测试网络连通性
echo -e "\n🧪 Network Connectivity Tests:"

# 测试localhost
echo -n "Testing localhost:8080... "
if curl -s --max-time 3 http://localhost:8080 > /dev/null; then
    echo "✅ OK"
else
    echo "❌ Failed"
fi

# 测试Docker bridge网络
echo -n "Testing 0.0.0.0:8080... "
if curl -s --max-time 3 http://0.0.0.0:8080 > /dev/null; then
    echo "✅ OK"
else
    echo "❌ Failed"
fi

# 获取WiFi接口IP
if [[ "$OSTYPE" == "darwin"* ]]; then
    WIFI_IP=$(ifconfig en0 | grep "inet " | awk '{print $2}')
    if [ ! -z "$WIFI_IP" ]; then
        echo -n "Testing WiFi IP ($WIFI_IP):8080... "
        if curl -s --max-time 3 "http://$WIFI_IP:8080" > /dev/null; then
            echo "✅ OK"
        else
            echo "❌ Failed"
        fi
    fi
fi

# Docker容器内部测试
echo -e "\n🔬 Docker Internal Connectivity:"
if docker ps --format "table {{.Names}}" | grep -q "ai-assistant-coordinator"; then
    echo "Testing from inside coordinator container:"
    docker exec ai-assistant-coordinator curl -s --max-time 3 http://localhost:8080 > /dev/null && echo "✅ Internal localhost OK" || echo "❌ Internal localhost failed"
fi

echo -e "\n📝 Recommendations for ESP8266:"
echo "================================"

# 推荐IP地址
if [[ "$OSTYPE" == "darwin"* ]]; then
    WIFI_IP=$(ifconfig en0 | grep "inet " | awk '{print $2}')
    if [ ! -z "$WIFI_IP" ]; then
        echo "🎯 Use this IP in ESP8266 code: $WIFI_IP"
        echo "   const char* server_host = \"$WIFI_IP\";"
        echo "   WebSocket URL: ws://$WIFI_IP:8080/ws"
    fi
else
    # 对于Linux，尝试获取主要网络接口IP
    MAIN_IP=$(ip route get 8.8.8.8 | grep -oP 'src \K\S+' 2>/dev/null)
    if [ ! -z "$MAIN_IP" ]; then
        echo "🎯 Use this IP in ESP8266 code: $MAIN_IP"
        echo "   const char* server_host = \"$MAIN_IP\";"
        echo "   WebSocket URL: ws://$MAIN_IP:8080/ws"
    fi
fi

echo -e "\n🔧 Troubleshooting Steps:"
echo "1. Ensure ESP8266 is on the same WiFi network"
echo "2. Check if macOS firewall is blocking incoming connections"
echo "3. Try disabling macOS firewall temporarily for testing"
echo "4. Verify Docker port binding with: docker port ai-assistant-coordinator"
echo "5. Test connectivity from another device on the same network"
