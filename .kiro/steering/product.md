---
inclusion: always
---

# Product Guidelines & User Experience Rules

## Core Product Principles (Non-Negotiable)

**Privacy-First**: All transcription happens locally using Whisper.cpp - NEVER send audio to external APIs or cloud services
**Apple Silicon Optimized**: Leverage M1/M2/M3/M4 performance for fast local processing
**Modular Design**: Each module operates independently - transcribe, extract, phone, chatbot
**Real-Time Feedback**: Always provide progress updates and clear status indicators

## Command Interface Standards

### CLI Commands (Primary Interface)
```bash
# Standard command patterns
python -m src.whisper_transcription_tool.main transcribe <file> [options]
python -m src.whisper_transcription_tool.main extract <video> [options]
python -m src.whisper_transcription_tool.main phone [options]
python -m src.whisper_transcription_tool.main web --port 8090
```

### Required CLI Behaviors
- **Progress bars**: Always use `tqdm` for long operations
- **Batch processing**: Support `--batch` flag for multiple files
- **Relative paths**: Display file paths relative to current directory
- **Time/size info**: Show processing time and file size in output
- **Clear status**: Explicit success/failure indicators with next steps

### Web Interface (Secondary)
- **Port**: Default 8090, configurable via `--port`
- **Real-time updates**: WebSocket progress for all operations
- **File handling**: Drag-and-drop support with clear upload status
- **Download links**: Direct access to completed transcriptions

## File Processing Rules

### Supported Input Formats
- **Audio**: `.mp3`, `.wav`, `.m4a`, `.flac` (process directly)
- **Video**: `.mp4`, `.mov`, `.avi` (extract audio first via FFmpeg)
- **Phone recordings**: Dual-track support for speaker separation

### Output File Structure
```
transcriptions/
├── original_filename.txt        # Plain text transcription
├── original_filename.srt        # Subtitle format
├── original_filename.vtt        # WebVTT format
└── temp/                        # Temporary files (auto-cleanup)
    ├── extracted_audio.wav
    └── processing_chunks/
```

### File Naming Conventions
- Preserve original filename with new extension
- Add timestamp suffix for duplicate names: `file_20240831_143022.txt`
- Use sanitized filenames (remove special characters)

## Model Management Strategy

### Model Selection Logic
- **Default**: `ggml-tiny.bin` (speed priority)
- **High accuracy**: `ggml-large-v3-turbo.bin` (quality priority)
- **Auto-download**: Download missing models to `models/` directory
- **Language detection**: Auto-detect or use `--language` parameter

### Performance Targets (Apple Silicon)
- **Tiny model**: 2-3x real-time speed
- **Large model**: 0.5-1x real-time speed
- **Memory usage**: Monitor and warn at 80% system memory
- **Disk space**: Check available space before processing

## Error Handling Standards

### Graceful Degradation
- Continue batch processing even if individual files fail
- Log failed files and continue with successful ones
- Provide summary of successes/failures at completion

### Error Message Format
```
ERROR: Failed to transcribe 'audio.mp3'
Reason: Model file not found at models/ggml-tiny.bin
Solution: Run 'python -m src.whisper_transcription_tool.main download-model tiny'
```

### Resource Monitoring
- Check disk space before processing (require 2x file size free)
- Monitor memory usage during processing
- Clean up temporary files on failure or completion

## User Interface Language

### Consistent Terminology
- **"Transcribing"**: Converting audio to text
- **"Extracting"**: Getting audio from video
- **"Processing"**: General operation in progress
- **"Completed"**: Successful operation
- **"Failed"**: Operation error with explanation

### Progress Indicators
```python
# CLI progress format
"Transcribing audio.mp3: 45% |████████████     | 2.3MB/5.1MB [00:32<00:18, 150kB/s]"

# Web progress format
{"progress": 45, "status": "transcribing", "file": "audio.mp3", "eta": "00:18"}
```

## Integration Requirements

### External Dependencies
- **FFmpeg**: Required for video processing (check availability on startup)
- **Whisper.cpp**: Core engine (must be compiled for target platform)
- **BlackHole**: Optional for live recording (graceful fallback if missing)

### Optional Features
- **ChromaDB**: Semantic search for chatbot module
- **Gradio**: Alternative web interface (if FastAPI unavailable)

## Quality Assurance Rules

### Before Processing
1. Validate input file exists and is readable
2. Check model availability (download if missing)
3. Verify sufficient disk space and memory
4. Test external dependencies (FFmpeg, Whisper binary)

### During Processing
1. Provide real-time progress updates
2. Monitor resource usage
3. Handle interruptions gracefully (Ctrl+C)
4. Log all operations for debugging

### After Processing
1. Verify output file integrity
2. Clean up temporary files
3. Display processing summary with file locations
4. Suggest next steps or related commands