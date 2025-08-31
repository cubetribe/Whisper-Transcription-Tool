---
inclusion: always
---

# Architecture & Code Structure Rules

## Import Patterns (Strictly Enforced)

### Core Module Imports
```python
# Always use absolute imports for core functionality
from whisper_transcription_tool.core import config, models, exceptions
from whisper_transcription_tool.core.logging_setup import setup_logging

# Never import core modules relatively
```

### Module-Internal Imports
```python
# Within modules, use relative imports
from .whisper_wrapper import WhisperWrapper
from .output_formatter import OutputFormatter

# Cross-module imports use absolute paths
from whisper_transcription_tool.module1_transcribe import WhisperWrapper
```

## Directory Structure (Fixed Locations)

```
src/whisper_transcription_tool/
├── core/                    # Shared functionality (config, logging, exceptions)
├── module1_transcribe/      # Audio transcription logic
├── module2_extract/         # Video-to-audio extraction
├── module3_phone/          # Live recording and phone calls
├── module4_chatbot/        # Optional semantic search
├── web/                    # FastAPI web interface
└── main.py                 # CLI entry point

transcriptions/             # Output files
├── temp/                   # Temporary files (auto-cleanup)
└── *.txt, *.srt, *.vtt    # Final transcription outputs

models/                     # Whisper model files
deps/whisper.cpp/          # External Whisper.cpp dependency
```

## Code Style (Non-Negotiable)

### Naming Conventions
- **Files**: `snake_case.py`
- **Classes**: `PascalCase` (e.g., `WhisperWrapper`, `AudioProcessor`)
- **Functions/Variables**: `snake_case` (e.g., `process_audio`, `file_path`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_MODEL_PATH`)

### Type Hints (Required)
```python
from typing import Optional, List, Dict, Union
from pathlib import Path

def process_file(input_path: Path, output_dir: Optional[Path] = None) -> Dict[str, str]:
    """Always include type hints and docstrings."""
    pass
```

### Error Handling Pattern
```python
from whisper_transcription_tool.core.exceptions import TranscriptionError, ModelNotFoundError

# Always use custom exceptions with descriptive messages
raise TranscriptionError(f"Failed to process {file_path}: {error_details}")
```

## Architecture Patterns

### Configuration Management
```python
# Always use the centralized config system
from whisper_transcription_tool.core import config

# Priority order: CLI args → --config file → ~/.whisper_tool.json → defaults
settings = config.load_config(config_path=args.config)
```

### Progress Tracking
```python
# CLI: Always use tqdm
from tqdm import tqdm
for item in tqdm(items, desc="Processing files"):
    process_item(item)

# Web: Use WebSocket updates
await websocket.send_json({"progress": 50, "status": "processing"})
```

### Resource Management
```python
# Always use context managers
with open(file_path, 'r') as f:
    content = f.read()

# For external processes
with subprocess.Popen([...]) as proc:
    output = proc.communicate()
```

## Module Communication

### Event System Usage
```python
from whisper_transcription_tool.core.events import EventBus

# Publish events for cross-module communication
EventBus.publish("transcription_started", {"file": file_path})
EventBus.subscribe("transcription_completed", callback_function)
```

### Async/Sync Boundaries
- **Web interface**: Use `async/await` throughout
- **CLI operations**: Synchronous unless explicitly needed
- **File I/O**: Synchronous (use `pathlib.Path`)
- **External processes**: Synchronous with `subprocess`

## Entry Point Rules

### CLI Execution
```bash
# Always use module execution (never direct script calls)
python -m src.whisper_transcription_tool.main transcribe file.mp3

# Never use
python src/whisper_transcription_tool/main.py
```

### File Path Handling
```python
from pathlib import Path

# Always use Path objects for file operations
input_path = Path(args.input_file).resolve()
output_dir = Path("transcriptions")
```