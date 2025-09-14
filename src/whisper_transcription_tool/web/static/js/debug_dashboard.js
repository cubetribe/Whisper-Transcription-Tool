/**
 * Debug Dashboard JavaScript
 * Handles real-time monitoring, metrics visualization, and debugging tools
 */

class DebugDashboard {
    constructor() {
        this.autoRefresh = true;
        this.refreshInterval = 30000; // 30 seconds
        this.refreshTimer = null;
        this.performanceChart = null;
        this.websocket = null;

        // Data storage
        this.metricsHistory = [];
        this.maxHistoryPoints = 50;

        // Chart colors
        this.chartColors = {
            cpu: '#ef4444',
            memory: '#3b82f6',
            disk: '#10b981'
        };

        // Bind methods
        this.updateMetrics = this.updateMetrics.bind(this);
        this.handleWebSocketMessage = this.handleWebSocketMessage.bind(this);
    }

    static init() {
        window.debugDashboard = new DebugDashboard();
        window.debugDashboard.initialize();
    }

    async initialize() {
        console.log('Initializing Debug Dashboard...');

        try {
            // Set up event listeners
            this.setupEventListeners();

            // Initialize WebSocket connection
            this.connectWebSocket();

            // Initialize chart
            this.initializeChart();

            // Load initial data
            await this.loadAllData();

            // Start auto-refresh if enabled
            this.startAutoRefresh();

            console.log('Debug Dashboard initialized successfully');
        } catch (error) {
            console.error('Failed to initialize Debug Dashboard:', error);
            this.showError('Failed to initialize dashboard. Please refresh the page.');
        }
    }

