"""
Pytest configuration and fixtures for the test suite.

This module provides common test fixtures, utilities, and configuration
for all tests in the Whisper Transcription Tool test suite.
"""

import pytest
import tempfile
import os
import sys
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, Generator, AsyncGenerator

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def temp_directory() -> Generator[Path, None, None]:
    """Provides a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_config() -> Dict[str, Any]:
    """Provides a mock configuration dictionary."""
    return {
        "whisper": {
            "model_path": "/tmp/test_models",
            "default_model": "large-v3-turbo"
        },
        "output": {
            "default_directory": "/tmp/test_output"
        },
        "text_correction": {
            "leolm_model_path": "/tmp/test_leolm.gguf",
            "enabled": True,
            "default_level": "basic",
            "default_language": "de"
        },
        "disk_management": {
            "max_disk_usage_percent": 90,
            "min_required_space_gb": 2.0,
            "enable_auto_cleanup": True,
            "cleanup_age_hours": 24
        }
    }


@pytest.fixture
def mock_leolm_model() -> Mock:
    """Provides a mock LeoLM model for testing."""
    mock_model = Mock()
    mock_model.return_value = {"choices": [{"text": "Corrected text"}]}
    mock_model.n_ctx.return_value = 2048
    mock_model.n_vocab.return_value = 32000
    mock_model.tokenize.return_value = [1, 2, 3, 4]
    return mock_model


@pytest.fixture
def sample_text_short() -> str:
    """Provides short sample text for testing."""
    return "Das ist ein Test text mit fehler."


@pytest.fixture
def sample_text_long() -> str:
    """Provides long sample text for chunking tests."""
    return "Das ist ein sehr langer Test text. " * 100


@pytest.fixture
def sample_srt_content() -> str:
    """Provides sample SRT content for testing."""
    return """1
00:00:00,000 --> 00:00:05,000
Dies ist der erste Untertitel.

2
00:00:05,000 --> 00:00:10,000
Dies ist der zweite Untertitel.

3
00:00:10,000 --> 00:00:15,000
Dies ist der dritte Untertitel.
"""


@pytest.fixture
def sample_json_transcription() -> Dict[str, Any]:
    """Provides sample JSON transcription for testing."""
    return {
        "segments": [
            {
                "start": 0.0,
                "end": 5.0,
                "text": "Dies ist der erste Untertitel."
            },
            {
                "start": 5.0,
                "end": 10.0,
                "text": "Dies ist der zweite Untertitel."
            },
            {
                "start": 10.0,
                "end": 15.0,
                "text": "Dies ist der dritte Untertitel."
            }
        ]
    }


@pytest.fixture
def mock_whisper_process() -> Mock:
    """Provides a mock Whisper process for testing."""
    mock_process = Mock()
    mock_process.pid = 12345
    mock_process.poll.return_value = None  # Running
    mock_process.terminate = Mock()
    mock_process.kill = Mock()
    mock_process.communicate.return_value = (b"Mock output", b"")
    mock_process.returncode = 0
    return mock_process


@pytest.fixture
def mock_llama_cpp() -> Mock:
    """Provides a mock llama-cpp-python module for testing."""
    mock_llama_cpp = Mock()
    mock_model = Mock()
    mock_model.return_value = {"choices": [{"text": "Corrected text"}]}
    mock_model.n_ctx.return_value = 2048
    mock_model.n_vocab.return_value = 32000
    mock_model.tokenize.return_value = [1, 2, 3, 4]
    mock_llama_cpp.Llama.return_value = mock_model
    return mock_llama_cpp


@pytest.fixture
def temp_model_file() -> Generator[str, None, None]:
    """Creates a temporary model file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.gguf', delete=False) as temp_file:
        temp_file.write(b"fake model data")
        temp_file_path = temp_file.name

    yield temp_file_path

    # Cleanup
    if os.path.exists(temp_file_path):
        os.unlink(temp_file_path)


@pytest.fixture
def mock_fastapi_app():
    """Provides a mock FastAPI app for testing endpoints."""
    from fastapi.testclient import TestClient
    from src.whisper_transcription_tool.web import app
    return TestClient(app)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_websocket():
    """Provides a mock WebSocket for testing."""
    mock_ws = Mock()
    mock_ws.accept = AsyncMagicMock()
    mock_ws.send_text = AsyncMagicMock()
    mock_ws.send_json = AsyncMagicMock()
    mock_ws.receive_text = AsyncMagicMock()
    mock_ws.receive_json = AsyncMagicMock()
    return mock_ws


class AsyncMagicMock(MagicMock):
    """MagicMock that supports async methods."""
    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


@pytest.fixture
def mock_progress_callback():
    """Provides a mock progress callback for testing."""
    return Mock()


@pytest.fixture
def mock_memory_stats():
    """Provides mock memory statistics for testing."""
    return {
        "total_gb": 16.0,
        "available_gb": 8.0,
        "used_gb": 8.0,
        "percent_used": 50.0,
        "free_gb": 8.0
    }


@pytest.fixture
def mock_psutil_virtual_memory():
    """Provides a mock psutil virtual memory object."""
    mock_memory = Mock()
    mock_memory.total = 16 * 1024**3  # 16GB in bytes
    mock_memory.available = 8 * 1024**3  # 8GB available
    mock_memory.used = 8 * 1024**3  # 8GB used
    mock_memory.percent = 50.0
    mock_memory.free = 8 * 1024**3  # 8GB free
    return mock_memory


@pytest.fixture
def performance_test_data():
    """Provides test data for performance testing."""
    return {
        "small_text": "Short test text.",
        "medium_text": "Medium length test text. " * 50,
        "large_text": "Large test text for performance testing. " * 500,
        "expected_processing_times": {
            "small": 0.1,  # seconds
            "medium": 1.0,  # seconds
            "large": 10.0   # seconds
        }
    }


# Test markers for different test categories
pytest_plugins = ["pytest_asyncio"]

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "requires_model: Tests that require actual model files")
    config.addinivalue_line("markers", "requires_internet: Tests that require internet connection")


# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle markers."""
    if config.getoption("--no-slow"):
        skip_slow = pytest.mark.skip(reason="--no-slow option given")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--no-slow", action="store_true", default=False,
        help="skip slow tests"
    )
    parser.addoption(
        "--run-integration", action="store_true", default=False,
        help="run integration tests"
    )
    parser.addoption(
        "--run-performance", action="store_true", default=False,
        help="run performance tests"
    )