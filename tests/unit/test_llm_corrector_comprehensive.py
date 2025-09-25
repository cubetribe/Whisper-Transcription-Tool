"""
Comprehensive Unit Tests for LLMCorrector

Tests cover:
- Model loading with various scenarios (success, failure, missing files)
- Text correction with different levels and languages
- Token management and chunking
- Memory management and cleanup
- Error handling and recovery
- Context manager functionality
- Mock-based testing for LLM calls

Author: QualityMarshal Agent
Version: 1.0.0
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import threading
import time
from pathlib import Path

# Import the classes to test
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.whisper_transcription_tool.module5_text_correction.llm_corrector import (
    LLMCorrector,
    correct_text_quick,
    LLAMA_CPP_AVAILABLE
)


class TestLLMCorrectorInitialization:
    """Test suite for LLMCorrector initialization and setup"""

    def test_init_with_defaults(self, mock_config):
        """Test initialization with default parameters"""
        with patch('os.path.exists', return_value=True):
            corrector = LLMCorrector()

            assert corrector.model_path == Path(LLMCorrector.DEFAULT_MODEL_PATH)
            assert corrector.context_length == 2048
            assert corrector.temperature == 0.3
            assert corrector.model is None
            assert not corrector._model_loaded

    def test_init_with_custom_parameters(self, temp_model_file):
        """Test initialization with custom parameters"""
        corrector = LLMCorrector(
            model_path=temp_model_file,
            context_length=4096,
            temperature=0.7,
            top_p=0.95,
            top_k=50
        )

        assert corrector.model_path == Path(temp_model_file)
        assert corrector.context_length == 4096
        assert corrector.temperature == 0.7
        assert corrector.top_p == 0.95
        assert corrector.top_k == 50

    def test_init_with_nonexistent_model(self):
        """Test initialization with non-existent model file"""
        with pytest.raises(FileNotFoundError):
            LLMCorrector(model_path="/nonexistent/path/model.gguf")

    @patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.LLAMA_CPP_AVAILABLE', False)
    def test_init_without_llama_cpp(self, temp_model_file):
        """Test initialization when llama-cpp-python is unavailable"""
        with pytest.raises(ImportError, match="llama-cpp-python is required"):
            LLMCorrector(model_path=temp_model_file)

    def test_init_validates_parameters(self, temp_model_file):
        """Test parameter validation during initialization"""
        # Test invalid context length
        with pytest.raises(ValueError):
            LLMCorrector(model_path=temp_model_file, context_length=0)

        # Test invalid temperature
        with pytest.raises(ValueError):
            LLMCorrector(model_path=temp_model_file, temperature=-0.1)

        with pytest.raises(ValueError):
            LLMCorrector(model_path=temp_model_file, temperature=2.1)


class TestLLMCorrectorModelManagement:
    """Test suite for model loading, unloading, and management"""

    @patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    @patch('os.cpu_count', return_value=8)
    @patch('psutil.virtual_memory')
    def test_load_model_success(self, mock_memory, mock_cpu_count, mock_llama, temp_model_file):
        """Test successful model loading"""
        # Mock memory availability
        mock_memory.return_value.available = 8 * 1024**3  # 8GB

        mock_model = Mock()
        mock_model.n_ctx.return_value = 2048
        mock_model.n_vocab.return_value = 32000
        mock_llama.return_value = mock_model

        corrector = LLMCorrector(model_path=temp_model_file)
        result = corrector.load_model()

        assert result is True
        assert corrector.is_model_loaded()
        assert corrector.model == mock_model

        # Verify Llama was called with correct parameters
        mock_llama.assert_called_once()
        call_args = mock_llama.call_args
        assert call_args[1]['model_path'] == temp_model_file
        assert call_args[1]['n_ctx'] == 2048

    @patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_load_model_failure(self, mock_llama, temp_model_file):
        """Test model loading failure"""
        mock_llama.side_effect = Exception("Failed to load model")

        corrector = LLMCorrector(model_path=temp_model_file)
        result = corrector.load_model()

        assert result is False
        assert not corrector.is_model_loaded()
        assert corrector.model is None

    @patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    @patch('psutil.virtual_memory')
    def test_load_model_insufficient_memory(self, mock_memory, mock_llama, temp_model_file):
        """Test model loading with insufficient memory"""
        # Mock low memory availability
        mock_memory.return_value.available = 1 * 1024**3  # 1GB

        corrector = LLMCorrector(model_path=temp_model_file)
        result = corrector.load_model()

        # Should fail due to insufficient memory
        assert result is False
        mock_llama.assert_not_called()

    @patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_load_model_already_loaded(self, mock_llama, temp_model_file):
        """Test loading model when already loaded"""
        mock_model = Mock()
        mock_llama.return_value = mock_model

        corrector = LLMCorrector(model_path=temp_model_file)

        # Load once
        corrector.load_model()

        # Load again - should not recreate
        result = corrector.load_model()

        assert result is True
        mock_llama.assert_called_once()  # Only called once

    def test_unload_model(self, temp_model_file):
        """Test model unloading"""
        corrector = LLMCorrector(model_path=temp_model_file)

        # Mock loaded state
        corrector.model = Mock()
        corrector._model_loaded = True
        corrector._load_time = 1.5

        corrector.unload_model()

        assert corrector.model is None
        assert not corrector._model_loaded
        assert corrector._load_time == 0.0

    def test_unload_model_not_loaded(self, temp_model_file):
        """Test unloading when no model is loaded"""
        corrector = LLMCorrector(model_path=temp_model_file)

        # Should not raise exception
        corrector.unload_model()

        assert corrector.model is None
        assert not corrector._model_loaded

    @patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_get_context_length(self, mock_llama, temp_model_file):
        """Test getting context length"""
        corrector = LLMCorrector(model_path=temp_model_file, context_length=4096)

        # When model not loaded
        assert corrector.get_context_length() == 4096

        # When model is loaded
        mock_model = Mock()
        mock_model.n_ctx.return_value = 2048
        mock_llama.return_value = mock_model

        corrector.load_model()
        assert corrector.get_context_length() == 2048


class TestLLMCorrectorTokenization:
    """Test suite for tokenization and token management"""

    def test_estimate_tokens_empty(self, temp_model_file):
        """Test token estimation for empty text"""
        corrector = LLMCorrector(model_path=temp_model_file)

        assert corrector.estimate_tokens("") == 1  # Minimum 1 token
        assert corrector.estimate_tokens("   ") == 1  # Whitespace only

    def test_estimate_tokens_various_lengths(self, temp_model_file):
        """Test token estimation for various text lengths"""
        corrector = LLMCorrector(model_path=temp_model_file)

        # Short text
        short_tokens = corrector.estimate_tokens("Kurzer Text")
        assert short_tokens > 1

        # Long text
        long_text = "Das ist ein sehr langer Text. " * 20
        long_tokens = corrector.estimate_tokens(long_text)
        assert long_tokens > short_tokens

    @patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_tokenize_with_model(self, mock_llama, temp_model_file):
        """Test tokenization using loaded model"""
        mock_model = Mock()
        mock_model.tokenize.return_value = [1, 2, 3, 4, 5]
        mock_llama.return_value = mock_model

        corrector = LLMCorrector(model_path=temp_model_file)
        corrector.load_model()

        tokens = corrector.tokenize("Test text")

        assert tokens == [1, 2, 3, 4, 5]
        mock_model.tokenize.assert_called_once_with(b"Test text")

    def test_tokenize_without_model(self, temp_model_file):
        """Test tokenization without loaded model"""
        corrector = LLMCorrector(model_path=temp_model_file)

        with pytest.raises(RuntimeError, match="Model not loaded"):
            corrector.tokenize("Test text")

    def test_chunk_text_short(self, temp_model_file):
        """Test chunking short text"""
        corrector = LLMCorrector(model_path=temp_model_file)
        text = "Kurzer Testtext."

        chunks = corrector.chunk_text(text, max_tokens=100)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_text_long(self, temp_model_file):
        """Test chunking long text"""
        corrector = LLMCorrector(model_path=temp_model_file)
        text = "Das ist ein langer Testtext. " * 50

        chunks = corrector.chunk_text(text, max_tokens=50)

        assert len(chunks) > 1
        # Each chunk should be within token limit
        for chunk in chunks:
            tokens = corrector.estimate_tokens(chunk)
            assert tokens <= 50

    def test_chunk_text_with_default_limit(self, temp_model_file):
        """Test chunking with default token limit"""
        corrector = LLMCorrector(model_path=temp_model_file, context_length=2048)
        text = "Das ist ein langer Testtext. " * 100

        chunks = corrector.chunk_text(text)

        # Should use 80% of context length as default
        expected_max = int(2048 * 0.8)
        for chunk in chunks:
            tokens = corrector.estimate_tokens(chunk)
            assert tokens <= expected_max


class TestLLMCorrectorTextGeneration:
    """Test suite for text generation and correction"""

    @patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_generate_correction_success(self, mock_llama, temp_model_file):
        """Test successful text generation"""
        mock_model = Mock()
        mock_model.return_value = {
            'choices': [{'text': '  "Korrigierter Text hier"  '}]
        }
        mock_llama.return_value = mock_model

        corrector = LLMCorrector(model_path=temp_model_file)
        corrector.load_model()

        result = corrector._generate_correction("Test prompt")

        # Should clean up quotes and whitespace
        assert result == "Korrigierter Text hier"
        mock_model.assert_called_once()

    @patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_generate_correction_with_parameters(self, mock_llama, temp_model_file):
        """Test generation with specific parameters"""
        mock_model = Mock()
        mock_model.return_value = {'choices': [{'text': 'Generated text'}]}
        mock_llama.return_value = mock_model

        corrector = LLMCorrector(
            model_path=temp_model_file,
            temperature=0.5,
            top_p=0.8,
            top_k=40
        )
        corrector.load_model()

        corrector._generate_correction("Test prompt")

        # Verify parameters were passed
        call_args = mock_model.call_args
        assert call_args[1]['temperature'] == 0.5
        assert call_args[1]['top_p'] == 0.8
        assert call_args[1]['top_k'] == 40

    def test_generate_correction_without_model(self, temp_model_file):
        """Test generation without loaded model"""
        corrector = LLMCorrector(model_path=temp_model_file)

        with pytest.raises(RuntimeError, match="Model not loaded"):
            corrector._generate_correction("Test prompt")

    @patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_generate_correction_handles_exceptions(self, mock_llama, temp_model_file):
        """Test generation handles LLM exceptions"""
        mock_model = Mock()
        mock_model.side_effect = Exception("LLM generation failed")
        mock_llama.return_value = mock_model

        corrector = LLMCorrector(model_path=temp_model_file)
        corrector.load_model()

        with pytest.raises(Exception, match="LLM generation failed"):
            corrector._generate_correction("Test prompt")


class TestLLMCorrectorCorrection:
    """Test suite for text correction functionality"""

    @patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_correct_text_short(self, mock_llama, temp_model_file):
        """Test correcting short text"""
        mock_model = Mock()
        mock_model.return_value = {
            'choices': [{'text': 'Das ist ein korrigierter Text.'}]
        }
        mock_llama.return_value = mock_model

        corrector = LLMCorrector(model_path=temp_model_file)

        result = corrector.correct_text(
            "Das ist ein Test text mit fehler.",
            level="basic",
            language="de"
        )

        assert result == "Das ist ein korrigierter Text."
        assert corrector.is_model_loaded()  # Should auto-load model

    @patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_correct_text_chunked(self, mock_llama, temp_model_file):
        """Test correcting text that requires chunking"""
        mock_model = Mock()
        mock_model.return_value = {
            'choices': [{'text': 'Korrigierter Chunk'}]
        }
        mock_llama.return_value = mock_model

        corrector = LLMCorrector(model_path=temp_model_file, context_length=100)

        long_text = "Das ist ein langer Text. " * 50
        result = corrector.correct_text(long_text, level="basic", language="de")

        assert "Korrigierter Chunk" in result

    def test_correct_text_empty(self, temp_model_file):
        """Test correcting empty text"""
        corrector = LLMCorrector(model_path=temp_model_file)

        result = corrector.correct_text("", level="basic", language="de")
        assert result == ""

        result = corrector.correct_text("   ", level="basic", language="de")
        assert result == "   "

    @patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_correct_text_invalid_level(self, mock_llama, temp_model_file):
        """Test correction with invalid level falls back to basic"""
        mock_model = Mock()
        mock_model.return_value = {
            'choices': [{'text': 'Corrected text'}]
        }
        mock_llama.return_value = mock_model

        corrector = LLMCorrector(model_path=temp_model_file)

        result = corrector.correct_text(
            "Test text",
            level="invalid_level",
            language="de"
        )

        assert result == "Corrected text"

    @patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_correct_text_invalid_language(self, mock_llama, temp_model_file):
        """Test correction with invalid language falls back to German"""
        mock_model = Mock()
        mock_model.return_value = {
            'choices': [{'text': 'Corrected text'}]
        }
        mock_llama.return_value = mock_model

        corrector = LLMCorrector(model_path=temp_model_file)

        result = corrector.correct_text(
            "Test text",
            level="basic",
            language="invalid_lang"
        )

        assert result == "Corrected text"

    @patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_correct_text_all_levels(self, mock_llama, temp_model_file):
        """Test correction with all available levels"""
        mock_model = Mock()
        mock_model.return_value = {
            'choices': [{'text': 'Corrected text'}]
        }
        mock_llama.return_value = mock_model

        corrector = LLMCorrector(model_path=temp_model_file)

        levels = ["basic", "advanced", "formal"]
        for level in levels:
            result = corrector.correct_text("Test text", level=level, language="de")
            assert result == "Corrected text"

    @patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_correct_text_all_languages(self, mock_llama, temp_model_file):
        """Test correction with all supported languages"""
        mock_model = Mock()
        mock_model.return_value = {
            'choices': [{'text': 'Corrected text'}]
        }
        mock_llama.return_value = mock_model

        corrector = LLMCorrector(model_path=temp_model_file)

        languages = ["de", "en"]
        for language in languages:
            result = corrector.correct_text("Test text", level="basic", language=language)
            assert result == "Corrected text"


class TestLLMCorrectorInformation:
    """Test suite for model information and metadata"""

    @patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_get_model_info_not_loaded(self, mock_llama, temp_model_file):
        """Test getting model info when model not loaded"""
        corrector = LLMCorrector(model_path=temp_model_file, context_length=4096)

        info = corrector.get_model_info()

        expected_keys = {"model_path", "model_loaded", "context_length", "temperature"}
        assert set(info.keys()) == expected_keys
        assert not info["model_loaded"]
        assert info["context_length"] == 4096

    @patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_get_model_info_loaded(self, mock_llama, temp_model_file):
        """Test getting model info when model is loaded"""
        mock_model = Mock()
        mock_model.n_ctx.return_value = 2048
        mock_model.n_vocab.return_value = 32000
        mock_llama.return_value = mock_model

        corrector = LLMCorrector(model_path=temp_model_file)
        corrector.load_model()

        info = corrector.get_model_info()

        assert info["model_loaded"]
        assert info["actual_context_length"] == 2048
        assert info["vocab_size"] == 32000
        assert info["load_time"] > 0

    def test_get_correction_prompts_exist(self, temp_model_file):
        """Test that all correction prompts are properly defined"""
        corrector = LLMCorrector(model_path=temp_model_file)

        levels = ["basic", "advanced", "formal"]
        languages = ["de", "en"]

        for level in levels:
            assert level in corrector.CORRECTION_PROMPTS
            for lang in languages:
                assert lang in corrector.CORRECTION_PROMPTS[level]
                prompt = corrector.CORRECTION_PROMPTS[level][lang]
                assert "{text}" in prompt  # Must contain text placeholder


class TestLLMCorrectorContextManager:
    """Test suite for context manager functionality"""

    @patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_context_manager_auto_load_unload(self, mock_llama, temp_model_file):
        """Test context manager automatically loads and unloads model"""
        mock_model = Mock()
        mock_llama.return_value = mock_model

        with LLMCorrector(model_path=temp_model_file) as corrector:
            assert corrector.is_model_loaded()

        # Model should be unloaded after exiting context
        assert not corrector.is_model_loaded()

    @patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_context_manager_with_exception(self, mock_llama, temp_model_file):
        """Test context manager unloads model even if exception occurs"""
        mock_model = Mock()
        mock_llama.return_value = mock_model

        corrector = None
        try:
            with LLMCorrector(model_path=temp_model_file) as c:
                corrector = c
                assert corrector.is_model_loaded()
                raise Exception("Test exception")
        except Exception:
            pass

        # Model should still be unloaded after exception
        assert not corrector.is_model_loaded()


class TestLLMCorrectorThreadSafety:
    """Test suite for thread safety"""

    @patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_concurrent_load_unload(self, mock_llama, temp_model_file):
        """Test concurrent loading and unloading is thread-safe"""
        mock_model = Mock()
        mock_llama.return_value = mock_model

        corrector = LLMCorrector(model_path=temp_model_file)
        results = []
        errors = []

        def load_and_unload():
            try:
                load_result = corrector.load_model()
                time.sleep(0.01)  # Small delay
                unload_result = corrector.unload_model()
                results.append((load_result, unload_result))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=load_and_unload) for _ in range(5)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Should not have any errors
        assert len(errors) == 0
        assert len(results) == 5

    @patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_concurrent_correction(self, mock_llama, temp_model_file):
        """Test concurrent text correction calls"""
        mock_model = Mock()
        mock_model.return_value = {
            'choices': [{'text': 'Corrected text'}]
        }
        mock_llama.return_value = mock_model

        corrector = LLMCorrector(model_path=temp_model_file)
        results = []
        errors = []

        def correct_text():
            try:
                result = corrector.correct_text("Test text", "basic", "de")
                results.append(result)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=correct_text) for _ in range(3)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Should have successful results without errors
        assert len(errors) == 0
        assert len(results) == 3
        assert all(r == "Corrected text" for r in results)


class TestCorrectTextQuick:
    """Test suite for quick correction function"""

    @patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.LLMCorrector')
    def test_correct_text_quick_success(self, mock_corrector_class, temp_model_file):
        """Test quick correction function"""
        mock_corrector = Mock()
        mock_corrector.correct_text.return_value = "Corrected text"
        mock_corrector_class.return_value.__enter__.return_value = mock_corrector
        mock_corrector_class.return_value.__exit__.return_value = None

        result = correct_text_quick(
            "Test text",
            level="advanced",
            language="en",
            model_path=temp_model_file
        )

        assert result == "Corrected text"
        mock_corrector_class.assert_called_once_with(model_path=temp_model_file)
        mock_corrector.correct_text.assert_called_once_with("Test text", "advanced", "en")

    @patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.LLMCorrector')
    def test_correct_text_quick_with_defaults(self, mock_corrector_class):
        """Test quick correction with default parameters"""
        mock_corrector = Mock()
        mock_corrector.correct_text.return_value = "Corrected text"
        mock_corrector_class.return_value.__enter__.return_value = mock_corrector
        mock_corrector_class.return_value.__exit__.return_value = None

        result = correct_text_quick("Test text")

        assert result == "Corrected text"
        mock_corrector.correct_text.assert_called_once_with("Test text", "basic", "de")


class TestLLMCorrectorErrorHandling:
    """Test suite for error handling scenarios"""

    @patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_model_loading_memory_error(self, mock_llama, temp_model_file):
        """Test handling of memory errors during model loading"""
        mock_llama.side_effect = MemoryError("Not enough memory")

        corrector = LLMCorrector(model_path=temp_model_file)
        result = corrector.load_model()

        assert result is False
        assert not corrector.is_model_loaded()

    @patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_generation_timeout_handling(self, mock_llama, temp_model_file):
        """Test handling of generation timeouts"""
        mock_model = Mock()
        mock_model.side_effect = TimeoutError("Generation timed out")
        mock_llama.return_value = mock_model

        corrector = LLMCorrector(model_path=temp_model_file)
        corrector.load_model()

        with pytest.raises(TimeoutError):
            corrector._generate_correction("Test prompt")

    def test_file_permission_errors(self):
        """Test handling of file permission errors"""
        # Try to create corrector with file that doesn't exist
        with pytest.raises(FileNotFoundError):
            LLMCorrector(model_path="/root/restricted/model.gguf")

    @patch('src.whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_corrupted_model_handling(self, mock_llama, temp_model_file):
        """Test handling of corrupted model files"""
        mock_llama.side_effect = ValueError("Invalid model format")

        corrector = LLMCorrector(model_path=temp_model_file)
        result = corrector.load_model()

        assert result is False
        assert not corrector.is_model_loaded()


class TestLLMCorrectorPerformance:
    """Test suite for performance-related functionality"""

    @pytest.mark.performance
    def test_token_estimation_performance(self, temp_model_file):
        """Test token estimation performance with large texts"""
        corrector = LLMCorrector(model_path=temp_model_file)

        large_text = "Performance test text. " * 1000

        import time
        start_time = time.time()

        token_count = corrector.estimate_tokens(large_text)

        estimation_time = time.time() - start_time

        assert token_count > 0
        assert estimation_time < 1.0  # Should be fast

    @pytest.mark.performance
    def test_chunking_performance(self, temp_model_file):
        """Test text chunking performance"""
        corrector = LLMCorrector(model_path=temp_model_file)

        large_text = "Chunking performance test. " * 500

        import time
        start_time = time.time()

        chunks = corrector.chunk_text(large_text, max_tokens=100)

        chunking_time = time.time() - start_time

        assert len(chunks) > 1
        assert chunking_time < 2.0  # Should be reasonably fast


if __name__ == "__main__":
    pytest.main([__file__, "-v"])