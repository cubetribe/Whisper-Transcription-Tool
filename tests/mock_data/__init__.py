"""
Mock data generators for Phone Recording System testing.

This package provides utilities to generate synthetic audio data,
transcripts, and other test data for comprehensive testing of the
Phone Recording System.
"""

from .audio_generator import (
    MockAudioGenerator,
    MockTranscriptGenerator,
    create_complete_mock_dataset
)

__all__ = [
    'MockAudioGenerator',
    'MockTranscriptGenerator',
    'create_complete_mock_dataset'
]