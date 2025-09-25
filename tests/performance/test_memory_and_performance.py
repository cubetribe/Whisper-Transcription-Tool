"""
Performance and Memory Tests for Text Correction System

Tests cover:
- Memory usage during model loading and processing
- Processing speed benchmarks for different text sizes
- Memory cleanup verification after operations
- Concurrent processing performance
- Resource leak detection
- Performance regression testing

Author: QualityMarshal Agent
Version: 1.0.0
"""

import pytest
import time
import threading
import gc
import psutil
import os
from pathlib import Path
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import the classes to test
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.whisper_transcription_tool.module5_text_correction.resource_manager import (
    ResourceManager, ModelType
)
from src.whisper_transcription_tool.module5_text_correction.batch_processor import BatchProcessor
from src.whisper_transcription_tool.module5_text_correction.llm_corrector import LLMCorrector


@pytest.mark.performance
class TestMemoryUsage:
    """Performance tests for memory usage and management"""

    def setUp(self):
        """Set up test environment"""
        ResourceManager._instance = None
        ResourceManager._initialized = False

    def tearDown(self):
        """Clean up test environment"""
        try:
            rm = ResourceManager()
            rm.cleanup_all()
        except:
            pass
        ResourceManager._instance = None
        ResourceManager._initialized = False
        gc.collect()  # Force garbage collection

    def get_memory_usage(self):
        """Get current memory usage in MB"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024

    def test_resource_manager_memory_overhead(self):
        """Test memory overhead of ResourceManager singleton"""
        self.setUp()

        # Measure baseline memory
        gc.collect()
        baseline_memory = self.get_memory_usage()

        # Create ResourceManager
        rm = ResourceManager()
        rm.enable_monitoring()

        # Measure memory after initialization
        gc.collect()
        after_init_memory = self.get_memory_usage()

        memory_overhead = after_init_memory - baseline_memory

        # ResourceManager should have minimal overhead
        assert memory_overhead < 5.0, f"ResourceManager overhead too high: {memory_overhead:.2f}MB"

        self.tearDown()

    def test_batch_processor_memory_scaling(self):
        """Test BatchProcessor memory usage scales with text size"""
        self.setUp()

        processor = BatchProcessor(max_context_length=500)

        # Test with different text sizes
        text_sizes = [
            ("small", "Short text. " * 10),
            ("medium", "Medium text with sentences. " * 100),
            ("large", "Large text for testing memory usage. " * 1000)
        ]

        memory_measurements = {}

        for size_name, text in text_sizes:
            gc.collect()
            before_memory = self.get_memory_usage()

            # Process text
            chunks = processor.chunk_text(text)

            gc.collect()
            after_memory = self.get_memory_usage()

            memory_used = after_memory - before_memory
            memory_measurements[size_name] = memory_used

            # Cleanup chunks
            del chunks
            gc.collect()

        # Memory usage should scale reasonably with text size
        assert memory_measurements["small"] < memory_measurements["medium"]
        assert memory_measurements["medium"] < memory_measurements["large"]

        # But shouldn't be excessive
        assert memory_measurements["large"] < 100.0, f"Large text processing uses too much memory: {memory_measurements['large']:.2f}MB"

        self.tearDown()

    @patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_llm_corrector_memory_cleanup(self, mock_llama, temp_model_file):
        """Test LLMCorrector properly cleans up memory"""
        self.setUp()

        mock_model = Mock()
        mock_model.return_value = {'choices': [{'text': 'Corrected text'}]}
        mock_model.n_ctx.return_value = 2048
        mock_llama.return_value = mock_model

        gc.collect()
        baseline_memory = self.get_memory_usage()

        # Load and use corrector
        corrector = LLMCorrector(model_path=temp_model_file)
        corrector.load_model()

        gc.collect()
        loaded_memory = self.get_memory_usage()

        # Process some text
        test_text = "Das ist ein Test text. " * 100
        corrected = corrector.correct_text(test_text, "standard", "de")

        gc.collect()
        after_processing_memory = self.get_memory_usage()

        # Unload model
        corrector.unload_model()
        del corrector

        gc.collect()
        after_cleanup_memory = self.get_memory_usage()

        # Verify memory is properly released
        cleanup_efficiency = (loaded_memory - after_cleanup_memory) / (loaded_memory - baseline_memory)

        # Should release at least 80% of allocated memory
        assert cleanup_efficiency > 0.8, f"Poor memory cleanup: only {cleanup_efficiency:.1%} released"

        self.tearDown()

    def test_resource_manager_model_swapping_memory(self):
        """Test memory usage during model swapping"""
        self.setUp()

        with patch('subprocess.Popen') as mock_popen, \
             patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama') as mock_llama:

            mock_whisper = Mock()
            mock_whisper.pid = 123
            mock_popen.return_value = mock_whisper

            mock_leolm = Mock()
            mock_leolm.return_value = {'choices': [{'text': 'Test'}]}
            mock_llama.return_value = mock_leolm

            rm = ResourceManager()
            rm.enable_monitoring()

            gc.collect()
            baseline_memory = self.get_memory_usage()

            # Load Whisper
            rm.request_model(ModelType.WHISPER, {
                "model": "large-v3-turbo",
                "whisper_cmd": ["whisper"]
            })

            gc.collect()
            whisper_memory = self.get_memory_usage()

            # Swap to LeoLM
            with patch.object(rm, '_load_leolm_model') as mock_load:
                mock_load.return_value = mock_leolm

                rm.swap_models(ModelType.WHISPER, ModelType.LEOLM, {
                    "model_path": "fake_model.gguf"
                })

            gc.collect()
            leolm_memory = self.get_memory_usage()

            # Cleanup all
            rm.cleanup_all()

            gc.collect()
            final_memory = self.get_memory_usage()

            # Memory should return close to baseline after cleanup
            memory_leak = final_memory - baseline_memory

            assert memory_leak < 10.0, f"Potential memory leak detected: {memory_leak:.2f}MB"

        self.tearDown()

    def test_concurrent_processing_memory_usage(self, temp_model_file):
        """Test memory usage under concurrent processing loads"""
        self.setUp()

        with patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama') as mock_llama:
            mock_model = Mock()
            mock_model.return_value = {'choices': [{'text': 'Concurrent result'}]}
            mock_llama.return_value = mock_model

            gc.collect()
            baseline_memory = self.get_memory_usage()

            def concurrent_processing_task(thread_id):
                """Task for concurrent processing"""
                processor = BatchProcessor(max_context_length=200)
                text = f"Thread {thread_id} processing text. " * 50

                chunks = processor.chunk_text(text)

                def mock_correction(chunk_text):
                    time.sleep(0.01)  # Simulate processing
                    return f"Thread-{thread_id}: {chunk_text[:20]}..."

                result = processor.process_chunks_sync(chunks, mock_correction)
                return len(result)

            # Run concurrent tasks
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [
                    executor.submit(concurrent_processing_task, i)
                    for i in range(10)
                ]

                # Monitor peak memory during execution
                peak_memory = baseline_memory

                for future in as_completed(futures):
                    current_memory = self.get_memory_usage()
                    peak_memory = max(peak_memory, current_memory)

                results = [future.result() for future in futures]

            gc.collect()
            final_memory = self.get_memory_usage()

            # All tasks should complete successfully
            assert len(results) == 10
            assert all(r > 0 for r in results)

            # Peak memory shouldn't be excessive
            peak_overhead = peak_memory - baseline_memory
            assert peak_overhead < 200.0, f"Peak memory overhead too high: {peak_overhead:.2f}MB"

            # Memory should be released after completion
            final_overhead = final_memory - baseline_memory
            assert final_overhead < 50.0, f"Memory not properly released: {final_overhead:.2f}MB"

        self.tearDown()


@pytest.mark.performance
class TestProcessingSpeed:
    """Performance tests for processing speed and throughput"""

    def setUp(self):
        """Set up test environment"""
        ResourceManager._instance = None
        ResourceManager._initialized = False

    def tearDown(self):
        """Clean up test environment"""
        try:
            rm = ResourceManager()
            rm.cleanup_all()
        except:
            pass
        ResourceManager._instance = None
        ResourceManager._initialized = False

    def test_batch_processor_chunking_speed(self):
        """Test BatchProcessor text chunking performance"""
        processor = BatchProcessor(max_context_length=500)

        # Test with different text sizes
        test_cases = [
            ("small", "Small text for testing. " * 10, 0.1),
            ("medium", "Medium text for performance testing. " * 100, 0.5),
            ("large", "Large text for comprehensive performance testing. " * 1000, 2.0),
            ("xlarge", "Extra large text for stress testing performance. " * 5000, 10.0)
        ]

        for size_name, text, max_time in test_cases:
            start_time = time.time()

            chunks = processor.chunk_text(text)

            processing_time = time.time() - start_time

            # Verify performance
            assert processing_time < max_time, f"{size_name} text chunking too slow: {processing_time:.2f}s > {max_time}s"

            # Verify correctness
            assert len(chunks) > 0
            total_text = ' '.join(chunk.text for chunk in chunks)
            assert len(total_text) > 0

            print(f"{size_name}: {len(text)} chars -> {len(chunks)} chunks in {processing_time:.3f}s")

    def test_token_estimation_speed(self, temp_model_file):
        """Test token estimation performance"""
        with patch('os.path.exists', return_value=True):
            corrector = LLMCorrector(model_path=temp_model_file)

        # Test with various text lengths
        test_texts = [
            ("short", "Kurzer Text."),
            ("medium", "Mittellanger Text mit mehreren Sätzen. " * 50),
            ("long", "Langer Text für Performance-Tests. " * 500),
            ("very_long", "Sehr langer Text für umfassende Performance-Tests. " * 2000)
        ]

        for size_name, text in test_texts:
            # Run multiple iterations for better timing
            iterations = 100
            start_time = time.time()

            for _ in range(iterations):
                token_count = corrector.estimate_tokens(text)

            total_time = time.time() - start_time
            avg_time = total_time / iterations

            # Should be very fast
            assert avg_time < 0.001, f"Token estimation too slow for {size_name}: {avg_time:.6f}s per call"
            assert token_count > 0

            print(f"{size_name} token estimation: {avg_time*1000:.3f}ms per call")

    @pytest.mark.asyncio
    async def test_async_processing_throughput(self):
        """Test async processing throughput"""
        processor = BatchProcessor(max_context_length=200)

        # Create multiple text chunks
        texts = [f"Async test text {i}. " * 20 for i in range(20)]
        all_chunks = []

        for text in texts:
            chunks = processor.chunk_text(text)
            all_chunks.extend(chunks)

        def fast_correction(text):
            # Simulate fast correction
            time.sleep(0.001)
            return f"Fast: {text[:30]}..."

        # Measure async processing throughput
        start_time = time.time()

        results = await processor.process_chunks_async(all_chunks, fast_correction)

        processing_time = time.time() - start_time

        # Calculate throughput
        chunks_per_second = len(all_chunks) / processing_time

        # Should achieve reasonable throughput
        assert chunks_per_second > 10, f"Async throughput too low: {chunks_per_second:.1f} chunks/second"

        print(f"Async processing throughput: {chunks_per_second:.1f} chunks/second")
        print(f"Processed {len(all_chunks)} chunks in {processing_time:.3f}s")

    def test_resource_manager_operation_speed(self):
        """Test ResourceManager operation performance"""
        self.setUp()

        rm = ResourceManager()

        # Test status checking speed
        start_time = time.time()
        for _ in range(100):
            status = rm.get_status()
        status_time = time.time() - start_time

        # Should be fast
        assert status_time < 1.0, f"Status checking too slow: {status_time:.3f}s for 100 calls"

        # Test memory checking speed
        start_time = time.time()
        for _ in range(100):
            memory_info = rm.check_available_memory()
        memory_time = time.time() - start_time

        assert memory_time < 1.0, f"Memory checking too slow: {memory_time:.3f}s for 100 calls"

        # Test monitoring enable/disable speed
        start_time = time.time()
        for _ in range(10):
            rm.enable_monitoring()
            rm.disable_monitoring()
        monitoring_time = time.time() - start_time

        assert monitoring_time < 0.5, f"Monitoring toggle too slow: {monitoring_time:.3f}s for 10 cycles"

        print(f"Status check: {status_time*10:.2f}ms per call")
        print(f"Memory check: {memory_time*10:.2f}ms per call")
        print(f"Monitor toggle: {monitoring_time*100:.2f}ms per cycle")

        self.tearDown()

    def test_prompt_generation_speed(self):
        """Test correction prompt generation performance"""
        from src.whisper_transcription_tool.module5_text_correction.correction_prompts import CorrectionPrompts

        cp = CorrectionPrompts()

        # Test texts of different sizes
        test_texts = [
            ("short", "Kurzer Text mit Fehlern."),
            ("medium", "Mittellanger Text mit verschiedenen Fehlern und Problemen. " * 20),
            ("long", "Langer Text für Performance-Tests mit vielen Sätzen. " * 100)
        ]

        for size_name, text in test_texts:
            iterations = 100
            start_time = time.time()

            for _ in range(iterations):
                prompt = cp.get_prompt("standard", text)
                token_estimate = cp.estimate_tokens(text, "standard")

            total_time = time.time() - start_time
            avg_time = total_time / iterations

            # Should be very fast
            assert avg_time < 0.01, f"Prompt generation too slow for {size_name}: {avg_time:.6f}s per call"

            print(f"{size_name} prompt generation: {avg_time*1000:.3f}ms per call")


@pytest.mark.performance
class TestResourceLeakDetection:
    """Tests for detecting resource leaks and cleanup issues"""

    def setUp(self):
        """Set up test environment"""
        ResourceManager._instance = None
        ResourceManager._initialized = False

    def tearDown(self):
        """Clean up test environment"""
        try:
            rm = ResourceManager()
            rm.cleanup_all()
        except:
            pass
        ResourceManager._instance = None
        ResourceManager._initialized = False

    def test_repeated_operations_memory_stability(self):
        """Test memory stability during repeated operations"""
        self.setUp()

        processor = BatchProcessor(max_context_length=200)

        # Record initial memory
        gc.collect()
        initial_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024

        memory_samples = [initial_memory]

        # Perform repeated operations
        for i in range(50):
            text = f"Repeated operation test {i}. " * 20
            chunks = processor.chunk_text(text)

            def mock_correction(chunk_text):
                return f"Processed: {chunk_text[:20]}..."

            result = processor.process_chunks_sync(chunks, mock_correction)

            # Sample memory every 10 iterations
            if i % 10 == 9:
                gc.collect()
                current_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)

        # Check for memory growth trend
        memory_growth = memory_samples[-1] - memory_samples[0]

        # Should not have significant memory growth
        assert memory_growth < 50.0, f"Potential memory leak: {memory_growth:.2f}MB growth over 50 iterations"

        # Check that memory doesn't grow monotonically
        max_growth = max(memory_samples) - memory_samples[0]
        assert max_growth < 100.0, f"Peak memory growth too high: {max_growth:.2f}MB"

        print(f"Memory stability test: {memory_growth:.2f}MB growth over 50 iterations")

        self.tearDown()

    def test_thread_cleanup_verification(self):
        """Test that threads are properly cleaned up"""
        self.setUp()

        initial_thread_count = threading.active_count()

        rm = ResourceManager()

        # Enable continuous monitoring (creates thread)
        rm.enable_monitoring(continuous=True)

        monitoring_thread_count = threading.active_count()
        assert monitoring_thread_count > initial_thread_count

        # Disable monitoring
        rm.disable_monitoring()

        # Wait a bit for thread cleanup
        time.sleep(0.1)

        final_thread_count = threading.active_count()

        # Thread count should return to initial level
        assert final_thread_count <= initial_thread_count, f"Threads not cleaned up: {initial_thread_count} -> {final_thread_count}"

        self.tearDown()

    def test_file_handle_cleanup(self, temp_directory):
        """Test that file handles are properly cleaned up"""
        # Get initial file descriptor count
        process = psutil.Process(os.getpid())
        initial_fds = process.num_fds() if hasattr(process, 'num_fds') else 0

        # Perform operations that create/use files
        processor = BatchProcessor()

        for i in range(20):
            # Simulate file operations
            temp_file = temp_directory / f"test_{i}.txt"
            temp_file.write_text(f"Test content {i}")

            # Read file
            content = temp_file.read_text()

            # Process content
            chunks = processor.chunk_text(content)

            # Cleanup file
            temp_file.unlink()

        # Check file descriptor count
        final_fds = process.num_fds() if hasattr(process, 'num_fds') else 0

        if initial_fds > 0 and final_fds > 0:
            fd_growth = final_fds - initial_fds
            assert fd_growth < 5, f"Potential file descriptor leak: {fd_growth} new FDs"

    def test_model_reference_cleanup(self, temp_model_file):
        """Test that model references are properly cleaned up"""
        self.setUp()

        with patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama') as mock_llama:
            mock_model = Mock()
            mock_llama.return_value = mock_model

            # Create and cleanup multiple correctors
            for i in range(10):
                corrector = LLMCorrector(model_path=temp_model_file)
                corrector.load_model()
                corrector.unload_model()
                del corrector

            gc.collect()

            # Should not have accumulated references
            assert len(gc.get_referrers(mock_llama)) < 20, "Potential reference leak detected"

        self.tearDown()


@pytest.mark.performance
class TestStressTests:
    """Stress tests for system limits and edge cases"""

    def setUp(self):
        """Set up test environment"""
        ResourceManager._instance = None
        ResourceManager._initialized = False

    def tearDown(self):
        """Clean up test environment"""
        try:
            rm = ResourceManager()
            rm.cleanup_all()
        except:
            pass
        ResourceManager._instance = None
        ResourceManager._initialized = False

    @pytest.mark.slow
    def test_large_text_processing_stress(self):
        """Stress test with very large text input"""
        processor = BatchProcessor(max_context_length=500)

        # Create very large text (several MB)
        large_text = "Large stress test text with multiple sentences for comprehensive testing. " * 50000  # ~3.5MB

        start_time = time.time()
        chunks = processor.chunk_text(large_text)
        chunking_time = time.time() - start_time

        # Should handle large text within reasonable time
        assert chunking_time < 30.0, f"Large text chunking too slow: {chunking_time:.2f}s"

        # Should create reasonable number of chunks
        assert len(chunks) > 100, "Not enough chunks created for large text"
        assert len(chunks) < 10000, "Too many chunks created"

        print(f"Large text stress test: {len(large_text)} chars -> {len(chunks)} chunks in {chunking_time:.2f}s")

    @pytest.mark.slow
    def test_concurrent_resource_manager_stress(self):
        """Stress test ResourceManager with high concurrency"""
        self.setUp()

        rm = ResourceManager()
        rm.enable_monitoring()

        results = []
        errors = []

        def stress_task(thread_id):
            try:
                # Perform various operations
                for i in range(20):
                    status = rm.get_status()
                    memory_info = rm.check_available_memory()

                    # Simulate some processing
                    time.sleep(0.001)

                results.append(thread_id)
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Run many concurrent threads
        threads = [threading.Thread(target=stress_task, args=(i,)) for i in range(50)]

        start_time = time.time()

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        total_time = time.time() - start_time

        # All threads should complete without errors
        assert len(errors) == 0, f"Errors occurred during stress test: {errors[:5]}"
        assert len(results) == 50

        # Should complete within reasonable time
        assert total_time < 10.0, f"Concurrent stress test too slow: {total_time:.2f}s"

        print(f"Concurrent stress test: 50 threads completed in {total_time:.2f}s")

        self.tearDown()

    @pytest.mark.slow
    def test_memory_pressure_handling(self):
        """Test system behavior under simulated memory pressure"""
        self.setUp()

        with patch('psutil.virtual_memory') as mock_memory:
            # Simulate decreasing available memory
            memory_levels = [
                Mock(available=8*1024**3, percent=50),    # 8GB available
                Mock(available=4*1024**3, percent=75),    # 4GB available
                Mock(available=2*1024**3, percent=87.5),  # 2GB available
                Mock(available=1*1024**3, percent=93.75), # 1GB available
            ]

            rm = ResourceManager()
            rm.enable_monitoring()

            for i, memory_state in enumerate(memory_levels):
                mock_memory.return_value = memory_state

                # Check system response to memory pressure
                memory_info = rm.check_available_memory()
                is_safe, message = rm._check_memory_threshold()

                # System should respond appropriately to memory pressure
                if i >= 2:  # Low memory scenarios
                    assert not is_safe, f"Should detect memory pressure at level {i}"

                # Force cleanup under pressure
                if i == 3:  # Lowest memory
                    initial_cleanups = rm.metrics.memory_cleanups
                    rm.force_cleanup()
                    assert rm.metrics.memory_cleanups > initial_cleanups

        self.tearDown()

    def test_rapid_model_operations_stress(self):
        """Stress test rapid model loading/unloading operations"""
        self.setUp()

        with patch('subprocess.Popen') as mock_popen, \
             patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama') as mock_llama:

            mock_whisper = Mock()
            mock_whisper.pid = 123
            mock_popen.return_value = mock_whisper

            mock_leolm = Mock()
            mock_llama.return_value = mock_leolm

            rm = ResourceManager()
            rm.enable_monitoring()

            start_time = time.time()

            # Rapidly load/unload models
            for i in range(20):
                # Load Whisper
                success = rm.request_model(ModelType.WHISPER, {
                    "model": "tiny",
                    "whisper_cmd": ["whisper"]
                })
                assert success

                # Quick operation
                status = rm.get_status()

                # Release Whisper
                rm.release_model(ModelType.WHISPER)

            total_time = time.time() - start_time

            # Should handle rapid operations efficiently
            assert total_time < 5.0, f"Rapid model operations too slow: {total_time:.2f}s"

            # Verify clean state
            assert len(rm.active_models) == 0

            print(f"Rapid model operations: 20 cycles in {total_time:.2f}s")

        self.tearDown()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])