# FileKeeper System Documentation

## Overview

The FileKeeper system is a comprehensive file management solution for the Whisper Transcription Tool that implements dual file output strategy for original and corrected transcriptions. It provides consistent file naming, format-specific handling, and batch processing capabilities.

## Architecture

The FileKeeper system consists of four main components:

### 1. FileKeeper (`core/file_keeper.py`)
- **Primary Class**: `FileKeeper`
- **Purpose**: Core file management with dual output strategy
- **Key Features**:
  - Dual file naming (original/corrected pairs)
  - Path sanitization and validation
  - Timestamp-based conflict resolution
  - Format-agnostic file operations

### 2. OutputHandler (`core/output_handler.py`)
- **Primary Class**: `OutputHandler`
- **Purpose**: Format-specific processing and output generation
- **Key Features**:
  - TXT: Both original and corrected versions
  - SRT/VTT: Original timing preserved, corrected text as separate TXT
  - JSON: Extended metadata structure
  - Format conversion utilities

### 3. BatchManager (`core/batch_manager.py`)
- **Primary Class**: `BatchManager`
- **Purpose**: Advanced batch processing and file organization
- **Key Features**:
  - Batch processing with progress tracking
  - File organization and directory management
  - Comprehensive batch summaries
  - Configurable processing options

### 4. Data Models
- **FileOutputPair**: Represents original/corrected file pairs
- **CorrectionMetadata**: Metadata for correction operations
- **BatchConfig**: Configuration for batch operations
- **BatchItem**: Individual batch processing items
- **BatchResult**: Results of batch processing

## File Naming Convention

### Standard Naming Pattern
```
Original: filename_original.txt
Corrected: filename_corrected.txt
```

### With Timestamps (for conflicts)
```
Original: filename_original_20240831_143022.txt
Corrected: filename_corrected_20240831_143022.txt
```

### Batch Processing
```
Batch item 1: meeting1_original.txt, meeting1_corrected.txt
Batch item 2: meeting2_original.txt, meeting2_corrected.txt
```

## Format-Specific Handling

### TXT Format
- **Output**: Both original and corrected files
- **Use Case**: Plain text transcriptions
- **Example**:
  ```
  meeting_original.txt
  meeting_corrected.txt
  ```

### SRT Format
- **Original**: SRT file with original timing
- **Corrected**: Corrected text as separate TXT file
- **Rationale**: Preserves timing accuracy while providing corrected content
- **Example**:
  ```
  meeting_original.srt  (with timing)
  meeting_corrected.txt (corrected text only)
  ```

### VTT Format
- **Original**: VTT file with original timing
- **Corrected**: Corrected text as separate TXT file
- **Similar to SRT**: Timing preservation approach
- **Example**:
  ```
  meeting_original.vtt
  meeting_corrected.txt
  ```

### JSON Format
- **Output**: Extended JSON with correction metadata
- **Structure**: Comprehensive metadata including processing times, models used
- **Example Structure**:
  ```json
  {
    "transcription": {
      "original_text": "...",
      "corrected_text": "...",
      "correction_applied": true,
      "correction_level": "standard",
      "processing_time": {
        "transcription_seconds": 45.2,
        "correction_seconds": 67.8
      },
      "chunks_processed": 5,
      "model_info": {
        "whisper_model": "large-v3",
        "correction_model": "GPT-4"
      }
    },
    "created_at": "2024-08-31T14:30:22",
    "segments": [...],
    "statistics": {...}
  }
  ```

## Usage Examples

### Basic Usage

```python
from whisper_transcription_tool.core.file_keeper import FileKeeper
from whisper_transcription_tool.core.models import OutputFormat

# Initialize FileKeeper
file_keeper = FileKeeper()

# Save dual files
original_text = "Original transcription with errors"
corrected_text = "Original transcription with corrections"

file_pair = file_keeper.save_dual_files(
    original_text, corrected_text, "my_transcription",
    OutputFormat.TXT
)

print(f"Original: {file_pair.original_path}")
print(f"Corrected: {file_pair.corrected_path}")
```

### Format-Specific Processing

```python
from whisper_transcription_tool.core.output_handler import OutputHandler
from whisper_transcription_tool.core.file_keeper import CorrectionMetadata

output_handler = OutputHandler()

# Create metadata
metadata = CorrectionMetadata(
    original_text="original",
    corrected_text="corrected",
    correction_applied=True,
    processing_time={"transcription_seconds": 30.0, "correction_seconds": 5.0}
)

# Process SRT with timing
result = output_handler.process_transcription_output(
    original_text, corrected_text, "example",
    OutputFormat.SRT, segments_data, metadata,
    srt_options={"max_chars": 30, "max_duration": 2.0}
)
```

### Batch Processing

