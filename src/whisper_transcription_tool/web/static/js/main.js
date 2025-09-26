/**
 * Main JavaScript file for Whisper Transcription Tool
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips, if any
    initTooltips();
    
    // Check for URL parameters
    handleUrlParameters();
    
    // Add event listeners for common elements
    addGlobalEventListeners();
});

/**
 * Initialize tooltips for elements with data-tooltip attribute
 */
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(element => {
        // Simple tooltip implementation could be added here
        // For now, we're using the title attribute
        if (element.dataset.tooltip) {
            element.title = element.dataset.tooltip;
        }
    });
}

/**
 * Handle URL parameters for page-specific functionality
 */
function handleUrlParameters() {
    const urlParams = new URLSearchParams(window.location.search);
    
    // Handle audio parameter for transcription page
    if (window.location.pathname === '/transcribe') {
        const audioParam = urlParams.get('audio');
        if (audioParam) {
            const infoElement = document.createElement('div');
            infoElement.className = 'info-message';
            infoElement.innerHTML = `
                <i class="fas fa-info-circle"></i>
                <p>Audio aus vorheriger Extraktion: ${audioParam}</p>
            `;
            
            const uploadContainer = document.querySelector('.upload-container');
            if (uploadContainer) {
                uploadContainer.prepend(infoElement);
            }
        }
    }
}

/**
 * Add event listeners for elements that appear on multiple pages
 */
function addGlobalEventListeners() {
    // Mobile navigation toggle
    const navToggle = document.querySelector('.nav-toggle');
    if (navToggle) {
        navToggle.addEventListener('click', function() {
            const nav = document.querySelector('nav ul');
            nav.classList.toggle('active');
        });
    }
    
    // File input styling
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const fileName = this.files[0]?.name || 'Keine Datei ausgewählt';
            const fileNameDisplay = this.parentElement.querySelector('.file-name');
            
            if (fileNameDisplay) {
                fileNameDisplay.textContent = fileName;
            } else {
                const span = document.createElement('span');
                span.className = 'file-name';
                span.textContent = fileName;
                this.parentElement.appendChild(span);
            }
        });
    });
}

/**
 * Format file size in human-readable format
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Show a notification message
 * @param {string} message - Message to display
 * @param {string} type - Message type (success, error, info, warning)
 * @param {number} duration - Duration in milliseconds
 */
function showNotification(message, type = 'info', duration = 5000) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${type === 'success' ? 'check-circle' : 
                              type === 'error' ? 'exclamation-circle' : 
                              type === 'warning' ? 'exclamation-triangle' : 
                              'info-circle'}"></i>
            <p>${message}</p>
        </div>
        <button class="notification-close">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Add to document
    document.body.appendChild(notification);
    
    // Add close button functionality
    const closeButton = notification.querySelector('.notification-close');
    closeButton.addEventListener('click', function() {
        notification.classList.add('closing');
        setTimeout(() => {
            notification.remove();
        }, 300);
    });
    
    // Auto-remove after duration
    setTimeout(() => {
        if (document.body.contains(notification)) {
            notification.classList.add('closing');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }
    }, duration);
    
    // Show with animation
    setTimeout(() => {
        notification.classList.add('visible');
    }, 10);
}

/**
 * Format timestamp in HH:MM:SS format
 * @param {number} seconds - Time in seconds
 * @returns {string} Formatted time
 */
function formatTimestamp(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);

    return [
        h > 0 ? h.toString().padStart(2, '0') : null,
        m.toString().padStart(2, '0'),
        s.toString().padStart(2, '0')
    ].filter(Boolean).join(':');
}

