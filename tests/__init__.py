"""
Test suite for Whisper Transcription Tool.

This package contains comprehensive tests for:
- Unit tests for individual components
- Integration tests between modules
- End-to-End tests for complete workflows
- Audio system tests for hardware integration
- Web interface tests for API and UI
"""

__version__ = "1.0.0"

# Test configuration
TEST_CONFIG = {
    "audio": {
        "sample_rate": 44100,
        "channels": 2,
        "bit_depth": 16,
        "test_duration": 10.0  # seconds
    },
    "blackhole": {
        "required_version": "0.4.0",
        "device_name": "BlackHole 2ch"
    },
    "performance": {
        "max_startup_time": 5.0,  # seconds
        "max_processing_time": 30.0,  # seconds per minute of audio
        "max_memory_usage": 1024  # MB
    },
    "web": {
        "timeout": 30.0,
        "port_range": (8090, 8099)
    }
}

# Mock data paths
MOCK_DATA_DIR = "tests/mock_data"
MOCK_AUDIO_DIR = f"{MOCK_DATA_DIR}/audio"
MOCK_TRANSCRIPTS_DIR = f"{MOCK_DATA_DIR}/transcripts"