"""
Batch Manager - Advanced batch processing for FileKeeper
Handles complex batch operations, file organization, and cleanup.
"""

import os
import json
import shutil
import glob
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Iterator
from dataclasses import dataclass, asdict

from .exceptions import FileFormatError
from .logging_setup import get_logger
from .models import OutputFormat
from .file_keeper import FileKeeper, CorrectionMetadata, FileOutputPair
from .output_handler import OutputHandler

logger = get_logger(__name__)


@dataclass
class BatchConfig:
    """Configuration for batch processing operations."""
    base_name_pattern: str = "batch_item_{index:03d}"
    output_format: OutputFormat = OutputFormat.TXT
    output_directory: Optional[str] = None
    preserve_original_names: bool = False
    add_timestamps: bool = True
    cleanup_after_processing: bool = True
    max_files_per_batch: int = 100
    create_summary: bool = True


@dataclass
class BatchItem:
    """Individual item in a batch processing operation."""
    index: int
    original_text: str
    corrected_text: Optional[str] = None
    base_name: Optional[str] = None
    segments_data: Optional[List[Dict]] = None
    metadata: Optional[CorrectionMetadata] = None
    source_file: Optional[str] = None


@dataclass
class BatchResult:
    """Results of a batch processing operation."""
    batch_id: str
    total_items: int
    successful_items: int
    failed_items: int
    output_files: List[str]
    failed_files: List[Dict[str, str]]
    summary_file: Optional[str]
    processing_time_seconds: float
    created_at: str


