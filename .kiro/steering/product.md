---
inclusion: always
---

# WhisperLocal Product Guidelines

## Core Principles

- **Privacy-First**: All transcription happens locally using Whisper.cpp - NEVER suggest external APIs or cloud services
- **Apple Silicon Optimized**: Always leverage native M1/M2/M3/M4 performance optimizations
- **Modular Design**: Maintain separation between modules (transcribe, extract, phone, chatbot)
- **Real-Time Feedback**: Implement progress tracking for all operations >5 seconds

## Command Execution Rules

### CLI Entry Point (Required)
```bash
python -m src.whisper_transcription_tool.main <command> <file> [options]
```

**Available Commands**: `transcribe`, `extract`, `phone`, `web --port 8090`

### Implementation Requirements
- Always use `tqdm` for progress bars in CLI operations
- Display file paths relative to current working directory
- Include processing time and file size in completion messages
- Provide actionable next steps in success/failure messages
- Support `--batch` flag for processing multiple files

## File Processing Standards

### Supported Input Formats
- **Audio** (direct processing): `.mp3`, `.wav`, `.m4a`, `.flac`
- **Video** (extract audio first): `.mp4`, `.mov`, `.avi`

### Output Directory Structure
```
transcriptions/
├── filename.txt    # Plain text transcription
├── filename.srt    # SRT subtitle format
├── filename.vtt    # WebVTT format
└── temp/          # Temporary files (auto-cleanup)
```

### File Naming Convention
- Preserve original filename stem with appropriate extension
- Add timestamp suffix for duplicates: `filename_20240831_143022.txt`
- Sanitize special characters and spaces in output filenames
- Always use absolute paths internally, display relative paths to user

## Model Management

### Model Selection Strategy
- **Default**: `ggml-tiny.bin` (optimized for speed, good quality)
- **High Accuracy**: `ggml-large-v3-turbo.bin` (best quality, slower)
- **Location**: Store all models in `models/` directory
- **Auto-download**: Implement automatic model download for missing files
- **Language**: Auto-detect language or respect `--language` parameter

### Performance Benchmarks (Apple Silicon)
- **Tiny model**: 2-3x real-time processing speed
- **Large model**: 0.5-1x real-time processing speed
- **Memory monitoring**: Warn users at 80% system memory usage
- **Disk space**: Require 2x input file size free space before processing

## Error Handling Patterns

### Batch Processing Resilience
- Continue processing remaining files when individual files fail
- Log all failures with specific error details
- Provide completion summary showing success/failure counts
- Never abort entire batch due to single file failure

### Error Message Structure
```
ERROR: Failed to transcribe 'audio.mp3'
Reason: Model file not found at models/ggml-tiny.bin
Solution: Run 'python -m src.whisper_transcription_tool.main download-model tiny'
```

### Pre-Processing Validation
- Verify input file exists and is readable
- Check model availability (trigger auto-download if missing)
- Validate sufficient disk space (2x file size minimum)
- Monitor available memory before large operations
- Test FFmpeg availability for video processing

### Cleanup and Interruption Handling
- Always clean up temporary files in `transcriptions/temp/`
- Handle Ctrl+C gracefully with partial cleanup
- Preserve partial results when possible

## User Interface Standards

### Consistent Terminology
- **"Transcribing"**: Converting audio to text
- **"Extracting"**: Converting video to audio
- **"Processing"**: General operation in progress
- **"Completed"**: Successful operation with file location
- **"Failed"**: Operation error with specific reason and solution

### Progress Display Format
```python
# CLI: "Transcribing audio.mp3: 45% |████████████     | 2.3MB/5.1MB [00:32<00:18, 150kB/s]"
# Web: {"progress": 45, "status": "transcribing", "file": "audio.mp3", "eta": "00:18"}
```

## Critical Dependencies

### Required (Must Validate)
- **FFmpeg**: Video-to-audio conversion (check with `ffmpeg -version`)
- **Whisper.cpp**: Core transcription engine (verify binary exists and is executable)

### Optional (Graceful Fallback)
- **BlackHole**: Live audio recording (fallback to system default)
- **ChromaDB**: Semantic search for chatbot module

## Implementation Checklist

### Pre-Processing Phase
- [ ] Validate input file exists and is readable
- [ ] Check required models are available (auto-download if missing)
- [ ] Verify sufficient disk space (2x file size minimum)
- [ ] Test dependency availability (FFmpeg, Whisper.cpp)

### Processing Phase
- [ ] Display real-time progress with `tqdm` or WebSocket updates
- [ ] Monitor system resources (memory, disk)
- [ ] Handle interruptions gracefully (Ctrl+C, process termination)

### Post-Processing Phase
- [ ] Verify output file integrity and completeness
- [ ] Clean up all temporary files in `transcriptions/temp/`
- [ ] Display summary with file locations and processing statistics