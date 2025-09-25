"""
Logging setup for the Whisper Transcription Tool.

This module provides comprehensive logging with privacy awareness,
categorization, and sanitization capabilities.
"""

import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, Optional, Union, Set, Pattern

# Configure default logging format
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FILE = str(Path.home() / ".whisper_tool" / "whisper_tool.log")

# Privacy patterns to sanitize from logs
PRIVACY_PATTERNS: Set[Pattern] = {
    re.compile(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', re.IGNORECASE),  # Email addresses
    re.compile(r'\b\d{3}[- ]?\d{3}[- ]?\d{4}\b'),  # Phone numbers (US format)
    re.compile(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'),  # Credit card numbers
    re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),  # SSN
    re.compile(r'\b(?:password|pwd|pass|token|key|secret|auth)\s*[:=]\s*\S+\b', re.IGNORECASE),  # Passwords/tokens
    re.compile(r'\b[A-Za-z0-9]{20,}\b'),  # Long tokens/hashes (20+ chars)
}

# Sensitive keywords that should be redacted
SENSITIVE_KEYWORDS = {
    'password', 'pwd', 'pass', 'token', 'key', 'secret', 'auth', 'credential',
    'api_key', 'access_token', 'refresh_token', 'bearer', 'authorization'
}


class PrivacyAwareFormatter(logging.Formatter):
    """
    Custom formatter that sanitizes sensitive information from log messages.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def format(self, record: logging.LogRecord) -> str:
        # Format the message normally first
        formatted_message = super().format(record)

        # Sanitize sensitive information
        return self.sanitize_message(formatted_message)

    def sanitize_message(self, message: str) -> str:
        """
        Sanitize sensitive information from log messages.

        Args:
            message: Original log message

        Returns:
            Sanitized log message
        """
        sanitized = message

        # Apply privacy patterns
        for pattern in PRIVACY_PATTERNS:
            sanitized = pattern.sub('[REDACTED]', sanitized)

        # Redact sensitive keywords
        for keyword in SENSITIVE_KEYWORDS:
            # Case-insensitive replacement
            pattern = re.compile(rf'\b{re.escape(keyword)}\b.*?(?=\s|$)', re.IGNORECASE)
            sanitized = pattern.sub(f'{keyword.upper()}: [REDACTED]', sanitized)

        return sanitized


class TextCorrectionLogger:
    """
    Specialized logger for text correction operations with privacy awareness.
    """

    def __init__(self, name: str = "text_correction"):
        self.logger = logging.getLogger(f"whisper_transcription_tool.{name}")
        self._setup_text_correction_logging()

    def _setup_text_correction_logging(self):
        """Set up specialized logging for text correction."""
        # Ensure we don't add multiple handlers
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = PrivacyAwareFormatter(
                "%(asctime)s - TEXT_CORRECTION - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def log_correction_start(self, text_length: int, model_name: str):
        """Log the start of a text correction operation."""
        self.logger.info(
            f"Starting text correction - Length: {text_length} chars, Model: {model_name}"
        )

    def log_correction_complete(self, duration_seconds: float, success: bool, partial: bool = False):
        """Log completion of text correction."""
        status = "SUCCESS" if success else "FAILED"
        if partial:
            status += " (PARTIAL)"

        self.logger.info(
            f"Text correction completed - Status: {status}, Duration: {duration_seconds:.2f}s"
        )

    def log_correction_error(self, error_type: str, error_message: str):
        """Log text correction errors without sensitive data."""
        # Sanitize error message
        sanitized_message = self._sanitize_error_message(error_message)
        self.logger.error(f"Text correction error [{error_type}]: {sanitized_message}")

    def log_chunking_info(self, total_chunks: int, chunk_size_avg: int):
        """Log text chunking information."""
        self.logger.info(f"Text chunked into {total_chunks} parts, avg size: {chunk_size_avg} chars")

    def log_memory_usage(self, memory_mb: float):
        """Log memory usage during correction."""
        self.logger.debug(f"Memory usage: {memory_mb:.1f} MB")

    def _sanitize_error_message(self, message: str) -> str:
        """Sanitize error messages to remove any sensitive content."""
        sanitized = message

        # Remove any quoted text that might contain transcription content
        sanitized = re.sub(r'"[^"]{50,}"', '"[CONTENT_REDACTED]"', sanitized)
        sanitized = re.sub(r"'[^']{50,}'", "'[CONTENT_REDACTED]'", sanitized)

        # Apply standard privacy patterns
        for pattern in PRIVACY_PATTERNS:
            sanitized = pattern.sub('[REDACTED]', sanitized)

        return sanitized


def setup_logging(
    log_level: Union[int, str] = DEFAULT_LOG_LEVEL,
    log_file: Optional[str] = DEFAULT_LOG_FILE,
    log_format: str = DEFAULT_LOG_FORMAT,
    config: Optional[Dict] = None,
    enable_privacy_filtering: bool = True,
) -> None:
    """
    Set up logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (None for no file logging)
        log_format: Logging format string
        config: Configuration dictionary that may contain logging settings
        enable_privacy_filtering: Enable privacy-aware log filtering
    """
    # Override with config if provided
    if config and "logging" in config:
        log_config = config["logging"]
        log_level = log_config.get("level", log_level)
        log_file = log_config.get("file", log_file)
        log_format = log_config.get("format", log_format)
        enable_privacy_filtering = log_config.get("privacy_filtering", enable_privacy_filtering)

    # Convert string log level to numeric if needed
    if isinstance(log_level, str):
        log_level = getattr(logging, log_level.upper(), logging.INFO)

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Choose formatter based on privacy filtering setting
    if enable_privacy_filtering:
        formatter = PrivacyAwareFormatter(log_format)
    else:
        formatter = logging.Formatter(log_format)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Create file handler if log_file is specified
    if log_file:
        try:
            # Create directory if it doesn't exist
            log_dir = os.path.dirname(log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)

            # Add file handler
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            logging.warning(f"Failed to set up file logging to {log_file}: {e}")

    # Set lower level for our own loggers
    logging.getLogger("whisper_transcription_tool").setLevel(log_level)

    # Set up specialized loggers
    _setup_specialized_loggers(log_level, enable_privacy_filtering)

    privacy_status = "ENABLED" if enable_privacy_filtering else "DISABLED"
    logging.info(f"Logging initialized at level {logging.getLevelName(log_level)} (Privacy filtering: {privacy_status})")
    if log_file:
        logging.info(f"Log file: {log_file}")


def _setup_specialized_loggers(log_level: int, enable_privacy_filtering: bool):
    """Set up specialized logger categories."""

    # Text correction logger
    text_correction_logger = logging.getLogger("whisper_transcription_tool.text_correction")
    text_correction_logger.setLevel(log_level)

    # Error handling logger
    error_logger = logging.getLogger("whisper_transcription_tool.error_handling")
    error_logger.setLevel(log_level)

    # Monitoring logger
    monitoring_logger = logging.getLogger("whisper_transcription_tool.monitoring")
    monitoring_logger.setLevel(log_level)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.

    Args:
        name: Logger name, typically __name__ of the calling module

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def get_text_correction_logger() -> TextCorrectionLogger:
    """
    Get the specialized text correction logger.

    Returns:
        TextCorrectionLogger instance
    """
    return TextCorrectionLogger()


def log_exception(logger: logging.Logger, exception: Exception, context: str = ""):
    """
    Log an exception with privacy-aware error handling.

    Args:
        logger: Logger instance to use
        exception: Exception to log
        context: Additional context information
    """
    # Import here to avoid circular imports
    from .exceptions import WhisperToolError

    if isinstance(exception, WhisperToolError):
        # Use the structured error information
        error_info = exception.to_dict()
        context_str = f" [{context}]" if context else ""

        logger.error(
            f"WhisperTool Error{context_str}: {error_info['error_type']} - "
            f"{error_info['user_message']} (Category: {error_info['category']}, "
            f"Recovery: {error_info['recovery_action']})"
        )

        # Log details at debug level if available
        if error_info['details']:
            logger.debug(f"Error details: {error_info['details']}")
    else:
        # Standard exception logging with sanitization
        context_str = f" [{context}]" if context else ""
        sanitized_message = _sanitize_exception_message(str(exception))
        logger.error(f"Exception{context_str}: {type(exception).__name__} - {sanitized_message}")


def _sanitize_exception_message(message: str) -> str:
    """Sanitize exception messages to remove sensitive content."""
    sanitized = message

    # Apply privacy patterns
    for pattern in PRIVACY_PATTERNS:
        sanitized = pattern.sub('[REDACTED]', sanitized)

    # Remove long text snippets that might contain transcription content
    sanitized = re.sub(r'"[^"]{100,}"', '"[LONG_CONTENT_REDACTED]"', sanitized)
    sanitized = re.sub(r"'[^']{100,}'", "'[LONG_CONTENT_REDACTED]'", sanitized)

    return sanitized


def configure_privacy_patterns(additional_patterns: Optional[Set[Pattern]] = None):
    """
    Configure additional privacy patterns for log sanitization.

    Args:
        additional_patterns: Additional regex patterns to use for sanitization
    """
    global PRIVACY_PATTERNS

    if additional_patterns:
        PRIVACY_PATTERNS.update(additional_patterns)


def configure_sensitive_keywords(additional_keywords: Optional[Set[str]] = None):
    """
    Configure additional sensitive keywords for log sanitization.

    Args:
        additional_keywords: Additional sensitive keywords to redact
    """
    global SENSITIVE_KEYWORDS

    if additional_keywords:
        SENSITIVE_KEYWORDS.update(additional_keywords)