class BatchManager:
    """
    Advanced batch processing manager for the FileKeeper system.
    Handles complex batch operations with proper file organization.
    """

    def __init__(self, config=None):
        """Initialize BatchManager with FileKeeper and OutputHandler."""
        self.file_keeper = FileKeeper(config)
        self.output_handler = OutputHandler(config)
        self.config = config

        # Active batch tracking
        self.active_batches: Dict[str, BatchResult] = {}

    def generate_batch_id(self, prefix: str = "batch") -> str:
        """Generate unique batch ID with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
        return f"{prefix}_{timestamp}"

    def create_batch_from_files(self,
                               file_paths: List[str],
                               batch_config: Optional[BatchConfig] = None) -> List[BatchItem]:
        """
        Create batch items from existing files.

        Args:
            file_paths: List of file paths to process
            batch_config: Batch configuration

        Returns:
            List of BatchItem objects
        """
        config = batch_config or BatchConfig()
        batch_items = []

        for i, file_path in enumerate(file_paths, 1):
            if not os.path.exists(file_path):
                logger.warning(f"File not found, skipping: {file_path}")
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Determine base name
                if config.preserve_original_names:
                    base_name = os.path.splitext(os.path.basename(file_path))[0]
                else:
                    base_name = config.base_name_pattern.format(index=i)

                batch_item = BatchItem(
                    index=i,
                    original_text=content,
                    base_name=base_name,
                    source_file=file_path
                )

                batch_items.append(batch_item)

            except Exception as e:
                logger.error(f"Failed to read file {file_path}: {e}")

        logger.info(f"Created batch with {len(batch_items)} items from {len(file_paths)} files")
        return batch_items

    def create_batch_from_data(self,
                              transcription_data: List[Dict[str, Any]],
                              batch_config: Optional[BatchConfig] = None) -> List[BatchItem]:
        """
        Create batch items from structured data.

        Args:
            transcription_data: List of transcription dictionaries
            batch_config: Batch configuration

        Returns:
            List of BatchItem objects
        """
        config = batch_config or BatchConfig()
        batch_items = []

        for i, data in enumerate(transcription_data, 1):
            try:
                # Extract metadata if present
                metadata = None
                if 'metadata' in data:
                    metadata_dict = data['metadata']
                    metadata = CorrectionMetadata(
                        original_text=metadata_dict.get('original_text', ''),
                        corrected_text=metadata_dict.get('corrected_text', ''),
                        correction_applied=metadata_dict.get('correction_applied', False),
                        correction_level=metadata_dict.get('correction_level', 'standard'),
                        processing_time=metadata_dict.get('processing_time', {}),
                        chunks_processed=metadata_dict.get('chunks_processed', 0),
                        model_info=metadata_dict.get('model_info', {})
                    )

                base_name = data.get('base_name') or config.base_name_pattern.format(index=i)

                batch_item = BatchItem(
                    index=i,
                    original_text=data.get('original_text', ''),
                    corrected_text=data.get('corrected_text'),
                    base_name=base_name,
                    segments_data=data.get('segments'),
                    metadata=metadata
                )

                batch_items.append(batch_item)

            except Exception as e:
                logger.error(f"Failed to create batch item {i}: {e}")

        logger.info(f"Created batch with {len(batch_items)} items from structured data")
        return batch_items

    def process_batch(self,
                     batch_items: List[BatchItem],
                     batch_config: Optional[BatchConfig] = None,
                     batch_id: Optional[str] = None) -> BatchResult:
        """
        Process a batch of items with comprehensive tracking.

        Args:
            batch_items: List of batch items to process
            batch_config: Batch configuration
            batch_id: Optional batch ID (generated if None)

        Returns:
            BatchResult with processing details
        """
        config = batch_config or BatchConfig()
        batch_id = batch_id or self.generate_batch_id()
        start_time = datetime.now()

        logger.info(f"Starting batch processing: {batch_id} with {len(batch_items)} items")

        # Initialize batch result
        result = BatchResult(
            batch_id=batch_id,
            total_items=len(batch_items),
            successful_items=0,
            failed_items=0,
            output_files=[],
            failed_files=[],
            summary_file=None,
            processing_time_seconds=0.0,
            created_at=start_time.isoformat()
        )

        # Track active batch
        self.active_batches[batch_id] = result

        # Process items in chunks if necessary
        chunk_size = config.max_files_per_batch
        for chunk_start in range(0, len(batch_items), chunk_size):
            chunk_end = min(chunk_start + chunk_size, len(batch_items))
            chunk_items = batch_items[chunk_start:chunk_end]

            logger.info(f"Processing chunk {chunk_start//chunk_size + 1}: items {chunk_start+1}-{chunk_end}")

            for item in chunk_items:
                try:
                    # Determine output directory
                    output_dir = config.output_directory or self.file_keeper.output_dir

                    # Process the item
                    item_result = self.output_handler.process_transcription_output(
                        original_text=item.original_text,
                        corrected_text=item.corrected_text,
                        base_name=item.base_name or f"item_{item.index:03d}",
                        output_format=config.output_format,
                        segments_data=item.segments_data,
                        metadata=item.metadata,
                        output_dir=output_dir
                    )

                    # Collect output files
                    for key, value in item_result.items():
                        if isinstance(value, str) and os.path.exists(value):
                            result.output_files.append(value)
                        elif isinstance(value, FileOutputPair):
                            result.output_files.extend([value.original_path, value.corrected_path])

                    result.successful_items += 1
                    logger.debug(f"Successfully processed item {item.index}")

                except Exception as e:
                    logger.error(f"Failed to process item {item.index}: {e}")
                    result.failed_files.append({
                        "index": item.index,
                        "base_name": item.base_name or f"item_{item.index:03d}",
                        "error": str(e),
                        "source_file": item.source_file
                    })
                    result.failed_items += 1

        # Calculate processing time
        end_time = datetime.now()
        result.processing_time_seconds = (end_time - start_time).total_seconds()

        # Create summary file if requested
        if config.create_summary:
            result.summary_file = self._create_comprehensive_summary(result, config)

        # Cleanup if requested
        if config.cleanup_after_processing:
            self._cleanup_batch_temp_files(batch_id)

        logger.info(f"Batch {batch_id} completed: {result.successful_items}/{result.total_items} successful "
                   f"in {result.processing_time_seconds:.2f} seconds")

        return result

    def _create_comprehensive_summary(self,
                                    batch_result: BatchResult,
                                    batch_config: BatchConfig) -> str:
        """Create a comprehensive summary file for the batch."""
        summary_data = {
            "batch_info": {
                "batch_id": batch_result.batch_id,
                "created_at": batch_result.created_at,
                "processing_time_seconds": batch_result.processing_time_seconds,
                "output_format": batch_config.output_format.value,
                "output_directory": batch_config.output_directory or self.file_keeper.output_dir
            },
            "statistics": {
                "total_items": batch_result.total_items,
                "successful_items": batch_result.successful_items,
                "failed_items": batch_result.failed_items,
                "success_rate": (batch_result.successful_items / batch_result.total_items * 100) if batch_result.total_items > 0 else 0,
                "total_output_files": len(batch_result.output_files),
                "average_processing_time_per_item": batch_result.processing_time_seconds / batch_result.total_items if batch_result.total_items > 0 else 0
            },
            "output_files": batch_result.output_files,
            "failed_files": batch_result.failed_files,
            "configuration": {
                "base_name_pattern": batch_config.base_name_pattern,
                "preserve_original_names": batch_config.preserve_original_names,
                "add_timestamps": batch_config.add_timestamps,
                "cleanup_after_processing": batch_config.cleanup_after_processing,
                "max_files_per_batch": batch_config.max_files_per_batch
            }
        }

        # Add file size statistics
        total_size = 0
        file_stats = []
        for file_path in batch_result.output_files:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                total_size += size
                file_stats.append({
                    "file": file_path,
                    "size_bytes": size,
                    "size_mb": round(size / (1024 * 1024), 2)
                })

        summary_data["file_statistics"] = {
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "average_file_size_bytes": total_size / len(batch_result.output_files) if batch_result.output_files else 0,
            "files": file_stats
        }

        # Save summary
        summary_filename = f"batch_summary_{batch_result.batch_id}.json"
        summary_path = os.path.join(
            batch_config.output_directory or self.file_keeper.output_dir,
            summary_filename
        )

        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Comprehensive batch summary saved: {summary_path}")
        return summary_path

    def _cleanup_batch_temp_files(self, batch_id: str):
        """Clean up temporary files created during batch processing."""
        try:
            cleanup_result = self.file_keeper.cleanup_temp_files(batch_id)
            logger.info(f"Batch {batch_id} cleanup: {cleanup_result.get('message', 'Completed')}")
        except Exception as e:
            logger.error(f"Failed to cleanup batch {batch_id}: {e}")

    def monitor_batch_progress(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current progress information for an active batch.

        Args:
            batch_id: Batch identifier

        Returns:
            Progress information or None if batch not found
        """
        if batch_id not in self.active_batches:
            return None

        batch_result = self.active_batches[batch_id]
        progress = {
            "batch_id": batch_id,
            "total_items": batch_result.total_items,
            "completed_items": batch_result.successful_items + batch_result.failed_items,
            "successful_items": batch_result.successful_items,
            "failed_items": batch_result.failed_items,
            "progress_percentage": ((batch_result.successful_items + batch_result.failed_items) / batch_result.total_items * 100) if batch_result.total_items > 0 else 0,
            "output_files_count": len(batch_result.output_files),
            "is_complete": (batch_result.successful_items + batch_result.failed_items) >= batch_result.total_items
        }

        return progress

    def list_output_files(self,
                         output_directory: Optional[str] = None,
                         file_pattern: Optional[str] = None,
                         include_pairs: bool = True) -> Dict[str, List[str]]:
        """
        List output files in the specified directory.

        Args:
            output_directory: Directory to scan
            file_pattern: Glob pattern for file matching
            include_pairs: Whether to group original/corrected pairs

        Returns:
            Dictionary with categorized file listings
        """
        search_dir = output_directory or self.file_keeper.output_dir
        pattern = file_pattern or "*.*"

        files = glob.glob(os.path.join(search_dir, pattern))

        if not include_pairs:
            return {"all_files": sorted(files)}

        # Categorize files
        original_files = []
        corrected_files = []
        other_files = []
        pairs = []

        for file_path in files:
            filename = os.path.basename(file_path)

            if self.file_keeper.original_suffix in filename:
                original_files.append(file_path)
            elif self.file_keeper.corrected_suffix in filename:
                corrected_files.append(file_path)
            else:
                other_files.append(file_path)

        # Match pairs
        for original_file in original_files:
            original_base = os.path.basename(original_file).replace(self.file_keeper.original_suffix, '')

            # Look for corresponding corrected file
            for corrected_file in corrected_files:
                corrected_base = os.path.basename(corrected_file).replace(self.file_keeper.corrected_suffix, '')

                if original_base == corrected_base:
                    pairs.append({
                        "base_name": original_base,
                        "original_file": original_file,
                        "corrected_file": corrected_file
                    })
                    break

        return {
            "total_files": len(files),
            "original_files": sorted(original_files),
            "corrected_files": sorted(corrected_files),
            "other_files": sorted(other_files),
            "pairs": pairs,
            "unpaired_originals": [f for f in original_files if not any(p["original_file"] == f for p in pairs)],
            "unpaired_corrected": [f for f in corrected_files if not any(p["corrected_file"] == f for p in pairs)]
        }

    def organize_output_directory(self,
                                 output_directory: Optional[str] = None,
                                 create_subdirs: bool = True,
                                 group_by_date: bool = True) -> Dict[str, Any]:
        """
        Organize output files into a structured directory layout.

        Args:
            output_directory: Directory to organize
            create_subdirs: Whether to create subdirectories
            group_by_date: Whether to group by creation date

        Returns:
            Organization results
        """
        target_dir = output_directory or self.file_keeper.output_dir

        if not os.path.exists(target_dir):
            return {"error": "Output directory does not exist"}

        organization_result = {
            "organized_files": 0,
            "created_directories": [],
            "errors": []
        }

        try:
            file_listing = self.list_output_files(target_dir, include_pairs=True)

            if create_subdirs:
                # Create subdirectories
                subdirs = ["originals", "corrected", "pairs", "summaries", "other"]

                if group_by_date:
                    # Also create date-based subdirectories
                    today = datetime.now().strftime("%Y-%m-%d")
                    subdirs = [os.path.join(subdir, today) for subdir in subdirs]

                for subdir in subdirs:
                    subdir_path = os.path.join(target_dir, subdir)
                    os.makedirs(subdir_path, exist_ok=True)
                    organization_result["created_directories"].append(subdir_path)

                # Move files to appropriate subdirectories
                # This would require careful implementation to avoid breaking existing references
                logger.info(f"Created {len(organization_result['created_directories'])} subdirectories")

            return organization_result

        except Exception as e:
            logger.error(f"Error organizing output directory: {e}")
            return {"error": str(e)}


def create_batch_manager(config=None) -> BatchManager:
    """Factory function to create BatchManager instance."""
    return BatchManager(config)