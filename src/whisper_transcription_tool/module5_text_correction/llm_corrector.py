"""
LLMCorrector - Local LLM Integration for Text Correction

This module provides text correction capabilities using the LeoLM model via llama-cpp-python.
Optimized for Apple Silicon with Metal acceleration.
"""

import logging
import re
import math
import os
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    logger.warning("llama-cpp-python not available. LLM correction disabled.")


class LLMCorrector:
    """
    Local LLM text corrector using LeoLM model with llama-cpp-python.

    Features:
    - Metal GPU acceleration on macOS
    - Context length management (2048 tokens default)
    - Temperature control for consistent corrections
    - Token counting and text chunking
    - Model lifecycle management
    """

    # Default model path
    DEFAULT_MODEL_PATH = "/Users/denniswestermann/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf"

    # Correction prompts for different levels
    CORRECTION_PROMPTS = {
        "basic": {
            "de": """Du bist ein deutscher Textkorrektur-Assistent. Korrigiere den folgenden Text:
- Behebe Rechtschreibfehler
- Korrigiere Grammatikfehler
- Verbessere die Zeichensetzung

Gib nur den korrigierten Text zurück, ohne Erklärungen:

Text: {text}

Korrigierter Text:""",
            "en": """You are a German text correction assistant. Correct the following text:
- Fix spelling errors
- Correct grammar errors
- Improve punctuation

Return only the corrected text without explanations:

Text: {text}

Corrected text:"""
        },
        "advanced": {
            "de": """Du bist ein professioneller deutscher Textkorrektur-Experte. Korrigiere und verbessere den folgenden Text:
- Behebe alle Rechtschreibfehler
- Korrigiere Grammatik und Satzbau
- Verbessere die Zeichensetzung
- Optimiere den Stil und die Lesbarkeit
- Achte auf konsistente Terminologie

Gib nur den korrigierten Text zurück, ohne Erklärungen:

Text: {text}

Korrigierter Text:""",
            "en": """You are a professional German text correction expert. Correct and improve the following text:
- Fix all spelling errors
- Correct grammar and sentence structure
- Improve punctuation
- Optimize style and readability
- Ensure consistent terminology

Return only the corrected text without explanations:

Text: {text}

Corrected text:"""
        },
        "formal": {
            "de": """Du bist ein Experte für formelle deutsche Texte. Korrigiere und formalisiere den folgenden Text:
- Behebe alle Rechtschreib- und Grammatikfehler
- Verwende formelle Sprache und Stil
- Optimiere für professionelle Kommunikation
- Achte auf korrekte Anrede und Höflichkeitsformen
- Verwende präzise und eindeutige Formulierungen

Gib nur den korrigierten, formalisierten Text zurück:

Text: {text}

Korrigierter Text:""",
            "en": """You are an expert for formal German texts. Correct and formalize the following text:
- Fix all spelling and grammar errors
- Use formal language and style
- Optimize for professional communication
- Use correct forms of address and politeness
- Use precise and clear formulations

Return only the corrected, formalized text:

Text: {text}

Corrected text:"""
        }
    }

    def __init__(self, model_path: Optional[str] = None, context_length: int = 2048):
        """
        Initialize LLMCorrector.

        Args:
            model_path: Path to LeoLM model file. Uses default if None.
            context_length: Maximum context length in tokens.
        """
        self.model_path = Path(model_path or self.DEFAULT_MODEL_PATH)
        self.context_length = context_length
        self.temperature = 0.3  # Low temperature for consistent corrections
        self.model: Optional[Llama] = None
        self._model_loaded = False

        # Validate model path
        if not self.model_path.exists():
            raise FileNotFoundError(f"LeoLM model not found at: {self.model_path}")

        if not LLAMA_CPP_AVAILABLE:
            raise ImportError("llama-cpp-python not available. Install with: pip install llama-cpp-python")

    def load_model(self) -> bool:
        """
        Load the LeoLM model with Metal optimization.

        Returns:
            True if model loaded successfully, False otherwise.
        """
        if self._model_loaded:
            logger.info("Model already loaded")
            return True

        try:
            logger.info(f"Loading LeoLM model from: {self.model_path}")

            # Configure for macOS Metal acceleration
            self.model = Llama(
                model_path=str(self.model_path),
                n_ctx=self.context_length,
                n_gpu_layers=-1,  # Use all GPU layers on Metal
                n_threads=os.cpu_count(),
                verbose=False,
                use_mlock=True,  # Lock model in memory
                use_mmap=True,   # Use memory mapping
            )

            self._model_loaded = True
            logger.info(f"Model loaded successfully. Context length: {self.context_length}")
            return True

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None
            self._model_loaded = False
            return False

    def unload_model(self) -> None:
        """Unload the model and free memory."""
        if self.model is not None:
            logger.info("Unloading LeoLM model")
            # llama-cpp-python handles cleanup automatically
            del self.model
            self.model = None
            self._model_loaded = False
            logger.info("Model unloaded")

    def is_model_loaded(self) -> bool:
        """Check if model is currently loaded."""
        return self._model_loaded and self.model is not None

    def get_context_length(self) -> int:
        """Get the context length of the loaded model."""
        if not self.is_model_loaded():
            return self.context_length
        return self.model.n_ctx()

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in text.

        Args:
            text: Input text to estimate tokens for.

        Returns:
            Estimated number of tokens.
        """
        # Simple estimation: ~4 characters per token for German text
        return max(1, len(text) // 4)

    def tokenize(self, text: str) -> List[int]:
        """
        Tokenize text using the loaded model.

        Args:
            text: Text to tokenize.

        Returns:
            List of token IDs.
        """
        if not self.is_model_loaded():
            raise RuntimeError("Model not loaded. Call load_model() first.")

        return self.model.tokenize(text.encode('utf-8'))

    def chunk_text(self, text: str, max_tokens: int = None) -> List[str]:
        """
        Split text into chunks that fit within token limits.

        Args:
            text: Text to chunk.
            max_tokens: Maximum tokens per chunk. Uses 80% of context length if None.

        Returns:
            List of text chunks.
        """
        if max_tokens is None:
            max_tokens = int(self.context_length * 0.8)  # Reserve 20% for prompt

        # Split on sentences first, keeping the punctuation
        sentences = re.split(r'([.!?]+\s*)', text)
        # Recombine sentences with their punctuation
        combined_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i]
            if i + 1 < len(sentences):
                sentence += sentences[i + 1]  # Add the punctuation back
            if sentence.strip():
                combined_sentences.append(sentence.strip())

        # Handle any remaining text without punctuation
        if len(sentences) % 2 == 1 and sentences[-1].strip():
            combined_sentences.append(sentences[-1].strip())

        sentences = combined_sentences
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Estimate tokens for current chunk + sentence
            test_chunk = f"{current_chunk} {sentence}".strip()
            estimated_tokens = self.estimate_tokens(test_chunk)

            if estimated_tokens <= max_tokens:
                current_chunk = test_chunk
            else:
                # Start new chunk
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence

                # If single sentence is too long, split by words
                if self.estimate_tokens(current_chunk) > max_tokens:
                    words = current_chunk.split()
                    current_chunk = ""
                    for word in words:
                        test_chunk = f"{current_chunk} {word}".strip()
                        if self.estimate_tokens(test_chunk) <= max_tokens:
                            current_chunk = test_chunk
                        else:
                            if current_chunk:
                                chunks.append(current_chunk)
                            current_chunk = word

        if current_chunk:
            chunks.append(current_chunk)

        return chunks if chunks else [text]

    def _generate_correction(self, prompt: str) -> str:
        """
        Generate text correction using the model.

        Args:
            prompt: Complete prompt including text to correct.

        Returns:
            Corrected text.
        """
        if not self.is_model_loaded():
            raise RuntimeError("Model not loaded. Call load_model() first.")

        try:
            response = self.model(
                prompt,
                max_tokens=min(512, self.context_length // 4),  # Limit response length
                temperature=self.temperature,
                top_p=0.9,
                repeat_penalty=1.1,
                stop=["Text:", "Korrigierter Text:", "Corrected text:"],
                echo=False
            )

            corrected_text = response['choices'][0]['text'].strip()

            # Clean up common artifacts
            corrected_text = re.sub(r'^["\']|["\']$', '', corrected_text)  # Remove quotes
            corrected_text = re.sub(r'\n+', ' ', corrected_text)  # Replace newlines with spaces
            corrected_text = re.sub(r'\s+', ' ', corrected_text)  # Normalize whitespace

            return corrected_text

        except Exception as e:
            logger.error(f"Error during text generation: {e}")
            raise

    def correct_text(self, text: str, correction_level: str = "basic", language: str = "de") -> str:
        """
        Correct text using the loaded LLM model.

        Args:
            text: Text to correct.
            correction_level: Level of correction ("basic", "advanced", "formal").
            language: Language for prompts ("de", "en").

        Returns:
            Corrected text.
        """
        if not text.strip():
            return text

        if not self.is_model_loaded():
            if not self.load_model():
                raise RuntimeError("Failed to load model")

        # Validate correction level
        if correction_level not in self.CORRECTION_PROMPTS:
            logger.warning(f"Unknown correction level: {correction_level}. Using 'basic'.")
            correction_level = "basic"

        # Validate language
        if language not in self.CORRECTION_PROMPTS[correction_level]:
            logger.warning(f"Language {language} not supported. Using 'de'.")
            language = "de"

        try:
            # Get prompt template
            prompt_template = self.CORRECTION_PROMPTS[correction_level][language]

            # Check if text needs chunking
            estimated_tokens = self.estimate_tokens(text)
            max_text_tokens = int(self.context_length * 0.6)  # Reserve 40% for prompt and response

            if estimated_tokens <= max_text_tokens:
                # Process entire text at once
                prompt = prompt_template.format(text=text)
                return self._generate_correction(prompt)
            else:
                # Process in chunks
                logger.info(f"Text too long ({estimated_tokens} tokens), processing in chunks")
                chunks = self.chunk_text(text, max_text_tokens)
                corrected_chunks = []

                for i, chunk in enumerate(chunks):
                    logger.info(f"Processing chunk {i+1}/{len(chunks)}")
                    prompt = prompt_template.format(text=chunk)
                    corrected_chunk = self._generate_correction(prompt)
                    corrected_chunks.append(corrected_chunk)

                # Join corrected chunks
                return " ".join(corrected_chunks)

        except Exception as e:
            logger.error(f"Error during text correction: {e}")
            raise

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.

        Returns:
            Dictionary with model information.
        """
        info = {
            "model_path": str(self.model_path),
            "model_loaded": self._model_loaded,
            "context_length": self.context_length,
            "temperature": self.temperature,
        }

        if self.is_model_loaded():
            info.update({
                "actual_context_length": self.model.n_ctx(),
                "vocab_size": self.model.n_vocab(),
            })

        return info

    def __enter__(self):
        """Context manager entry."""
        self.load_model()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.unload_model()

    def __del__(self):
        """Destructor to ensure cleanup."""
        if hasattr(self, 'model') and self.model is not None:
            self.unload_model()


# Convenience function for quick text correction
def correct_text_quick(text: str, correction_level: str = "basic", language: str = "de",
                      model_path: Optional[str] = None) -> str:
    """
    Quick text correction function.

    Args:
        text: Text to correct.
        correction_level: Level of correction ("basic", "advanced", "formal").
        language: Language for prompts ("de", "en").
        model_path: Path to LeoLM model file.

    Returns:
        Corrected text.
    """
    with LLMCorrector(model_path=model_path) as corrector:
        return corrector.correct_text(text, correction_level, language)


if __name__ == "__main__":
    # Example usage
    import argparse

    parser = argparse.ArgumentParser(description="Test LLMCorrector")
    parser.add_argument("text", help="Text to correct")
    parser.add_argument("--level", default="basic", choices=["basic", "advanced", "formal"],
                       help="Correction level")
    parser.add_argument("--lang", default="de", choices=["de", "en"],
                       help="Language")
    parser.add_argument("--model", help="Path to model file")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    try:
        corrected = correct_text_quick(args.text, args.level, args.lang, args.model)
        print("Original:", args.text)
        print("Corrected:", corrected)
    except Exception as e:
        print(f"Error: {e}")