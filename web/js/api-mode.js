const ModeSwitcher = {
        checkInterval: null,
        reconnectAttempts: 0,
        maxReconnectAttempts: 30, // 最多尝试30次，约30秒
        
        // 初始化
        async init() {
            await this.updateModeDisplay();
            this.setupEventListeners();
        },
        
        // 设置事件监听
        setupEventListeners() {
            // 监听服务状态
            window.addEventListener('beforeunload', () => {
                if (this.checkInterval) {
                    clearInterval(this.checkInterval);
                }
            });
        },
        
        // 获取当前模式
        async getCurrentMode() {
            try {
                const response = await fetch(`${API_URLS.coordinator}/api/mode`);
                if (!response.ok) throw new Error('Failed to get mode');
                return await response.json();
            } catch (error) {
                console.error('Error getting mode:', error);
                throw error;
            }
        },
        
        // 更新模式显示
        async updateModeDisplay() {
            try {
                const modeData = await this.getCurrentMode();
                
                // 更新显示
                document.getElementById('current-mode-display').textContent = modeData.mode.toUpperCase();
                document.getElementById('current-model-display').textContent = modeData.model;
                
                // 更新按钮状态
                const localBtn = document.getElementById('local-mode-btn');
                const apiBtn = document.getElementById('api-mode-btn');
                
                if (modeData.mode === 'local') {
                    localBtn.classList.add('active', 'btn-primary');
                    localBtn.classList.remove('btn-outline-primary');
                    apiBtn.classList.remove('active', 'btn-primary');
                    apiBtn.classList.add('btn-outline-primary');
                } else {
                    apiBtn.classList.add('active', 'btn-primary');
                    apiBtn.classList.remove('btn-outline-primary');
                    localBtn.classList.remove('active', 'btn-primary');
                    localBtn.classList.add('btn-outline-primary');
                }
                
                // 清除错误消息
                this.hideError();
                
            } catch (error) {
                this.showError('Unable to connect to service');
            }
        },
        
        // 切换模式
        async switchMode(newMode) {
            try {
                // 显示加载状态
                this.showLoading('Switching mode...');
                
                const response = await fetch(`${API_URLS.coordinator}/api/mode/switch`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mode: newMode })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    if (result.restart_required) {
                        // 服务需要重启
                        this.handleServiceRestart();
                    } else {
                        // 不需要重启（已经在该模式）
                        this.hideLoading();
                        await this.updateModeDisplay();
                        alert(result.message);
                    }
                } else {
                    throw new Error(result.error || 'Failed to switch mode');
                }
                
            } catch (error) {
                this.hideLoading();
                this.showError(`Failed to switch mode: ${error.message}`);
            }
        },
        
        // 处理服务重启
        handleServiceRestart() {
            this.showRestartProgress();
            this.reconnectAttempts = 0;
            
            // 等待2秒后开始检查服务
            setTimeout(() => {
                this.checkServiceAvailability();
            }, 2000);
        },
        
        // 检查服务可用性
        checkServiceAvailability() {
            this.checkInterval = setInterval(async () => {
                this.reconnectAttempts++;
                
                // 更新进度条
                const progress = (this.reconnectAttempts / this.maxReconnectAttempts) * 100;
                document.getElementById('restart-progress-bar').style.width = `${progress}%`;
                
                try {
                    // 尝试连接服务
                    const response = await fetch(`${API_URLS.coordinator}/health`, {
                        method: 'GET',
                        signal: AbortSignal.timeout(2000) // 2秒超时
                    });
                    
                    if (response.ok) {
                        // 服务已恢复
                        clearInterval(this.checkInterval);
                        this.onServiceRestored();
                    }
                } catch (error) {
                    // 服务仍然不可用
                    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                        clearInterval(this.checkInterval);
                        this.onRestartTimeout();
                    }
                }
            }, 1000); // 每秒检查一次
        },
        
        // 服务恢复
        async onServiceRestored() {
            document.getElementById('restart-message').innerHTML = 
                '<i class="bi bi-check-circle text-success"></i> Service restarted successfully!';
            
            // 等待1秒后刷新显示
            setTimeout(async () => {
                this.hideRestartProgress();
                await this.updateModeDisplay();
                
                // 如果有 WebSocket 连接，重新连接
                if (typeof connectWebSocket === 'function') {
                    connectWebSocket();
                }
                
                // 通知其他组件刷新
                if (typeof ModelManager !== 'undefined' && ModelManager.loadModels) {
                    ModelManager.loadModels();
                }
                
                // 显示成功消息
                this.showSuccess('Mode switched successfully! Service has been restarted.');
            }, 1000);
        },
        
        // 重启超时
        onRestartTimeout() {
            this.hideRestartProgress();
            this.showError('Service restart timeout. Please check the service manually.');
        },
        
        // 显示/隐藏各种状态
        showLoading(message) {
            document.getElementById('local-mode-btn').disabled = true;
            document.getElementById('api-mode-btn').disabled = true;
        },
        
        hideLoading() {
            document.getElementById('local-mode-btn').disabled = false;
            document.getElementById('api-mode-btn').disabled = false;
        },
        
        showRestartProgress() {
            document.getElementById('restart-progress').style.display = 'block';
            document.getElementById('local-mode-btn').disabled = true;
            document.getElementById('api-mode-btn').disabled = true;
        },
        
        hideRestartProgress() {
            document.getElementById('restart-progress').style.display = 'none';
            document.getElementById('restart-progress-bar').style.width = '0%';
            document.getElementById('local-mode-btn').disabled = false;
            document.getElementById('api-mode-btn').disabled = false;
        },
        
        showError(message) {
            document.getElementById('mode-error-text').textContent = message;
            document.getElementById('mode-error-message').style.display = 'block';
        },
        
        hideError() {
            document.getElementById('mode-error-message').style.display = 'none';
        },
        
        showSuccess(message) {
            // 可以使用现有的通知系统或创建临时提示
            if (typeof showNotification === 'function') {
                showNotification(message, 'success');
            } else {
                alert(message);
            }
        }
    };

    // 全局函数供按钮调用
    async function switchMode(mode) {
        await ModeSwitcher.switchMode(mode);
    }

    // 初始化模式切换器
    document.addEventListener('DOMContentLoaded', () => {
        // 延迟初始化，确保其他组件已加载
        setTimeout(() => {
            ModeSwitcher.init();
        }, 1000);
    });