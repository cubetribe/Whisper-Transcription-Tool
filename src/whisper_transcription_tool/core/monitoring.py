"""
Monitoring and metrics collection for the Whisper Transcription Tool.

This module provides optional monitoring capabilities including performance metrics,
memory usage tracking, and error reporting.
"""

import json
import os
import psutil
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from contextlib import contextmanager

from .logging_setup import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceMetric:
    """Individual performance metric data."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class OperationMetrics:
    """Metrics for a complete operation."""
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    success: bool = True
    error_type: Optional[str] = None
    memory_peak_mb: Optional[float] = None
    memory_start_mb: Optional[float] = None
    memory_end_mb: Optional[float] = None
    custom_metrics: Dict[str, Any] = field(default_factory=dict)

    def finish(self, success: bool = True, error_type: Optional[str] = None):
        """Mark operation as finished."""
        self.end_time = datetime.now()
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()
        self.success = success
        self.error_type = error_type

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


class MetricsCollector:
    """
    Collects and manages performance metrics.
    """

    def __init__(self, enabled: bool = False, max_metrics: int = 1000):
        self.enabled = enabled
        self.max_metrics = max_metrics
        self._metrics: deque = deque(maxlen=max_metrics)
        self._operations: Dict[str, OperationMetrics] = {}
        self._counters: Dict[str, int] = defaultdict(int)
        self._timers: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()

        # Memory monitoring
        self._process = psutil.Process() if enabled else None
        self._memory_samples: deque = deque(maxlen=100)  # Last 100 memory samples

        logger.info(f"Metrics collection {'ENABLED' if enabled else 'DISABLED'}")

    def is_enabled(self) -> bool:
        """Check if monitoring is enabled."""
        return self.enabled

    def record_metric(self, name: str, value: float, unit: str = "", metadata: Optional[Dict] = None) -> None:
        """
        Record a performance metric.

        Args:
            name: Metric name
            value: Metric value
            unit: Unit of measurement
            metadata: Additional metadata
        """
        if not self.enabled:
            return

        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )

        with self._lock:
            self._metrics.append(metric)

        logger.debug(f"Metric recorded: {name}={value}{unit}")

    def start_operation(self, operation_name: str, metadata: Optional[Dict] = None) -> str:
        """
        Start tracking an operation.

        Args:
            operation_name: Name of the operation
            metadata: Additional metadata

        Returns:
            Operation ID for tracking
        """
        if not self.enabled:
            return ""

        operation_id = f"{operation_name}_{int(time.time() * 1000)}"

        # Record initial memory usage
        memory_mb = self.get_memory_usage_mb() if self._process else None

        operation_metrics = OperationMetrics(
            operation_name=operation_name,
            start_time=datetime.now(),
            memory_start_mb=memory_mb,
            custom_metrics=metadata or {}
        )

        with self._lock:
            self._operations[operation_id] = operation_metrics

        logger.debug(f"Started operation tracking: {operation_name} (ID: {operation_id})")
        return operation_id

    def finish_operation(self, operation_id: str, success: bool = True, error_type: Optional[str] = None) -> None:
        """
        Finish tracking an operation.

        Args:
            operation_id: Operation ID from start_operation
            success: Whether the operation succeeded
            error_type: Type of error if operation failed
        """
        if not self.enabled or not operation_id:
            return

        with self._lock:
            if operation_id not in self._operations:
                logger.warning(f"Unknown operation ID: {operation_id}")
                return

            operation = self._operations[operation_id]

            # Record final memory usage and peak
            if self._process:
                operation.memory_end_mb = self.get_memory_usage_mb()
                operation.memory_peak_mb = max(
                    sample.value for sample in self._memory_samples
                    if sample.timestamp >= operation.start_time
                ) if self._memory_samples else operation.memory_end_mb

            operation.finish(success, error_type)

            # Record duration metric
            if operation.duration_seconds:
                self.record_metric(
                    f"{operation.operation_name}_duration",
                    operation.duration_seconds,
                    "seconds",
                    {"success": success, "error_type": error_type}
                )

            # Record memory usage if available
            if operation.memory_peak_mb:
                self.record_metric(
                    f"{operation.operation_name}_memory_peak",
                    operation.memory_peak_mb,
                    "MB"
                )

            # Clean up
            del self._operations[operation_id]

        logger.debug(f"Finished operation tracking: {operation.operation_name} (Duration: {operation.duration_seconds:.2f}s)")

    @contextmanager
    def operation_timer(self, operation_name: str, metadata: Optional[Dict] = None):
        """
        Context manager for timing operations.

        Args:
            operation_name: Name of the operation
            metadata: Additional metadata

        Example:
            with metrics.operation_timer("text_correction"):
                # perform operation
                pass
        """
        operation_id = self.start_operation(operation_name, metadata)
        success = True
        error_type = None

        try:
            yield
        except Exception as e:
            success = False
            error_type = type(e).__name__
            raise
        finally:
            self.finish_operation(operation_id, success, error_type)

    def increment_counter(self, counter_name: str, increment: int = 1) -> None:
        """
        Increment a counter metric.

        Args:
            counter_name: Name of the counter
            increment: Amount to increment by
        """
        if not self.enabled:
            return

        with self._lock:
            self._counters[counter_name] += increment

        logger.debug(f"Counter incremented: {counter_name} += {increment} (now: {self._counters[counter_name]})")

    def record_timer(self, timer_name: str, duration_seconds: float) -> None:
        """
        Record a timer measurement.

        Args:
            timer_name: Name of the timer
            duration_seconds: Duration in seconds
        """
        if not self.enabled:
            return

        with self._lock:
            self._timers[timer_name].append(duration_seconds)
            # Keep only last 100 measurements per timer
            if len(self._timers[timer_name]) > 100:
                self._timers[timer_name] = self._timers[timer_name][-100:]

        self.record_metric(timer_name, duration_seconds, "seconds")

    def get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        if not self.enabled or not self._process:
            return 0.0

        try:
            memory_info = self._process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024  # Convert bytes to MB

            # Store sample for peak tracking
            sample = PerformanceMetric(
                name="memory_usage",
                value=memory_mb,
                unit="MB",
                timestamp=datetime.now()
            )

            with self._lock:
                self._memory_samples.append(sample)

            return memory_mb
        except Exception as e:
            logger.warning(f"Failed to get memory usage: {e}")
            return 0.0

    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get a summary of collected metrics.

        Returns:
            Dictionary with metrics summary
        """
        if not self.enabled:
            return {"monitoring_enabled": False}

        with self._lock:
            # Calculate timer statistics
            timer_stats = {}
            for name, times in self._timers.items():
                if times:
                    timer_stats[name] = {
                        "count": len(times),
                        "avg": sum(times) / len(times),
                        "min": min(times),
                        "max": max(times)
                    }

            # Get recent metrics
            recent_metrics = [m.to_dict() for m in list(self._metrics)[-50:]]  # Last 50 metrics

            return {
                "monitoring_enabled": True,
                "total_metrics": len(self._metrics),
                "counters": dict(self._counters),
                "timer_stats": timer_stats,
                "active_operations": len(self._operations),
                "current_memory_mb": self.get_memory_usage_mb(),
                "recent_metrics": recent_metrics
            }

    def export_metrics(self, file_path: Optional[str] = None) -> str:
        """
        Export metrics to a JSON file.

        Args:
            file_path: Path to export file. If None, uses default location.

        Returns:
            Path to the exported file
        """
        if not self.enabled:
            return ""

        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_dir = Path.home() / ".whisper_tool" / "metrics"
            export_dir.mkdir(parents=True, exist_ok=True)
            file_path = str(export_dir / f"metrics_{timestamp}.json")

        metrics_data = self.get_metrics_summary()

        # Add all metrics details
        with self._lock:
            metrics_data["all_metrics"] = [m.to_dict() for m in self._metrics]

        try:
            with open(file_path, 'w') as f:
                json.dump(metrics_data, f, indent=2, default=str)

            logger.info(f"Metrics exported to: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
            return ""

    def clear_metrics(self) -> None:
        """Clear all collected metrics."""
        if not self.enabled:
            return

        with self._lock:
            self._metrics.clear()
            self._counters.clear()
            self._timers.clear()
            self._memory_samples.clear()

        logger.info("All metrics cleared")


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def initialize_monitoring(enabled: bool = False, config: Optional[Dict] = None) -> MetricsCollector:
    """
    Initialize the global metrics collector.

    Args:
        enabled: Whether to enable monitoring
        config: Configuration dictionary

    Returns:
        MetricsCollector instance
    """
    global _metrics_collector

    # Check config for monitoring settings
    if config and "monitoring" in config:
        monitoring_config = config["monitoring"]
        enabled = monitoring_config.get("enabled", enabled)
        max_metrics = monitoring_config.get("max_metrics", 1000)
    else:
        max_metrics = 1000

    _metrics_collector = MetricsCollector(enabled=enabled, max_metrics=max_metrics)
    return _metrics_collector


def get_metrics_collector() -> Optional[MetricsCollector]:
    """
    Get the global metrics collector.

    Returns:
        MetricsCollector instance or None if not initialized
    """
    return _metrics_collector


def is_monitoring_enabled() -> bool:
    """
    Check if monitoring is enabled.

    Returns:
        True if monitoring is enabled, False otherwise
    """
    return _metrics_collector is not None and _metrics_collector.is_enabled()


# Convenience functions for common metrics
def record_correction_duration(duration_seconds: float, success: bool = True, model_name: str = "unknown"):
    """Record text correction duration metric."""
    if _metrics_collector and _metrics_collector.is_enabled():
        _metrics_collector.record_metric(
            "correction_duration_seconds",
            duration_seconds,
            "seconds",
            {"success": success, "model": model_name}
        )


def record_memory_usage():
    """Record current memory usage metric."""
    if _metrics_collector and _metrics_collector.is_enabled():
        memory_mb = _metrics_collector.get_memory_usage_mb()
        _metrics_collector.record_metric("memory_usage", memory_mb, "MB")


def increment_correction_count(success: bool = True):
    """Increment correction operation counter."""
    if _metrics_collector and _metrics_collector.is_enabled():
        counter_name = "corrections_successful" if success else "corrections_failed"
        _metrics_collector.increment_counter(counter_name)


@contextmanager
def text_correction_timer(model_name: str = "unknown"):
    """Context manager for timing text correction operations."""
    if _metrics_collector and _metrics_collector.is_enabled():
        with _metrics_collector.operation_timer(
            "text_correction",
            metadata={"model": model_name}
        ):
            yield
    else:
        yield