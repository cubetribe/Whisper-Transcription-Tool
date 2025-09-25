"""
Integration Tests for End-to-End Correction Workflow

Tests cover:
- Complete correction workflow from transcription to corrected output
- Integration between ResourceManager, BatchProcessor, and LLMCorrector
- Error recovery scenarios and partial failures
- Memory management during processing
- Progress reporting through event system
- File handling and cleanup

Author: QualityMarshal Agent
Version: 1.0.0
"""

import pytest
import asyncio
import tempfile
import os
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock

# Import the classes to test
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.whisper_transcription_tool.module5_text_correction.resource_manager import (
    ResourceManager, ModelType
)
from src.whisper_transcription_tool.module5_text_correction.batch_processor import (
    BatchProcessor, TextChunk
)
from src.whisper_transcription_tool.module5_text_correction.llm_corrector import LLMCorrector
from src.whisper_transcription_tool.module5_text_correction.correction_prompts import CorrectionPrompts
from src.whisper_transcription_tool.core.events import EventType, Event, publish, subscribe, unsubscribe


@pytest.mark.integration
class TestEndToEndCorrectionWorkflow:
    """Integration tests for complete correction workflow"""

    def setUp(self):
        """Set up test environment"""
        # Reset ResourceManager singleton
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

    def test_simple_correction_workflow(self, temp_model_file, sample_text_short):
        """Test basic end-to-end correction workflow"""
        self.setUp()

        # Mock dependencies
        with patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama') as mock_llama:
            mock_model = Mock()
            mock_model.return_value = {'choices': [{'text': 'Corrected text output'}]}
            mock_model.n_ctx.return_value = 2048
            mock_llama.return_value = mock_model

            # Initialize components
            rm = ResourceManager()
            batch_processor = BatchProcessor(max_context_length=500)
            correction_prompts = CorrectionPrompts()

            # Step 1: Load LeoLM model
            with patch.object(rm, '_load_leolm_model') as mock_load:
                mock_load.return_value = mock_model
                load_success = rm.request_model(ModelType.LEOLM, {
                    "model_path": temp_model_file
                })

            assert load_success is True

            # Step 2: Generate correction prompt
            prompt_data = correction_prompts.get_prompt(
                level="standard",
                text=sample_text_short
            )

            assert "system" in prompt_data
            assert "user" in prompt_data

            # Step 3: Process text through batch processor (short text = single chunk)
            chunks = batch_processor.chunk_text(sample_text_short)
            assert len(chunks) == 1

            # Step 4: Mock correction function
            def mock_correction_fn(text):
                return f"[CORRECTED] {text}"

            # Step 5: Process chunks
            corrected_text = batch_processor.process_chunks_sync(
                chunks, mock_correction_fn
            )

            assert "[CORRECTED]" in corrected_text
            assert sample_text_short in corrected_text

            # Step 6: Cleanup
            rm.release_model(ModelType.LEOLM)
            assert ModelType.LEOLM not in rm.active_models

        self.tearDown()

    @pytest.mark.asyncio
    async def test_async_correction_workflow(self, temp_model_file, sample_text_long):
        """Test asynchronous correction workflow with chunking"""
        self.setUp()

        events_received = []

        def event_handler(event):
            events_received.append(event)

        subscribe(EventType.PROGRESS_UPDATE, event_handler)

        try:
            with patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama') as mock_llama:
                mock_model = Mock()
                mock_model.return_value = {'choices': [{'text': 'Chunk corrected'}]}
                mock_model.n_ctx.return_value = 2048
                mock_llama.return_value = mock_model

                # Initialize components
                rm = ResourceManager()
                batch_processor = BatchProcessor(max_context_length=100)  # Small for chunking

                # Load model
                with patch.object(rm, '_load_leolm_model') as mock_load:
                    mock_load.return_value = mock_model
                    load_success = rm.request_model(ModelType.LEOLM, {
                        "model_path": temp_model_file
                    })

                assert load_success is True

                # Process long text (will create multiple chunks)
                chunks = batch_processor.chunk_text(sample_text_long)
                assert len(chunks) > 1

                # Progress callback
                progress_updates = []
                def progress_callback(current, total, status):
                    progress_updates.append((current, total, status))
                    # Simulate progress events
                    publish(Event(
                        event_type=EventType.PROGRESS_UPDATE,
                        data={
                            "progress": int(current / total * 100),
                            "status": status,
                            "task": "correction"
                        }
                    ))

                # Async correction function
                def mock_correction_fn(text):
                    time.sleep(0.01)  # Simulate processing time
                    return f"[ASYNC-CORRECTED] {text[:50]}..."

                # Process chunks asynchronously
                corrected_text = await batch_processor.process_chunks_async(
                    chunks, mock_correction_fn, progress_callback
                )

                assert "[ASYNC-CORRECTED]" in corrected_text
                assert len(progress_updates) == len(chunks)

                # Cleanup
                rm.release_model(ModelType.LEOLM)

        finally:
            unsubscribe(EventType.PROGRESS_UPDATE, event_handler)

        self.tearDown()

    def test_model_swapping_workflow(self, temp_model_file):
        """Test workflow with model swapping between Whisper and LeoLM"""
        self.setUp()

        with patch('subprocess.Popen') as mock_popen, \
             patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama') as mock_llama:

            # Mock Whisper process
            mock_whisper_process = Mock()
            mock_whisper_process.pid = 12345
            mock_whisper_process.poll.return_value = None
            mock_popen.return_value = mock_whisper_process

            # Mock LeoLM model
            mock_leolm_model = Mock()
            mock_leolm_model.return_value = {'choices': [{'text': 'Corrected by LeoLM'}]}
            mock_llama.return_value = mock_leolm_model

            rm = ResourceManager()
            rm.enable_monitoring()

            # Step 1: Load Whisper for transcription
            whisper_success = rm.request_model(ModelType.WHISPER, {
                "model": "large-v3-turbo",
                "whisper_cmd": ["whisper"],
                "input_file": "test.wav"
            })

            assert whisper_success is True
            assert ModelType.WHISPER in rm.active_models

            # Step 2: Swap to LeoLM for correction
            with patch.object(rm, '_load_leolm_model') as mock_load:
                mock_load.return_value = mock_leolm_model

                swap_success = rm.swap_models(
                    ModelType.WHISPER,
                    ModelType.LEOLM,
                    {"model_path": temp_model_file}
                )

            assert swap_success is True
            assert ModelType.WHISPER not in rm.active_models
            assert ModelType.LEOLM in rm.active_models
            assert rm.metrics.swaps_performed == 1

            # Step 3: Use LeoLM for correction
            batch_processor = BatchProcessor(max_context_length=500)
            test_text = "Das ist ein Test text mit fehler."

            chunks = batch_processor.chunk_text(test_text)

            def correction_fn(text):
                # Simulate using the loaded LeoLM model
                return f"Corrected: {text}"

            corrected = batch_processor.process_chunks_sync(chunks, correction_fn)
            assert "Corrected:" in corrected

            # Cleanup
            rm.cleanup_all()

        self.tearDown()

    def test_error_recovery_workflow(self, temp_model_file):
        """Test error recovery during correction workflow"""
        self.setUp()

        with patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama') as mock_llama:
            mock_model = Mock()
            mock_llama.return_value = mock_model

            rm = ResourceManager()
            batch_processor = BatchProcessor(max_context_length=100)

            # Load model successfully
            with patch.object(rm, '_load_leolm_model') as mock_load:
                mock_load.return_value = mock_model
                load_success = rm.request_model(ModelType.LEOLM, {
                    "model_path": temp_model_file
                })

            assert load_success is True

            # Create test chunks
            test_text = "First chunk. Second chunk that will fail. Third chunk."
            chunks = batch_processor.chunk_text(test_text)

            # Mock correction function that fails on second chunk
            def failing_correction_fn(text):
                if "fail" in text:
                    raise Exception("Correction failed for this chunk")
                return f"Corrected: {text}"

            # Process with error handling
            corrected_text = batch_processor.process_chunks_sync(
                chunks, failing_correction_fn
            )

            # Should still return merged text with failed chunk as original
            assert "Corrected:" in corrected_text
            assert "that will fail" in corrected_text  # Original text preserved

            # Cleanup
            rm.release_model(ModelType.LEOLM)

        self.tearDown()

    def test_memory_management_workflow(self, temp_model_file):
        """Test memory management during correction workflow"""
        self.setUp()

        with patch('psutil.virtual_memory') as mock_memory, \
             patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama') as mock_llama:

            # Mock memory with progression from high to low
            memory_calls = [
                Mock(total=16*1024**3, available=12*1024**3, percent=25),  # High memory
                Mock(total=16*1024**3, available=6*1024**3, percent=62.5),  # Medium memory
                Mock(total=16*1024**3, available=2*1024**3, percent=87.5),  # Low memory
            ]
            mock_memory.side_effect = memory_calls

            mock_model = Mock()
            mock_model.return_value = {'choices': [{'text': 'Corrected'}]}
            mock_llama.return_value = mock_model

            rm = ResourceManager()
            rm.enable_monitoring()

            # Load model when memory is sufficient
            with patch.object(rm, '_load_leolm_model') as mock_load:
                mock_load.return_value = mock_model
                load_success = rm.request_model(ModelType.LEOLM, {
                    "model_path": temp_model_file
                })

            assert load_success is True

            # Check memory status
            is_safe, message = rm._check_memory_threshold()
            assert isinstance(is_safe, bool)
            assert isinstance(message, str)

            # Force cleanup when memory gets low
            initial_cleanups = rm.metrics.memory_cleanups
            rm.force_cleanup()
            assert rm.metrics.memory_cleanups == initial_cleanups + 1

            # Cleanup
            rm.cleanup_all()

        self.tearDown()

    def test_file_handling_workflow(self, temp_directory):
        """Test file handling during correction workflow"""
        self.setUp()

        # Create test input file
        input_file = temp_directory / "input.txt"
        test_content = "Das ist ein Test text mit fehler. Mehr text hier."
        input_file.write_text(test_content, encoding='utf-8')

        output_file = temp_directory / "output.txt"
        metadata_file = temp_directory / "metadata.json"

        with patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama') as mock_llama:
            mock_model = Mock()
            mock_model.return_value = {'choices': [{'text': 'Das ist ein korrigierter Text.'}]}
            mock_llama.return_value = mock_model

            # Simulate file-based correction workflow
            rm = ResourceManager()

            with patch.object(rm, '_load_leolm_model') as mock_load:
                mock_load.return_value = mock_model

                # Load model
                load_success = rm.request_model(ModelType.LEOLM, {
                    "model_path": str(temp_directory / "fake_model.gguf")
                })

                # Create fake model file
                (temp_directory / "fake_model.gguf").write_bytes(b"fake model data")

                with patch('os.path.exists', return_value=True):
                    corrector = LLMCorrector(model_path=str(temp_directory / "fake_model.gguf"))

                    # Read input
                    text = input_file.read_text(encoding='utf-8')

                    # Process correction
                    corrected = corrector.correct_text(text, level="standard", language="de")

                    # Write output
                    output_file.write_text(corrected, encoding='utf-8')

                    # Write metadata
                    metadata = {
                        "input_file": str(input_file),
                        "output_file": str(output_file),
                        "correction_level": "standard",
                        "model_used": "leolm",
                        "processing_time": 1.5,
                        "chunks_processed": 1
                    }
                    metadata_file.write_text(json.dumps(metadata, indent=2), encoding='utf-8')

                    # Verify files
                    assert output_file.exists()
                    assert metadata_file.exists()

                    output_content = output_file.read_text(encoding='utf-8')
                    assert len(output_content) > 0

                    metadata_content = json.loads(metadata_file.read_text(encoding='utf-8'))
                    assert metadata_content["correction_level"] == "standard"

            # Cleanup
            rm.cleanup_all()

        self.tearDown()

    def test_concurrent_correction_workflow(self, temp_model_file):
        """Test concurrent correction workflows"""
        self.setUp()

        with patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama') as mock_llama:
            mock_model = Mock()
            mock_model.return_value = {'choices': [{'text': 'Concurrent correction'}]}
            mock_llama.return_value = mock_model

            rm = ResourceManager()
            rm.enable_monitoring()

            results = []
            errors = []

            def correction_workflow(thread_id):
                try:
                    # Each thread tries to process some text
                    batch_processor = BatchProcessor(max_context_length=200)
                    test_text = f"Thread {thread_id} test text with errors."

                    chunks = batch_processor.chunk_text(test_text)

                    def correction_fn(text):
                        time.sleep(0.01)  # Simulate processing
                        return f"Thread-{thread_id}-Corrected: {text}"

                    corrected = batch_processor.process_chunks_sync(chunks, correction_fn)
                    results.append((thread_id, corrected))

                except Exception as e:
                    errors.append((thread_id, str(e)))

            # Start multiple correction workflows
            import threading
            threads = [
                threading.Thread(target=correction_workflow, args=(i,))
                for i in range(3)
            ]

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join()

            # Check results
            assert len(errors) == 0, f"Errors occurred: {errors}"
            assert len(results) == 3

            for thread_id, corrected_text in results:
                assert f"Thread-{thread_id}-Corrected:" in corrected_text

            # Cleanup
            rm.cleanup_all()

        self.tearDown()

    @pytest.mark.asyncio
    async def test_progress_reporting_workflow(self, temp_model_file):
        """Test progress reporting during correction workflow"""
        self.setUp()

        events_received = []

        def progress_handler(event):
            events_received.append(event.data)

        subscribe(EventType.PROGRESS_UPDATE, progress_handler)

        try:
            with patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama') as mock_llama:
                mock_model = Mock()
                mock_model.return_value = {'choices': [{'text': 'Progress test'}]}
                mock_llama.return_value = mock_model

                rm = ResourceManager()
                batch_processor = BatchProcessor(max_context_length=50)

                # Load model
                with patch.object(rm, '_load_leolm_model') as mock_load:
                    mock_load.return_value = mock_model
                    rm.request_model(ModelType.LEOLM, {"model_path": temp_model_file})

                # Create text that will generate multiple chunks
                long_text = "This is chunk one. This is chunk two. This is chunk three. " * 10
                chunks = batch_processor.chunk_text(long_text)

                assert len(chunks) > 1

                progress_reports = []

                def progress_callback(current, total, status):
                    progress_reports.append({
                        "current": current,
                        "total": total,
                        "progress": int(current / total * 100),
                        "status": status
                    })

                    # Publish progress event
                    publish(Event(
                        event_type=EventType.PROGRESS_UPDATE,
                        data={
                            "progress": int(current / total * 100),
                            "current": current,
                            "total": total,
                            "status": status,
                            "task": "text_correction"
                        }
                    ))

                def correction_fn(text):
                    time.sleep(0.01)
                    return f"Processed: {text[:20]}..."

                # Process with progress reporting
                corrected = await batch_processor.process_chunks_async(
                    chunks, correction_fn, progress_callback
                )

                # Verify progress was reported
                assert len(progress_reports) == len(chunks)
                assert progress_reports[-1]["progress"] == 100

                # Verify events were received
                assert len(events_received) >= len(chunks)

                progress_events = [e for e in events_received if e.get("task") == "text_correction"]
                assert len(progress_events) > 0

                # Cleanup
                rm.release_model(ModelType.LEOLM)

        finally:
            unsubscribe(EventType.PROGRESS_UPDATE, progress_handler)

        self.tearDown()

    def test_configuration_driven_workflow(self, temp_model_file, mock_config):
        """Test workflow driven by configuration settings"""
        self.setUp()

        with patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama') as mock_llama:
            mock_model = Mock()
            mock_model.return_value = {'choices': [{'text': 'Config-driven correction'}]}
            mock_llama.return_value = mock_model

            # Test configuration
            correction_config = {
                "enabled": True,
                "level": "standard",
                "language": "de",
                "batch_size": 3,
                "max_context_length": 200,
                "model_path": temp_model_file
            }

            rm = ResourceManager()
            batch_processor = BatchProcessor(
                max_context_length=correction_config["max_context_length"]
            )
            correction_prompts = CorrectionPrompts()

            # Load model
            with patch.object(rm, '_load_leolm_model') as mock_load:
                mock_load.return_value = mock_model
                load_success = rm.request_model(ModelType.LEOLM, {
                    "model_path": correction_config["model_path"]
                })

            assert load_success is True

            # Process text according to configuration
            test_text = "Configuration test text with multiple sentences. Each sentence should be processed."
            chunks = batch_processor.chunk_text(test_text)

            # Generate prompt based on config
            prompt_data = correction_prompts.get_prompt(
                level=correction_config["level"],
                text=test_text
            )

            assert prompt_data["system"] is not None

            def config_driven_correction(text):
                # Simulate using configuration parameters
                return f"[{correction_config['level'].upper()}] {text}"

            corrected = batch_processor.process_chunks_sync(chunks, config_driven_correction)

            assert f"[{correction_config['level'].upper()}]" in corrected

            # Cleanup
            rm.release_model(ModelType.LEOLM)

        self.tearDown()


