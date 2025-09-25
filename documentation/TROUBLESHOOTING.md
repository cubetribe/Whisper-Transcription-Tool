# 🛠️ LLM Text Correction - Troubleshooting Guide

**Comprehensive troubleshooting guide for LeoLM text correction issues**

---

## 📋 Quick Diagnostic Checklist

Before diving into specific issues, run this quick diagnostic:

```bash
# 1. Check system resources
python3 -c "
import psutil
mem = psutil.virtual_memory()
print(f'💾 Memory: {mem.available/1024**3:.1f}GB available ({mem.percent:.1f}% used)')
print(f'💻 CPU cores: {psutil.cpu_count()}')
"

# 2. Check model file
python3 -c "
from pathlib import Path
model_path = Path('~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf').expanduser()
if model_path.exists():
    size_gb = model_path.stat().st_size / 1024**3
    print(f'✅ Model found: {size_gb:.1f}GB')
else:
    print('❌ Model not found')
"

# 3. Test basic correction
python3 -c "
try:
    from whisper_transcription_tool.module5_text_correction import LLMCorrector
    print('✅ Module import successful')
    with LLMCorrector() as corrector:
        result = corrector.correct_text('test')
        print('✅ Basic correction test passed')
except Exception as e:
    print(f'❌ Error: {e}')
"
```

---

## 🚨 Common Errors and Solutions

### 1. Model Loading Errors

#### Error: `FileNotFoundError: LeoLM model not found`

**Symptoms**:
```
FileNotFoundError: LeoLM model not found at: ~/.lmstudio/models/...
```

**Causes**:
- Model not downloaded
- Incorrect path in configuration
- File permissions issue

**Solutions**:

1. **Download the model**:
   ```bash
   # Using LM Studio (recommended)
   # Open LM Studio → Search: "LeoLM-hesseianai-13b-chat"
   # Select: mradermacher/LeoLM-hesseianai-13b-chat-GGUF
   # Download: Q4_K_M variant
   ```

2. **Check and fix path**:
   ```bash
   # Find where LM Studio stores models
   find ~ -name "*LeoLM*" -type f 2>/dev/null

   # Common paths:
   # ~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/
   # ~/.cache/lm-studio/models/...
   # ~/Library/Caches/LMStudio/models/...
   ```

3. **Update configuration**:
   ```json
   {
     "text_correction": {
       "model_path": "/correct/path/to/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf"
     }
   }
   ```

4. **Fix permissions**:
   ```bash
   chmod 644 ~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/*.gguf
   ```

#### Error: `ImportError: llama-cpp-python not available`

**Symptoms**:
```
ImportError: llama-cpp-python not available. Install with: pip install llama-cpp-python
```

**Solution**:
```bash
# Install llama-cpp-python with Metal support
source venv_new/bin/activate
pip install llama-cpp-python>=0.2.0

# Verify installation
python -c "from llama_cpp import Llama; print('✅ llama-cpp-python installed')"
```

**If installation fails**:
```bash
# Force reinstall with specific flags
CMAKE_ARGS="-DLLAMA_METAL=ON" pip install llama-cpp-python --force-reinstall --no-cache-dir

# Alternative: Use pre-built wheels
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/metal
```

#### Error: `RuntimeError: Model loading failed`

**Symptoms**:
```
RuntimeError: Model loading failed
```

**Diagnostic Steps**:

1. **Check available memory**:
   ```python
   import psutil
   available_gb = psutil.virtual_memory().available / 1024**3
   print(f"Available memory: {available_gb:.1f}GB")
   # Need at least 6GB for LeoLM-13B
   ```

2. **Test with reduced parameters**:
   ```python
   from whisper_transcription_tool.module5_text_correction import LLMCorrector

   # Try with minimal settings
   corrector = LLMCorrector(context_length=512)
   # In configuration, set n_gpu_layers to smaller value
   ```

3. **Check model file integrity**:
   ```bash
   # Verify file is not corrupted
   file ~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/*.gguf
   # Should show "data"

   # Check file size (should be ~7.5GB for Q4_K_M)
   ls -lh ~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/*.gguf
   ```

**Solutions**:

