"""
Mock audio data generator for testing Phone Recording System.

This module provides utilities to generate synthetic audio data
for testing purposes, including stereo channels, different frequencies,
and various audio quality scenarios.
"""

import json
import os
import tempfile
import wave
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np


class MockAudioGenerator:
    """Generates mock audio data for testing purposes."""

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate

    def generate_sine_wave(self, frequency: float, duration: float, amplitude: float = 0.5) -> np.ndarray:
        """Generate a sine wave with specified parameters."""
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        return amplitude * np.sin(2 * np.pi * frequency * t)

    def generate_noise(self, duration: float, amplitude: float = 0.1) -> np.ndarray:
        """Generate white noise."""
        samples = int(self.sample_rate * duration)
        return amplitude * np.random.normal(0, 1, samples)

    def generate_stereo_conversation(self, duration: float = 30.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate a mock stereo conversation with different speakers on each channel.

        Returns:
            Tuple of (left_channel, right_channel) arrays
        """
        # Speaker 1 (left channel) - lower frequency, speaks first
        left_segments = []
        right_segments = []

        # Create alternating speech segments
        segment_duration = 2.0
        pause_duration = 0.5
        total_time = 0

        speaker_1_freq = 440  # A4 note
        speaker_2_freq = 880  # A5 note (one octave higher)

        while total_time < duration:
            # Speaker 1 speaks
            if total_time + segment_duration <= duration:
                segment = self.generate_sine_wave(speaker_1_freq, segment_duration, 0.7)
                left_segments.append(segment)
                right_segments.append(np.zeros(len(segment)))
                total_time += segment_duration

            # Pause
            if total_time + pause_duration <= duration:
                pause = np.zeros(int(self.sample_rate * pause_duration))
                left_segments.append(pause)
                right_segments.append(pause)
                total_time += pause_duration

            # Speaker 2 speaks
            if total_time + segment_duration <= duration:
                segment = self.generate_sine_wave(speaker_2_freq, segment_duration, 0.6)
                left_segments.append(np.zeros(len(segment)))
                right_segments.append(segment)
                total_time += segment_duration

            # Pause
            if total_time + pause_duration <= duration:
                pause = np.zeros(int(self.sample_rate * pause_duration))
                left_segments.append(pause)
                right_segments.append(pause)
                total_time += pause_duration

        # Concatenate segments
        left_channel = np.concatenate(left_segments) if left_segments else np.array([])
        right_channel = np.concatenate(right_segments) if right_segments else np.array([])

        # Ensure both channels have the same length
        min_length = min(len(left_channel), len(right_channel))
        if min_length > 0:
            left_channel = left_channel[:min_length]
            right_channel = right_channel[:min_length]

        # Add some background noise
        noise_amplitude = 0.02
        left_channel += self.generate_noise(len(left_channel) / self.sample_rate, noise_amplitude)
        right_channel += self.generate_noise(len(right_channel) / self.sample_rate, noise_amplitude)

        return left_channel, right_channel

    def generate_phone_recording_pair(self, duration: float = 30.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate a pair of audio files simulating phone recording (mic + system audio).

        Returns:
            Tuple of (microphone_audio, system_audio) arrays
        """
        # Microphone audio: user speaking with some background noise
        user_freq = 300  # Lower frequency for user voice
        mic_audio = []

        # System audio: remote speaker with phone-quality compression
        remote_freq = 500  # Mid frequency for remote voice
        system_audio = []

        # Generate alternating speech pattern
        segment_duration = 3.0
        pause_duration = 1.0
        total_time = 0

        while total_time < duration:
            # User speaks (microphone picks up)
            if total_time + segment_duration <= duration:
                user_segment = self.generate_sine_wave(user_freq, segment_duration, 0.8)
                # Add some room tone/noise to microphone
                user_segment += self.generate_noise(segment_duration, 0.05)
                mic_audio.append(user_segment)

                # System audio is quiet during user speech (but may have some bleed)
                system_segment = self.generate_noise(segment_duration, 0.02)
                system_audio.append(system_segment)

                total_time += segment_duration

            # Pause
            if total_time + pause_duration <= duration:
                pause_mic = self.generate_noise(pause_duration, 0.03)
                pause_sys = self.generate_noise(pause_duration, 0.02)
                mic_audio.append(pause_mic)
                system_audio.append(pause_sys)
                total_time += pause_duration

            # Remote speaker (system audio)
            if total_time + segment_duration <= duration:
                remote_segment = self.generate_sine_wave(remote_freq, segment_duration, 0.7)
                # Simulate phone compression/quality
                remote_segment = self.apply_phone_effects(remote_segment)
                system_audio.append(remote_segment)

                # Microphone may pick up some system audio bleed
                mic_bleed = remote_segment * 0.1 + self.generate_noise(segment_duration, 0.04)
                mic_audio.append(mic_bleed)

                total_time += segment_duration

            # Pause
            if total_time + pause_duration <= duration:
                pause_mic = self.generate_noise(pause_duration, 0.03)
                pause_sys = self.generate_noise(pause_duration, 0.02)
                mic_audio.append(pause_mic)
                system_audio.append(pause_sys)
                total_time += pause_duration

        # Concatenate all segments
        mic_channel = np.concatenate(mic_audio) if mic_audio else np.array([])
        sys_channel = np.concatenate(system_audio) if system_audio else np.array([])

        # Ensure same length
        min_length = min(len(mic_channel), len(sys_channel))
        if min_length > 0:
            mic_channel = mic_channel[:min_length]
            sys_channel = sys_channel[:min_length]

        return mic_channel, sys_channel

    def apply_phone_effects(self, audio: np.ndarray) -> np.ndarray:
        """Apply phone-quality effects to audio (bandwidth limiting, compression)."""
        # Simple simulation of phone quality:
        # - Add some harmonic distortion
        # - Reduce dynamic range

        # Add harmonic distortion
        distorted = audio + 0.1 * np.sin(6 * np.pi * np.cumsum(audio))

        # Simple compression (reduce dynamic range)
        compressed = np.tanh(distorted * 2) * 0.7

        return compressed

    def save_wav_file(self, audio_data: np.ndarray, file_path: str, channels: int = 1) -> bool:
        """Save audio data to a WAV file."""
        try:
            # Convert to 16-bit PCM
            if audio_data.dtype != np.int16:
                # Normalize to [-1, 1] range first
                if np.max(np.abs(audio_data)) > 0:
                    audio_data = audio_data / np.max(np.abs(audio_data))
                # Convert to 16-bit
                audio_data = (audio_data * 32767).astype(np.int16)

            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Write WAV file
            with wave.open(file_path, 'wb') as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(2)  # 2 bytes per sample (16-bit)
                wav_file.setframerate(self.sample_rate)

                if channels == 1:
                    wav_file.writeframes(audio_data.tobytes())
                else:
                    # For stereo, interleave the channels
                    if audio_data.ndim == 1:
                        # Mono data, duplicate to stereo
                        stereo_data = np.column_stack((audio_data, audio_data))
                    else:
                        stereo_data = audio_data
                    wav_file.writeframes(stereo_data.tobytes())

            return True

        except Exception as e:
            print(f"Error saving WAV file {file_path}: {e}")
            return False

    def create_test_audio_set(self, output_dir: str) -> Dict[str, str]:
        """
        Create a complete set of test audio files for phone recording tests.

        Returns:
            Dictionary mapping test names to file paths
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        test_files = {}

        # 1. Stereo conversation test
        left_channel, right_channel = self.generate_stereo_conversation(20.0)
        stereo_data = np.column_stack((left_channel, right_channel))
        stereo_file = output_path / "stereo_conversation.wav"
        if self.save_wav_file(stereo_data, str(stereo_file), channels=2):
            test_files["stereo_conversation"] = str(stereo_file)

        # 2. Phone recording simulation
        mic_audio, sys_audio = self.generate_phone_recording_pair(25.0)

        mic_file = output_path / "phone_microphone.wav"
        sys_file = output_path / "phone_system.wav"

        if self.save_wav_file(mic_audio, str(mic_file)):
            test_files["phone_microphone"] = str(mic_file)

        if self.save_wav_file(sys_audio, str(sys_file)):
            test_files["phone_system"] = str(sys_file)

        # 3. Quality test files
        # High quality
        high_quality = self.generate_sine_wave(440, 10.0, 0.8)
        hq_file = output_path / "high_quality.wav"
        if self.save_wav_file(high_quality, str(hq_file)):
            test_files["high_quality"] = str(hq_file)

        # Low quality (with noise)
        low_quality = self.generate_sine_wave(440, 10.0, 0.3) + self.generate_noise(10.0, 0.2)
        lq_file = output_path / "low_quality.wav"
        if self.save_wav_file(low_quality, str(lq_file)):
            test_files["low_quality"] = str(lq_file)

        # 4. Silent file
        silence = np.zeros(int(self.sample_rate * 5.0))
        silent_file = output_path / "silence.wav"
        if self.save_wav_file(silence, str(silent_file)):
            test_files["silence"] = str(silent_file)

        # 5. Very short file
        short_audio = self.generate_sine_wave(1000, 0.5, 0.5)
        short_file = output_path / "short_audio.wav"
        if self.save_wav_file(short_audio, str(short_file)):
            test_files["short_audio"] = str(short_file)

        return test_files


class MockTranscriptGenerator:
    """Generates mock transcript data for testing."""

    def __init__(self):
        self.mock_sentences = [
            "Hello, how are you today?",
            "I'm doing well, thank you for asking.",
            "Can you hear me clearly?",
            "Yes, the audio quality is excellent.",
            "Let's discuss the project requirements.",
            "I think we should focus on the main features first.",
            "That sounds like a good approach.",
            "When do you think we can have the first version ready?",
            "I estimate about two weeks for the initial prototype.",
            "Perfect, that aligns with our timeline."
        ]

    def generate_transcript_segments(self, duration: float = 30.0, num_speakers: int = 2) -> List[Dict]:
        """Generate mock transcript segments with timestamps."""
        segments = []
        current_time = 0.0
        speaker_index = 0

        while current_time < duration:
            # Random segment duration between 2-5 seconds
            segment_duration = np.random.uniform(2.0, 5.0)

            if current_time + segment_duration > duration:
                segment_duration = duration - current_time

            # Select a random sentence
            sentence = np.random.choice(self.mock_sentences)

            # Generate segment
            segment = {
                "text": sentence,
                "start": round(current_time, 2),
                "end": round(current_time + segment_duration, 2),
                "confidence": round(np.random.uniform(0.85, 0.98), 3),
                "speaker": f"Speaker_{speaker_index % num_speakers + 1}"
            }

            segments.append(segment)

            # Move to next time and speaker
            current_time += segment_duration + np.random.uniform(0.5, 1.5)  # Add pause
            speaker_index += 1

        return segments

    def generate_channel_based_transcripts(self) -> Dict[str, Dict]:
        """Generate separate transcripts for microphone and system audio channels."""

        # Microphone transcript (local user)
        mic_segments = [
            {
                "text": "Hello, can you hear me?",
                "start": 0.0,
                "end": 2.5,
                "confidence": 0.95,
                "speaker": "Local_User"
            },
            {
                "text": "I'm calling about the project status.",
                "start": 8.0,
                "end": 11.0,
                "confidence": 0.92,
                "speaker": "Local_User"
            },
            {
                "text": "That sounds good to me.",
                "start": 18.0,
                "end": 20.0,
                "confidence": 0.89,
                "speaker": "Local_User"
            },
            {
                "text": "Thank you for the update.",
                "start": 28.0,
                "end": 30.5,
                "confidence": 0.94,
                "speaker": "Local_User"
            }
        ]

        # System audio transcript (remote speaker)
        sys_segments = [
            {
                "text": "Yes, I can hear you perfectly.",
                "start": 3.0,
                "end": 5.5,
                "confidence": 0.91,
                "speaker": "Remote_Speaker"
            },
            {
                "text": "The project is progressing well.",
                "start": 12.0,
                "end": 15.0,
                "confidence": 0.87,
                "speaker": "Remote_Speaker"
            },
            {
                "text": "We should have the first version ready next week.",
                "start": 21.0,
                "end": 24.5,
                "confidence": 0.93,
                "speaker": "Remote_Speaker"
            }
        ]

        return {
            "microphone": {
                "segments": mic_segments,
                "language": "en",
                "duration": 30.5
            },
            "system": {
                "segments": sys_segments,
                "language": "en",
                "duration": 30.5
            }
        }

    def save_transcript_json(self, transcript_data: Dict, file_path: str) -> bool:
        """Save transcript data to a JSON file."""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"Error saving transcript file {file_path}: {e}")
            return False

    def create_test_transcript_set(self, output_dir: str) -> Dict[str, str]:
        """Create a complete set of test transcript files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        test_files = {}

        # 1. Channel-based transcripts
        channel_transcripts = self.generate_channel_based_transcripts()

        mic_file = output_path / "microphone_transcript.json"
        sys_file = output_path / "system_transcript.json"

        if self.save_transcript_json(channel_transcripts["microphone"], str(mic_file)):
            test_files["microphone_transcript"] = str(mic_file)

        if self.save_transcript_json(channel_transcripts["system"], str(sys_file)):
            test_files["system_transcript"] = str(sys_file)

        # 2. Combined transcript
        combined_segments = []
        for segment in channel_transcripts["microphone"]["segments"]:
            combined_segments.append({**segment, "channel": "microphone"})
        for segment in channel_transcripts["system"]["segments"]:
            combined_segments.append({**segment, "channel": "system"})

        # Sort by start time
        combined_segments.sort(key=lambda x: x["start"])

        combined_transcript = {
            "segments": combined_segments,
            "language": "en",
            "duration": 30.5,
            "metadata": {
                "total_segments": len(combined_segments),
                "speakers": ["Local_User", "Remote_Speaker"],
                "channels": ["microphone", "system"]
            }
        }

        combined_file = output_path / "combined_transcript.json"
        if self.save_transcript_json(combined_transcript, str(combined_file)):
            test_files["combined_transcript"] = str(combined_file)

        # 3. Long transcript for stress testing
        long_segments = self.generate_transcript_segments(300.0, 3)  # 5 minutes, 3 speakers
        long_transcript = {
            "segments": long_segments,
            "language": "en",
            "duration": 300.0
        }

        long_file = output_path / "long_transcript.json"
        if self.save_transcript_json(long_transcript, str(long_file)):
            test_files["long_transcript"] = str(long_file)

        return test_files


def create_complete_mock_dataset(base_dir: str = None) -> Dict[str, Dict[str, str]]:
    """
    Create a complete mock dataset for testing Phone Recording System.

    Args:
        base_dir: Base directory for mock data. If None, uses temporary directory.

    Returns:
        Dictionary with 'audio' and 'transcript' file mappings
    """
    if base_dir is None:
        base_dir = tempfile.mkdtemp(prefix="phone_recording_test_")

    base_path = Path(base_dir)
    audio_dir = base_path / "audio"
    transcript_dir = base_path / "transcripts"

    # Generate audio files
    audio_generator = MockAudioGenerator()
    audio_files = audio_generator.create_test_audio_set(str(audio_dir))

    # Generate transcript files
    transcript_generator = MockTranscriptGenerator()
    transcript_files = transcript_generator.create_test_transcript_set(str(transcript_dir))

    return {
        "base_directory": str(base_path),
        "audio": audio_files,
        "transcripts": transcript_files
    }


if __name__ == "__main__":
    # Example usage
    print("Creating mock data for Phone Recording System tests...")

    mock_data = create_complete_mock_dataset("./test_data")

    print(f"Mock data created in: {mock_data['base_directory']}")
    print(f"Audio files: {len(mock_data['audio'])}")
    print(f"Transcript files: {len(mock_data['transcripts'])}")

    for category, files in mock_data.items():
        if isinstance(files, dict):
            print(f"\n{category.upper()}:")
            for name, path in files.items():
                print(f"  {name}: {path}")