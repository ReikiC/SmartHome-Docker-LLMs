/**
 * Enhanced Dynamic Model Manager for Smart Home Assistant
 * 支持配置文件自动生成和管理的模型切换功能
 * 
 * 核心功能：
 * 1. 获取可用模型列表
 * 2. 动态切换当前模型
 * 3. 配置文件自动生成和状态显示
 * 4. 模型性能测试
 * 5. 实时状态监控
 */

// 全局模型管理状态
const ModelManager = {
    currentModel: '',
    availableModels: [],
    modelInfo: {},
    switchInProgress: false,
    downloadInProgress: false,
    lastUpdateTime: 0,
    updateInterval: 30000, // 30秒更新间隔
    configStatus: null,
    
    // UI元素引用
    elements: {
        currentModelBadge: null,
        modelSelector: null,
        switchButton: null,
        refreshButton: null,
        downloadButton: null,
        downloadInput: null,
        testButton: null,
        statusOutput: null,
        modelInfo: null,
        responseTimeBadge: null,
        modelSizeBadge: null,
        modelsCountBadge: null,
        testResult: null,
        chatCurrentModel: null,
        configStatusIndicator: null,
        configDetails: null,
        saveConfigButton: null
    },
    
    // 初始化
    init() {
        console.log('🤖 Initializing Enhanced Dynamic Model Manager...');
        this.bindElements();
        this.bindEvents();
        this.loadModels();
        this.startPeriodicUpdate();
        console.log('✅ Enhanced Model Manager initialized');
    },
    
    // 绑定DOM元素
    bindElements() {
        this.elements = {
            currentModelBadge: document.getElementById('current-model-badge'),
            modelSelector: document.getElementById('model-selector'),
            switchButton: document.getElementById('switch-model-btn'),
            refreshButton: document.getElementById('refresh-models-btn'),
            downloadButton: document.getElementById('download-model-btn'),
            downloadInput: document.getElementById('model-download-input'),
            testButton: document.getElementById('test-current-model'),
            statusOutput: document.getElementById('model-status-output'),
            modelInfo: document.getElementById('model-info-display'),
            responseTimeBadge: document.getElementById('response-time-badge'),
            modelSizeBadge: document.getElementById('model-size-badge'),
            modelsCountBadge: document.getElementById('models-count-badge'),
            testResult: document.getElementById('test-result'),
            chatCurrentModel: document.getElementById('chat-current-model'),
            configStatusIndicator: document.getElementById('config-status-indicator'),
            configDetails: document.getElementById('config-details'),
            saveConfigButton: document.getElementById('save-config-btn')
        };
        
        console.log('🔗 UI elements bound successfully');
    },
    
    // 绑定事件
    bindEvents() {
        // 切换模型按钮
        if (this.elements.switchButton) {
            this.elements.switchButton.addEventListener('click', () => {
                this.switchModel();
            });
        }
        
        // 刷新模型列表按钮
        if (this.elements.refreshButton) {
            this.elements.refreshButton.addEventListener('click', () => {
                this.refreshModels();
            });
        }
        
        // 下载模型按钮
        if (this.elements.downloadButton) {
            this.elements.downloadButton.addEventListener('click', () => {
                this.downloadModel();
            });
        }
        
        // 测试当前模型按钮
        if (this.elements.testButton) {
            this.elements.testButton.addEventListener('click', () => {
                this.testCurrentModel();
            });
        }
        
        // 手动保存配置按钮
        if (this.elements.saveConfigButton) {
            this.elements.saveConfigButton.addEventListener('click', () => {
                this.saveConfigManually();
            });
        }
        
        // 模型选择器变化
        if (this.elements.modelSelector) {
            this.elements.modelSelector.addEventListener('change', () => {
                this.onModelSelectorChange();
            });
        }
        
        console.log('📡 Event listeners attached successfully');
    },
    
    // 记录状态日志
    logStatus(message, type = 'info') {
        if (!this.elements.statusOutput) return;
        
        const timestamp = new Date().toLocaleTimeString();
        const cssClass = type === 'error' ? 'console-output error' : 
                        type === 'success' ? 'console-output success' : 'console-output';
        
        this.elements.statusOutput.innerHTML += `<div class="${cssClass}">[${timestamp}] ${message}</div>`;
        
        // 自动滚动到底部
        this.elements.statusOutput.scrollTop = this.elements.statusOutput.scrollHeight;
        
        // 限制日志条数，避免界面卡顿
        const logs = this.elements.statusOutput.querySelectorAll('div');
        if (logs.length > 50) {
            for (let i = 0; i < 10; i++) {
                if (logs[i]) logs[i].remove();
            }
        }
        
        console.log(`[ModelManager] ${message}`);
    },
    
    // 加载可用模型列表 - 增强版本
    async loadModels() {
        try {
            this.logStatus('🔍 正在获取可用模型列表和配置状态...');
            
            const response = await fetch(`${API_URLS.coordinator}/models`);
            const data = await response.json();
            
            if (response.ok) {
                this.availableModels = data.available_models || [];
                this.currentModel = data.current_model || '';
                this.modelInfo = {};
                
                // 构建模型信息映射
                this.availableModels.forEach(model => {
                    this.modelInfo[model.name] = model;
                });
                
                this.updateUI(data);
                this.updateModelSelector();
                
                this.logStatus(`✅ 成功加载 ${this.availableModels.length} 个模型`);
                console.log('📋 Available models:', this.availableModels.map(m => m.name));
                
                // 🔥 新增：处理配置文件信息
                if (data.config_file_info) {
                    const configInfo = data.config_file_info;
                    this.configStatus = configInfo;
                    
                    this.logStatus(`📁 配置文件状态: ${configInfo.exists ? '已存在' : '不存在'}`);
                    
                    if (configInfo.exists) {
                        this.logStatus(`📍 配置路径: ${configInfo.path}`);
                        this.logStatus(`📊 文件大小: ${configInfo.size_bytes} 字节`);
                        
                        if (configInfo.last_modified) {
                            this.logStatus(`⏰ 最后修改: ${configInfo.last_modified}`);
                        }
                    }
                    
                    // 更新配置状态UI
                    this.updateConfigStatusUI(configInfo);
                }
                
                this.lastUpdateTime = Date.now();
                
            } else {
                throw new Error(data.error || 'Failed to load models');
            }
            
        } catch (error) {
            console.error('❌ Error loading models:', error);
            this.logStatus(`❌ 加载模型失败: ${error.message}`, 'error');
        }
    },
    
    // 切换模型 - 增强版本，支持配置文件状态显示
    async switchModel() {
        if (!this.elements.modelSelector) return;
        
        const selectedModel = this.elements.modelSelector.value;
        if (!selectedModel) {
            alert('请选择要切换的模型');
            return;
        }
        
        if (selectedModel === this.currentModel) {
            alert('该模型已经是当前使用的模型');
            return;
        }
        
        if (this.switchInProgress) {
            alert('模型切换正在进行中，请稍候');
            return;
        }
        
        this.switchInProgress = true;
        this.updateSwitchButtonState(true);
        
        try {
            this.logStatus(`🔄 正在切换到模型: ${selectedModel}...`);
            
            const startTime = Date.now();
            
            const response = await fetch(`${API_URLS.coordinator}/models/switch`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model_name: selectedModel })
            });
            
            const data = await response.json();
            const switchTime = Date.now() - startTime;
            
            if (response.ok && data.success) {
                this.currentModel = selectedModel;
                
                this.logStatus(`✅ 成功切换到 ${selectedModel} (耗时: ${switchTime}ms)`, 'success');
                
                // 🔥 新增：显示配置文件状态
                if (data.config_file_info) {
                    const configInfo = data.config_file_info;
                    
                    if (configInfo.config_updated) {
                        this.logStatus(`💾 配置文件已自动生成: ${configInfo.config_file_path}`, 'success');
                        
                        // 显示配置文件详细信息
                        if (configInfo.after_switch) {
                            const afterConfig = configInfo.after_switch;
                            this.logStatus(`📁 配置文件大小: ${afterConfig.config_size_bytes} 字节`);
                            
                            if (afterConfig.config_modified) {
                                this.logStatus(`⏰ 更新时间: ${afterConfig.config_modified}`);
                            }
                            
                            // 更新配置状态
                            this.configStatus = afterConfig;
                            this.updateConfigStatusUI(afterConfig);
                        }
                    } else {
                        this.logStatus(`⚠️ 配置文件生成失败`, 'error');
                    }
                }
                
                // 显示模型测试结果
                if (data.test_result) {
                    const testResult = data.test_result;
                    this.logStatus(`📊 模型测试: ${testResult.success ? '✅ 通过' : '❌ 失败'}`);
                    
                    if (testResult.eval_count) {
                        const processingTime = Math.round(testResult.eval_duration / 1000000);
                        this.logStatus(`⚡ 性能: ${testResult.eval_count} tokens, ${processingTime}ms`);
                        
                        // 更新性能指标
                        if (this.elements.responseTimeBadge) {
                            this.elements.responseTimeBadge.textContent = `${processingTime} ms`;
                        }
                    }
                }
                
                // 刷新界面
                await this.loadModels();
                
                // 通知其他组件模型已切换
                this.notifyModelSwitch(selectedModel);
                
                // 🔥 新增：检查并显示配置文件状态
                await this.checkConfigFileStatus();
                
            } else {
                throw new Error(data.error || 'Unknown error during model switch');
            }
            
        } catch (error) {
            console.error('❌ Model switch failed:', error);
            this.logStatus(`❌ 模型切换失败: ${error.message}`, 'error');
        } finally {
            this.switchInProgress = false;
            this.updateSwitchButtonState(false);
        }
    },
    
    // 🔥 新增：检查配置文件状态
    async checkConfigFileStatus() {
        try {
            const response = await fetch(`${API_URLS.coordinator}/models/config/status`);
            const data = await response.json();
            
            if (response.ok && data.success) {
                const configStatus = data.config_status;
                
                this.logStatus(`📋 配置文件状态检查:`);
                this.logStatus(`  📁 文件存在: ${configStatus.config_exists ? '✅' : '❌'}`);
                this.logStatus(`  📍 路径: ${configStatus.config_file_path}`);
                this.logStatus(`  📊 大小: ${configStatus.config_size_bytes} 字节`);
                this.logStatus(`  🔢 模型数量: ${configStatus.total_available_models}`);
                
                if (configStatus.config_modified) {
                    this.logStatus(`  ⏰ 修改时间: ${configStatus.config_modified}`);
                }
                
                // 更新UI中的配置状态指示器
                this.updateConfigStatusUI(configStatus);
                
            } else {
                this.logStatus(`⚠️ 无法获取配置文件状态: ${data.error}`, 'error');
            }
            
        } catch (error) {
            console.error('❌ Error checking config status:', error);
            this.logStatus(`❌ 配置状态检查失败: ${error.message}`, 'error');
        }
    },
    
    // 🔥 新增：更新配置状态UI
    updateConfigStatusUI(configStatus) {
        // 更新配置状态指示器
        if (this.elements.configStatusIndicator) {
            if (configStatus.config_exists) {
                this.elements.configStatusIndicator.innerHTML = `
                    <span class="badge bg-success">
                        <i class="bi bi-check-circle"></i> 配置已保存
                    </span>
                `;
                this.elements.configStatusIndicator.title = `配置文件: ${configStatus.config_file_path}`;
            } else {
                this.elements.configStatusIndicator.innerHTML = `
                    <span class="badge bg-warning">
                        <i class="bi bi-exclamation-triangle"></i> 配置未保存
                    </span>
                `;
            }
        }
        
        // 更新配置详细信息面板
        if (this.elements.configDetails) {
            this.elements.configDetails.innerHTML = `
                <div class="small text-muted">
                    <div><strong>配置文件:</strong> ${configStatus.config_exists ? '已存在' : '不存在'}</div>
                    <div><strong>路径:</strong> <code>${configStatus.config_file_path}</code></div>
                    <div><strong>大小:</strong> ${configStatus.config_size_bytes} 字节</div>
                    ${configStatus.config_modified ? `<div><strong>修改时间:</strong> ${configStatus.config_modified}</div>` : ''}
                </div>
            `;
        }
        
        // 保存配置状态到实例
        this.configStatus = configStatus;
    },
    
    // 🔥 新增：手动保存配置功能
    async saveConfigManually() {
        try {
            this.logStatus('💾 正在手动保存配置...');
            
            const response = await fetch(`${API_URLS.coordinator}/models/config/save`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                this.logStatus('✅ 配置已手动保存', 'success');
                
                if (data.config_info) {
                    this.updateConfigStatusUI(data.config_info);
                }
                
                // 刷新配置状态
                await this.checkConfigFileStatus();
            } else {
                throw new Error(data.error || 'Failed to save config');
            }
            
        } catch (error) {
            console.error('❌ Error saving config manually:', error);
            this.logStatus(`❌ 手动保存配置失败: ${error.message}`, 'error');
        }
    },
    
    // 刷新模型列表
    async refreshModels() {
        if (this.elements.refreshButton) {
            this.elements.refreshButton.disabled = true;
            this.elements.refreshButton.innerHTML = '<i class="bi bi-arrow-clockwise"></i> 刷新中...';
        }
        
        try {
            await this.loadModels();
        } finally {
            if (this.elements.refreshButton) {
                this.elements.refreshButton.disabled = false;
                this.elements.refreshButton.innerHTML = '<i class="bi bi-arrow-clockwise"></i> 刷新模型列表';
            }
        }
    },
    
    // 下载新模型
    async downloadModel() {
        if (!this.elements.downloadInput) return;
        
        const modelName = this.elements.downloadInput.value.trim();
        if (!modelName) {
            alert('请输入要下载的模型名称');
            return;
        }
        
        if (this.downloadInProgress) {
            alert('模型下载正在进行中，请稍候');
            return;
        }
        
        this.downloadInProgress = true;
        this.updateDownloadButtonState(true);
        
        try {
            this.logStatus(`📥 开始下载模型: ${modelName}...`);
            
            const response = await fetch(`${API_URLS.coordinator}/models/pull`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model_name: modelName })
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                this.logStatus(`✅ 模型 ${modelName} 下载成功`, 'success');
                
                // 下载完成后刷新模型列表
                await this.loadModels();
                
                // 清空输入框
                this.elements.downloadInput.value = '';
                
            } else {
                throw new Error(data.error || 'Download failed');
            }
            
        } catch (error) {
            console.error('❌ Model download failed:', error);
            this.logStatus(`❌ 模型下载失败: ${error.message}`, 'error');
        } finally {
            this.downloadInProgress = false;
            this.updateDownloadButtonState(false);
        }
    },
    
    // 测试当前模型
    async testCurrentModel() {
        if (!this.currentModel) {
            alert('没有当前模型可供测试');
            return;
        }
        
        try {
            this.logStatus(`🧪 正在测试模型: ${this.currentModel}...`);
            
            const startTime = Date.now();
            
            const response = await fetch(`${API_URLS.coordinator}/models/test`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model_name: this.currentModel })
            });
            
            const data = await response.json();
            const testTime = Date.now() - startTime;
            
            if (response.ok && data.success) {
                this.logStatus(`✅ 模型测试通过 (耗时: ${testTime}ms)`, 'success');
                
                if (data.eval_count) {
                    const processingTime = Math.round(data.eval_duration / 1000000);
                    this.logStatus(`📊 性能指标: ${data.eval_count} tokens, ${processingTime}ms`);
                    
                    // 更新性能显示
                    if (this.elements.responseTimeBadge) {
                        this.elements.responseTimeBadge.textContent = `${processingTime} ms`;
                    }
                }
                
                if (this.elements.testResult) {
                    this.elements.testResult.innerHTML = `
                        <div class="alert alert-success">
                            <strong>测试通过!</strong><br>
                            响应时间: ${testTime}ms<br>
                            ${data.eval_count ? `处理速度: ${Math.round(data.eval_duration / 1000000)}ms` : ''}
                        </div>
                    `;
                }
                
            } else {
                throw new Error(data.error || 'Test failed');
            }
            
        } catch (error) {
            console.error('❌ Model test failed:', error);
            this.logStatus(`❌ 模型测试失败: ${error.message}`, 'error');
            
            if (this.elements.testResult) {
                this.elements.testResult.innerHTML = `
                    <div class="alert alert-danger">
                        <strong>测试失败!</strong><br>
                        错误: ${error.message}
                    </div>
                `;
            }
        }
    },
    
    // 更新UI
    updateUI(data) {
        // 更新当前模型显示
        if (this.elements.currentModelBadge) {
            this.elements.currentModelBadge.textContent = data.current_model || 'None';
        }
        
        if (this.elements.chatCurrentModel) {
            this.elements.chatCurrentModel.textContent = data.current_model || 'None';
        }
        
        // 更新模型计数
        if (this.elements.modelsCountBadge) {
            this.elements.modelsCountBadge.textContent = data.total_models || 0;
        }
        
        // 更新当前模型大小
        const currentModelData = data.available_models ? 
            data.available_models.find(m => m.is_current) : null;
        
        if (currentModelData) {
            if (this.elements.modelSizeBadge) {
                this.elements.modelSizeBadge.textContent = `${currentModelData.size_mb} MB`;
            }
        }
    },
    
    // 更新模型选择器
    updateModelSelector() {
        if (!this.elements.modelSelector) return;
        
        if (this.availableModels.length === 0) {
            this.elements.modelSelector.innerHTML = '<option value="">暂无可用模型</option>';
            if (this.elements.switchButton) {
                this.elements.switchButton.disabled = true;
            }
            return;
        }
        
        // 添加默认选项
        this.elements.modelSelector.innerHTML = '<option value="">选择模型...</option>';
        
        // 添加模型选项
        this.availableModels.forEach(model => {
            const option = document.createElement('option');
            option.value = model.name;
            option.textContent = `${model.name} (${model.size_mb} MB)`;
            
            if (model.is_current) {
                option.textContent += ' [当前使用]';
                option.style.fontWeight = 'bold';
                option.style.color = '#0d6efd';
            }
            
            this.elements.modelSelector.appendChild(option);
        });
        
        if (this.elements.switchButton) {
            this.elements.switchButton.disabled = false;
        }
    },
    
    // 模型选择器变化处理
    onModelSelectorChange() {
        if (!this.elements.modelSelector || !this.elements.modelInfo) return;
        
        const selectedModel = this.elements.modelSelector.value;
        
        if (!selectedModel) {
            this.elements.modelInfo.innerHTML = '<small class="text-muted">选择模型以查看详细信息</small>';
            return;
        }
        
        const modelData = this.modelInfo[selectedModel];
        if (modelData) {
            const modifiedDate = modelData.modified_at ? 
                new Date(modelData.modified_at).toLocaleDateString('zh-CN') : '未知';
            
            this.elements.modelInfo.innerHTML = `
                <strong>${modelData.name}</strong><br>
                <small class="text-muted">
                    大小: ${modelData.size_mb} MB<br>
                    修改时间: ${modifiedDate}<br>
                    状态: ${modelData.is_current ? '<span class="text-primary">当前使用</span>' : '可切换'}
                </small>
            `;
        }
    },
    
    // 更新切换按钮状态
    updateSwitchButtonState(isLoading) {
        if (!this.elements.switchButton) return;
        
        if (isLoading) {
            this.elements.switchButton.disabled = true;
            this.elements.switchButton.innerHTML = '<i class="bi bi-arrow-repeat"></i> 切换中...';
        } else {
            this.elements.switchButton.disabled = false;
            this.elements.switchButton.innerHTML = '<i class="bi bi-arrow-left-right"></i> 切换模型';
        }
    },
    
    // 更新下载按钮状态
    updateDownloadButtonState(isLoading) {
        if (!this.elements.downloadButton) return;
        
        if (isLoading) {
            this.elements.downloadButton.disabled = true;
            this.elements.downloadButton.innerHTML = '<i class="bi bi-download"></i> 下载中...';
        } else {
            this.elements.downloadButton.disabled = false;
            this.elements.downloadButton.innerHTML = '<i class="bi bi-download"></i> 下载模型';
        }
    },
    
    // 通知模型切换
    notifyModelSwitch(newModel) {
        // 触发自定义事件
        const event = new CustomEvent('modelSwitched', {
            detail: {
                newModel: newModel,
                oldModel: this.currentModel,
                timestamp: Date.now(),
                configStatus: this.configStatus
            }
        });
        document.dispatchEvent(event);
        
        // 如果有WebSocket连接，通知服务器
        if (typeof wsConnection !== 'undefined' && wsConnection && wsConnection.readyState === WebSocket.OPEN) {
            wsConnection.send(JSON.stringify({
                type: 'model_switch_notification',
                new_model: newModel,
                timestamp: Date.now()
            }));
        }
        
        console.log(`🔄 Model switched notification sent: ${newModel}`);
    },
    
    // 定期更新
    startPeriodicUpdate() {
        setInterval(() => {
            // 如果没有操作进行中且距离上次更新超过间隔时间，则自动更新
            if (!this.switchInProgress && !this.downloadInProgress) {
                const timeSinceUpdate = Date.now() - this.lastUpdateTime;
                if (timeSinceUpdate > this.updateInterval) {
                    this.loadModels();
                }
            }
        }, this.updateInterval);
    },
    
    // 获取当前模型信息
    getCurrentModel() {
        return this.currentModel;
    },
    
    // 获取可用模型列表
    getAvailableModels() {
        return this.availableModels;
    },
    
    // 检查模型是否可用
    isModelAvailable(modelName) {
        return this.availableModels.some(model => model.name === modelName);
    },
    
    // 获取模型详细信息
    getModelInfo(modelName) {
        return this.modelInfo[modelName] || null;
    },
    
    // 获取配置状态
    getConfigStatus() {
        return this.configStatus;
    },
    
    // 清除状态日志
    clearStatusLog() {
        if (this.elements.statusOutput) {
            this.elements.statusOutput.innerHTML = '<div class="console-output">状态日志已清除</div>';
        }
    }
};

