"""
Module 5: Text Correction with LLM Integration

This module provides AI-powered text correction capabilities for transcripts using
local LLM models, with advanced resource management and memory optimization.

Components:
- BatchProcessor: Intelligent text chunking and batch processing for LLM correction
- TextChunk: Data structure for text chunks with overlap handling
- ResourceManager: Thread-safe singleton for managing system resources and model swapping
- TextCorrector: Main interface for text correction using LLM models
- LLMManager: Interface for local LLM models (LeoLM integration)

Features:
- Intelligent text chunking with sentence boundary respect
- SentencePiece tokenizer integration for LeoLM compatibility
- NLTK fallback for sentence segmentation
- Async and sync processing modes with progress reporting
- Thread-safe model loading/unloading
- Memory monitoring and automatic cleanup
- Model swapping between Whisper and LeoLM
- GPU acceleration support (Metal on macOS)
- Performance metrics collection
"""

import asyncio
import json
import os
import logging
import time
import difflib
from pathlib import Path
from typing import Dict, Any, Optional, Union, Tuple, List
from datetime import datetime

from ..core.config import load_config
from ..core.events import publish, EventType
from ..core.logging_setup import get_logger

logger = get_logger(__name__)

# Import with graceful fallbacks for optional dependencies
try:
    from .batch_processor import BatchProcessor, TextChunk, TokenizerStrategy, ChunkProcessingResult
except ImportError as e:
    logger.warning(f"BatchProcessor not available: {e}")
    BatchProcessor = None
    TextChunk = None
    TokenizerStrategy = None
    ChunkProcessingResult = None

try:
    from .llm_corrector import LLMCorrector, correct_text_quick
except ImportError as e:
    logger.warning(f"LLMCorrector not available: {e}")
    LLMCorrector = None
    correct_text_quick = None

try:
    from .resource_manager import ResourceManager
except ImportError as e:
    logger.warning(f"ResourceManager not available: {e}")
    ResourceManager = None


def _analyze_corrections(original: str, corrected: str) -> Tuple[List[str], float]:
    """Create a simple diff-based summary between original and corrected text."""
    if not original or original == corrected:
        return [], 0.0

    original_words = original.split()
    corrected_words = corrected.split()
    matcher = difflib.SequenceMatcher(None, original_words, corrected_words)

    corrections: List[str] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            before = " ".join(original_words[i1:i2]).strip()
            after = " ".join(corrected_words[j1:j2]).strip()
            if before or after:
                corrections.append(f"Ersetzt: '{before}' → '{after}'")
        elif tag == "delete":
            removed = " ".join(original_words[i1:i2]).strip()
            if removed:
                corrections.append(f"Entfernt: '{removed}'")
        elif tag == "insert":
            added = " ".join(corrected_words[j1:j2]).strip()
            if added:
                corrections.append(f"Hinzugefügt: '{added}'")

    unique_corrections: List[str] = []
    for entry in corrections:
        if entry and entry not in unique_corrections:
            unique_corrections.append(entry)

    improvement = (len(unique_corrections) / max(len(original_words), 1)) * 100
    return unique_corrections, round(improvement, 2)

