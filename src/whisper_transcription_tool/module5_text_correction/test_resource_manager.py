"""
Comprehensive Unit Tests for ResourceManager

Tests cover:
- Singleton pattern behavior
- Memory monitoring functionality
- Thread-safe model loading/unloading
- Model swapping mechanisms
- GPU acceleration detection
- Performance metrics collection
- Error recovery scenarios

Author: ResourceSentinel Agent
Version: 1.0.0
"""

import unittest
import threading
import time
import psutil
import subprocess
from unittest.mock import patch, MagicMock, Mock
import tempfile
import os
from pathlib import Path

# Import the classes to test
from .resource_manager import (
    ResourceManager,
    ModelType,
    ResourceConstraints,
    ModelResource,
    PerformanceMetrics
)


class TestResourceManager(unittest.TestCase):
    """Test suite for ResourceManager class"""

    def setUp(self):
        """Set up test environment"""
        # Reset singleton for each test
        ResourceManager._instance = None
        ResourceManager._initialized = False

    def tearDown(self):
        """Clean up after each test"""
        # Clean up any remaining resources
        try:
            rm = ResourceManager()
            rm.cleanup_all()
        except:
            pass

        # Reset singleton
        ResourceManager._instance = None
        ResourceManager._initialized = False

    def test_singleton_pattern(self):
        """Test that ResourceManager follows singleton pattern"""
        rm1 = ResourceManager()
        rm2 = ResourceManager()

        # Should be the same instance
        self.assertIs(rm1, rm2)
        self.assertEqual(id(rm1), id(rm2))

    def test_thread_safe_singleton(self):
        """Test singleton pattern is thread-safe"""
        instances = []

        def create_instance():
            rm = ResourceManager()
            instances.append(rm)

        # Create multiple threads to test concurrency
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_instance)
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All instances should be the same object
        first_instance = instances[0]
        for instance in instances[1:]:
            self.assertIs(instance, first_instance)

    def test_gpu_acceleration_detection(self):
        """Test GPU acceleration detection logic"""
        rm = ResourceManager()

        # GPU acceleration should be detected as string
        self.assertIsInstance(rm.gpu_acceleration, str)
        self.assertIn(rm.gpu_acceleration, ["metal", "cuda", "cpu"])

    @patch('platform.system')
    @patch('platform.mac_ver')
    def test_metal_detection_macos(self, mock_mac_ver, mock_system):
        """Test Metal detection on macOS"""
        mock_system.return_value = "Darwin"
        mock_mac_ver.return_value = ("11.0.0", "", "")

        # Reset singleton to test detection
        ResourceManager._instance = None
        ResourceManager._initialized = False

        rm = ResourceManager()
        self.assertEqual(rm.gpu_acceleration, "metal")

    @patch('platform.system')
    @patch('subprocess.run')
    def test_cuda_detection_linux(self, mock_subprocess, mock_system):
        """Test CUDA detection on Linux"""
        mock_system.return_value = "Linux"
        mock_subprocess.return_value = Mock(returncode=0)

        # Reset singleton to test detection
        ResourceManager._instance = None
        ResourceManager._initialized = False

        rm = ResourceManager()
        self.assertEqual(rm.gpu_acceleration, "cuda")

    def test_memory_monitoring(self):
        """Test memory monitoring functionality"""
        rm = ResourceManager()

        memory_info = rm.check_available_memory()

        # Check all required fields are present
        required_fields = ["total_gb", "available_gb", "used_gb", "percent_used", "free_gb"]
        for field in required_fields:
            self.assertIn(field, memory_info)
            self.assertIsInstance(memory_info[field], (int, float))
            self.assertGreaterEqual(memory_info[field], 0)

        # Sanity checks
        self.assertGreater(memory_info["total_gb"], 0)
        self.assertLessEqual(memory_info["percent_used"], 100)

    def test_memory_threshold_checking(self):
        """Test memory threshold checking"""
        rm = ResourceManager()

        # Test with normal memory usage
        rm.memory_warning_threshold = 0.9
        rm.memory_critical_threshold = 0.95

        is_safe, message = rm._check_memory_threshold()

        # Should return boolean and string
        self.assertIsInstance(is_safe, bool)
        self.assertIsInstance(message, str)

    def test_force_cleanup(self):
        """Test force cleanup functionality"""
        rm = ResourceManager()
        rm.enable_monitoring()

        initial_cleanups = rm.metrics.memory_cleanups

        rm.force_cleanup()

        # Cleanup count should increase
        self.assertEqual(rm.metrics.memory_cleanups, initial_cleanups + 1)

    @patch('subprocess.Popen')
    def test_whisper_model_loading(self, mock_popen):
        """Test Whisper model loading"""
        # Mock subprocess
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        rm = ResourceManager()
        rm.enable_monitoring()

        config = {"model": "large-v3-turbo", "whisper_cmd": ["mock-whisper"]}

        # Request Whisper model
        success = rm.request_model(ModelType.WHISPER, config)

        self.assertTrue(success)
        self.assertIn(ModelType.WHISPER, rm.active_models)

        # Check metrics updated
        self.assertEqual(rm.metrics.model_loads, 1)

    def test_whisper_model_release(self):
        """Test Whisper model release"""
        rm = ResourceManager()

        # Mock a loaded Whisper model
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

        # Release model
        rm.release_model(ModelType.WHISPER)

        # Should be removed from active models
        self.assertNotIn(ModelType.WHISPER, rm.active_models)

        # Should have tried to terminate
        mock_process.terminate.assert_called_once()

    @patch('importlib.import_module')
    def test_leolm_model_loading(self, mock_import):
        """Test LeoLM model loading"""
        # Mock llama_cpp
        mock_llama_cpp = Mock()
        mock_llm = Mock()
        mock_llama_cpp.Llama.return_value = mock_llm
        mock_import.return_value = mock_llama_cpp

        rm = ResourceManager()
        rm.enable_monitoring()

        config = {"model_path": "test.gguf", "n_ctx": 2048}

        with patch('importlib.import_module', return_value=mock_llama_cpp):
            success = rm.request_model(ModelType.LEOLM, config)

        self.assertTrue(success)
        self.assertIn(ModelType.LEOLM, rm.active_models)

    def test_model_swapping(self):
        """Test model swapping functionality"""
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

            # Perform swap
            success = rm.swap_models(ModelType.WHISPER, ModelType.LEOLM, {})

            # Whisper should be released
            self.assertNotIn(ModelType.WHISPER, rm.active_models)

            # Metrics should be updated
            self.assertEqual(rm.metrics.swaps_performed, 1)

    def test_performance_monitoring(self):
        """Test performance monitoring functionality"""
        rm = ResourceManager()

        # Initially disabled
        self.assertFalse(rm.monitoring_enabled)
        self.assertEqual(rm.get_metrics(), {})

        # Enable monitoring
        rm.enable_monitoring()
        self.assertTrue(rm.monitoring_enabled)

        # Get metrics
        metrics = rm.get_metrics()
        self.assertIsInstance(metrics, dict)
        self.assertIn("model_loads", metrics)
        self.assertIn("current_memory_usage", metrics)
        self.assertIn("gpu_acceleration", metrics)

    def test_continuous_monitoring(self):
        """Test continuous monitoring thread"""
        rm = ResourceManager()

        # Enable continuous monitoring
        rm.enable_monitoring(continuous=True)

        self.assertIsNotNone(rm._monitor_thread)
        self.assertTrue(rm._monitor_thread.is_alive())

        # Let it run briefly
        time.sleep(0.1)

        # Disable monitoring
        rm.disable_monitoring()

        # Thread should be stopped
        self.assertIsNone(rm._monitor_thread)

    def test_resource_constraints(self):
        """Test resource constraints checking"""
        rm = ResourceManager()

        # Check constraints are defined
        self.assertIn(ModelType.WHISPER, rm.RESOURCE_CONSTRAINTS)
        self.assertIn(ModelType.LEOLM, rm.RESOURCE_CONSTRAINTS)

        whisper_constraints = rm.RESOURCE_CONSTRAINTS[ModelType.WHISPER]
        leolm_constraints = rm.RESOURCE_CONSTRAINTS[ModelType.LEOLM]

        # LeoLM should require more memory than Whisper
        self.assertGreater(leolm_constraints.min_memory_gb, whisper_constraints.min_memory_gb)

    @patch('psutil.virtual_memory')
    def test_insufficient_memory_handling(self, mock_memory):
        """Test handling when insufficient memory is available"""
        # Mock very low memory
        mock_memory.return_value = Mock(
            total=1024**3,  # 1GB
            available=512*1024**2,  # 512MB
            used=512*1024**2,  # 512MB
            percent=50,
            free=512*1024**2
        )

        rm = ResourceManager()

        # Should fail to load LeoLM (requires 6GB)
        success = rm.request_model(ModelType.LEOLM, {})
        self.assertFalse(success)

    def test_thread_safety_model_operations(self):
        """Test thread safety of model operations"""
        rm = ResourceManager()
        rm.enable_monitoring()

        results = []
        errors = []

        def load_and_release_model(model_type):
            try:
                # Try to load model
                with patch.object(rm, '_load_whisper_model') if model_type == ModelType.WHISPER else \
                     patch.object(rm, '_load_leolm_model') as mock_load:

                    mock_model = Mock()
                    mock_load.return_value = mock_model

                    success = rm.request_model(model_type, {})
                    results.append((threading.current_thread().name, model_type, success))

                    if success:
                        time.sleep(0.1)  # Hold model briefly
                        rm.release_model(model_type)

            except Exception as e:
                errors.append((threading.current_thread().name, str(e)))

        # Create multiple threads trying to load the same model type
        threads = []
        for i in range(5):
            thread = threading.Thread(
                target=load_and_release_model,
                args=(ModelType.WHISPER,),
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
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 5)

        # Only one should succeed due to locking (depending on implementation)
        successful_loads = [r for r in results if r[2]]
        self.assertGreaterEqual(len(successful_loads), 1)

    def test_status_reporting(self):
        """Test status reporting functionality"""
        rm = ResourceManager()

        status = rm.get_status()

        # Check required fields
        required_fields = [
            "initialized", "monitoring_enabled", "gpu_acceleration",
            "memory_safe", "active_models", "system_info"
        ]

        for field in required_fields:
            self.assertIn(field, status)

        self.assertTrue(status["initialized"])
        self.assertIsInstance(status["active_models"], dict)
        self.assertIn("total_memory_gb", status["system_info"])

    def test_cleanup_all(self):
        """Test cleanup all functionality"""
        rm = ResourceManager()
        rm.enable_monitoring(continuous=True)

        # Mock some loaded models
        mock_whisper = Mock()
        rm.active_models[ModelType.WHISPER] = ModelResource(
            instance=mock_whisper,
            process_id=123,
            memory_usage=2.0,
            load_time=1.0,
            last_used=time.time()
        )

        # Cleanup all
        rm.cleanup_all()

        # Should be empty
        self.assertEqual(len(rm.active_models), 0)
        self.assertFalse(rm.monitoring_enabled)

    def test_error_recovery(self):
        """Test error recovery scenarios"""
        rm = ResourceManager()

        # Test release of non-existent model (should not crash)
        rm.release_model(ModelType.WHISPER)  # Should handle gracefully

        # Test request with invalid config
        with patch.object(rm, '_load_whisper_model', side_effect=Exception("Load failed")):
            success = rm.request_model(ModelType.WHISPER, {})
            self.assertFalse(success)

        # ResourceManager should still be functional
        status = rm.get_status()
        self.assertTrue(status["initialized"])


