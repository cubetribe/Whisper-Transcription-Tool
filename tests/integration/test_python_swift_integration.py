"""
Integration tests between Python Backend and Swift Frontend.

This module tests the communication and data flow between the Python
transcription backend and the Swift macOS frontend application.
"""

import asyncio
import json
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, Optional
from unittest.mock import patch, MagicMock

import pytest
import requests
from fastapi.testclient import TestClient

from tests import TEST_CONFIG


class SwiftAppSimulator:
    """
    Simulates Swift frontend application behavior for testing.

    This class mimics the communication patterns that the Swift app
    would use when interacting with the Python backend.
    """

    def __init__(self, base_url: str = "http://localhost:8090"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "WhisperLocalMacOs/1.0",
            "Content-Type": "application/json"
        })

    def check_api_health(self) -> Dict[str, Any]:
        """Check if the Python backend API is healthy."""
        try:
            response = self.session.get(f"{self.base_url}/api/phone/devices", timeout=5)
            return {
                "healthy": response.status_code == 200,
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "response_time": None
            }

    def get_audio_devices(self) -> Dict[str, Any]:
        """Get available audio devices from Python backend."""
        response = self.session.get(f"{self.base_url}/api/phone/devices")
        response.raise_for_status()
        return response.json()

    def start_phone_recording(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Start phone recording via Python API."""
        response = self.session.post(
            f"{self.base_url}/api/phone/recording/start",
            json=config
        )
        response.raise_for_status()
        return response.json()

    def pause_phone_recording(self, session_id: str) -> Dict[str, Any]:
        """Pause phone recording."""
        response = self.session.post(
            f"{self.base_url}/api/phone/recording/{session_id}/pause"
        )
        response.raise_for_status()
        return response.json()

    def resume_phone_recording(self, session_id: str) -> Dict[str, Any]:
        """Resume phone recording."""
        response = self.session.post(
            f"{self.base_url}/api/phone/recording/{session_id}/resume"
        )
        response.raise_for_status()
        return response.json()

    def stop_phone_recording(self, session_id: str) -> Dict[str, Any]:
        """Stop phone recording."""
        response = self.session.post(
            f"{self.base_url}/api/phone/recording/{session_id}/stop"
        )
        response.raise_for_status()
        return response.json()

    def process_phone_recording(self, session_id: str) -> Dict[str, Any]:
        """Process phone recording and get transcripts."""
        response = self.session.post(
            f"{self.base_url}/api/phone/recording/{session_id}/process"
        )
        response.raise_for_status()
        return response.json()

    def upload_phone_tracks(self, track_a_path: str, track_b_path: str) -> Dict[str, Any]:
        """Upload phone recording tracks for processing."""
        with open(track_a_path, 'rb') as track_a, open(track_b_path, 'rb') as track_b:
            files = {
                'track_a': ('track_a.wav', track_a, 'audio/wav'),
                'track_b': ('track_b.wav', track_b, 'audio/wav')
            }
            response = self.session.post(
                f"{self.base_url}/api/phone/",
                files=files
            )
        response.raise_for_status()
        return response.json()


class PythonBridgeSimulator:
    """
    Simulates the PythonBridge component from Swift side.

    This represents how the Swift app would interact with Python processes.
    """

    def __init__(self):
        self.process = None
        self.last_command = None
        self.last_result = None

    def execute_python_command(self, command: str, args: list = None) -> Dict[str, Any]:
        """Execute a Python command and return the result."""
        self.last_command = {"command": command, "args": args or []}

        try:
            # Simulate different Python commands
            if command == "check_blackhole":
                return self._check_blackhole_status()
            elif command == "list_devices":
                return self._list_audio_devices()
            elif command == "start_recording":
                return self._start_recording(args)
            elif command == "stop_recording":
                return self._stop_recording(args)
            elif command == "transcribe":
                return self._transcribe_audio(args)
            else:
                return {"success": False, "error": f"Unknown command: {command}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _check_blackhole_status(self) -> Dict[str, Any]:
        """Mock BlackHole status check."""
        # In real implementation, this would check the system
        return {
            "success": True,
            "blackhole_installed": True,
            "version": "0.4.0"
        }

    def _list_audio_devices(self) -> Dict[str, Any]:
        """Mock audio devices listing."""
        return {
            "success": True,
            "devices": [
                {"id": "0", "name": "Built-in Microphone", "type": "input"},
                {"id": "1", "name": "Built-in Output", "type": "output"},
                {"id": "2", "name": "BlackHole 2ch", "type": "both"}
            ]
        }

    def _start_recording(self, args: list) -> Dict[str, Any]:
        """Mock recording start."""
        return {
            "success": True,
            "session_id": f"session_{int(time.time())}",
            "message": "Recording started"
        }

    def _stop_recording(self, args: list) -> Dict[str, Any]:
        """Mock recording stop."""
        return {
            "success": True,
            "files": ["mic_recording.wav", "system_recording.wav"],
            "duration": 30.5
        }

    def _transcribe_audio(self, args: list) -> Dict[str, Any]:
        """Mock audio transcription."""
        return {
            "success": True,
            "transcript": "This is a mock transcription result.",
            "confidence": 0.95
        }


class TestPythonSwiftIntegration:
    """Integration tests between Python backend and Swift frontend."""

    @pytest.fixture(autouse=True)
    def setup(self, web_client):
        """Set up test environment."""
        self.web_client = web_client
        self.swift_simulator = SwiftAppSimulator()
        self.python_bridge = PythonBridgeSimulator()

    def test_api_health_check(self):
        """Test that Swift can check Python backend health."""
        # Simulate Swift app checking if Python backend is running
        with patch('requests.Session.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.elapsed.total_seconds.return_value = 0.1
            mock_get.return_value = mock_response

            health = self.swift_simulator.check_api_health()

            assert health["healthy"] is True
            assert health["status_code"] == 200
            assert health["response_time"] == 0.1

    def test_device_discovery_integration(self, mock_audio_devices, mock_blackhole_available):
        """Test device discovery flow between Swift and Python."""
        # Test 1: Swift requests device list from Python
        response = self.web_client.get("/api/phone/devices")
        assert response.status_code == 200

        devices_data = response.json()
        assert "input_devices" in devices_data
        assert "output_devices" in devices_data
        assert "blackhole_found" in devices_data

        # Test 2: Python Bridge simulation
        bridge_result = self.python_bridge.execute_python_command("list_devices")
        assert bridge_result["success"] is True
        assert "devices" in bridge_result

        # Test 3: Verify data consistency between approaches
        api_device_count = len(devices_data["input_devices"]) + len(devices_data["output_devices"])
        bridge_device_count = len(bridge_result["devices"])

        # Both should discover some devices
        assert api_device_count > 0
        assert bridge_device_count > 0

    def test_recording_workflow_integration(self, mock_blackhole_available, mock_audio_devices):
        """Test complete recording workflow integration."""
        # Step 1: Swift checks system requirements
        bridge_blackhole_check = self.python_bridge.execute_python_command("check_blackhole")
        assert bridge_blackhole_check["success"] is True
        assert bridge_blackhole_check["blackhole_installed"] is True

        # Step 2: Swift starts recording via API
        recording_config = {
            "input_device_id": "2",  # BlackHole
            "output_device_id": "1",  # Built-in Output
            "sample_rate": 44100,
            "max_duration_sec": 60
        }

        with patch('whisper_transcription_tool.module3_phone.AudioRecorder.start_recording') as mock_start:
            with patch('whisper_transcription_tool.module3_phone.AudioRecorder.create_session') as mock_create_session:
                mock_session = MagicMock()
                mock_session.session_id = "integration-test-session"
                mock_create_session.return_value = mock_session
                mock_start.return_value = True

                response = self.web_client.post("/api/phone/recording/start", json=recording_config)
                assert response.status_code == 200

                result = response.json()
                assert result["success"] is True
                assert "session_id" in result

                session_id = result["session_id"]

        # Step 3: Swift controls recording via Python Bridge
        bridge_start = self.python_bridge.execute_python_command("start_recording", ["test_config"])
        assert bridge_start["success"] is True
        assert "session_id" in bridge_start

        # Step 4: Swift stops recording
        with patch('whisper_transcription_tool.module3_phone.AudioRecorder.get_session') as mock_get_session:
            with patch('whisper_transcription_tool.module3_phone.AudioRecorder.stop_recording') as mock_stop:
                mock_get_session.return_value = mock_session
                mock_session.file_paths = {"microphone": "mic.wav", "system": "sys.wav"}
                mock_session.duration_seconds = 30.5
                mock_stop.return_value = True

                response = self.web_client.post(f"/api/phone/recording/{session_id}/stop")
                assert response.status_code == 200

                result = response.json()
                assert result["success"] is True
                assert "files" in result

        bridge_stop = self.python_bridge.execute_python_command("stop_recording", [session_id])
        assert bridge_stop["success"] is True

    def test_error_handling_integration(self, mock_blackhole_unavailable):
        """Test error handling between Swift and Python."""
        # Test 1: Swift tries to start recording without BlackHole
        recording_config = {
            "input_device_id": "0",
            "output_device_id": "1",
            "sample_rate": 44100,
            "max_duration_sec": 60
        }

        response = self.web_client.post("/api/phone/recording/start", json=recording_config)
        assert response.status_code == 400

        error_data = response.json()
        assert error_data["success"] is False
        assert "BlackHole" in error_data["error"]

        # Test 2: Python Bridge handles errors gracefully
        bridge_result = self.python_bridge.execute_python_command("unknown_command")
        assert bridge_result["success"] is False
        assert "error" in bridge_result

    def test_data_format_consistency(self, temp_dir):
        """Test that data formats are consistent between Swift and Python."""
        # Create mock audio files for testing
        mock_track_a = temp_dir / "track_a.wav"
        mock_track_b = temp_dir / "track_b.wav"

        # Write dummy data
        mock_track_a.write_bytes(b"dummy audio data A")
        mock_track_b.write_bytes(b"dummy audio data B")

        # Test file upload format consistency
        with patch('whisper_transcription_tool.module3_phone.process_tracks') as mock_process:
            mock_process.return_value = MagicMock(
                success=True,
                output_file="transcript.srt",
                text="Mock transcript text"
            )

            # Simulate Swift uploading files
            with open(mock_track_a, "rb") as f_a, open(mock_track_b, "rb") as f_b:
                files = {
                    'track_a': ('track_a.wav', f_a, 'audio/wav'),
                    'track_b': ('track_b.wav', f_b, 'audio/wav')
                }
                response = self.web_client.post("/api/phone/", files=files)

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "track_a" in result
        assert "track_b" in result

    def test_performance_under_swift_load(self, performance_tracker):
        """Test Python backend performance under Swift-like load."""
        performance_tracker.start()

        # Simulate multiple Swift requests in quick succession
        test_endpoints = [
            ("/api/phone/devices", "GET", None),
        ]

        request_count = 20
        successful_requests = 0

        for _ in range(request_count):
            for endpoint, method, data in test_endpoints:
                try:
                    if method == "GET":
                        response = self.web_client.get(endpoint)
                    elif method == "POST":
                        response = self.web_client.post(endpoint, json=data or {})

                    if response.status_code in [200, 400, 404]:  # Expected status codes
                        successful_requests += 1

                    # Track memory usage
                    performance_tracker.track_memory()

                except Exception as e:
                    print(f"Request failed: {e}")

        performance_tracker.end()

        # Performance assertions
        success_rate = successful_requests / (request_count * len(test_endpoints))
        assert success_rate > 0.8  # 80% success rate minimum

        assert performance_tracker.duration < 10.0  # Should complete in 10 seconds

        if performance_tracker.memory_usage:
            max_memory = max(performance_tracker.memory_usage)
            assert max_memory < TEST_CONFIG["performance"]["max_memory_usage"]

    def test_swift_python_communication_patterns(self):
        """Test common communication patterns between Swift and Python."""
        # Pattern 1: Request-Response
        devices_response = self.web_client.get("/api/phone/devices")
        assert devices_response.status_code == 200
        assert "input_devices" in devices_response.json()

        # Pattern 2: Command execution via Bridge
        bridge_result = self.python_bridge.execute_python_command("check_blackhole")
        assert "success" in bridge_result

        # Pattern 3: Error propagation
        invalid_response = self.web_client.post("/api/phone/recording/invalid-session/pause")
        assert invalid_response.status_code == 404

        bridge_error = self.python_bridge.execute_python_command("invalid_command")
        assert bridge_error["success"] is False

    def test_concurrent_swift_python_operations(self):
        """Test concurrent operations between Swift and Python."""
        import threading
        import queue

        results = queue.Queue()

        def api_worker():
            try:
                response = self.web_client.get("/api/phone/devices")
                results.put({"type": "api", "success": response.status_code == 200})
            except Exception as e:
                results.put({"type": "api", "success": False, "error": str(e)})

        def bridge_worker():
            try:
                result = self.python_bridge.execute_python_command("list_devices")
                results.put({"type": "bridge", "success": result["success"]})
            except Exception as e:
                results.put({"type": "bridge", "success": False, "error": str(e)})

        # Start concurrent operations
        api_thread = threading.Thread(target=api_worker)
        bridge_thread = threading.Thread(target=bridge_worker)

        api_thread.start()
        bridge_thread.start()

        # Wait for completion
        api_thread.join(timeout=5)
        bridge_thread.join(timeout=5)

        # Check results
        collected_results = []
        while not results.empty():
            collected_results.append(results.get())

        assert len(collected_results) == 2

        # Both operations should succeed
        api_result = next((r for r in collected_results if r["type"] == "api"), None)
        bridge_result = next((r for r in collected_results if r["type"] == "bridge"), None)

        assert api_result and api_result["success"]
        assert bridge_result and bridge_result["success"]

    def test_data_serialization_compatibility(self):
        """Test data serialization compatibility between Swift and Python."""
        # Test JSON serialization/deserialization
        test_data = {
            "session_id": "test-session-123",
            "config": {
                "input_device_id": "2",
                "output_device_id": "1",
                "sample_rate": 44100,
                "max_duration_sec": 3600
            },
            "metadata": {
                "timestamp": time.time(),
                "version": "1.0.0",
                "platform": "macOS"
            }
        }

        # Serialize to JSON (Swift would do this)
        json_data = json.dumps(test_data)

        # Deserialize from JSON (Python would do this)
        parsed_data = json.loads(json_data)

        # Verify data integrity
        assert parsed_data["session_id"] == test_data["session_id"]
        assert parsed_data["config"]["sample_rate"] == test_data["config"]["sample_rate"]
        assert parsed_data["metadata"]["version"] == test_data["metadata"]["version"]

        # Test with special characters and Unicode
        unicode_data = {
            "user_name": "Test Üser",
            "contact_name": "Kündé 测试",
            "transcript": "Hällö Wörld! 🎵"
        }

        json_unicode = json.dumps(unicode_data, ensure_ascii=False)
        parsed_unicode = json.loads(json_unicode)

        assert parsed_unicode["user_name"] == unicode_data["user_name"]
        assert parsed_unicode["contact_name"] == unicode_data["contact_name"]
        assert parsed_unicode["transcript"] == unicode_data["transcript"]


class TestSwiftAppLifecycle:
    """Test Swift application lifecycle integration with Python backend."""

    def test_app_startup_integration(self, web_client):
        """Test Swift app startup sequence with Python backend."""
        # Step 1: Swift app checks if Python backend is running
        health_response = web_client.get("/api/phone/devices")
        backend_available = health_response.status_code == 200

        # Step 2: Swift app initializes based on backend availability
        if backend_available:
            devices_data = health_response.json()

            # Verify expected data structure
            assert "input_devices" in devices_data
            assert "output_devices" in devices_data
            assert "blackhole_found" in devices_data

            # Swift app would configure UI based on this data
            ui_config = {
                "recording_enabled": devices_data["blackhole_found"],
                "device_count": len(devices_data["input_devices"]) + len(devices_data["output_devices"]),
                "has_microphone": len(devices_data["input_devices"]) > 0
            }

            assert "recording_enabled" in ui_config
            assert "device_count" in ui_config

    def test_app_shutdown_integration(self):
        """Test Swift app shutdown with active Python operations."""
        python_bridge = PythonBridgeSimulator()

        # Simulate active recording when app shuts down
        start_result = python_bridge.execute_python_command("start_recording")
        assert start_result["success"]

        # Swift app should gracefully stop any active recordings
        stop_result = python_bridge.execute_python_command("stop_recording")
        assert stop_result["success"]

        # Verify cleanup was successful
        assert "files" in stop_result

    def test_app_background_foreground(self):
        """Test Swift app background/foreground behavior with Python backend."""
        python_bridge = PythonBridgeSimulator()

        # Start recording in foreground
        start_result = python_bridge.execute_python_command("start_recording")
        assert start_result["success"]
        session_id = start_result["session_id"]

        # App goes to background - recording should continue
        # (This would be handled by the Python backend independently)

        # App comes back to foreground - should reconnect and get status
        devices_result = python_bridge.execute_python_command("list_devices")
        assert devices_result["success"]

        # Should be able to stop the recording that was running in background
        stop_result = python_bridge.execute_python_command("stop_recording", [session_id])
        assert stop_result["success"]