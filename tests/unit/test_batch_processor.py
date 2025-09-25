"""
Comprehensive Unit Tests for BatchProcessor

Tests cover:
- Text chunking with sentence boundaries
- Token estimation strategies
- Overlap handling and merging
- Async and sync processing modes
- Error recovery and edge cases
- Performance estimation

Author: QualityMarshal Agent
Version: 1.0.0
"""

import pytest
import asyncio
import unittest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import tempfile
import os
from pathlib import Path

# Import the classes to test
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.whisper_transcription_tool.module5_text_correction.batch_processor import (
    BatchProcessor,
    TextChunk,
    ChunkProcessingResult,
    TokenizerStrategy
)


class TestTextChunk:
    """Test suite for TextChunk dataclass"""

    def test_text_chunk_creation(self):
        """Test TextChunk creation with valid parameters"""
        chunk = TextChunk(
            text="Test text",
            index=0,
            start_pos=0,
            end_pos=9,
            overlap_start=0,
            overlap_end=0,
            sentence_start=0,
            sentence_end=1,
            token_count=5
        )

        assert chunk.text == "Test text"
        assert chunk.index == 0
        assert chunk.start_pos == 0
        assert chunk.end_pos == 9
        assert chunk.token_count == 5

    def test_text_chunk_validation_invalid_positions(self):
        """Test TextChunk validation with invalid positions"""
        with pytest.raises(ValueError, match="Invalid chunk positions"):
            TextChunk(
                text="Test text",
                index=0,
                start_pos=10,  # Invalid: start > end
                end_pos=9,
                token_count=5
            )

    def test_text_chunk_validation_negative_index(self):
        """Test TextChunk validation with negative index"""
        with pytest.raises(ValueError, match="Invalid chunk index"):
            TextChunk(
                text="Test text",
                index=-1,  # Invalid negative index
                start_pos=0,
                end_pos=9,
                token_count=5
            )

    def test_text_chunk_whitespace_warning(self, caplog):
        """Test TextChunk logs warning for whitespace-only text"""
        chunk = TextChunk(
            text="   \n\t   ",  # Only whitespace
            index=0,
            start_pos=0,
            end_pos=7,
            token_count=0
        )

        assert "contains only whitespace" in caplog.text


class TestChunkProcessingResult:
    """Test suite for ChunkProcessingResult dataclass"""

    def test_processing_result_success(self):
        """Test processing result with success"""
        chunk = TextChunk("Test", 0, 0, 4, token_count=1)
        result = ChunkProcessingResult(
            chunk=chunk,
            corrected_text="Corrected test",
            processing_time=1.5
        )

        assert result.success is True
        assert result.error is None
        assert result.corrected_text == "Corrected test"

    def test_processing_result_with_error(self):
        """Test processing result with error"""
        chunk = TextChunk("Test", 0, 0, 4, token_count=1)
        error = Exception("Processing failed")

        result = ChunkProcessingResult(
            chunk=chunk,
            corrected_text="",
            processing_time=0.0,
            error=error
        )

        assert result.success is False
        assert result.error == error