class TestResourceConstraints(unittest.TestCase):
    """Test suite for ResourceConstraints dataclass"""

    def test_resource_constraints_creation(self):
        """Test ResourceConstraints creation"""
        constraints = ResourceConstraints(
            min_memory_gb=4.0,
            preferred_memory_gb=8.0,
            gpu_required=True,
            max_concurrent=2
        )

        self.assertEqual(constraints.min_memory_gb, 4.0)
        self.assertEqual(constraints.preferred_memory_gb, 8.0)
        self.assertTrue(constraints.gpu_required)
        self.assertEqual(constraints.max_concurrent, 2)


class TestModelResource(unittest.TestCase):
    """Test suite for ModelResource dataclass"""

    def test_model_resource_creation(self):
        """Test ModelResource creation"""
        mock_instance = Mock()
        resource = ModelResource(
            instance=mock_instance,
            process_id=12345,
            memory_usage=2.5,
            load_time=1.2,
            last_used=time.time()
        )

        self.assertEqual(resource.instance, mock_instance)
        self.assertEqual(resource.process_id, 12345)
        self.assertEqual(resource.memory_usage, 2.5)
        self.assertEqual(resource.load_time, 1.2)


class TestPerformanceMetrics(unittest.TestCase):
    """Test suite for PerformanceMetrics dataclass"""

    def test_performance_metrics_defaults(self):
        """Test PerformanceMetrics default values"""
        metrics = PerformanceMetrics()

        self.assertEqual(metrics.model_loads, 0)
        self.assertEqual(metrics.model_unloads, 0)
        self.assertEqual(metrics.memory_cleanups, 0)
        self.assertEqual(metrics.swaps_performed, 0)
        self.assertEqual(metrics.total_load_time, 0.0)
        self.assertEqual(metrics.total_unload_time, 0.0)
        self.assertEqual(metrics.peak_memory_usage, 0.0)
        self.assertEqual(metrics.current_memory_usage, 0.0)


