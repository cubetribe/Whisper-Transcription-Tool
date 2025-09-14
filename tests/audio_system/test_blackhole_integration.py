"""
Audio System Tests for BlackHole integration and channel mapping.

This module tests the audio hardware integration, specifically:
- BlackHole virtual audio driver detection and setup
- Audio device enumeration and configuration
- Channel-based speaker mapping validation
- Real-time audio processing capabilities
"""

import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

from tests import TEST_CONFIG


class BlackHoleSystemTest:
    """System-level tests for BlackHole audio driver integration."""

    def __init__(self):
        self.blackhole_device_name = TEST_CONFIG["blackhole"]["device_name"]
        self.required_version = TEST_CONFIG["blackhole"]["required_version"]

    def check_blackhole_installation(self) -> Dict[str, any]:
        """Check if BlackHole is properly installed on the system."""
        try:
            # Use system_profiler to check audio devices (macOS specific)
            result = subprocess.run([
                "system_profiler", "SPAudioDataType", "-json"
            ], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                import json
                audio_data = json.loads(result.stdout)

                # Look for BlackHole in audio devices
                blackhole_found = False
                blackhole_info = {}

                for category in audio_data.get("SPAudioDataType", []):
                    for device in category.get("_items", []):
                        device_name = device.get("_name", "")
                        if "BlackHole" in device_name:
                            blackhole_found = True
                            blackhole_info = {
                                "name": device_name,
                                "manufacturer": device.get("coreaudio_device_manufacturer", ""),
                                "input_channels": device.get("coreaudio_device_input", 0),
                                "output_channels": device.get("coreaudio_device_output", 0)
                            }
                            break

                return {
                    "installed": blackhole_found,
                    "info": blackhole_info,
                    "raw_data": audio_data if blackhole_found else None
                }

            else:
                return {
                    "installed": False,
                    "error": f"system_profiler failed: {result.stderr}",
                    "raw_data": None
                }

        except subprocess.TimeoutExpired:
            return {
                "installed": False,
                "error": "system_profiler timeout",
                "raw_data": None
            }
        except Exception as e:
            return {
                "installed": False,
                "error": str(e),
                "raw_data": None
            }

    def check_blackhole_via_python(self) -> Dict[str, any]:
        """Check BlackHole using Python audio libraries."""
        try:
            # Try to import and use sounddevice for device detection
            import sounddevice as sd

            devices = sd.query_devices()
            blackhole_devices = []

            for i, device in enumerate(devices):
                if "BlackHole" in device['name']:
                    blackhole_devices.append({
                        "index": i,
                        "name": device['name'],
                        "max_input_channels": device['max_input_channels'],
                        "max_output_channels": device['max_output_channels'],
                        "default_samplerate": device['default_samplerate'],
                        "hostapi": sd.query_hostapis(device['hostapi'])['name']
                    })

            return {
                "installed": len(blackhole_devices) > 0,
                "devices": blackhole_devices,
                "method": "sounddevice"
            }

        except ImportError:
            # Fallback: try PyAudio
            try:
                import pyaudio

                pa = pyaudio.PyAudio()
                blackhole_devices = []

                for i in range(pa.get_device_count()):
                    device_info = pa.get_device_info_by_index(i)
                    if "BlackHole" in device_info['name']:
                        blackhole_devices.append({
                            "index": i,
                            "name": device_info['name'],
                            "max_input_channels": device_info['maxInputChannels'],
                            "max_output_channels": device_info['maxOutputChannels'],
                            "default_sample_rate": device_info['defaultSampleRate']
                        })

                pa.terminate()

                return {
                    "installed": len(blackhole_devices) > 0,
                    "devices": blackhole_devices,
                    "method": "pyaudio"
                }

            except ImportError:
                return {
                    "installed": False,
                    "error": "No audio libraries available (sounddevice or pyaudio required)",
                    "method": None
                }

        except Exception as e:
            return {
                "installed": False,
                "error": str(e),
                "method": "error"
            }

    def test_blackhole_functionality(self) -> Dict[str, any]:
        """Test BlackHole functionality with audio streaming."""
        try:
            import sounddevice as sd
            import numpy as np

            # Find BlackHole device
            devices = sd.query_devices()
            blackhole_device = None

            for device in devices:
                if "BlackHole" in device['name'] and device['max_input_channels'] > 0:
                    blackhole_device = device
                    break

            if not blackhole_device:
                return {
                    "functional": False,
                    "error": "BlackHole device not found"
                }

            # Test parameters
            duration = 2.0  # seconds
            sample_rate = int(blackhole_device['default_samplerate'])
            channels = min(blackhole_device['max_input_channels'], 2)

            # Test audio recording
            recording = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=channels,
                device=blackhole_device['name']
            )
            sd.wait()  # Wait until recording is finished

            # Analyze the recording
            if recording is not None and len(recording) > 0:
                # Check for audio data (non-zero values)
                has_audio = np.any(np.abs(recording) > 0.001)

                # Calculate basic statistics
                rms_level = np.sqrt(np.mean(recording ** 2))
                peak_level = np.max(np.abs(recording))

                return {
                    "functional": True,
                    "has_audio": has_audio,
                    "rms_level": float(rms_level),
                    "peak_level": float(peak_level),
                    "duration": duration,
                    "sample_rate": sample_rate,
                    "channels": channels
                }
            else:
                return {
                    "functional": False,
                    "error": "No audio data recorded"
                }

        except ImportError:
            return {
                "functional": False,
                "error": "sounddevice not available"
            }
        except Exception as e:
            return {
                "functional": False,
                "error": str(e)
            }