class TestBatchProcessor:
    """Test suite for BatchProcessor class"""

    def test_init_default_parameters(self):
        """Test BatchProcessor initialization with defaults"""
        processor = BatchProcessor()

        assert processor.max_context_length == 2048
        assert processor.overlap_sentences == 1
        assert processor.tokenizer_strategy == TokenizerStrategy.SENTENCEPIECE

    def test_init_custom_parameters(self):
        """Test BatchProcessor initialization with custom parameters"""
        processor = BatchProcessor(
            max_context_length=4096,
            overlap_sentences=2,
            tokenizer_strategy="nltk"
        )

        assert processor.max_context_length == 4096
        assert processor.overlap_sentences == 2
        assert processor.tokenizer_strategy == TokenizerStrategy.NLTK

    def test_init_invalid_strategy(self):
        """Test BatchProcessor initialization with invalid strategy"""
        with pytest.raises(ValueError):
            BatchProcessor(tokenizer_strategy="invalid_strategy")

    @patch('src.whisper_transcription_tool.module5_text_correction.batch_processor.HAS_NLTK', True)
    @patch('src.whisper_transcription_tool.module5_text_correction.batch_processor.nltk')
    def test_initialize_tokenizers_nltk(self, mock_nltk):
        """Test tokenizer initialization with NLTK"""
        mock_nltk.download = Mock()

        processor = BatchProcessor(tokenizer_strategy="nltk")

        mock_nltk.download.assert_called_with('punkt', quiet=True)

    def test_initialize_tokenizers_fallback(self):
        """Test tokenizer fallback to simple regex splitting"""
        with patch('src.whisper_transcription_tool.module5_text_correction.batch_processor.HAS_NLTK', False):
            processor = BatchProcessor(tokenizer_strategy="nltk")

            # Should fall back to simple sentence splitting
            assert processor._sentence_tokenizer_fn == processor._simple_sentence_split

    def test_simple_sentence_split(self):
        """Test simple sentence splitting functionality"""
        processor = BatchProcessor()
        text = "Erster Satz. Zweiter Satz! Dritter Satz?"

        sentences = processor._simple_sentence_split(text)

        assert len(sentences) == 3
        assert sentences[0].strip() == "Erster Satz."
        assert sentences[1].strip() == "Zweiter Satz!"
        assert sentences[2].strip() == "Dritter Satz?"

    def test_simple_sentence_split_complex(self):
        """Test simple sentence splitting with complex punctuation"""
        processor = BatchProcessor()
        text = "Dr. Schmidt sagte... Das ist interessant! Wirklich? Ja, das stimmt."

        sentences = processor._simple_sentence_split(text)

        # Should handle complex punctuation correctly
        assert len(sentences) > 2
        assert any("Dr. Schmidt" in s for s in sentences)

    def test_estimate_token_count_empty_text(self):
        """Test token estimation for empty text"""
        processor = BatchProcessor()

        count = processor.estimate_token_count("")
        assert count == 0

        count = processor.estimate_token_count("   ")
        assert count == 0

    def test_estimate_token_count_fallback(self):
        """Test token estimation fallback method"""
        processor = BatchProcessor()
        text = "This is a test with five words"

        count = processor.estimate_token_count(text)

        # Should use word-based estimation (words * 1.3 + 10)
        expected = int(6 * 1.3) + 10  # 6 words
        assert count == expected

    @patch('src.whisper_transcription_tool.module5_text_correction.batch_processor.HAS_TRANSFORMERS', True)
    @patch('src.whisper_transcription_tool.module5_text_correction.batch_processor.AutoTokenizer')
    def test_estimate_token_count_transformers(self, mock_tokenizer_class):
        """Test token estimation using Transformers tokenizer"""
        mock_tokenizer = Mock()
        mock_tokenizer.encode.return_value = [1, 2, 3, 4, 5]
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer

        processor = BatchProcessor(tokenizer_strategy="transformers")
        text = "Test text"

        count = processor.estimate_token_count(text)

        assert count == 5
        mock_tokenizer.encode.assert_called_with(text)

    def test_chunk_text_empty_input(self):
        """Test chunking empty text raises ValueError"""
        processor = BatchProcessor()

        with pytest.raises(ValueError, match="Cannot chunk empty text"):
            processor.chunk_text("")

        with pytest.raises(ValueError, match="Cannot chunk empty text"):
            processor.chunk_text("   ")

    def test_chunk_text_short_text(self):
        """Test chunking short text creates single chunk"""
        processor = BatchProcessor()
        text = "Das ist ein kurzer Text."

        chunks = processor.chunk_text(text)

        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].index == 0

    def test_chunk_text_long_text(self):
        """Test chunking long text creates multiple chunks"""
        processor = BatchProcessor(max_context_length=50)  # Small limit
        text = "Das ist ein langer Text. " * 20  # Will exceed limit

        chunks = processor.chunk_text(text)

        assert len(chunks) > 1
        # Each chunk should respect token limit
        for chunk in chunks:
            assert processor.estimate_token_count(chunk.text) <= 50

    def test_chunk_text_with_overlap(self):
        """Test chunking with sentence overlap"""
        processor = BatchProcessor(max_context_length=50, overlap_sentences=1)
        text = "Erster Satz. Zweiter Satz. Dritter Satz. Vierter Satz. Fünfter Satz."

        chunks = processor.chunk_text(text)

        if len(chunks) > 1:
            # Check that overlaps are calculated
            for i, chunk in enumerate(chunks[1:], 1):
                assert chunk.overlap_start >= 0

    @patch('src.whisper_transcription_tool.module5_text_correction.batch_processor.sent_tokenize')
    def test_chunk_text_tokenization_failure(self, mock_sent_tokenize):
        """Test chunking handles tokenization failure"""
        mock_sent_tokenize.side_effect = Exception("Tokenization failed")
        processor = BatchProcessor()

        with pytest.raises(ValueError, match="Failed to tokenize sentences"):
            processor.chunk_text("Test text.")

    def test_create_chunk_from_sentences(self):
        """Test creating chunk from sentences"""
        processor = BatchProcessor()
        sentences = ["Erster Satz.", "Zweiter Satz."]
        original_text = "Erster Satz. Zweiter Satz."

        chunk = processor._create_chunk_from_sentences(
            sentences, 0, 0, 1, original_text
        )

        assert chunk.text == "Erster Satz. Zweiter Satz."
        assert chunk.index == 0
        assert chunk.sentence_start == 0
        assert chunk.sentence_end == 1

    def test_calculate_overlaps(self):
        """Test overlap calculation between chunks"""
        processor = BatchProcessor()

        chunk1 = TextChunk("Text one overlap", 0, 0, 16, token_count=3)
        chunk2 = TextChunk("overlap text two", 1, 9, 25, token_count=3)
        chunks = [chunk1, chunk2]

        processor._calculate_overlaps(chunks, "Text one overlap text two")

        # Should detect overlap
        assert chunk2.overlap_start > 0

    def test_find_overlap(self):
        """Test finding overlap between two texts"""
        processor = BatchProcessor()

        text1 = "This is some text with overlap"
        text2 = "overlap and more text here"

        overlap = processor._find_overlap(text1, text2)

        assert overlap == "overlap"

    def test_find_overlap_no_overlap(self):
        """Test finding overlap when none exists"""
        processor = BatchProcessor()

        text1 = "Completely different text"
        text2 = "No matching content here"

        overlap = processor._find_overlap(text1, text2)

        assert overlap == ""

    @pytest.mark.asyncio
    async def test_process_chunks_async_empty(self):
        """Test async processing with empty chunks list"""
        processor = BatchProcessor()

        result = await processor.process_chunks_async([], lambda x: x)

        assert result == ""

    @pytest.mark.asyncio
    async def test_process_chunks_async_success(self):
        """Test successful async chunk processing"""
        processor = BatchProcessor()

        chunks = [
            TextChunk("Text one", 0, 0, 8, token_count=2),
            TextChunk("Text two", 1, 9, 17, token_count=2)
        ]

        def mock_correction(text):
            return f"Corrected {text}"

        mock_progress = Mock()

        result = await processor.process_chunks_async(
            chunks, mock_correction, mock_progress
        )

        assert "Corrected" in result
        assert mock_progress.call_count == 2

    @pytest.mark.asyncio
    async def test_process_chunks_async_with_error(self):
        """Test async processing handles errors gracefully"""
        processor = BatchProcessor()

        chunks = [
            TextChunk("Text one", 0, 0, 8, token_count=2),
            TextChunk("Text two", 1, 9, 17, token_count=2)
        ]

        def failing_correction(text):
            if "two" in text:
                raise Exception("Processing failed")
            return f"Corrected {text}"

        result = await processor.process_chunks_async(chunks, failing_correction)

        # Should still return merged result, with failed chunk as original
        assert result != ""

    def test_process_chunks_sync_empty(self):
        """Test sync processing with empty chunks list"""
        processor = BatchProcessor()

        result = processor.process_chunks_sync([], lambda x: x)

        assert result == ""

    def test_process_chunks_sync_success(self):
        """Test successful sync chunk processing"""
        processor = BatchProcessor()

        chunks = [
            TextChunk("Text one", 0, 0, 8, token_count=2),
            TextChunk("Text two", 1, 9, 17, token_count=2)
        ]

        def mock_correction(text):
            return f"Corrected {text}"

        mock_progress = Mock()

        result = processor.process_chunks_sync(
            chunks, mock_correction, mock_progress
        )

        assert "Corrected" in result
        assert mock_progress.call_count == 2

    def test_process_chunks_sync_with_error(self):
        """Test sync processing handles errors gracefully"""
        processor = BatchProcessor()

        chunks = [
            TextChunk("Text one", 0, 0, 8, token_count=2),
            TextChunk("Text two", 1, 9, 17, token_count=2)
        ]

        def failing_correction(text):
            if "two" in text:
                raise Exception("Processing failed")
            return f"Corrected {text}"

        result = processor.process_chunks_sync(chunks, failing_correction)

        # Should still return merged result, with failed chunk as original
        assert result != ""

    def test_merge_overlapping_chunks_empty(self):
        """Test merging empty chunks list"""
        processor = BatchProcessor()

        result = processor._merge_overlapping_chunks([], [])

        assert result == ""

    def test_merge_overlapping_chunks_single(self):
        """Test merging single chunk"""
        processor = BatchProcessor()

        processed = ["Single chunk text"]
        original = [TextChunk("Single chunk text", 0, 0, 18, token_count=3)]

        result = processor._merge_overlapping_chunks(processed, original)

        assert result == "Single chunk text"

    def test_merge_overlapping_chunks_multiple(self):
        """Test merging multiple chunks with overlap"""
        processor = BatchProcessor()

        processed = ["First chunk with overlap", "overlap second chunk"]
        original = [
            TextChunk("First chunk with overlap", 0, 0, 24, overlap_end=7, token_count=4),
            TextChunk("overlap second chunk", 1, 17, 37, overlap_start=7, token_count=3)
        ]

        result = processor._merge_overlapping_chunks(processed, original)

        # Should handle overlap removal
        assert result != ""
        assert "First chunk" in result
        assert "second chunk" in result

    def test_remove_overlap_content(self):
        """Test removing overlap content from chunk"""
        processor = BatchProcessor()

        prev_chunk = "Text with some overlap content"
        current_chunk = "overlap content and more text"
        overlap_length = 15  # "overlap content"

        result = processor._remove_overlap_content(
            prev_chunk, current_chunk, overlap_length
        )

        # Should remove overlapping content
        assert "and more text" in result
        assert len(result) < len(current_chunk)

    def test_remove_overlap_content_no_overlap(self):
        """Test removing overlap when none exists"""
        processor = BatchProcessor()

        current_chunk = "No overlap here"

        result = processor._remove_overlap_content("", current_chunk, 0)

        assert result == current_chunk

    def test_remove_overlap_content_full_overlap(self):
        """Test removing overlap when overlap is entire chunk"""
        processor = BatchProcessor()

        current_chunk = "Short"
        overlap_length = 10  # Longer than chunk

        result = processor._remove_overlap_content("", current_chunk, overlap_length)

        assert result == current_chunk  # Should not remove entire chunk

    def test_estimate_processing_time_empty(self):
        """Test processing time estimation for empty text"""
        processor = BatchProcessor()

        time_estimate = processor.estimate_processing_time("")

        assert time_estimate == 0

    def test_estimate_processing_time_normal(self):
        """Test processing time estimation for normal text"""
        processor = BatchProcessor()
        text = "This is a normal length text for processing estimation."

        time_estimate = processor.estimate_processing_time(text)

        assert time_estimate >= 1  # At least 1 second minimum
        assert isinstance(time_estimate, int)

    def test_estimate_processing_time_long_text(self):
        """Test processing time estimation for long text"""
        processor = BatchProcessor()
        text = "Long text for processing. " * 1000  # Very long text

        time_estimate = processor.estimate_processing_time(text)

        assert time_estimate > 10  # Should be substantial time
        assert isinstance(time_estimate, int)

    def test_estimate_processing_time_custom_speed(self):
        """Test processing time estimation with custom speed"""
        processor = BatchProcessor()
        text = "Text for speed testing."

        fast_estimate = processor.estimate_processing_time(text, chars_per_second=1000)
        slow_estimate = processor.estimate_processing_time(text, chars_per_second=10)

        assert slow_estimate > fast_estimate