1. **Reduce GPU layers**:
   ```json
   {
     "text_correction": {
       "n_gpu_layers": 20,  // Instead of -1
       "context_length": 1024  // Smaller context
     }
   }
   ```

2. **CPU-only mode**:
   ```json
   {
     "text_correction": {
       "n_gpu_layers": 0,  // CPU only
       "n_threads": 4
     }
   }
   ```

3. **Re-download model**:
   ```bash
   # Remove corrupted model
   rm ~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/*.gguf
   # Re-download via LM Studio
   ```

---

### 2. Memory Issues

#### Error: `MemoryError` or System Freeze

**Symptoms**:
- System becomes unresponsive
- "MemoryError" or "Out of memory" messages
- Excessive swap usage

**Prevention**:
```python
# Check memory before loading
def check_memory_safety():
    import psutil
    mem = psutil.virtual_memory()
    available_gb = mem.available / 1024**3

    if available_gb < 6.0:
        print(f"⚠️  Only {available_gb:.1f}GB available (need 6GB+)")
        return False
    return True

if not check_memory_safety():
    print("❌ Insufficient memory for LeoLM")
    exit(1)
```

**Solutions**:

1. **Close other applications**:
   ```bash
   # Check memory usage by application
   top -o mem -n 10

   # Close memory-intensive apps
   # Chrome, Photoshop, other AI tools
   ```

2. **Use low-memory configuration**:
   ```json
   {
     "text_correction": {
       "context_length": 512,
       "n_gpu_layers": 10,
       "batch_size": 1,
       "use_mlock": false,
       "use_mmap": false
     }
   }
   ```

3. **Enable swap** (macOS):
   ```bash
   # Check current swap usage
   sysctl vm.swapusage

   # macOS manages swap automatically, but you can force cleanup
   sudo purge
   ```

4. **Process in smaller chunks**:
   ```python
   # For large texts, process in very small chunks
   processor = BatchProcessor(max_context_length=400)
   ```

#### Error: `Metal GPU out of memory`

**Symptoms**:
```
RuntimeError: Metal GPU out of memory
```

**Solutions**:

1. **Reduce GPU layers**:
   ```json
   {
     "text_correction": {
       "n_gpu_layers": 15  // Instead of -1 (all layers)
     }
   }
   ```

2. **Use CPU fallback**:
   ```json
   {
     "text_correction": {
       "n_gpu_layers": 0,  // CPU only
       "n_threads": 6
     }
   }
   ```

3. **Clear GPU memory**:
   ```python
   # Force cleanup between corrections
   import gc
   gc.collect()  # Python garbage collection

   # In your code:
   with LLMCorrector() as corrector:
       result = corrector.correct_text(text)
   # Model is automatically unloaded here
   ```

---

### 3. Performance Issues

#### Issue: Very Slow Correction (>5 seconds per sentence)

**Diagnostic**:
```python
import time
from whisper_transcription_tool.module5_text_correction import LLMCorrector

test_text = "Das ist ein kurzer test."
start = time.time()

with LLMCorrector() as corrector:
    result = corrector.correct_text(test_text)

processing_time = time.time() - start
chars_per_sec = len(test_text) / processing_time

print(f"Processing time: {processing_time:.2f}s")
print(f"Speed: {chars_per_sec:.1f} chars/second")

# Should be >20 chars/second on Apple Silicon
if chars_per_sec < 10:
    print("⚠️  Performance issue detected")
```

**Solutions**:

1. **Check GPU utilization**:
   ```bash
   # Monitor GPU usage during correction
   sudo powermetrics -i 1000 -s gpu_power --samplers gpu_power
   ```

2. **Optimize configuration for speed**:
   ```json
   {
     "text_correction": {
       "context_length": 1024,      // Smaller context
       "correction_level": "basic",  // Faster level
       "temperature": 0.1,          // Lower temperature
       "max_tokens": 256,           // Shorter responses
       "n_threads": -1              // Use all threads
     }
   }
   ```

3. **Check thermal throttling**:
   ```bash
   # Monitor CPU temperature
   sudo powermetrics -i 1000 --samplers smc -n 10 | grep -i temp

   # If overheating (>85°C), improve cooling or reduce load
   ```

