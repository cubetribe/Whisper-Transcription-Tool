"""
Comprehensive Unit Tests for ResourceManager

Tests cover:
- Singleton pattern implementation and thread safety
- Memory monitoring and threshold checking
- Model loading/unloading for different model types
- Model swapping mechanisms and cleanup
- GPU acceleration detection
- Performance metrics collection
- Thread-safe operations
- Error recovery scenarios
- Resource constraints validation

Author: QualityMarshal Agent
Version: 1.0.0
"""

import pytest
import unittest
import threading
import time
import subprocess
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from pathlib import Path

# Import the classes to test
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.whisper_transcription_tool.module5_text_correction.resource_manager import (
    ResourceManager,
    ModelType,
    ResourceConstraints,
    ModelResource,
    PerformanceMetrics
)


class TestResourceManagerSingleton:
    """Test suite for ResourceManager singleton pattern"""

    def setUp(self):
        """Reset singleton for each test"""
        ResourceManager._instance = None
        ResourceManager._initialized = False

    def tearDown(self):
        """Clean up after each test"""
        try:
            rm = ResourceManager()
            rm.cleanup_all()
        except:
            pass
        ResourceManager._instance = None
        ResourceManager._initialized = False

    def test_singleton_pattern(self):
        """Test that ResourceManager follows singleton pattern"""
        self.setUp()  # Ensure clean state

        rm1 = ResourceManager()
        rm2 = ResourceManager()

        # Should be the same instance
        assert rm1 is rm2
        assert id(rm1) == id(rm2)

        self.tearDown()

    def test_thread_safe_singleton(self):
        """Test singleton pattern is thread-safe"""
        self.setUp()

        instances = []
        exceptions = []

        def create_instance():
            try:
                rm = ResourceManager()
                instances.append(rm)
            except Exception as e:
                exceptions.append(e)

        # Create multiple threads
        threads = [threading.Thread(target=create_instance) for _ in range(10)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # No exceptions should occur
        assert len(exceptions) == 0
        assert len(instances) == 10

        # All instances should be the same object
        first_instance = instances[0]
        for instance in instances[1:]:
            assert instance is first_instance

        self.tearDown()

    def test_singleton_initialization_once(self):
        """Test that singleton is only initialized once"""
        self.setUp()

        with patch.object(ResourceManager, '_initialize_system_info') as mock_init:
            rm1 = ResourceManager()
            rm2 = ResourceManager()

            # Should only be called once
            mock_init.assert_called_once()

        self.tearDown()


class TestResourceManagerSystemInfo:
    """Test suite for system information detection"""

    def setUp(self):
        ResourceManager._instance = None
        ResourceManager._initialized = False

    def tearDown(self):
        try:
            rm = ResourceManager()
            rm.cleanup_all()
        except:
            pass
        ResourceManager._instance = None
        ResourceManager._initialized = False

    def test_gpu_acceleration_detection(self):
        """Test GPU acceleration detection"""
        self.setUp()

        rm = ResourceManager()
        assert isinstance(rm.gpu_acceleration, str)
        assert rm.gpu_acceleration in ["metal", "cuda", "cpu"]

        self.tearDown()

    @patch('platform.system')
    @patch('platform.mac_ver')
    def test_metal_detection_macos(self, mock_mac_ver, mock_system):
        """Test Metal detection on macOS"""
        self.setUp()

        mock_system.return_value = "Darwin"
        mock_mac_ver.return_value = ("11.0.0", "", "")

        rm = ResourceManager()
        assert rm.gpu_acceleration == "metal"

        self.tearDown()

    @patch('platform.system')
    @patch('subprocess.run')
    def test_cuda_detection_linux(self, mock_subprocess, mock_system):
        """Test CUDA detection on Linux"""
        self.setUp()

        mock_system.return_value = "Linux"
        mock_subprocess.return_value = Mock(returncode=0)

        rm = ResourceManager()
        assert rm.gpu_acceleration == "cuda"

        self.tearDown()

    @patch('platform.system')
    def test_cpu_fallback(self, mock_system):
        """Test fallback to CPU when no GPU is detected"""
        self.setUp()

        mock_system.return_value = "Windows"  # No GPU detection implemented

        rm = ResourceManager()
        assert rm.gpu_acceleration == "cpu"

        self.tearDown()


class TestResourceManagerMemoryMonitoring:
    """Test suite for memory monitoring functionality"""

    def setUp(self):
        ResourceManager._instance = None
        ResourceManager._initialized = False

    def tearDown(self):
        try:
            rm = ResourceManager()
            rm.cleanup_all()
        except:
            pass
        ResourceManager._instance = None
        ResourceManager._initialized = False

    @patch('psutil.virtual_memory')
    def test_check_available_memory(self, mock_memory):
        """Test memory checking functionality"""
        self.setUp()

        # Mock memory stats
        mock_memory.return_value = Mock(
            total=16 * 1024**3,      # 16GB
            available=8 * 1024**3,   # 8GB
            used=8 * 1024**3,        # 8GB
            percent=50.0,
            free=8 * 1024**3         # 8GB
        )

        rm = ResourceManager()
        memory_info = rm.check_available_memory()

        required_fields = ["total_gb", "available_gb", "used_gb", "percent_used", "free_gb"]
        for field in required_fields:
            assert field in memory_info
            assert isinstance(memory_info[field], (int, float))

        assert memory_info["total_gb"] == 16.0
        assert memory_info["available_gb"] == 8.0
        assert memory_info["percent_used"] == 50.0

        self.tearDown()

    def test_memory_threshold_checking_safe(self):
        """Test memory threshold checking with safe memory levels"""
        self.setUp()

        rm = ResourceManager()
        rm.memory_warning_threshold = 0.9
        rm.memory_critical_threshold = 0.95

        with patch.object(rm, 'check_available_memory') as mock_check:
            mock_check.return_value = {
                "percent_used": 70.0,
                "available_gb": 4.0
            }

            is_safe, message = rm._check_memory_threshold()

            assert is_safe is True
            assert isinstance(message, str)

        self.tearDown()

    def test_memory_threshold_checking_warning(self):
        """Test memory threshold checking with warning level memory"""
        self.setUp()

        rm = ResourceManager()
        rm.memory_warning_threshold = 0.8
        rm.memory_critical_threshold = 0.95

        with patch.object(rm, 'check_available_memory') as mock_check:
            mock_check.return_value = {
                "percent_used": 85.0,
                "available_gb": 2.0
            }

            is_safe, message = rm._check_memory_threshold()

            assert is_safe is False
            assert "warning" in message.lower()

        self.tearDown()

    def test_memory_threshold_checking_critical(self):
        """Test memory threshold checking with critical memory levels"""
        self.setUp()

        rm = ResourceManager()
        rm.memory_warning_threshold = 0.8
        rm.memory_critical_threshold = 0.9

        with patch.object(rm, 'check_available_memory') as mock_check:
            mock_check.return_value = {
                "percent_used": 95.0,
                "available_gb": 0.5
            }

            is_safe, message = rm._check_memory_threshold()

            assert is_safe is False
            assert "critical" in message.lower()

        self.tearDown()


class TestResourceManagerModelOperations:
    """Test suite for model loading and management operations"""

    def setUp(self):
        ResourceManager._instance = None
        ResourceManager._initialized = False

    def tearDown(self):
        try:
            rm = ResourceManager()
            rm.cleanup_all()
        except:
            pass
        ResourceManager._instance = None
        ResourceManager._initialized = False

    @patch('subprocess.Popen')
    def test_whisper_model_loading(self, mock_popen):
        """Test Whisper model loading"""
        self.setUp()

        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Running
        mock_popen.return_value = mock_process

        rm = ResourceManager()
        rm.enable_monitoring()

        config = {
            "model": "large-v3-turbo",
            "whisper_cmd": ["mock-whisper"],
            "input_file": "test.wav"
        }

        success = rm.request_model(ModelType.WHISPER, config)

        assert success is True
        assert ModelType.WHISPER in rm.active_models
        assert rm.metrics.model_loads == 1

        self.tearDown()

    @patch('subprocess.Popen')
    def test_whisper_model_loading_failure(self, mock_popen):
        """Test Whisper model loading failure"""
        self.setUp()

        mock_popen.side_effect = Exception("Failed to start process")

        rm = ResourceManager()
        config = {"model": "large-v3-turbo", "whisper_cmd": ["mock-whisper"]}

        success = rm.request_model(ModelType.WHISPER, config)

        assert success is False
        assert ModelType.WHISPER not in rm.active_models

        self.tearDown()

    def test_whisper_model_release(self):
        """Test Whisper model release"""
        self.setUp()

        rm = ResourceManager()

        # Mock loaded model
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Still running

        rm.active_models[ModelType.WHISPER] = ModelResource(
            instance=mock_process,
            process_id=12345,
            memory_usage=2.0,
            load_time=1.5,
            last_used=time.time()
        )

        rm.release_model(ModelType.WHISPER)

        assert ModelType.WHISPER not in rm.active_models
        mock_process.terminate.assert_called_once()

        self.tearDown()

    @patch('importlib.import_module')
    def test_leolm_model_loading(self, mock_import):
        """Test LeoLM model loading"""
        self.setUp()

        # Mock llama_cpp module
        mock_llama_cpp = Mock()
        mock_llm = Mock()
        mock_llama_cpp.Llama.return_value = mock_llm
        mock_import.return_value = mock_llama_cpp

        rm = ResourceManager()
        rm.enable_monitoring()

        config = {
            "model_path": "test.gguf",
            "n_ctx": 2048
        }

        success = rm.request_model(ModelType.LEOLM, config)

        assert success is True
        assert ModelType.LEOLM in rm.active_models
        assert rm.metrics.model_loads == 1

        self.tearDown()

    @patch('importlib.import_module')
    def test_leolm_model_loading_failure(self, mock_import):
        """Test LeoLM model loading failure"""
        self.setUp()

        mock_import.side_effect = ImportError("llama-cpp-python not found")

        rm = ResourceManager()
        config = {"model_path": "test.gguf"}

        success = rm.request_model(ModelType.LEOLM, config)

        assert success is False
        assert ModelType.LEOLM not in rm.active_models

        self.tearDown()

    def test_leolm_model_release(self):
        """Test LeoLM model release"""
        self.setUp()

        rm = ResourceManager()

        # Mock loaded model
        mock_model = Mock()
        rm.active_models[ModelType.LEOLM] = ModelResource(
            instance=mock_model,
            process_id=None,
            memory_usage=4.0,
            load_time=2.0,
            last_used=time.time()
        )

        rm.release_model(ModelType.LEOLM)

        assert ModelType.LEOLM not in rm.active_models

        self.tearDown()


class TestResourceManagerModelSwapping:
    """Test suite for model swapping functionality"""

    def setUp(self):
        ResourceManager._instance = None
        ResourceManager._initialized = False

    def tearDown(self):
        try:
            rm = ResourceManager()
            rm.cleanup_all()
        except:
            pass
        ResourceManager._instance = None
        ResourceManager._initialized = False

    def test_model_swapping_whisper_to_leolm(self):
        """Test swapping from Whisper to LeoLM"""
        self.setUp()

        rm = ResourceManager()
        rm.enable_monitoring()

        # Mock loaded Whisper model
        mock_whisper = Mock()
        rm.active_models[ModelType.WHISPER] = ModelResource(
            instance=mock_whisper,
            process_id=123,
            memory_usage=2.0,
            load_time=1.0,
            last_used=time.time()
        )

        # Mock LeoLM loading
        with patch.object(rm, '_load_leolm_model') as mock_load:
            mock_llm = Mock()
            mock_load.return_value = mock_llm

            success = rm.swap_models(
                ModelType.WHISPER,
                ModelType.LEOLM,
                {"model_path": "test.gguf"}
            )

            assert success is True
            assert ModelType.WHISPER not in rm.active_models
            assert ModelType.LEOLM in rm.active_models
            assert rm.metrics.swaps_performed == 1

        self.tearDown()

    def test_model_swapping_leolm_to_whisper(self):
        """Test swapping from LeoLM to Whisper"""
        self.setUp()

        rm = ResourceManager()
        rm.enable_monitoring()

        # Mock loaded LeoLM model
        mock_leolm = Mock()
        rm.active_models[ModelType.LEOLM] = ModelResource(
            instance=mock_leolm,
            process_id=None,
            memory_usage=4.0,
            load_time=2.0,
            last_used=time.time()
        )

        # Mock Whisper loading
        with patch.object(rm, '_load_whisper_model') as mock_load:
            mock_process = Mock()
            mock_process.pid = 456
            mock_load.return_value = mock_process

            success = rm.swap_models(
                ModelType.LEOLM,
                ModelType.WHISPER,
                {"model": "large-v3-turbo", "whisper_cmd": ["whisper"]}
            )

            assert success is True
            assert ModelType.LEOLM not in rm.active_models
            assert ModelType.WHISPER in rm.active_models
            assert rm.metrics.swaps_performed == 1

        self.tearDown()

    def test_model_swapping_same_type_fails(self):
        """Test that swapping to same model type fails"""
        self.setUp()

        rm = ResourceManager()

        success = rm.swap_models(ModelType.WHISPER, ModelType.WHISPER, {})

        assert success is False
        assert rm.metrics.swaps_performed == 0

        self.tearDown()

    def test_model_swapping_no_source_model(self):
        """Test swapping when source model is not loaded"""
        self.setUp()

        rm = ResourceManager()

        success = rm.swap_models(ModelType.WHISPER, ModelType.LEOLM, {})

        assert success is False
        assert rm.metrics.swaps_performed == 0

        self.tearDown()

    def test_model_swapping_target_load_failure(self):
        """Test swapping when target model fails to load"""
        self.setUp()

        rm = ResourceManager()
        rm.enable_monitoring()

        # Mock loaded Whisper model
        mock_whisper = Mock()
        rm.active_models[ModelType.WHISPER] = ModelResource(
            instance=mock_whisper,
            process_id=123,
            memory_usage=2.0,
            load_time=1.0,
            last_used=time.time()
        )

        # Mock LeoLM loading failure
        with patch.object(rm, '_load_leolm_model') as mock_load:
            mock_load.side_effect = Exception("Load failed")

            success = rm.swap_models(
                ModelType.WHISPER,
                ModelType.LEOLM,
                {"model_path": "test.gguf"}
            )

            assert success is False
            # Whisper should still be loaded since swap failed
            assert ModelType.WHISPER in rm.active_models
            assert rm.metrics.swaps_performed == 0

        self.tearDown()


class TestResourceManagerMonitoring:
    """Test suite for performance monitoring functionality"""

    def setUp(self):
        ResourceManager._instance = None
        ResourceManager._initialized = False

    def tearDown(self):
        try:
            rm = ResourceManager()
            rm.cleanup_all()
        except:
            pass
        ResourceManager._instance = None
        ResourceManager._initialized = False

    def test_monitoring_disabled_by_default(self):
        """Test that monitoring is disabled by default"""
        self.setUp()

        rm = ResourceManager()

        assert rm.monitoring_enabled is False
        assert rm.get_metrics() == {}

        self.tearDown()

    def test_enable_monitoring(self):
        """Test enabling monitoring"""
        self.setUp()

        rm = ResourceManager()
        rm.enable_monitoring()

        assert rm.monitoring_enabled is True
        metrics = rm.get_metrics()
        assert isinstance(metrics, dict)
        assert "model_loads" in metrics

        self.tearDown()

    def test_disable_monitoring(self):
        """Test disabling monitoring"""
        self.setUp()

        rm = ResourceManager()
        rm.enable_monitoring()
        rm.disable_monitoring()

        assert rm.monitoring_enabled is False
        assert rm.get_metrics() == {}

        self.tearDown()

    def test_continuous_monitoring_start_stop(self):
        """Test starting and stopping continuous monitoring"""
        self.setUp()

        rm = ResourceManager()
        rm.enable_monitoring(continuous=True)

        assert rm._monitor_thread is not None
        assert rm._monitor_thread.is_alive()

        time.sleep(0.1)  # Let it run briefly

        rm.disable_monitoring()

        assert rm._monitor_thread is None

        self.tearDown()

    def test_get_metrics_structure(self):
        """Test metrics structure and content"""
        self.setUp()

        rm = ResourceManager()
        rm.enable_monitoring()

        metrics = rm.get_metrics()

        expected_fields = [
            "model_loads", "model_unloads", "swaps_performed",
            "current_memory_usage", "gpu_acceleration"
        ]

        for field in expected_fields:
            assert field in metrics

        self.tearDown()

    def test_metrics_update_on_operations(self):
        """Test that metrics are updated during operations"""
        self.setUp()

        rm = ResourceManager()
        rm.enable_monitoring()

        initial_loads = rm.metrics.model_loads

        # Mock a successful model load
        with patch.object(rm, '_load_whisper_model') as mock_load:
            mock_process = Mock()
            mock_process.pid = 123
            mock_load.return_value = mock_process

            rm.request_model(ModelType.WHISPER, {"model": "test"})

        assert rm.metrics.model_loads == initial_loads + 1

        self.tearDown()


class TestResourceManagerConstraints:
    """Test suite for resource constraints checking"""

    def setUp(self):
        ResourceManager._instance = None
        ResourceManager._initialized = False

    def tearDown(self):
        try:
            rm = ResourceManager()
            rm.cleanup_all()
        except:
            pass
        ResourceManager._instance = None
        ResourceManager._initialized = False

    def test_resource_constraints_defined(self):
        """Test that resource constraints are properly defined"""
        self.setUp()

        rm = ResourceManager()

        assert ModelType.WHISPER in rm.RESOURCE_CONSTRAINTS
        assert ModelType.LEOLM in rm.RESOURCE_CONSTRAINTS

        whisper_constraints = rm.RESOURCE_CONSTRAINTS[ModelType.WHISPER]
        leolm_constraints = rm.RESOURCE_CONSTRAINTS[ModelType.LEOLM]

        assert isinstance(whisper_constraints, ResourceConstraints)
        assert isinstance(leolm_constraints, ResourceConstraints)

        # LeoLM should require more memory than Whisper
        assert leolm_constraints.min_memory_gb > whisper_constraints.min_memory_gb

        self.tearDown()

    @patch('psutil.virtual_memory')
    def test_insufficient_memory_handling(self, mock_memory):
        """Test handling when insufficient memory is available"""
        self.setUp()

        # Mock very low memory (1GB)
        mock_memory.return_value = Mock(
            total=1024**3,
            available=512*1024**2,
            used=512*1024**2,
            percent=50,
            free=512*1024**2
        )

        rm = ResourceManager()

        # Should fail to load LeoLM (requires more memory)
        success = rm.request_model(ModelType.LEOLM, {"model_path": "test.gguf"})
        assert success is False

        self.tearDown()

    @patch('psutil.virtual_memory')
    def test_sufficient_memory_handling(self, mock_memory):
        """Test handling when sufficient memory is available"""
        self.setUp()

        # Mock high memory availability (16GB)
        mock_memory.return_value = Mock(
            total=16*1024**3,
            available=12*1024**3,
            used=4*1024**3,
            percent=25,
            free=12*1024**3
        )

        rm = ResourceManager()

        # Mock successful loading
        with patch.object(rm, '_load_leolm_model') as mock_load:
            mock_model = Mock()
            mock_load.return_value = mock_model

            success = rm.request_model(ModelType.LEOLM, {"model_path": "test.gguf"})
            assert success is True

        self.tearDown()


class TestResourceManagerThreadSafety:
    """Test suite for thread safety of ResourceManager operations"""

    def setUp(self):
        ResourceManager._instance = None
        ResourceManager._initialized = False

    def tearDown(self):
        try:
            rm = ResourceManager()
            rm.cleanup_all()
        except:
            pass
        ResourceManager._instance = None
        ResourceManager._initialized = False

    def test_thread_safe_model_operations(self):
        """Test thread safety of model operations"""
        self.setUp()

        rm = ResourceManager()
        rm.enable_monitoring()

        results = []
        errors = []

        def load_and_release_model(model_type, thread_id):
            try:
                # Mock appropriate loader
                if model_type == ModelType.WHISPER:
                    with patch.object(rm, '_load_whisper_model') as mock_load:
                        mock_process = Mock()
                        mock_process.pid = thread_id
                        mock_load.return_value = mock_process

                        success = rm.request_model(model_type, {"model": "test"})
                        results.append((thread_id, model_type, success))

                        if success:
                            time.sleep(0.1)  # Hold briefly
                            rm.release_model(model_type)

                else:  # LEOLM
                    with patch.object(rm, '_load_leolm_model') as mock_load:
                        mock_model = Mock()
                        mock_load.return_value = mock_model

                        success = rm.request_model(model_type, {"model_path": "test.gguf"})
                        results.append((thread_id, model_type, success))

                        if success:
                            time.sleep(0.1)  # Hold briefly
                            rm.release_model(model_type)

            except Exception as e:
                errors.append((thread_id, str(e)))

        # Create multiple threads for same model type
        threads = []
        for i in range(5):
            thread = threading.Thread(
                target=load_and_release_model,
                args=(ModelType.WHISPER, i),
                name=f"Thread-{i}"
            )
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5

        self.tearDown()

    def test_concurrent_different_model_types(self):
        """Test concurrent access to different model types"""
        self.setUp()

        rm = ResourceManager()
        rm.enable_monitoring()

        results = {}
        errors = []

        def load_model(model_type, thread_id):
            try:
                if model_type == ModelType.WHISPER:
                    with patch.object(rm, '_load_whisper_model') as mock_load:
                        mock_process = Mock()
                        mock_process.pid = 123
                        mock_load.return_value = mock_process

                        success = rm.request_model(model_type, {"model": "test"})
                        results[thread_id] = (model_type, success)
                else:
                    with patch.object(rm, '_load_leolm_model') as mock_load:
                        mock_model = Mock()
                        mock_load.return_value = mock_model

                        success = rm.request_model(model_type, {"model_path": "test.gguf"})
                        results[thread_id] = (model_type, success)

            except Exception as e:
                errors.append((thread_id, str(e)))

        # Create threads for different model types
        threads = [
            threading.Thread(target=load_model, args=(ModelType.WHISPER, "whisper_thread")),
            threading.Thread(target=load_model, args=(ModelType.LEOLM, "leolm_thread"))
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Both should succeed since they're different model types
        assert len(errors) == 0
        assert results["whisper_thread"][1] is True
        assert results["leolm_thread"][1] is True

        self.tearDown()


class TestResourceManagerStatus:
    """Test suite for status reporting functionality"""

    def setUp(self):
        ResourceManager._instance = None
        ResourceManager._initialized = False

    def tearDown(self):
        try:
            rm = ResourceManager()
            rm.cleanup_all()
        except:
            pass
        ResourceManager._instance = None
        ResourceManager._initialized = False

    def test_get_status_structure(self):
        """Test status reporting structure"""
        self.setUp()

        rm = ResourceManager()
        status = rm.get_status()

        required_fields = [
            "initialized", "monitoring_enabled", "gpu_acceleration",
            "memory_safe", "active_models", "system_info"
        ]

        for field in required_fields:
            assert field in status

        assert status["initialized"] is True
        assert isinstance(status["active_models"], dict)
        assert "total_memory_gb" in status["system_info"]

        self.tearDown()

    def test_get_status_with_loaded_models(self):
        """Test status reporting with loaded models"""
        self.setUp()

        rm = ResourceManager()

        # Mock a loaded model
        mock_process = Mock()
        rm.active_models[ModelType.WHISPER] = ModelResource(
            instance=mock_process,
            process_id=123,
            memory_usage=2.0,
            load_time=1.0,
            last_used=time.time()
        )

        status = rm.get_status()

        assert len(status["active_models"]) == 1
        assert "whisper" in status["active_models"]

        model_info = status["active_models"]["whisper"]
        assert "memory_usage" in model_info
        assert "load_time" in model_info

        self.tearDown()


class TestResourceManagerCleanup:
    """Test suite for cleanup functionality"""

    def setUp(self):
        ResourceManager._instance = None
        ResourceManager._initialized = False

    def tearDown(self):
        try:
            rm = ResourceManager()
            rm.cleanup_all()
        except:
            pass
        ResourceManager._instance = None
        ResourceManager._initialized = False

    def test_cleanup_all(self):
        """Test cleanup all functionality"""
        self.setUp()

        rm = ResourceManager()
        rm.enable_monitoring(continuous=True)

        # Mock loaded models
        mock_whisper = Mock()
        mock_leolm = Mock()

        rm.active_models[ModelType.WHISPER] = ModelResource(
            instance=mock_whisper,
            process_id=123,
            memory_usage=2.0,
            load_time=1.0,
            last_used=time.time()
        )

        rm.active_models[ModelType.LEOLM] = ModelResource(
            instance=mock_leolm,
            process_id=None,
            memory_usage=4.0,
            load_time=2.0,
            last_used=time.time()
        )

        rm.cleanup_all()

        assert len(rm.active_models) == 0
        assert rm.monitoring_enabled is False
        assert rm._monitor_thread is None

        self.tearDown()

    def test_force_cleanup(self):
        """Test force cleanup functionality"""
        self.setUp()

        rm = ResourceManager()
        rm.enable_monitoring()

        initial_cleanups = rm.metrics.memory_cleanups

        rm.force_cleanup()

        assert rm.metrics.memory_cleanups == initial_cleanups + 1

        self.tearDown()


class TestResourceManagerErrorHandling:
    """Test suite for error handling scenarios"""

    def setUp(self):
        ResourceManager._instance = None
        ResourceManager._initialized = False

    def tearDown(self):
        try:
            rm = ResourceManager()
            rm.cleanup_all()
        except:
            pass
        ResourceManager._instance = None
        ResourceManager._initialized = False

    def test_release_nonexistent_model(self):
        """Test releasing a model that doesn't exist"""
        self.setUp()

        rm = ResourceManager()

        # Should handle gracefully without raising exception
        rm.release_model(ModelType.WHISPER)
        rm.release_model(ModelType.LEOLM)

        self.tearDown()

    def test_request_model_with_invalid_config(self):
        """Test requesting model with invalid configuration"""
        self.setUp()

        rm = ResourceManager()

        # Empty config should fail
        success = rm.request_model(ModelType.WHISPER, {})
        assert success is False

        # Invalid model path for LeoLM
        success = rm.request_model(ModelType.LEOLM, {"model_path": "/nonexistent/path"})
        assert success is False

        self.tearDown()

    def test_model_loading_exceptions(self):
        """Test handling of exceptions during model loading"""
        self.setUp()

        rm = ResourceManager()

        with patch.object(rm, '_load_whisper_model', side_effect=Exception("Load failed")):
            success = rm.request_model(ModelType.WHISPER, {"model": "test"})
            assert success is False

        # ResourceManager should still be functional
        status = rm.get_status()
        assert status["initialized"] is True

        self.tearDown()


class TestModelResource:
    """Test suite for ModelResource dataclass"""

    def test_model_resource_creation(self):
        """Test ModelResource creation and attributes"""
        mock_instance = Mock()
        current_time = time.time()

        resource = ModelResource(
            instance=mock_instance,
            process_id=12345,
            memory_usage=2.5,
            load_time=1.2,
            last_used=current_time
        )

        assert resource.instance == mock_instance
        assert resource.process_id == 12345
        assert resource.memory_usage == 2.5
        assert resource.load_time == 1.2
        assert resource.last_used == current_time


class TestPerformanceMetrics:
    """Test suite for PerformanceMetrics dataclass"""

    def test_performance_metrics_defaults(self):
        """Test PerformanceMetrics default values"""
        metrics = PerformanceMetrics()

        assert metrics.model_loads == 0
        assert metrics.model_unloads == 0
        assert metrics.memory_cleanups == 0
        assert metrics.swaps_performed == 0
        assert metrics.total_load_time == 0.0
        assert metrics.total_unload_time == 0.0
        assert metrics.peak_memory_usage == 0.0
        assert metrics.current_memory_usage == 0.0

    def test_performance_metrics_updates(self):
        """Test updating performance metrics"""
        metrics = PerformanceMetrics()

        metrics.model_loads += 1
        metrics.total_load_time += 1.5
        metrics.peak_memory_usage = 8.0

        assert metrics.model_loads == 1
        assert metrics.total_load_time == 1.5
        assert metrics.peak_memory_usage == 8.0


class TestResourceConstraints:
    """Test suite for ResourceConstraints dataclass"""

    def test_resource_constraints_creation(self):
        """Test ResourceConstraints creation and validation"""
        constraints = ResourceConstraints(
            min_memory_gb=4.0,
            preferred_memory_gb=8.0,
            gpu_required=True,
            max_concurrent=2
        )

        assert constraints.min_memory_gb == 4.0
        assert constraints.preferred_memory_gb == 8.0
        assert constraints.gpu_required is True
        assert constraints.max_concurrent == 2

    def test_resource_constraints_validation(self):
        """Test ResourceConstraints logical validation"""
        constraints = ResourceConstraints(
            min_memory_gb=2.0,
            preferred_memory_gb=8.0,
            gpu_required=False,
            max_concurrent=1
        )

        # Preferred should be >= minimum
        assert constraints.preferred_memory_gb >= constraints.min_memory_gb


if __name__ == "__main__":
    pytest.main([__file__, "-v"])