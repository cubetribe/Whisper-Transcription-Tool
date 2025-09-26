"""
Error recovery and graceful degradation for the Whisper Transcription Tool.

This module implements comprehensive error recovery strategies based on the
error recovery matrix defined in the exceptions module.
"""

import time
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar, Union, List
from functools import wraps

from .exceptions import (
    WhisperToolError,
    ErrorCategory,
    RecoveryAction,
    ModelNotFoundError,
    InsufficientMemoryError,
    ModelLoadError,
    ChunkingError,
    LLMInferenceError
)
from .logging_setup import get_logger, log_exception, get_text_correction_logger
from .monitoring import get_metrics_collector, is_monitoring_enabled

logger = get_logger(__name__)
text_logger = get_text_correction_logger()

T = TypeVar('T')


class RecoveryResult:
    """
    Result of an error recovery attempt.
    """

    def __init__(
        self,
        success: bool,
        result: Any = None,
        error: Optional[Exception] = None,
        recovery_action_taken: Optional[RecoveryAction] = None,
        message: str = ""
    ):
        self.success = success
        self.result = result
        self.error = error
        self.recovery_action_taken = recovery_action_taken
        self.message = message

    def __bool__(self) -> bool:
        return self.success

    def __repr__(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        return f"RecoveryResult({status}, action={self.recovery_action_taken}, message='{self.message}')"


class ErrorRecoveryManager:
    """
    Manages error recovery strategies and graceful degradation.
    """

    def __init__(self):
        self.recovery_strategies: Dict[type, Callable] = {}
        self.fallback_handlers: Dict[str, Callable] = {}
        self.retry_configs: Dict[type, Dict] = {}

        # Initialize default recovery strategies
        self._setup_default_strategies()

        # Statistics
        self.recovery_stats = {
            "total_errors": 0,
            "successful_recoveries": 0,
            "failed_recoveries": 0,
            "recovery_actions": {action.value: 0 for action in RecoveryAction}
        }

    def _setup_default_strategies(self):
        """Set up default recovery strategies for known error types."""

        # Model-related error strategies
        self.recovery_strategies[ModelNotFoundError] = self._handle_model_not_found
        self.recovery_strategies[InsufficientMemoryError] = self._handle_insufficient_memory
        self.recovery_strategies[ModelLoadError] = self._handle_model_load_error
        self.recovery_strategies[ChunkingError] = self._handle_chunking_error
        self.recovery_strategies[LLMInferenceError] = self._handle_llm_inference_error

        # Retry configurations
        self.retry_configs[LLMInferenceError] = {
            "max_attempts": 2,
            "delay_seconds": 1.0,
            "backoff_multiplier": 1.5
        }

    def recover_from_error(
        self,
        error: Exception,
        context: str = "",
        original_args: Tuple = (),
        original_kwargs: Dict = None,
        fallback_result: Any = None
    ) -> RecoveryResult:
        """
        Attempt to recover from an error using appropriate strategies.

        Args:
            error: The error that occurred
            context: Context information about where the error occurred
            original_args: Original function arguments
            original_kwargs: Original function keyword arguments
            fallback_result: Default result to return if recovery fails

        Returns:
            RecoveryResult indicating success/failure and any recovered data
        """
        original_kwargs = original_kwargs or {}

        # Log the error
        log_exception(logger, error, context)

        # Update statistics
        self.recovery_stats["total_errors"] += 1

        # Record metrics if monitoring is enabled
        if is_monitoring_enabled():
            metrics = get_metrics_collector()
            metrics.increment_counter("errors_total")
            metrics.increment_counter(f"errors_{type(error).__name__}")

        # Handle WhisperToolError with structured recovery
        if isinstance(error, WhisperToolError):
            return self._recover_whisper_tool_error(
                error, context, original_args, original_kwargs, fallback_result
            )

        # Handle other exceptions with generic recovery
        return self._recover_generic_error(
            error, context, original_args, original_kwargs, fallback_result
        )

    def _recover_whisper_tool_error(
        self,
        error: WhisperToolError,
        context: str,
        original_args: Tuple,
        original_kwargs: Dict,
        fallback_result: Any
    ) -> RecoveryResult:
        """Recover from a structured WhisperToolError."""

        recovery_action = error.recovery_action
        self.recovery_stats["recovery_actions"][recovery_action.value] += 1

        logger.info(f"Attempting recovery for {type(error).__name__} with action: {recovery_action.value}")

        # Try specific recovery strategy if available
        if type(error) in self.recovery_strategies:
            try:
                strategy = self.recovery_strategies[type(error)]
                result = strategy(error, original_args, original_kwargs)

                if result.success:
                    self.recovery_stats["successful_recoveries"] += 1
                    logger.info(f"Recovery successful: {result.message}")

                    # Record successful recovery metric
                    if is_monitoring_enabled():
                        metrics = get_metrics_collector()
                        metrics.increment_counter("recoveries_successful")
                        metrics.increment_counter(f"recovery_{recovery_action.value}_successful")

                    return result

            except Exception as recovery_error:
                logger.error(f"Recovery strategy failed: {recovery_error}")
                log_exception(logger, recovery_error, "recovery_strategy")

        # Apply generic recovery based on action
        return self._apply_generic_recovery_action(
            error, recovery_action, context, fallback_result
        )

    def _apply_generic_recovery_action(
        self,
        error: Exception,
        recovery_action: RecoveryAction,
        context: str,
        fallback_result: Any
    ) -> RecoveryResult:
        """Apply generic recovery action."""

        if recovery_action == RecoveryAction.SKIP:
            message = f"Skipping operation due to {type(error).__name__}"
            logger.info(message)
            self.recovery_stats["successful_recoveries"] += 1

            return RecoveryResult(
                success=True,
                result=fallback_result,
                recovery_action_taken=recovery_action,
                message=message
            )

        elif recovery_action == RecoveryAction.CONTINUE:
            message = f"Continuing with partial results due to {type(error).__name__}"
            logger.info(message)

            # Extract partial result if available
            partial_result = getattr(error, 'details', {}).get('partial_result', fallback_result)
            self.recovery_stats["successful_recoveries"] += 1

            return RecoveryResult(
                success=True,
                result=partial_result,
                recovery_action_taken=recovery_action,
                message=message
            )

        elif recovery_action == RecoveryAction.FALLBACK:
            message = f"Using fallback strategy due to {type(error).__name__}"
            logger.info(message)

            # Try to find a fallback handler
            fallback_handler = self.fallback_handlers.get(context)
            if fallback_handler:
                try:
                    fallback_result = fallback_handler(error)
                    self.recovery_stats["successful_recoveries"] += 1

                    return RecoveryResult(
                        success=True,
                        result=fallback_result,
                        recovery_action_taken=recovery_action,
                        message=message
                    )
                except Exception as fallback_error:
                    logger.error(f"Fallback strategy failed: {fallback_error}")

            # Use default fallback result
            self.recovery_stats["successful_recoveries"] += 1
            return RecoveryResult(
                success=True,
                result=fallback_result,
                recovery_action_taken=recovery_action,
                message=message
            )

        elif recovery_action == RecoveryAction.RETRY:
            # This should be handled by the retry decorator
            message = f"Retry recommended for {type(error).__name__}"
            logger.info(message)

            return RecoveryResult(
                success=False,
                error=error,
                recovery_action_taken=recovery_action,
                message=message
            )

        elif recovery_action == RecoveryAction.ABORT:
            message = f"Aborting due to critical error: {type(error).__name__}"
            logger.error(message)
            self.recovery_stats["failed_recoveries"] += 1

            return RecoveryResult(
                success=False,
                error=error,
                recovery_action_taken=recovery_action,
                message=message
            )

        # Unknown recovery action
        self.recovery_stats["failed_recoveries"] += 1
        return RecoveryResult(
            success=False,
            error=error,
            message=f"Unknown recovery action: {recovery_action}"
        )

    def _recover_generic_error(
        self,
        error: Exception,
        context: str,
        original_args: Tuple,
        original_kwargs: Dict,
        fallback_result: Any
    ) -> RecoveryResult:
        """Recover from generic (non-WhisperToolError) exceptions."""

        logger.warning(f"Attempting generic recovery for {type(error).__name__}")

        # Try fallback handler for the context
        fallback_handler = self.fallback_handlers.get(context)
        if fallback_handler:
            try:
                result = fallback_handler(error)
                self.recovery_stats["successful_recoveries"] += 1

                return RecoveryResult(
                    success=True,
                    result=result,
                    recovery_action_taken=RecoveryAction.FALLBACK,
                    message=f"Generic recovery successful using fallback handler"
                )
            except Exception as fallback_error:
                logger.error(f"Fallback handler failed: {fallback_error}")

        # Default to graceful degradation
        self.recovery_stats["failed_recoveries"] += 1
        return RecoveryResult(
            success=False,
            error=error,
            message=f"No recovery strategy available for {type(error).__name__}"
        )

    # Specific recovery strategies for different error types

    def _handle_model_not_found(
        self,
        error: ModelNotFoundError,
        original_args: Tuple,
        original_kwargs: Dict
    ) -> RecoveryResult:
        """Handle model not found errors by skipping model-based processing."""

        model_name = getattr(error, 'details', {}).get("model_name", "unknown")
        text_logger.log_correction_error("ModelNotFoundError", f"Model '{model_name}' not found")

        # Return original text without correction
        original_text = original_kwargs.get("text") or (original_args[0] if original_args else "")

        return RecoveryResult(
            success=True,
            result=original_text,
            recovery_action_taken=RecoveryAction.SKIP,
            message=f"Using original text due to missing model '{model_name}'"
        )

    def _handle_insufficient_memory(
        self,
        error: InsufficientMemoryError,
        original_args: Tuple,
        original_kwargs: Dict
    ) -> RecoveryResult:
        """Handle insufficient memory by skipping memory-intensive operations."""

        required = getattr(error, 'details', {}).get("required_memory", "unknown")
        available = getattr(error, 'details', {}).get("available_memory", "unknown")

        text_logger.log_correction_error(
            "InsufficientMemoryError",
            f"Required: {required}MB, Available: {available}MB"
        )

        # Return original text without correction
        original_text = original_kwargs.get("text") or (original_args[0] if original_args else "")

        return RecoveryResult(
            success=True,
            result=original_text,
            recovery_action_taken=RecoveryAction.SKIP,
            message="Using original text due to insufficient memory"
        )

    def _handle_model_load_error(
        self,
        error: ModelLoadError,
        original_args: Tuple,
        original_kwargs: Dict
    ) -> RecoveryResult:
        """Handle model load errors by skipping model-based processing."""

        model_name = getattr(error, 'details', {}).get("model_name", "unknown")
        reason = getattr(error, 'details', {}).get("reason", "unknown")

        text_logger.log_correction_error("ModelLoadError", f"Model '{model_name}': {reason}")

        # Return original text without correction
        original_text = original_kwargs.get("text") or (original_args[0] if original_args else "")

        return RecoveryResult(
            success=True,
            result=original_text,
            recovery_action_taken=RecoveryAction.SKIP,
            message=f"Using original text due to model load failure: {model_name}"
        )

    def _handle_chunking_error(
        self,
        error: ChunkingError,
        original_args: Tuple,
        original_kwargs: Dict
    ) -> RecoveryResult:
        """Handle chunking errors by processing text as a whole."""

        text_logger.log_correction_error("ChunkingError", "Text chunking failed, processing as whole")

        # Try to process the entire text without chunking
        original_text = original_kwargs.get("text") or (original_args[0] if original_args else "")

        return RecoveryResult(
            success=True,
            result={"text": original_text, "chunked": False},
            recovery_action_taken=RecoveryAction.CONTINUE,
            message="Processing text as a whole due to chunking failure"
        )

    def _handle_llm_inference_error(
        self,
        error: LLMInferenceError,
        original_args: Tuple,
        original_kwargs: Dict
    ) -> RecoveryResult:
        """Handle LLM inference errors by returning partial results or original text."""

        partial_result = getattr(error, 'details', {}).get("partial_result")

        if partial_result:
            text_logger.log_correction_error("LLMInferenceError", "Partial correction available")

            return RecoveryResult(
                success=True,
                result=partial_result,
                recovery_action_taken=RecoveryAction.CONTINUE,
                message="Using partial correction due to LLM inference failure"
            )
        else:
            text_logger.log_correction_error("LLMInferenceError", "No partial result, using original")

            # Return original text
            original_text = original_kwargs.get("text") or (original_args[0] if original_args else "")

            return RecoveryResult(
                success=True,
                result=original_text,
                recovery_action_taken=RecoveryAction.CONTINUE,
                message="Using original text due to complete LLM inference failure"
            )

    def register_recovery_strategy(self, error_type: type, strategy: Callable) -> None:
        """Register a custom recovery strategy for an error type."""
        self.recovery_strategies[error_type] = strategy
        logger.info(f"Registered recovery strategy for {error_type.__name__}")

    def register_fallback_handler(self, context: str, handler: Callable) -> None:
        """Register a fallback handler for a specific context."""
        self.fallback_handlers[context] = handler
        logger.info(f"Registered fallback handler for context '{context}'")

    def get_recovery_stats(self) -> Dict[str, Any]:
        """Get recovery statistics."""
        success_rate = 0.0
        if self.recovery_stats["total_errors"] > 0:
            success_rate = (
                self.recovery_stats["successful_recoveries"] /
                self.recovery_stats["total_errors"] * 100
            )

        return {
            **self.recovery_stats,
            "success_rate_percent": round(success_rate, 2)
        }


# Global error recovery manager
_recovery_manager: Optional[ErrorRecoveryManager] = None


def get_recovery_manager() -> ErrorRecoveryManager:
    """Get the global error recovery manager, creating it if needed."""
    global _recovery_manager
    if _recovery_manager is None:
        _recovery_manager = ErrorRecoveryManager()
    return _recovery_manager


def with_error_recovery(
    context: str = "",
    fallback_result: Any = None,
    log_recovery: bool = True
) -> Callable:
    """
    Decorator that adds error recovery to functions.

    Args:
        context: Context string for recovery strategies
        fallback_result: Default result if recovery fails
        log_recovery: Whether to log recovery attempts

    Example:
        @with_error_recovery(context="text_correction", fallback_result="")
        def correct_text(text: str) -> str:
            # Function that might raise errors
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                recovery_manager = get_recovery_manager()

                recovery_result = recovery_manager.recover_from_error(
                    error=e,
                    context=context or func.__name__,
                    original_args=args,
                    original_kwargs=kwargs,
                    fallback_result=fallback_result
                )

                if log_recovery and recovery_result.message:
                    logger.info(f"Recovery result: {recovery_result.message}")

                if recovery_result.success:
                    return recovery_result.result

                # Recovery failed, re-raise the original exception
                # unless it's a critical error with ABORT action
                if isinstance(e, WhisperToolError) and e.recovery_action == RecoveryAction.ABORT:
                    raise e

                # For other errors, return fallback result or re-raise
                if fallback_result is not None:
                    return fallback_result

                raise e

        return wrapper
    return decorator


def with_retry(
    max_attempts: int = 3,
    delay_seconds: float = 1.0,
    backoff_multiplier: float = 2.0,
    retry_on: Tuple[type, ...] = (Exception,),
    context: str = ""
) -> Callable:
    """
    Decorator that adds retry logic with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        delay_seconds: Initial delay between retries
        backoff_multiplier: Multiplier for delay after each attempt
        retry_on: Exception types to retry on
        context: Context string for logging

    Example:
        @with_retry(max_attempts=3, retry_on=(LLMInferenceError,))
        def llm_inference(text: str) -> str:
            # Function that might need retrying
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            current_delay = delay_seconds

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e

                    if attempt == max_attempts - 1:
                        # Last attempt failed
                        break

                    # Log retry attempt
                    context_str = f" [{context}]" if context else ""
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed{context_str}: "
                        f"{type(e).__name__}. Retrying in {current_delay:.1f}s..."
                    )

                    # Record retry metric
                    if is_monitoring_enabled():
                        metrics = get_metrics_collector()
                        metrics.increment_counter("retries_attempted")
                        metrics.increment_counter(f"retry_{type(e).__name__}")

                    # Wait before retry
                    time.sleep(current_delay)
                    current_delay *= backoff_multiplier

                except Exception as e:
                    # Non-retryable exception
                    raise e

            # All attempts failed
            context_str = f" [{context}]" if context else ""
            logger.error(f"All {max_attempts} retry attempts failed{context_str}")

            if is_monitoring_enabled():
                metrics = get_metrics_collector()
                metrics.increment_counter("retries_exhausted")

            raise last_exception

        return wrapper
    return decorator