function formatCorrectionLevelLabel(level) {
    if (!level) return 'Standard';
    const normalized = level.toString().toLowerCase();
    const mapping = {
        light: 'Leicht',
        minimal: 'Leicht',
        standard: 'Standard',
        strict: 'Strikt',
        enhanced: 'Strikt',
        none: 'Keine'
    };
    return mapping[normalized] || normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

function formatCorrectionMethodLabel(method) {
    if (!method) return 'LLM';
    const normalized = method.toString().toLowerCase();
    if (normalized === 'llm') return 'LLM';
    if (normalized === 'rule_based') return 'Regelbasiert';
    return normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

function formatNumberLocalized(value) {
    const number = Number(value);
    if (Number.isNaN(number)) return value ?? '0';
    return new Intl.NumberFormat('de-DE').format(number);
}

/**
 * Text Correction Manager
 */
class TextCorrectionManager {
    constructor() {
        this.isAvailable = false;
        this.modelInfo = null;
        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.checkModelAvailability();
    }

    setupEventListeners() {
        const enableCorrectionCheckbox = document.getElementById('enable-correction');
        const correctionOptions = document.getElementById('correction-options');

        if (enableCorrectionCheckbox && correctionOptions) {
            enableCorrectionCheckbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    correctionOptions.style.display = 'block';
                } else {
                    correctionOptions.style.display = 'none';
                }
            });
        }
    }

    async checkModelAvailability() {
        const statusIndicator = document.getElementById('correction-availability');
        const ramInfo = document.getElementById('ram-info');
        const modelStatus = document.getElementById('model-status');

        try {
            const response = await fetch('/api/correction-status');
            const data = await response.json();

            this.isAvailable = data.available;
            this.modelInfo = data;

            if (data.available) {
                statusIndicator.className = 'status-indicator available';
                statusIndicator.innerHTML = '<i class="fas fa-check-circle"></i> LeoLM-Modell verfügbar';
                modelStatus.className = 'model-status';

                if (data.ram_required) {
                    ramInfo.textContent = `Benötigter RAM: ~${data.ram_required} GB`;
                }
            } else if (data.downloading) {
                statusIndicator.className = 'status-indicator warning';
                statusIndicator.innerHTML = '<i class="fas fa-download"></i> Modell wird heruntergeladen...';
                modelStatus.className = 'model-status warning';
                ramInfo.textContent = 'Download läuft, bitte warten...';
            } else {
                statusIndicator.className = 'status-indicator unavailable';
                statusIndicator.innerHTML = '<i class="fas fa-times-circle"></i> LeoLM-Modell nicht verfügbar';
                modelStatus.className = 'model-status unavailable';
                ramInfo.textContent = data.error || 'Modell kann nicht geladen werden';

                // Disable correction option
                const enableCorrectionCheckbox = document.getElementById('enable-correction');
                if (enableCorrectionCheckbox) {
                    enableCorrectionCheckbox.disabled = true;
                    enableCorrectionCheckbox.parentElement.style.opacity = '0.6';
                }
            }
        } catch (error) {
            console.error('Error checking model availability:', error);
            statusIndicator.className = 'status-indicator unavailable';
            statusIndicator.innerHTML = '<i class="fas fa-exclamation-circle"></i> Fehler beim Prüfen der Verfügbarkeit';
            modelStatus.className = 'model-status unavailable';
            ramInfo.textContent = 'Netzwerkfehler';
        }
    }
}

/**
 * Two-Phase Progress Manager
 */
class TwoPhaseProgressManager {
    constructor() {
        this.currentPhase = null;
        this.phases = {
            transcription: {
                element: document.getElementById('transcription-phase'),
                title: document.getElementById('transcription-phase-title'),
                progressBar: document.getElementById('transcription-progress-bar'),
                eta: document.getElementById('transcription-eta'),
                chunkInfo: document.getElementById('transcription-chunk-info')
            },
            correction: {
                element: document.getElementById('correction-phase'),
                title: document.getElementById('correction-phase-title'),
                progressBar: document.getElementById('correction-progress-bar'),
                eta: document.getElementById('correction-eta'),
                chunkInfo: document.getElementById('correction-chunk-info')
            }
        };
        this.startTime = null;
    }

    startProgress(hasCorrectionEnabled = false) {
        const progressPhases = document.getElementById('progress-phases');
        const progressContainer = document.getElementById('progress-container');

        if (progressPhases) {
            progressPhases.style.display = 'block';
            progressContainer.style.display = 'none';

            // Show/hide correction phase based on settings
            if (this.phases.correction.element) {
                this.phases.correction.element.style.display = hasCorrectionEnabled ? 'block' : 'none';
            }

            this.startTime = Date.now();
            this.setPhase('transcription', 'active');
        } else {
            // Fallback to legacy progress bar
            progressContainer.style.display = 'block';
        }
    }

