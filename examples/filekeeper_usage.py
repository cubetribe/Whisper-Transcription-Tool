#!/usr/bin/env python3
"""
FileKeeper Usage Examples
Demonstrates how to use the FileKeeper system for dual file output management.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from whisper_transcription_tool.core.file_keeper import FileKeeper, CorrectionMetadata
from whisper_transcription_tool.core.output_handler import OutputHandler
from whisper_transcription_tool.core.batch_manager import BatchManager, BatchConfig, BatchItem
from whisper_transcription_tool.core.models import OutputFormat


def example_basic_dual_files():
    """Example 1: Basic dual file creation with original/corrected content."""
    print("=" * 60)
    print("Example 1: Basic Dual File Creation")
    print("=" * 60)

    # Initialize FileKeeper
    file_keeper = FileKeeper()

    # Sample transcription data
    original_text = "Hello, this is a test transcription with some errors. The speeker said something interesting."
    corrected_text = "Hello, this is a test transcription with some errors. The speaker said something interesting."

    base_name = "example_transcription"

    # Create metadata
    metadata = CorrectionMetadata(
        original_text=original_text,
        corrected_text=corrected_text,
        correction_applied=True,
        correction_level="standard",
        processing_time={"transcription_seconds": 45.2, "correction_seconds": 12.8},
        chunks_processed=3,
        model_info={"whisper_model": "large-v3", "correction_model": "GPT-4"}
    )

    # Save dual TXT files
    file_pair = file_keeper.save_dual_files(
        original_text, corrected_text, base_name,
        OutputFormat.TXT, metadata
    )

    print(f"Original file: {file_pair.original_path}")
    print(f"Corrected file: {file_pair.corrected_path}")
    print(f"Files exist: {file_keeper.validate_output_paths(file_pair)}")


def example_format_specific_output():
    """Example 2: Format-specific output handling."""
    print("\n" + "=" * 60)
    print("Example 2: Format-Specific Output Handling")
    print("=" * 60)

    output_handler = OutputHandler()

    # Sample data with segments for timing
    original_text = "This is the first segment. This is the second segment with more content."
    corrected_text = "This is the first segment. This is the second segment with more content."

    segments_data = [
        {"start": 0.0, "end": 2.5, "text": "This is the first segment."},
        {"start": 2.5, "end": 6.0, "text": " This is the second segment with more content."}
    ]

    metadata = CorrectionMetadata(
        original_text=original_text,
        corrected_text=corrected_text,
        correction_applied=False,
        processing_time={"transcription_seconds": 30.0, "correction_seconds": 0.0}
    )

    # Process SRT output (original timing preserved)
    srt_result = output_handler.process_transcription_output(
        original_text, corrected_text, "srt_example",
        OutputFormat.SRT, segments_data, metadata,
        srt_options={"max_chars": 30, "max_duration": 2.0, "linebreaks": True}
    )

    print("SRT Processing Results:")
    for key, value in srt_result.items():
        print(f"  {key}: {value}")

    # Process JSON output with extended metadata
    json_result = output_handler.process_transcription_output(
        original_text, corrected_text, "json_example",
        OutputFormat.JSON, segments_data, metadata
    )

    print("\nJSON Processing Results:")
    for key, value in json_result.items():
        print(f"  {key}: {value}")


def example_batch_processing():
    """Example 3: Batch processing multiple transcriptions."""
    print("\n" + "=" * 60)
    print("Example 3: Batch Processing")
    print("=" * 60)

    batch_manager = BatchManager()

    # Prepare batch data
    batch_data = [
        {
            "original_text": "First transcription with errors in speach.",
            "corrected_text": "First transcription with errors in speech.",
            "base_name": "transcript_001",
            "metadata": {
                "original_text": "First transcription with errors in speach.",
                "corrected_text": "First transcription with errors in speech.",
                "correction_applied": True,
                "correction_level": "standard",
                "processing_time": {"transcription_seconds": 15.0, "correction_seconds": 5.0},
                "chunks_processed": 1,
                "model_info": {"whisper_model": "large-v3", "correction_model": "GPT-4"}
            }
        },
        {
            "original_text": "Second transcription is alredy perfect.",
            "corrected_text": "Second transcription is already perfect.",
            "base_name": "transcript_002",
            "metadata": {
                "original_text": "Second transcription is alredy perfect.",
                "corrected_text": "Second transcription is already perfect.",
                "correction_applied": True,
                "correction_level": "standard",
                "processing_time": {"transcription_seconds": 20.0, "correction_seconds": 3.0},
                "chunks_processed": 1,
                "model_info": {"whisper_model": "large-v3", "correction_model": "GPT-4"}
            }
        },
        {
            "original_text": "Third transcription needs no corection.",
            "corrected_text": "Third transcription needs no correction.",
            "base_name": "transcript_003"
        }
    ]

    # Create batch configuration
    batch_config = BatchConfig(
        output_format=OutputFormat.TXT,
        preserve_original_names=True,
        add_timestamps=False,
        create_summary=True
    )

    # Create batch items
    batch_items = batch_manager.create_batch_from_data(batch_data, batch_config)

    # Process the batch
    batch_result = batch_manager.process_batch(batch_items, batch_config)

    print(f"Batch ID: {batch_result.batch_id}")
    print(f"Total items: {batch_result.total_items}")
    print(f"Successful: {batch_result.successful_items}")
    print(f"Failed: {batch_result.failed_items}")
    print(f"Processing time: {batch_result.processing_time_seconds:.2f} seconds")
    print(f"Output files: {len(batch_result.output_files)}")
    print(f"Summary file: {batch_result.summary_file}")


def example_file_organization():
    """Example 4: File organization and management."""
    print("\n" + "=" * 60)
    print("Example 4: File Organization")
    print("=" * 60)

    batch_manager = BatchManager()
    file_keeper = FileKeeper()

    # List output files
    file_listing = batch_manager.list_output_files(include_pairs=True)

    print("File Organization Results:")
    print(f"Total files: {file_listing.get('total_files', 0)}")
    print(f"Original files: {len(file_listing.get('original_files', []))}")
    print(f"Corrected files: {len(file_listing.get('corrected_files', []))}")
    print(f"Matched pairs: {len(file_listing.get('pairs', []))}")
    print(f"Unpaired originals: {len(file_listing.get('unpaired_originals', []))}")
    print(f"Unpaired corrected: {len(file_listing.get('unpaired_corrected', []))}")

    # Show some pairs
    pairs = file_listing.get('pairs', [])
    if pairs:
        print("\nSample file pairs:")
        for i, pair in enumerate(pairs[:3]):  # Show first 3 pairs
            print(f"  Pair {i+1}: {pair['base_name']}")
            print(f"    Original: {os.path.basename(pair['original_file'])}")
            print(f"    Corrected: {os.path.basename(pair['corrected_file'])}")


def example_format_conversion():
    """Example 5: Format conversion between different output types."""
    print("\n" + "=" * 60)
    print("Example 5: Format Conversion")
    print("=" * 60)

    output_handler = OutputHandler()
    file_keeper = FileKeeper()

    # Create a sample TXT file first
    sample_text = "This is a sample transcription for conversion testing. It has multiple sentences."
    txt_path = file_keeper.save_original_file(sample_text, "conversion_test", OutputFormat.TXT)

    print(f"Created sample TXT file: {txt_path}")

    # Convert TXT to different formats
    formats_to_test = [OutputFormat.SRT, OutputFormat.VTT, OutputFormat.JSON]

    for target_format in formats_to_test:
        try:
            conversion_result = output_handler.convert_between_formats(
                txt_path, target_format, f"converted_to_{target_format.value}"
            )
            print(f"Converted to {target_format.value}: {conversion_result['output_file']}")
        except Exception as e:
            print(f"Failed to convert to {target_format.value}: {e}")


def example_advanced_json_metadata():
    """Example 6: Advanced JSON metadata structure."""
    print("\n" + "=" * 60)
    print("Example 6: Advanced JSON Metadata")
    print("=" * 60)

    file_keeper = FileKeeper()

    # Create rich metadata
    metadata = CorrectionMetadata(
        original_text="Original transcription with speeling errors.",
        corrected_text="Original transcription with spelling errors.",
        correction_applied=True,
        correction_level="detailed",
        processing_time={
            "transcription_seconds": 67.5,
            "correction_seconds": 23.1,
            "total_seconds": 90.6
        },
        chunks_processed=5,
        model_info={
            "whisper_model": "large-v3-turbo",
            "whisper_version": "20231117",
            "correction_model": "GPT-4",
            "correction_provider": "OpenAI",
            "language_detected": "en",
            "confidence_score": 0.95
        }
    )

    # Create extended JSON with segments
    segments_data = [
        {
            "id": 0,
            "start": 0.0,
            "end": 3.5,
            "text": "Original transcription with",
            "confidence": 0.98
        },
        {
            "id": 1,
            "start": 3.5,
            "end": 6.0,
            "text": " speeling errors.",
            "confidence": 0.92
        }
    ]

    # Use the private method to create extended JSON structure
    extended_json = file_keeper._create_extended_json(
        metadata.original_text,
        metadata.corrected_text,
        segments_data,
        metadata
    )

    # Save the JSON
    json_path = file_keeper.save_original_file(
        json.dumps(extended_json, indent=2, ensure_ascii=False),
        "advanced_metadata_example",
        OutputFormat.JSON
    )

    print(f"Advanced JSON metadata saved: {json_path}")
    print("\nJSON structure preview:")
    print(json.dumps(extended_json, indent=2)[:500] + "..." if len(json.dumps(extended_json)) > 500 else json.dumps(extended_json, indent=2))


def main():
    """Run all examples."""
    print("FileKeeper System Usage Examples")
    print("================================")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    try:
        example_basic_dual_files()
        example_format_specific_output()
        example_batch_processing()
        example_file_organization()
        example_format_conversion()
        example_advanced_json_metadata()

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()