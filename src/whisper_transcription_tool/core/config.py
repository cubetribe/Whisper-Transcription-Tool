"""
Configuration management for the Whisper Transcription Tool.
"""

import json
import logging
import os
import platform
import psutil
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)

# Finde Projekt-Wurzelverzeichnis, um relative Pfade zu verwenden
def find_project_root():
    """Find the project root directory."""
    # Beginne mit dem aktuellen Verzeichnis der Datei
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Navigiere nach oben bis zum Projektverzeichnis
    # Wir suchen nach dem 'src' Verzeichnis als Indikator
    while current_dir and not current_dir.endswith('src'):
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            # Wir haben das Root-Verzeichnis erreicht ohne 'src' zu finden
            return str(Path.home())
        current_dir = parent_dir
    
    # Gehe ein Level hoeher vom 'src' Verzeichnis
    return os.path.dirname(current_dir)

# Projektverzeichnis ermitteln für relative Pfade
PROJECT_ROOT = find_project_root()

DEFAULT_CONFIG = {
    "whisper": {
        "model_path": os.path.join(PROJECT_ROOT, "models"),
        "default_model": "large-v3-turbo",  # Using large-v3-turbo as specified by user
        "threads": 4,
    },
    "ffmpeg": {
        "binary_path": "/opt/homebrew/bin/ffmpeg",
        "audio_format": "wav",
        "sample_rate": 16000,
    },
    "output": {
        "default_directory": os.path.join(PROJECT_ROOT, "transcriptions"),
        "temp_directory": os.path.join(PROJECT_ROOT, "transcriptions", "temp"),
        "default_format": "txt",
    },
    "chunking": {
        "enabled": True,
        "max_duration_minutes": 20,
        "overlap_seconds": 10,
        "auto_detect_threshold": 20,  # Auto-enable for files > 20 minutes
        "format": "wav"
    },
    "chatbot": {
        "mode": "local",
        "model": "mistral-7b",
    },
    "disk_management": {
        "min_required_space_gb": 2.0,      # Mindestens 2 GB freier Speicherplatz
        "max_disk_usage_percent": 90,     # Maximale Speichernutzung in Prozent
        "enable_auto_cleanup": True,      # Automatische Bereinigung aktivieren
        "cleanup_age_hours": 24,         # Dateien älter als 24 Stunden bereinigen
        "batch_warning_threshold_gb": 5.0 # Mindestens 5 GB für Stapelverarbeitung
    },
    "cleanup": {
        "enabled": True,
        "auto_cleanup_after_transcription": True,  # Automatisch nach Transkription aufräumen
        "cleanup_age_hours": 24,  # Dateien älter als 24 Stunden löschen
        "keep_transcriptions": True,  # Transkriptions-Dateien behalten (.txt, .srt, etc.)
        "cleanup_chunks": True,  # Chunk-Verzeichnisse löschen
        "max_temp_size_gb": 5.0  # Maximale Temp-Verzeichnisgröße bevor automatisches Cleanup
    },
    "text_correction": {
        "enabled": False,
        "model_path": "~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",
        "context_length": 2048,
        "temperature": 0.3,
        "correction_level": "standard",  # light, standard, strict
        "keep_original": True,
        "auto_batch": True,
        "max_parallel_jobs": 1,
        "dialect_normalization": False,
        "chunk_overlap_sentences": 1,
        "memory_threshold_gb": 6.0,
        "monitoring_enabled": False,
        "gpu_acceleration": "auto",  # auto, metal, cuda, cpu
        "fallback_on_error": True,
        "platform_optimization": {
            "macos_metal": True,
            "cuda_support": False,
            "cpu_threads": "auto"
        }
    },
}


def _expand_path(path: str) -> str:
    """Expand user home directory and environment variables in path."""
    return os.path.expanduser(os.path.expandvars(path))


