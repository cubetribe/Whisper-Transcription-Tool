"""
Output Handler - Format-specific processing for FileKeeper
Extends output_formatter.py with dual file handling and correction support.
"""

import os
import json
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime

from .exceptions import FileFormatError
from .logging_setup import get_logger
from .models import OutputFormat
from .file_keeper import FileKeeper, CorrectionMetadata, FileOutputPair
from ..module1_transcribe.output_formatter import (
    convert_format, srt_to_text, vtt_to_text, json_to_text,
    text_to_srt, text_to_vtt, text_to_json, segments_to_srt,
    format_text_with_max_chars, split_into_sentences
)

logger = get_logger(__name__)


class OutputHandler:
    """
    Enhanced output handler for dual file (original/corrected) processing.
    Integrates with FileKeeper for consistent file management.
    """

    def __init__(self, config=None):
        """Initialize with FileKeeper integration."""
        self.file_keeper = FileKeeper(config)
        self.config = config

    def process_transcription_output(self,
                                   original_text: str,
                                   corrected_text: Optional[str],
                                   base_name: str,
                                   output_format: Union[str, OutputFormat],
                                   segments_data: Optional[List[Dict]] = None,
                                   metadata: Optional[CorrectionMetadata] = None,
                                   output_dir: Optional[str] = None,
                                   srt_options: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process transcription output with dual file handling.

        Args:
            original_text: Original transcription text
            corrected_text: Corrected text (None if no correction applied)
            base_name: Base filename
            output_format: Target output format
            segments_data: Original segments with timing info
            metadata: Correction metadata
            output_dir: Output directory
            srt_options: SRT formatting options (max_chars, max_duration, linebreaks)

        Returns:
            Dict with processing results and file paths
        """
        if isinstance(output_format, str):
            output_format = OutputFormat(output_format)

        # Use original text as corrected if no correction was applied
        final_corrected = corrected_text if corrected_text is not None else original_text
        correction_applied = corrected_text is not None and corrected_text != original_text

        logger.info(f"Processing {output_format.value} output - correction applied: {correction_applied}")

        if output_format == OutputFormat.TXT:
            return self._process_txt_output(
                original_text, final_corrected, base_name, metadata, output_dir
            )

        elif output_format == OutputFormat.SRT:
            return self._process_srt_output(
                original_text, final_corrected, base_name, segments_data,
                metadata, output_dir, srt_options
            )

        elif output_format == OutputFormat.VTT:
            return self._process_vtt_output(
                original_text, final_corrected, base_name, segments_data,
                metadata, output_dir
            )

        elif output_format == OutputFormat.JSON:
            return self._process_json_output(
                original_text, final_corrected, base_name, segments_data,
                metadata, output_dir
            )

        else:
            raise FileFormatError(f"Unsupported output format: {output_format}")

    def _process_txt_output(self,
                           original_text: str,
                           corrected_text: str,
                           base_name: str,
                           metadata: Optional[CorrectionMetadata],
                           output_dir: Optional[str]) -> Dict[str, Any]:
        """Process TXT format output with dual files."""
        file_pair = self.file_keeper.save_dual_files(
            original_text, corrected_text, base_name,
            OutputFormat.TXT, metadata, output_dir
        )

        return {
            "format": "txt",
            "original_file": file_pair.original_path,
            "corrected_file": file_pair.corrected_path,
            "file_pair": file_pair,
            "correction_applied": corrected_text != original_text
        }

    def _process_srt_output(self,
                           original_text: str,
                           corrected_text: str,
                           base_name: str,
                           segments_data: Optional[List[Dict]],
                           metadata: Optional[CorrectionMetadata],
                           output_dir: Optional[str],
                           srt_options: Optional[Dict]) -> Dict[str, Any]:
        """Process SRT format output - original timing + corrected TXT."""
        srt_opts = srt_options or {}
        max_chars = srt_opts.get('max_chars', 20)
        max_duration = srt_opts.get('max_duration', 1.0)
        linebreaks = srt_opts.get('linebreaks', True)

        # Generate SRT content
        if segments_data:
            # Use segments with original timing
            original_srt = segments_to_srt(segments_data, max_chars, max_duration, linebreaks)

            # Create corrected segments by replacing text but keeping timing
            corrected_segments = []
            for seg in segments_data:
                corrected_seg = seg.copy()
                # This is a simplified approach - in practice, you might want more sophisticated
                # text alignment between original and corrected versions
                corrected_seg['text'] = corrected_text[
                    int(len(corrected_text) * (seg.get('start', 0) / segments_data[-1].get('end', 1))
                    ):int(len(corrected_text) * (seg.get('end', 0) / segments_data[-1].get('end', 1)))
                ] if segments_data else corrected_text
                corrected_segments.append(corrected_seg)

            corrected_srt = segments_to_srt(corrected_segments, max_chars, max_duration, linebreaks)
        else:
            # Generate SRT from plain text
            original_srt = text_to_srt(original_text, max_chars, max_duration, linebreaks)
            corrected_srt = text_to_srt(corrected_text, max_chars, max_duration, linebreaks)

        # Save original SRT with timing
        original_path = self.file_keeper.save_original_file(
            original_srt, base_name, OutputFormat.SRT, output_dir
        )

        # Save corrected version as both SRT and TXT
        corrected_srt_path = self.file_keeper.save_corrected_file(
            corrected_srt, base_name, OutputFormat.SRT, output_dir
        )

        corrected_txt_path = self.file_keeper.save_corrected_file(
            corrected_text, base_name, OutputFormat.TXT, output_dir
        )

        return {
            "format": "srt",
            "original_srt": original_path,
            "corrected_srt": corrected_srt_path,
            "corrected_txt": corrected_txt_path,
            "timing_preserved": segments_data is not None,
            "correction_applied": corrected_text != original_text
        }

    def _process_vtt_output(self,
                           original_text: str,
                           corrected_text: str,
                           base_name: str,
                           segments_data: Optional[List[Dict]],
                           metadata: Optional[CorrectionMetadata],
                           output_dir: Optional[str]) -> Dict[str, Any]:
        """Process VTT format output - original timing + corrected TXT."""
        # Convert to VTT format
        original_vtt = text_to_vtt(original_text)

        # For VTT, we keep original timing and provide corrected text separately
        original_path = self.file_keeper.save_original_file(
            original_vtt, base_name, OutputFormat.VTT, output_dir
        )

        corrected_txt_path = self.file_keeper.save_corrected_file(
            corrected_text, base_name, OutputFormat.TXT, output_dir
        )

        return {
            "format": "vtt",
            "original_vtt": original_path,
            "corrected_txt": corrected_txt_path,
            "correction_applied": corrected_text != original_text
        }

    def _process_json_output(self,
                            original_text: str,
                            corrected_text: str,
                            base_name: str,
                            segments_data: Optional[List[Dict]],
                            metadata: Optional[CorrectionMetadata],
                            output_dir: Optional[str]) -> Dict[str, Any]:
        """Process JSON format with extended correction metadata."""
        # Create extended JSON structure
        json_data = {
            "transcription": {
                "original_text": original_text,
                "corrected_text": corrected_text,
                "correction_applied": corrected_text != original_text,
                "correction_level": metadata.correction_level if metadata else "none",
                "processing_time": metadata.processing_time if metadata else {
                    "transcription_seconds": 0.0,
                    "correction_seconds": 0.0
                },
                "chunks_processed": metadata.chunks_processed if metadata else 0,
                "model_info": metadata.model_info if metadata else {}
            },
            "created_at": datetime.now().isoformat(),
            "format_version": "1.0"
        }

        # Add segments if available
        if segments_data:
            json_data["segments"] = segments_data

        # Add text statistics
        json_data["statistics"] = {
            "original_length": len(original_text),
            "corrected_length": len(corrected_text),
            "length_difference": len(corrected_text) - len(original_text),
            "original_words": len(original_text.split()),
            "corrected_words": len(corrected_text.split())
        }

        json_content = json.dumps(json_data, indent=2, ensure_ascii=False)

        json_path = self.file_keeper.save_original_file(
            json_content, base_name, OutputFormat.JSON, output_dir
        )

        return {
            "format": "json",
            "json_file": json_path,
            "metadata_included": metadata is not None,
            "segments_included": segments_data is not None,
            "correction_applied": corrected_text != original_text
        }

    def process_batch_transcriptions(self,
                                   transcriptions: List[Dict[str, Any]],
                                   output_format: Union[str, OutputFormat],
                                   base_name_prefix: str = "batch_item",
                                   output_dir: Optional[str] = None,
                                   srt_options: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process multiple transcriptions in batch mode.

        Args:
            transcriptions: List of transcription dicts with 'original_text', 'corrected_text', etc.
            output_format: Target output format
            base_name_prefix: Prefix for generated filenames
            output_dir: Output directory
            srt_options: SRT formatting options

        Returns:
            Batch processing results
        """
        if isinstance(output_format, str):
            output_format = OutputFormat(output_format)

        results = {
            "batch_info": {
                "total_items": len(transcriptions),
                "format": output_format.value,
                "timestamp": datetime.now().isoformat(),
                "output_directory": output_dir or self.file_keeper.output_dir
            },
            "processed_items": [],
            "failed_items": [],
            "summary_file": None
        }

        for i, transcription in enumerate(transcriptions, 1):
            try:
                base_name = f"{base_name_prefix}_{i:03d}"

                # Extract transcription data
                original_text = transcription.get('original_text', '')
                corrected_text = transcription.get('corrected_text')
                segments_data = transcription.get('segments')

                # Create metadata if available
                metadata = None
                if 'metadata' in transcription:
                    metadata = CorrectionMetadata(**transcription['metadata'])

                # Process the transcription
                item_result = self.process_transcription_output(
                    original_text, corrected_text, base_name, output_format,
                    segments_data, metadata, output_dir, srt_options
                )

                results["processed_items"].append({
                    "index": i,
                    "base_name": base_name,
                    "result": item_result
                })

                logger.info(f"Processed batch item {i}/{len(transcriptions)}: {base_name}")

            except Exception as e:
                logger.error(f"Failed to process batch item {i}: {e}")
                results["failed_items"].append({
                    "index": i,
                    "base_name": f"{base_name_prefix}_{i:03d}",
                    "error": str(e)
                })

        # Generate summary statistics
        results["summary"] = {
            "successful_items": len(results["processed_items"]),
            "failed_items": len(results["failed_items"]),
            "success_rate": (len(results["processed_items"]) / len(transcriptions)) * 100,
            "total_files_created": sum(
                len([v for v in item["result"].values() if isinstance(v, str) and os.path.exists(v)])
                for item in results["processed_items"]
            )
        }

        # Create batch summary file
        results["summary_file"] = self._create_batch_summary_file(results, output_dir)

        logger.info(f"Batch processing complete: {results['summary']['successful_items']}/{len(transcriptions)} successful")
        return results

    def _create_batch_summary_file(self,
                                  batch_results: Dict[str, Any],
                                  output_dir: Optional[str]) -> str:
        """Create a comprehensive batch summary file."""
        if output_dir is None:
            output_dir = self.file_keeper.output_dir

        timestamp = self.file_keeper.generate_timestamp()
        summary_filename = f"batch_processing_summary_{timestamp}.json"
        summary_path = os.path.join(output_dir, summary_filename)

        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(batch_results, f, indent=2, ensure_ascii=False)

        logger.info(f"Batch summary saved: {summary_path}")
        return summary_path

    def convert_between_formats(self,
                               input_file: str,
                               target_format: Union[str, OutputFormat],
                               base_name: Optional[str] = None,
                               output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert existing file to different format with dual output support.

        Args:
            input_file: Path to input file
            target_format: Target output format
            base_name: Base name for output (derived from input if None)
            output_dir: Output directory

        Returns:
            Conversion results
        """
        if not os.path.exists(input_file):
            raise FileFormatError(f"Input file not found: {input_file}")

        if isinstance(target_format, str):
            target_format = OutputFormat(target_format)

        # Determine source format from extension
        input_ext = os.path.splitext(input_file)[1].lower().lstrip('.')
        try:
            source_format = OutputFormat(input_ext)
        except ValueError:
            raise FileFormatError(f"Unsupported input format: {input_ext}")

        # Generate base name if not provided
        if base_name is None:
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            # Remove existing suffixes
            base_name = base_name.replace(self.file_keeper.original_suffix, '')
            base_name = base_name.replace(self.file_keeper.corrected_suffix, '')

        # Read input file
        with open(input_file, 'r', encoding='utf-8') as f:
            input_content = f.read()

        # Convert format
        converted_content = convert_format(input_content, source_format, target_format)

        # Save converted file (as original since no correction is involved)
        output_path = self.file_keeper.save_original_file(
            converted_content, base_name, target_format, output_dir
        )

        return {
            "source_file": input_file,
            "source_format": source_format.value,
            "target_format": target_format.value,
            "output_file": output_path,
            "base_name": base_name,
            "conversion_successful": True
        }


def create_output_handler(config=None) -> OutputHandler:
    """Factory function to create OutputHandler instance."""
    return OutputHandler(config)