class TestIntegration(unittest.TestCase):
    """Integration tests for ResourceManager"""

    def setUp(self):
        """Set up integration test environment"""
        ResourceManager._instance = None
        ResourceManager._initialized = False

    def tearDown(self):
        """Clean up integration test environment"""
        try:
            rm = ResourceManager()
            rm.cleanup_all()
        except:
            pass
        ResourceManager._instance = None
        ResourceManager._initialized = False

    def test_complete_workflow(self):
        """Test complete workflow: load -> use -> swap -> cleanup"""
        rm = ResourceManager()
        rm.enable_monitoring()

        # Mock model implementations
        with patch.object(rm, '_load_whisper_model') as mock_whisper, \
             patch.object(rm, '_load_leolm_model') as mock_leolm:

            mock_whisper.return_value = Mock()
            mock_leolm.return_value = Mock()

            # Step 1: Load Whisper
            success = rm.request_model(ModelType.WHISPER, {})
            self.assertTrue(success)

            # Step 2: Check status
            status = rm.get_status()
            self.assertEqual(len(status["active_models"]), 1)

            # Step 3: Swap to LeoLM
            success = rm.swap_models(ModelType.WHISPER, ModelType.LEOLM, {})
            self.assertTrue(success)

            # Step 4: Check metrics
            metrics = rm.get_metrics()
            self.assertEqual(metrics["swaps_performed"], 1)
            self.assertEqual(metrics["model_loads"], 2)  # Whisper + LeoLM

            # Step 5: Cleanup
            rm.cleanup_all()

            status = rm.get_status()
            self.assertEqual(len(status["active_models"]), 0)

    def test_concurrent_access_different_models(self):
        """Test concurrent access to different model types"""
        rm = ResourceManager()
        rm.enable_monitoring()

        results = {}

        def load_model(model_type, thread_id):
            with patch.object(rm, '_load_whisper_model' if model_type == ModelType.WHISPER else '_load_leolm_model') as mock_load:
                mock_load.return_value = Mock()
                success = rm.request_model(model_type, {})
                results[thread_id] = (model_type, success)

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
        self.assertTrue(results["whisper_thread"][1])
        self.assertTrue(results["leolm_thread"][1])


if __name__ == '__main__':
    unittest.main(verbosity=2)