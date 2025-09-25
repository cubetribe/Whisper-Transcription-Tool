# LLM Dependencies Troubleshooting Guide

This guide provides solutions to common issues when setting up and using LLM dependencies for text correction in the Whisper Transcription Tool.

## Quick Diagnostic Commands

Run these commands to quickly identify issues:

```bash
# Check all LLM dependencies
python -m src.whisper_transcription_tool.core.dependency_checker --status

# Test individual components
python -c "import llama_cpp; print('✓ llama-cpp-python works')"
python -c "import sentencepiece; print('✓ sentencepiece works')"
python -c "import nltk; print('✓ nltk works')"
python -c "import transformers; print('✓ transformers works')"

# Check NLTK data
python -c "import nltk; nltk.data.find('tokenizers/punkt')"

# List downloaded models
python -m src.whisper_transcription_tool.core.llm_model_manager list --downloaded
```

## Installation Issues

### 1. llama-cpp-python Compilation Errors

#### Symptoms
```
ERROR: Failed building wheel for llama-cpp-python
error: Microsoft Visual C++ 14.0 is required
clang: error: no such file or directory
```

#### Solutions

**macOS:**
```bash
# Install Xcode command line tools
xcode-select --install

# Update build tools
pip install --upgrade pip setuptools wheel cmake

# Retry installation with verbose output
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --verbose
```

**Linux:**
```bash
# Install build essentials
sudo apt-get update
sudo apt-get install build-essential cmake

# Or on CentOS/RHEL
sudo yum groupinstall "Development Tools"
sudo yum install cmake

# Retry installation
pip install llama-cpp-python
```

**Windows:**
```cmd
# Install Visual Studio Build Tools
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/

# Or install via chocolatey
choco install visualstudio2022buildtools

# Retry installation
pip install llama-cpp-python
```

### 2. Metal Support Not Detected

#### Symptoms
```
Metal device not found
Using CPU for inference (slow)
```

#### Solutions

**Check Metal Support:**
```bash
# Verify Metal is available
python -c "import llama_cpp; print(llama_cpp.llama_supports_mlock())"

# Check system info
system_profiler SPDisplaysDataType | grep Metal
```

**Reinstall with Metal:**
```bash
# Remove existing installation
pip uninstall llama-cpp-python

# Clean pip cache
pip cache purge

# Reinstall with explicit Metal support
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --no-cache-dir --verbose
```

### 3. NLTK Installation Issues

#### Symptoms
```
LookupError: Resource punkt not found
NLTK data not available
```

#### Solutions

**Download NLTK Data:**
```bash
# Direct download
python -c "import nltk; nltk.download('punkt')"

# Alternative download location
python -c "import nltk; nltk.download('punkt', download_dir='~/nltk_data')"

# Manual download if automated fails
mkdir -p ~/nltk_data/tokenizers
cd ~/nltk_data/tokenizers
wget https://github.com/nltk/nltk_data/raw/gh-pages/packages/tokenizers/punkt.zip
unzip punkt.zip
```

**Set NLTK Data Path:**
```bash
export NLTK_DATA=~/nltk_data
```

### 4. SentencePiece Issues

#### Symptoms
```
ImportError: No module named sentencepiece
Segmentation fault when loading tokenizer
```

#### Solutions

**Reinstall SentencePiece:**
```bash
pip uninstall sentencepiece
pip install sentencepiece>=0.1.99

# If issues persist, try building from source
pip install sentencepiece --no-binary sentencepiece
```

## Runtime Issues

### 1. Out of Memory Errors

#### Symptoms
```
RuntimeError: [Errno 12] Cannot allocate memory
Model loading failed: insufficient memory
```

#### Solutions

**Reduce Model Size:**
```bash
# Switch to smaller quantized model
python -m src.whisper_transcription_tool.core.llm_model_manager download leolm-13b-chat-q2_k

# Remove larger models to free space
python -m src.whisper_transcription_tool.core.llm_model_manager remove leolm-13b-chat-q5_k_m
```

**System Memory Management:**
```bash
# Check available memory
free -h  # Linux
vm_stat  # macOS
wmic OS get TotalVisibleMemorySize /value  # Windows

# Increase swap space (Linux)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

**Application Settings:**
```python
# Reduce model context window
llm_config = {
    'n_ctx': 1024,  # Reduce from default 2048
    'n_batch': 64   # Reduce batch size
}
```

### 2. Model Loading Failures

#### Symptoms
```
FileNotFoundError: Model file not found
Model verification failed
Corrupted model file
```

#### Solutions

**Re-download Models:**
```bash
# Force re-download with verification
python -m src.whisper_transcription_tool.core.llm_model_manager download leolm-13b-chat-q4_0 --force

