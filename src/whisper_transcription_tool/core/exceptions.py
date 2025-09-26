"""
Exception handling for the Whisper Transcription Tool.

This module provides comprehensive error handling with categorization,
recovery strategies, and user-friendly error messages.
"""

from typing import Optional, Dict, Any
from enum import Enum


class ErrorCategory(Enum):
    """Error categories for better error handling and recovery."""
    CRITICAL = "critical"  # System failure, no recovery possible
    RECOVERABLE = "recoverable"  # Can attempt recovery or fallback
    WARNING = "warning"  # Issue but can continue with degraded functionality
    USER_ERROR = "user_error"  # User input or configuration issue


class RecoveryAction(Enum):
    """Actions that can be taken when an error occurs."""
    ABORT = "abort"  # Stop processing entirely
    SKIP = "skip"  # Skip the current operation and continue
    FALLBACK = "fallback"  # Use fallback method/data
    RETRY = "retry"  # Retry the operation
    CONTINUE = "continue"  # Continue with partial results


class WhisperToolError(Exception):
    """
    Base exception class for Whisper Transcription Tool.

    All custom exceptions should inherit from this class and provide
    categorization and recovery information.
    """

    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.CRITICAL,
        recovery_action: RecoveryAction = RecoveryAction.ABORT,
        user_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.recovery_action = recovery_action
        # Details are needed by many _generate_user_message implementations
        # so populate them before creating the default user message.
        self.details = details or {}
        self.user_message = user_message or self._generate_user_message()

    def _generate_user_message(self) -> str:
        """Generate a user-friendly error message."""
        return "Ein unbekannter Fehler ist aufgetreten."

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "category": self.category.value,
            "recovery_action": self.recovery_action.value,
            "user_message": self.user_message,
            "details": self.details
        }


class ConfigError(WhisperToolError):
    """Exception raised for configuration errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.USER_ERROR,
            recovery_action=RecoveryAction.ABORT,
            **kwargs
        )

    def _generate_user_message(self) -> str:
        return "Konfigurationsfehler. Bitte überprüfen Sie Ihre Einstellungen."


class ModelError(WhisperToolError):
    """Exception raised for model-related errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.RECOVERABLE,
            recovery_action=RecoveryAction.FALLBACK,
            **kwargs
        )

    def _generate_user_message(self) -> str:
        return "Modell-Fehler aufgetreten. Versuche Fallback-Strategie."


class ModelNotFoundError(ModelError):
    """Exception raised when a required model cannot be found."""

    def __init__(self, model_name: str, **kwargs):
        message = f"Model '{model_name}' not found"
        super().__init__(
            message,
            category=ErrorCategory.RECOVERABLE,
            recovery_action=RecoveryAction.SKIP,
            details={"model_name": model_name},
            **kwargs
        )

    def _generate_user_message(self) -> str:
        model_name = self.details.get("model_name", "unbekannt")
        return f"Modell '{model_name}' nicht gefunden. Verwende Original-Text."


class InsufficientMemoryError(ModelError):
    """Exception raised when there's insufficient memory to load a model."""

    def __init__(self, required_memory: Optional[int] = None, available_memory: Optional[int] = None, **kwargs):
        message = "Insufficient memory to load model"
        if required_memory and available_memory:
            message += f" (required: {required_memory}MB, available: {available_memory}MB)"

        super().__init__(
            message,
            category=ErrorCategory.RECOVERABLE,
            recovery_action=RecoveryAction.SKIP,
            details={
                "required_memory": required_memory,
                "available_memory": available_memory
            },
            **kwargs
        )

    def _generate_user_message(self) -> str:
        return "Zu wenig RAM verfügbar. Verwende Original-Text ohne Korrektur."


class ModelLoadError(ModelError):
    """Exception raised when a model fails to load."""

    def __init__(self, model_name: str, reason: Optional[str] = None, **kwargs):
        message = f"Failed to load model '{model_name}'"
        if reason:
            message += f": {reason}"

        super().__init__(
            message,
            category=ErrorCategory.RECOVERABLE,
            recovery_action=RecoveryAction.SKIP,
            details={"model_name": model_name, "reason": reason},
            **kwargs
        )

    def _generate_user_message(self) -> str:
        return "Modell konnte nicht geladen werden. Verwende Original-Text."


