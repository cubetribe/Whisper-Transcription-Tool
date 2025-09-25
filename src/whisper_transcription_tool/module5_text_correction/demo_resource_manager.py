#!/usr/bin/env python3
"""
ResourceManager Demo Script

This script demonstrates the full functionality of the ResourceManager:
- Singleton pattern and thread safety
- Memory monitoring and thresholds
- Model loading and swapping
- Performance metrics
- Error recovery

Usage:
    python demo_resource_manager.py

Author: ResourceSentinel Agent
Version: 1.0.0
"""

import sys
import time
import threading
from pathlib import Path
from unittest.mock import patch, Mock

# Add the src directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from whisper_transcription_tool.module5_text_correction.resource_manager import (
    ResourceManager, ModelType
)


def demo_singleton_pattern():
    """Demonstrate thread-safe singleton pattern"""
    print("\n=== 1. Singleton Pattern Demo ===")

    instances = []

    def create_instance(thread_id):
        rm = ResourceManager()
        instances.append((thread_id, id(rm)))

    # Create multiple threads
    threads = []
    for i in range(10):
        thread = threading.Thread(target=create_instance, args=(i,))
        threads.append(thread)

    start_time = time.time()
    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    creation_time = time.time() - start_time

    # Check all instances are the same
    unique_ids = set(instance_id for _, instance_id in instances)

    print(f"✓ Created {len(instances)} instances in {creation_time:.3f}s")
    print(f"✓ Unique instance IDs: {len(unique_ids)} (should be 1)")
    print(f"✓ Singleton pattern working correctly: {len(unique_ids) == 1}")


def demo_memory_monitoring():
    """Demonstrate memory monitoring capabilities"""
    print("\n=== 2. Memory Monitoring Demo ===")

    rm = ResourceManager()

    # Check initial memory
    memory_info = rm.check_available_memory()
    print(f"✓ Total system memory: {memory_info['total_gb']:.1f}GB")
    print(f"✓ Currently used: {memory_info['used_gb']:.1f}GB ({memory_info['percent_used']:.1f}%)")
    print(f"✓ Available: {memory_info['available_gb']:.1f}GB")

    # Check memory safety
    is_safe, warning = rm._check_memory_threshold()
    print(f"✓ Memory is safe: {is_safe}")
    if warning:
        print(f"  Warning: {warning}")

    # Test force cleanup
    print("\n--- Testing Force Cleanup ---")
    rm.enable_monitoring()
    initial_cleanups = rm.metrics.memory_cleanups

    rm.force_cleanup()

    final_cleanups = rm.metrics.memory_cleanups
    print(f"✓ Force cleanup executed (cleanups: {initial_cleanups} → {final_cleanups})")


def demo_gpu_detection():
    """Demonstrate GPU acceleration detection"""
    print("\n=== 3. GPU Acceleration Detection ===")

    rm = ResourceManager()

    print(f"✓ Detected GPU acceleration: {rm.gpu_acceleration}")

    if rm.gpu_acceleration == "metal":
        print("  → macOS Metal Performance Shaders available")
    elif rm.gpu_acceleration == "cuda":
        print("  → NVIDIA CUDA acceleration available")
    else:
        print("  → CPU-only processing (no GPU acceleration)")


def demo_model_operations():
    """Demonstrate model loading, swapping, and resource management"""
    print("\n=== 4. Model Operations Demo ===")

    rm = ResourceManager()
    rm.enable_monitoring()

    print("--- Mock Model Loading ---")

    # Mock Whisper model loading
    with patch.object(rm, '_load_whisper_model') as mock_whisper:
        mock_process = Mock()
        mock_process.pid = 12345
        mock_whisper.return_value = mock_process

        # Load Whisper model
        print("Loading Whisper model...")
        success = rm.request_model(ModelType.WHISPER, {"model": "large-v3-turbo"})
        print(f"✓ Whisper model loaded: {success}")

        if success:
            print(f"  Active models: {[m.value for m in rm.active_models.keys()]}")

            # Check resource usage
            resource = rm.active_models[ModelType.WHISPER]
            print(f"  Memory usage: {resource.memory_usage:.1f}GB")
            print(f"  Load time: {resource.load_time:.2f}s")

    print("\n--- Mock Model Swapping ---")

    # Mock LeoLM model for swapping
    with patch.object(rm, '_load_leolm_model') as mock_leolm:
        mock_llm = Mock()
        mock_leolm.return_value = mock_llm

        print("Swapping from Whisper to LeoLM...")
        start_time = time.time()
        success = rm.swap_models(ModelType.WHISPER, ModelType.LEOLM, {"model_path": "test.gguf"})
        swap_time = time.time() - start_time

        print(f"✓ Model swap completed: {success}")
        print(f"  Swap time: {swap_time:.2f}s")
        print(f"  Active models after swap: {[m.value for m in rm.active_models.keys()]}")

    # Clean up
    print("\n--- Cleanup ---")
    rm.cleanup_all()
    print(f"✓ All models cleaned up, active: {len(rm.active_models)}")


