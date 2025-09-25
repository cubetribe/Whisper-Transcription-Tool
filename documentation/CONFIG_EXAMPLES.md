# ⚙️ LLM Text Correction - Configuration Examples

**Comprehensive configuration examples for optimal LeoLM performance across different hardware setups**

---

## 📋 Table of Contents

1. [Default Configurations](#-default-configurations)
2. [Hardware-Specific Configs](#-hardware-specific-configurations)
3. [Performance-Optimized Configs](#-performance-optimized-configurations)
4. [Low-Memory Configs](#-low-memory-configurations)
5. [Platform-Specific Configs](#-platform-specific-configurations)
6. [Migration Guide](#-migration-guide)
7. [Advanced Scenarios](#-advanced-scenarios)

---

## 🎯 Default Configurations

### Basic Configuration
**Ideal for**: First-time setup, testing, most users

```json
{
  "text_correction": {
    "enabled": true,
    "model_path": "~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",
    "context_length": 2048,
    "correction_level": "standard",
    "temperature": 0.3
  }
}
```

### Comprehensive Default Configuration
**Full configuration with all available options**

```json
{
  "whisper": {
    "model_path": "models",
    "default_model": "large-v3-turbo",
    "threads": 4
  },
  "text_correction": {
    "enabled": true,

    // Core Model Settings
    "model_path": "~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",
    "context_length": 2048,
    "correction_level": "standard",

    // Generation Parameters
    "temperature": 0.3,
    "max_tokens": 512,
    "top_p": 0.9,
    "repeat_penalty": 1.1,
    "stop_tokens": ["Text:", "Korrigierter Text:", "Corrected text:"],

    // Hardware Acceleration
    "n_gpu_layers": -1,
    "n_threads": 8,
    "use_mlock": true,
    "use_mmap": true,
    "rope_freq_base": 10000.0,
    "rope_freq_scale": 1.0,

    // Text Processing
    "enable_chunking": true,
    "max_chunk_size": 1600,
    "overlap_sentences": 1,
    "tokenizer_strategy": "nltk",
    "preserve_formatting": true,

    // Performance & Resource Management
    "batch_size": 4,
    "timeout_seconds": 120,
    "max_retries": 2,
    "retry_delay": 5.0,
    "memory_threshold_gb": 6.0,

    // Debugging & Monitoring
    "verbose": false,
    "log_corrections": true,
    "save_intermediate_results": false,
    "enable_metrics": false
  },
  "output": {
    "default_directory": "transcriptions",
    "formats": ["txt", "srt"],
    "include_timestamps": true
  }
}
```

---

## 💻 Hardware-Specific Configurations

### MacBook Air M1 (8GB RAM)
**Optimized for**: Entry-level Apple Silicon with limited RAM

```json
{
  "text_correction": {
    "enabled": true,
    "model_path": "~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",

    // Reduced context to save memory
    "context_length": 1024,
    "correction_level": "basic",

    // Conservative generation settings
    "temperature": 0.2,
    "max_tokens": 256,

    // Limited GPU layers to prevent memory issues
    "n_gpu_layers": 25,
    "n_threads": 4,
    "use_mlock": false,  // Don't lock model in RAM
    "use_mmap": true,

    // Small batch processing
    "batch_size": 1,
    "max_chunk_size": 800,
    "overlap_sentences": 0,

    // Strict memory management
    "memory_threshold_gb": 5.0,
    "timeout_seconds": 60,
    "max_retries": 1
  }
}
```

### MacBook Pro M2 (16GB RAM)
**Optimized for**: Mid-range Apple Silicon with good performance

```json
{
  "text_correction": {
    "enabled": true,
    "model_path": "~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",

    // Standard configuration
    "context_length": 2048,
    "correction_level": "advanced",

    // Balanced generation settings
    "temperature": 0.3,
    "max_tokens": 512,

    // Full GPU utilization
    "n_gpu_layers": -1,
    "n_threads": 8,
    "use_mlock": true,
    "use_mmap": true,

    // Moderate batch processing
    "batch_size": 4,
    "max_chunk_size": 1600,
    "overlap_sentences": 1,

    // Standard memory settings
    "memory_threshold_gb": 6.0,
    "timeout_seconds": 120
  }
}
```

### MacBook Pro M3 Max (32GB+ RAM)
**Optimized for**: High-end Apple Silicon with maximum performance

```json
{
  "text_correction": {
    "enabled": true,
    "model_path": "~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",

    // Maximum context length
    "context_length": 4096,
    "correction_level": "formal",

    // High-quality generation
    "temperature": 0.3,
    "max_tokens": 1024,
    "top_p": 0.95,

    // Full hardware utilization
    "n_gpu_layers": -1,
    "n_threads": 12,
    "use_mlock": true,
    "use_mmap": true,

    // Aggressive batch processing
    "batch_size": 8,
    "max_chunk_size": 3000,
    "overlap_sentences": 2,

    // High memory threshold
    "memory_threshold_gb": 8.0,
    "timeout_seconds": 180,
    "enable_metrics": true
  }
}
```

### Mac Studio M2 Ultra (64GB+ RAM)
**Optimized for**: Professional workstation with maximum resources

```json
{
  "text_correction": {
    "enabled": true,
    // Consider using larger model variants for best quality
    "model_path": "~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",

    // Maximum performance settings
    "context_length": 8192,
    "correction_level": "formal",

    // High-precision generation
    "temperature": 0.25,
    "max_tokens": 2048,
    "top_p": 0.95,
    "repeat_penalty": 1.05,

    // Full resource utilization
    "n_gpu_layers": -1,
    "n_threads": 16,
    "use_mlock": true,
    "use_mmap": true,
    "rope_freq_base": 10000.0,

    // Maximum throughput
    "batch_size": 12,
    "max_chunk_size": 6000,
    "overlap_sentences": 3,

    // Professional settings
    "memory_threshold_gb": 12.0,
    "timeout_seconds": 300,
    "enable_metrics": true,
    "log_corrections": true,
    "save_intermediate_results": true
  }
}
```

---

## ⚡ Performance-Optimized Configurations

### Speed-Optimized (Fast Correction)
**Ideal for**: Real-time applications, quick drafts

```json
{
  "text_correction": {
    "enabled": true,
    "model_path": "~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",

    // Reduced context for speed
    "context_length": 1024,
    "correction_level": "basic",

    // Fast generation parameters
    "temperature": 0.1,     // Very low for consistency
    "max_tokens": 256,      // Shorter responses
    "top_p": 0.8,          // Focused sampling

    // Maximum GPU utilization
    "n_gpu_layers": -1,
    "n_threads": -1,       // Use all available threads

    // Small chunks for parallel processing
    "batch_size": 6,
    "max_chunk_size": 600,
    "overlap_sentences": 0, // No overlap for speed

    // Short timeouts
    "timeout_seconds": 30,
    "max_retries": 1,

    // Minimal logging
    "verbose": false,
    "log_corrections": false
  }
}
```

### Quality-Optimized (Best Results)
**Ideal for**: Final documents, professional content

```json
{
  "text_correction": {
    "enabled": true,
    "model_path": "~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",

    // Maximum context for quality
    "context_length": 4096,
    "correction_level": "formal",

    // Quality-focused generation
    "temperature": 0.4,     // Slightly higher for nuanced corrections
    "max_tokens": 1024,
    "top_p": 0.95,
    "repeat_penalty": 1.1,

    // Full hardware utilization
    "n_gpu_layers": -1,
    "n_threads": 8,
    "use_mlock": true,

    // Large chunks with overlap for context
    "batch_size": 2,       // Smaller batches for quality
    "max_chunk_size": 3000,
    "overlap_sentences": 3, // Maximum overlap for context

    // Generous timeouts
    "timeout_seconds": 300,
    "max_retries": 3,
    "retry_delay": 10.0,

    // Full logging for review
    "verbose": true,
    "log_corrections": true,
    "save_intermediate_results": true
  }
}
```

### Balanced Configuration
**Ideal for**: Most production use cases

```json
{
  "text_correction": {
    "enabled": true,
    "model_path": "~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",

    // Balanced settings
    "context_length": 2048,
    "correction_level": "advanced",

    // Balanced generation
    "temperature": 0.3,
    "max_tokens": 512,
    "top_p": 0.9,

    // Optimal hardware usage
    "n_gpu_layers": -1,
    "n_threads": 8,
    "use_mlock": true,
    "use_mmap": true,

    // Moderate batching
    "batch_size": 4,
    "max_chunk_size": 1600,
    "overlap_sentences": 1,

    // Standard resilience
    "timeout_seconds": 120,
    "max_retries": 2,

    // Selective logging
    "verbose": false,
    "log_corrections": true,
    "enable_metrics": true
  }
}
```

---

## 🔋 Low-Memory Configurations

### Minimal Memory (4GB Available)
**For systems with very limited RAM**

```json
{
  "text_correction": {
    "enabled": true,
    "model_path": "~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",

    // Minimal context
    "context_length": 512,
    "correction_level": "basic",

    // Conservative generation
    "temperature": 0.1,
    "max_tokens": 128,

    // CPU-only processing
    "n_gpu_layers": 0,     // Force CPU-only
    "n_threads": 2,        // Minimal threading
    "use_mlock": false,    // Don't lock memory
    "use_mmap": false,     // No memory mapping

    // Sequential processing
    "batch_size": 1,
    "max_chunk_size": 300,
    "overlap_sentences": 0,

    // Strict limits
    "memory_threshold_gb": 3.0,
    "timeout_seconds": 30,
    "max_retries": 1,

    // No logging to save memory
    "verbose": false,
    "log_corrections": false,
    "enable_metrics": false
  }
}
```

### Memory-Efficient (6-8GB Available)
**For systems meeting minimum requirements**

```json
{
  "text_correction": {
    "enabled": true,
    "model_path": "~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",

    // Reduced context
    "context_length": 1024,
    "correction_level": "basic",

    // Efficient generation
    "temperature": 0.2,
    "max_tokens": 256,

    // Partial GPU usage
    "n_gpu_layers": 20,    // Only some layers on GPU
    "n_threads": 4,
    "use_mlock": false,
    "use_mmap": true,      // Memory mapping only

    // Small batches
    "batch_size": 2,
    "max_chunk_size": 800,
    "overlap_sentences": 0,

    // Memory monitoring
    "memory_threshold_gb": 5.5,
    "timeout_seconds": 60,

    // Minimal logging
    "log_corrections": false,
    "enable_metrics": false
  }
}
```

---

## 🖥️ Platform-Specific Configurations

### macOS with Metal Acceleration
**Optimized for Apple Silicon Macs**

```json
{
  "text_correction": {
    "enabled": true,
    "model_path": "~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",

    "context_length": 2048,
    "correction_level": "advanced",

    // Metal-optimized settings
    "n_gpu_layers": -1,           // All layers on Metal GPU
    "n_threads": 8,
    "use_mlock": true,            // Lock model in unified memory
    "use_mmap": true,
    "rope_freq_base": 10000.0,    // RoPE settings for Metal
    "rope_freq_scale": 1.0,

    // macOS-specific optimizations
    "batch_size": 4,
    "temperature": 0.3,
    "max_tokens": 512,

    // Take advantage of unified memory
    "memory_threshold_gb": 6.0,
    "enable_chunking": true,
    "max_chunk_size": 1600,

    "timeout_seconds": 120,
    "log_corrections": true
  }
}
```

### Linux with CUDA (if available in future)
**Example for potential CUDA support**

```json
{
  "text_correction": {
    "enabled": true,
    "model_path": "/home/user/.local/share/lm-studio/models/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",

    "context_length": 2048,
    "correction_level": "advanced",

    // CUDA settings (hypothetical)
    "n_gpu_layers": -1,
    "n_threads": 8,
    "use_mlock": false,    // Different memory model on Linux
    "use_mmap": true,

    // Standard settings
    "batch_size": 4,
    "temperature": 0.3,
    "max_tokens": 512,

    // Linux paths and settings
    "memory_threshold_gb": 6.0,
    "timeout_seconds": 120,
    "log_corrections": true
  }
}
```

---

## 🔄 Migration Guide

### From Version 0.9.6 to 0.9.7+
**Upgrading existing configurations**

#### Old Configuration (v0.9.6)
```json
{
  "text_correction": {
    "enabled": false,
    "model_path": "~/.lmstudio/models/...",
    "context_length": 2048
  }
}
```

#### New Configuration (v0.9.7+)
```json
{
  "text_correction": {
    "enabled": true,
    "model_path": "~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",
    "context_length": 2048,
    "correction_level": "standard",
    "temperature": 0.3,

    // New options in v0.9.7
    "n_gpu_layers": -1,
    "use_mlock": true,
    "use_mmap": true,
    "batch_size": 4,
    "enable_chunking": true,
    "max_chunk_size": 1600,
    "overlap_sentences": 1
  }
}
```

### Migration Script
**Automatic configuration upgrade**

```python
#!/usr/bin/env python3
"""
Configuration migration script for Whisper Tool v0.9.7+
"""

import json
import shutil
from pathlib import Path

def migrate_config():
    config_path = Path.home() / ".whisper_tool.json"
    backup_path = Path.home() / ".whisper_tool.json.backup"

    if not config_path.exists():
        print("No existing configuration found.")
        return

    # Create backup
    shutil.copy2(config_path, backup_path)
    print(f"Backup created: {backup_path}")

    # Load existing config
    with open(config_path) as f:
        config = json.load(f)

    # Migrate text_correction section
    if "text_correction" in config:
        tc = config["text_correction"]

        # Add new default values
        tc.setdefault("correction_level", "standard")
        tc.setdefault("temperature", 0.3)
        tc.setdefault("n_gpu_layers", -1)
        tc.setdefault("use_mlock", True)
        tc.setdefault("use_mmap", True)
        tc.setdefault("batch_size", 4)
        tc.setdefault("enable_chunking", True)
        tc.setdefault("max_chunk_size", 1600)
        tc.setdefault("overlap_sentences", 1)
        tc.setdefault("timeout_seconds", 120)
        tc.setdefault("max_retries", 2)
        tc.setdefault("log_corrections", True)

        # Enable by default if model path exists
        if tc.get("model_path") and not tc.get("enabled", False):
            model_path = Path(tc["model_path"]).expanduser()
            if model_path.exists():
                tc["enabled"] = True
                print("Enabled text correction (model found)")

    # Save updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"Configuration migrated successfully!")
    print(f"Backup available at: {backup_path}")

if __name__ == "__main__":
    migrate_config()
```

---

## 🎯 Advanced Scenarios

### Multi-Language Support
**Configuration for German + English correction**

```json
{
  "text_correction": {
    "enabled": true,
    "model_path": "~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",

    "context_length": 2048,
    "correction_level": "advanced",
    "temperature": 0.3,

    // Language-specific settings
    "default_language": "de",
    "supported_languages": ["de", "en"],
    "auto_detect_language": true,

    // Prompt customization per language
    "custom_prompts": {
      "de_formal": "Du bist ein Experte für deutsche Geschäftskorrespondenz...",
      "en_formal": "You are an expert for English business correspondence..."
    },

    "n_gpu_layers": -1,
    "batch_size": 4,
    "timeout_seconds": 120
  }
}
```

### Development and Testing
**Configuration for development environments**

```json
{
  "text_correction": {
    "enabled": true,
    "model_path": "~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",

    "context_length": 1024,  // Faster for testing
    "correction_level": "basic",
    "temperature": 0.1,      // Consistent results

    // Development settings
    "n_gpu_layers": 10,      // Partial GPU for debugging
    "batch_size": 1,         // Sequential for debugging
    "timeout_seconds": 30,   // Short timeout for tests

    // Extensive logging
    "verbose": true,
    "log_corrections": true,
    "save_intermediate_results": true,
    "enable_metrics": true,

    // Test-specific options
    "dry_run": false,
    "benchmark_mode": false,
    "debug_chunks": true
  }
}
```

### Production Server
**Configuration for server deployments**

```json
{
  "text_correction": {
    "enabled": true,
    "model_path": "/opt/models/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",

    "context_length": 2048,
    "correction_level": "advanced",
    "temperature": 0.3,

    // Production optimization
    "n_gpu_layers": -1,
    "n_threads": 8,
    "use_mlock": true,
    "use_mmap": true,

    // Server settings
    "batch_size": 6,
    "timeout_seconds": 180,
    "max_retries": 3,
    "retry_delay": 10.0,

    // Resource management
    "memory_threshold_gb": 8.0,
    "max_concurrent_requests": 4,

    // Monitoring
    "enable_metrics": true,
    "metrics_port": 9090,
    "health_check_interval": 60,

    // Logging (reduced for production)
    "verbose": false,
    "log_corrections": false,
    "log_level": "INFO"
  }
}
```

### Research and Experimentation
**Configuration for testing different parameters**

```json
{
  "text_correction": {
    "enabled": true,
    "model_path": "~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",

    // Experimental parameters
    "context_length": 4096,
    "correction_level": "experimental",
    "temperature": 0.35,
    "top_p": 0.92,
    "repeat_penalty": 1.15,
    "presence_penalty": 0.1,
    "frequency_penalty": 0.1,

    // Advanced sampling
    "min_p": 0.05,
    "typical_p": 1.0,
    "tfs_z": 1.0,
    "mirostat": 0,
    "mirostat_tau": 5.0,
    "mirostat_eta": 0.1,

    // Research settings
    "n_gpu_layers": -1,
    "batch_size": 1,        // Single batch for controlled experiments
    "seed": 42,             // Reproducible results

    // Comprehensive logging
    "verbose": true,
    "log_corrections": true,
    "save_intermediate_results": true,
    "enable_metrics": true,
    "benchmark_mode": true,

    // Custom evaluation
    "enable_quality_scoring": true,
    "compare_with_baseline": true,
    "export_results": true
  }
}
```

---

## 🔧 Configuration Validation

### Validation Script
**Check your configuration for common issues**

```python
#!/usr/bin/env python3
"""
Configuration validation script for LeoLM text correction
"""

import json
import psutil
from pathlib import Path

def validate_config(config_path: str = None):
    if config_path is None:
        config_path = Path.home() / ".whisper_tool.json"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        print("❌ Configuration file not found")
        return False

    with open(config_path) as f:
        config = json.load(f)

    tc = config.get("text_correction", {})

    print("🔍 Validating Text Correction Configuration...\n")

    # Check if enabled
    if not tc.get("enabled", False):
        print("⚠️  Text correction is disabled")
        return True

    valid = True

    # Model path validation
    model_path = Path(tc.get("model_path", "")).expanduser()
    if model_path.exists():
        size_gb = model_path.stat().st_size / 1024**3
        print(f"✅ Model file found: {model_path}")
        print(f"   Size: {size_gb:.1f} GB")
    else:
        print(f"❌ Model file not found: {model_path}")
        valid = False

    # Memory requirements
    available_gb = psutil.virtual_memory().available / 1024**3
    required_gb = tc.get("memory_threshold_gb", 6.0)

    if available_gb >= required_gb:
        print(f"✅ Sufficient memory: {available_gb:.1f}GB available (need {required_gb:.1f}GB)")
    else:
        print(f"⚠️  Low memory: {available_gb:.1f}GB available (need {required_gb:.1f}GB)")

    # Context length validation
    context_length = tc.get("context_length", 2048)
    if 512 <= context_length <= 8192:
        print(f"✅ Context length valid: {context_length}")
    else:
        print(f"⚠️  Unusual context length: {context_length}")

    # Temperature validation
    temperature = tc.get("temperature", 0.3)
    if 0.0 <= temperature <= 1.0:
        print(f"✅ Temperature valid: {temperature}")
    else:
        print(f"❌ Invalid temperature: {temperature} (should be 0.0-1.0)")
        valid = False

    # GPU layers validation
    n_gpu_layers = tc.get("n_gpu_layers", -1)
    if n_gpu_layers == -1 or n_gpu_layers >= 0:
        print(f"✅ GPU layers setting: {n_gpu_layers}")
    else:
        print(f"❌ Invalid GPU layers: {n_gpu_layers}")
        valid = False

    print(f"\n{'✅ Configuration valid!' if valid else '❌ Configuration has issues!'}")
    return valid

if __name__ == "__main__":
    import sys
    config_file = sys.argv[1] if len(sys.argv) > 1 else None
    validate_config(config_file)
```

### Configuration Testing
**Test your configuration with a sample correction**

```bash
#!/bin/bash
# test_config.sh - Test your text correction configuration

echo "🧪 Testing Text Correction Configuration..."

# Test text
TEST_TEXT="das ist ein test mit viele fehler und schlecht grammatik."

# Test correction
python3 -c "
from whisper_transcription_tool.module5_text_correction import LLMCorrector
import time

try:
    print('Loading model...')
    start = time.time()

    with LLMCorrector() as corrector:
        load_time = time.time() - start
        print(f'✅ Model loaded in {load_time:.1f}s')

        print('Testing correction...')
        result = corrector.correct_text('$TEST_TEXT')

        print(f'Original:  $TEST_TEXT')
        print(f'Corrected: {result}')
        print('✅ Configuration test successful!')

except Exception as e:
    print(f'❌ Configuration test failed: {e}')
    exit(1)
"

echo "✅ Configuration test completed!"
```

---

## 📊 Performance Benchmarks

### Benchmark Different Configurations
**Compare performance across different settings**

```python
#!/usr/bin/env python3
"""
Performance benchmark for different LeoLM configurations
"""

import time
import json
import psutil
from dataclasses import dataclass
from typing import List
from whisper_transcription_tool.module5_text_correction import LLMCorrector

@dataclass
class BenchmarkResult:
    config_name: str
    load_time: float
    correction_time: float
    chars_per_second: float
    memory_used_gb: float
    success: bool
    error: str = ""

def benchmark_config(config_name: str, config: dict, test_text: str) -> BenchmarkResult:
    """Benchmark a specific configuration."""

    start_memory = psutil.virtual_memory().used

    try:
        # Model loading
        load_start = time.time()
        corrector = LLMCorrector(
            model_path=config.get("model_path"),
            context_length=config.get("context_length", 2048)
        )
        corrector.load_model()
        load_time = time.time() - load_start

        # Correction
        correction_start = time.time()
        result = corrector.correct_text(
            test_text,
            correction_level=config.get("correction_level", "basic")
        )
        correction_time = time.time() - correction_start

        # Cleanup
        corrector.unload_model()

        # Metrics
        end_memory = psutil.virtual_memory().used
        memory_used = (end_memory - start_memory) / 1024**3
        chars_per_second = len(test_text) / correction_time

        return BenchmarkResult(
            config_name=config_name,
            load_time=load_time,
            correction_time=correction_time,
            chars_per_second=chars_per_second,
            memory_used_gb=memory_used,
            success=True
        )

    except Exception as e:
        return BenchmarkResult(
            config_name=config_name,
            load_time=0,
            correction_time=0,
            chars_per_second=0,
            memory_used_gb=0,
            success=False,
            error=str(e)
        )

def run_benchmark():
    """Run benchmarks for different configurations."""

    test_text = """Das ist ein längerer test text mit viele fehler und schlecht grammatik.
    Wir möchten sehen wie gut die verschiedene konfigurationen funktioniert und wie schnell sie sind.
    Diese text enthält absichtlich fehler damit wir die qualität der korrektur bewerten können."""

    configs = {
        "Speed Optimized": {
            "model_path": "~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",
            "context_length": 1024,
            "correction_level": "basic"
        },
        "Balanced": {
            "model_path": "~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",
            "context_length": 2048,
            "correction_level": "advanced"
        },
        "Quality Optimized": {
            "model_path": "~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",
            "context_length": 4096,
            "correction_level": "formal"
        }
    }

    print("🚀 Running LeoLM Configuration Benchmarks...\n")

    results = []
    for name, config in configs.items():
        print(f"Testing {name}...")
        result = benchmark_config(name, config, test_text)
        results.append(result)

        if result.success:
            print(f"  ✅ Load: {result.load_time:.1f}s, Correction: {result.correction_time:.1f}s")
            print(f"     Speed: {result.chars_per_second:.1f} chars/s, Memory: {result.memory_used_gb:.1f}GB")
        else:
            print(f"  ❌ Failed: {result.error}")
        print()

    # Summary
    print("📊 Benchmark Results Summary:")
    print("-" * 80)
    print(f"{'Config':<20} {'Load(s)':<8} {'Correct(s)':<10} {'Speed':<12} {'Memory(GB)':<10} {'Status'}")
    print("-" * 80)

    for r in results:
        status = "✅" if r.success else "❌"
        print(f"{r.config_name:<20} {r.load_time:<8.1f} {r.correction_time:<10.1f} {r.chars_per_second:<12.1f} {r.memory_used_gb:<10.1f} {status}")

if __name__ == "__main__":
    run_benchmark()
```

---

## 🎯 Recommended Configurations by Use Case

### Content Creator (YouTube, Podcast)
```json
{
  "text_correction": {
    "enabled": true,
    "model_path": "~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",
    "context_length": 2048,
    "correction_level": "advanced",
    "temperature": 0.3,
    "preserve_colloquial": true,
    "batch_size": 4,
    "enable_timestamps": true
  }
}
```

### Academic Research
```json
{
  "text_correction": {
    "enabled": true,
    "model_path": "~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",
    "context_length": 4096,
    "correction_level": "formal",
    "temperature": 0.25,
    "academic_style": true,
    "citation_preservation": true,
    "terminology_consistency": true
  }
}
```

### Business Documentation
```json
{
  "text_correction": {
    "enabled": true,
    "model_path": "~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",
    "context_length": 2048,
    "correction_level": "formal",
    "temperature": 0.2,
    "business_terminology": true,
    "professional_tone": true,
    "compliance_check": true
  }
}
```

---

**Version**: 1.0.0 | **Date**: September 2025
**Created by**: DocsNarrator Agent | **Website**: [www.goaiex.com](https://www.goaiex.com)

This configuration guide is continuously updated. Feedback and improvements welcome!