class TestTokenizerStrategy:
    """Test suite for TokenizerStrategy enum"""

    def test_tokenizer_strategy_values(self):
        """Test that all expected tokenizer strategies exist"""
        assert TokenizerStrategy.SENTENCEPIECE.value == "sentencepiece"
        assert TokenizerStrategy.TRANSFORMERS.value == "transformers"
        assert TokenizerStrategy.NLTK.value == "nltk"
        assert TokenizerStrategy.SIMPLE.value == "simple"

    def test_tokenizer_strategy_from_string(self):
        """Test creating strategy from string value"""
        strategy = TokenizerStrategy("sentencepiece")
        assert strategy == TokenizerStrategy.SENTENCEPIECE

        strategy = TokenizerStrategy("nltk")
        assert strategy == TokenizerStrategy.NLTK


class TestBatchProcessorIntegration:
    """Integration tests for BatchProcessor with real dependencies"""

    @pytest.mark.integration
    def test_full_processing_workflow(self):
        """Test complete processing workflow"""
        processor = BatchProcessor(max_context_length=100, overlap_sentences=1)

        # Long text that will require chunking
        text = "Dies ist ein langer Beispieltext. " * 20

        # Mock correction function
        def mock_correction(chunk_text):
            return f"[KORRIGIERT] {chunk_text}"

        # Process text
        chunks = processor.chunk_text(text)
        result = processor.process_chunks_sync(chunks, mock_correction)

        # Verify results
        assert len(chunks) > 1  # Should be chunked
        assert "[KORRIGIERT]" in result
        assert len(result) > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_async_processing_workflow(self):
        """Test complete async processing workflow"""
        processor = BatchProcessor(max_context_length=100, overlap_sentences=1)

        # Long text that will require chunking
        text = "Dies ist ein langer Beispieltext für asynchrone Verarbeitung. " * 15

        # Mock async correction function
        def mock_correction(chunk_text):
            import time
            time.sleep(0.01)  # Simulate processing time
            return f"[ASYNC-KORRIGIERT] {chunk_text}"

        progress_updates = []
        def progress_callback(current, total, status):
            progress_updates.append((current, total, status))

        # Process text
        chunks = processor.chunk_text(text)
        result = await processor.process_chunks_async(
            chunks, mock_correction, progress_callback
        )

        # Verify results
        assert len(chunks) > 1  # Should be chunked
        assert "[ASYNC-KORRIGIERT]" in result
        assert len(progress_updates) == len(chunks)  # Progress reported for each chunk

    @pytest.mark.performance
    def test_performance_large_text(self):
        """Test performance with large text input"""
        processor = BatchProcessor(max_context_length=500)

        # Very large text
        text = "Performance test text with multiple sentences. " * 500

        import time
        start_time = time.time()

        chunks = processor.chunk_text(text)

        processing_time = time.time() - start_time

        # Should complete within reasonable time
        assert processing_time < 5.0  # Less than 5 seconds
        assert len(chunks) > 1

        # Verify all chunks respect token limits
        for chunk in chunks:
            estimated_tokens = processor.estimate_token_count(chunk.text)
            assert estimated_tokens <= 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])