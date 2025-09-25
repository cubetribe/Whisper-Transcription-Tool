"""
BatchProcessor: Intelligent Text Chunking for LLM Correction

This module provides intelligent text chunking with sentence boundary respect,
overlap handling, and both async/sync processing modes.

Key Features:
- Sentence-boundary respecting text chunking
- SentencePiece tokenizer integration for LeoLM compatibility
- NLTK fallback for sentence segmentation
- Configurable overlap between chunks for context continuity
- Async and sync processing with progress reporting
- Comprehensive error handling and recovery
"""

from typing import List, Iterator, Callable, Dict, Optional, Tuple, Union
from dataclasses import dataclass
import asyncio
import logging
import re
import math
from concurrent.futures import ThreadPoolExecutor
from enum import Enum

# Import dependencies with graceful fallbacks
try:
    import sentencepiece as spm
    HAS_SENTENCEPIECE = True
except ImportError:
    HAS_SENTENCEPIECE = False
    spm = None

try:
    import nltk
    from nltk.tokenize import sent_tokenize
    HAS_NLTK = True
except ImportError:
    HAS_NLTK = False
    nltk = None
    sent_tokenize = None

try:
    from transformers import AutoTokenizer
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    AutoTokenizer = None


logger = logging.getLogger(__name__)


class TokenizerStrategy(Enum):
    """Available tokenization strategies"""
    SENTENCEPIECE = "sentencepiece"
    TRANSFORMERS = "transformers"
    NLTK = "nltk"
    SIMPLE = "simple"


@dataclass
class TextChunk:
    """
    Represents a chunk of text for processing with overlap information.

    Attributes:
        text: The actual text content of the chunk
        index: Sequential index of this chunk (0-based)
        start_pos: Character position where chunk starts in original text
        end_pos: Character position where chunk ends in original text
        overlap_start: Number of characters overlapping with previous chunk
        overlap_end: Number of characters overlapping with next chunk
        sentence_start: Index of first sentence in chunk
        sentence_end: Index of last sentence in chunk
        token_count: Estimated number of tokens in this chunk
    """
    text: str
    index: int
    start_pos: int
    end_pos: int
    overlap_start: int = 0
    overlap_end: int = 0
    sentence_start: int = 0
    sentence_end: int = 0
    token_count: int = 0

    def __post_init__(self):
        """Validate chunk data after initialization"""
        if self.start_pos < 0 or self.end_pos < self.start_pos:
            raise ValueError(f"Invalid chunk positions: start={self.start_pos}, end={self.end_pos}")
        if self.index < 0:
            raise ValueError(f"Invalid chunk index: {self.index}")
        if not self.text.strip():
            logger.warning(f"Chunk {self.index} contains only whitespace")


@dataclass
class ChunkProcessingResult:
    """Result of processing a single chunk"""
    chunk: TextChunk
    corrected_text: str
    processing_time: float
    error: Optional[Exception] = None
    success: bool = True

    def __post_init__(self):
        """Set success based on error presence"""
        self.success = self.error is None


