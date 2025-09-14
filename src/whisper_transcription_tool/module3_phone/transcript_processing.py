"""
Transcript processing utilities for phone call recordings.
Handles transcript formatting, speaker identification, and other transcript-related tasks.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from ..core.logging_setup import get_logger
from ..core.models import OutputFormat

logger = get_logger(__name__)


class ChannelMapping:
    """Enum für Channel-zu-Speaker Mapping."""
    MICROPHONE = "microphone"
    SYSTEM_AUDIO = "system_audio"


class SpeakerRole:
    """Enum für Speaker-Rollen."""
    LOCAL_USER = "local_user"  # Der lokale Nutzer ("Ich")
    REMOTE_USER = "remote_user"  # Der Gesprächspartner


def parse_json_transcript(json_text: str) -> List[Dict]:
    """
    Parse a JSON transcript into segments with comprehensive error handling.

    Args:
        json_text: JSON transcript text or file path

    Returns:
        List of transcript segments
    """
    try:
        # Handle different input types
        if json_text is None:
            logger.warning("Received None as JSON transcript input")
            return []

        if isinstance(json_text, str):
            # Check if it's a file path
            if json_text.endswith('.json') and os.path.exists(json_text):
                logger.debug(f"Reading JSON transcript from file: {json_text}")
                with open(json_text, 'r', encoding='utf-8') as f:
                    json_text = f.read()

            # Parse JSON string
            try:
                data = json.loads(json_text)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON format: {e}")
                logger.debug(f"JSON content preview: {json_text[:200]}...")
                return []

        elif isinstance(json_text, dict):
            # Already parsed JSON
            data = json_text
        else:
            logger.error(f"Unsupported JSON transcript input type: {type(json_text)}")
            return []

        # Extract segments with validation
        if isinstance(data, dict):
            if "segments" in data:
                segments = data["segments"]
                if isinstance(segments, list):
                    logger.debug(f"Successfully parsed {len(segments)} segments")
                    # Validate segment structure
                    valid_segments = []
                    for i, segment in enumerate(segments):
                        if isinstance(segment, dict):
                            # Ensure required fields exist
                            if "text" in segment:
                                # Add default values for missing fields
                                if "start" not in segment:
                                    segment["start"] = 0.0
                                if "end" not in segment:
                                    segment["end"] = segment.get("start", 0.0)
                                valid_segments.append(segment)
                            else:
                                logger.warning(f"Segment {i} missing 'text' field: {segment}")
                        else:
                            logger.warning(f"Segment {i} is not a dictionary: {type(segment)}")

                    logger.debug(f"Validated {len(valid_segments)} out of {len(segments)} segments")
                    return valid_segments
                else:
                    logger.error(f"'segments' field is not a list: {type(segments)}")
            else:
                logger.warning("JSON data does not contain 'segments' field")
                # Try to handle direct segment list
                if isinstance(data, list):
                    logger.debug("Treating input as direct segment list")
                    return data
        else:
            logger.error(f"JSON data is not a dictionary: {type(data)}")

        return []

    except FileNotFoundError as e:
        logger.error(f"Transcript file not found: {e}")
        return []
    except PermissionError as e:
        logger.error(f"Permission denied reading transcript file: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error parsing JSON transcript: {e}")
        logger.debug(f"Input type: {type(json_text)}, Input preview: {str(json_text)[:100]}...")
        return []


def merge_transcripts_by_channel_mapping(
    mic_transcript_json: str,
    system_transcript_json: str,
    user_name: str = "Ich",
    contact_name: str = "Gesprächspartner",
    output_format: str = "txt",
    confidence_threshold: float = 0.0
) -> str:
    """
    Merge transcripts based on channel mapping with 100% confidence.

    Channel-Based Speaker Assignment:
    - MIKROFONKANAL (input_device) = Lokaler User (user_name)
    - BLACKHOLE SYSTEM-AUDIO (output_device) = Gesprächspartner (contact_name)

    Args:
        mic_transcript_json: JSON transcript from microphone channel
        system_transcript_json: JSON transcript from system audio channel
        user_name: Name of the local user (default: "Ich")
        contact_name: Name of the conversation partner
        output_format: Output format (txt, md, json)
        confidence_threshold: Minimum confidence for segments (0.0-1.0)

    Returns:
        Merged conversation transcript with channel-based speaker mapping

    Raises:
        ValueError: If input parameters are invalid
        FileNotFoundError: If transcript files don't exist
        RuntimeError: If merging fails due to data issues
    """
    logger.info(f"Merging transcripts by channel mapping: {user_name} (mic) + {contact_name} (system)")

    try:
        # Validate input parameters
        if not mic_transcript_json:
            raise ValueError("Microphone transcript JSON is required")
        if not system_transcript_json:
            raise ValueError("System transcript JSON is required")
        if not user_name.strip():
            raise ValueError("User name cannot be empty")
        if not contact_name.strip():
            raise ValueError("Contact name cannot be empty")
        if not 0.0 <= confidence_threshold <= 1.0:
            raise ValueError(f"Confidence threshold must be between 0.0 and 1.0, got {confidence_threshold}")

        # Parse JSON transcripts with error handling
        logger.debug("Parsing microphone transcript...")
        mic_segments = parse_json_transcript(mic_transcript_json)

        logger.debug("Parsing system audio transcript...")
        system_segments = parse_json_transcript(system_transcript_json)

        logger.debug(f"Parsed {len(mic_segments)} microphone segments and {len(system_segments)} system segments")

        # Check if we have any segments to work with
        if not mic_segments and not system_segments:
            logger.warning("No segments found in either transcript")
            return _create_empty_transcript_output(user_name, contact_name, output_format)

        if not mic_segments:
            logger.warning("No microphone segments found - conversation may be incomplete")
        if not system_segments:
            logger.warning("No system audio segments found - conversation may be incomplete")

        # Apply confidence threshold filtering
        original_mic_count = len(mic_segments)
        original_sys_count = len(system_segments)

        if confidence_threshold > 0:
            mic_segments = [seg for seg in mic_segments if seg.get('confidence', 1.0) >= confidence_threshold]
            system_segments = [seg for seg in system_segments if seg.get('confidence', 1.0) >= confidence_threshold]
            logger.debug(f"After confidence filtering ({confidence_threshold}): "
                        f"mic: {original_mic_count} -> {len(mic_segments)}, "
                        f"system: {original_sys_count} -> {len(system_segments)}")

        # Add channel-based speaker information with 100% confidence
        try:
            for i, segment in enumerate(mic_segments):
                segment["speaker"] = user_name
                segment["channel"] = ChannelMapping.MICROPHONE
                segment["speaker_role"] = SpeakerRole.LOCAL_USER
                segment["channel_confidence"] = 1.0  # Hardware-based = 100% confidence
                segment["segment_index"] = i

                # Validate segment timing
                start_time = segment.get("start", 0.0)
                end_time = segment.get("end", start_time)
                if end_time < start_time:
                    logger.warning(f"Microphone segment {i}: end_time ({end_time}) < start_time ({start_time})")
                    segment["end"] = start_time

            for i, segment in enumerate(system_segments):
                segment["speaker"] = contact_name
                segment["channel"] = ChannelMapping.SYSTEM_AUDIO
                segment["speaker_role"] = SpeakerRole.REMOTE_USER
                segment["channel_confidence"] = 1.0  # Hardware-based = 100% confidence
                segment["segment_index"] = i

                # Validate segment timing
                start_time = segment.get("start", 0.0)
                end_time = segment.get("end", start_time)
                if end_time < start_time:
                    logger.warning(f"System segment {i}: end_time ({end_time}) < start_time ({start_time})")
                    segment["end"] = start_time

        except Exception as e:
            logger.error(f"Error adding channel metadata to segments: {e}")
            raise RuntimeError(f"Failed to process segment metadata: {e}")

        # Combine and sort segments by start time
        try:
            all_segments = mic_segments + system_segments
            all_segments.sort(key=lambda x: x.get("start", 0))
            logger.info(f"Successfully merged {len(all_segments)} total segments")
        except Exception as e:
            logger.error(f"Error combining and sorting segments: {e}")
            raise RuntimeError(f"Failed to merge segments: {e}")

        # Format output based on requested format
        try:
            if output_format.lower() == "json":
                return json.dumps({
                    "metadata": {
                        "channel_mapping": {
                            ChannelMapping.MICROPHONE: user_name,
                            ChannelMapping.SYSTEM_AUDIO: contact_name
                        },
                        "confidence_threshold": confidence_threshold,
                        "total_segments": len(all_segments),
                        "microphone_segments": len(mic_segments),
                        "system_segments": len(system_segments),
                        "original_microphone_segments": original_mic_count,
                        "original_system_segments": original_sys_count,
                        "processing_timestamp": datetime.now().isoformat()
                    },
                    "segments": all_segments
                }, indent=2, ensure_ascii=False)

            elif output_format.lower() == "md":
                return format_channel_mapped_transcript_markdown(all_segments, user_name, contact_name)

            else:  # Default to txt
                return format_channel_mapped_transcript_text(all_segments, user_name, contact_name)

        except Exception as e:
            logger.error(f"Error formatting output as {output_format}: {e}")
            raise RuntimeError(f"Failed to format transcript output: {e}")

    except ValueError as e:
        logger.error(f"Invalid input parameters: {e}")
        raise
    except FileNotFoundError as e:
        logger.error(f"Transcript file not found: {e}")
        raise
    except RuntimeError as e:
        logger.error(f"Runtime error during transcript merging: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during channel-based transcript merging: {e}")
        raise RuntimeError(f"Unexpected error: {e}")


def _create_empty_transcript_output(
    user_name: str,
    contact_name: str,
    output_format: str
) -> str:
    """Create an empty transcript output when no segments are found."""
    if output_format.lower() == "json":
        return json.dumps({
            "metadata": {
                "channel_mapping": {
                    ChannelMapping.MICROPHONE: user_name,
                    ChannelMapping.SYSTEM_AUDIO: contact_name
                },
                "total_segments": 0,
                "microphone_segments": 0,
                "system_segments": 0,
                "error": "No segments found in transcripts"
            },
            "segments": []
        }, indent=2)
    elif output_format.lower() == "md":
        return f"""# Telefongesprächstranskript

