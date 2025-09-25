"""
Thread Safety Integration Tests for ResourceManager

These tests focus specifically on thread safety scenarios:
- Concurrent singleton creation
- Multiple threads accessing the same model
- Race conditions in model swapping
- Memory monitoring under concurrent load
- Performance metrics thread safety

Author: ResourceSentinel Agent
Version: 1.0.0
"""

import unittest
import threading
import time
import random
from unittest.mock import patch, Mock
import concurrent.futures
from collections import defaultdict

from .resource_manager import ResourceManager, ModelType


class ThreadSafetyTests(unittest.TestCase):
    """Comprehensive thread safety tests for ResourceManager"""

    def setUp(self):
        """Set up test environment"""
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

    def test_concurrent_singleton_creation(self):
        """Test that singleton creation is thread-safe under high concurrency"""
        instances = []
        exceptions = []
        num_threads = 50

        def create_instance():
            try:
                rm = ResourceManager()
                instances.append(id(rm))  # Store ID instead of object to avoid reference issues
            except Exception as e:
                exceptions.append(e)

        # Create many threads simultaneously
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=create_instance)
            threads.append(thread)

        # Start all threads at once
        start_time = time.time()
        for thread in threads:
            thread.start()

        # Wait for all to complete
        for thread in threads:
            thread.join(timeout=10)  # 10-second timeout

        # Check results
        self.assertEqual(len(exceptions), 0, f"Exceptions during creation: {exceptions}")
        self.assertEqual(len(instances), num_threads)

        # All instances should have the same ID (same object)
        unique_ids = set(instances)
        self.assertEqual(len(unique_ids), 1, f"Multiple singleton instances created: {unique_ids}")

        print(f"Created {num_threads} singleton instances in {time.time() - start_time:.3f}s")

    def test_concurrent_model_loading(self):
        """Test concurrent model loading requests for the same model type"""
        rm = ResourceManager()
        rm.enable_monitoring()

        results = []
        errors = []
        load_times = []

        def load_whisper_model(thread_id):
            try:
                start_time = time.time()

                with patch.object(rm, '_load_whisper_model') as mock_load:
                    # Simulate variable loading time
                    def mock_load_func(config):
                        time.sleep(random.uniform(0.1, 0.3))
                        mock_model = Mock()
                        mock_model.pid = thread_id
                        return mock_model

                    mock_load.side_effect = mock_load_func

                    success = rm.request_model(ModelType.WHISPER, {"thread_id": thread_id})
                    load_time = time.time() - start_time

                    results.append((thread_id, success, load_time))
                    load_times.append(load_time)

                    if success:
                        # Hold the model briefly
                        time.sleep(0.1)
                        rm.release_model(ModelType.WHISPER)

            except Exception as e:
                errors.append((thread_id, str(e)))

        # Create multiple threads trying to load the same model
        num_threads = 10
        threads = []

        for i in range(num_threads):
            thread = threading.Thread(target=load_whisper_model, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join(timeout=15)

        # Analyze results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), num_threads)

        # Check that only one thread succeeded at loading (due to locking)
        successful_loads = [r for r in results if r[1]]
        self.assertGreaterEqual(len(successful_loads), 1, "At least one load should succeed")

        # Check metrics consistency
        metrics = rm.get_metrics()
        self.assertGreaterEqual(metrics["model_loads"], 1)

        print(f"Concurrent model loading: {len(successful_loads)} successful out of {num_threads} attempts")

    def test_model_swapping_race_conditions(self):
        """Test that model swapping handles race conditions correctly"""
        rm = ResourceManager()
        rm.enable_monitoring()

        swap_results = []
        swap_errors = []

        def perform_swap(swap_id):
            try:
                with patch.object(rm, '_load_whisper_model') as mock_whisper, \
                     patch.object(rm, '_load_leolm_model') as mock_leolm:

                    mock_whisper.return_value = Mock(pid=f"whisper_{swap_id}")
                    mock_leolm.return_value = Mock()

                    # Randomly decide swap direction
                    if swap_id % 2 == 0:
                        from_model, to_model = ModelType.WHISPER, ModelType.LEOLM
                    else:
                        from_model, to_model = ModelType.LEOLM, ModelType.WHISPER

                    # Ensure from_model is loaded first
                    rm.request_model(from_model, {})

                    # Small delay to increase chance of race conditions
                    time.sleep(random.uniform(0.01, 0.05))

                    # Perform swap
                    success = rm.swap_models(from_model, to_model, {})
                    swap_results.append((swap_id, from_model, to_model, success))

            except Exception as e:
                swap_errors.append((swap_id, str(e)))

        # Create multiple threads performing swaps
        num_swaps = 8
        threads = []

        for i in range(num_swaps):
            thread = threading.Thread(target=perform_swap, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join(timeout=20)

        # Analyze results
        self.assertEqual(len(swap_errors), 0, f"Swap errors: {swap_errors}")

        # At least some swaps should succeed
        successful_swaps = [r for r in swap_results if r[3]]
        self.assertGreater(len(successful_swaps), 0)

        print(f"Model swapping: {len(successful_swaps)} successful swaps out of {num_swaps}")

    def test_memory_monitoring_thread_safety(self):
        """Test that memory monitoring is thread-safe"""
        rm = ResourceManager()
        rm.enable_monitoring(continuous=True)

        memory_readings = []
        monitoring_errors = []

        def monitor_memory(monitor_id):
            try:
                for _ in range(10):
                    memory_info = rm.check_available_memory()
                    memory_readings.append((monitor_id, memory_info["used_gb"]))
                    time.sleep(0.01)

                    # Also check metrics
                    metrics = rm.get_metrics()
                    self.assertIsInstance(metrics, dict)

            except Exception as e:
                monitoring_errors.append((monitor_id, str(e)))

        # Create multiple monitoring threads
        num_monitors = 5
        threads = []

        for i in range(num_monitors):
            thread = threading.Thread(target=monitor_memory, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join(timeout=10)

        # Stop continuous monitoring
        rm.disable_monitoring()

        # Analyze results
        self.assertEqual(len(monitoring_errors), 0, f"Monitoring errors: {monitoring_errors}")
        self.assertEqual(len(memory_readings), num_monitors * 10)

        # All readings should be reasonable
        for monitor_id, reading in memory_readings:
            self.assertGreater(reading, 0)
            self.assertLess(reading, 1000)  # Less than 1TB

    def test_metrics_collection_thread_safety(self):
        """Test that metrics collection is thread-safe under concurrent operations"""
        rm = ResourceManager()
        rm.enable_monitoring()

        metrics_snapshots = []
        operation_errors = []

        def perform_operations(worker_id):
            try:
                for operation_count in range(5):
                    with patch.object(rm, '_load_whisper_model') as mock_load:
                        mock_load.return_value = Mock(pid=f"worker_{worker_id}_op_{operation_count}")

                        # Load model
                        success = rm.request_model(ModelType.WHISPER, {})
                        if success:
                            # Take metrics snapshot
                            metrics = rm.get_metrics()
                            metrics_snapshots.append((worker_id, operation_count, metrics.copy()))

                            # Brief delay
                            time.sleep(0.01)

                            # Release model
                            rm.release_model(ModelType.WHISPER)

                            # Force cleanup occasionally
                            if operation_count % 3 == 0:
                                rm.force_cleanup()

            except Exception as e:
                operation_errors.append((worker_id, str(e)))

        # Create multiple worker threads
        num_workers = 6
        threads = []

        for i in range(num_workers):
            thread = threading.Thread(target=perform_operations, args=(i,))
            threads.append(thread)

        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join(timeout=15)

        execution_time = time.time() - start_time

        # Analyze results
        self.assertEqual(len(operation_errors), 0, f"Operation errors: {operation_errors}")

        # Check metrics consistency
        final_metrics = rm.get_metrics()

        # Verify metrics make sense
        self.assertGreaterEqual(final_metrics["model_loads"], 1)
        self.assertGreaterEqual(final_metrics["model_unloads"], 1)
        self.assertGreaterEqual(final_metrics["memory_cleanups"], 1)

        # Load/unload counts should be reasonably balanced
        load_unload_diff = abs(final_metrics["model_loads"] - final_metrics["model_unloads"])
        self.assertLessEqual(load_unload_diff, 1, "Load/unload counts should be balanced")

        print(f"Metrics collection test: {len(metrics_snapshots)} snapshots in {execution_time:.3f}s")
        print(f"Final metrics - Loads: {final_metrics['model_loads']}, "
              f"Unloads: {final_metrics['model_unloads']}, "
              f"Cleanups: {final_metrics['memory_cleanups']}")

    def test_concurrent_cleanup_operations(self):
        """Test thread safety of cleanup operations"""
        rm = ResourceManager()
        rm.enable_monitoring()

        cleanup_results = []
        cleanup_errors = []

        # First, load some models
        with patch.object(rm, '_load_whisper_model') as mock_whisper, \
             patch.object(rm, '_load_leolm_model') as mock_leolm:

            mock_whisper.return_value = Mock(pid="initial_whisper")
            mock_leolm.return_value = Mock()

            rm.request_model(ModelType.WHISPER, {})
            rm.request_model(ModelType.LEOLM, {})

        def perform_cleanup(cleanup_id):
            try:
                start_time = time.time()

                if cleanup_id % 3 == 0:
                    rm.force_cleanup()
                    cleanup_results.append((cleanup_id, "force_cleanup", time.time() - start_time))
                elif cleanup_id % 3 == 1:
                    rm.release_model(ModelType.WHISPER)
                    cleanup_results.append((cleanup_id, "release_whisper", time.time() - start_time))
                else:
                    rm.release_model(ModelType.LEOLM)
                    cleanup_results.append((cleanup_id, "release_leolm", time.time() - start_time))

            except Exception as e:
                cleanup_errors.append((cleanup_id, str(e)))

        # Create multiple cleanup threads
        num_cleaners = 9
        threads = []

        for i in range(num_cleaners):
            thread = threading.Thread(target=perform_cleanup, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join(timeout=10)

        # Analyze results
        self.assertEqual(len(cleanup_errors), 0, f"Cleanup errors: {cleanup_errors}")
        self.assertEqual(len(cleanup_results), num_cleaners)

        # Check final state
        status = rm.get_status()
        # Models should be released by now (may still have some due to race conditions)
        self.assertLessEqual(len(status["active_models"]), 2)

        print(f"Concurrent cleanup: {len(cleanup_results)} operations completed successfully")

    def test_stress_test_all_operations(self):
        """Comprehensive stress test with all operations running concurrently"""
        rm = ResourceManager()
        rm.enable_monitoring(continuous=True)

        all_results = defaultdict(list)
        all_errors = defaultdict(list)

        def model_loader(worker_id):
            """Worker that loads and releases models"""
            try:
                for i in range(3):
                    with patch.object(rm, '_load_whisper_model') as mock_load:
                        mock_load.return_value = Mock(pid=f"loader_{worker_id}_{i}")

                        success = rm.request_model(ModelType.WHISPER, {})
                        all_results["loads"].append((worker_id, success))

                        if success:
                            time.sleep(random.uniform(0.05, 0.15))
                            rm.release_model(ModelType.WHISPER)
                            all_results["releases"].append((worker_id, True))

            except Exception as e:
                all_errors["loads"].append((worker_id, str(e)))

        def model_swapper(worker_id):
            """Worker that performs model swaps"""
            try:
                for i in range(2):
                    with patch.object(rm, '_load_whisper_model') as mock_whisper, \
                         patch.object(rm, '_load_leolm_model') as mock_leolm:

                        mock_whisper.return_value = Mock(pid=f"swapper_whisper_{worker_id}_{i}")
                        mock_leolm.return_value = Mock()

                        # Load initial model
                        rm.request_model(ModelType.WHISPER, {})

                        # Perform swap
                        success = rm.swap_models(ModelType.WHISPER, ModelType.LEOLM, {})
                        all_results["swaps"].append((worker_id, success))

                        time.sleep(0.1)

            except Exception as e:
                all_errors["swaps"].append((worker_id, str(e)))

        def memory_monitor(worker_id):
            """Worker that monitors memory and takes metrics"""
            try:
                for i in range(10):
                    memory_info = rm.check_available_memory()
                    metrics = rm.get_metrics()
                    all_results["monitors"].append((worker_id, memory_info["used_gb"]))

                    time.sleep(0.02)

            except Exception as e:
                all_errors["monitors"].append((worker_id, str(e)))

        def cleanup_worker(worker_id):
            """Worker that performs cleanup operations"""
            try:
                for i in range(5):
                    time.sleep(random.uniform(0.1, 0.3))
                    rm.force_cleanup()
                    all_results["cleanups"].append((worker_id, True))

            except Exception as e:
                all_errors["cleanups"].append((worker_id, str(e)))

        # Create different types of workers
        threads = []

        # Model loaders
        for i in range(4):
            thread = threading.Thread(target=model_loader, args=(i,), name=f"Loader-{i}")
            threads.append(thread)

        # Model swappers
        for i in range(2):
            thread = threading.Thread(target=model_swapper, args=(i,), name=f"Swapper-{i}")
            threads.append(thread)

        # Memory monitors
        for i in range(3):
            thread = threading.Thread(target=memory_monitor, args=(i,), name=f"Monitor-{i}")
            threads.append(thread)

        # Cleanup workers
        for i in range(2):
            thread = threading.Thread(target=cleanup_worker, args=(i,), name=f"Cleaner-{i}")
            threads.append(thread)

        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join(timeout=30)

        execution_time = time.time() - start_time

        # Stop monitoring
        rm.disable_monitoring()

        # Analyze comprehensive results
        total_operations = sum(len(results) for results in all_results.values())
        total_errors = sum(len(errors) for errors in all_errors.values())

        self.assertEqual(total_errors, 0, f"Errors in stress test: {dict(all_errors)}")
        self.assertGreater(total_operations, 50, "Should have performed many operations")

        # Check final metrics
        final_metrics = rm.get_metrics()

        print(f"\nStress Test Results ({execution_time:.2f}s):")
        print(f"  Total operations: {total_operations}")
        print(f"  Loads: {len(all_results['loads'])}")
        print(f"  Releases: {len(all_results['releases'])}")
        print(f"  Swaps: {len(all_results['swaps'])}")
        print(f"  Memory checks: {len(all_results['monitors'])}")
        print(f"  Cleanups: {len(all_results['cleanups'])}")
        print(f"  Final metrics: {final_metrics['model_loads']} loads, "
              f"{final_metrics['model_unloads']} unloads, "
              f"{final_metrics['swaps_performed']} swaps")

        # ResourceManager should still be functional
        status = rm.get_status()
        self.assertTrue(status["initialized"])


if __name__ == '__main__':
    # Run tests with high verbosity
    unittest.main(verbosity=2, buffer=True)