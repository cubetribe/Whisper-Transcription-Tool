"""Modul 3: Telefonanruf-Aufnahme und Verarbeitung

Dieses Modul stellt Funktionen zur Aufnahme von Telefonaten mit getrennten
Audiokanälen für Mikrofon und Systemton bereit.

Erfordert BlackHole als virtuelle Audioschnittstelle.
"""

# Import basic models without audio dependencies
from .models import RecordingSession, RecordingConfig

# Audio-dependent imports are loaded on demand to avoid dependency issues
def get_audio_recorder():
    """Get AudioRecorder instance (loads audio dependencies on demand)."""
    from .recorder import AudioRecorder
    return AudioRecorder()

def get_device_manager():
    """Get DeviceManager instance (loads audio dependencies on demand)."""
    from .recorder import DeviceManager
    return DeviceManager()

# Core transcript processing (no audio dependencies)
from .transcript_processing import (
    merge_transcripts_by_channel_mapping,
    merge_transcripts_with_timestamps,
    ChannelMapping,
    SpeakerRole
)

# Channel mapping functionality (may have optional audio dependencies)
from .channel_speaker_mapping import (
    ChannelMappingConfig,
    ChannelValidationResult,
    SpeakerDetectionResult
)

__all__ = [
    'RecordingSession', 'RecordingConfig',
    'get_audio_recorder', 'get_device_manager',
    'merge_transcripts_by_channel_mapping', 'merge_transcripts_with_timestamps',
    'ChannelMapping', 'SpeakerRole',
    'ChannelMappingConfig', 'ChannelValidationResult', 'SpeakerDetectionResult'
]