// 全局快捷函数，方便其他模块调用
window.ModelManager = ModelManager;

// 快捷访问函数
window.getCurrentModel = () => ModelManager.getCurrentModel();
window.getAvailableModels = () => ModelManager.getAvailableModels();
window.getConfigStatus = () => ModelManager.getConfigStatus();
window.switchToModel = (modelName) => {
    if (ModelManager.elements.modelSelector) {
        ModelManager.elements.modelSelector.value = modelName;
        return ModelManager.switchModel();
    }
};

// 监听模型切换事件（其他模块可以使用）
document.addEventListener('modelSwitched', (event) => {
    console.log('🔔 Model switch event detected:', event.detail);
    
    // 更新聊天界面的模型显示
    const chatModelElements = document.querySelectorAll('[data-current-model]');
    chatModelElements.forEach(element => {
        element.textContent = event.detail.newModel;
    });
    
    // 显示配置状态变化
    if (event.detail.configStatus) {
        console.log('📁 Config status:', event.detail.configStatus);
    }
    
    // 可以在这里添加其他需要响应模型切换的逻辑
});

// DOM加载完成后自动初始化
document.addEventListener('DOMContentLoaded', () => {
    // 延迟初始化，确保其他模块已加载
    setTimeout(() => {
        ModelManager.init();
    }, 500);
});

// 调试函数 - 仅在开发模式下可用
if (typeof window.DEBUG !== 'undefined' && window.DEBUG) {
    window.debugModelManager = () => {
        console.log('🔧 Enhanced Model Manager Debug Info:');
        console.log('Current Model:', ModelManager.currentModel);
        console.log('Available Models:', ModelManager.availableModels);
        console.log('Model Info:', ModelManager.modelInfo);
        console.log('Config Status:', ModelManager.configStatus);
        console.log('Switch in Progress:', ModelManager.switchInProgress);
        console.log('Download in Progress:', ModelManager.downloadInProgress);
        console.log('Last Update Time:', new Date(ModelManager.lastUpdateTime).toLocaleString());
    };
}

// 错误恢复机制
window.addEventListener('beforeunload', () => {
    // 在页面卸载前清理定时器等资源
    if (ModelManager.updateTimer) {
        clearInterval(ModelManager.updateTimer);
    }
});

console.log('📦 Enhanced Dynamic Model Manager module loaded successfully');