    setPhase(phaseName, status) {
        this.currentPhase = phaseName;
        const phase = this.phases[phaseName];

        if (!phase || !phase.title) return;

        // Reset all phases
        Object.keys(this.phases).forEach(key => {
            const p = this.phases[key];
            if (p.title) {
                p.title.className = 'phase-title';
            }
            if (p.progressBar) {
                p.progressBar.className = 'phase-progress-bar';
            }
        });

        // Set current phase status
        if (phase.title) {
            phase.title.className = `phase-title ${status}`;
        }
        if (phase.progressBar) {
            phase.progressBar.className = `phase-progress-bar ${status}`;
        }
    }

    updateProgress(phaseName, progress, chunkCurrent = null, chunkTotal = null, eta = null) {
        const phase = this.phases[phaseName];
        if (!phase) return;

        // Update progress bar
        if (phase.progressBar) {
            phase.progressBar.style.width = `${Math.max(0, Math.min(100, progress))}%`;
        }

        // Update chunk info
        if (phase.chunkInfo && chunkCurrent && chunkTotal) {
            phase.chunkInfo.textContent = `${chunkCurrent}/${chunkTotal} Chunks`;
            phase.chunkInfo.className = 'chunk-info active';
        }

        // Update ETA
        if (phase.eta && eta) {
            phase.eta.textContent = `ETA: ${eta}`;
        }
    }

    completePhase(phaseName) {
        const phase = this.phases[phaseName];
        if (!phase) return;

        this.setPhase(phaseName, 'completed');

        if (phase.progressBar) {
            phase.progressBar.style.width = '100%';
        }

        if (phase.eta) {
            phase.eta.textContent = 'Abgeschlossen';
        }

        if (phase.chunkInfo) {
            phase.chunkInfo.className = 'chunk-info';
        }
    }

    hideProgress() {
        const progressPhases = document.getElementById('progress-phases');
        const progressContainer = document.getElementById('progress-container');

        if (progressPhases) {
            progressPhases.style.display = 'none';
        }
        if (progressContainer) {
            progressContainer.style.display = 'none';
        }
    }

    calculateETA(progress, startTime) {
        if (progress <= 0 || !startTime) return null;

        const elapsed = Date.now() - startTime;
        const estimatedTotal = elapsed / (progress / 100);
        const remaining = estimatedTotal - elapsed;

        if (remaining <= 0) return null;

        const seconds = Math.ceil(remaining / 1000);
        if (seconds < 60) {
            return `${seconds}s`;
        } else {
            const minutes = Math.ceil(seconds / 60);
            return `${minutes}m`;
        }
    }
}

/**
 * Result Display Manager
 */
class ResultDisplayManager {
    constructor() {
        this.resultContainer = document.getElementById('transcription-result');
    }

    displayResults(data) {
        if (!this.resultContainer) return;
        const correctionInfo = data.correction || {};
        const correctionEnabled = data.correction_enabled ?? correctionInfo.enabled ?? false;
        const correctionSuccess = data.correction_success ?? correctionInfo.success ?? false;
        const correctionError = data.correction_error || correctionInfo.error;
        const correctedText = data.corrected_text || correctionInfo.corrected_text;
        const correctedOutputFile = data.corrected_output_file || correctionInfo.corrected_file;

        if (correctionEnabled) {
            const modelInfo = correctionInfo.model_info || {};
            const enrichedData = {
                ...data,
                corrected_text: correctedText,
                corrected_output_file: correctedOutputFile,
                correction_level: data.correction_level || correctionInfo.correction_level,
                correction_method: data.correction_method || correctionInfo.method,
                correction_changes: data.correction_changes ?? (Array.isArray(correctionInfo.corrections_made) ? correctionInfo.corrections_made.length : correctionInfo.corrections_made || 0),
                correction_improvement_score: data.correction_improvement_score ?? correctionInfo.improvement_score,
                correction_metadata_file: data.correction_metadata_file || correctionInfo.metadata_file,
                correction_time: data.correction_time || correctionInfo.processing_time,
                correction_time_seconds: data.correction_time_seconds ?? correctionInfo.processing_time_seconds,
                correction_model: data.correction_model || correctionInfo.model || modelInfo.model_name || (modelInfo.model_path ? modelInfo.model_path.split('/').pop() : undefined),
                correction_model_path: data.correction_model_path || modelInfo.model_path,
                correction_llm_level: data.correction_llm_level || correctionInfo.llm_level
            };

            if (correctionSuccess && correctedText) {
                this.displayDualResults(enrichedData);
                showNotification(
                    `Textkorrektur abgeschlossen (${formatCorrectionLevelLabel(enrichedData.correction_level || 'standard')})`,
                    'success',
                    6000
                );
            } else if (correctionSuccess && !correctedText) {
                // No text difference – inform user but still show single result
                this.displaySingleResult(data);
                this.injectCorrectionMessage('info', 'Textkorrektur abgeschlossen – keine Änderungen erforderlich.');
                showNotification('Textkorrektur abgeschlossen – keine Änderungen erforderlich.', 'info', 5000);
            } else {
                this.displaySingleResult(data);
                const errorMessage = correctionError || 'Textkorrektur konnte nicht durchgeführt werden.';
                this.injectCorrectionMessage('warning', errorMessage);
                showNotification(`Textkorrektur übersprungen: ${errorMessage}`, 'warning', 6000);
            }
        } else {
            this.displaySingleResult(data);
        }
    }

