"""
Core functionality for the Whisper Transcription Tool.
"""

__version__ = "0.1.0"

# Export configuration functions for text correction
from .config import (
    load_config,
    save_config,
    is_correction_available,
    print_correction_status,
    validate_and_migrate_config,
)

# Export telemetry and error handling
from .exceptions import (
    WhisperToolError,
    ErrorCategory,
    RecoveryAction,
    ModelNotFoundError,
    InsufficientMemoryError,
    ModelLoadError,
    ChunkingError,
    LLMInferenceError,
    ConfigError,
    ModelError,
    TranscriptionError,
    ExtractionError,
    PhoneProcessingError,
    ChatbotError,
    DependencyError,
    FileFormatError,
    APIError,
)

# Export logging functionality
from .logging_setup import (
    setup_logging,
    get_logger,
    get_text_correction_logger,
    log_exception,
    TextCorrectionLogger,
    PrivacyAwareFormatter,
    configure_privacy_patterns,
    configure_sensitive_keywords,
)

# Export monitoring functionality
from .monitoring import (
    initialize_monitoring,
    get_metrics_collector,
    is_monitoring_enabled,
    record_correction_duration,
    record_memory_usage,
    increment_correction_count,
    text_correction_timer,
    MetricsCollector,
    PerformanceMetric,
    OperationMetrics,
)

# Export error recovery functionality
from .error_recovery import (
    get_recovery_manager,
    with_error_recovery,
    with_retry,
    RecoveryResult,
    ErrorRecoveryManager,
)

# Export telemetry integration
from .telemetry_integration import (
    initialize_telemetry,
    get_telemetry_manager,
    monitored_text_correction,
    safe_model_operation,
    TelemetryManager,
)

__all__ = [
    # Configuration
    "load_config",
    "save_config",
    "is_correction_available",
    "print_correction_status",
    "validate_and_migrate_config",

    # Exceptions
    "WhisperToolError",
    "ErrorCategory",
    "RecoveryAction",
    "ModelNotFoundError",
    "InsufficientMemoryError",
    "ModelLoadError",
    "ChunkingError",
    "LLMInferenceError",
    "ConfigError",
    "ModelError",
    "TranscriptionError",
    "ExtractionError",
    "PhoneProcessingError",
    "ChatbotError",
    "DependencyError",
    "FileFormatError",
    "APIError",

    # Logging
    "setup_logging",
    "get_logger",
    "get_text_correction_logger",
    "log_exception",
    "TextCorrectionLogger",
    "PrivacyAwareFormatter",
    "configure_privacy_patterns",
    "configure_sensitive_keywords",

    # Monitoring
    "initialize_monitoring",
    "get_metrics_collector",
    "is_monitoring_enabled",
    "record_correction_duration",
    "record_memory_usage",
    "increment_correction_count",
    "text_correction_timer",
    "MetricsCollector",
    "PerformanceMetric",
    "OperationMetrics",

    # Error Recovery
    "get_recovery_manager",
    "with_error_recovery",
    "with_retry",
    "RecoveryResult",
    "ErrorRecoveryManager",

    # Telemetry Integration
    "initialize_telemetry",
    "get_telemetry_manager",
    "monitored_text_correction",
    "safe_model_operation",
    "TelemetryManager",
]
