---
inclusion: always
---

# Technology Stack & Development Guidelines

## Core Technology Stack

**Runtime**: Python 3.11+ (required for modern type hints and performance)
**Transcription**: Whisper.cpp (Apple Silicon optimized, local processing only)
**Media Processing**: FFmpeg (video-to-audio extraction, format conversion)
**Web Framework**: FastAPI + Uvicorn + WebSockets (real-time progress updates)

## Critical Dependencies

### Always Required
- `numpy` - Numerical operations for audio processing
- `tqdm` - CLI progress bars (use consistently across all modules)
- `pyyaml` - Configuration parsing (prefer YAML over JSON)
- `psutil` - System resource monitoring (check before large operations)

### Web Interface
- `fastapi>=0.116.0` + `uvicorn>=0.35.0` - Web server stack
- `jinja2>=3.1.0` - Template rendering
- `websockets>=15.0.0` - Real-time progress updates
- `python-multipart` - File upload handling

### Audio Processing
- `srt>=3.5.0` - Subtitle format generation
- `sounddevice>=0.4.6` - Live audio recording (module3_phone)

## Development Environment Setup

### Virtual Environment (Required)
```bash
# Always use venv_new/ (primary), fallback to venv/
python3 -m venv venv_new
source venv_new/bin/activate
pip install -e ".[web]"  # Editable install with web extras
```

### Binary Dependencies (macOS)
```bash
# FFmpeg (required for video processing)
brew install ffmpeg

# BlackHole (optional, for live recording)
brew install --cask blackhole-2ch

# Ensure Whisper binary is executable
chmod +x deps/whisper.cpp/build/bin/whisper-cli
```

## Command Patterns

### Application Entry Point
**Always use**: `python -m src.whisper_transcription_tool.main [command]`
**Never use**: Direct script execution or relative imports

### Standard Commands
- `transcribe <file>` - Process audio/video files
- `extract <video>` - Extract audio from video
- `phone` - Live phone call recording/transcription
- `web --port 8090` - Start web interface

### Development Commands
```bash
# Code quality (run before commits)
black src/ && isort src/ && mypy src/

# Testing
pytest

# Package installation
pip install -e ".[full]"  # All features
```

## Configuration Management

### File Locations (Priority Order)
1. Command-line `--config` parameter
2. User config: `~/.whisper_tool.json`
3. System config: `~/.config/whisper_tool/config.json`
4. Default config in `core/config.py`

### Format Requirements
- Use JSON for user configs (better error messages)
- Use YAML for complex configurations
- Always validate config with `core/config.py` functions
- Support dynamic path resolution for cross-platform compatibility

## Performance Guidelines

### Apple Silicon Optimization
- Leverage Metal Performance Shaders when available
- Use Whisper.cpp compiled with Apple Silicon optimizations
- Monitor memory usage with `psutil` before large operations

### Resource Management
- Always use context managers for file operations
- Clean up temporary files in `transcriptions/temp/`
- Check available disk space before processing
- Implement graceful degradation for resource constraints