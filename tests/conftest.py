"""
PyTest configuration and fixtures for all tests.
"""

import asyncio
import json
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Dict, Generator, Optional
from unittest.mock import MagicMock, patch

import pytest
import numpy as np
from fastapi.testclient import TestClient

# Import test configuration
from tests import TEST_CONFIG, MOCK_DATA_DIR

# Import main application components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from whisper_transcription_tool.web import app
from whisper_transcription_tool.core.config import load_config
from whisper_transcription_tool.module3_phone.models import RecordingConfig, RecordingSession


@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration."""
    return TEST_CONFIG


@pytest.fixture(scope="session")
def mock_data_dir():
    """Provide mock data directory path."""
    return Path(__file__).parent / "mock_data"


@pytest.fixture(scope="function")
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture(scope="function")
def web_client():
    """Create a test client for the FastAPI web application."""
    return TestClient(app)


@pytest.fixture(scope="function")
def mock_audio_data():
    """Generate mock audio data for testing."""
    sample_rate = TEST_CONFIG["audio"]["sample_rate"]
    duration = TEST_CONFIG["audio"]["test_duration"]
    channels = TEST_CONFIG["audio"]["channels"]

    # Generate stereo sine wave test signal
    t = np.linspace(0, duration, int(sample_rate * duration))
    left_channel = np.sin(2 * np.pi * 440 * t)  # 440 Hz tone
    right_channel = np.sin(2 * np.pi * 880 * t)  # 880 Hz tone

    # Combine channels
    audio_data = np.column_stack((left_channel, right_channel))

    return {
        "data": audio_data,
        "sample_rate": sample_rate,
        "channels": channels,
        "duration": duration
    }


@pytest.fixture(scope="function")
def mock_recording_session():
    """Create a mock recording session for testing."""
    session = RecordingSession(
        session_id="test-session-123",
        config=RecordingConfig(
            input_device_id="test-mic",
            output_device_id="test-speakers",
            sample_rate=44100,
            max_duration_sec=60,
            output_directory="/tmp/test_recordings"
        )
    )

    # Mock file paths
    session.file_paths = {
        "microphone": "/tmp/test_recordings/mic_test.wav",
        "system": "/tmp/test_recordings/system_test.wav"
    }

    session.duration_seconds = 30.5
    session.start_time = time.time()

    return session


@pytest.fixture(scope="function")
def mock_transcript_data():
    """Provide mock transcript data for testing."""
    return {
        "microphone": {
            "segments": [
                {
                    "text": "Hello, this is a test recording from the microphone.",
                    "start": 0.0,
                    "end": 3.5,
                    "confidence": 0.95
                },
                {
                    "text": "Can you hear me clearly?",
                    "start": 4.0,
                    "end": 6.0,
                    "confidence": 0.92
                }
            ]
        },
        "system": {
            "segments": [
                {
                    "text": "Yes, I can hear you perfectly.",
                    "start": 6.5,
                    "end": 8.5,
                    "confidence": 0.93
                },
                {
                    "text": "The audio quality is excellent.",
                    "start": 9.0,
                    "end": 11.0,
                    "confidence": 0.89
                }
            ]
        }
    }


@pytest.fixture(scope="function")
def mock_blackhole_available():
    """Mock BlackHole availability."""
    with patch('whisper_transcription_tool.module3_phone.DeviceManager.is_blackhole_installed') as mock:
        mock.return_value = True
        yield mock


@pytest.fixture(scope="function")
def mock_blackhole_unavailable():
    """Mock BlackHole being unavailable."""
    with patch('whisper_transcription_tool.module3_phone.DeviceManager.is_blackhole_installed') as mock:
        mock.return_value = False
        yield mock


@pytest.fixture(scope="function")
def mock_audio_devices():
    """Mock audio device list."""
    devices = [
        {
            "id": "0",
            "name": "Built-in Microphone",
            "is_input": True,
            "is_output": False,
            "sample_rate": 44100,
            "channels": 1
        },
        {
            "id": "1",
            "name": "Built-in Output",
            "is_input": False,
            "is_output": True,
            "sample_rate": 44100,
            "channels": 2
        },
        {
            "id": "2",
            "name": "BlackHole 2ch",
            "is_input": True,
            "is_output": True,
            "sample_rate": 44100,
            "channels": 2
        }
    ]

    with patch('whisper_transcription_tool.module3_phone.DeviceManager.list_devices') as mock:
        mock.return_value = devices
        yield devices


@pytest.fixture(scope="function")
def mock_whisper_transcription():
    """Mock Whisper transcription process."""
    def mock_transcribe(audio_path, model="large-v3-turbo", language=None):
        # Return mock transcription result
        return {
            "segments": [
                {
                    "text": "This is a mock transcription result.",
                    "start": 0.0,
                    "end": 3.0,
                    "confidence": 0.95
                }
            ],
            "language": language or "en"
        }

    with patch('whisper_transcription_tool.module1_transcribe.transcribe_audio') as mock:
        mock.side_effect = mock_transcribe
        yield mock


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment before each test."""
    # Ensure mock data directory exists
    os.makedirs(MOCK_DATA_DIR, exist_ok=True)
    os.makedirs(f"{MOCK_DATA_DIR}/audio", exist_ok=True)
    os.makedirs(f"{MOCK_DATA_DIR}/transcripts", exist_ok=True)

    yield

    # Cleanup after test if needed
    pass


class MockWebSocket:
    """Mock WebSocket for testing real-time communication."""

    def __init__(self):
        self.messages = []
        self.closed = False

    async def send_text(self, message: str):
        if not self.closed:
            self.messages.append(message)

    async def send_json(self, data: dict):
        if not self.closed:
            self.messages.append(json.dumps(data))

    async def receive_text(self):
        if self.messages:
            return self.messages.pop(0)
        return None

    async def close(self):
        self.closed = True


@pytest.fixture(scope="function")
def mock_websocket():
    """Provide a mock WebSocket for testing."""
    return MockWebSocket()


# Performance testing helpers
class PerformanceTracker:
    """Track performance metrics during tests."""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.memory_usage = []

    def start(self):
        self.start_time = time.perf_counter()

    def end(self):
        self.end_time = time.perf_counter()

    @property
    def duration(self):
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

    def track_memory(self):
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_usage.append(memory_mb)
            return memory_mb
        except ImportError:
            return None


@pytest.fixture(scope="function")
def performance_tracker():
    """Provide a performance tracker for tests."""
    return PerformanceTracker()


# Error simulation helpers
@pytest.fixture(scope="function")
def simulate_network_error():
    """Simulate network errors for testing error handling."""
    import requests

    def mock_request(*args, **kwargs):
        raise requests.ConnectionError("Simulated network error")

    with patch('requests.get', side_effect=mock_request):
        with patch('requests.post', side_effect=mock_request):
            yield


@pytest.fixture(scope="function")
def simulate_disk_full():
    """Simulate disk full error for testing."""
    def mock_write(*args, **kwargs):
        raise OSError(28, "No space left on device")

    with patch('builtins.open', side_effect=mock_write):
        yield