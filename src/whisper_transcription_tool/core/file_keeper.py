"""
FileKeeper - Output Strategy for Original/Corrected Files
Handles dual file output with format-specific processing and batch management.
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, asdict

from .exceptions import FileFormatError
from .logging_setup import get_logger
from .models import OutputFormat
from .config import load_config

logger = get_logger(__name__)


@dataclass
class FileOutputPair:
    """Represents a pair of original and corrected output files."""
    original_path: str
    corrected_path: str
    format: OutputFormat
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CorrectionMetadata:
    """Metadata for text correction operations."""
    original_text: str
    corrected_text: str
    correction_applied: bool
    correction_level: str = "standard"
    processing_time: Dict[str, float] = None
    chunks_processed: int = 0
    model_info: Dict[str, str] = None

    def __post_init__(self):
        if self.processing_time is None:
            self.processing_time = {"transcription_seconds": 0.0, "correction_seconds": 0.0}
        if self.model_info is None:
            self.model_info = {}


class FileKeeper:
    """
    FileKeeper manages dual file output strategy for original/corrected transcriptions.
    Implements Tasks 8.1-8.3: File naming, format handling, and batch management.
    """

    def __init__(self, config=None):
        """Initialize FileKeeper with configuration."""
        self.config = config or load_config()
        self.output_dir = self._get_output_dir()
        self.temp_dir = self._get_temp_dir()

        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

        # File naming configuration
        self.original_suffix = "_original"
        self.corrected_suffix = "_corrected"
        self.timestamp_format = "%Y%m%d_%H%M%S"

    def _get_output_dir(self) -> str:
        """Get configured output directory."""
        from .constants import DEFAULT_OUTPUT_DIR
        output_dir = self.config.get("output", {}).get("default_directory", DEFAULT_OUTPUT_DIR)
        return os.path.expanduser(output_dir)

    def _get_temp_dir(self) -> str:
        """Get configured temporary directory."""
        from .constants import DEFAULT_TEMP_DIR
        temp_dir = self.config.get("output", {}).get("temp_directory", DEFAULT_TEMP_DIR)
        return os.path.expanduser(temp_dir)

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename by removing or replacing invalid characters.

        Args:
            filename: Raw filename

        Returns:
            Sanitized filename safe for filesystem
        """
        # Remove or replace invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        sanitized = re.sub(r'\s+', '_', sanitized)  # Replace spaces with underscores
        sanitized = re.sub(r'_+', '_', sanitized)   # Remove multiple underscores
        sanitized = sanitized.strip('_')            # Remove leading/trailing underscores

        # Ensure it's not too long (max 200 chars for the base name)
        name, ext = os.path.splitext(sanitized)
        if len(name) > 200:
            name = name[:200]
            sanitized = name + ext

        return sanitized

    def generate_timestamp(self) -> str:
        """Generate timestamp string for file naming."""
        return datetime.now().strftime(self.timestamp_format)

    def generate_dual_filenames(self,
                               base_name: str,
                               format_ext: str,
                               output_dir: Optional[str] = None,
                               add_timestamp: bool = False) -> Tuple[str, str]:
        """
        Generate original and corrected file paths.

        Args:
            base_name: Base filename without extension
            format_ext: File extension (e.g., '.txt', '.srt')
            output_dir: Output directory (defaults to configured dir)
            add_timestamp: Whether to add timestamp suffix

        Returns:
            Tuple of (original_path, corrected_path)
        """
        if output_dir is None:
            output_dir = self.output_dir

        # Sanitize base name
        base_name = self.sanitize_filename(base_name)

        # Add timestamp if requested or if files exist
        timestamp_suffix = ""
        if add_timestamp:
            timestamp_suffix = f"_{self.generate_timestamp()}"

        # Generate paths
        original_name = f"{base_name}{self.original_suffix}{timestamp_suffix}{format_ext}"
        corrected_name = f"{base_name}{self.corrected_suffix}{timestamp_suffix}{format_ext}"

        original_path = os.path.join(output_dir, original_name)
        corrected_path = os.path.join(output_dir, corrected_name)

        # Check for conflicts and add timestamp if needed
        if not add_timestamp and (os.path.exists(original_path) or os.path.exists(corrected_path)):
            logger.info(f"File conflict detected for {base_name}, adding timestamp")
            return self.generate_dual_filenames(base_name, format_ext, output_dir, add_timestamp=True)

        return original_path, corrected_path

    def save_original_file(self,
                          content: str,
                          base_name: str,
                          output_format: Union[str, OutputFormat],
                          output_dir: Optional[str] = None) -> str:
        """
        Save original transcription content.

        Args:
            content: File content to save
            base_name: Base filename
            output_format: Output format
            output_dir: Output directory

        Returns:
            Path to saved original file
        """
        if isinstance(output_format, str):
            output_format = OutputFormat(output_format)

        format_ext = f".{output_format.value}"
        original_path, _ = self.generate_dual_filenames(base_name, format_ext, output_dir)

        with open(original_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Saved original file: {original_path}")
        return original_path

    def save_corrected_file(self,
                           content: str,
                           base_name: str,
                           output_format: Union[str, OutputFormat],
                           output_dir: Optional[str] = None) -> str:
        """
        Save corrected transcription content.

        Args:
            content: File content to save
            base_name: Base filename
            output_format: Output format
            output_dir: Output directory

        Returns:
            Path to saved corrected file
        """
        if isinstance(output_format, str):
            output_format = OutputFormat(output_format)

        format_ext = f".{output_format.value}"
        _, corrected_path = self.generate_dual_filenames(base_name, format_ext, output_dir)

        with open(corrected_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Saved corrected file: {corrected_path}")
        return corrected_path

    def save_dual_files(self,
                       original_content: str,
                       corrected_content: str,
                       base_name: str,
                       output_format: Union[str, OutputFormat],
                       metadata: Optional[CorrectionMetadata] = None,
                       output_dir: Optional[str] = None) -> FileOutputPair:
        """
        Save both original and corrected files.

        Args:
            original_content: Original content
            corrected_content: Corrected content
            base_name: Base filename
            output_format: Output format
            metadata: Correction metadata
            output_dir: Output directory

        Returns:
            FileOutputPair with saved file paths
        """
        if isinstance(output_format, str):
            output_format = OutputFormat(output_format)

        format_ext = f".{output_format.value}"
        original_path, corrected_path = self.generate_dual_filenames(base_name, format_ext, output_dir)

        # Save original file
        with open(original_path, 'w', encoding='utf-8') as f:
            f.write(original_content)

        # Save corrected file
        with open(corrected_path, 'w', encoding='utf-8') as f:
            f.write(corrected_content)

        logger.info(f"Saved dual files - Original: {original_path}, Corrected: {corrected_path}")

        return FileOutputPair(
            original_path=original_path,
            corrected_path=corrected_path,
            format=output_format,
            timestamp=self.generate_timestamp(),
            metadata=asdict(metadata) if metadata else None
        )

    def save_format_specific_output(self,
                                  original_content: str,
                                  corrected_content: str,
                                  base_name: str,
                                  output_format: Union[str, OutputFormat],
                                  segments_data: Optional[List[Dict]] = None,
                                  metadata: Optional[CorrectionMetadata] = None,
                                  output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle format-specific output saving.

        Args:
            original_content: Original transcription content
            corrected_content: Corrected transcription content
            base_name: Base filename
            output_format: Target format
            segments_data: Original segments for timing preservation
            metadata: Correction metadata
            output_dir: Output directory

        Returns:
            Dict with saved file information
        """
        if isinstance(output_format, str):
            output_format = OutputFormat(output_format)

        results = {}

        if output_format == OutputFormat.TXT:
            # TXT: Save both original and corrected versions
            file_pair = self.save_dual_files(
                original_content, corrected_content, base_name,
                output_format, metadata, output_dir
            )
            results['txt_files'] = file_pair

        elif output_format in [OutputFormat.SRT, OutputFormat.VTT]:
            # SRT/VTT: Original timing + corrected text in separate TXT
            original_path = self.save_original_file(
                original_content, base_name, output_format, output_dir
            )

            # Save corrected version as TXT
            corrected_txt_path = self.save_corrected_file(
                corrected_content, base_name, OutputFormat.TXT, output_dir
            )

            results['timed_original'] = original_path
            results['corrected_txt'] = corrected_txt_path

        elif output_format == OutputFormat.JSON:
            # JSON: Extended with correction metadata
            extended_json = self._create_extended_json(
                original_content, corrected_content, segments_data, metadata
            )

            json_path = self.save_original_file(
                json.dumps(extended_json, indent=2, ensure_ascii=False),
                base_name, output_format, output_dir
            )

            results['json_file'] = json_path

        return results

    def _create_extended_json(self,
                             original_text: str,
                             corrected_text: str,
                             segments_data: Optional[List[Dict]] = None,
                             metadata: Optional[CorrectionMetadata] = None) -> Dict[str, Any]:
        """
        Create extended JSON format with correction metadata.

        Args:
            original_text: Original transcription
            corrected_text: Corrected transcription
            segments_data: Original segments
            metadata: Correction metadata

        Returns:
            Extended JSON structure
        """
        json_data = {
            "transcription": {
                "original_text": original_text,
                "corrected_text": corrected_text,
                "correction_applied": corrected_text != original_text,
                "correction_level": metadata.correction_level if metadata else "standard",
                "processing_time": metadata.processing_time if metadata else {},
                "chunks_processed": metadata.chunks_processed if metadata else 0,
                "model_info": metadata.model_info if metadata else {}
            }
        }

        # Add segments if available
        if segments_data:
            json_data["segments"] = segments_data

        # Add timestamp
        json_data["created_at"] = datetime.now().isoformat()

        return json_data

    def process_batch_files(self,
                           file_pairs: List[Tuple[str, str, str]],  # (original, corrected, base_name)
                           output_format: Union[str, OutputFormat],
                           output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Process multiple file pairs for batch operations.

        Args:
            file_pairs: List of (original_content, corrected_content, base_name) tuples
            output_format: Output format
            output_dir: Output directory

        Returns:
            Batch processing results
        """
        if isinstance(output_format, str):
            output_format = OutputFormat(output_format)

        results = {
            "total_files": len(file_pairs),
            "processed_files": [],
            "failed_files": [],
            "summary": {}
        }

        for i, (original_content, corrected_content, base_name) in enumerate(file_pairs, 1):
            try:
                # Use numbered base names for batch
                batch_base_name = f"{base_name}{i}"

                file_result = self.save_format_specific_output(
                    original_content, corrected_content, batch_base_name,
                    output_format, output_dir=output_dir
                )

                results["processed_files"].append({
                    "base_name": batch_base_name,
                    "files": file_result
                })

            except Exception as e:
                logger.error(f"Failed to process batch file {i}: {e}")
                results["failed_files"].append({
                    "index": i,
                    "base_name": base_name,
                    "error": str(e)
                })

        # Generate batch summary
        results["summary"] = {
            "successful": len(results["processed_files"]),
            "failed": len(results["failed_files"]),
            "success_rate": len(results["processed_files"]) / len(file_pairs) * 100
        }

        # Create batch summary file
        self._create_batch_summary(results, output_format, output_dir)

        logger.info(f"Batch processing complete: {results['summary']['successful']}/{results['total_files']} successful")
        return results

    def _create_batch_summary(self,
                             batch_results: Dict[str, Any],
                             output_format: Union[str, OutputFormat],
                             output_dir: Optional[str] = None) -> str:
        """
        Create a summary file for batch processing results.

        Args:
            batch_results: Batch processing results
            output_format: Output format used
            output_dir: Output directory

        Returns:
            Path to summary file
        """
        if output_dir is None:
            output_dir = self.output_dir

        timestamp = self.generate_timestamp()
        summary_name = f"batch_summary_{timestamp}.json"
        summary_path = os.path.join(output_dir, summary_name)

        summary_data = {
            "batch_info": {
                "timestamp": timestamp,
                "format": output_format.value if isinstance(output_format, OutputFormat) else output_format,
                "output_directory": output_dir
            },
            "results": batch_results
        }

        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Batch summary saved: {summary_path}")
        return summary_path

    def cleanup_temp_files(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Clean up temporary files after processing.

        Args:
            session_id: Optional session ID for targeted cleanup

        Returns:
            Cleanup results
        """
        from .file_manager import FileManager

        file_manager = FileManager(self.config)

        if session_id:
            return file_manager.cleanup_after_transcription(session_id)
        else:
            return file_manager.cleanup_temp_directory()

    def validate_output_paths(self, file_pair: FileOutputPair) -> Dict[str, bool]:
        """
        Validate that output files exist and are accessible.

        Args:
            file_pair: FileOutputPair to validate

        Returns:
            Validation results
        """
        results = {
            "original_exists": os.path.exists(file_pair.original_path),
            "corrected_exists": os.path.exists(file_pair.corrected_path),
            "original_readable": False,
            "corrected_readable": False
        }

        # Test readability
        try:
            if results["original_exists"]:
                with open(file_pair.original_path, 'r', encoding='utf-8') as f:
                    f.read(1)  # Test read access
                results["original_readable"] = True
        except Exception as e:
            logger.warning(f"Original file not readable: {e}")

        try:
            if results["corrected_exists"]:
                with open(file_pair.corrected_path, 'r', encoding='utf-8') as f:
                    f.read(1)  # Test read access
                results["corrected_readable"] = True
        except Exception as e:
            logger.warning(f"Corrected file not readable: {e}")

        return results


def create_file_keeper(config=None) -> FileKeeper:
    """Factory function to create FileKeeper instance."""
    return FileKeeper(config)