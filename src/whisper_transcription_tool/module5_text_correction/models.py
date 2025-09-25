"""
Data models for the Text Correction module.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum


class CorrectionLevel(Enum):
    """Available correction levels."""
    LIGHT = "light"
    STANDARD = "standard"
    STRICT = "strict"


class ModelType(Enum):
    """Types of models that can be managed."""
    WHISPER = "whisper"
    LEOLM = "leolm"


class JobStatus(Enum):
    """Job status states."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class CorrectionResult:
    """Result of a text correction operation."""
    original_text: str
    corrected_text: Optional[str]
    success: bool
    correction_level: str
    processing_time_seconds: float
    chunks_processed: int
    model_used: str
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "original_text": self.original_text,
            "corrected_text": self.corrected_text,
            "success": self.success,
            "correction_level": self.correction_level,
            "processing_time_seconds": self.processing_time_seconds,
            "chunks_processed": self.chunks_processed,
            "model_used": self.model_used,
            "error_message": self.error_message,
            "metadata": self.metadata or {}
        }


@dataclass
class CorrectionJob:
    """Represents a text correction job."""
    job_id: str
    input_file: str
    correction_level: str
    dialect_normalization: bool
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[CorrectionResult] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "job_id": self.job_id,
            "input_file": self.input_file,
            "correction_level": self.correction_level,
            "dialect_normalization": self.dialect_normalization,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result.to_dict() if self.result else None
        }


@dataclass
class ModelStatus:
    """Status information for a loaded model."""
    model_type: str
    is_loaded: bool
    model_path: str
    memory_usage_mb: int
    load_time_seconds: Optional[float] = None
    last_used: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "model_type": self.model_type,
            "is_loaded": self.is_loaded,
            "model_path": self.model_path,
            "memory_usage_mb": self.memory_usage_mb,
            "load_time_seconds": self.load_time_seconds,
            "last_used": self.last_used.isoformat() if self.last_used else None
        }


@dataclass
class SystemResources:
    """System resource information."""
    total_ram_gb: float
    available_ram_gb: float
    cpu_usage_percent: float
    gpu_available: bool
    gpu_memory_gb: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_ram_gb": self.total_ram_gb,
            "available_ram_gb": self.available_ram_gb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "gpu_available": self.gpu_available,
            "gpu_memory_gb": self.gpu_memory_gb
        }


@dataclass
class TextChunk:
    """Represents a chunk of text for processing."""
    text: str
    index: int
    start_pos: int
    end_pos: int
    overlap_start: int = 0  # Characters overlapping with previous chunk
    overlap_end: int = 0    # Characters overlapping with next chunk

    def __len__(self) -> int:
        """Return the length of the text."""
        return len(self.text)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "text": self.text,
            "index": self.index,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "overlap_start": self.overlap_start,
            "overlap_end": self.overlap_end
        }


@dataclass
class CorrectionConfig:
    """Configuration for text correction operations."""
    enabled: bool = False
    model_path: str = "~/models/leolm-13b/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf"
    context_length: int = 2048
    temperature: float = 0.3
    correction_level: CorrectionLevel = CorrectionLevel.STANDARD
    keep_original: bool = True
    auto_batch: bool = True
    max_parallel_jobs: int = 1
    dialect_normalization: bool = False
    chunk_overlap_sentences: int = 1
    memory_threshold_gb: float = 6.0
    monitoring_enabled: bool = False
    gpu_acceleration: str = "auto"
    fallback_on_error: bool = True
    platform_optimization: Dict[str, Any] = field(default_factory=lambda: {
        "macos_metal": True,
        "cuda_support": False,
        "cpu_threads": "auto"
    })

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "enabled": self.enabled,
            "model_path": self.model_path,
            "context_length": self.context_length,
            "temperature": self.temperature,
            "correction_level": self.correction_level.value,
            "keep_original": self.keep_original,
            "auto_batch": self.auto_batch,
            "max_parallel_jobs": self.max_parallel_jobs,
            "dialect_normalization": self.dialect_normalization,
            "chunk_overlap_sentences": self.chunk_overlap_sentences,
            "memory_threshold_gb": self.memory_threshold_gb,
            "monitoring_enabled": self.monitoring_enabled,
            "gpu_acceleration": self.gpu_acceleration,
            "fallback_on_error": self.fallback_on_error,
            "platform_optimization": self.platform_optimization
        }