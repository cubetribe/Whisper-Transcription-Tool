"""
Telemetry integration module for the Whisper Transcription Tool.

This module provides a unified interface for error handling, logging, and monitoring.
It demonstrates how to use all the telemetry features together.
"""

import time
from typing import Dict, Optional, Any, List
from contextlib import contextmanager

from .exceptions import (
    ModelNotFoundError,
    InsufficientMemoryError,
    ModelLoadError,
    ChunkingError,
    LLMInferenceError
)
from .logging_setup import setup_logging, get_text_correction_logger, log_exception
from .monitoring import initialize_monitoring, text_correction_timer, record_correction_duration
from .error_recovery import get_recovery_manager, with_error_recovery, with_retry


class TelemetryManager:
    """
    Centralized manager for all telemetry features.
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.monitoring_enabled = False
        self.text_logger = None
        self.recovery_manager = None

        # Initialize all telemetry components
        self._initialize_components()

    def _initialize_components(self):
        """Initialize all telemetry components based on configuration."""

        # Initialize logging
        logging_config = self.config.get("logging", {})
        setup_logging(
            log_level=logging_config.get("level", "INFO"),
            log_file=logging_config.get("file"),
            enable_privacy_filtering=logging_config.get("privacy_filtering", True),
            config=self.config
        )

        # Initialize monitoring
        monitoring_config = self.config.get("monitoring", {})
        self.monitoring_enabled = monitoring_config.get("enabled", False)

        if self.monitoring_enabled:
            initialize_monitoring(enabled=True, config=self.config)

        # Initialize text correction logger
        self.text_logger = get_text_correction_logger()

        # Initialize recovery manager
        self.recovery_manager = get_recovery_manager()

    def is_monitoring_enabled(self) -> bool:
        """Check if monitoring is enabled."""
        return self.monitoring_enabled

    @contextmanager
    def text_correction_operation(
        self,
        text: str,
        model_name: str = "unknown",
        operation_context: str = "text_correction"
    ):
        """
        Context manager for complete text correction telemetry.

        This handles logging, monitoring, and error recovery for text correction operations.

        Args:
            text: Text being corrected
            model_name: Name of the model being used
            operation_context: Context for error recovery

        Example:
            with telemetry.text_correction_operation(text, "llama2-7b"):
                corrected_text = perform_correction(text)
        """
        start_time = time.time()
        text_length = len(text)

        # Start logging
        self.text_logger.log_correction_start(text_length, model_name)

        # Start monitoring if enabled
        monitoring_context = None
        if self.monitoring_enabled:
            monitoring_context = text_correction_timer(model_name)
            monitoring_context.__enter__()

        success = False
        partial = False
        error_occurred = None

        try:
            yield

            # Operation completed successfully
            success = True

        except (ModelNotFoundError, InsufficientMemoryError, ModelLoadError) as e:
            # Recoverable model errors - log and handle gracefully
            error_occurred = e
            success = False

            # Attempt recovery
            recovery_result = self.recovery_manager.recover_from_error(
                error=e,
                context=operation_context,
                fallback_result=text  # Use original text as fallback
            )

            if recovery_result.success:
                success = True
                self.text_logger.logger.info(f"Recovery successful: {recovery_result.message}")

        except (ChunkingError, LLMInferenceError) as e:
            # Errors that might have partial results
            error_occurred = e
            success = False

            # Check for partial results
            partial_result = getattr(e, 'details', {}).get('partial_result')
            if partial_result:
                partial = True
                success = True

            # Attempt recovery
            recovery_result = self.recovery_manager.recover_from_error(
                error=e,
                context=operation_context,
                fallback_result=text
            )

            if recovery_result.success:
                success = True
                if recovery_result.recovery_action_taken.value == "continue":
                    partial = True

        except Exception as e:
            # Unexpected errors
            error_occurred = e
            success = False
            log_exception(self.text_logger.logger, e, operation_context)

        finally:
            # Calculate duration
            duration = time.time() - start_time

            # Complete logging
            self.text_logger.log_correction_complete(duration, success, partial)

            # Complete monitoring
            if monitoring_context:
                try:
                    monitoring_context.__exit__(
                        type(error_occurred) if error_occurred else None,
                        error_occurred,
                        None
                    )
                except:
                    pass  # Don't let monitoring errors affect the main operation

            # Record duration metric
            if self.monitoring_enabled:
                record_correction_duration(duration, success, model_name)

    def get_telemetry_status(self) -> Dict[str, Any]:
        """Get current telemetry system status."""
        from .monitoring import get_metrics_collector

        status = {
            "logging_enabled": True,  # Always enabled
            "monitoring_enabled": self.monitoring_enabled,
            "privacy_filtering_enabled": True,  # Default
            "recovery_manager_initialized": self.recovery_manager is not None
        }

        # Add recovery statistics if available
        if self.recovery_manager:
            status["recovery_stats"] = self.recovery_manager.get_recovery_stats()

        # Add monitoring statistics if enabled
        if self.monitoring_enabled:
            metrics_collector = get_metrics_collector()
            if metrics_collector:
                status["metrics_summary"] = metrics_collector.get_metrics_summary()

        return status

    def export_telemetry_data(self, file_path: Optional[str] = None) -> str:
        """
        Export all telemetry data to a file.

        Args:
            file_path: Path to export file

        Returns:
            Path to exported file
        """
        if not self.monitoring_enabled:
            return ""

        from .monitoring import get_metrics_collector

        metrics_collector = get_metrics_collector()
        if metrics_collector:
            return metrics_collector.export_metrics(file_path)

        return ""

    def configure_custom_recovery(self, error_type: type, strategy_func):
        """
        Register a custom recovery strategy.

        Args:
            error_type: Exception type to handle
            strategy_func: Recovery strategy function
        """
        if self.recovery_manager:
            self.recovery_manager.register_recovery_strategy(error_type, strategy_func)

    def configure_fallback_handler(self, context: str, handler_func):
        """
        Register a fallback handler for a specific context.

        Args:
            context: Context string
            handler_func: Fallback handler function
        """
        if self.recovery_manager:
            self.recovery_manager.register_fallback_handler(context, handler_func)


# Global telemetry manager instance
_telemetry_manager: Optional[TelemetryManager] = None


def initialize_telemetry(config: Optional[Dict] = None) -> TelemetryManager:
    """
    Initialize the global telemetry manager.

    Args:
        config: Configuration dictionary

    Returns:
        TelemetryManager instance

    Example config:
    {
        "logging": {
            "level": "INFO",
            "file": "/path/to/log.txt",
            "privacy_filtering": True
        },
        "monitoring": {
            "enabled": True,
            "max_metrics": 1000
        }
    }
    """
    global _telemetry_manager
    _telemetry_manager = TelemetryManager(config)
    return _telemetry_manager


def get_telemetry_manager() -> Optional[TelemetryManager]:
    """Get the global telemetry manager."""
    return _telemetry_manager


# Convenience decorators that use the global telemetry manager

def monitored_text_correction(
    model_name: str = "unknown",
    context: str = "text_correction"
):
    """
    Decorator for text correction functions that adds full telemetry.

    Args:
        model_name: Name of the model being used
        context: Context for error recovery

    Example:
        @monitored_text_correction(model_name="llama2-7b")
        def correct_text_with_llm(text: str, model: str) -> str:
            # Function implementation
            return corrected_text
    """
    def decorator(func):
        @with_error_recovery(context=context, fallback_result="")
        @with_retry(max_attempts=2, retry_on=(LLMInferenceError,))
        def wrapper(text: str, *args, **kwargs):
            telemetry = get_telemetry_manager()

            if telemetry:
                with telemetry.text_correction_operation(text, model_name, context):
                    return func(text, *args, **kwargs)
            else:
                # No telemetry manager, run function directly
                return func(text, *args, **kwargs)

        return wrapper
    return decorator


def safe_model_operation(
    operation_name: str = "model_operation",
    fallback_result: Any = None
):
    """
    Decorator that adds comprehensive error handling to model operations.

    Args:
        operation_name: Name of the operation for logging
        fallback_result: Result to return if operation fails

    Example:
        @safe_model_operation("model_loading", fallback_result=None)
        def load_model(model_path: str):
            # Model loading implementation
            return model
    """
    def decorator(func):
        @with_error_recovery(context=operation_name, fallback_result=fallback_result)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper
    return decorator


# Example usage functions

def example_text_correction_with_telemetry():
    """
    Example of how to use the telemetry system for text correction.
    """
    # Initialize telemetry
    config = {
        "logging": {
            "level": "INFO",
            "privacy_filtering": True
        },
        "monitoring": {
            "enabled": True
        }
    }

    telemetry = initialize_telemetry(config)

    # Example text correction operation
    text = "This is som text with speling errors."
    model_name = "llama2-7b"

    try:
        with telemetry.text_correction_operation(text, model_name):
            # Simulate text correction (this would be real LLM inference)
            time.sleep(0.1)  # Simulate processing time

            # Simulate different error scenarios for demonstration
            import random
            error_chance = random.choice([0, 1, 2, 3])

            if error_chance == 1:
                raise ModelNotFoundError(model_name)
            elif error_chance == 2:
                raise InsufficientMemoryError(required_memory=8000, available_memory=4000)
            elif error_chance == 3:
                raise LLMInferenceError(
                    "Inference failed",
                    partial_result="This is some text with spelling"  # Partial correction
                )

            # Success case
            corrected_text = "This is some text with spelling errors."
            return corrected_text

    except Exception as e:
        print(f"Operation failed: {e}")
        return text  # Return original text as fallback

    finally:
        # Get telemetry status
        status = telemetry.get_telemetry_status()
        print("Telemetry Status:", status)


def example_decorated_function():
    """Example of using telemetry decorators."""

    @monitored_text_correction(model_name="phi-2")
    def correct_text(text: str) -> str:
        # Simulate text correction
        time.sleep(0.05)

        # Simulate potential error
        if "error" in text.lower():
            raise LLMInferenceError("Simulated inference error")

        return text.replace("error", "correction")

    @safe_model_operation("model_loading", fallback_result=None)
    def load_model(model_path: str):
        # Simulate model loading
        if not model_path:
            raise ModelNotFoundError("empty_model_path")

        return {"model": "loaded", "path": model_path}

    # Test the decorated functions
    result1 = correct_text("This text has no issues")
    print(f"Correction result: {result1}")

    result2 = load_model("/path/to/model")
    print(f"Model loading result: {result2}")


if __name__ == "__main__":
    # Run examples
    print("=== Text Correction with Telemetry Example ===")
    example_text_correction_with_telemetry()

    print("\n=== Decorated Functions Example ===")
    example_decorated_function()