class ChunkingError(WhisperToolError):
    """Exception raised when text chunking fails."""

    def __init__(self, message: str, chunk_info: Optional[Dict] = None, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.RECOVERABLE,
            recovery_action=RecoveryAction.CONTINUE,
            details={"chunk_info": chunk_info},
            **kwargs
        )

    def _generate_user_message(self) -> str:
        return "Fehler bei Textaufteilung. Verarbeite gesamten Text."


class LLMInferenceError(WhisperToolError):
    """Exception raised when LLM inference fails."""

    def __init__(self, message: str, partial_result: Optional[str] = None, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.RECOVERABLE,
            recovery_action=RecoveryAction.CONTINUE,
            details={"partial_result": partial_result},
            **kwargs
        )

    def _generate_user_message(self) -> str:
        if self.details.get("partial_result"):
            return "Teilweise Korrektur verfügbar. Einige Teile wurden nicht korrigiert."
        return "LLM-Korrektur fehlgeschlagen. Verwende Original-Text."


class TranscriptionError(WhisperToolError):
    """Exception raised for transcription errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.CRITICAL,
            recovery_action=RecoveryAction.ABORT,
            **kwargs
        )

    def _generate_user_message(self) -> str:
        return "Transkription fehlgeschlagen. Bitte versuchen Sie es erneut."


class ExtractionError(WhisperToolError):
    """Exception raised for audio extraction errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.CRITICAL,
            recovery_action=RecoveryAction.ABORT,
            **kwargs
        )

    def _generate_user_message(self) -> str:
        return "Audio-Extraktion fehlgeschlagen. Prüfen Sie die Eingabedatei."


class PhoneProcessingError(WhisperToolError):
    """Exception raised for phone call processing errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.RECOVERABLE,
            recovery_action=RecoveryAction.FALLBACK,
            **kwargs
        )

    def _generate_user_message(self) -> str:
        return "Fehler bei Telefonverarbeitung. Verwende Einzelspur-Verarbeitung."


class ChatbotError(WhisperToolError):
    """Exception raised for chatbot-related errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.WARNING,
            recovery_action=RecoveryAction.CONTINUE,
            **kwargs
        )

    def _generate_user_message(self) -> str:
        return "Chatbot-Funktionalität temporär nicht verfügbar."


class DependencyError(WhisperToolError):
    """Exception raised for missing dependencies."""

    def __init__(self, dependency: str, **kwargs):
        message = f"Missing dependency: {dependency}"
        super().__init__(
            message,
            category=ErrorCategory.CRITICAL,
            recovery_action=RecoveryAction.ABORT,
            details={"dependency": dependency},
            **kwargs
        )

    def _generate_user_message(self) -> str:
        dependency = self.details.get("dependency", "unbekannt")
        return f"Erforderliche Komponente '{dependency}' nicht gefunden. Installation erforderlich."


class FileFormatError(WhisperToolError):
    """Exception raised for unsupported file formats."""

    def __init__(self, file_format: str, supported_formats: Optional[list] = None, **kwargs):
        message = f"Unsupported file format: {file_format}"
        if supported_formats:
            message += f" (supported: {', '.join(supported_formats)})"

        super().__init__(
            message,
            category=ErrorCategory.USER_ERROR,
            recovery_action=RecoveryAction.ABORT,
            details={"file_format": file_format, "supported_formats": supported_formats},
            **kwargs
        )

    def _generate_user_message(self) -> str:
        file_format = self.details.get("file_format", "unbekannt")
        supported = self.details.get("supported_formats", [])
        if supported:
            return f"Format '{file_format}' nicht unterstützt. Unterstützte Formate: {', '.join(supported)}"
        return f"Dateiformat '{file_format}' wird nicht unterstützt."


class APIError(WhisperToolError):
    """Exception raised for API-related errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.RECOVERABLE,
            recovery_action=RecoveryAction.RETRY,
            details={"status_code": status_code},
            **kwargs
        )

    def _generate_user_message(self) -> str:
        return "API-Fehler aufgetreten. Versuche es später erneut."