4. **CPU vs GPU comparison**:
   ```python
   # Test CPU-only performance
   corrector_cpu = LLMCorrector(context_length=2048)
   # Configure with n_gpu_layers=0

   # Test GPU performance
   corrector_gpu = LLMCorrector(context_length=2048)
   # Configure with n_gpu_layers=-1

   # Compare timing
   ```

#### Issue: High Memory Usage During Correction

**Monitor memory usage**:
```python
import psutil
import time
from whisper_transcription_tool.module5_text_correction import LLMCorrector

def monitor_memory_usage():
    process = psutil.Process()
    start_memory = process.memory_info().rss / 1024**2  # MB

    with LLMCorrector() as corrector:
        # Memory after model load
        after_load = process.memory_info().rss / 1024**2
        print(f"Memory after load: {after_load - start_memory:.1f}MB increase")

        result = corrector.correct_text("Test text" * 100)

        # Memory during correction
        during_correction = process.memory_info().rss / 1024**2
        print(f"Peak memory usage: {during_correction - start_memory:.1f}MB")

    # Memory after cleanup
    final_memory = process.memory_info().rss / 1024**2
    print(f"Memory after cleanup: {final_memory - start_memory:.1f}MB")

monitor_memory_usage()
```

**Solutions**:
1. **Enable memory mapping**:
   ```json
   {
     "text_correction": {
       "use_mmap": true,   // Memory mapping
       "use_mlock": false  // Don't lock in RAM
     }
   }
   ```

2. **Process smaller chunks**:
   ```json
   {
     "text_correction": {
       "max_chunk_size": 800,  // Smaller chunks
       "batch_size": 1         // Process one at a time
     }
   }
   ```

---

### 4. Configuration Errors

#### Error: `KeyError: 'text_correction'`

**Symptoms**:
```
KeyError: 'text_correction'
```

**Solution**:
```bash
# Check if configuration file exists
ls -la ~/.whisper_tool.json

# If missing, create minimal configuration
cat > ~/.whisper_tool.json << 'EOF'
{
  "text_correction": {
    "enabled": true,
    "model_path": "~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",
    "context_length": 2048
  }
}
EOF
```

#### Error: Configuration validation fails

**Diagnostic script**:
```python
#!/usr/bin/env python3
import json
from pathlib import Path

def validate_and_fix_config():
    config_path = Path.home() / ".whisper_tool.json"

    try:
        with open(config_path) as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ Configuration file not found")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return False

    # Check and fix text_correction section
    tc = config.setdefault("text_correction", {})

    # Required fields with defaults
    defaults = {
        "enabled": False,
        "model_path": "~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",
        "context_length": 2048,
        "correction_level": "standard",
        "temperature": 0.3
    }

    fixed = False
    for key, default_value in defaults.items():
        if key not in tc:
            tc[key] = default_value
            fixed = True
            print(f"✅ Added missing '{key}': {default_value}")

    if fixed:
        # Save corrected configuration
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✅ Configuration fixed and saved")

    return True

validate_and_fix_config()
```

---

### 5. Text Processing Issues

#### Issue: Correction produces wrong results or hallucinations

**Symptoms**:
- Output contains information not in original text
- Completely different meaning
- Made-up facts or names

**Solutions**:

1. **Lower temperature for consistency**:
   ```json
   {
     "text_correction": {
       "temperature": 0.1,  // Very low for factual corrections
       "top_p": 0.8        // Focused sampling
     }
   }
   ```

2. **Use more conservative prompt**:
   ```python
   # Custom prompt that emphasizes preservation
   conservative_prompt = """Korrigiere nur offensichtliche Rechtschreibfehler im folgenden Text.
   ÄNDERE NICHT den Inhalt oder die Bedeutung. Behalte alle Namen, Zahlen und Fakten bei.

   Text: {text}

   Korrigierter Text:"""
   ```

3. **Process smaller chunks**:
   ```json
   {
     "text_correction": {
       "max_chunk_size": 400,  // Very small chunks
       "overlap_sentences": 0   // No overlap to prevent confusion
     }
   }
   ```

4. **Use basic correction level**:
   ```json
   {
     "text_correction": {
       "correction_level": "basic"  // Less aggressive corrections
     }
   }
   ```