@pytest.mark.integration
class TestWorkflowErrorScenarios:
    """Integration tests for error scenarios in correction workflows"""

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

    def test_model_loading_failure_recovery(self):
        """Test recovery when model loading fails"""
        self.setUp()

        rm = ResourceManager()

        # Attempt to load non-existent model
        load_success = rm.request_model(ModelType.LEOLM, {
            "model_path": "/nonexistent/model.gguf"
        })

        assert load_success is False
        assert ModelType.LEOLM not in rm.active_models

        # Resource manager should still be functional
        status = rm.get_status()
        assert status["initialized"] is True

        self.tearDown()

    def test_insufficient_memory_workflow(self):
        """Test workflow behavior with insufficient memory"""
        self.setUp()

        with patch('psutil.virtual_memory') as mock_memory:
            # Mock very low memory
            mock_memory.return_value = Mock(
                total=2*1024**3,      # 2GB
                available=0.5*1024**3, # 512MB
                percent=75,
                free=0.5*1024**3
            )

            rm = ResourceManager()

            # Should fail to load LeoLM due to memory constraints
            load_success = rm.request_model(ModelType.LEOLM, {
                "model_path": "fake_model.gguf"
            })

            assert load_success is False

            # But Whisper should still work (lower memory requirements)
            with patch('subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_process.pid = 123
                mock_popen.return_value = mock_process

                whisper_success = rm.request_model(ModelType.WHISPER, {
                    "model": "tiny",  # Small model
                    "whisper_cmd": ["whisper"]
                })

                # Should succeed with small model
                assert whisper_success is True

        self.tearDown()

    def test_partial_chunk_failure_workflow(self, temp_model_file):
        """Test workflow when some chunks fail to process"""
        self.setUp()

        with patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama') as mock_llama:
            mock_model = Mock()
            mock_llama.return_value = mock_model

            rm = ResourceManager()
            batch_processor = BatchProcessor(max_context_length=100)

            # Load model
            with patch.object(rm, '_load_leolm_model') as mock_load:
                mock_load.return_value = mock_model
                rm.request_model(ModelType.LEOLM, {"model_path": temp_model_file})

            # Create text with problematic chunks
            test_text = "Good chunk. Bad chunk with error. Another good chunk."
            chunks = batch_processor.chunk_text(test_text)

            failed_chunks = []
            success_count = 0

            def partially_failing_correction(text):
                nonlocal success_count
                if "error" in text:
                    failed_chunks.append(text)
                    raise Exception(f"Processing failed for: {text}")
                success_count += 1
                return f"Corrected: {text}"

            # Process with partial failures
            corrected = batch_processor.process_chunks_sync(
                chunks, partially_failing_correction
            )

            # Should have partial success
            assert success_count > 0
            assert len(failed_chunks) > 0
            assert "Corrected:" in corrected
            assert "error" in corrected  # Failed chunk kept as original

            # Cleanup
            rm.release_model(ModelType.LEOLM)

        self.tearDown()

    def test_resource_exhaustion_workflow(self, temp_model_file):
        """Test workflow behavior under resource exhaustion"""
        self.setUp()

        with patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama') as mock_llama:
            mock_model = Mock()

            # Simulate resource exhaustion on some calls
            call_count = [0]
            def side_effect(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] > 3:  # Fail after 3 calls
                    raise MemoryError("Out of memory")
                return {'choices': [{'text': f'Response {call_count[0]}'}]}

            mock_model.side_effect = side_effect
            mock_llama.return_value = mock_model

            rm = ResourceManager()
            batch_processor = BatchProcessor(max_context_length=50)

            # Load model
            with patch.object(rm, '_load_leolm_model') as mock_load:
                mock_load.return_value = mock_model
                rm.request_model(ModelType.LEOLM, {"model_path": temp_model_file})

            # Create text that will generate multiple chunks
            long_text = "Chunk one. Chunk two. Chunk three. Chunk four. Chunk five."
            chunks = batch_processor.chunk_text(long_text)

            assert len(chunks) >= 4  # Should create enough chunks to trigger failure

            successful_corrections = 0
            failed_corrections = 0

            def resource_exhaustion_correction(text):
                nonlocal successful_corrections, failed_corrections
                try:
                    # This will eventually fail due to mock side effect
                    mock_model()
                    successful_corrections += 1
                    return f"Success: {text}"
                except MemoryError:
                    failed_corrections += 1
                    # Return original text when resource exhausted
                    return text

            corrected = batch_processor.process_chunks_sync(
                chunks, resource_exhaustion_correction
            )

            # Should have both successes and failures
            assert successful_corrections > 0
            assert failed_corrections > 0
            assert len(corrected) > 0

            # Cleanup
            rm.release_model(ModelType.LEOLM)

        self.tearDown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])