# Orchestration functions for API integration
async def correct_transcription(
    transcription_file: Union[str, Path],
    enable_correction: bool = True,
    correction_level: str = "standard",
    dialect_normalization: bool = False,
    config: Optional[Dict] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main orchestration function for text correction.

    Args:
        transcription_file: Path to transcription file
        enable_correction: Whether to enable correction
        correction_level: Level of correction (minimal, standard, enhanced)
        dialect_normalization: Whether to normalize dialects
        config: Configuration dictionary
        user_id: User ID for progress tracking

    Returns:
        Dict with correction results
    """
    if not enable_correction:
        return {
            "success": True,
            "correction_enabled": False,
            "message": "Text correction was disabled"
        }

    if config is None:
        config = load_config()

    transcription_file = Path(transcription_file)

    # Generate correction ID
    import uuid
    correction_id = str(uuid.uuid4())[:8]
    if user_id:
        correction_id = f"{user_id}_{correction_id}"

    logger.info(f"Starting text correction for: {transcription_file}")

    # Publish correction started event
    publish(EventType.CUSTOM, {
        "type": "correction_started",
        "file": str(transcription_file),
        "correction_level": correction_level,
        "dialect_normalization": dialect_normalization,
        "correction_id": correction_id,
        "user_id": user_id
    })

    try:
        # Check if file exists
        if not transcription_file.exists():
            raise FileNotFoundError(f"Transcription file not found: {transcription_file}")

        # Read original text
        with open(transcription_file, 'r', encoding='utf-8') as f:
            original_text = f.read()

        # Progress update
        publish(EventType.PROGRESS_UPDATE, {
            "task": "correction",
            "status": f"Starting text correction with {correction_level} level...",
            "progress": 10,
            "correction_id": correction_id,
            "user_id": user_id,
            "phase": "initialization"
        })

        # Check if LLM correction is available
        if LLMCorrector is None:
            logger.warning("LLMCorrector not available, using fallback method")
            correction_result = await _fallback_correction(
                original_text, correction_level, dialect_normalization, correction_id, user_id
            )
        else:
            # Get ResourceManager to check availability if available
            if ResourceManager is None:
                logger.warning("ResourceManager not available, assuming correction is possible")
                status = {"can_run_correction": True}
            else:
                resource_manager = ResourceManager()
                status = resource_manager.get_status()

            if not status.get("can_run_correction", False):
                # Fallback to simple rule-based correction
                logger.warning("LLM correction not available due to resource constraints, using fallback method")
                correction_result = await _fallback_correction(
                    original_text, correction_level, dialect_normalization, correction_id, user_id
                )
            else:
                # Use full LLM correction
                logger.info("Using LLM-based text correction")
                corrector = LLMCorrector()
                correction_result = await _llm_correction(
                    corrector, original_text, correction_level, dialect_normalization, correction_id, user_id
                )

        # Save corrected file
        output_dir = transcription_file.parent
        stem = transcription_file.stem
        suffix = transcription_file.suffix

        corrected_file = output_dir / f"{stem}_corrected{suffix}"
        metadata_file = output_dir / f"{stem}_correction_metadata.json"

        # Write corrected text
        with open(corrected_file, 'w', encoding='utf-8') as f:
            f.write(correction_result["corrected_text"])

        # Write metadata
        metadata = {
            "original_file": str(transcription_file),
            "corrected_file": str(corrected_file),
            "correction_timestamp": datetime.now().isoformat(),
            "correction_level": correction_level,
            "dialect_normalization": dialect_normalization,
            "method": correction_result.get("method", "unknown"),
            **correction_result.get("metadata", {})
        }

        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        # Final progress update
        publish(EventType.PROGRESS_UPDATE, {
            "task": "correction",
            "status": "Text correction completed",
            "progress": 100,
            "correction_id": correction_id,
            "user_id": user_id,
            "phase": "completed"
        })

        # Publish completion event
        publish(EventType.CUSTOM, {
            "type": "correction_completed",
            "original_file": str(transcription_file),
            "corrected_file": str(corrected_file),
            "metadata_file": str(metadata_file),
            "corrections_made": correction_result.get("corrections_made", []),
            "improvement_score": correction_result.get("improvement_score", 0),
            "correction_id": correction_id,
            "user_id": user_id
        })

        return {
            "success": True,
            "original_file": str(transcription_file),
            "corrected_file": str(corrected_file),
            "metadata_file": str(metadata_file),
            "correction_result": correction_result
        }

    except Exception as e:
        error_msg = f"Text correction failed: {str(e)}"
        logger.error(error_msg)

        # Determine error category and recommendation
        error_category = "unknown"
        error_recommendation = "Please check the logs for more details."

        if "model" in str(e).lower() and "not found" in str(e).lower():
            error_category = "model_missing"
            error_recommendation = "Download the LeoLM model to enable AI-powered text correction."
        elif "tensor" in str(e).lower() or "dimension" in str(e).lower():
            error_category = "model_incompatible"
            error_recommendation = "The model file appears incompatible. Try a different quantization or update llama-cpp-python."
        elif "memory" in str(e).lower() or "ram" in str(e).lower():
            error_category = "insufficient_memory"
            error_recommendation = "Not enough memory available. Close other applications or use a smaller model."
        elif "file not found" in str(e).lower():
            error_category = "file_not_found"
            error_recommendation = f"The transcription file was not found: {transcription_file}"
        elif "load model" in str(e).lower():
            error_category = "model_load_failed"
            error_recommendation = "Failed to load the LLM model. Check model file integrity and system resources."

        # Publish detailed error event
        publish(EventType.CUSTOM, {
            "type": "correction_error",
            "file": str(transcription_file),
            "error": error_msg,
            "error_category": error_category,
            "error_recommendation": error_recommendation,
            "error_type": type(e).__name__,
            "correction_id": correction_id,
            "user_id": user_id,
            "correction_level": correction_level,
            "fallback_available": True  # Rule-based correction is always available
        })

        return {
            "success": False,
            "error": error_msg,
            "error_category": error_category,
            "recommendation": error_recommendation,
            "fallback_available": True,
            "original_file": str(transcription_file)
        }

def correct_transcription_sync(
    transcription_file: Union[str, Path],
    enable_correction: bool = True,
    correction_level: str = "standard",
    dialect_normalization: bool = False,
    config: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Synchronous wrapper for text correction (for CLI usage).
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            correct_transcription(
                transcription_file,
                enable_correction,
                correction_level,
                dialect_normalization,
                config
            )
        )
        return result
    finally:
        loop.close()

def check_correction_availability() -> Dict[str, Any]:
    """
    Check if text correction is available and return detailed status information.
    """
    try:
        # Check if LLM corrector is available
        llm_available = LLMCorrector is not None
        llm_error = None
        model_status = "not_checked"

        # Try to validate LLM model if available
        if llm_available:
            try:
                # Try to check if model file exists
                from .llm_corrector import LLMCorrector as LLMCorrectorClass
                model_path = LLMCorrectorClass.DEFAULT_MODEL_PATH

                if os.path.exists(model_path):
                    model_status = "model_found"
                    # Try to validate model format
                    try:
                        # Quick validation - check if it's a valid GGUF file
                        with open(model_path, 'rb') as f:
                            header = f.read(4)
                            if header == b'GGUF':
                                model_status = "model_valid"
                            else:
                                model_status = "model_invalid"
                                llm_error = "Model file is not in valid GGUF format"
                    except Exception as e:
                        model_status = "model_unreadable"
                        llm_error = f"Cannot read model file: {str(e)}"
                else:
                    model_status = "model_missing"
                    llm_error = f"Model file not found at {model_path}"
            except Exception as e:
                model_status = "check_failed"
                llm_error = f"Failed to check model: {str(e)}"

        # Check system resources if ResourceManager is available
        if ResourceManager is not None:
            resource_manager = ResourceManager()
            status = resource_manager.get_status()
            memory_info = resource_manager.check_available_memory()
            available_ram = memory_info.get("available_gb", 0)
            can_run = status.get("memory_safe", False) and available_ram >= 4.0
        else:
            # Fallback - try to get basic memory info
            try:
                import psutil
                memory = psutil.virtual_memory()
                available_ram = memory.available / (1024**3)
            except ImportError:
                # If psutil not available, assume reasonable defaults
                available_ram = 8.0  # Assume 8GB available
                logger.warning("psutil not available, using default memory assumptions")

            can_run = available_ram >= 2.0
            status = {"can_run_correction": can_run}

        # Determine overall status and recommendation
        if not llm_available:
            overall_status = "llm_unavailable"
            recommendation = "LLM module not available. Using fallback rule-based correction."
        elif model_status == "model_missing":
            overall_status = "model_missing"
            recommendation = "LLM model not found. Please download LeoLM model to enable AI correction."
        elif model_status == "model_invalid":
            overall_status = "model_incompatible"
            recommendation = "Model file format issue. Try downloading a different quantization of LeoLM."
        elif not can_run:
            overall_status = "insufficient_memory"
            recommendation = f"Not enough memory. Need at least 4GB free RAM, have {available_ram:.1f}GB."
        else:
            overall_status = "ready"
            recommendation = "Text correction ready with LLM support."

        return {
            "available": llm_available and can_run and model_status == "model_valid",
            "fallback_available": True,  # Rule-based correction always available
            "llm_available": llm_available,
            "llm_error": llm_error,
            "model_status": model_status,
            "resource_manager_available": ResourceManager is not None,
            "status": overall_status,
            "recommendation": recommendation,
            "available_ram_gb": available_ram,
            "min_required_ram_gb": 4.0,
            "recommended_ram_gb": 8.0,
            "models_available": {
                "minimal": available_ram >= 2.0,
                "standard": available_ram >= 4.0 and llm_available and model_status == "model_valid",
                "enhanced": available_ram >= 8.0 and llm_available and model_status == "model_valid"
            },
            "system_status": status,
            "fallback_active": not (llm_available and can_run and model_status == "model_valid")
        }
    except Exception as e:
        logger.error(f"Error checking correction availability: {e}")
        return {
            "available": False,
            "fallback_available": True,  # Rule-based correction should always work
            "fallback_active": True,
            "error": str(e),
            "status": "error",
            "recommendation": f"Error checking correction status: {str(e)}"
        }

async def _llm_correction(
    corrector: LLMCorrector,
    text: str,
    correction_level: str,
    dialect_normalization: bool,
    correction_id: str,
    user_id: Optional[str]
) -> Dict[str, Any]:
    """Use LLM-based correction."""
    try:
        # Progress update
        publish(EventType.PROGRESS_UPDATE, {
            "task": "correction",
            "status": "Loading LLM model for text correction...",
            "progress": 30,
            "correction_id": correction_id,
            "user_id": user_id,
            "phase": "model_loading"
        })

        # Perform correction
        start_time = time.time()
        llm_level_map = {
            "minimal": "basic",
            "light": "basic",
            "standard": "advanced",
            "strict": "formal",
            "enhanced": "formal"
        }
        llm_level = llm_level_map.get(correction_level.lower(), "advanced") if isinstance(correction_level, str) else "advanced"

        result = await corrector.correct_text_async(
            text=text,
            correction_level=llm_level,
            language="de"
        )
        duration = time.time() - start_time

        if isinstance(result, dict):
            corrected_text = result.get("corrected_text", text)
            corrections_made = result.get("corrections", [])
            improvement_score = result.get("improvement_score", 0)
            metadata = result.get("metadata", {})
        else:
            corrected_text = result if isinstance(result, str) else text
            corrections_made = []
            improvement_score = 0.0
            metadata = {}

        if not corrections_made:
            corrections_made, improvement_score = _analyze_corrections(text, corrected_text)

        model_info = corrector.get_model_info()
        if model_info.get("model_path"):
            model_info["model_name"] = Path(model_info["model_path"]).name

        metadata = {
            **metadata,
            "processing_time_seconds": duration,
            "model_info": model_info,
            "correction_level": correction_level,
            "llm_level": llm_level,
            "dialect_normalization": dialect_normalization
        }

        logger.info(
            "LLM correction completed in %.2fs with %d adjustments (model=%s)",
            duration,
            len(corrections_made),
            model_info.get("model_name") or model_info.get("model_path")
        )

        return {
            "success": True,
            "corrected_text": corrected_text or text,
            "corrections_made": corrections_made,
            "improvement_score": improvement_score,
            "method": "llm",
            "metadata": metadata
        }

    except Exception as e:
        logger.error(f"LLM correction failed: {e}")
        # Fallback to rule-based correction
        return await _fallback_correction(text, correction_level, dialect_normalization, correction_id, user_id)

async def _fallback_correction(
    text: str,
    correction_level: str,
    dialect_normalization: bool,
    correction_id: str,
    user_id: Optional[str]
) -> Dict[str, Any]:
    """Fallback rule-based correction."""
    start_time = time.time()
    # Progress update
    publish(EventType.PROGRESS_UPDATE, {
        "task": "correction",
        "status": "Using fallback rule-based correction...",
        "progress": 50,
        "correction_id": correction_id,
        "user_id": user_id,
        "phase": "fallback_processing"
    })

    corrected_text = text
    corrections_made = []

    # Basic corrections
    simple_corrections = {
        " äh ": " ",
        " ähm ": " ",
        " eh ": " ",
        " ehm ": " ",
        "  ": " ",  # Double spaces
    }

    for wrong, right in simple_corrections.items():
        if wrong in corrected_text:
            corrected_text = corrected_text.replace(wrong, right)
            corrections_made.append(f"Removed filler word/space: '{wrong}' -> '{right}'")

    # Capitalize sentences
    sentences = corrected_text.split('. ')
    capitalized_sentences = []
    for sentence in sentences:
        if sentence.strip():
            sentence = sentence.strip()
            sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
            capitalized_sentences.append(sentence)

    if len(sentences) > 1:
        corrected_text = '. '.join(capitalized_sentences)
        if not corrected_text.endswith('.'):
            corrected_text += '.'

    # Dialect normalization
    if dialect_normalization:
        dialect_corrections = {
            "net": "nicht",
            "hab": "habe",
            "n": "ein",
            "mal": "einmal"
        }

        for dialect, standard in dialect_corrections.items():
            pattern = f" {dialect} "
            replacement = f" {standard} "
            if pattern in corrected_text:
                corrected_text = corrected_text.replace(pattern, replacement)
                corrections_made.append(f"Dialect correction: '{dialect}' -> '{standard}'")

    # Calculate improvement score
    improvement_score = len(corrections_made) / max(len(text.split()), 1) * 100

    duration = time.time() - start_time

    logger.info(
        "Fallback rule-based correction completed in %.2fs with %d adjustments",
        duration,
        len(corrections_made)
    )

    return {
        "success": True,
        "corrected_text": corrected_text,
        "corrections_made": corrections_made,
        "improvement_score": round(improvement_score, 2),
        "method": "rule_based",
        "metadata": {
            "original_length": len(text),
            "corrected_length": len(corrected_text),
            "correction_level": correction_level,
            "dialect_normalization": dialect_normalization,
            "processing_time_seconds": duration,
            "model_info": {
                "model_path": None,
                "model_loaded": False,
                "model_name": "rule_based"
            }
        }
    }

__version__ = "1.0.0"

# Build __all__ list based on available components
__all__ = [
    "correct_transcription",
    "correct_transcription_sync",
    "check_correction_availability"
]

# Add available components
if BatchProcessor is not None:
    __all__.extend(["BatchProcessor", "TokenizerStrategy", "ChunkProcessingResult"])
if TextChunk is not None:
    __all__.append("TextChunk")
if LLMCorrector is not None:
    __all__.extend(["LLMCorrector", "correct_text_quick"])
if ResourceManager is not None:
    __all__.append("ResourceManager")