#### Issue: Text formatting is lost

**Symptoms**:
- Line breaks removed
- Paragraph structure lost
- Special characters changed

**Solutions**:

1. **Enable formatting preservation**:
   ```json
   {
     "text_correction": {
       "preserve_formatting": true,
       "preserve_line_breaks": true
     }
   }
   ```

2. **Pre-process text to protect formatting**:
   ```python
   def preserve_formatting(text: str) -> tuple[str, dict]:
       import re

       # Save formatting markers
       formatting = {}
       protected_text = text

       # Protect line breaks
       protected_text = re.sub(r'\n\n+', ' [PARAGRAPH_BREAK] ', protected_text)
       protected_text = re.sub(r'\n', ' [LINE_BREAK] ', protected_text)

       return protected_text, formatting

   def restore_formatting(text: str, formatting: dict) -> str:
       # Restore formatting
       text = text.replace(' [PARAGRAPH_BREAK] ', '\n\n')
       text = text.replace(' [LINE_BREAK] ', '\n')
       return text
   ```

---

### 6. Integration Issues

#### Issue: Web interface doesn't show text correction option

**Diagnostic**:
```python
# Check if text correction is enabled in config
from whisper_transcription_tool.core.config import load_config

config = load_config()
tc_config = config.get("text_correction", {})

print(f"Text correction enabled: {tc_config.get('enabled', False)}")
print(f"Model path: {tc_config.get('model_path', 'Not set')}")
```

**Solutions**:

1. **Enable in configuration**:
   ```json
   {
     "text_correction": {
       "enabled": true
     }
   }
   ```

2. **Restart web server**:
   ```bash
   # Kill existing server
   pkill -f "whisper_transcription_tool.main"

   # Start fresh
   ./start_server.sh
   ```

3. **Check browser cache**:
   ```bash
   # Hard refresh in browser: Cmd+Shift+R (Mac) or Ctrl+Shift+R
   # Or clear browser cache
   ```

#### Issue: Command line tool not found

**Symptoms**:
```bash
whisper-tool: command not found
```

**Solutions**:

1. **Install in development mode**:
   ```bash
   source venv_new/bin/activate
   pip install -e ".[full]"
   ```

2. **Use Python module directly**:
   ```bash
   python -m whisper_transcription_tool.main correct "text to correct"
   ```

3. **Check PATH**:
   ```bash
   # Find where whisper-tool is installed
   which whisper-tool

   # If not found, add to PATH
   export PATH="$PATH:$(python -m site --user-base)/bin"
   ```

---

### 7. Platform-Specific Issues

#### macOS: Metal Performance Shaders Issues

**Symptoms**:
```
Metal GPU not available
MPS backend not available
```

**Solutions**:

1. **Check Metal support**:
   ```python
   # Check if Metal is available
   import subprocess
   result = subprocess.run(['system_profiler', 'SPDisplaysDataType'],
                          capture_output=True, text=True)
   if 'Metal' in result.stdout:
       print("✅ Metal supported")
   else:
       print("❌ Metal not available")
   ```

2. **Update macOS**:
   ```bash
   # Check macOS version
   sw_vers

   # Metal requires macOS 12.0+
   # Update if needed via System Preferences
   ```

3. **Force CPU mode if Metal unavailable**:
   ```json
   {
     "text_correction": {
       "n_gpu_layers": 0,
       "force_cpu": true
     }
   }
   ```

#### Issue: Xcode Command Line Tools missing

**Symptoms**:
```
xcrun: error: invalid active developer path
```

**Solution**:
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Verify installation
gcc --version
```

---

## 🔍 Advanced Diagnostics

### Full System Diagnostic Script

```python
#!/usr/bin/env python3
"""
Comprehensive diagnostic script for LeoLM text correction
"""

import json
import os
import platform
import psutil
import subprocess
import sys
from pathlib import Path

