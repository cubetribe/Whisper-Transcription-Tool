"""
Channel-Based Speaker Mapping for Phone Call Recordings.

This module provides robust speaker identification through hardware audio channel mapping.
It implements the core principle: Microphone = Local User, System Audio = Remote User.
"""

import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union, Any
from pathlib import Path
from datetime import datetime

# Optional audio dependencies
try:
    import sounddevice as sd
    AUDIO_AVAILABLE = True
except ImportError:
    sd = None
    AUDIO_AVAILABLE = False

from ..core.logging_setup import get_logger
from .models import RecordingConfig, RecordingSession
from .transcript_processing import ChannelMapping, SpeakerRole

logger = get_logger(__name__)


@dataclass
class ChannelMappingConfig:
    """Configuration for channel-based speaker mapping."""

    microphone_device_id: str
    system_audio_device_id: str
    user_name: str = "Ich"
    contact_name: str = "Gesprächspartner"
    confidence_threshold: float = 0.0
    auto_detect_channels: bool = True
    fallback_to_generic_names: bool = True


@dataclass
class ChannelValidationResult:
    """Result of channel mapping validation."""

    is_valid: bool
    microphone_available: bool
    system_audio_available: bool
    microphone_info: Optional[Dict] = None
    system_audio_info: Optional[Dict] = None
    errors: List[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


@dataclass
class SpeakerDetectionResult:
    """Result of speaker detection based on channel mapping."""

    speaker_mapping: Dict[str, str]  # channel -> speaker_name
    confidence: float
    channel_mapping_used: bool
    detection_method: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


def validate_channel_mapping(config: ChannelMappingConfig) -> ChannelValidationResult:
    """
    Validate that the specified audio channels are available and properly configured.

    Args:
        config: Channel mapping configuration

    Returns:
        ChannelValidationResult with validation status and details
    """
    logger.info("Validating channel mapping configuration...")

    result = ChannelValidationResult(
        is_valid=False,
        microphone_available=False,
        system_audio_available=False
    )

    try:
        # Check if audio is available
        if not AUDIO_AVAILABLE:
            result.errors.append("sounddevice not available - install with: pip install sounddevice")
            logger.warning("Audio validation skipped: sounddevice not available")
            return result

        # Get all available devices
        devices = sd.query_devices()
        device_list = []

        for i, device in enumerate(devices):
            device_info = {
                'id': i,
                'name': device['name'],
                'channels_in': device['max_input_channels'],
                'channels_out': device['max_output_channels'],
                'default_samplerate': device['default_samplerate'],
                'is_input': device['max_input_channels'] > 0,
                'is_output': device['max_output_channels'] > 0
            }
            device_list.append(device_info)

        logger.debug(f"Found {len(device_list)} audio devices")

        # Validate microphone device
        try:
            mic_device_id = int(config.microphone_device_id)
            if mic_device_id < len(device_list):
                mic_info = device_list[mic_device_id]
                result.microphone_info = mic_info

                if mic_info['is_input'] and mic_info['channels_in'] > 0:
                    result.microphone_available = True
                    logger.debug(f"Microphone device validated: {mic_info['name']}")
                else:
                    result.errors.append(f"Device {mic_device_id} is not a valid input device")

            else:
                result.errors.append(f"Microphone device ID {mic_device_id} not found")

        except (ValueError, IndexError) as e:
            result.errors.append(f"Invalid microphone device ID: {config.microphone_device_id}")

        # Validate system audio device (BlackHole or similar)
        try:
            sys_device_id = int(config.system_audio_device_id)
            if sys_device_id < len(device_list):
                sys_info = device_list[sys_device_id]
                result.system_audio_info = sys_info

                if sys_info['is_input'] and sys_info['channels_in'] > 0:
                    result.system_audio_available = True
                    logger.debug(f"System audio device validated: {sys_info['name']}")

                    # Check if it's likely a BlackHole device
                    if 'BlackHole' not in sys_info['name']:
                        result.warnings.append(
                            f"System audio device '{sys_info['name']}' is not BlackHole. "
                            "Consider using BlackHole for optimal system audio capture."
                        )
                else:
                    result.errors.append(f"Device {sys_device_id} is not a valid input device")

            else:
                result.errors.append(f"System audio device ID {sys_device_id} not found")

        except (ValueError, IndexError) as e:
            result.errors.append(f"Invalid system audio device ID: {config.system_audio_device_id}")

        # Overall validation
        result.is_valid = result.microphone_available and result.system_audio_available

        if result.is_valid:
            logger.info("Channel mapping validation successful")
        else:
            logger.warning(f"Channel mapping validation failed: {result.errors}")

    except Exception as e:
        logger.error(f"Error during channel validation: {e}")
        result.errors.append(f"Validation error: {str(e)}")

    return result


def detect_speaker_by_channel(
    transcript_file_paths: Dict[str, str],
    config: ChannelMappingConfig
) -> SpeakerDetectionResult:
    """
    Detect speakers based on hardware channel mapping with 100% confidence.

    Args:
        transcript_file_paths: Dictionary mapping channel names to transcript file paths
                              Expected keys: 'microphone', 'system' or 'system_audio'
        config: Channel mapping configuration

    Returns:
        SpeakerDetectionResult with channel-based speaker assignments
    """
    logger.info("Detecting speakers using hardware channel mapping...")

    # Validate channel mapping first
    validation_result = validate_channel_mapping(config)

    if not validation_result.is_valid:
        logger.error(f"Channel mapping validation failed: {validation_result.errors}")
        return SpeakerDetectionResult(
            speaker_mapping={},
            confidence=0.0,
            channel_mapping_used=False,
            detection_method="failed_validation",
            metadata={
                "validation_errors": validation_result.errors,
                "validation_warnings": validation_result.warnings
            }
        )

    # Build speaker mapping based on hardware channels
    speaker_mapping = {}

    # Map microphone channel to local user
    for mic_key in ['microphone', 'mic']:
        if mic_key in transcript_file_paths:
            speaker_mapping[mic_key] = config.user_name
            logger.debug(f"Mapped {mic_key} channel to {config.user_name}")

    # Map system audio channel to remote user
    for sys_key in ['system', 'system_audio']:
        if sys_key in transcript_file_paths:
            speaker_mapping[sys_key] = config.contact_name
            logger.debug(f"Mapped {sys_key} channel to {config.contact_name}")

    # Validate that we have at least one mapping
    if not speaker_mapping:
        logger.warning("No valid channel mappings found in transcript file paths")
        if config.fallback_to_generic_names:
            # Fallback: try to map any available files
            available_keys = list(transcript_file_paths.keys())
            if len(available_keys) >= 2:
                speaker_mapping[available_keys[0]] = config.user_name
                speaker_mapping[available_keys[1]] = config.contact_name
                logger.info(f"Fallback mapping applied: {speaker_mapping}")
            else:
                logger.error("Insufficient channels for speaker mapping")

    # Calculate confidence (100% for hardware-based mapping)
    confidence = 1.0 if speaker_mapping else 0.0

    # Verify transcript files exist
    missing_files = []
    for channel, file_path in transcript_file_paths.items():
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        logger.warning(f"Missing transcript files: {missing_files}")
        confidence *= 0.8  # Reduce confidence if files are missing

    result = SpeakerDetectionResult(
        speaker_mapping=speaker_mapping,
        confidence=confidence,
        channel_mapping_used=True,
        detection_method="hardware_channel_mapping",
        metadata={
            "validation_result": validation_result,
            "transcript_files": transcript_file_paths,
            "missing_files": missing_files,
            "mapping_config": {
                "user_name": config.user_name,
                "contact_name": config.contact_name,
                "microphone_device": validation_result.microphone_info,
                "system_audio_device": validation_result.system_audio_info
            }
        }
    )

    logger.info(f"Speaker detection completed with {confidence:.0%} confidence: {speaker_mapping}")
    return result


def create_channel_mapping_from_session(
    session: RecordingSession,
    user_name: str = "Ich",
    contact_name: str = "Gesprächspartner"
) -> ChannelMappingConfig:
    """
    Create a channel mapping configuration from a recording session.

    Args:
        session: Recording session with device configuration
        user_name: Name for the local user
        contact_name: Name for the conversation partner

    Returns:
        ChannelMappingConfig based on the session
    """
    return ChannelMappingConfig(
        microphone_device_id=session.config.input_device_id,
        system_audio_device_id=session.config.output_device_id,
        user_name=user_name,
        contact_name=contact_name,
        auto_detect_channels=True,
        fallback_to_generic_names=True
    )


def format_conversation_transcript(
    segments: List[Dict],
    speaker_mapping: Dict[str, str],
    output_format: str = "txt",
    enhanced_metadata: bool = True
) -> str:
    """
    Format conversation transcript with channel-based speaker information.

    Args:
        segments: List of transcript segments with channel information
        speaker_mapping: Mapping from channels to speaker names
        output_format: Output format (txt, md, json)
        enhanced_metadata: Include enhanced metadata in output

    Returns:
        Formatted conversation transcript
    """
    logger.debug(f"Formatting conversation transcript in {output_format} format")

    # Add speaker information to segments based on channel mapping
    for segment in segments:
        channel = segment.get('channel', 'unknown')
        if channel in speaker_mapping:
            segment['speaker'] = speaker_mapping[channel]
            segment['channel_confidence'] = 1.0  # Hardware-based = 100% confidence
        else:
            segment['speaker'] = 'Unknown'
            segment['channel_confidence'] = 0.0

    # Sort segments by timestamp
    segments.sort(key=lambda x: x.get('start', 0))

    if output_format.lower() == 'json':
        return json.dumps({
            "metadata": {
                "speaker_mapping": speaker_mapping,
                "enhanced_metadata": enhanced_metadata,
                "total_segments": len(segments),
                "format_version": "1.0",
                "generated_at": datetime.now().isoformat()
            },
            "segments": segments
        }, indent=2)

    elif output_format.lower() == 'md':
        return _format_conversation_markdown(segments, speaker_mapping, enhanced_metadata)

    else:  # Default to txt
        return _format_conversation_text(segments, speaker_mapping, enhanced_metadata)


def _format_conversation_text(
    segments: List[Dict],
    speaker_mapping: Dict[str, str],
    enhanced_metadata: bool
) -> str:
    """Format conversation as plain text."""
    lines = []
    lines.append("CONVERSATION TRANSCRIPT")
    lines.append("=" * 50)
    lines.append("")

    if enhanced_metadata:
        lines.append("SPEAKER MAPPING:")
        for channel, speaker in speaker_mapping.items():
            channel_icon = "🎤" if "mic" in channel.lower() else "🔊"
            lines.append(f"{channel_icon} {channel}: {speaker}")
        lines.append("")
        lines.append(f"Total Segments: {len(segments)}")
        lines.append("")

    lines.append("TRANSCRIPT:")
    lines.append("-" * 30)

    current_speaker = None

    for segment in segments:
        speaker = segment.get('speaker', 'Unknown')
        text = segment.get('text', '').strip()
        start_time = segment.get('start', 0)
        channel = segment.get('channel', 'unknown')
        confidence = segment.get('confidence', 0.0)

        # Format timestamp
        minutes = int(start_time // 60)
        seconds = int(start_time % 60)
        timestamp = f"{minutes:02d}:{seconds:02d}"

        # Channel indicator
        channel_icon = "🎤" if "mic" in channel.lower() else "🔊"

        # Add speaker change
        if speaker != current_speaker:
            lines.append("")
            lines.append(f"{channel_icon} {speaker} [{timestamp}]:")
            current_speaker = speaker

        # Add text
        if enhanced_metadata and confidence > 0:
            lines.append(f"   {text} (conf: {confidence:.2f})")
        else:
            lines.append(f"   {text}")

    return "\n".join(lines)


def _format_conversation_markdown(
    segments: List[Dict],
    speaker_mapping: Dict[str, str],
    enhanced_metadata: bool
) -> str:
    """Format conversation as Markdown."""
    lines = []
    lines.append("# Conversation Transcript")
    lines.append("")

    if enhanced_metadata:
        lines.append("## Speaker Mapping")
        lines.append("")
        lines.append("| Channel | Speaker |")
        lines.append("|---------|---------|")
        for channel, speaker in speaker_mapping.items():
            channel_icon = "🎤" if "mic" in channel.lower() else "🔊"
            lines.append(f"| {channel_icon} {channel} | {speaker} |")
        lines.append("")

        lines.append("## Statistics")
        lines.append("")
        lines.append(f"- **Total Segments:** {len(segments)}")
        total_duration = max((seg.get('end', seg.get('start', 0)) for seg in segments), default=0)
        duration_min = int(total_duration // 60)
        duration_sec = int(total_duration % 60)
        lines.append(f"- **Duration:** {duration_min:02d}:{duration_sec:02d}")
        lines.append("")

    lines.append("## Transcript")
    lines.append("")

    current_speaker = None

    for segment in segments:
        speaker = segment.get('speaker', 'Unknown')
        text = segment.get('text', '').strip()
        start_time = segment.get('start', 0)
        channel = segment.get('channel', 'unknown')
        confidence = segment.get('confidence', 0.0)

        # Format timestamp
        minutes = int(start_time // 60)
        seconds = int(start_time % 60)
        timestamp = f"{minutes:02d}:{seconds:02d}"

        # Channel indicator
        channel_icon = "🎤" if "mic" in channel.lower() else "🔊"

        # Add speaker change
        if speaker != current_speaker:
            lines.append("")
            lines.append(f"### {channel_icon} {speaker}")
            lines.append("")
            current_speaker = speaker

        # Add text with metadata
        if enhanced_metadata and confidence > 0:
            lines.append(f"**{timestamp}**: {text} *(conf: {confidence:.2f})*")
        else:
            lines.append(f"**{timestamp}**: {text}")
        lines.append("")

    return "\n".join(lines)


def get_recommended_channel_setup() -> Dict:
    """
    Get recommended channel setup for optimal phone call recording.

    Returns:
        Dictionary with recommended device configuration
    """
    logger.info("Analyzing available devices for recommended channel setup...")

    try:
        # Check if audio is available
        if not AUDIO_AVAILABLE:
            return {
                'status': 'error',
                'message': 'sounddevice not available - install with: pip install sounddevice',
                'confidence': 'low',
                'devices_found': 0,
                'blackhole_available': False,
                'microphone_available': False
            }

        devices = sd.query_devices()
        device_list = []

        for i, device in enumerate(devices):
            device_info = {
                'id': i,
                'name': device['name'],
                'channels_in': device['max_input_channels'],
                'channels_out': device['max_output_channels'],
                'default_samplerate': device['default_samplerate'],
                'is_input': device['max_input_channels'] > 0,
                'is_output': device['max_output_channels'] > 0
            }
            device_list.append(device_info)

        # Find BlackHole device
        blackhole_device = None
        for device in device_list:
            if 'BlackHole' in device['name'] and device['is_input']:
                blackhole_device = device
                break

        # Find default or best microphone
        default_input = sd.default.device[0] if sd.default.device else None
        microphone_device = None

        if default_input is not None and default_input < len(device_list):
            mic_candidate = device_list[default_input]
            if mic_candidate['is_input']:
                microphone_device = mic_candidate

        # Fallback: find first available input device
        if microphone_device is None:
            for device in device_list:
                if device['is_input'] and 'BlackHole' not in device['name']:
                    microphone_device = device
                    break

        # Build recommendation
        recommendation = {
            'status': 'success',
            'devices_found': len(device_list),
            'blackhole_available': blackhole_device is not None,
            'microphone_available': microphone_device is not None
        }

        if blackhole_device and microphone_device:
            recommendation['recommended_config'] = {
                'microphone_device': microphone_device,
                'system_audio_device': blackhole_device,
                'sample_rate': min(
                    microphone_device['default_samplerate'],
                    blackhole_device['default_samplerate']
                )
            }
            recommendation['confidence'] = 'high'
            recommendation['message'] = "Optimal setup available with BlackHole"

        elif microphone_device and not blackhole_device:
            recommendation['issues'] = [
                "BlackHole not found. System audio capture will not work optimally."
            ]
            recommendation['installation_guide'] = {
                'BlackHole': 'https://github.com/ExistentialAudio/BlackHole',
                'instructions': 'Install BlackHole for system audio capture'
            }
            recommendation['confidence'] = 'medium'
            recommendation['message'] = "Microphone available, but BlackHole needed for system audio"

        else:
            recommendation['status'] = 'error'
            recommendation['message'] = "No suitable audio devices found"
            recommendation['confidence'] = 'low'

        return recommendation

    except Exception as e:
        logger.error(f"Error getting recommended channel setup: {e}")
        return {
            'status': 'error',
            'message': f"Error analyzing devices: {str(e)}",
            'confidence': 'low'
        }