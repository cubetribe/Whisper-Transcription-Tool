/**
 * Phone Recording System - Frontend JavaScript
 * Handles WebSocket communication, UI updates, and user interactions
 */

class PhoneRecording {
    constructor() {
        this.websockets = {
            recording: null,
            monitoring: null,
            debug: null
        };

        this.state = {
            currentSession: null,
            isRecording: false,
            isPaused: false,
            devices: {
                input: [],
                output: []
            },
            systemStatus: {
                blackholeAvailable: false,
                deviceCount: 0
            }
        };

        this.audioLevelAnimationId = null;
        this.connectionRetryCount = 0;
        this.maxRetries = 5;
        this.retryDelay = 2000;

        // Bind methods to preserve context
        this.handleRecordingMessage = this.handleRecordingMessage.bind(this);
        this.handleMonitoringMessage = this.handleMonitoringMessage.bind(this);
        this.handleDebugMessage = this.handleDebugMessage.bind(this);
    }

    /**
     * Initialize the phone recording system
     */
    static init() {
        window.phoneRecording = new PhoneRecording();
        window.phoneRecording.initialize();
    }

    async initialize() {
        console.log('Initializing Phone Recording System...');

        try {
            // Set up event listeners
            this.setupEventListeners();

            // Load initial data
            await this.loadDevices();

            // Connect WebSockets
            await this.connectWebSockets();

            console.log('Phone Recording System initialized successfully');
        } catch (error) {
            console.error('Failed to initialize Phone Recording System:', error);
            this.showError('Failed to initialize the recording system. Please refresh the page.');
        }
    }