```python
from whisper_transcription_tool.core.batch_manager import BatchManager, BatchConfig

batch_manager = BatchManager()

# Configure batch
config = BatchConfig(
    output_format=OutputFormat.TXT,
    preserve_original_names=True,
    create_summary=True
)

# Prepare batch data
batch_data = [
    {
        "original_text": "First transcription",
        "corrected_text": "First corrected transcription",
        "base_name": "transcript_001"
    },
    # ... more items
]

# Process batch
batch_items = batch_manager.create_batch_from_data(batch_data, config)
result = batch_manager.process_batch(batch_items, config)

print(f"Processed {result.successful_items}/{result.total_items} items")
```

## Configuration

The FileKeeper system uses the existing whisper tool configuration system. Key configuration options:

```json
{
  "output": {
    "default_directory": "/path/to/transcriptions",
    "temp_directory": "/path/to/temp"
  },
  "disk_management": {
    "enable_auto_cleanup": true,
    "min_required_space_gb": 2.0
  }
}
```

## Integration with Existing System

### Integration Points

1. **Module 1 (Transcription)**:
   - Replace existing output formatter calls
   - Use OutputHandler for dual file generation

2. **Web Interface**:
   - Update routes to handle dual file responses
   - Provide file pair download options

3. **CLI Interface**:
   - Add options for correction processing
   - Support batch mode operations

### Migration Path

1. **Phase 1**: Implement FileKeeper alongside existing system
2. **Phase 2**: Update transcription modules to use FileKeeper
3. **Phase 3**: Replace old output formatter completely
4. **Phase 4**: Add web UI support for dual files

## API Reference

### FileKeeper Class

#### Methods

##### `save_dual_files(original_content, corrected_content, base_name, output_format, metadata=None, output_dir=None)`
Save both original and corrected files.

**Parameters**:
- `original_content` (str): Original transcription content
- `corrected_content` (str): Corrected transcription content
- `base_name` (str): Base filename without extension
- `output_format` (OutputFormat): Target format
- `metadata` (CorrectionMetadata, optional): Correction metadata
- `output_dir` (str, optional): Output directory

**Returns**: `FileOutputPair` object

##### `generate_dual_filenames(base_name, format_ext, output_dir=None, add_timestamp=False)`
Generate original and corrected file paths.

**Returns**: Tuple of (original_path, corrected_path)

##### `sanitize_filename(filename)`
Sanitize filename for filesystem compatibility.

**Returns**: Sanitized filename string

### OutputHandler Class

#### Methods

##### `process_transcription_output(original_text, corrected_text, base_name, output_format, segments_data=None, metadata=None, output_dir=None, srt_options=None)`
Process transcription output with format-specific handling.

**Returns**: Dictionary with processing results and file paths

##### `convert_between_formats(input_file, target_format, base_name=None, output_dir=None)`
Convert existing file to different format.

**Returns**: Conversion results dictionary

### BatchManager Class

#### Methods

##### `process_batch(batch_items, batch_config=None, batch_id=None)`
Process a batch of items with comprehensive tracking.

**Returns**: `BatchResult` object

##### `list_output_files(output_directory=None, file_pattern=None, include_pairs=True)`
List and categorize output files.

**Returns**: Dictionary with file categorization

## Error Handling

The FileKeeper system includes comprehensive error handling:

1. **File Conflicts**: Automatic timestamp addition
2. **Invalid Characters**: Filename sanitization
3. **Missing Directories**: Automatic directory creation
4. **Batch Failures**: Individual item error tracking
5. **Format Errors**: Detailed error reporting

## Performance Considerations

1. **File I/O**: Efficient file operations with proper error handling
2. **Memory Usage**: Streaming for large files where possible
3. **Batch Processing**: Chunked processing for large batches
4. **Cleanup**: Automatic temporary file cleanup

## Testing

The system includes comprehensive test coverage:

- Unit tests for core functionality
- Integration tests for format handling
- Batch processing tests
- Error condition tests

Run tests with:
```bash
pytest tests/test_file_keeper.py
pytest tests/test_output_handler.py
pytest tests/test_batch_manager.py
```

## Troubleshooting

### Common Issues

1. **File Conflicts**: System automatically adds timestamps
2. **Permission Errors**: Check directory write permissions
3. **Format Errors**: Verify input format compatibility
4. **Batch Failures**: Check individual item error details in results

### Debug Mode

Enable detailed logging:
```python
import logging
logging.getLogger('whisper_transcription_tool.core').setLevel(logging.DEBUG)
```

## Future Enhancements

1. **Cloud Storage**: Support for S3, Google Drive integration
2. **Compression**: Automatic compression for large files
3. **Versioning**: File versioning support
4. **Templates**: Custom filename templates
5. **Metadata Search**: Search files by metadata
6. **Diff Generation**: Visual diffs between original/corrected

## Contributing

When contributing to the FileKeeper system:

1. Follow existing code patterns
2. Add comprehensive tests
3. Update documentation
4. Consider backward compatibility
5. Test with real-world data

## License

Part of the Whisper Transcription Tool project. See main project license.