# Verify model integrity
python -m src.whisper_transcription_tool.core.llm_model_manager verify leolm-13b-chat-q4_0
```

**Check File Permissions:**
```bash
# Fix permissions
chmod 644 models/llm/*.gguf

# Check disk space
df -h
```

### 3. Slow Inference Performance

#### Symptoms
- Text correction takes very long
- High CPU usage
- System becomes unresponsive

#### Solutions

**Optimize Configuration:**
```python
# Reduce context window
llm_config = {
    'n_ctx': 512,        # Smaller context
    'n_threads': 4,      # Limit CPU threads
    'n_gpu_layers': 35   # Use GPU layers (if available)
}
```

**Use Faster Model:**
```bash
# Switch to Q2_K quantization (faster, lower quality)
python -m src.whisper_transcription_tool.core.llm_model_manager download leolm-13b-chat-q2_k
```

**System Optimization:**
```bash
# Close other applications
# Ensure sufficient RAM available
# Use SSD storage for models
```

## Platform-Specific Issues

### macOS

#### Issue: "cannot be opened because the developer cannot be verified"
**Solution:**
```bash
sudo spctl --master-disable  # Disable Gatekeeper temporarily
# Then re-enable after installation
sudo spctl --master-enable
```

#### Issue: Rosetta translation on Apple Silicon
**Solution:**
```bash
# Ensure using native Python
which python
# Should show /opt/homebrew/bin/python or similar

# Reinstall with correct architecture
arch -arm64 pip install llama-cpp-python
```

### Linux

#### Issue: GLIBC version compatibility
**Solution:**
```bash
# Check GLIBC version
ldd --version

# Use older Python version if needed
pyenv install 3.11.7
pyenv local 3.11.7

# Or build from source
pip install llama-cpp-python --no-binary llama-cpp-python
```

#### Issue: CUDA not found
**Solution:**
```bash
# Install CUDA development kit
sudo apt install nvidia-cuda-toolkit

# Set environment variables
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH

# Reinstall with CUDA support
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python --force-reinstall
```

### Windows

#### Issue: Visual C++ redistributable missing
**Solution:**
```cmd
# Install Visual C++ Redistributable
# Download from Microsoft website
# Or use chocolatey
choco install vcredist2022
```

#### Issue: Long path support
**Solution:**
```cmd
# Enable long path support
reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled /t REG_DWORD /d 1

# Or use shorter paths
set LLM_MODELS_PATH=C:\models
```

## Network and Download Issues

### 1. Model Download Failures

#### Symptoms
```
ConnectionError: Failed to download model
Timeout during model download
Incomplete download
```

#### Solutions

**Network Configuration:**
```bash
# Check connectivity
ping huggingface.co
curl -I https://huggingface.co/mradermacher/LeoLM-hesseianai-13b-chat-GGUF

# Configure proxy if needed
export https_proxy=http://proxy.company.com:8080
pip install --proxy http://proxy.company.com:8080 llama-cpp-python
```

**Retry with Different Settings:**
```bash
# Increase timeout
pip install --timeout 300 llama-cpp-python

# Use different index
pip install -i https://pypi.python.org/simple/ llama-cpp-python
```

**Manual Download:**
```bash
# Download manually using wget or curl
curl -L -o models/llm/leolm-hesseianai-13b-chat-q4_0.gguf \
  "https://huggingface.co/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/resolve/main/LeoLM-hesseianai-13b-chat.Q4_0.gguf"
```

## Environment and Dependency Conflicts

### 1. Package Version Conflicts

#### Symptoms
```
VersionConflict: transformers 4.20.0 but transformers>=4.21.0 is required
```

#### Solutions

**Create Clean Environment:**
```bash
# Create new virtual environment
python -m venv venv_llm
source venv_llm/bin/activate  # or venv_llm\Scripts\activate on Windows

# Install only required packages
pip install -e ".[llm]"
```

**Resolve Conflicts:**
```bash
# Check conflicting packages
pip check

# Force specific versions
pip install transformers==4.21.0 --force-reinstall
```

### 2. Python Version Issues

#### Symptoms
```
Python 3.8 is not supported
Requires Python >=3.9
```

#### Solutions

**Upgrade Python:**
```bash
# Using pyenv
pyenv install 3.11.7
pyenv global 3.11.7

# Using conda
conda create -n llm_env python=3.11
conda activate llm_env
```

## Performance Monitoring and Optimization

### 1. Memory Usage Monitoring

```bash
# Monitor memory during model loading
top -p $(pgrep -f whisper)

# Python memory profiling
pip install memory-profiler
python -m memory_profiler your_script.py
```

### 2. CPU/GPU Utilization

```bash
# Monitor CPU usage
htop

# Monitor GPU usage (macOS)
sudo powermetrics -n 1 -s gpu_power

# Monitor GPU usage (Linux with NVIDIA)
nvidia-smi
```

## Logging and Debugging

### Enable Detailed Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable llama-cpp-python verbose logging
import llama_cpp
llama_cpp.llama_log_set_verbosity(2)
```

### Debug Configuration

```python
# Debug model loading
from whisper_transcription_tool.core.dependency_checker import DependencyChecker
status = DependencyChecker.get_dependency_status()
print(json.dumps(status, indent=2))
```

## Getting Additional Help

1. **Check Application Logs**: Look in logs directory for detailed error messages
2. **Run Diagnostics**: Use the built-in dependency checker
3. **System Information**: Collect system info for bug reports:

```bash
# System info script
cat > debug_info.sh << 'EOF'
#!/bin/bash
echo "=== System Information ==="
uname -a
python --version
pip --version

echo "=== Python Packages ==="
pip list | grep -E "(llama|sentence|nltk|transform)"

echo "=== Memory ==="
free -h 2>/dev/null || vm_stat

echo "=== Disk Space ==="
df -h

echo "=== LLM Dependencies ==="
python -m src.whisper_transcription_tool.core.dependency_checker --status
EOF

chmod +x debug_info.sh
./debug_info.sh > debug_report.txt
```

4. **Community Resources**:
   - llama-cpp-python GitHub issues
   - Hugging Face model discussions
   - Python packaging troubleshooting guides

## Known Limitations

1. **Model Size**: Large models require significant RAM (8GB+ recommended)
2. **Platform Support**: Metal acceleration only on Apple Silicon
3. **Network Requirements**: Initial setup requires internet for downloads
4. **Storage Requirements**: Models require 5-10GB disk space
5. **Performance**: CPU-only inference is significantly slower than GPU-accelerated