class BatchProcessor:
    """
    Intelligent text chunking and batch processing for LLM correction.

    This class handles the complex task of splitting long texts into processable
    chunks while respecting sentence boundaries and maintaining context through
    overlaps.
    """

    def __init__(
        self,
        max_context_length: int = 2048,
        overlap_sentences: int = 1,
        tokenizer_strategy: str = "sentencepiece"
    ):
        """
        Initialize BatchProcessor with configurable parameters.

        Args:
            max_context_length: Maximum tokens per chunk (default: 2048)
            overlap_sentences: Number of sentences to overlap between chunks
            tokenizer_strategy: Preferred tokenization method
        """
        self.max_context_length = max_context_length
        self.overlap_sentences = overlap_sentences
        self.tokenizer_strategy = TokenizerStrategy(tokenizer_strategy)

        # Initialize tokenizer components
        self._tokenizer = None
        self._sentence_tokenizer_fn = None
        self._initialize_tokenizers()

        logger.info(f"BatchProcessor initialized: max_length={max_context_length}, "
                   f"overlap={overlap_sentences}, strategy={self.tokenizer_strategy.value}")

    def _initialize_tokenizers(self) -> None:
        """Initialize available tokenizers based on strategy and availability"""

        # Try to initialize sentence tokenizer
        if self.tokenizer_strategy == TokenizerStrategy.NLTK and HAS_NLTK:
            try:
                # Ensure punkt tokenizer is downloaded
                nltk.download('punkt', quiet=True)
                self._sentence_tokenizer_fn = sent_tokenize
                logger.info("NLTK sentence tokenizer initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize NLTK: {e}")
                self._sentence_tokenizer_fn = self._simple_sentence_split
        elif self.tokenizer_strategy == TokenizerStrategy.SENTENCEPIECE and HAS_SENTENCEPIECE:
            # SentencePiece doesn't have built-in sentence segmentation
            # We'll use it for token estimation but fall back for sentences
            if HAS_NLTK:
                try:
                    nltk.download('punkt', quiet=True)
                    self._sentence_tokenizer_fn = sent_tokenize
                    logger.info("Using NLTK for sentence segmentation with SentencePiece tokens")
                except Exception as e:
                    logger.warning(f"NLTK fallback failed: {e}")
                    self._sentence_tokenizer_fn = self._simple_sentence_split
            else:
                self._sentence_tokenizer_fn = self._simple_sentence_split
        else:
            # Fallback to simple sentence splitting
            self._sentence_tokenizer_fn = self._simple_sentence_split
            logger.info("Using simple regex-based sentence tokenizer")

    def _simple_sentence_split(self, text: str) -> List[str]:
        """
        Simple regex-based sentence splitting as ultimate fallback.

        Args:
            text: Text to split into sentences

        Returns:
            List of sentences
        """
        # German-aware sentence splitting regex
        sentence_endings = r'[.!?]+(?:\s|$)'
        sentences = re.split(sentence_endings, text)

        # Clean up and reconstruct with punctuation
        result = []
        for i, sentence in enumerate(sentences[:-1]):  # Skip last empty element
            sentence = sentence.strip()
            if sentence:
                # Find the original ending in the text
                start_pos = text.find(sentence)
                if start_pos >= 0:
                    end_pos = start_pos + len(sentence)
                    while end_pos < len(text) and text[end_pos] in '.!?':
                        end_pos += 1
                    result.append(text[start_pos:end_pos].strip())
                else:
                    result.append(sentence)

        return [s for s in result if s.strip()]

    def estimate_token_count(self, text: str) -> int:
        """
        Estimate token count for a given text.

        Uses the best available method based on configured strategy.

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated number of tokens
        """
        if not text.strip():
            return 0

        # Try SentencePiece if available (most accurate for LeoLM)
        if self.tokenizer_strategy == TokenizerStrategy.SENTENCEPIECE and HAS_SENTENCEPIECE:
            try:
                if self._tokenizer is None:
                    # For now, use word-based estimation
                    # TODO: Load actual LeoLM tokenizer model
                    pass
            except Exception as e:
                logger.debug(f"SentencePiece estimation failed: {e}")

        # Try Transformers tokenizer
        if self.tokenizer_strategy == TokenizerStrategy.TRANSFORMERS and HAS_TRANSFORMERS:
            try:
                if self._tokenizer is None:
                    # Load a German tokenizer as approximation
                    self._tokenizer = AutoTokenizer.from_pretrained(
                        "bert-base-german-cased",
                        use_fast=True
                    )
                return len(self._tokenizer.encode(text))
            except Exception as e:
                logger.debug(f"Transformers tokenizer estimation failed: {e}")

        # Fallback to word-based estimation (1.3 tokens per word for German)
        words = len(text.split())
        estimated_tokens = int(words * 1.3)

        # Add some buffer for punctuation and special tokens
        return estimated_tokens + 10

    def chunk_text(self, text: str) -> List[TextChunk]:
        """
        Split text into processable chunks respecting sentence boundaries.

        Strategy:
        1. Split text into sentences using best available tokenizer
        2. Group sentences into chunks respecting max_context_length
        3. Add sentence-level overlap between chunks for context continuity
        4. Validate token counts and adjust if necessary

        Args:
            text: Input text to be chunked

        Returns:
            List of TextChunk objects ready for processing

        Raises:
            ValueError: If text is empty or tokenization fails
        """
        if not text.strip():
            raise ValueError("Cannot chunk empty text")

        logger.info(f"Starting text chunking: {len(text)} characters")

        # Step 1: Split into sentences
        try:
            sentences = self._sentence_tokenizer_fn(text.strip())
            if not sentences:
                raise ValueError("No sentences found in text")
        except Exception as e:
            logger.error(f"Sentence tokenization failed: {e}")
            raise ValueError(f"Failed to tokenize sentences: {e}")

        logger.debug(f"Found {len(sentences)} sentences")

        # Step 2: Group sentences into chunks
        chunks = []
        current_chunk_sentences = []
        current_token_count = 0
        sentence_start_idx = 0

        for i, sentence in enumerate(sentences):
            sentence_tokens = self.estimate_token_count(sentence)

            # Check if adding this sentence would exceed max length
            if (current_token_count + sentence_tokens > self.max_context_length
                and current_chunk_sentences):

                # Create chunk from current sentences
                chunk = self._create_chunk_from_sentences(
                    current_chunk_sentences,
                    len(chunks),
                    sentence_start_idx,
                    i - 1,
                    text
                )
                chunks.append(chunk)

                # Start new chunk with overlap
                overlap_start = max(0, len(current_chunk_sentences) - self.overlap_sentences)
                current_chunk_sentences = current_chunk_sentences[overlap_start:]
                sentence_start_idx = sentence_start_idx + overlap_start
                current_token_count = sum(
                    self.estimate_token_count(s) for s in current_chunk_sentences
                )

            current_chunk_sentences.append(sentence)
            current_token_count += sentence_tokens

        # Add final chunk if there are remaining sentences
        if current_chunk_sentences:
            chunk = self._create_chunk_from_sentences(
                current_chunk_sentences,
                len(chunks),
                sentence_start_idx,
                len(sentences) - 1,
                text
            )
            chunks.append(chunk)

        # Step 3: Add overlap information
        self._calculate_overlaps(chunks, text)

        logger.info(f"Created {len(chunks)} chunks with average {sum(c.token_count for c in chunks) / len(chunks):.1f} tokens each")

        return chunks

    def _create_chunk_from_sentences(
        self,
        sentences: List[str],
        chunk_index: int,
        sentence_start: int,
        sentence_end: int,
        original_text: str
    ) -> TextChunk:
        """
        Create a TextChunk from a list of sentences.

        Args:
            sentences: List of sentences for this chunk
            chunk_index: Index of this chunk
            sentence_start: Starting sentence index in original text
            sentence_end: Ending sentence index in original text
            original_text: The complete original text

        Returns:
            TextChunk object
        """
        chunk_text = ' '.join(sentences).strip()
        token_count = self.estimate_token_count(chunk_text)

        # Find positions in original text
        start_pos = original_text.find(sentences[0]) if sentences else 0
        end_pos = start_pos + len(chunk_text) if start_pos >= 0 else len(chunk_text)

        return TextChunk(
            text=chunk_text,
            index=chunk_index,
            start_pos=start_pos,
            end_pos=end_pos,
            sentence_start=sentence_start,
            sentence_end=sentence_end,
            token_count=token_count
        )

    def _calculate_overlaps(self, chunks: List[TextChunk], original_text: str) -> None:
        """
        Calculate overlap information between adjacent chunks.

        Args:
            chunks: List of chunks to calculate overlaps for
            original_text: Original text for reference
        """
        for i, chunk in enumerate(chunks):
            if i > 0:
                # Calculate overlap with previous chunk
                prev_chunk = chunks[i - 1]
                overlap_text = self._find_overlap(prev_chunk.text, chunk.text)
                chunk.overlap_start = len(overlap_text) if overlap_text else 0

            if i < len(chunks) - 1:
                # Calculate overlap with next chunk
                next_chunk = chunks[i + 1]
                overlap_text = self._find_overlap(chunk.text, next_chunk.text)
                chunk.overlap_end = len(overlap_text) if overlap_text else 0

    def _find_overlap(self, text1: str, text2: str) -> str:
        """
        Find overlapping text between two chunks.

        Args:
            text1: First text (earlier chunk)
            text2: Second text (later chunk)

        Returns:
            Overlapping text or empty string if none found
        """
        # Simple approach: find longest suffix of text1 that matches prefix of text2
        max_overlap_len = min(len(text1), len(text2))

        for length in range(max_overlap_len, 0, -1):
            suffix = text1[-length:]
            prefix = text2[:length]
            if suffix.strip() == prefix.strip():
                return suffix

        return ""

    async def process_chunks_async(
        self,
        chunks: List[TextChunk],
        correction_fn: Callable[[str], str],
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> str:
        """
        Process chunks asynchronously using ThreadPoolExecutor.

        Args:
            chunks: List of TextChunk objects to process
            correction_fn: Function to apply correction to each chunk
            progress_callback: Optional callback for progress updates (current, total, status)

        Returns:
            Merged corrected text

        Raises:
            Exception: If processing fails completely
        """
        if not chunks:
            return ""

        logger.info(f"Starting async processing of {len(chunks)} chunks")

        # Use ThreadPoolExecutor for CPU-bound correction tasks
        max_workers = min(4, len(chunks))  # Limit concurrent processing

        async def process_single_chunk(chunk: TextChunk) -> ChunkProcessingResult:
            """Process a single chunk in thread pool"""
            loop = asyncio.get_event_loop()

            try:
                import time
                start_time = time.time()

                # Run correction in thread pool
                corrected_text = await loop.run_in_executor(
                    None, correction_fn, chunk.text
                )

                processing_time = time.time() - start_time

                return ChunkProcessingResult(
                    chunk=chunk,
                    corrected_text=corrected_text,
                    processing_time=processing_time,
                    success=True
                )

            except Exception as e:
                logger.error(f"Error processing chunk {chunk.index}: {e}")
                return ChunkProcessingResult(
                    chunk=chunk,
                    corrected_text=chunk.text,  # Fallback to original
                    processing_time=0.0,
                    error=e,
                    success=False
                )

        # Process chunks with progress reporting
        results = []
        completed = 0

        # Create semaphore to limit concurrent processing
        semaphore = asyncio.Semaphore(max_workers)

        async def process_with_semaphore(chunk: TextChunk) -> ChunkProcessingResult:
            async with semaphore:
                return await process_single_chunk(chunk)

        # Start all tasks
        tasks = [process_with_semaphore(chunk) for chunk in chunks]

        # Collect results with progress reporting
        for coro in asyncio.as_completed(tasks):
            result = await coro
            results.append(result)
            completed += 1

            if progress_callback:
                status = f"Processed chunk {result.chunk.index + 1}"
                if not result.success:
                    status += f" (failed: {result.error})"
                progress_callback(completed, len(chunks), status)

        # Sort results by chunk index to maintain order
        results.sort(key=lambda r: r.chunk.index)

        # Merge processed chunks
        corrected_texts = [r.corrected_text for r in results]
        merged_text = self._merge_overlapping_chunks(corrected_texts, chunks)

        # Log processing statistics
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        avg_time = sum(r.processing_time for r in results if r.success) / max(successful, 1)

        logger.info(f"Async processing completed: {successful} successful, {failed} failed, "
                   f"avg time: {avg_time:.2f}s")

        return merged_text

    def process_chunks_sync(
        self,
        chunks: List[TextChunk],
        correction_fn: Callable[[str], str],
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> str:
        """
        Process chunks sequentially for synchronous contexts.

        Args:
            chunks: List of TextChunk objects to process
            correction_fn: Function to apply correction to each chunk
            progress_callback: Optional callback for progress updates

        Returns:
            Merged corrected text
        """
        if not chunks:
            return ""

        logger.info(f"Starting sync processing of {len(chunks)} chunks")

        results = []

        for i, chunk in enumerate(chunks):
            try:
                import time
                start_time = time.time()

                corrected_text = correction_fn(chunk.text)
                processing_time = time.time() - start_time

                result = ChunkProcessingResult(
                    chunk=chunk,
                    corrected_text=corrected_text,
                    processing_time=processing_time,
                    success=True
                )

            except Exception as e:
                logger.error(f"Error processing chunk {chunk.index}: {e}")
                result = ChunkProcessingResult(
                    chunk=chunk,
                    corrected_text=chunk.text,  # Fallback to original
                    processing_time=0.0,
                    error=e,
                    success=False
                )

            results.append(result)

            if progress_callback:
                status = f"Processed chunk {chunk.index + 1}"
                if not result.success:
                    status += f" (failed: {result.error})"
                progress_callback(i + 1, len(chunks), status)

        # Merge processed chunks
        corrected_texts = [r.corrected_text for r in results]
        merged_text = self._merge_overlapping_chunks(corrected_texts, chunks)

        # Log processing statistics
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        avg_time = sum(r.processing_time for r in results if r.success) / max(successful, 1)

        logger.info(f"Sync processing completed: {successful} successful, {failed} failed, "
                   f"avg time: {avg_time:.2f}s")

        return merged_text

    def _merge_overlapping_chunks(
        self,
        processed_chunks: List[str],
        original_chunks: List[TextChunk]
    ) -> str:
        """
        Merge processed chunks handling overlaps intelligently.

        This method carefully handles overlapping content between chunks to avoid
        duplication or gaps in the final text.

        Args:
            processed_chunks: List of processed text chunks
            original_chunks: Corresponding TextChunk objects with overlap info

        Returns:
            Merged text with overlaps handled correctly
        """
        if not processed_chunks:
            return ""

        if len(processed_chunks) == 1:
            return processed_chunks[0]

        logger.debug(f"Merging {len(processed_chunks)} chunks with overlap handling")

        merged_parts = [processed_chunks[0]]  # Start with first chunk

        for i in range(1, len(processed_chunks)):
            current_chunk = processed_chunks[i]
            current_info = original_chunks[i]
            prev_chunk = merged_parts[-1]

            # Handle overlap with previous chunk
            if current_info.overlap_start > 0:
                # Try to find and remove overlapping content
                overlap_removed = self._remove_overlap_content(
                    prev_chunk, current_chunk, current_info.overlap_start
                )
                merged_parts.append(overlap_removed)
            else:
                # No overlap, just append
                merged_parts.append(current_chunk)

        merged_text = ' '.join(merged_parts)

        # Clean up extra whitespace
        merged_text = re.sub(r'\s+', ' ', merged_text).strip()

        logger.debug(f"Merged text length: {len(merged_text)} characters")

        return merged_text

    def _remove_overlap_content(
        self,
        prev_chunk: str,
        current_chunk: str,
        overlap_length: int
    ) -> str:
        """
        Remove overlapping content from the beginning of current chunk.

        Args:
            prev_chunk: Previously processed chunk
            current_chunk: Current chunk to remove overlap from
            overlap_length: Estimated overlap length in characters

        Returns:
            Current chunk with overlap removed
        """
        if overlap_length <= 0 or len(current_chunk) <= overlap_length:
            return current_chunk

        # Try to find sentence boundary near overlap point
        search_text = current_chunk[:overlap_length + 50]  # Look a bit beyond
        sentence_patterns = [r'[.!?]\s+', r'\.\s*$', r'!\s*$', r'\?\s*$']

        best_cut_pos = overlap_length  # Default fallback

        for pattern in sentence_patterns:
            matches = list(re.finditer(pattern, search_text))
            if matches:
                # Find match closest to overlap_length
                for match in matches:
                    cut_pos = match.end()
                    if abs(cut_pos - overlap_length) < abs(best_cut_pos - overlap_length):
                        best_cut_pos = cut_pos

        # Return chunk with overlap removed
        result = current_chunk[best_cut_pos:].strip()

        logger.debug(f"Removed {best_cut_pos} characters overlap from chunk")

        return result

    def estimate_processing_time(self, text: str, chars_per_second: float = 100.0) -> int:
        """
        Estimate processing time for progress reporting.

        Args:
            text: Text to be processed
            chars_per_second: Processing speed estimate

        Returns:
            Estimated processing time in seconds
        """
        if not text.strip():
            return 0

        # Factor in chunking overhead and LLM processing time
        base_time = len(text) / chars_per_second

        # Add overhead for chunking and merging
        chunking_overhead = len(text) / 10000  # 1 second per 10k chars

        # Estimate number of chunks and add per-chunk overhead
        estimated_chunks = math.ceil(len(text) / (self.max_context_length * 4))  # ~4 chars per token
        chunk_overhead = estimated_chunks * 0.5  # 0.5 seconds per chunk

        total_estimate = int(base_time + chunking_overhead + chunk_overhead)

        logger.debug(f"Estimated processing time: {total_estimate}s for {len(text)} chars "
                    f"({estimated_chunks} chunks)")

        return max(1, total_estimate)  # Minimum 1 second