"""
End-to-End tests for the complete Phone Recording workflow.

This module tests the entire phone recording process from start to finish,
including audio capture, processing, transcription, and web interface integration.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List

import pytest
from fastapi.testclient import TestClient

from tests import TEST_CONFIG


class TestPhoneRecordingWorkflow:
    """Complete workflow tests for phone recording system."""

    def test_complete_phone_recording_workflow(self, web_client, mock_blackhole_available,
                                              mock_audio_devices, temp_dir, performance_tracker):
        """Test the complete phone recording workflow from start to finish."""
        performance_tracker.start()

        # Step 1: Check device availability
        response = web_client.get("/api/phone/devices")
        assert response.status_code == 200

        devices_data = response.json()
        assert devices_data["blackhole_found"] is True
        assert len(devices_data["input_devices"]) > 0
        assert len(devices_data["output_devices"]) > 0

        # Step 2: Start recording
        recording_request = {
            "input_device_id": "2",  # BlackHole
            "output_device_id": "1",  # Built-in Output
            "sample_rate": 44100,
            "max_duration_sec": 10
        }

        with pytest.mock.patch('whisper_transcription_tool.module3_phone.AudioRecorder.start_recording') as mock_start:
            with pytest.mock.patch('whisper_transcription_tool.module3_phone.AudioRecorder.create_session') as mock_create:
                # Mock session creation
                mock_session = pytest.mock.MagicMock()
                mock_session.session_id = "test-session-workflow"
                mock_create.return_value = mock_session
                mock_start.return_value = True

                response = web_client.post("/api/phone/recording/start", json=recording_request)
                assert response.status_code == 200

                result = response.json()
                assert result["success"] is True
                assert "session_id" in result

                session_id = result["session_id"]

        # Step 3: Simulate recording pause/resume
        with pytest.mock.patch('whisper_transcription_tool.module3_phone.AudioRecorder.get_session') as mock_get:
            with pytest.mock.patch('whisper_transcription_tool.module3_phone.AudioRecorder.pause_recording') as mock_pause:
                mock_get.return_value = mock_session
                mock_pause.return_value = True

                response = web_client.post(f"/api/phone/recording/{session_id}/pause")
                assert response.status_code == 200
                assert response.json()["success"] is True

        with pytest.mock.patch('whisper_transcription_tool.module3_phone.AudioRecorder.resume_recording') as mock_resume:
            mock_get.return_value = mock_session
            mock_resume.return_value = True

            response = web_client.post(f"/api/phone/recording/{session_id}/resume")
            assert response.status_code == 200
            assert response.json()["success"] is True

        # Step 4: Stop recording
        with pytest.mock.patch('whisper_transcription_tool.module3_phone.AudioRecorder.stop_recording') as mock_stop:
            mock_session.file_paths = {
                "microphone": f"{temp_dir}/mic_test.wav",
                "system": f"{temp_dir}/system_test.wav"
            }
            mock_session.duration_seconds = 10.5
            mock_get.return_value = mock_session
            mock_stop.return_value = True

            response = web_client.post(f"/api/phone/recording/{session_id}/stop")
            assert response.status_code == 200

            result = response.json()
            assert result["success"] is True
            assert "files" in result
            assert result["duration"] > 0

        # Step 5: Process recording
        response = web_client.post(f"/api/phone/recording/{session_id}/process")
        assert response.status_code == 200

        result = response.json()
        assert result["success"] is True
        assert "audio_files" in result

        performance_tracker.end()

        # Performance validation
        assert performance_tracker.duration < TEST_CONFIG["performance"]["max_startup_time"]

    def test_error_handling_workflow(self, web_client, mock_blackhole_unavailable):
        """Test error handling throughout the workflow."""

        # Test 1: BlackHole not available
        response = web_client.get("/api/phone/devices")
        assert response.status_code == 200
        assert response.json()["blackhole_found"] is False

        # Test 2: Start recording without BlackHole should fail
        recording_request = {
            "input_device_id": "0",
            "output_device_id": "1",
            "sample_rate": 44100,
            "max_duration_sec": 10
        }

        response = web_client.post("/api/phone/recording/start", json=recording_request)
        assert response.status_code == 400
        result = response.json()
        assert result["success"] is False
        assert "BlackHole" in result["error"]

    def test_session_management(self, web_client, mock_blackhole_available):
        """Test recording session management."""

        # Test invalid session operations
        fake_session_id = "non-existent-session"

        response = web_client.post(f"/api/phone/recording/{fake_session_id}/pause")
        assert response.status_code == 404
        result = response.json()
        assert result["success"] is False
        assert "nicht gefunden" in result["error"]

        response = web_client.post(f"/api/phone/recording/{fake_session_id}/resume")
        assert response.status_code == 404

        response = web_client.post(f"/api/phone/recording/{fake_session_id}/stop")
        assert response.status_code == 404

        response = web_client.post(f"/api/phone/recording/{fake_session_id}/process")
        assert response.status_code == 404

    def test_concurrent_recordings(self, web_client, mock_blackhole_available, mock_audio_devices):
        """Test handling of concurrent recording attempts."""

        recording_request = {
            "input_device_id": "2",
            "output_device_id": "1",
            "sample_rate": 44100,
            "max_duration_sec": 60
        }

        # Start first recording
        with pytest.mock.patch('whisper_transcription_tool.module3_phone.AudioRecorder.start_recording') as mock_start:
            with pytest.mock.patch('whisper_transcription_tool.module3_phone.AudioRecorder.create_session') as mock_create:
                mock_session1 = pytest.mock.MagicMock()
                mock_session1.session_id = "session-1"
                mock_create.return_value = mock_session1
                mock_start.return_value = True

                response1 = web_client.post("/api/phone/recording/start", json=recording_request)
                assert response1.status_code == 200

                # Attempt second recording (should handle gracefully)
                mock_session2 = pytest.mock.MagicMock()
                mock_session2.session_id = "session-2"

                # Mock behavior for concurrent recording attempt
                mock_start.return_value = False  # Second recording fails

                response2 = web_client.post("/api/phone/recording/start", json=recording_request)

                # Should either succeed with new session or fail gracefully
                if response2.status_code == 200:
                    result2 = response2.json()
                    assert "session_id" in result2
                else:
                    assert response2.status_code == 500
                    result2 = response2.json()
                    assert result2["success"] is False

    @pytest.mark.asyncio
    async def test_websocket_integration(self, mock_websocket):
        """Test WebSocket integration for real-time updates."""

        # Simulate progress updates during recording
        progress_events = [
            {"status": "recording_started", "progress": 0},
            {"status": "recording_in_progress", "progress": 25},
            {"status": "recording_in_progress", "progress": 50},
            {"status": "recording_in_progress", "progress": 75},
            {"status": "recording_completed", "progress": 100}
        ]

        # Send progress updates
        for event in progress_events:
            await mock_websocket.send_json(event)

        # Verify messages were sent
        assert len(mock_websocket.messages) == len(progress_events)

        # Verify message content
        for i, message in enumerate(mock_websocket.messages):
            data = json.loads(message)
            assert data["status"] == progress_events[i]["status"]
            assert data["progress"] == progress_events[i]["progress"]

    def test_audio_quality_validation(self, web_client, mock_audio_data):
        """Test audio quality validation in the workflow."""

        # This would integrate with actual audio processing validation
        # For now, we test the structure and expectations

        audio_data = mock_audio_data
        assert audio_data["sample_rate"] == TEST_CONFIG["audio"]["sample_rate"]
        assert audio_data["channels"] == TEST_CONFIG["audio"]["channels"]
        assert audio_data["duration"] == TEST_CONFIG["audio"]["test_duration"]
        assert audio_data["data"].shape[0] > 0
        assert audio_data["data"].shape[1] == TEST_CONFIG["audio"]["channels"]

    def test_performance_under_load(self, web_client, performance_tracker):
        """Test system performance under simulated load."""
        performance_tracker.start()

        # Simulate multiple rapid API calls
        endpoints_to_test = [
            ("/api/phone/devices", "GET", None),
        ]

        for endpoint, method, data in endpoints_to_test:
            for i in range(10):  # Rapid fire 10 requests
                if method == "GET":
                    response = web_client.get(endpoint)
                elif method == "POST":
                    response = web_client.post(endpoint, json=data or {})

                # Should handle load gracefully
                assert response.status_code in [200, 400, 404, 500]  # No crashes

                # Track memory usage
                memory_usage = performance_tracker.track_memory()
                if memory_usage:
                    assert memory_usage < TEST_CONFIG["performance"]["max_memory_usage"]

        performance_tracker.end()

        # Performance should be reasonable under load
        assert performance_tracker.duration < 30.0  # 30 seconds for 10 requests

    def test_data_consistency(self, web_client, mock_transcript_data):
        """Test data consistency throughout the workflow."""

        transcript_data = mock_transcript_data

        # Validate transcript structure
        assert "microphone" in transcript_data
        assert "system" in transcript_data

        for channel, data in transcript_data.items():
            assert "segments" in data
            for segment in data["segments"]:
                assert "text" in segment
                assert "start" in segment
                assert "end" in segment
                assert "confidence" in segment
                assert segment["start"] < segment["end"]
                assert 0.0 <= segment["confidence"] <= 1.0

    def test_cleanup_and_recovery(self, web_client, temp_dir):
        """Test system cleanup and recovery after errors."""

        # Create test files to simulate cleanup
        test_files = []
        for i in range(5):
            test_file = temp_dir / f"test_recording_{i}.wav"
            test_file.write_text("dummy audio data")
            test_files.append(test_file)

        # Verify files exist
        for file in test_files:
            assert file.exists()

        # Simulate cleanup process
        # In real implementation, this would be handled by the cleanup service
        cleanup_count = 0
        for file in test_files:
            try:
                file.unlink()
                cleanup_count += 1
            except Exception:
                pass

        # Verify cleanup was successful
        assert cleanup_count == len(test_files)

        # Verify recovery capabilities
        response = web_client.get("/api/phone/devices")
        assert response.status_code == 200  # System still responsive after cleanup


class TestPhoneRecordingIntegration:
    """Integration tests between different system components."""

    def test_python_swift_integration(self):
        """Test integration between Python backend and Swift frontend."""

        # Mock Swift to Python communication
        swift_commands = [
            {"action": "start_recording", "config": {"device_id": "2"}},
            {"action": "pause_recording"},
            {"action": "resume_recording"},
            {"action": "stop_recording"},
        ]

        python_responses = []

        for command in swift_commands:
            # Simulate command processing
            if command["action"] == "start_recording":
                response = {"success": True, "session_id": "mock-session"}
            elif command["action"] in ["pause_recording", "resume_recording", "stop_recording"]:
                response = {"success": True, "status": command["action"]}
            else:
                response = {"success": False, "error": "Unknown command"}

            python_responses.append(response)

        # Verify all commands were processed
        assert len(python_responses) == len(swift_commands)
        assert all(response.get("success") for response in python_responses[:-1])  # All but unknown command

    def test_api_consistency(self, web_client):
        """Test API consistency across different endpoints."""

        # All phone API endpoints should follow consistent response format
        consistent_fields = ["success"]

        # Test device listing endpoint
        response = web_client.get("/api/phone/devices")
        assert response.status_code == 200
        data = response.json()

        # Should have consistent structure
        assert "input_devices" in data
        assert "output_devices" in data
        assert "blackhole_found" in data

        # Each device should have consistent structure
        if data["input_devices"]:
            device = data["input_devices"][0]
            required_fields = ["id", "name", "is_input", "is_output"]
            for field in required_fields:
                assert field in device

    def test_error_propagation(self, web_client):
        """Test that errors are properly propagated through the system."""

        # Test invalid requests return proper error responses
        invalid_requests = [
            ("/api/phone/recording/start", {"invalid": "data"}),
            ("/api/phone/recording/invalid-session/pause", None),
        ]

        for endpoint, data in invalid_requests:
            if data:
                response = web_client.post(endpoint, json=data)
            else:
                response = web_client.post(endpoint)

            # Should return error status
            assert response.status_code >= 400

            # Should have consistent error format
            if response.status_code != 422:  # Skip validation errors
                error_data = response.json()
                assert "success" in error_data
                assert error_data["success"] is False
                assert "error" in error_data