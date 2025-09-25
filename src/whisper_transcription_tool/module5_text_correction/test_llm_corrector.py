"""
Unit tests for LLMCorrector class.

Tests cover all functionality including model loading, text correction,
token management, and error handling.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from pathlib import Path

from .llm_corrector import LLMCorrector, correct_text_quick, LLAMA_CPP_AVAILABLE


class TestLLMCorrector(unittest.TestCase):
    """Test suite for LLMCorrector class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary model file for testing
        self.temp_model = tempfile.NamedTemporaryFile(suffix='.gguf', delete=False)
        self.temp_model.write(b"fake model data")
        self.temp_model.close()
        self.temp_model_path = self.temp_model.name

        # Test texts
        self.test_text_short = "Das ist ein Test text mit fehler."
        self.test_text_long = "Das ist ein sehr langer Test text. " * 100  # ~400 words
        self.test_text_empty = ""
        self.test_text_whitespace = "   \n\t   "

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_model_path):
            os.unlink(self.temp_model_path)

    def test_init_default_model_path(self):
        """Test initialization with default model path."""
        with patch('os.path.exists', return_value=True):
            corrector = LLMCorrector()
            self.assertEqual(corrector.model_path, Path(LLMCorrector.DEFAULT_MODEL_PATH))
            self.assertEqual(corrector.context_length, 2048)
            self.assertEqual(corrector.temperature, 0.3)
            self.assertIsNone(corrector.model)
            self.assertFalse(corrector._model_loaded)

    def test_init_custom_model_path(self):
        """Test initialization with custom model path."""
        corrector = LLMCorrector(model_path=self.temp_model_path, context_length=4096)
        self.assertEqual(corrector.model_path, Path(self.temp_model_path))
        self.assertEqual(corrector.context_length, 4096)

    def test_init_nonexistent_model(self):
        """Test initialization with non-existent model file."""
        with self.assertRaises(FileNotFoundError):
            LLMCorrector(model_path="/nonexistent/model.gguf")

    @patch('whisper_transcription_tool.module5_text_correction.llm_corrector.LLAMA_CPP_AVAILABLE', False)
    def test_init_llama_cpp_unavailable(self):
        """Test initialization when llama-cpp-python is not available."""
        with self.assertRaises(ImportError):
            LLMCorrector(model_path=self.temp_model_path)

    @patch('whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    @patch('os.cpu_count', return_value=8)
    def test_load_model_success(self, mock_cpu_count, mock_llama):
        """Test successful model loading."""
        mock_model = Mock()
        mock_model.n_ctx.return_value = 2048
        mock_llama.return_value = mock_model

        corrector = LLMCorrector(model_path=self.temp_model_path)
        result = corrector.load_model()

        self.assertTrue(result)
        self.assertTrue(corrector.is_model_loaded())
        self.assertEqual(corrector.model, mock_model)

        # Verify Llama was called with correct parameters
        mock_llama.assert_called_once_with(
            model_path=self.temp_model_path,
            n_ctx=2048,
            n_gpu_layers=-1,
            n_threads=8,
            verbose=False,
            use_mlock=True,
            use_mmap=True,
        )

    @patch('whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_load_model_failure(self, mock_llama):
        """Test model loading failure."""
        mock_llama.side_effect = Exception("Model loading failed")

        corrector = LLMCorrector(model_path=self.temp_model_path)
        result = corrector.load_model()

        self.assertFalse(result)
        self.assertFalse(corrector.is_model_loaded())
        self.assertIsNone(corrector.model)

    @patch('whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_load_model_already_loaded(self, mock_llama):
        """Test loading model when already loaded."""
        mock_model = Mock()
        mock_llama.return_value = mock_model

        corrector = LLMCorrector(model_path=self.temp_model_path)
        corrector.load_model()

        # Try loading again
        result = corrector.load_model()

        self.assertTrue(result)
        # Llama should only be called once
        mock_llama.assert_called_once()

    def test_unload_model(self):
        """Test model unloading."""
        corrector = LLMCorrector(model_path=self.temp_model_path)
        corrector.model = Mock()
        corrector._model_loaded = True

        corrector.unload_model()

        self.assertIsNone(corrector.model)
        self.assertFalse(corrector._model_loaded)

    def test_unload_model_not_loaded(self):
        """Test unloading when no model is loaded."""
        corrector = LLMCorrector(model_path=self.temp_model_path)
        # Should not raise exception
        corrector.unload_model()

    def test_get_context_length(self):
        """Test getting context length."""
        corrector = LLMCorrector(model_path=self.temp_model_path, context_length=4096)

        # When model not loaded, return configured value
        self.assertEqual(corrector.get_context_length(), 4096)

        # When model is loaded, return model's actual value
        mock_model = Mock()
        mock_model.n_ctx.return_value = 2048
        corrector.model = mock_model
        corrector._model_loaded = True

        self.assertEqual(corrector.get_context_length(), 2048)

    def test_estimate_tokens(self):
        """Test token estimation."""
        corrector = LLMCorrector(model_path=self.temp_model_path)

        # Test various text lengths
        self.assertEqual(corrector.estimate_tokens(""), 1)  # Minimum 1 token
        self.assertEqual(corrector.estimate_tokens("test"), 1)  # 4 chars = 1 token
        self.assertEqual(corrector.estimate_tokens("test text"), 2)  # 9 chars = 2 tokens
        self.assertEqual(corrector.estimate_tokens("a" * 100), 25)  # 100 chars = 25 tokens

    @patch('whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_tokenize(self, mock_llama):
        """Test text tokenization."""
        mock_model = Mock()
        mock_model.tokenize.return_value = [1, 2, 3, 4]
        mock_llama.return_value = mock_model

        corrector = LLMCorrector(model_path=self.temp_model_path)
        corrector.load_model()

        tokens = corrector.tokenize("test text")
        self.assertEqual(tokens, [1, 2, 3, 4])
        mock_model.tokenize.assert_called_once_with(b"test text")

    def test_tokenize_model_not_loaded(self):
        """Test tokenization when model not loaded."""
        corrector = LLMCorrector(model_path=self.temp_model_path)

        with self.assertRaises(RuntimeError):
            corrector.tokenize("test text")

    def test_chunk_text_short(self):
        """Test chunking short text."""
        corrector = LLMCorrector(model_path=self.temp_model_path)
        chunks = corrector.chunk_text(self.test_text_short, max_tokens=100)

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], self.test_text_short)

    def test_chunk_text_long(self):
        """Test chunking long text."""
        corrector = LLMCorrector(model_path=self.temp_model_path)
        chunks = corrector.chunk_text(self.test_text_long, max_tokens=50)

        self.assertGreater(len(chunks), 1)
        # Verify no chunk is too long
        for chunk in chunks:
            self.assertLessEqual(corrector.estimate_tokens(chunk), 50)

    def test_chunk_text_default_limit(self):
        """Test chunking with default token limit."""
        corrector = LLMCorrector(model_path=self.temp_model_path, context_length=2048)
        chunks = corrector.chunk_text(self.test_text_long)

        # Should use 80% of context length as default
        expected_max_tokens = int(2048 * 0.8)
        for chunk in chunks:
            self.assertLessEqual(corrector.estimate_tokens(chunk), expected_max_tokens)

    @patch('whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_generate_correction(self, mock_llama):
        """Test text generation for correction."""
        mock_model = Mock()
        mock_model.return_value = {
            'choices': [{'text': '  "Corrected text here"  '}]
        }
        mock_llama.return_value = mock_model

        corrector = LLMCorrector(model_path=self.temp_model_path)
        corrector.load_model()

        result = corrector._generate_correction("Test prompt")

        # Verify cleanup of quotes and whitespace
        self.assertEqual(result, "Corrected text here")

        # Verify model call parameters
        mock_model.assert_called_once()
        call_args = mock_model.call_args
        self.assertEqual(call_args[0][0], "Test prompt")
        self.assertEqual(call_args[1]['temperature'], 0.3)
        self.assertEqual(call_args[1]['top_p'], 0.9)

    def test_generate_correction_model_not_loaded(self):
        """Test generation when model not loaded."""
        corrector = LLMCorrector(model_path=self.temp_model_path)

        with self.assertRaises(RuntimeError):
            corrector._generate_correction("Test prompt")

    @patch('whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_correct_text_short(self, mock_llama):
        """Test correcting short text."""
        mock_model = Mock()
        mock_model.return_value = {
            'choices': [{'text': 'Das ist ein korrigierter Text.'}]
        }
        mock_llama.return_value = mock_model

        corrector = LLMCorrector(model_path=self.temp_model_path)

        result = corrector.correct_text(self.test_text_short, "basic", "de")

        self.assertEqual(result, "Das ist ein korrigierter Text.")
        self.assertTrue(corrector.is_model_loaded())

    @patch('whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_correct_text_chunked(self, mock_llama):
        """Test correcting text that requires chunking."""
        mock_model = Mock()
        mock_model.return_value = {
            'choices': [{'text': 'Corrected chunk'}]
        }
        mock_llama.return_value = mock_model

        corrector = LLMCorrector(model_path=self.temp_model_path, context_length=100)

        result = corrector.correct_text(self.test_text_long, "basic", "de")

        # Result should contain corrected chunks joined together
        self.assertIn("Corrected chunk", result)

    def test_correct_text_empty(self):
        """Test correcting empty text."""
        corrector = LLMCorrector(model_path=self.temp_model_path)

        result = corrector.correct_text(self.test_text_empty)
        self.assertEqual(result, self.test_text_empty)

    def test_correct_text_whitespace_only(self):
        """Test correcting whitespace-only text."""
        corrector = LLMCorrector(model_path=self.temp_model_path)

        result = corrector.correct_text(self.test_text_whitespace)
        self.assertEqual(result, self.test_text_whitespace)

    @patch('whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_correct_text_invalid_level(self, mock_llama):
        """Test correction with invalid level."""
        mock_model = Mock()
        mock_model.return_value = {
            'choices': [{'text': 'Corrected text'}]
        }
        mock_llama.return_value = mock_model

        corrector = LLMCorrector(model_path=self.temp_model_path)

        # Should fall back to "basic" level
        result = corrector.correct_text(self.test_text_short, "invalid_level", "de")
        self.assertEqual(result, "Corrected text")

    @patch('whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_correct_text_invalid_language(self, mock_llama):
        """Test correction with invalid language."""
        mock_model = Mock()
        mock_model.return_value = {
            'choices': [{'text': 'Corrected text'}]
        }
        mock_llama.return_value = mock_model

        corrector = LLMCorrector(model_path=self.temp_model_path)

        # Should fall back to "de" language
        result = corrector.correct_text(self.test_text_short, "basic", "invalid_lang")
        self.assertEqual(result, "Corrected text")

    @patch('whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_get_model_info(self, mock_llama):
        """Test getting model information."""
        mock_model = Mock()
        mock_model.n_ctx.return_value = 2048
        mock_model.n_vocab.return_value = 32000
        mock_llama.return_value = mock_model

        corrector = LLMCorrector(model_path=self.temp_model_path, context_length=4096)

        # Before loading
        info = corrector.get_model_info()
        expected_keys = {"model_path", "model_loaded", "context_length", "temperature"}
        self.assertEqual(set(info.keys()), expected_keys)
        self.assertFalse(info["model_loaded"])

        # After loading
        corrector.load_model()
        info = corrector.get_model_info()

        self.assertTrue(info["model_loaded"])
        self.assertEqual(info["actual_context_length"], 2048)
        self.assertEqual(info["vocab_size"], 32000)

    @patch('whisper_transcription_tool.module5_text_correction.llm_corrector.Llama')
    def test_context_manager(self, mock_llama):
        """Test using LLMCorrector as context manager."""
        mock_model = Mock()
        mock_llama.return_value = mock_model

        with LLMCorrector(model_path=self.temp_model_path) as corrector:
            self.assertTrue(corrector.is_model_loaded())

        # Model should be unloaded after exiting context
        self.assertFalse(corrector.is_model_loaded())

    @patch('whisper_transcription_tool.module5_text_correction.llm_corrector.LLMCorrector')
    def test_correct_text_quick(self, mock_corrector_class):
        """Test quick correction function."""
        mock_corrector = Mock()
        mock_corrector.correct_text.return_value = "Corrected text"
        mock_corrector_class.return_value.__enter__.return_value = mock_corrector
        mock_corrector_class.return_value.__exit__.return_value = None

        result = correct_text_quick("Test text", "advanced", "en", "/path/to/model")

        self.assertEqual(result, "Corrected text")
        mock_corrector_class.assert_called_once_with(model_path="/path/to/model")
        mock_corrector.correct_text.assert_called_once_with("Test text", "advanced", "en")

    def test_correction_prompts_exist(self):
        """Test that all correction prompts are defined."""
        levels = ["basic", "advanced", "formal"]
        languages = ["de", "en"]

        for level in levels:
            self.assertIn(level, LLMCorrector.CORRECTION_PROMPTS)
            for lang in languages:
                self.assertIn(lang, LLMCorrector.CORRECTION_PROMPTS[level])
                prompt = LLMCorrector.CORRECTION_PROMPTS[level][lang]
                self.assertIn("{text}", prompt)  # Must contain text placeholder


class TestLLMCorrectorIntegration(unittest.TestCase):
    """Integration tests for LLMCorrector (require actual model file)."""

    def setUp(self):
        """Set up for integration tests."""
        # Only run if model exists
        self.model_path = LLMCorrector.DEFAULT_MODEL_PATH
        self.model_exists = os.path.exists(self.model_path) and LLAMA_CPP_AVAILABLE

    @unittest.skipUnless(os.path.exists(LLMCorrector.DEFAULT_MODEL_PATH) and LLAMA_CPP_AVAILABLE,
                        "LeoLM model not found or llama-cpp-python not available")
    def test_actual_model_loading(self):
        """Test loading the actual LeoLM model."""
        corrector = LLMCorrector()

        try:
            success = corrector.load_model()
            self.assertTrue(success)
            self.assertTrue(corrector.is_model_loaded())

            # Test basic functionality
            info = corrector.get_model_info()
            self.assertTrue(info["model_loaded"])
            self.assertGreater(info["actual_context_length"], 0)
            self.assertGreater(info["vocab_size"], 0)

        finally:
            corrector.unload_model()

    @unittest.skipUnless(os.path.exists(LLMCorrector.DEFAULT_MODEL_PATH) and LLAMA_CPP_AVAILABLE,
                        "LeoLM model not found or llama-cpp-python not available")
    def test_actual_text_correction(self):
        """Test actual text correction with real model."""
        test_text = "Das ist ein test text mit einigen fehler und schlechte grammatik."

        try:
            corrected = correct_text_quick(test_text, "basic", "de")

            # Basic checks - corrected text should be different and non-empty
            self.assertIsInstance(corrected, str)
            self.assertGreater(len(corrected.strip()), 0)

            print(f"Original:  {test_text}")
            print(f"Corrected: {corrected}")

        except Exception as e:
            self.fail(f"Text correction failed: {e}")


if __name__ == "__main__":
    # Configure test runner
    import sys

    # Add verbose output for integration tests
    if "--integration" in sys.argv:
        sys.argv.remove("--integration")
        unittest.main(verbosity=2, argv=sys.argv)
    else:
        # Run unit tests only
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestLLMCorrector)
        runner = unittest.TextTestRunner(verbosity=2)
        runner.run(suite)