def run_full_diagnostic():
    print("🔍 LeoLM Text Correction - Full System Diagnostic")
    print("=" * 60)

    # System Information
    print("\n💻 System Information:")
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    print(f"Python: {sys.version.split()[0]}")

    # Memory Information
    print("\n💾 Memory Information:")
    mem = psutil.virtual_memory()
    print(f"Total RAM: {mem.total / 1024**3:.1f}GB")
    print(f"Available: {mem.available / 1024**3:.1f}GB ({mem.percent:.1f}% used)")

    # Disk Space
    print("\n💽 Disk Space:")
    disk = psutil.disk_usage(Path.home())
    print(f"Free space: {disk.free / 1024**3:.1f}GB")

    # Configuration Check
    print("\n⚙️  Configuration Check:")
    config_path = Path.home() / ".whisper_tool.json"
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = json.load(f)
            tc = config.get("text_correction", {})
            print(f"✅ Config file found")
            print(f"   Enabled: {tc.get('enabled', False)}")
            print(f"   Model path: {tc.get('model_path', 'Not set')}")
            print(f"   Context length: {tc.get('context_length', 'Not set')}")
        except Exception as e:
            print(f"❌ Config file error: {e}")
    else:
        print("❌ Configuration file not found")

    # Model File Check
    print("\n📦 Model File Check:")
    model_paths = [
        "~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",
        "~/.cache/lm-studio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf"
    ]

    model_found = False
    for path in model_paths:
        expanded_path = Path(path).expanduser()
        if expanded_path.exists():
            size_gb = expanded_path.stat().st_size / 1024**3
            print(f"✅ Model found: {expanded_path}")
            print(f"   Size: {size_gb:.1f}GB")
            model_found = True
            break

    if not model_found:
        print("❌ Model file not found in common locations")
        # Search for any LeoLM files
        print("🔎 Searching for LeoLM files...")
        try:
            result = subprocess.run(
                ["find", str(Path.home()), "-name", "*LeoLM*", "-type", "f"],
                capture_output=True, text=True, timeout=30
            )
            if result.stdout:
                print("Found LeoLM files:")
                for line in result.stdout.strip().split('\n')[:5]:  # Show first 5
                    print(f"   {line}")
            else:
                print("   No LeoLM files found")
        except:
            print("   Search failed")

    # Python Dependencies
    print("\n🐍 Python Dependencies:")
    required_packages = [
        "llama_cpp",
        "whisper_transcription_tool",
        "psutil",
        "nltk"
    ]

    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} not installed")

    # Metal/GPU Check (macOS only)
    if platform.system() == "Darwin":
        print("\n🔥 Metal GPU Check:")
        try:
            result = subprocess.run(
                ["system_profiler", "SPDisplaysDataType"],
                capture_output=True, text=True
            )
            if "Metal" in result.stdout:
                print("✅ Metal GPU support available")
            else:
                print("❌ Metal GPU support not detected")
        except:
            print("❓ Could not check Metal support")

    # Test Basic Import
    print("\n🧪 Basic Functionality Test:")
    try:
        from whisper_transcription_tool.module5_text_correction import LLMCorrector
        print("✅ LLMCorrector import successful")

        # Test model loading (without actually loading)
        corrector = LLMCorrector()
        if corrector.model_path.exists():
            print("✅ Model path accessible")
        else:
            print("❌ Model path not accessible")

    except Exception as e:
        print(f"❌ Import failed: {e}")

    print("\n🎯 Recommendations:")

    # Memory recommendation
    if mem.available / 1024**3 < 6:
        print("⚠️  Consider freeing up memory (need 6GB+ available)")

    # Model recommendation
    if not model_found:
        print("⚠️  Download LeoLM model via LM Studio")

    # Configuration recommendation
    if not config_path.exists():
        print("⚠️  Create configuration file with text_correction section")

    print("\nDiagnostic complete! 🎉")

if __name__ == "__main__":
    run_full_diagnostic()
```

### Performance Profiling Script

```python
#!/usr/bin/env python3
"""
Performance profiling for LeoLM text correction
"""

import cProfile
import io
import pstats
import time
from whisper_transcription_tool.module5_text_correction import LLMCorrector

