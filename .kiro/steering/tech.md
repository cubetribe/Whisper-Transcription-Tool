---
inclusion: always
---

# Technology Stack & Development Guidelines

## Core Technology Stack
- **Python 3.11+** with modern type hints
- **Whisper.cpp** for Apple Silicon optimized local transcription
- **FFmpeg** for video-to-audio extraction
- **FastAPI + Uvicorn** for web interface with WebSocket progress

## Critical Dependencies & Versions
```python
# Core requirements (always install)
numpy>=1.24.0, tqdm>=4.65.0, pyyaml>=6.0, psutil>=5.9.0
fastapi>=0.116.0, uvicorn>=0.35.0, websockets>=15.0.0
srt>=3.5.0, sounddevice>=0.4.6
```

## Command Execution Rules
**ALWAYS use module execution**: `python -m src.whisper_transcription_tool.main [command]`
**NEVER use direct script calls**: `python main.py` or relative imports

Standard commands: `transcribe`, `extract`, `phone`, `web --port 8090`

## Environment Setup (macOS)
```bash
# Required setup sequence
python3 -m venv venv_new && source venv_new/bin/activate
pip install -e ".[web]"
brew install ffmpeg  # Required dependency
chmod +x deps/whisper.cpp/build/bin/whisper-cli
```

## Configuration Priority Order
1. CLI `--config` parameter
2. `~/.whisper_tool.json` (user config)
3. `~/.config/whisper_tool/config.json` (system)
4. `core/config.py` defaults

Use JSON for user configs, YAML for complex configurations. Always validate via `core/config.py`.

## Performance & Resource Management
- **Apple Silicon**: Leverage Metal Performance Shaders and optimized Whisper.cpp builds
- **Memory**: Monitor with `psutil` before large operations, implement graceful degradation
- **Files**: Always use context managers, auto-clean `transcriptions/temp/`
- **Disk**: Check available space before processing (require 2x file size free)

## Code Quality Standards
```bash
# Pre-commit requirements
black src/ && isort src/ && mypy src/
pytest  # Run tests
```

## Type Hints & Error Handling
```python
from typing import Optional, List, Dict, Path
from whisper_transcription_tool.core.exceptions import TranscriptionError

def process_file(input_path: Path, output_dir: Optional[Path] = None) -> Dict[str, str]:
    """Always include type hints and docstrings"""
    try:
        # Implementation
    except Exception as e:
        raise TranscriptionError(f"Failed to process {input_path}: {e}")
```