def demo_performance_monitoring():
    """Demonstrate performance monitoring and metrics"""
    print("\n=== 5. Performance Monitoring Demo ===")

    rm = ResourceManager()
    rm.enable_monitoring(continuous=True)

    print("Starting continuous monitoring...")

    # Simulate some operations
    with patch.object(rm, '_load_whisper_model') as mock_whisper:
        mock_whisper.return_value = Mock(pid=999)

        # Perform several load/release cycles
        for i in range(3):
            print(f"  Operation cycle {i+1}...")
            rm.request_model(ModelType.WHISPER, {})
            time.sleep(0.1)  # Brief hold
            rm.release_model(ModelType.WHISPER)
            rm.force_cleanup()
            time.sleep(0.1)

    # Let continuous monitoring run briefly
    time.sleep(0.5)

    # Get final metrics
    metrics = rm.get_metrics()

    print("\n--- Performance Metrics ---")
    print(f"✓ Model loads: {metrics['model_loads']}")
    print(f"✓ Model unloads: {metrics['model_unloads']}")
    print(f"✓ Memory cleanups: {metrics['memory_cleanups']}")
    print(f"✓ Average load time: {metrics['average_load_time']:.3f}s")
    print(f"✓ Peak memory usage: {metrics['peak_memory_usage']:.1f}GB")
    print(f"✓ Current memory utilization: {metrics['memory_utilization']:.1f}%")

    # Stop monitoring
    rm.disable_monitoring()
    print("✓ Continuous monitoring stopped")


def demo_thread_safety():
    """Demonstrate thread safety under concurrent operations"""
    print("\n=== 6. Thread Safety Demo ===")

    rm = ResourceManager()
    rm.enable_monitoring()

    results = []
    errors = []

    def concurrent_operations(worker_id):
        try:
            # Mock model operations
            with patch.object(rm, '_load_whisper_model') as mock_load:
                mock_load.return_value = Mock(pid=worker_id * 1000)

                for op in range(2):
                    # Try to load model
                    success = rm.request_model(ModelType.WHISPER, {"worker": worker_id})
                    results.append((worker_id, op, success))

                    if success:
                        time.sleep(0.01)  # Brief hold
                        rm.release_model(ModelType.WHISPER)

                    # Force cleanup occasionally
                    if op % 2 == 0:
                        rm.force_cleanup()

        except Exception as e:
            errors.append((worker_id, str(e)))

    # Create concurrent workers
    threads = []
    num_workers = 5

    print(f"Starting {num_workers} concurrent workers...")

    start_time = time.time()
    for i in range(num_workers):
        thread = threading.Thread(target=concurrent_operations, args=(i,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    execution_time = time.time() - start_time

    print(f"✓ Concurrent operations completed in {execution_time:.3f}s")
    print(f"✓ Total operations: {len(results)}")
    print(f"✓ Errors: {len(errors)}")
    print(f"✓ Success rate: {len([r for r in results if r[2]])/max(len(results), 1)*100:.1f}%")

    # Final metrics
    metrics = rm.get_metrics()
    print(f"✓ Final loads/unloads: {metrics['model_loads']}/{metrics['model_unloads']}")


def demo_status_reporting():
    """Demonstrate status reporting capabilities"""
    print("\n=== 7. Status Reporting Demo ===")

    rm = ResourceManager()
    rm.enable_monitoring()

    status = rm.get_status()

    print("--- System Status ---")
    print(f"✓ Initialized: {status['initialized']}")
    print(f"✓ Monitoring enabled: {status['monitoring_enabled']}")
    print(f"✓ GPU acceleration: {status['gpu_acceleration']}")
    print(f"✓ Memory safe: {status['memory_safe']}")

    if status['memory_warning']:
        print(f"⚠  Memory warning: {status['memory_warning']}")

    print("\n--- System Information ---")
    sys_info = status['system_info']
    print(f"✓ Total system memory: {sys_info['total_memory_gb']:.1f}GB")

    current_memory = sys_info['current_memory']
    print(f"✓ Current usage: {current_memory['used_gb']:.1f}GB ({current_memory['percent_used']:.1f}%)")

    thresholds = sys_info['memory_thresholds']
    print(f"✓ Warning threshold: {thresholds['warning']*100:.0f}%")
    print(f"✓ Critical threshold: {thresholds['critical']*100:.0f}%")

    print(f"✓ Active models: {len(status['active_models'])}")
    print(f"✓ Continuous monitoring: {status['continuous_monitoring']}")


def main():
    """Run all demonstrations"""
    print("🤖 ResourceManager Comprehensive Demo")
    print("=====================================")

    try:
        demo_singleton_pattern()
        demo_memory_monitoring()
        demo_gpu_detection()
        demo_model_operations()
        demo_performance_monitoring()
        demo_thread_safety()
        demo_status_reporting()

        print("\n🎉 All Demonstrations Completed Successfully!")
        print("\nResourceManager Features Demonstrated:")
        print("✅ Thread-safe Singleton pattern")
        print("✅ Memory monitoring with psutil integration")
        print("✅ GPU acceleration detection (Metal/CUDA/CPU)")
        print("✅ Model resource management and lifecycle")
        print("✅ Model swapping with cleanup delays")
        print("✅ Performance metrics collection")
        print("✅ Continuous monitoring capabilities")
        print("✅ Thread safety under concurrent operations")
        print("✅ Comprehensive status reporting")
        print("✅ Error recovery and cleanup")

    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())