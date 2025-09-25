"""
Resource Manager for Whisper Transcription Tool

This module provides a thread-safe singleton ResourceManager that handles:
- Memory monitoring and management
- Model loading/unloading with resource constraints
- Thread-safe model swapping between Whisper and LeoLM
- GPU acceleration detection
- Performance metrics collection

Author: ResourceSentinel Agent
Version: 1.0.0
"""

import threading
import psutil
import gc
import subprocess
import platform
import time
import logging
import os
import signal
from typing import Optional, Dict, Any, Union, List, Tuple
from enum import Enum
from dataclasses import dataclass
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

class ModelType(Enum):
    """Supported model types for resource management"""
    WHISPER = "whisper"
    LEOLM = "leolm"

@dataclass
class ResourceConstraints:
    """Resource constraints for different models"""
    min_memory_gb: float
    preferred_memory_gb: float
    gpu_required: bool = False
    max_concurrent: int = 1

@dataclass
class ModelResource:
    """Container for model instance and metadata"""
    instance: Union[subprocess.Popen, Any]  # Any for llama_cpp.Llama
    process_id: Optional[int]
    memory_usage: float
    load_time: float
    last_used: float

@dataclass
class PerformanceMetrics:
    """Performance metrics for model operations"""
    model_loads: int = 0
    model_unloads: int = 0
    memory_cleanups: int = 0
    swaps_performed: int = 0
    total_load_time: float = 0.0
    total_unload_time: float = 0.0
    peak_memory_usage: float = 0.0
    current_memory_usage: float = 0.0

