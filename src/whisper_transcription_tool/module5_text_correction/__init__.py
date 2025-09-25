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
from pathlib import Path
from typing import Dict, Any, Optional, Union
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

        # Publish error event
        publish(EventType.CUSTOM, {
            "type": "correction_error",
            "file": str(transcription_file),
            "error": error_msg,
            "correction_id": correction_id,
            "user_id": user_id
        })

        return {
            "success": False,
            "error": error_msg,
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
    Check if text correction is available and return status information.
    """
    try:
        # Check if LLM corrector is available
        llm_available = LLMCorrector is not None

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

        return {
            "available": llm_available and can_run,
            "fallback_available": True,  # Rule-based correction always available
            "llm_available": llm_available,
            "resource_manager_available": ResourceManager is not None,
            "status": "ready" if (llm_available and can_run) else "limited",
            "available_ram_gb": available_ram,
            "min_required_ram_gb": 4.0,
            "recommended_ram_gb": 8.0,
            "models_available": {
                "minimal": available_ram >= 2.0,
                "standard": available_ram >= 4.0 and llm_available,
                "enhanced": available_ram >= 8.0 and llm_available
            },
            "system_status": status
        }
    except Exception as e:
        logger.error(f"Error checking correction availability: {e}")
        return {
            "available": False,
            "fallback_available": True,  # Rule-based correction should always work
            "error": str(e),
            "status": "error"
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
        result = await corrector.correct_text_async(
            text=text,
            correction_level=correction_level,
            dialect_normalization=dialect_normalization,
            progress_callback=lambda p, s: publish(EventType.PROGRESS_UPDATE, {
                "task": "correction",
                "status": s,
                "progress": 30 + int(p * 0.5),  # 30-80% progress
                "correction_id": correction_id,
                "user_id": user_id,
                "phase": "processing"
            })
        )

        return {
            "success": True,
            "corrected_text": result.get("corrected_text", text),
            "corrections_made": result.get("corrections", []),
            "improvement_score": result.get("improvement_score", 0),
            "method": "llm",
            "metadata": result.get("metadata", {})
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
    improvement_score = len(corrections_made) / max(len(text), 1) * 100

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
            "dialect_normalization": dialect_normalization
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