def _detect_platform_capabilities() -> Dict[str, Any]:
    """Detect platform-specific GPU capabilities."""
    capabilities = {
        "macos_metal": False,
        "cuda_support": False,
        "cpu_threads": os.cpu_count() or 4
    }

    system = platform.system()
    if system == "Darwin":  # macOS
        # Check for Metal support (available on macOS 10.11+)
        try:
            import subprocess
            result = subprocess.run(
                ["system_profiler", "SPDisplaysDataType"],
                capture_output=True, text=True, timeout=10
            )
            capabilities["macos_metal"] = "Metal" in result.stdout
        except Exception:
            # Assume Metal is available on modern macOS
            capabilities["macos_metal"] = True
    elif system == "Linux":
        # Check for NVIDIA GPU and CUDA
        try:
            import subprocess
            result = subprocess.run(
                ["nvidia-smi"],
                capture_output=True, text=True, timeout=5
            )
            capabilities["cuda_support"] = result.returncode == 0
        except Exception:
            capabilities["cuda_support"] = False

    return capabilities


def is_correction_available(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Check if text correction is available and properly configured.

    Args:
        config: Configuration dictionary (if None, loads default config)

    Returns:
        Dict with availability status and details
    """
    if config is None:
        config = load_config()

    correction_config = config.get("text_correction", {})

    # Check if feature is enabled
    if not correction_config.get("enabled", False):
        return {
            "available": False,
            "reason": "text_correction_disabled",
            "message": "Text correction is disabled in configuration",
            "details": {}
        }

    # Expand model path
    model_path = _expand_path(correction_config.get("model_path", ""))

    # Check if model file exists
    if not os.path.exists(model_path):
        return {
            "available": False,
            "reason": "model_not_found",
            "message": f"LeoLM model not found at: {model_path}",
            "details": {
                "expected_path": model_path,
                "suggestion": "Download LeoLM-hesseianai-13b-chat.Q4_K_M.gguf and place it in the models directory"
            }
        }

    # Check available RAM
    memory_info = psutil.virtual_memory()
    available_gb = memory_info.available / (1024**3)
    required_gb = correction_config.get("memory_threshold_gb", 6.0)

    if available_gb < required_gb:
        return {
            "available": False,
            "reason": "insufficient_memory",
            "message": f"Insufficient RAM for text correction (required: {required_gb}GB, available: {available_gb:.1f}GB)",
            "details": {
                "required_gb": required_gb,
                "available_gb": round(available_gb, 1),
                "total_gb": round(memory_info.total / (1024**3), 1)
            }
        }

    # Detect platform capabilities
    platform_caps = _detect_platform_capabilities()

    return {
        "available": True,
        "reason": "ready",
        "message": "Text correction is available and ready",
        "details": {
            "model_path": model_path,
            "model_size_mb": round(os.path.getsize(model_path) / (1024**2), 1),
            "available_memory_gb": round(available_gb, 1),
            "required_memory_gb": required_gb,
            "platform_capabilities": platform_caps,
            "correction_level": correction_config.get("correction_level", "standard"),
            "gpu_acceleration": correction_config.get("gpu_acceleration", "auto")
        }
    }


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from file or use default configuration.
    
    Args:
        config_path: Path to configuration file (JSON or YAML)
        
    Returns:
        Dict containing configuration
    """
    config = DEFAULT_CONFIG.copy()
    
    # Check for config file in default locations if not specified
    if not config_path:
        default_locations = [
            Path.home() / ".whisper_tool.json",
            Path.home() / ".whisper_tool.yaml",
            Path.home() / ".whisper_tool.yml",
            Path.home() / ".config" / "whisper_tool" / "config.json",
            Path.home() / ".config" / "whisper_tool" / "config.yaml",
        ]
        
        for path in default_locations:
            if path.exists():
                config_path = str(path)
                break
    
    # Load config from file if it exists
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                if config_path.endswith(('.yaml', '.yml')):
                    user_config = yaml.safe_load(f)
                else:
                    user_config = json.load(f)
                
                # Update config with user settings
                _update_nested_dict(config, user_config)
                logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
    else:
        logger.info("Using default configuration")
    
    # Create directories if they don't exist
    os.makedirs(config["whisper"]["model_path"], exist_ok=True)
    os.makedirs(config["output"]["default_directory"], exist_ok=True)

    # Validate and migrate configuration
    config = validate_and_migrate_config(config)

    return config


def save_config(config: Dict[str, Any], config_path: str) -> bool:
    """
    Save configuration to file.
    
    Args:
        config: Configuration dictionary
        config_path: Path to save configuration file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)
        
        with open(config_path, 'w') as f:
            if config_path.endswith(('.yaml', '.yml')):
                yaml.dump(config, f, default_flow_style=False)
            else:
                json.dump(config, f, indent=4)
                
        logger.info(f"Saved configuration to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving configuration to {config_path}: {e}")
        return False


def _update_nested_dict(d: Dict[str, Any], u: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update nested dictionary recursively.
    
    Args:
        d: Dictionary to update
        u: Dictionary with updates
        
    Returns:
        Updated dictionary
    """
    for k, v in u.items():
        if isinstance(v, dict) and k in d and isinstance(d[k], dict):
            _update_nested_dict(d[k], v)
        else:
            d[k] = v
    return d


def validate_and_migrate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and migrate configuration to ensure compatibility.

    Args:
        config: Configuration dictionary to validate

    Returns:
        Validated and migrated configuration
    """
    # Ensure text_correction section exists
    if "text_correction" not in config:
        config["text_correction"] = DEFAULT_CONFIG["text_correction"].copy()
        logger.info("Added missing text_correction configuration section")

    # Validate text_correction configuration
    correction_config = config["text_correction"]
    default_correction = DEFAULT_CONFIG["text_correction"]

    # Add missing keys with defaults
    for key, default_value in default_correction.items():
        if key not in correction_config:
            correction_config[key] = default_value
            logger.debug(f"Added missing text_correction.{key} with default value")

    # Validate correction_level
    valid_levels = ["light", "standard", "strict"]
    if correction_config.get("correction_level") not in valid_levels:
        logger.warning(f"Invalid correction_level '{correction_config.get('correction_level')}', using 'standard'")
        correction_config["correction_level"] = "standard"

    # Validate gpu_acceleration
    valid_gpu = ["auto", "metal", "cuda", "cpu"]
    if correction_config.get("gpu_acceleration") not in valid_gpu:
        logger.warning(f"Invalid gpu_acceleration '{correction_config.get('gpu_acceleration')}', using 'auto'")
        correction_config["gpu_acceleration"] = "auto"

    # Update platform optimization based on current platform
    platform_caps = _detect_platform_capabilities()
    correction_config["platform_optimization"].update(platform_caps)

    # Expand model path
    if "model_path" in correction_config:
        correction_config["model_path"] = _expand_path(correction_config["model_path"])

    return config


def print_correction_status(config: Optional[Dict[str, Any]] = None):
    """
    Print detailed status information about text correction availability.

    Args:
        config: Configuration dictionary (if None, loads default config)
    """
    status = is_correction_available(config)

    print("\n" + "="*60)
    print("TEXT CORRECTION STATUS")
    print("="*60)

    if status["available"]:
        print("✅ Status: AVAILABLE")
        print(f"📝 Message: {status['message']}")

        details = status["details"]
        print(f"\n📍 Model Path: {details['model_path']}")
        print(f"💾 Model Size: {details['model_size_mb']} MB")
        print(f"🧠 Available Memory: {details['available_memory_gb']} GB")
        print(f"⚠️  Required Memory: {details['required_memory_gb']} GB")
        print(f"🎯 Correction Level: {details['correction_level']}")
        print(f"🔧 GPU Acceleration: {details['gpu_acceleration']}")

        caps = details["platform_capabilities"]
        print(f"\n🖥️  Platform Capabilities:")
        print(f"   • macOS Metal: {'✅' if caps['macos_metal'] else '❌'}")
        print(f"   • CUDA Support: {'✅' if caps['cuda_support'] else '❌'}")
        print(f"   • CPU Threads: {caps['cpu_threads']}")

    else:
        print("❌ Status: NOT AVAILABLE")
        print(f"⚠️  Reason: {status['reason']}")
        print(f"📝 Message: {status['message']}")

        if status["details"]:
            details = status["details"]
            if "expected_path" in details:
                print(f"\n📍 Expected Path: {details['expected_path']}")
            if "suggestion" in details:
                print(f"💡 Suggestion: {details['suggestion']}")
            if "required_gb" in details and "available_gb" in details:
                print(f"\n💾 Memory Status:")
                print(f"   • Required: {details['required_gb']} GB")
                print(f"   • Available: {details['available_gb']} GB")
                if "total_gb" in details:
                    print(f"   • Total: {details['total_gb']} GB")

    print("="*60 + "\n")