## Fehler
Keine Segmente in den Transkripten gefunden.

**Teilnehmer:**
- {user_name} (Mikrofon)
- {contact_name} (System-Audio)
"""
    else:
        return f"""TELEFONGESPRÄCHSTRANSKRIPT
===============================

FEHLER: Keine Segmente in den Transkripten gefunden.

Teilnehmer:
- {user_name} (Mikrofon)
- {contact_name} (System-Audio)
"""


def merge_transcripts_with_timestamps(
    transcript_a_json: str,
    transcript_b_json: str,
    speaker_a_name: str = "Speaker A",
    speaker_b_name: str = "Speaker B",
    output_format: str = "txt",
    channel_mapping: Optional[Dict[str, str]] = None,
    use_channel_based_detection: bool = False,
    confidence_threshold: float = 0.0
) -> str:
    """
    Merge two JSON transcripts into a conversation format with timestamps.
    Enhanced with optional channel-mapping support for better speaker detection.

    Args:
        transcript_a_json: JSON transcript from first audio track
        transcript_b_json: JSON transcript from second audio track
        speaker_a_name: Name for speaker A
        speaker_b_name: Name for speaker B
        output_format: Output format (txt, md, json)
        channel_mapping: Optional mapping of channels to speakers
                        {"channel_a": "mic", "channel_b": "system"}
        use_channel_based_detection: Use channel-based speaker detection if available
        confidence_threshold: Minimum confidence for segments (0.0-1.0)

    Returns:
        Merged transcript
    """
    logger.info(f"Merging transcripts: {speaker_a_name} + {speaker_b_name} "
                f"(channel_mapping: {use_channel_based_detection})")

    # Parse JSON transcripts
    segments_a = parse_json_transcript(transcript_a_json)
    segments_b = parse_json_transcript(transcript_b_json)

    logger.debug(f"Parsed {len(segments_a)} + {len(segments_b)} segments")

    # Apply confidence threshold filtering if specified
    if confidence_threshold > 0:
        original_count_a = len(segments_a)
        original_count_b = len(segments_b)

        segments_a = [seg for seg in segments_a if seg.get('confidence', 1.0) >= confidence_threshold]
        segments_b = [seg for seg in segments_b if seg.get('confidence', 1.0) >= confidence_threshold]

        logger.debug(f"Applied confidence threshold {confidence_threshold}: "
                    f"A: {original_count_a} -> {len(segments_a)}, "
                    f"B: {original_count_b} -> {len(segments_b)}")

    # Enhanced speaker assignment with channel mapping support
    if use_channel_based_detection and channel_mapping:
        # Use channel-based speaker detection
        channel_a = channel_mapping.get("channel_a", "unknown")
        channel_b = channel_mapping.get("channel_b", "unknown")

        # Determine speaker roles based on channels
        if channel_a == ChannelMapping.MICROPHONE:
            speaker_a_role = SpeakerRole.LOCAL_USER
            speaker_b_role = SpeakerRole.REMOTE_USER
        elif channel_a == ChannelMapping.SYSTEM_AUDIO:
            speaker_a_role = SpeakerRole.REMOTE_USER
            speaker_b_role = SpeakerRole.LOCAL_USER
        else:
            # Fallback to generic assignment
            speaker_a_role = "speaker_a"
            speaker_b_role = "speaker_b"

        # Add enhanced metadata to segments
        for segment in segments_a:
            segment["speaker"] = speaker_a_name
            segment["channel"] = channel_a
            segment["speaker_role"] = speaker_a_role
            segment["channel_confidence"] = 1.0 if channel_a in [ChannelMapping.MICROPHONE, ChannelMapping.SYSTEM_AUDIO] else 0.5

        for segment in segments_b:
            segment["speaker"] = speaker_b_name
            segment["channel"] = channel_b
            segment["speaker_role"] = speaker_b_role
            segment["channel_confidence"] = 1.0 if channel_b in [ChannelMapping.MICROPHONE, ChannelMapping.SYSTEM_AUDIO] else 0.5

        logger.info(f"Applied channel-based speaker detection: "
                   f"A={channel_a}→{speaker_a_name}, B={channel_b}→{speaker_b_name}")

    else:
        # Legacy speaker assignment (backward compatibility)
        for segment in segments_a:
            segment["speaker"] = speaker_a_name
            segment["speaker_role"] = "speaker_a"
            segment["channel_confidence"] = 0.5  # Unknown channel = lower confidence

        for segment in segments_b:
            segment["speaker"] = speaker_b_name
            segment["speaker_role"] = "speaker_b"
            segment["channel_confidence"] = 0.5  # Unknown channel = lower confidence

    # Combine and sort segments by start time
    all_segments = segments_a + segments_b
    all_segments.sort(key=lambda x: x.get("start", 0))

    logger.info(f"Successfully merged {len(all_segments)} total segments")

    # Enhanced output formatting
    if output_format.lower() == "json":
        metadata = {
            "speaker_mapping": {
                "speaker_a": speaker_a_name,
                "speaker_b": speaker_b_name
            },
            "confidence_threshold": confidence_threshold,
            "total_segments": len(all_segments),
            "segments_a": len(segments_a),
            "segments_b": len(segments_b),
            "channel_mapping_used": use_channel_based_detection
        }

        if channel_mapping:
            metadata["channel_mapping"] = channel_mapping

        return json.dumps({
            "metadata": metadata,
            "segments": all_segments
        }, indent=2)

    elif output_format.lower() == "md":
        # Use enhanced formatting if channel mapping was used
        if use_channel_based_detection and any(seg.get("channel") for seg in all_segments):
            return format_channel_mapped_transcript_markdown(all_segments, speaker_a_name, speaker_b_name)
        else:
            return format_transcript_markdown(all_segments, speaker_a_name, speaker_b_name)

    else:  # Default to txt
        # Use enhanced formatting if channel mapping was used
        if use_channel_based_detection and any(seg.get("channel") for seg in all_segments):
            return format_channel_mapped_transcript_text(all_segments, speaker_a_name, speaker_b_name)
        else:
            return format_transcript_text(all_segments, speaker_a_name, speaker_b_name)


def format_channel_mapped_transcript_text(
    segments: List[Dict],
    user_name: str,
    contact_name: str
) -> str:
    """
    Format channel-mapped transcript segments as plain text with enhanced metadata.

    Args:
        segments: List of transcript segments with channel information
        user_name: Name of the local user
        contact_name: Name of the conversation partner

    Returns:
        Formatted transcript with channel information
    """
    lines = []
    lines.append("TELEFONGESPRÄCHSTRANSKRIPT")
    lines.append("=" * 50)
    lines.append("")
    lines.append("CHANNEL-BASED SPEAKER MAPPING:")
    lines.append(f"🎤 Mikrofon-Kanal: {user_name}")
    lines.append(f"🔊 System-Audio-Kanal: {contact_name}")
    lines.append("")
    lines.append(f"Gesamtsegmente: {len(segments)}")
    lines.append("")

    # Count segments per channel
    mic_count = sum(1 for seg in segments if seg.get('channel') == ChannelMapping.MICROPHONE)
    sys_count = sum(1 for seg in segments if seg.get('channel') == ChannelMapping.SYSTEM_AUDIO)
    lines.append(f"Segmente pro Kanal:")
    lines.append(f"  - Mikrofon: {mic_count}")
    lines.append(f"  - System-Audio: {sys_count}")
    lines.append("")
    lines.append("TRANSKRIPT:")
    lines.append("-" * 30)

    current_speaker = None

    for i, segment in enumerate(segments):
        speaker = segment.get("speaker", "Unknown")
        text = segment.get("text", "").strip()
        start_time = segment.get("start", 0)
        channel = segment.get("channel", "unknown")
        confidence = segment.get("confidence", 0.0)
        channel_confidence = segment.get("channel_confidence", 1.0)

        # Format timestamp
        timestamp = format_timestamp(start_time)

        # Channel indicator
        channel_indicator = "🎤" if channel == ChannelMapping.MICROPHONE else "🔊"

        # Add speaker change
        if speaker != current_speaker:
            lines.append("")
            lines.append(f"{channel_indicator} {speaker} [{timestamp}] (Ch: {channel_confidence:.0%}):")
            current_speaker = speaker

        # Add text with confidence if available
        if confidence > 0:
            lines.append(f"   {text} (conf: {confidence:.2f})")
        else:
            lines.append(f"   {text}")

    return "\n".join(lines)


def format_channel_mapped_transcript_markdown(
    segments: List[Dict],
    user_name: str,
    contact_name: str
) -> str:
    """
    Format channel-mapped transcript segments as Markdown with enhanced metadata.

    Args:
        segments: List of transcript segments with channel information
        user_name: Name of the local user
        contact_name: Name of the conversation partner

    Returns:
        Formatted transcript in Markdown with channel information
    """
    lines = []
    lines.append("# Telefongesprächstranskript")
    lines.append("")
    lines.append("## Channel-Based Speaker Mapping")
    lines.append("")
    lines.append("| Kanal | Speaker | Rolle |")
    lines.append("|-------|---------|-------|")
    lines.append(f"| 🎤 Mikrofon | {user_name} | Lokaler Nutzer |")
    lines.append(f"| 🔊 System-Audio | {contact_name} | Gesprächspartner |")
    lines.append("")

    # Statistics
    mic_count = sum(1 for seg in segments if seg.get('channel') == ChannelMapping.MICROPHONE)
    sys_count = sum(1 for seg in segments if seg.get('channel') == ChannelMapping.SYSTEM_AUDIO)
    total_duration = max((seg.get('end', seg.get('start', 0)) for seg in segments), default=0)

    lines.append("## Statistiken")
    lines.append("")
    lines.append(f"- **Gesamtsegmente:** {len(segments)}")
    lines.append(f"- **Mikrofon-Segmente:** {mic_count}")
    lines.append(f"- **System-Audio-Segmente:** {sys_count}")
    lines.append(f"- **Gesamtdauer:** {format_timestamp(total_duration)}")
    lines.append("")

    lines.append("## Transkript")
    lines.append("")

    current_speaker = None

    for segment in segments:
        speaker = segment.get("speaker", "Unknown")
        text = segment.get("text", "").strip()
        start_time = segment.get("start", 0)
        end_time = segment.get("end", start_time)
        channel = segment.get("channel", "unknown")
        confidence = segment.get("confidence", 0.0)
        channel_confidence = segment.get("channel_confidence", 1.0)

        # Format timestamps
        start_timestamp = format_timestamp(start_time)
        duration = end_time - start_time

        # Channel indicator
        channel_indicator = "🎤" if channel == ChannelMapping.MICROPHONE else "🔊"

        # Add speaker change
        if speaker != current_speaker:
            lines.append("")
            lines.append(f"### {channel_indicator} {speaker}")
            lines.append(f"*Zeit: {start_timestamp} | Kanal-Konfidenz: {channel_confidence:.0%}*")
            lines.append("")
            current_speaker = speaker

        # Add text with metadata
        confidence_info = f" *(Konfidenz: {confidence:.2f})*" if confidence > 0 else ""
        lines.append(f"**{start_timestamp}** ({duration:.1f}s): {text}{confidence_info}")
        lines.append("")

    return "\n".join(lines)


def format_transcript_text(
    segments: List[Dict],
    speaker_a_name: str,
    speaker_b_name: str
) -> str:
    """
    Format transcript segments as plain text.
    
    Args:
        segments: List of transcript segments
        speaker_a_name: Name for speaker A
        speaker_b_name: Name for speaker B
        
    Returns:
        Formatted transcript
    """
    lines = []
    lines.append("Telefongesprächstranskript")
    lines.append("=========================")
    lines.append("")
    lines.append(f"Teilnehmer: {speaker_a_name}, {speaker_b_name}")
    lines.append("")
    lines.append("Transkript:")
    lines.append("")
    
    current_speaker = None
    
    for segment in segments:
        speaker = segment.get("speaker", "Unknown")
        text = segment.get("text", "").strip()
        start_time = segment.get("start", 0)
        
        # Format timestamp
        timestamp = format_timestamp(start_time)
        
        # Add speaker change
        if speaker != current_speaker:
            lines.append("")
            lines.append(f"{speaker} [{timestamp}]:")
            current_speaker = speaker
        
        # Add text
        lines.append(f"  {text}")
    
    return "\n".join(lines)


def format_transcript_markdown(
    segments: List[Dict],
    speaker_a_name: str,
    speaker_b_name: str
) -> str:
    """
    Format transcript segments as Markdown.
    
    Args:
        segments: List of transcript segments
        speaker_a_name: Name for speaker A
        speaker_b_name: Name for speaker B
        
    Returns:
        Formatted transcript
    """
    lines = []
    lines.append("# Telefongesprächstranskript")
    lines.append("")
    lines.append("## Teilnehmer")
    lines.append(f"- {speaker_a_name}")
    lines.append(f"- {speaker_b_name}")
    lines.append("")
    lines.append("## Transkript")
    lines.append("")
    
    current_speaker = None
    
    for segment in segments:
        speaker = segment.get("speaker", "Unknown")
        text = segment.get("text", "").strip()
        start_time = segment.get("start", 0)
        
        # Format timestamp
        timestamp = format_timestamp(start_time)
        
        # Add speaker change
        if speaker != current_speaker:
            lines.append("")
            lines.append(f"### {speaker} [{timestamp}]")
            current_speaker = speaker
        
        # Add text
        lines.append(text)
    
    return "\n".join(lines)


def format_timestamp(seconds: float) -> str:
    """
    Format time in seconds to MM:SS format.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted time string
    """
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    
    return f"{minutes:02d}:{seconds:02d}"


def identify_speakers(
    transcript_a: str,
    transcript_b: str
) -> Tuple[str, str]:
    """
    Attempt to identify speakers based on transcript content.
    
    Args:
        transcript_a: Transcript from first audio track
        transcript_b: Transcript from second audio track
        
    Returns:
        Tuple of (speaker_a_name, speaker_b_name)
    """
    # This is a placeholder for a more advanced implementation
    # that would use NLP to identify speakers based on content
    
    # For now, we'll use simple heuristics
    
    # Default names
    speaker_a_name = "Anrufer"
    speaker_b_name = "Empfänger"
    
    # Check for common greeting patterns
    if re.search(r'\b(hallo|guten tag|grüß|grüss|servus|moin)\b', transcript_a.lower()):
        # First speaker is likely the caller
        speaker_a_name = "Anrufer"
        speaker_b_name = "Empfänger"
    
    if re.search(r'\b(hallo|guten tag|grüß|grüss|servus|moin)\b', transcript_b.lower()):
        # Second speaker is likely the caller
        speaker_a_name = "Empfänger"
        speaker_b_name = "Anrufer"
    
    return speaker_a_name, speaker_b_name


def extract_key_information(transcript: str) -> Dict:
    """
    Extract key information from a transcript.
    
    Args:
        transcript: Transcript text
        
    Returns:
        Dictionary with extracted information
    """
    info = {
        "names": [],
        "phone_numbers": [],
        "email_addresses": [],
        "dates": [],
        "key_topics": []
    }
    
    # Extract phone numbers
    phone_pattern = r'\b(\+?[\d\s\(\)-]{8,})\b'
    info["phone_numbers"] = re.findall(phone_pattern, transcript)
    
    # Extract email addresses
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    info["email_addresses"] = re.findall(email_pattern, transcript)
    
    # Extract dates
    date_pattern = r'\b(\d{1,2}[./]\d{1,2}[./]\d{2,4})\b'
    info["dates"] = re.findall(date_pattern, transcript)
    
    # This is a placeholder for more advanced NLP-based extraction
    # In a real implementation, we would use NLP to extract names and key topics
    
    return info