def profile_correction():
    """Profile a text correction operation."""

    test_text = """
    Das ist ein längerer text mit verschiedene fehler die korrigiert werden müssen.
    Wir möchten die performance der korrektur messen und verstehen wo die Zeit verbracht wird.
    Diese profiling hilft uns bei der optimierung der geschwindigkeit.
    """

    # Profile the correction
    profiler = cProfile.Profile()

    profiler.enable()

    try:
        with LLMCorrector() as corrector:
            result = corrector.correct_text(test_text)

    finally:
        profiler.disable()

    # Analyze results
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s)
    ps.sort_stats('cumulative')
    ps.print_stats(20)  # Top 20 functions

    print("🔍 Performance Profile:")
    print(s.getvalue())

if __name__ == "__main__":
    profile_correction()
```

---

## 📞 Getting Help

### Log Collection for Support

```bash
#!/bin/bash
# collect_logs.sh - Collect diagnostic information for support

echo "📋 Collecting diagnostic information..."

# Create support bundle directory
SUPPORT_DIR="whisper_support_$(date +%Y%m%d_%H%M%S)"
mkdir "$SUPPORT_DIR"

# System information
echo "💻 Collecting system information..."
system_profiler SPSoftwareDataType SPHardwareDataType > "$SUPPORT_DIR/system_info.txt"
sw_vers > "$SUPPORT_DIR/macos_version.txt"

# Memory and disk info
echo "💾 Collecting memory and disk info..."
vm_stat > "$SUPPORT_DIR/memory_info.txt"
df -h > "$SUPPORT_DIR/disk_info.txt"

# Configuration
echo "⚙️  Collecting configuration..."
if [ -f ~/.whisper_tool.json ]; then
    cp ~/.whisper_tool.json "$SUPPORT_DIR/config.json"
else
    echo "Configuration file not found" > "$SUPPORT_DIR/config.json"
fi

# Python environment
echo "🐍 Collecting Python environment info..."
source venv_new/bin/activate 2>/dev/null || true
pip list > "$SUPPORT_DIR/python_packages.txt"
python --version > "$SUPPORT_DIR/python_version.txt"

# Logs (if they exist)
echo "📝 Collecting logs..."
if [ -d "logs" ]; then
    cp -r logs "$SUPPORT_DIR/"
fi

# Run diagnostic script
echo "🔍 Running diagnostics..."
python3 - > "$SUPPORT_DIR/diagnostic_output.txt" << 'EOF'
# Run the diagnostic script from above
import sys
sys.path.append('src')
exec(open('diagnostic_script.py').read())
EOF

# Create archive
echo "📦 Creating support bundle..."
tar -czf "${SUPPORT_DIR}.tar.gz" "$SUPPORT_DIR"
rm -rf "$SUPPORT_DIR"

echo "✅ Support bundle created: ${SUPPORT_DIR}.tar.gz"
echo "📧 Send this file to: mail@goaiex.com"
```

### Community Resources

- **GitHub Issues**: [Report bugs or request features](https://github.com/cubetribe/WhisperCC_MacOS_Local/issues)
- **LM Studio Discord**: [Community support for model issues](https://discord.com/invite/aPQfnNkxGC)
- **Email Support**: mail@goaiex.com (for commercial licenses)

### Before Reporting Issues

Please include:

1. **System Information**:
   - macOS version
   - RAM amount
   - Mac model (M1/M2/M3)

2. **Configuration**:
   - Your `~/.whisper_tool.json` file (remove sensitive info)
   - Model version and path

3. **Error Details**:
   - Complete error message
   - Steps to reproduce
   - Expected vs actual behavior

4. **Diagnostic Output**:
   - Run the diagnostic script above
   - Include output in your report

---

## 🎯 Quick Solutions Summary

| Problem | Quick Fix |
|---------|-----------|
| Model not found | Download via LM Studio, check path in config |
| Out of memory | Close apps, reduce `n_gpu_layers`, use smaller context |
| Very slow | Enable Metal GPU, reduce temperature, use "basic" level |
| Import errors | `pip install llama-cpp-python` |
| Wrong corrections | Lower temperature (0.1), use "basic" level |
| Config errors | Run validation script, recreate config file |
| Web UI missing option | Enable in config, restart server |
| Metal errors | Update macOS, install Xcode tools |

---

**Version**: 1.0.0 | **Date**: September 2025
**Created by**: DocsNarrator Agent | **Website**: [www.goaiex.com](https://www.goaiex.com)

This troubleshooting guide is regularly updated. If you encounter new issues, please report them so we can help others!