    displayDualResults(data) {
        const levelLabel = formatCorrectionLevelLabel(data.correction_level || 'standard');
        const methodLabel = formatCorrectionMethodLabel(data.correction_method || 'llm');
        const changesLabel = formatNumberLocalized(data.correction_changes ?? 0);
        const improvement = data.correction_improvement_score;
        const improvementLabel = typeof improvement === 'number' && !Number.isNaN(improvement)
            ? `${improvement.toFixed(2)}%`
            : null;
        const durationLabel = data.correction_time
            || (typeof data.correction_time_seconds === 'number' ? `${data.correction_time_seconds.toFixed(2)} s` : null);
        const modelLabel = data.correction_model
            || (data.correction_model_path ? data.correction_model_path.split('/').pop() : null);
        const llmLevelLabel = data.correction_llm_level
            ? formatCorrectionLevelLabel(data.correction_llm_level)
            : null;

        const resultHTML = `
            <div class="correction-summary" style="border: 1px solid #c7e8c1; background: #f5fff4; padding: 16px; border-radius: 12px; margin-bottom: 18px; display: flex; gap: 16px; align-items: center;">
                <div class="summary-icon" style="font-size: 26px; color: #2f9e44;">
                    <i class="fas fa-spell-check"></i>
                </div>
                <div class="summary-content" style="flex: 1;">
                    <div style="font-weight: 600; font-size: 16px;">Textkorrektur abgeschlossen</div>
                    <div style="font-size: 14px; color: #2f9e44;">
                        ${levelLabel}
                        ${llmLevelLabel && llmLevelLabel !== levelLabel ? ` · LLM-Level: ${llmLevelLabel}` : ''}
                        · ${methodLabel}
                        · ${changesLabel} Änderungen
                        ${improvementLabel ? ` · ${improvementLabel} Verbesserung` : ''}
                        ${durationLabel ? ` · ${durationLabel}` : ''}
                        ${modelLabel ? ` · Modell: ${modelLabel}` : ''}
                    </div>
                </div>
                ${data.correction_metadata_file ? `<button class="btn secondary" onclick="downloadFile('${data.correction_metadata_file}')">
                        <i class="fas fa-file-alt"></i> Metadaten
                    </button>` : ''}
            </div>
            <div class="result-versions">
                <div class="result-version">
                    <div class="version-header">
                        <div class="version-title">
                            <i class="fas fa-microphone"></i> Original-Transkription
                        </div>
                        <div class="version-badge">Original</div>
                    </div>
                    <div class="version-content">
                        <pre>${data.text || 'Kein Text verfügbar'}</pre>
                    </div>
                    <div class="version-metadata">
                        <div class="metadata-item">
                            <span>Verarbeitungszeit:</span>
                            <span>${data.transcription_time || 'N/A'}</span>
                        </div>
                        <div class="metadata-item">
                            <span>Modell:</span>
                            <span>${data.model || 'N/A'}</span>
                        </div>
                        <div class="metadata-item">
                            <span>Sprache:</span>
                            <span>${data.language || 'Auto-erkannt'}</span>
                        </div>
                    </div>
                    <div class="version-actions">
                        <button class="btn primary" onclick="downloadFile('${data.output_file}')">
                            <i class="fas fa-download"></i> Download
                        </button>
                    </div>
                </div>

                <div class="result-version">
                    <div class="version-header">
                        <div class="version-title">
                            <i class="fas fa-spell-check"></i> Korrigierte Version
                        </div>
                        <div class="version-badge corrected">Korrigiert</div>
                    </div>
                    <div class="version-content">
                        <pre>${data.corrected_text || 'Keine Korrektur verfügbar'}</pre>
                    </div>
                    <div class="version-metadata">
                        <div class="metadata-item">
                            <span>Korrektur-Zeit:</span>
                            <span>${durationLabel || 'N/A'}</span>
                        </div>
                        <div class="metadata-item">
                            <span>Modell:</span>
                            <span>${modelLabel || 'Unbekannt'}</span>
                        </div>
                        <div class="metadata-item">
                            <span>Korrekturstufe:</span>
                            <span>${levelLabel}</span>
                        </div>
                        <div class="metadata-item">
                            <span>LLM-Level:</span>
                            <span>${llmLevelLabel || 'N/A'}</span>
                        </div>
                        <div class="metadata-item">
                            <span>Änderungen:</span>
                            <span>${changesLabel} Korrekturen</span>
                        </div>
                    </div>
                        <div class="version-actions">
                            <button class="btn primary" onclick="downloadFile('${data.corrected_output_file}')">
                                <i class="fas fa-download"></i> Download
                            </button>
                        </div>
                </div>
            </div>
        `;

        this.resultContainer.innerHTML = resultHTML;
    }