class ResourceManager:
    """
    Thread-safe singleton ResourceManager for managing system resources and models.

    Features:
    - Singleton pattern with thread safety
    - Memory monitoring with configurable thresholds
    - Model resource mapping and lifecycle management
    - GPU acceleration detection (Metal on macOS)
    - Thread-safe model locks and swapping
    - Performance metrics collection
    - Automatic cleanup and garbage collection
    """

    _instance = None
    _lock = threading.Lock()
    _initialized = False

    # Resource constraints for different models
    RESOURCE_CONSTRAINTS = {
        ModelType.WHISPER: ResourceConstraints(
            min_memory_gb=2.0,
            preferred_memory_gb=4.0,
            gpu_required=False,
            max_concurrent=2
        ),
        ModelType.LEOLM: ResourceConstraints(
            min_memory_gb=6.0,
            preferred_memory_gb=8.0,
            gpu_required=False,
            max_concurrent=1
        )
    }

    def __new__(cls):
        """Thread-safe singleton implementation"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize ResourceManager (only once due to singleton pattern)"""
        if self._initialized:
            return

        with self._lock:
            if self._initialized:
                return

            # Model resource tracking
            self.active_models: Dict[ModelType, ModelResource] = {}
            self.model_locks: Dict[ModelType, threading.Lock] = {
                ModelType.WHISPER: threading.Lock(),
                ModelType.LEOLM: threading.Lock()
            }

            # System resource detection
            self.gpu_acceleration = self._detect_gpu_acceleration()
            self.system_memory_gb = psutil.virtual_memory().total / (1024**3)

            # Performance monitoring
            self.monitoring_enabled = False
            self.metrics = PerformanceMetrics()
            self._metrics_lock = threading.Lock()

            # Memory thresholds
            self.memory_warning_threshold = 0.8  # 80% memory usage
            self.memory_critical_threshold = 0.9  # 90% memory usage

            # Monitoring thread
            self._monitor_thread = None
            self._stop_monitoring = threading.Event()

            self._initialized = True
            logger.info(f"ResourceManager initialized with {self.system_memory_gb:.1f}GB RAM, GPU: {self.gpu_acceleration}")

    def _detect_gpu_acceleration(self) -> str:
        """
        Detect available GPU acceleration

        Returns:
            str: "metal" for macOS, "cuda" for NVIDIA, "cpu" for no GPU
        """
        import platform
        system = platform.system().lower()

        if system == "darwin":  # macOS
            # Check for Metal Performance Shaders availability
            try:
                # Simple check for macOS version that supports Metal
                version = platform.mac_ver()[0]
                if version:
                    major, minor = map(int, version.split('.')[:2])
                    if major >= 10 and minor >= 11:  # macOS 10.11+ supports Metal
                        return "metal"
            except Exception:
                pass
            return "cpu"

        elif system == "linux":
            # Check for NVIDIA GPU
            try:
                result = subprocess.run(["nvidia-smi"],
                                      capture_output=True,
                                      text=True,
                                      timeout=5)
                if result.returncode == 0:
                    return "cuda"
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            return "cpu"

        else:  # Windows or other
            # Add Windows CUDA detection if needed
            return "cpu"

    def check_available_memory(self) -> Dict[str, float]:
        """
        Check available system memory in GB

        Returns:
            Dict[str, float]: Memory information including total, available, used, and percentage
        """
        memory = psutil.virtual_memory()
        return {
            "total_gb": memory.total / (1024**3),
            "available_gb": memory.available / (1024**3),
            "used_gb": memory.used / (1024**3),
            "percent_used": memory.percent,
            "free_gb": memory.free / (1024**3)
        }

    def _check_memory_threshold(self) -> Tuple[bool, str]:
        """
        Check if memory usage is within safe thresholds

        Returns:
            Tuple[bool, str]: (is_safe, warning_message)
        """
        memory_info = self.check_available_memory()
        percent_used = memory_info["percent_used"] / 100.0

        if percent_used >= self.memory_critical_threshold:
            return False, f"Critical memory usage: {percent_used:.1%}"
        elif percent_used >= self.memory_warning_threshold:
            return False, f"High memory usage: {percent_used:.1%}"
        else:
            return True, ""

    def request_model(self, model_type: ModelType, config: Dict[str, Any] = None) -> bool:
        """
        Request exclusive access to model with resource checking

        Args:
            model_type (ModelType): Type of model to request
            config (Dict[str, Any], optional): Model configuration parameters

        Returns:
            bool: True if model was successfully loaded, False otherwise
        """
        config = config or {}

        # Check if already loaded
        if model_type in self.active_models:
            self.active_models[model_type].last_used = time.time()
            logger.debug(f"{model_type.value} model already loaded")
            return True

        # Get model lock
        with self.model_locks[model_type]:
            # Double-check after acquiring lock
            if model_type in self.active_models:
                self.active_models[model_type].last_used = time.time()
                return True

            # Check resource constraints
            constraints = self.RESOURCE_CONSTRAINTS[model_type]
            memory_info = self.check_available_memory()

            if memory_info["available_gb"] < constraints.min_memory_gb:
                logger.warning(f"Insufficient memory for {model_type.value}: "
                             f"{memory_info['available_gb']:.1f}GB available, "
                             f"{constraints.min_memory_gb:.1f}GB required")

                # Try cleanup and retry once
                self.force_cleanup()
                memory_info = self.check_available_memory()

                if memory_info["available_gb"] < constraints.min_memory_gb:
                    return False

            # Load model
            start_time = time.time()
            try:
                model_instance = self._load_model(model_type, config)
                load_time = time.time() - start_time

                # Create resource record
                memory_after = self.check_available_memory()
                memory_used = memory_info["available_gb"] - memory_after["available_gb"]

                self.active_models[model_type] = ModelResource(
                    instance=model_instance,
                    process_id=getattr(model_instance, 'pid', None),
                    memory_usage=memory_used,
                    load_time=load_time,
                    last_used=time.time()
                )

                # Update metrics
                if self.monitoring_enabled:
                    with self._metrics_lock:
                        self.metrics.model_loads += 1
                        self.metrics.total_load_time += load_time
                        current_used = memory_after["used_gb"]
                        self.metrics.current_memory_usage = current_used
                        if current_used > self.metrics.peak_memory_usage:
                            self.metrics.peak_memory_usage = current_used

                logger.info(f"Successfully loaded {model_type.value} model in {load_time:.2f}s, "
                           f"using {memory_used:.1f}GB memory")
                return True

            except Exception as e:
                logger.error(f"Failed to load {model_type.value} model: {e}")
                return False

    def _load_model(self, model_type: ModelType, config: Dict[str, Any]) -> Union[subprocess.Popen, Any]:
        """
        Load specific model type

        Args:
            model_type (ModelType): Type of model to load
            config (Dict[str, Any]): Model configuration

        Returns:
            Union[subprocess.Popen, Any]: Loaded model instance
        """
        if model_type == ModelType.WHISPER:
            return self._load_whisper_model(config)
        elif model_type == ModelType.LEOLM:
            return self._load_leolm_model(config)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")

    def _load_whisper_model(self, config: Dict[str, Any]) -> subprocess.Popen:
        """
        Load Whisper model as subprocess

        Args:
            config (Dict[str, Any]): Whisper configuration

        Returns:
            subprocess.Popen: Whisper subprocess
        """
        # Default whisper command (this would be customized based on actual usage)
        whisper_cmd = config.get('whisper_cmd', [
            'whisper-cli',
            '--model', config.get('model', 'large-v3-turbo'),
            '--output-format', 'json'
        ])

        # Start subprocess with proper settings
        process = subprocess.Popen(
            whisper_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        return process

    def _load_leolm_model(self, config: Dict[str, Any]) -> Any:
        """
        Load LeoLM model using llama_cpp

        Args:
            config (Dict[str, Any]): LeoLM configuration

        Returns:
            Any: llama_cpp.Llama instance (using Any to avoid import issues)
        """
        try:
            # Import llama_cpp only when needed
            import llama_cpp

            # Configure model parameters
            model_path = config.get('model_path', 'models/leolm-7b.gguf')
            n_ctx = config.get('n_ctx', 2048)
            n_threads = config.get('n_threads', None)

            # Configure GPU layers based on acceleration
            n_gpu_layers = 0
            if self.gpu_acceleration == "metal":
                n_gpu_layers = config.get('n_gpu_layers', 35)  # Use GPU acceleration

            # Load model
            llm = llama_cpp.Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_threads=n_threads,
                n_gpu_layers=n_gpu_layers,
                verbose=False
            )

            return llm

        except ImportError:
            logger.error("llama_cpp not available. Please install llama-cpp-python")
            raise
        except Exception as e:
            logger.error(f"Failed to load LeoLM model: {e}")
            raise

    def release_model(self, model_type: ModelType) -> None:
        """
        Release model and free resources

        Resource Cleanup Strategy:
        - WHISPER: Terminate subprocess, wait for cleanup
        - LEOLM: Call destructor, force garbage collection

        Args:
            model_type (ModelType): Type of model to release
        """
        if model_type not in self.active_models:
            logger.debug(f"{model_type.value} model not loaded, nothing to release")
            return

        with self.model_locks[model_type]:
            if model_type not in self.active_models:
                return

            start_time = time.time()
            resource = self.active_models[model_type]

            try:
                if model_type == ModelType.WHISPER:
                    self._release_whisper_model(resource)
                elif model_type == ModelType.LEOLM:
                    self._release_leolm_model(resource)

                # Remove from active models
                del self.active_models[model_type]

                unload_time = time.time() - start_time

                # Update metrics
                if self.monitoring_enabled:
                    with self._metrics_lock:
                        self.metrics.model_unloads += 1
                        self.metrics.total_unload_time += unload_time
                        self.metrics.current_memory_usage = self.check_available_memory()["used_gb"]

                logger.info(f"Released {model_type.value} model in {unload_time:.2f}s, "
                           f"freed {resource.memory_usage:.1f}GB memory")

            except Exception as e:
                logger.error(f"Error releasing {model_type.value} model: {e}")
                # Force removal even if cleanup failed
                if model_type in self.active_models:
                    del self.active_models[model_type]

    def _release_whisper_model(self, resource: ModelResource) -> None:
        """
        Release Whisper subprocess

        Args:
            resource (ModelResource): Whisper model resource
        """
        process = resource.instance

        if isinstance(process, subprocess.Popen):
            try:
                # Try graceful termination first
                process.terminate()

                # Wait for process to end with timeout
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't terminate gracefully
                    process.kill()
                    process.wait(timeout=2)

            except Exception as e:
                logger.warning(f"Error terminating Whisper process: {e}")
                # Try force kill as last resort
                try:
                    if process.poll() is None:  # Still running
                        os.kill(process.pid, signal.SIGKILL)
                except:
                    pass

    def _release_leolm_model(self, resource: ModelResource) -> None:
        """
        Release LeoLM model

        Args:
            resource (ModelResource): LeoLM model resource
        """
        llm_instance = resource.instance

        try:
            # Call destructor if available
            if hasattr(llm_instance, '__del__'):
                llm_instance.__del__()

            # Clear reference
            del llm_instance

            # Force garbage collection
            gc.collect()

        except Exception as e:
            logger.warning(f"Error releasing LeoLM model: {e}")

    def swap_models(self, from_model: ModelType, to_model: ModelType, config: Dict[str, Any] = None) -> bool:
        """
        Safely swap between models with resource management

        Args:
            from_model (ModelType): Model to unload
            to_model (ModelType): Model to load
            config (Dict[str, Any], optional): Configuration for new model

        Returns:
            bool: True if swap was successful
        """
        config = config or {}

        # Check memory safety before starting swap
        is_safe, warning = self._check_memory_threshold()
        if not is_safe:
            logger.warning(f"Memory threshold exceeded before swap: {warning}")
            self.force_cleanup()

        start_time = time.time()
        success = False

        try:
            # Step 1: Release the from_model
            if from_model in self.active_models:
                logger.info(f"Releasing {from_model.value} model for swap")
                self.release_model(from_model)

            # Step 2: Wait for cleanup (2-3 seconds as specified)
            time.sleep(2.5)

            # Step 3: Force garbage collection
            gc.collect()

            # Step 4: Load the to_model
            logger.info(f"Loading {to_model.value} model for swap")
            success = self.request_model(to_model, config)

            if success:
                swap_time = time.time() - start_time

                # Update metrics
                if self.monitoring_enabled:
                    with self._metrics_lock:
                        self.metrics.swaps_performed += 1

                logger.info(f"Successfully swapped from {from_model.value} to {to_model.value} "
                           f"in {swap_time:.2f}s")
            else:
                logger.error(f"Failed to load {to_model.value} during swap")

        except Exception as e:
            logger.error(f"Error during model swap: {e}")
            success = False

        return success

    def force_cleanup(self) -> None:
        """
        Force garbage collection and memory cleanup
        """
        logger.info("Performing forced cleanup")

        # Run multiple garbage collection cycles
        for i in range(3):
            collected = gc.collect()
            if collected > 0:
                logger.debug(f"GC cycle {i+1}: collected {collected} objects")

        # Update metrics
        if self.monitoring_enabled:
            with self._metrics_lock:
                self.metrics.memory_cleanups += 1
                self.metrics.current_memory_usage = self.check_available_memory()["used_gb"]

        memory_info = self.check_available_memory()
        logger.info(f"Cleanup completed, memory usage: {memory_info['percent_used']:.1f}% "
                   f"({memory_info['used_gb']:.1f}GB used)")

    def enable_monitoring(self, continuous: bool = False) -> None:
        """
        Enable performance monitoring and metrics collection

        Args:
            continuous (bool): Enable continuous monitoring in background thread
        """
        self.monitoring_enabled = True
        logger.info("Performance monitoring enabled")

        if continuous and self._monitor_thread is None:
            self._stop_monitoring.clear()
            self._monitor_thread = threading.Thread(
                target=self._continuous_monitoring,
                daemon=True,
                name="ResourceMonitor"
            )
            self._monitor_thread.start()
            logger.info("Continuous monitoring thread started")

    def disable_monitoring(self) -> None:
        """Disable performance monitoring"""
        self.monitoring_enabled = False

        if self._monitor_thread is not None:
            self._stop_monitoring.set()
            self._monitor_thread.join(timeout=5)
            self._monitor_thread = None

        logger.info("Performance monitoring disabled")

    def _continuous_monitoring(self) -> None:
        """Continuous monitoring loop (runs in background thread)"""
        while not self._stop_monitoring.wait(10):  # Check every 10 seconds
            try:
                memory_info = self.check_available_memory()

                # Update current memory usage
                if self.monitoring_enabled:
                    with self._metrics_lock:
                        current_usage = memory_info["used_gb"]
                        self.metrics.current_memory_usage = current_usage
                        if current_usage > self.metrics.peak_memory_usage:
                            self.metrics.peak_memory_usage = current_usage

                # Check for memory pressure
                is_safe, warning = self._check_memory_threshold()
                if not is_safe:
                    logger.warning(f"Memory pressure detected: {warning}")

                    # Auto-cleanup if critical
                    if memory_info["percent_used"] > self.memory_critical_threshold * 100:
                        logger.warning("Critical memory usage, performing auto-cleanup")
                        self.force_cleanup()

            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get collected performance metrics

        Returns:
            Dict[str, Any]: Current performance metrics
        """
        if not self.monitoring_enabled:
            return {}

        with self._metrics_lock:
            memory_info = self.check_available_memory()

            return {
                "model_loads": self.metrics.model_loads,
                "model_unloads": self.metrics.model_unloads,
                "memory_cleanups": self.metrics.memory_cleanups,
                "swaps_performed": self.metrics.swaps_performed,
                "total_load_time": self.metrics.total_load_time,
                "total_unload_time": self.metrics.total_unload_time,
                "average_load_time": (self.metrics.total_load_time / max(1, self.metrics.model_loads)),
                "average_unload_time": (self.metrics.total_unload_time / max(1, self.metrics.model_unloads)),
                "peak_memory_usage": self.metrics.peak_memory_usage,
                "current_memory_usage": memory_info["used_gb"],
                "memory_utilization": memory_info["percent_used"],
                "available_memory": memory_info["available_gb"],
                "gpu_acceleration": self.gpu_acceleration,
                "system_memory_gb": self.system_memory_gb,
                "active_models": list(self.active_models.keys()),
                "active_model_count": len(self.active_models)
            }

    def get_status(self) -> Dict[str, Any]:
        """
        Get current ResourceManager status

        Returns:
            Dict[str, Any]: Current status information
        """
        memory_info = self.check_available_memory()
        is_safe, warning = self._check_memory_threshold()

        return {
            "initialized": self._initialized,
            "monitoring_enabled": self.monitoring_enabled,
            "gpu_acceleration": self.gpu_acceleration,
            "memory_safe": is_safe,
            "memory_warning": warning,
            "active_models": {
                model_type.value: {
                    "memory_usage": resource.memory_usage,
                    "load_time": resource.load_time,
                    "last_used": resource.last_used,
                    "process_id": resource.process_id
                }
                for model_type, resource in self.active_models.items()
            },
            "system_info": {
                "total_memory_gb": self.system_memory_gb,
                "current_memory": memory_info,
                "memory_thresholds": {
                    "warning": self.memory_warning_threshold,
                    "critical": self.memory_critical_threshold
                }
            },
            "continuous_monitoring": self._monitor_thread is not None
        }

    def cleanup_all(self) -> None:
        """Release all models and clean up resources"""
        logger.info("Cleaning up all resources")

        # Release all active models
        models_to_release = list(self.active_models.keys())
        for model_type in models_to_release:
            try:
                self.release_model(model_type)
            except Exception as e:
                logger.error(f"Error releasing {model_type.value}: {e}")

        # Stop monitoring
        self.disable_monitoring()

        # Force cleanup
        self.force_cleanup()

        logger.info("All resources cleaned up")

    def __del__(self):
        """Cleanup on destruction"""
        try:
            self.cleanup_all()
        except:
            pass