    setupEventListeners() {
        // Auto-refresh toggle
        const autoRefreshCheckbox = document.getElementById('auto-refresh');
        if (autoRefreshCheckbox) {
            autoRefreshCheckbox.addEventListener('change', (e) => {
                this.autoRefresh = e.target.checked;
                if (this.autoRefresh) {
                    this.startAutoRefresh();
                } else {
                    this.stopAutoRefresh();
                }
            });
        }

        // Refresh all button
        const refreshAllBtn = document.getElementById('refresh-all');
        if (refreshAllBtn) {
            refreshAllBtn.addEventListener('click', () => this.loadAllData());
        }

        // Tab navigation
        const tabButtons = document.querySelectorAll('.tab-button');
        tabButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const tabName = e.target.dataset.tab;
                this.switchTab(tabName);
            });
        });

        // Chart timerange selector
        const chartTimerange = document.getElementById('chart-timerange');
        if (chartTimerange) {
            chartTimerange.addEventListener('change', (e) => {
                this.updateChartTimerange(parseInt(e.target.value));
            });
        }

        // Clear alerts button
        const clearAlertsBtn = document.getElementById('clear-alerts');
        if (clearAlertsBtn) {
            clearAlertsBtn.addEventListener('click', () => this.clearAlerts());
        }

        // Log level filter
        const logLevelSelect = document.getElementById('log-level');
        if (logLevelSelect) {
            logLevelSelect.addEventListener('change', () => this.loadLogs());
        }

        // Refresh buttons
        document.getElementById('refresh-logs')?.addEventListener('click', () => this.loadLogs());
        document.getElementById('refresh-connections')?.addEventListener('click', () => this.loadConnectionDetails());
        document.getElementById('refresh-system-info')?.addEventListener('click', () => this.loadSystemInfo());

        // Test tools
        document.getElementById('test-recording')?.addEventListener('click', () => this.testRecordingSystem());
        document.getElementById('health-check')?.addEventListener('click', () => this.runHealthCheck());
        document.getElementById('benchmark')?.addEventListener('click', () => this.runBenchmark());
    }

    connectWebSocket() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.host;
            const wsUrl = `${protocol}//${host}/ws/debug?client_id=debug_dashboard`;

            this.websocket = new WebSocket(wsUrl);

            this.websocket.onopen = () => {
                console.log('Debug WebSocket connected');
                this.updateConnectionStatus(true);
            };

            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

            this.websocket.onclose = () => {
                console.log('Debug WebSocket disconnected');
                this.updateConnectionStatus(false);
                // Attempt reconnection after 5 seconds
                setTimeout(() => this.connectWebSocket(), 5000);
            };

            this.websocket.onerror = (error) => {
                console.error('Debug WebSocket error:', error);
                this.updateConnectionStatus(false);
            };

        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.updateConnectionStatus(false);
        }
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'metrics_update':
                this.updateMetricsFromWebSocket(data.data);
                break;
            case 'debug_info':
                console.log('Debug info received:', data.data);
                break;
            case 'ping':
                this.sendWebSocketMessage({ type: 'pong' });
                break;
            default:
                console.log('Unknown WebSocket message type:', data.type);
        }
    }

    sendWebSocketMessage(message) {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify(message));
        }
    }

    updateConnectionStatus(connected) {
        // Update connection indicator in header if it exists
        const indicator = document.querySelector('.connection-status');
        if (indicator) {
            indicator.className = `connection-status ${connected ? 'connected' : 'disconnected'}`;
            indicator.textContent = connected ? 'Connected' : 'Disconnected';
        }
    }

    initializeChart() {
        const ctx = document.getElementById('performance-chart');
        if (!ctx) return;

        this.performanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'CPU Usage (%)',
                        data: [],
                        borderColor: this.chartColors.cpu,
                        backgroundColor: this.chartColors.cpu + '20',
                        tension: 0.4,
                        fill: false
                    },
                    {
                        label: 'Memory Usage (%)',
                        data: [],
                        borderColor: this.chartColors.memory,
                        backgroundColor: this.chartColors.memory + '20',
                        tension: 0.4,
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    },
                    x: {
                        type: 'time',
                        time: {
                            unit: 'minute',
                            displayFormats: {
                                minute: 'HH:mm'
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + '%';
                            }
                        }
                    }
                },
                animation: {
                    duration: 750
                }
            }
        });
    }

    async loadAllData() {
        try {
            this.updateLastUpdateTime();

            // Load all dashboard data in parallel
            await Promise.all([
                this.loadSystemMetrics(),
                this.loadAudioStatus(),
                this.loadRecordingStatus(),
                this.loadWebSocketStatus(),
                this.loadPerformanceAlerts(),
                this.loadHealthStatus()
            ]);

            // Load tab-specific data for active tab
            const activeTab = document.querySelector('.tab-button.active')?.dataset.tab;
            if (activeTab) {
                await this.loadTabData(activeTab);
            }

        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showError('Failed to load dashboard data');
        }
    }

    async loadSystemMetrics() {
        try {
            const response = await fetch('/debug/api/system_metrics');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const result = await response.json();
            if (result.success) {
                this.updateSystemMetricsDisplay(result.data);
                this.addMetricsToHistory(result.data, result.timestamp);
                this.updateChart();
            }
        } catch (error) {
            console.error('Failed to load system metrics:', error);
            this.updateSystemStatus('error');
        }
    }

    async loadAudioStatus() {
        try {
            const response = await fetch('/debug/api/audio_status');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const result = await response.json();
            if (result.success) {
                this.updateAudioStatusDisplay(result.data);
            }
        } catch (error) {
            console.error('Failed to load audio status:', error);
            this.updateAudioStatus('error');
        }
    }

    async loadRecordingStatus() {
        try {
            const response = await fetch('/debug/api/recording_status');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const result = await response.json();
            if (result.success) {
                this.updateRecordingStatusDisplay(result.data);
            }
        } catch (error) {
            console.error('Failed to load recording status:', error);
            this.updateRecordingStatus('error');
        }
    }

    async loadWebSocketStatus() {
        try {
            const response = await fetch('/debug/api/websocket_status');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const result = await response.json();
            if (result.success) {
                this.updateWebSocketStatusDisplay(result.data);
            }
        } catch (error) {
            console.error('Failed to load WebSocket status:', error);
            this.updateWebSocketStatus('error');
        }
    }

    async loadPerformanceAlerts() {
        try {
            const response = await fetch('/debug/api/performance_alerts');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const result = await response.json();
            if (result.success) {
                this.updatePerformanceAlertsDisplay(result.data);
            }
        } catch (error) {
            console.error('Failed to load performance alerts:', error);
        }
    }

    async loadHealthStatus() {
        try {
            const response = await fetch('/debug/api/health_check');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const result = await response.json();
            this.updateHealthStatusDisplay(result);
        } catch (error) {
            console.error('Failed to load health status:', error);
            this.updateHealthStatusDisplay({ overall: 'error', error: error.message });
        }
    }

    updateSystemMetricsDisplay(data) {
        // Update CPU usage
        const cpuUsage = document.getElementById('cpu-usage');
        const cpuProgress = document.getElementById('cpu-progress');
        if (cpuUsage && cpuProgress) {
            cpuUsage.textContent = `${data.cpu_percent.toFixed(1)}%`;
            cpuProgress.style.width = `${data.cpu_percent}%`;
            cpuProgress.className = `metric-progress ${data.cpu_percent > 80 ? 'danger' : data.cpu_percent > 60 ? 'warning' : ''}`;
        }

        // Update Memory usage
        const memoryUsage = document.getElementById('memory-usage');
        const memoryProgress = document.getElementById('memory-progress');
        if (memoryUsage && memoryProgress) {
            memoryUsage.textContent = `${data.memory_percent.toFixed(1)}%`;
            memoryProgress.style.width = `${data.memory_percent}%`;
            memoryProgress.className = `metric-progress ${data.memory_percent > 85 ? 'danger' : data.memory_percent > 70 ? 'warning' : ''}`;
        }

        // Update Disk free space
        const diskFree = document.getElementById('disk-free');
        if (diskFree) {
            diskFree.textContent = `${data.disk_free_gb.toFixed(1)} GB`;
        }

        // Update Uptime
        const uptime = document.getElementById('uptime');
        if (uptime) {
            uptime.textContent = this.formatUptime(data.uptime_seconds);
        }

        // Update system status indicator
        const cpuOk = data.cpu_percent < 90;
        const memoryOk = data.memory_percent < 90;
        const diskOk = data.disk_free_gb > 0.5;

        if (cpuOk && memoryOk && diskOk) {
            this.updateSystemStatus('healthy');
        } else if (!cpuOk || !memoryOk || !diskOk) {
            this.updateSystemStatus('warning');
        } else {
            this.updateSystemStatus('error');
        }
    }

    updateAudioStatusDisplay(data) {
        const blackholeStatus = document.getElementById('blackhole-status');
        const inputDevices = document.getElementById('input-devices');
        const outputDevices = document.getElementById('output-devices');
        const defaultInput = document.getElementById('default-input');

        if (blackholeStatus) {
            blackholeStatus.textContent = data.blackhole_available ? 'Available' : 'Not Available';
            blackholeStatus.className = `metric-value ${data.blackhole_available ? 'status-healthy' : 'status-warning'}`;
        }

        if (inputDevices) {
            inputDevices.textContent = data.input_devices_count.toString();
        }

        if (outputDevices) {
            outputDevices.textContent = data.output_devices_count.toString();
        }

        if (defaultInput) {
            defaultInput.textContent = data.default_input || 'None';
        }

        // Update audio system status
        const audioHealthy = data.blackhole_available && data.input_devices_count > 0 && data.output_devices_count > 0;
        this.updateAudioStatus(audioHealthy ? 'healthy' : 'warning');
    }

    updateRecordingStatusDisplay(data) {
        const activeSessions = document.getElementById('active-sessions');
        const totalSessions = document.getElementById('total-sessions');
        const recordingInProgress = document.getElementById('recording-in-progress');
        const recordingsToday = document.getElementById('recordings-today');

        if (activeSessions) activeSessions.textContent = data.active_sessions.toString();
        if (totalSessions) totalSessions.textContent = data.total_sessions.toString();
        if (recordingInProgress) {
            recordingInProgress.textContent = data.recording_in_progress ? 'Yes' : 'No';
            recordingInProgress.className = `metric-value ${data.recording_in_progress ? 'status-warning' : 'status-healthy'}`;
        }
        if (recordingsToday) recordingsToday.textContent = data.recordings_today.toString();

        this.updateRecordingStatus('healthy');
    }

    updateWebSocketStatusDisplay(data) {
        const totalConnections = document.getElementById('total-connections');
        const recordingConnections = document.getElementById('recording-connections');
        const monitoringConnections = document.getElementById('monitoring-connections');
        const debugConnections = document.getElementById('debug-connections');

        if (totalConnections) totalConnections.textContent = data.total_connections.toString();
        if (recordingConnections) recordingConnections.textContent = data.recording_connections.toString();
        if (monitoringConnections) monitoringConnections.textContent = data.monitoring_connections.toString();
        if (debugConnections) debugConnections.textContent = data.debug_connections.toString();

        this.updateWebSocketStatus('healthy');
    }

    updatePerformanceAlertsDisplay(data) {
        const alertsContainer = document.getElementById('alerts-container');
        if (!alertsContainer) return;

        if (data.alerts.length === 0) {
            alertsContainer.innerHTML = '<div class="no-alerts">No performance alerts</div>';
        } else {
            const alertsHtml = data.alerts.map(alert => `
                <div class="alert-item ${alert.severity}">
                    <div class="alert-timestamp">${new Date(alert.timestamp).toLocaleString()}</div>
                    <div class="alert-message">${alert.message}</div>
                </div>
            `).join('');
            alertsContainer.innerHTML = alertsHtml;
        }
    }

    updateHealthStatusDisplay(data) {
        const healthIcon = document.querySelector('.health-icon');
        const healthStatus = document.getElementById('health-status');
        const healthDetails = document.getElementById('health-details');

        if (healthIcon) {
            healthIcon.className = `health-icon ${data.overall}`;
        }

        if (healthStatus) {
            healthStatus.textContent = data.overall.charAt(0).toUpperCase() + data.overall.slice(1);
            healthStatus.className = `health-status ${data.overall}`;
        }

        if (healthDetails && data.checks) {
            const checksCount = Object.keys(data.checks).length;
            const healthyCount = Object.values(data.checks).filter(check => check.status === 'healthy').length;
            healthDetails.textContent = `${healthyCount}/${checksCount} systems healthy`;
        } else if (healthDetails && data.error) {
            healthDetails.textContent = `Error: ${data.error}`;
        }
    }

    updateSystemStatus(status) {
        this.updateStatusIndicator('system-status', status);
    }

    updateAudioStatus(status) {
        this.updateStatusIndicator('audio-status', status);
    }

    updateRecordingStatus(status) {
        this.updateStatusIndicator('recording-status', status);
    }

    updateWebSocketStatus(status) {
        this.updateStatusIndicator('websocket-status', status);
    }

    updateStatusIndicator(elementId, status) {
        const indicator = document.getElementById(elementId);
        if (indicator) {
            const icon = indicator.querySelector('i');
            if (icon) {
                icon.className = `fas fa-circle status-${status}`;
            }
        }
    }

    addMetricsToHistory(data, timestamp) {
        this.metricsHistory.push({
            timestamp: new Date(timestamp),
            cpu: data.cpu_percent,
            memory: data.memory_percent,
            disk: data.disk_free_gb
        });

        // Keep only the last N points
        if (this.metricsHistory.length > this.maxHistoryPoints) {
            this.metricsHistory = this.metricsHistory.slice(-this.maxHistoryPoints);
        }
    }

    updateMetricsFromWebSocket(data) {
        this.updateSystemMetricsDisplay(data);
        this.addMetricsToHistory(data, new Date().toISOString());
        this.updateChart();
    }

    updateChart() {
        if (!this.performanceChart || this.metricsHistory.length === 0) return;

        const labels = this.metricsHistory.map(item => item.timestamp);
        const cpuData = this.metricsHistory.map(item => item.cpu);
        const memoryData = this.metricsHistory.map(item => item.memory);

        this.performanceChart.data.labels = labels;
        this.performanceChart.data.datasets[0].data = cpuData;
        this.performanceChart.data.datasets[1].data = memoryData;

        this.performanceChart.update('none');
    }

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');

        // Load tab-specific data
        this.loadTabData(tabName);
    }

    async loadTabData(tabName) {
        switch (tabName) {
            case 'logs':
                await this.loadLogs();
                break;
            case 'connections':
                await this.loadConnectionDetails();
                break;
            case 'system-info':
                await this.loadSystemInfo();
                break;
        }
    }

    async loadLogs() {
        const container = document.getElementById('logs-container');
        const levelSelect = document.getElementById('log-level');
        if (!container) return;

        try {
            container.innerHTML = '<div class="loading">Loading logs...</div>';

            const level = levelSelect?.value || 'INFO';
            const response = await fetch(`/debug/api/log_entries?level=${level}&limit=100`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const result = await response.json();
            if (result.success) {
                if (result.data.logs.length === 0) {
                    container.innerHTML = '<div class="no-logs">No log entries found</div>';
                } else {
                    const logsHtml = result.data.logs.map(log => `
                        <div class="log-entry">
                            <div class="log-timestamp">${new Date(log.timestamp).toLocaleString()}</div>
                            <span class="log-level ${log.level}">${log.level}</span>
                            <span class="log-module">[${log.module}]</span>
                            <div class="log-message">${log.message}</div>
                        </div>
                    `).join('');
                    container.innerHTML = logsHtml;
                }
            } else {
                container.innerHTML = '<div class="error">Failed to load logs</div>';
            }
        } catch (error) {
            console.error('Failed to load logs:', error);
            container.innerHTML = '<div class="error">Error loading logs</div>';
        }
    }

    async loadConnectionDetails() {
        const container = document.getElementById('connections-container');
        if (!container) return;

        try {
            container.innerHTML = '<div class="loading">Loading connection details...</div>';

            const response = await fetch('/debug/api/websocket_status');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const result = await response.json();
            if (result.success) {
                const connections = result.data.connection_details || [];
                if (connections.length === 0) {
                    container.innerHTML = '<div class="no-connections">No active connections</div>';
                } else {
                    const connectionsHtml = connections.map(conn => `
                        <div class="connection-item">
                            <div class="connection-header">
                                <div class="connection-id">${conn.client_id}</div>
                                <div class="connection-type">${conn.type}</div>
                            </div>
                            <div class="connection-details">
                                <div class="connection-detail">
                                    <span class="label">Connected:</span>
                                    <span class="value">${new Date(conn.connected_at).toLocaleString()}</span>
                                </div>
                                <div class="connection-detail">
                                    <span class="label">Messages:</span>
                                    <span class="value">${conn.message_count}</span>
                                </div>
                            </div>
                        </div>
                    `).join('');
                    container.innerHTML = connectionsHtml;
                }
            } else {
                container.innerHTML = '<div class="error">Failed to load connection details</div>';
            }
        } catch (error) {
            console.error('Failed to load connection details:', error);
            container.innerHTML = '<div class="error">Error loading connection details</div>';
        }
    }

    async loadSystemInfo() {
        const container = document.getElementById('system-info-container');
        if (!container) return;

        try {
            container.innerHTML = '<div class="loading">Loading system information...</div>';

            const response = await fetch('/debug/api/system_info');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const result = await response.json();
            if (result.success) {
                const data = result.data;
                const systemInfoHtml = `
                    <div class="info-section">
                        <h4>System Information</h4>
                        <div class="info-grid">
                            <div class="info-item">
                                <span class="info-label">Platform:</span>
                                <span class="info-value">${data.system.platform}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Platform Version:</span>
                                <span class="info-value">${data.system.platform_version}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Architecture:</span>
                                <span class="info-value">${data.system.architecture}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Python Version:</span>
                                <span class="info-value">${data.system.python_version}</span>
                            </div>
                        </div>
                    </div>
                    <div class="info-section">
                        <h4>Process Information</h4>
                        <div class="info-grid">
                            <div class="info-item">
                                <span class="info-label">PID:</span>
                                <span class="info-value">${data.process.pid}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">CPU Usage:</span>
                                <span class="info-value">${data.process.cpu_percent.toFixed(1)}%</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Memory RSS:</span>
                                <span class="info-value">${(data.process.memory_info.rss / 1024 / 1024).toFixed(1)} MB</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Threads:</span>
                                <span class="info-value">${data.process.num_threads}</span>
                            </div>
                        </div>
                    </div>
                    <div class="info-section">
                        <h4>Audio System</h4>
                        <div class="info-grid">
                            <div class="info-item">
                                <span class="info-label">BlackHole:</span>
                                <span class="info-value">${data.audio.blackhole_available ? 'Available' : 'Not Available'}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Input Devices:</span>
                                <span class="info-value">${data.audio.input_devices_count}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Output Devices:</span>
                                <span class="info-value">${data.audio.output_devices_count}</span>
                            </div>
                        </div>
                    </div>
                `;
                container.innerHTML = systemInfoHtml;
            } else {
                container.innerHTML = '<div class="error">Failed to load system information</div>';
            }
        } catch (error) {
            console.error('Failed to load system info:', error);
            container.innerHTML = '<div class="error">Error loading system information</div>';
        }
    }

    async clearAlerts() {
        try {
            const response = await fetch('/debug/api/clear_alerts', { method: 'POST' });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const result = await response.json();
            if (result.success) {
                await this.loadPerformanceAlerts();
                this.showSuccess('Performance alerts cleared');
            } else {
                this.showError('Failed to clear alerts');
            }
        } catch (error) {
            console.error('Failed to clear alerts:', error);
            this.showError('Error clearing alerts');
        }
    }

    async testRecordingSystem() {
        const button = document.getElementById('test-recording');
        const resultDiv = document.getElementById('test-recording-result');

        if (!button || !resultDiv) return;

        try {
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
            resultDiv.style.display = 'none';

            const response = await fetch('/debug/api/test_recording', { method: 'POST' });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const result = await response.json();
            if (result.success) {
                const allPassed = result.data.overall_result;
                resultDiv.className = `test-result ${allPassed ? 'success' : 'error'}`;
                resultDiv.innerHTML = `
                    <strong>Test Result: ${allPassed ? 'PASSED' : 'FAILED'}</strong><br>
                    Audio Devices: ${result.data.test_results.audio_devices?.success ? 'OK' : 'FAIL'}<br>
                    WebSocket: ${result.data.test_results.websocket_connection?.success ? 'OK' : 'FAIL'}<br>
                    API Endpoints: ${result.data.test_results.api_endpoints?.success ? 'OK' : 'FAIL'}
                `;
            } else {
                resultDiv.className = 'test-result error';
                resultDiv.textContent = 'Test failed: ' + (result.error || 'Unknown error');
            }

            resultDiv.style.display = 'block';

        } catch (error) {
            console.error('Test failed:', error);
            resultDiv.className = 'test-result error';
            resultDiv.textContent = 'Error running test: ' + error.message;
            resultDiv.style.display = 'block';
        } finally {
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-play"></i> Run Test';
        }
    }

    async runHealthCheck() {
        const button = document.getElementById('health-check');
        const resultDiv = document.getElementById('health-check-result');

        if (!button || !resultDiv) return;

        try {
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Checking...';
            resultDiv.style.display = 'none';

            const response = await fetch('/debug/api/health_check');
            const result = await response.json();

            const statusClass = result.overall === 'healthy' ? 'success' :
                               result.overall === 'warning' ? 'warning' : 'error';

            resultDiv.className = `test-result ${statusClass}`;
            resultDiv.innerHTML = `
                <strong>Health Status: ${result.overall.toUpperCase()}</strong><br>
                Timestamp: ${new Date(result.timestamp).toLocaleString()}<br>
                ${result.error ? `Error: ${result.error}` : 'All systems operational'}
            `;

            resultDiv.style.display = 'block';

        } catch (error) {
            console.error('Health check failed:', error);
            resultDiv.className = 'test-result error';
            resultDiv.textContent = 'Health check failed: ' + error.message;
            resultDiv.style.display = 'block';
        } finally {
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-heartbeat"></i> Check Health';
        }
    }

    async runBenchmark() {
        const button = document.getElementById('benchmark');
        const resultDiv = document.getElementById('benchmark-result');

        if (!button || !resultDiv) return;

        try {
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Benchmarking...';
            resultDiv.style.display = 'none';

            // Simulate benchmark by measuring API response times
            const startTime = performance.now();
            await Promise.all([
                fetch('/debug/api/system_metrics'),
                fetch('/debug/api/audio_status'),
                fetch('/debug/api/recording_status')
            ]);
            const endTime = performance.now();

            const responseTime = endTime - startTime;
            const performanceGrade = responseTime < 100 ? 'excellent' :
                                   responseTime < 500 ? 'good' :
                                   responseTime < 1000 ? 'fair' : 'poor';

            resultDiv.className = `test-result ${responseTime < 500 ? 'success' : 'warning'}`;
            resultDiv.innerHTML = `
                <strong>Performance Benchmark</strong><br>
                API Response Time: ${responseTime.toFixed(1)}ms<br>
                Performance Grade: ${performanceGrade.toUpperCase()}
            `;

            resultDiv.style.display = 'block';

        } catch (error) {
            console.error('Benchmark failed:', error);
            resultDiv.className = 'test-result error';
            resultDiv.textContent = 'Benchmark failed: ' + error.message;
            resultDiv.style.display = 'block';
        } finally {
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-stopwatch"></i> Run Benchmark';
        }
    }

    startAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }

        if (this.autoRefresh) {
            this.refreshTimer = setInterval(() => {
                this.updateMetrics();
            }, this.refreshInterval);
        }
    }

    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    }

    async updateMetrics() {
        try {
            await Promise.all([
                this.loadSystemMetrics(),
                this.loadAudioStatus(),
                this.loadRecordingStatus(),
                this.loadWebSocketStatus()
            ]);
            this.updateLastUpdateTime();
        } catch (error) {
            console.error('Error updating metrics:', error);
        }
    }

    updateLastUpdateTime() {
        const element = document.getElementById('last-update-time');
        if (element) {
            element.textContent = new Date().toLocaleTimeString();
        }
    }

    formatUptime(seconds) {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);

        if (days > 0) {
            return `${days}d ${hours}h ${minutes}m`;
        } else if (hours > 0) {
            return `${hours}h ${minutes}m`;
        } else {
            return `${minutes}m`;
        }
    }

    showError(message) {
        console.error(message);
        // Could implement toast notifications here
    }

    showSuccess(message) {
        console.log(message);
        // Could implement toast notifications here
    }

    updateChartTimerange(hours) {
        // In a real implementation, this would fetch historical data
        console.log(`Chart timerange changed to ${hours} hours`);
    }

    cleanup() {
        this.stopAutoRefresh();
        if (this.websocket) {
            this.websocket.close();
        }
        if (this.performanceChart) {
            this.performanceChart.destroy();
        }
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', DebugDashboard.init);
} else {
    DebugDashboard.init();
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.debugDashboard) {
        window.debugDashboard.cleanup();
    }
});