    injectCorrectionMessage(type, message) {
        if (!this.resultContainer) return;
        const existing = this.resultContainer.querySelector('.correction-message');
        if (existing) {
            existing.remove();
        }

        const icon = type === 'warning' ? 'exclamation-triangle' : type === 'info' ? 'info-circle' : 'check-circle';
        const color = type === 'warning' ? '#b35c00' : '#1e66f5';

        const messageHtml = document.createElement('div');
        messageHtml.className = 'correction-message';
        messageHtml.style.border = `1px solid ${color}`;
        messageHtml.style.background = type === 'warning' ? '#fff4e6' : '#eef4ff';
        messageHtml.style.padding = '12px 16px';
        messageHtml.style.borderRadius = '10px';
        messageHtml.style.marginBottom = '16px';
        messageHtml.style.display = 'flex';
        messageHtml.style.alignItems = 'center';
        messageHtml.style.gap = '12px';
        messageHtml.innerHTML = `
            <span style="color:${color}; font-size: 20px;"><i class="fas fa-${icon}"></i></span>
            <span style="color:${color};">${message}</span>
        `;

        this.resultContainer.prepend(messageHtml);
    }

    displaySingleResult(data) {
        let resultHtml = `
            <div class="success-message">
                <i class="fas fa-check-circle"></i> Transkription erfolgreich!
            </div>
            <div class="result-info">
                <p><strong>Modell:</strong> ${data.model}</p>
                <p><strong>Sprache:</strong> ${data.language || 'Automatisch erkannt'}</p>
                <p><strong>Ausgabedatei:</strong> ${data.output_file}</p>
            </div>
        `;

        // Handle SRT format display
        const outputFormat = document.getElementById('output-format')?.value?.toLowerCase();
        if (outputFormat === 'srt') {
            resultHtml += `
                <div class="result-text srt-format">
                    <h4>SRT-Untertitel mit Zeitstempeln:</h4>
                    <pre class="srt-content">${data.text}</pre>
                </div>
            `;
        } else {
            resultHtml += `
                <div class="result-text">
                    <h4>Transkribierter Text:</h4>
                    <pre>${data.text}</pre>
                </div>
            `;
        }

        this.resultContainer.innerHTML = resultHtml;
    }

    displayError(error) {
        if (!this.resultContainer) return;

        this.resultContainer.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i> Fehler bei der Transkription
            </div>
            <p>${error || 'Unbekannter Fehler'}</p>
        `;
    }
}

// Global instances
let correctionManager;
let progressManager;
let resultManager;

// Initialize managers when transcribe page loads
if (window.location.pathname === '/transcribe' || window.location.pathname.includes('transcribe')) {
    document.addEventListener('DOMContentLoaded', function() {
        correctionManager = new TextCorrectionManager();
        progressManager = new TwoPhaseProgressManager();
        resultManager = new ResultDisplayManager();
    });
}