    /**
     * Set up DOM event listeners
     */
    setupEventListeners() {
        // Device management
        const refreshDevicesBtn = document.getElementById('refresh-devices');
        if (refreshDevicesBtn) {
            refreshDevicesBtn.addEventListener('click', () => this.loadDevices());
        }

        // Recording controls
        const startBtn = document.getElementById('start-recording');
        const pauseBtn = document.getElementById('pause-recording');
        const resumeBtn = document.getElementById('resume-recording');
        const stopBtn = document.getElementById('stop-recording');
        const processBtn = document.getElementById('process-recording');

        if (startBtn) startBtn.addEventListener('click', () => this.startRecording());
        if (pauseBtn) pauseBtn.addEventListener('click', () => this.pauseRecording());
        if (resumeBtn) resumeBtn.addEventListener('click', () => this.resumeRecording());
        if (stopBtn) stopBtn.addEventListener('click', () => this.stopRecording());
        if (processBtn) processBtn.addEventListener('click', () => this.processRecording());

        // Device selection
        const inputDevice = document.getElementById('input-device');
        const outputDevice = document.getElementById('output-device');

        if (inputDevice) {
            inputDevice.addEventListener('change', () => this.updateRecordingControls());
        }
        if (outputDevice) {
            outputDevice.addEventListener('change', () => this.updateRecordingControls());
        }

        // Window events
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });
    }

    /**
     * Connect to WebSocket endpoints
     */
    async connectWebSockets() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        const clientId = `web_${Date.now()}`;

        try {
            // Recording WebSocket
            await this.connectWebSocket(
                'recording',
                `${protocol}//${host}/ws/recording?client_id=${clientId}`,
                this.handleRecordingMessage
            );

            // Monitoring WebSocket
            await this.connectWebSocket(
                'monitoring',
                `${protocol}//${host}/ws/monitoring?client_id=${clientId}`,
                this.handleMonitoringMessage
            );

            // Debug WebSocket
            await this.connectWebSocket(
                'debug',
                `${protocol}//${host}/ws/debug?client_id=${clientId}`,
                this.handleDebugMessage
            );

            this.updateConnectionStatus(true);
            this.connectionRetryCount = 0;

        } catch (error) {
            console.error('WebSocket connection failed:', error);
            this.updateConnectionStatus(false);
            this.scheduleReconnect();
        }
    }

    /**
     * Connect individual WebSocket
     */
    async connectWebSocket(type, url, messageHandler) {
        return new Promise((resolve, reject) => {
            try {
                const ws = new WebSocket(url);

                ws.onopen = () => {
                    console.log(`${type} WebSocket connected`);
                    this.websockets[type] = ws;
                    resolve();
                };

                ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        messageHandler(data);
                        this.logWebSocketMessage(type, 'received', data);
                    } catch (error) {
                        console.error(`Error parsing ${type} WebSocket message:`, error);
                    }
                };

                ws.onclose = (event) => {
                    console.log(`${type} WebSocket closed:`, event.reason);
                    this.websockets[type] = null;
                    this.updateConnectionStatus(false);
                    this.scheduleReconnect();
                };

                ws.onerror = (error) => {
                    console.error(`${type} WebSocket error:`, error);
                    reject(error);
                };

            } catch (error) {
                reject(error);
            }
        });
    }

    /**
     * Handle recording WebSocket messages
     */
    handleRecordingMessage(data) {
        switch (data.type) {
            case 'initial_state':
                this.handleInitialState(data.recording_state);
                break;

            case 'recording_update':
                this.handleRecordingUpdate(data.data);
                break;

            case 'audio_levels':
                this.handleAudioLevels(data.data);
                break;

            case 'ping':
                this.sendWebSocketMessage('recording', { type: 'pong' });
                break;

            default:
                console.log('Unknown recording message type:', data.type);
        }
    }

    /**
     * Handle monitoring WebSocket messages
     */
    handleMonitoringMessage(data) {
        switch (data.type) {
            case 'system_state':
                this.handleSystemState(data.system_state);
                break;

            case 'system_update':
                this.handleSystemUpdate(data.data);
                break;

            case 'ping':
                this.sendWebSocketMessage('monitoring', { type: 'pong' });
                break;

            default:
                console.log('Unknown monitoring message type:', data.type);
        }
    }

    /**
     * Handle debug WebSocket messages
     */
    handleDebugMessage(data) {
        switch (data.type) {
            case 'debug_info':
                this.handleDebugInfo(data.data);
                break;

            case 'connection_stats':
                this.handleConnectionStats(data.data);
                break;

            case 'ping':
                this.sendWebSocketMessage('debug', { type: 'pong' });
                break;

            default:
                console.log('Unknown debug message type:', data.type);
        }
    }

    /**
     * Send message via WebSocket
     */
    sendWebSocketMessage(type, message) {
        const ws = this.websockets[type];
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify(message));
            this.logWebSocketMessage(type, 'sent', message);
        } else {
            console.warn(`${type} WebSocket not connected, cannot send message`);
        }
    }

    /**
     * Load audio devices from API
     */
    async loadDevices() {
        try {
            console.log('Loading audio devices...');
            const response = await fetch('/api/phone/devices');

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            this.state.devices.input = data.input_devices || [];
            this.state.devices.output = data.output_devices || [];
            this.state.systemStatus.blackholeAvailable = data.blackhole_found || false;
            this.state.systemStatus.deviceCount =
                this.state.devices.input.length + this.state.devices.output.length;

            this.updateDeviceSelections();
            this.updateSystemStatus();
            this.updateRecordingControls();

            console.log(`Loaded ${this.state.systemStatus.deviceCount} devices, BlackHole: ${this.state.systemStatus.blackholeAvailable}`);

        } catch (error) {
            console.error('Failed to load devices:', error);
            this.showError('Failed to load audio devices. Please check your system configuration.');
        }
    }

    /**
     * Update device selection dropdowns
     */
    updateDeviceSelections() {
        const inputSelect = document.getElementById('input-device');
        const outputSelect = document.getElementById('output-device');

        if (inputSelect) {
            inputSelect.innerHTML = this.state.devices.input.length === 0
                ? '<option value="">No input devices found</option>'
                : this.state.devices.input.map(device =>
                    `<option value="${device.id}" ${device.is_default ? 'selected' : ''}>
                        ${device.name} ${device.is_default ? '(Default)' : ''}
                    </option>`
                ).join('');
        }

        if (outputSelect) {
            outputSelect.innerHTML = this.state.devices.output.length === 0
                ? '<option value="">No output devices found</option>'
                : this.state.devices.output.map(device =>
                    `<option value="${device.id}" ${device.is_default ? 'selected' : ''}>
                        ${device.name} ${device.is_default ? '(Default)' : ''}
                    </option>`
                ).join('');
        }
    }

    /**
     * Update system status display
     */
    updateSystemStatus() {
        const blackholeStatus = document.getElementById('blackhole-status');
        const devicesCount = document.getElementById('devices-count');
        const recordingStatus = document.getElementById('recording-status');

        if (blackholeStatus) {
            blackholeStatus.textContent = this.state.systemStatus.blackholeAvailable ? 'Available' : 'Not Available';
            blackholeStatus.className = `value ${this.state.systemStatus.blackholeAvailable ? 'available' : 'unavailable'}`;
        }

        if (devicesCount) {
            devicesCount.textContent = `${this.state.systemStatus.deviceCount} devices found`;
            devicesCount.className = 'value';
        }

        if (recordingStatus) {
            let status = 'Idle';
            if (this.state.isRecording) {
                status = this.state.isPaused ? 'Paused' : 'Recording';
            }
            recordingStatus.textContent = status;
            recordingStatus.className = `value ${status.toLowerCase()}`;
        }
    }

    /**
     * Update recording control buttons
     */
    updateRecordingControls() {
        const inputDevice = document.getElementById('input-device')?.value;
        const outputDevice = document.getElementById('output-device')?.value;
        const hasDevices = inputDevice && outputDevice;
        const canRecord = hasDevices && this.state.systemStatus.blackholeAvailable && !this.state.isRecording;

        // Button references
        const startBtn = document.getElementById('start-recording');
        const pauseBtn = document.getElementById('pause-recording');
        const resumeBtn = document.getElementById('resume-recording');
        const stopBtn = document.getElementById('stop-recording');
        const processBtn = document.getElementById('process-recording');

        // Update button states
        if (startBtn) startBtn.disabled = !canRecord;
        if (pauseBtn) pauseBtn.disabled = !this.state.isRecording || this.state.isPaused;
        if (resumeBtn) resumeBtn.disabled = !this.state.isPaused;
        if (stopBtn) stopBtn.disabled = !this.state.isRecording;
        if (processBtn) processBtn.disabled = !this.state.currentSession || this.state.isRecording;
    }

    /**
     * Start recording
     */
    async startRecording() {
        try {
            const inputDevice = document.getElementById('input-device').value;
            const outputDevice = document.getElementById('output-device').value;
            const sampleRate = parseInt(document.getElementById('sample-rate').value);
            const maxDuration = parseInt(document.getElementById('max-duration').value) || 0;

            if (!inputDevice || !outputDevice) {
                throw new Error('Please select both input and output devices');
            }

            const requestData = {
                input_device_id: inputDevice,
                output_device_id: outputDevice,
                sample_rate: sampleRate,
                max_duration_sec: maxDuration
            };

            console.log('Starting recording with config:', requestData);

            const response = await fetch('/api/phone/recording/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                this.state.currentSession = data.session_id;
                this.state.isRecording = true;
                this.state.isPaused = false;

                this.showRecordingInfo();
                this.updateRecordingControls();
                this.updateSystemStatus();

                this.showSuccess('Recording started successfully');
                console.log('Recording started, session ID:', data.session_id);
            } else {
                throw new Error(data.error || 'Unknown error starting recording');
            }

        } catch (error) {
            console.error('Failed to start recording:', error);
            this.showError(`Failed to start recording: ${error.message}`);
        }
    }

    /**
     * Pause recording
     */
    async pauseRecording() {
        if (!this.state.currentSession) return;

        try {
            const response = await fetch(`/api/phone/recording/${this.state.currentSession}/pause`, {
                method: 'POST'
            });

            const data = await response.json();

            if (data.success) {
                this.state.isPaused = true;
                this.updateRecordingControls();
                this.updateSystemStatus();
                this.showSuccess('Recording paused');
            } else {
                throw new Error(data.message || 'Failed to pause recording');
            }

        } catch (error) {
            console.error('Failed to pause recording:', error);
            this.showError(`Failed to pause recording: ${error.message}`);
        }
    }

    /**
     * Resume recording
     */
    async resumeRecording() {
        if (!this.state.currentSession) return;

        try {
            const response = await fetch(`/api/phone/recording/${this.state.currentSession}/resume`, {
                method: 'POST'
            });

            const data = await response.json();

            if (data.success) {
                this.state.isPaused = false;
                this.updateRecordingControls();
                this.updateSystemStatus();
                this.showSuccess('Recording resumed');
            } else {
                throw new Error(data.message || 'Failed to resume recording');
            }

        } catch (error) {
            console.error('Failed to resume recording:', error);
            this.showError(`Failed to resume recording: ${error.message}`);
        }
    }

    /**
     * Stop recording
     */
    async stopRecording() {
        if (!this.state.currentSession) return;

        try {
            const response = await fetch(`/api/phone/recording/${this.state.currentSession}/stop`, {
                method: 'POST'
            });

            const data = await response.json();

            if (data.success) {
                this.state.isRecording = false;
                this.state.isPaused = false;

                // Show processing panel
                this.showProcessingPanel(data);

                this.updateRecordingControls();
                this.updateSystemStatus();
                this.showSuccess('Recording stopped successfully');
            } else {
                console.warn('Stop recording returned false, but handled gracefully');
                this.state.isRecording = false;
                this.state.isPaused = false;
                this.updateRecordingControls();
                this.updateSystemStatus();
            }

        } catch (error) {
            console.error('Failed to stop recording:', error);
            this.showError(`Failed to stop recording: ${error.message}`);
        }
    }

    /**
     * Process recording
     */
    async processRecording() {
        if (!this.state.currentSession) return;

        try {
            this.showProcessingStatus(true);

            const response = await fetch(`/api/phone/recording/${this.state.currentSession}/process`, {
                method: 'POST'
            });

            const data = await response.json();

            if (data.success) {
                this.showResults(data);
                this.showSuccess('Recording processed successfully');
            } else {
                throw new Error(data.error || 'Failed to process recording');
            }

        } catch (error) {
            console.error('Failed to process recording:', error);
            this.showError(`Failed to process recording: ${error.message}`);
        } finally {
            this.showProcessingStatus(false);
        }
    }

    /**
     * Handle initial state from WebSocket
     */
    handleInitialState(recordingState) {
        if (recordingState.session_id) {
            this.state.currentSession = recordingState.session_id;
            this.state.isRecording = recordingState.status !== 'idle';

            this.updateRecordingInfo(recordingState);
            this.showRecordingInfo();
        }

        this.updateRecordingControls();
        this.updateSystemStatus();
    }

    /**
     * Handle recording updates from WebSocket
     */
    handleRecordingUpdate(data) {
        console.log('Recording update:', data);

        if (data.session_id) {
            this.state.currentSession = data.session_id;
        }

        switch (data.status) {
            case 'recording':
                this.state.isRecording = true;
                this.state.isPaused = false;
                break;
            case 'paused':
                this.state.isPaused = true;
                break;
            case 'completed':
            case 'idle':
                this.state.isRecording = false;
                this.state.isPaused = false;
                break;
            case 'error':
                this.state.isRecording = false;
                this.state.isPaused = false;
                this.showError(data.error || 'Recording error occurred');
                break;
        }

        this.updateRecordingInfo(data);
        this.updateRecordingControls();
        this.updateSystemStatus();
    }

    /**
     * Handle audio level updates
     */
    handleAudioLevels(data) {
        const micLevel = Math.max(0, Math.min(100, data.microphone_level * 100));
        const systemLevel = Math.max(0, Math.min(100, data.system_level * 100));

        const micLevelBar = document.getElementById('mic-level');
        const systemLevelBar = document.getElementById('system-level');
        const micLevelValue = document.getElementById('mic-level-value');
        const systemLevelValue = document.getElementById('system-level-value');

        if (micLevelBar) micLevelBar.style.width = `${micLevel}%`;
        if (systemLevelBar) systemLevelBar.style.width = `${systemLevel}%`;
        if (micLevelValue) micLevelValue.textContent = `${Math.round(micLevel)}%`;
        if (systemLevelValue) systemLevelValue.textContent = `${Math.round(systemLevel)}%`;
    }

    /**
     * Handle system state updates
     */
    handleSystemState(data) {
        this.state.systemStatus = { ...this.state.systemStatus, ...data };
        this.updateSystemStatus();
    }

    /**
     * Handle system updates
     */
    handleSystemUpdate(data) {
        this.handleSystemState(data);
    }

    /**
     * Handle debug information
     */
    handleDebugInfo(data) {
        console.log('Debug info:', data);
    }

    /**
     * Handle connection statistics
     */
    handleConnectionStats(data) {
        const statsContainer = document.getElementById('connection-stats');
        if (statsContainer) {
            statsContainer.innerHTML = `
                <div>Total Connections: ${data.total_connections}</div>
                <div>Recording Connections: ${data.recording_connections}</div>
                <div>Monitoring Connections: ${data.monitoring_connections}</div>
                <div>Debug Connections: ${data.debug_connections}</div>
            `;
        }
    }

    /**
     * Update connection status indicator
     */
    updateConnectionStatus(isConnected) {
        const indicator = document.getElementById('connection-indicator');
        if (indicator) {
            indicator.className = `status-indicator ${isConnected ? 'online' : 'offline'}`;
            indicator.innerHTML = `<i class="fas fa-circle"></i> ${isConnected ? 'Online' : 'Offline'}`;
        }
    }

    /**
     * Show recording information panel
     */
    showRecordingInfo() {
        const panel = document.getElementById('recordingInfo');
        if (panel) {
            panel.style.display = 'block';
        }
    }

    /**
     * Update recording information display
     */
    updateRecordingInfo(data) {
        const sessionIdEl = document.getElementById('session-id');
        const durationEl = document.getElementById('recording-duration');
        const filesEl = document.getElementById('recording-files');

        if (sessionIdEl && data.session_id) {
            sessionIdEl.textContent = data.session_id;
        }

        if (durationEl && data.duration !== undefined) {
            const duration = typeof data.duration === 'number' ? data.duration : 0;
            const minutes = Math.floor(duration / 60);
            const seconds = Math.floor(duration % 60);
            durationEl.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }

        if (filesEl && data.files) {
            const fileList = Object.entries(data.files)
                .map(([type, path]) => `<div>${type}: ${path}</div>`)
                .join('');
            filesEl.innerHTML = fileList;
        }
    }

    /**
     * Show processing panel
     */
    showProcessingPanel(data) {
        const panel = document.getElementById('processingPanel');
        if (panel) {
            panel.style.display = 'block';
        }

        // Enable process button if we have recording data
        const processBtn = document.getElementById('process-recording');
        if (processBtn && data.files) {
            processBtn.disabled = false;
        }
    }

    /**
     * Show processing status
     */
    showProcessingStatus(isProcessing) {
        const progressText = document.getElementById('progress-text');
        const progressFill = document.getElementById('progress-fill');
        const processBtn = document.getElementById('process-recording');

        if (isProcessing) {
            if (progressText) progressText.textContent = 'Processing recording...';
            if (progressFill) progressFill.style.width = '50%';
            if (processBtn) processBtn.disabled = true;
        } else {
            if (progressText) progressText.textContent = 'Processing complete';
            if (progressFill) progressFill.style.width = '100%';
            if (processBtn) processBtn.disabled = false;
        }
    }

    /**
     * Show results panel
     */
    showResults(data) {
        const panel = document.getElementById('resultsPanel');
        if (panel) {
            panel.style.display = 'block';
        }

        // Display audio files
        const audioFilesEl = document.getElementById('audio-files');
        if (audioFilesEl && data.audio_files) {
            const audioList = data.audio_files.map(file =>
                `<div class="audio-file">
                    <strong>${file.type}:</strong> ${file.path}
                </div>`
            ).join('');
            audioFilesEl.innerHTML = audioList;
        }
    }

    /**
     * Log WebSocket messages for debugging
     */
    logWebSocketMessage(type, direction, data) {
        const logContainer = document.getElementById('websocket-log');
        if (logContainer) {
            const timestamp = new Date().toLocaleTimeString();
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            entry.innerHTML = `
                <div class="log-timestamp">${timestamp} [${type}] ${direction}</div>
                <div class="log-message">${JSON.stringify(data, null, 2)}</div>
            `;

            logContainer.appendChild(entry);
            logContainer.scrollTop = logContainer.scrollHeight;

            // Keep only last 50 entries
            while (logContainer.children.length > 50) {
                logContainer.removeChild(logContainer.firstChild);
            }
        }
    }

    /**
     * Schedule WebSocket reconnection
     */
    scheduleReconnect() {
        if (this.connectionRetryCount < this.maxRetries) {
            this.connectionRetryCount++;
            console.log(`Scheduling reconnection attempt ${this.connectionRetryCount}/${this.maxRetries} in ${this.retryDelay}ms`);

            setTimeout(() => {
                this.connectWebSockets();
            }, this.retryDelay);

            // Exponential backoff
            this.retryDelay = Math.min(this.retryDelay * 1.5, 30000);
        } else {
            console.error('Max reconnection attempts reached');
            this.showError('Connection lost. Please refresh the page to reconnect.');
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        this.showMessage(message, 'error');
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        this.showMessage(message, 'success');
    }

    /**
     * Show message with specified type
     */
    showMessage(message, type) {
        const container = document.getElementById(`${type}-messages`);
        if (container) {
            const messageEl = document.createElement('div');
            messageEl.className = `${type}-message`;
            messageEl.textContent = message;

            container.appendChild(messageEl);

            // Auto-remove after 5 seconds
            setTimeout(() => {
                if (messageEl.parentNode) {
                    messageEl.parentNode.removeChild(messageEl);
                }
            }, 5000);
        }

        console[type === 'error' ? 'error' : 'log'](message);
    }

    /**
     * Clean up resources
     */
    cleanup() {
        // Close WebSocket connections
        Object.values(this.websockets).forEach(ws => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.close();
            }
        });

        // Cancel animation frames
        if (this.audioLevelAnimationId) {
            cancelAnimationFrame(this.audioLevelAnimationId);
        }
    }
}

// Global functions for debug panel
function toggleDebugPanel() {
    const panel = document.getElementById('debugPanel');
    if (panel) {
        panel.classList.toggle('collapsed');
    }
}

function clearWebSocketLog() {
    const logContainer = document.getElementById('websocket-log');
    if (logContainer) {
        logContainer.innerHTML = '';
    }
}

function requestConnectionStats() {
    if (window.phoneRecording) {
        window.phoneRecording.sendWebSocketMessage('debug', { type: 'get_stats' });
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', PhoneRecording.init);
} else {
    PhoneRecording.init();
}