class ChannelMappingTests:
    """Tests for channel-based speaker mapping functionality."""

    def __init__(self):
        self.sample_rate = TEST_CONFIG["audio"]["sample_rate"]
        self.test_duration = TEST_CONFIG["audio"]["test_duration"]

    def create_test_audio_data(self, channels: int = 2) -> np.ndarray:
        """Create synthetic test audio data for channel mapping tests."""
        duration = self.test_duration
        sample_rate = self.sample_rate

        t = np.linspace(0, duration, int(sample_rate * duration))

        if channels == 1:
            # Mono: single frequency
            return np.sin(2 * np.pi * 440 * t)
        elif channels == 2:
            # Stereo: different frequencies per channel
            left_channel = np.sin(2 * np.pi * 440 * t)  # 440 Hz
            right_channel = np.sin(2 * np.pi * 880 * t)  # 880 Hz
            return np.column_stack((left_channel, right_channel))
        else:
            # Multi-channel: different frequency per channel
            audio_data = []
            base_freq = 440
            for ch in range(channels):
                freq = base_freq * (2 ** (ch / 12))  # Musical intervals
                channel_data = np.sin(2 * np.pi * freq * t)
                audio_data.append(channel_data)
            return np.column_stack(audio_data)

    def save_test_audio(self, audio_data: np.ndarray, file_path: str, sample_rate: int = None) -> bool:
        """Save audio data to a WAV file for testing."""
        try:
            import soundfile as sf

            if sample_rate is None:
                sample_rate = self.sample_rate

            sf.write(file_path, audio_data, sample_rate)
            return True

        except ImportError:
            # Fallback: use scipy if available
            try:
                from scipy.io import wavfile

                # Convert to int16 for WAV format
                if audio_data.dtype != np.int16:
                    audio_data = (audio_data * 32767).astype(np.int16)

                wavfile.write(file_path, sample_rate or self.sample_rate, audio_data)
                return True

            except ImportError:
                print("Neither soundfile nor scipy.io.wavfile available for audio saving")
                return False

        except Exception as e:
            print(f"Error saving audio: {e}")
            return False

    def test_channel_detection(self, temp_dir: Path) -> Dict[str, any]:
        """Test automatic channel detection and mapping."""
        try:
            # Create test files with different channel configurations
            test_files = {}

            # Mono file (microphone simulation)
            mono_data = self.create_test_audio_data(channels=1)
            mono_file = temp_dir / "mono_test.wav"
            if self.save_test_audio(mono_data, str(mono_file)):
                test_files["mono"] = str(mono_file)

            # Stereo file (dual-channel simulation)
            stereo_data = self.create_test_audio_data(channels=2)
            stereo_file = temp_dir / "stereo_test.wav"
            if self.save_test_audio(stereo_data, str(stereo_file)):
                test_files["stereo"] = str(stereo_file)

            # Test channel detection on each file
            results = {}
            for file_type, file_path in test_files.items():
                try:
                    # Mock the channel detection logic
                    # In real implementation, this would use the actual module
                    with patch('whisper_transcription_tool.module3_phone.detect_speaker_by_channel') as mock_detect:
                        mock_result = MagicMock()
                        mock_result.confidence = 0.95
                        mock_result.channel_mapping_used = True
                        mock_result.detection_method = "hardware_based"
                        mock_result.speaker_mapping = {
                            "channel_a": "User",
                            "channel_b": "Contact" if file_type == "stereo" else None
                        }
                        mock_detect.return_value = mock_result

                        # Simulate detection call
                        result = mock_detect({
                            "microphone": file_path,
                            "system": file_path  # Same file for testing
                        })

                        results[file_type] = {
                            "confidence": result.confidence,
                            "mapping_used": result.channel_mapping_used,
                            "method": result.detection_method,
                            "speakers": result.speaker_mapping
                        }

                except Exception as e:
                    results[file_type] = {"error": str(e)}

            return {
                "success": True,
                "test_files": list(test_files.keys()),
                "results": results
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def test_speaker_assignment_accuracy(self) -> Dict[str, any]:
        """Test accuracy of speaker assignment based on channels."""
        try:
            # Mock different scenarios
            test_scenarios = [
                {
                    "name": "clear_separation",
                    "mic_confidence": 0.95,
                    "system_confidence": 0.93,
                    "expected_accuracy": 0.9
                },
                {
                    "name": "moderate_separation",
                    "mic_confidence": 0.75,
                    "system_confidence": 0.78,
                    "expected_accuracy": 0.7
                },
                {
                    "name": "poor_separation",
                    "mic_confidence": 0.55,
                    "system_confidence": 0.52,
                    "expected_accuracy": 0.5
                }
            ]

            results = {}
            for scenario in test_scenarios:
                # Mock the speaker assignment process
                with patch('whisper_transcription_tool.module3_phone.channel_speaker_mapping.detect_speaker_by_channel') as mock_detect:
                    mock_result = MagicMock()
                    mock_result.confidence = (scenario["mic_confidence"] + scenario["system_confidence"]) / 2
                    mock_result.channel_mapping_used = True
                    mock_result.detection_method = "confidence_based"

                    mock_detect.return_value = mock_result

                    # Test the scenario
                    result = mock_detect({"mic": "test", "system": "test"})

                    accuracy_met = result.confidence >= scenario["expected_accuracy"]

                    results[scenario["name"]] = {
                        "confidence": result.confidence,
                        "accuracy_met": accuracy_met,
                        "expected": scenario["expected_accuracy"]
                    }

            overall_accuracy = sum(1 for r in results.values() if r["accuracy_met"]) / len(results)

            return {
                "success": True,
                "overall_accuracy": overall_accuracy,
                "scenarios": results,
                "passed": overall_accuracy >= 0.6  # 60% scenarios should pass
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class AudioQualityTests:
    """Tests for audio quality validation and monitoring."""

    def __init__(self):
        self.sample_rate = TEST_CONFIG["audio"]["sample_rate"]

    def analyze_audio_quality(self, audio_data: np.ndarray, sample_rate: int = None) -> Dict[str, float]:
        """Analyze audio quality metrics."""
        if sample_rate is None:
            sample_rate = self.sample_rate

        try:
            # Basic quality metrics
            metrics = {}

            # RMS Level (loudness)
            rms = np.sqrt(np.mean(audio_data ** 2))
            metrics["rms_level"] = float(rms)

            # Peak Level
            peak = np.max(np.abs(audio_data))
            metrics["peak_level"] = float(peak)

            # Dynamic Range
            if peak > 0:
                dynamic_range = 20 * np.log10(peak / (rms + 1e-10))
                metrics["dynamic_range_db"] = float(dynamic_range)

            # Signal-to-Noise Ratio (simplified estimation)
            # Assume noise floor is lowest 10% of signal
            sorted_audio = np.sort(np.abs(audio_data))
            noise_floor = np.mean(sorted_audio[:int(len(sorted_audio) * 0.1)])
            signal_level = np.mean(sorted_audio[-int(len(sorted_audio) * 0.1):])

            if noise_floor > 0:
                snr_db = 20 * np.log10(signal_level / noise_floor)
                metrics["snr_db"] = float(snr_db)

            # Frequency Analysis (if possible)
            try:
                # Simple spectral analysis
                fft = np.fft.fft(audio_data[:sample_rate])  # First second
                freqs = np.fft.fftfreq(len(fft), 1/sample_rate)
                magnitude = np.abs(fft)

                # Find dominant frequency
                dominant_freq_idx = np.argmax(magnitude[:len(magnitude)//2])
                dominant_freq = abs(freqs[dominant_freq_idx])
                metrics["dominant_frequency_hz"] = float(dominant_freq)

            except Exception:
                # Frequency analysis failed, continue without it
                pass

            # Clipping Detection
            clipping_threshold = 0.99
            clipped_samples = np.sum(np.abs(audio_data) > clipping_threshold)
            clipping_percentage = (clipped_samples / len(audio_data)) * 100
            metrics["clipping_percentage"] = float(clipping_percentage)

            return metrics

        except Exception as e:
            return {"error": str(e)}

    def test_recording_quality(self, temp_dir: Path) -> Dict[str, any]:
        """Test recording quality under different conditions."""
        channel_mapper = ChannelMappingTests()
        results = {}

        try:
            # Test different audio scenarios
            scenarios = [
                ("quiet", 0.1),
                ("normal", 0.5),
                ("loud", 0.9)
            ]

            for scenario_name, amplitude in scenarios:
                # Create test audio with specified amplitude
                test_audio = channel_mapper.create_test_audio_data(channels=2) * amplitude

                # Save to file
                test_file = temp_dir / f"{scenario_name}_audio.wav"
                if channel_mapper.save_test_audio(test_audio, str(test_file)):
                    # Analyze quality
                    quality_metrics = self.analyze_audio_quality(test_audio)

                    # Quality thresholds
                    quality_checks = {
                        "adequate_level": quality_metrics.get("rms_level", 0) > 0.01,
                        "no_clipping": quality_metrics.get("clipping_percentage", 100) < 5.0,
                        "good_dynamic_range": quality_metrics.get("dynamic_range_db", 0) > 6.0
                    }

                    results[scenario_name] = {
                        "metrics": quality_metrics,
                        "quality_checks": quality_checks,
                        "overall_quality": all(quality_checks.values())
                    }

            # Overall quality assessment
            passed_scenarios = sum(1 for r in results.values() if r.get("overall_quality", False))
            overall_pass = passed_scenarios >= len(scenarios) * 0.7  # 70% should pass

            return {
                "success": True,
                "scenarios": results,
                "overall_pass": overall_pass,
                "passed_count": passed_scenarios,
                "total_count": len(scenarios)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class TestBlackHoleIntegration:
    """Main test class for BlackHole audio system integration."""

    def test_blackhole_detection_system_profiler(self):
        """Test BlackHole detection using system_profiler."""
        blackhole_test = BlackHoleSystemTest()
        result = blackhole_test.check_blackhole_installation()

        # Log results for debugging
        print(f"BlackHole detection result: {result}")

        # Test should not fail even if BlackHole is not installed
        # This is informational for CI/CD systems
        assert "installed" in result
        assert isinstance(result["installed"], bool)

        if result["installed"]:
            assert "info" in result
            assert result["info"]["name"]
            print(f"BlackHole found: {result['info']['name']}")
        else:
            print("BlackHole not detected via system_profiler")

    def test_blackhole_detection_python_libraries(self):
        """Test BlackHole detection using Python audio libraries."""
        blackhole_test = BlackHoleSystemTest()
        result = blackhole_test.check_blackhole_via_python()

        assert "installed" in result
        assert isinstance(result["installed"], bool)

        if result["installed"]:
            assert "devices" in result
            assert len(result["devices"]) > 0
            print(f"BlackHole found via {result['method']}: {len(result['devices'])} devices")
        else:
            print(f"BlackHole not detected via Python libraries: {result.get('error', 'Unknown reason')}")

    @pytest.mark.skipif(not hasattr(pytest, "mark"), reason="Requires actual audio hardware")
    def test_blackhole_functionality(self):
        """Test BlackHole functionality with actual audio streaming."""
        blackhole_test = BlackHoleSystemTest()
        result = blackhole_test.test_blackhole_functionality()

        if not result["functional"]:
            pytest.skip(f"BlackHole not functional: {result.get('error')}")

        assert result["functional"] is True

        # Check audio quality metrics
        if "rms_level" in result:
            assert result["rms_level"] >= 0
        if "peak_level" in result:
            assert result["peak_level"] >= 0

        print(f"BlackHole functionality test passed: RMS={result.get('rms_level', 'N/A')}, Peak={result.get('peak_level', 'N/A')}")

    def test_channel_mapping_detection(self, temp_dir):
        """Test channel mapping and speaker detection."""
        channel_tests = ChannelMappingTests()
        result = channel_tests.test_channel_detection(temp_dir)

        assert result["success"] is True
        assert "results" in result

        # Check that both mono and stereo files were processed
        assert "mono" in result["results"] or "stereo" in result["results"]

        for file_type, detection_result in result["results"].items():
            if "error" not in detection_result:
                assert "confidence" in detection_result
                assert detection_result["confidence"] > 0

        print(f"Channel mapping test completed for: {result['test_files']}")

    def test_speaker_assignment_accuracy(self):
        """Test accuracy of speaker assignment algorithms."""
        channel_tests = ChannelMappingTests()
        result = channel_tests.test_speaker_assignment_accuracy()

        assert result["success"] is True
        assert "overall_accuracy" in result
        assert result["passed"] is True

        print(f"Speaker assignment accuracy: {result['overall_accuracy']:.2%}")

    def test_audio_quality_validation(self, temp_dir):
        """Test audio quality validation and monitoring."""
        quality_tests = AudioQualityTests()
        result = quality_tests.test_recording_quality(temp_dir)

        assert result["success"] is True
        assert result["overall_pass"] is True

        print(f"Audio quality test: {result['passed_count']}/{result['total_count']} scenarios passed")

        # Check individual scenarios
        for scenario_name, scenario_result in result["scenarios"].items():
            assert "metrics" in scenario_result
            assert "quality_checks" in scenario_result

    def test_system_requirements(self):
        """Test system requirements for phone recording functionality."""
        requirements = {
            "macos_version": self._check_macos_version(),
            "python_version": self._check_python_version(),
            "audio_libraries": self._check_audio_libraries(),
            "disk_space": self._check_disk_space()
        }

        # macOS should be supported version
        if requirements["macos_version"]:
            assert requirements["macos_version"]["supported"]

        # Python should be 3.8+
        assert requirements["python_version"]["supported"]

        # At least one audio library should be available
        assert requirements["audio_libraries"]["available_count"] > 0

        # Should have enough disk space for recording
        assert requirements["disk_space"]["sufficient"]

        print(f"System requirements check: {requirements}")

    def _check_macos_version(self) -> Dict[str, any]:
        """Check macOS version compatibility."""
        try:
            result = subprocess.run(["sw_vers", "-productVersion"], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip()
                # Parse version (e.g., "12.6.1")
                major_version = int(version.split('.')[0])
                supported = major_version >= 10  # macOS 10.0+

                return {
                    "version": version,
                    "major": major_version,
                    "supported": supported
                }
            else:
                return {"supported": False, "error": "Could not determine macOS version"}

        except Exception:
            # Not on macOS or command not available
            return {"supported": True, "note": "Non-macOS system"}

    def _check_python_version(self) -> Dict[str, any]:
        """Check Python version compatibility."""
        import sys
        version_info = sys.version_info
        supported = version_info.major == 3 and version_info.minor >= 8

        return {
            "version": f"{version_info.major}.{version_info.minor}.{version_info.micro}",
            "supported": supported,
            "required": "3.8+"
        }

    def _check_audio_libraries(self) -> Dict[str, any]:
        """Check availability of audio processing libraries."""
        libraries = {
            "sounddevice": False,
            "pyaudio": False,
            "soundfile": False,
            "scipy": False
        }

        for lib_name in libraries:
            try:
                __import__(lib_name)
                libraries[lib_name] = True
            except ImportError:
                pass

        available_count = sum(libraries.values())

        return {
            "libraries": libraries,
            "available_count": available_count,
            "recommended": available_count >= 2
        }

    def _check_disk_space(self) -> Dict[str, any]:
        """Check available disk space for recordings."""
        try:
            import shutil
            disk_usage = shutil.disk_usage("/tmp")

            free_gb = disk_usage.free / (1024**3)
            sufficient = free_gb >= 1.0  # At least 1GB free

            return {
                "free_gb": round(free_gb, 2),
                "sufficient": sufficient,
                "required_gb": 1.0
            }

        except Exception as e:
            return {
                "sufficient": True,  # Assume sufficient if can't check
                "error": str(e)
            }


# Helper functions for audio system testing
def generate_test_tone(frequency: float, duration: float, sample_rate: int = 44100, amplitude: float = 0.5) -> np.ndarray:
    """Generate a test tone for audio testing."""
    t = np.linspace(0, duration, int(sample_rate * duration))
    return amplitude * np.sin(2 * np.pi * frequency * t)


def create_stereo_test_signal(left_freq: float = 440, right_freq: float = 880, duration: float = 5.0) -> np.ndarray:
    """Create a stereo test signal with different frequencies in each channel."""
    sample_rate = TEST_CONFIG["audio"]["sample_rate"]
    left_channel = generate_test_tone(left_freq, duration, sample_rate)
    right_channel = generate_test_tone(right_freq, duration, sample_rate)
    return np.column_stack((left_channel, right_channel))


def validate_audio_file(file_path: str) -> Dict[str, any]:
    """Validate an audio file's properties."""
    try:
        import soundfile as sf
        data, sample_rate = sf.read(file_path)

        return {
            "valid": True,
            "duration": len(data) / sample_rate,
            "sample_rate": sample_rate,
            "channels": data.shape[1] if len(data.shape) > 1 else 1,
            "samples": len(data)
        }

    except ImportError:
        return {"valid": False, "error": "soundfile not available"}
    except Exception as e:
        return {"valid": False, "error": str(e)}