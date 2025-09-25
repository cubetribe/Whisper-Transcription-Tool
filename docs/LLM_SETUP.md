# LLM Setup Guide

This guide covers the installation and setup of Local Large Language Model (LLM) dependencies for the Whisper Transcription Tool's text correction features.

## Quick Start

For most users on macOS with Apple Silicon:

```bash
# Install all LLM dependencies
pip install -e ".[llm]"

# Setup NLTK data
python -c "import nltk; nltk.download('punkt')"

# Download recommended LeoLM model
python -m src.whisper_transcription_tool.core.llm_model_manager setup
```

## Dependencies Overview

The LLM text correction feature requires the following dependencies:

### Core Dependencies

1. **llama-cpp-python** (≥0.2.0)
   - Python bindings for llama.cpp
   - Enables local LLM inference
   - Supports Metal acceleration on Apple Silicon

2. **sentencepiece** (≥0.1.99)
   - Required for LeoLM tokenization
   - Handles German text tokenization

3. **nltk** (≥3.8)
   - Fallback tokenization library
   - Requires data downloads

4. **transformers** (≥4.21.0)
   - Hugging Face library for model utilities
   - Configuration and helper functions

## Platform-Specific Installation

### macOS (Apple Silicon - M1/M2/M3)

**Recommended - Metal Acceleration:**
```bash
# Install llama-cpp-python with Metal support
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python>=0.2.0

# Install other dependencies
pip install sentencepiece>=0.1.99 nltk>=3.8 transformers>=4.21.0

# Or install all at once
pip install -e ".[llm]"
```

**Alternative - CPU Only:**
```bash
pip install llama-cpp-python>=0.2.0  # No CMAKE_ARGS
```

### macOS (Intel)

```bash
# CPU-only installation
pip install llama-cpp-python>=0.2.0
pip install sentencepiece>=0.1.99 nltk>=3.8 transformers>=4.21.0
```

### Linux

**With CUDA (NVIDIA GPU):**
```bash
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python>=0.2.0
pip install sentencepiece>=0.1.99 nltk>=3.8 transformers>=4.21.0
```

**CPU Only:**
```bash
pip install llama-cpp-python>=0.2.0
pip install sentencepiece>=0.1.99 nltk>=3.8 transformers>=4.21.0
```

### Windows

**With CUDA:**
```cmd
set CMAKE_ARGS=-DLLAMA_CUBLAS=on
pip install llama-cpp-python>=0.2.0
pip install sentencepiece>=0.1.99 nltk>=3.8 transformers>=4.21.0
```

**CPU Only:**
```cmd
pip install llama-cpp-python>=0.2.0
pip install sentencepiece>=0.1.99 nltk>=3.8 transformers>=4.21.0
```

## NLTK Data Setup

After installing NLTK, you need to download required datasets:

```bash
python -c "import nltk; nltk.download('punkt')"
```

Or use the interactive downloader:
```bash
python -m nltk.downloader
```

Required datasets:
- `punkt` - Punkt Tokenizer Models

## LeoLM Model Setup

### Automatic Setup (Recommended)

```bash
# Download and setup the recommended LeoLM model
python -m src.whisper_transcription_tool.core.llm_model_manager setup
```

This will:
1. Download the recommended LeoLM 13B Chat Q4_0 model (~7.5GB)
2. Verify the download
3. Set up the model for use

### Manual Model Management

**List available models:**
```bash
python -m src.whisper_transcription_tool.core.llm_model_manager list
```

**Download specific model:**
```bash
python -m src.whisper_transcription_tool.core.llm_model_manager download leolm-13b-chat-q4_0
```

**List downloaded models:**
```bash
python -m src.whisper_transcription_tool.core.llm_model_manager list --downloaded
```

**Remove a model:**
```bash
python -m src.whisper_transcription_tool.core.llm_model_manager remove leolm-13b-chat-q4_0
```

### Available Models

| Model | Size | Quality | Speed | Recommended |
|-------|------|---------|--------|-------------|
| LeoLM 13B Q2_K | ~5.1GB | Lower | Fastest | No |
| LeoLM 13B Q4_0 | ~7.5GB | Good | Fast | **Yes** |
| LeoLM 13B Q5_K_M | ~9.2GB | Higher | Slower | No |

## Dependency Validation

### Automatic Validation

The application automatically validates dependencies on startup. To manually check:

```bash
# Check all LLM dependencies
python -m src.whisper_transcription_tool.core.dependency_checker

# Show detailed status
python -m src.whisper_transcription_tool.core.dependency_checker --status

# Require all dependencies (exit with error if missing)
python -m src.whisper_transcription_tool.core.dependency_checker --require-all
```

### Programmatic Validation

```python
from whisper_transcription_tool.core.dependency_checker import validate_startup_dependencies

# Graceful validation (allows missing dependencies)
success = validate_startup_dependencies(require_all=False)

# Strict validation (requires all dependencies)
success = validate_startup_dependencies(require_all=True)
```

## Storage Requirements

### Disk Space

- **Dependencies**: ~500MB
- **NLTK Data**: ~50MB
- **LeoLM Models**:
  - Q2_K: ~5.1GB
  - Q4_0: ~7.5GB (recommended)
  - Q5_K_M: ~9.2GB

**Total**: ~8-10GB for full setup

### Model Storage Location

Models are stored in: `{project_root}/models/llm/`

You can change this by setting the `LLM_MODELS_PATH` environment variable:
```bash
export LLM_MODELS_PATH="/path/to/your/models"
```

## Performance Considerations

### Hardware Requirements

**Minimum:**
- 8GB RAM
- 10GB free disk space
- Any modern CPU

**Recommended:**
- 16GB+ RAM
- Apple Silicon Mac (M1/M2/M3) for Metal acceleration
- Or NVIDIA GPU with CUDA support on Linux/Windows

### Performance Tips

1. **Use Metal acceleration on macOS**: Significantly faster inference
2. **Choose appropriate quantization**: Q4_0 balances speed and quality
3. **Ensure sufficient RAM**: Model runs entirely in memory
4. **Close other applications**: Free up system resources

## Troubleshooting

### Common Issues

#### 1. llama-cpp-python Installation Fails

**Problem**: CMAKE errors during installation

**Solutions:**
```bash
# Update build tools
pip install --upgrade pip setuptools wheel

# macOS: Install Xcode command line tools
xcode-select --install

# Try installing without Metal support
pip install llama-cpp-python  # CPU-only fallback
```

#### 2. Metal Support Not Working

**Problem**: No GPU acceleration on Apple Silicon

**Solutions:**
```bash
# Reinstall with explicit Metal flags
pip uninstall llama-cpp-python
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --no-cache-dir
```

#### 3. NLTK Data Missing

**Problem**: "Resource punkt not found" error

**Solution:**
```bash
python -c "import nltk; nltk.download('punkt', quiet=False)"
```

#### 4. Model Download Fails

**Problem**: Network errors or incomplete downloads

**Solutions:**
```bash
# Retry with force flag
python -m src.whisper_transcription_tool.core.llm_model_manager download leolm-13b-chat-q4_0 --force

# Check internet connection and disk space
df -h  # Check disk space
ping huggingface.co  # Check connectivity
```

#### 5. Out of Memory During Inference

**Problem**: System runs out of RAM

**Solutions:**
1. Use a smaller quantized model (Q2_K instead of Q4_0)
2. Close other applications
3. Increase swap/virtual memory
4. Use a machine with more RAM

### Getting Help

1. **Check dependency status**: Run the dependency checker
2. **Verify model integrity**: Use the model verification command
3. **Check logs**: Look for detailed error messages in application logs
4. **Check system resources**: Ensure sufficient RAM and disk space

### Environment Debugging

```bash
# Check Python environment
python --version
pip --version

# Check installed packages
pip list | grep -E "(llama|sentence|nltk|transform)"

# Check available disk space
df -h

# Check system memory
free -h  # Linux
vm_stat  # macOS

# Test llama-cpp-python installation
python -c "import llama_cpp; print('llama-cpp-python works!')"
```

## Integration with Whisper Tool

Once dependencies are installed, LLM features will be automatically available in the web interface:

1. Start the web server: `bash start_server.sh`
2. Navigate to http://localhost:8090
3. Look for text correction options in transcription results
4. Configure LLM settings in the configuration panel

## Security Considerations

- **Local Processing**: All LLM inference happens locally, no data sent to external services
- **Model Storage**: Models are stored locally and not shared
- **Network Access**: Only required for initial model downloads

## Performance Benchmarks

Approximate inference times on M1 MacBook Pro (16GB):

| Model | Input Length | Processing Time |
|-------|--------------|-----------------|
| Q2_K  | 100 words    | ~2 seconds      |
| Q4_0  | 100 words    | ~3 seconds      |
| Q5_K_M| 100 words    | ~4 seconds      |

Times scale roughly linearly with input length.