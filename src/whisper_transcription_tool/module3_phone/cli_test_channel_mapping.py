#!/usr/bin/env python3
"""
CLI Test Tool for Channel-Based Speaker Mapping.

This tool provides interactive testing and validation of the channel mapping
functionality for phone call recordings.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from whisper_transcription_tool.module3_phone.channel_speaker_mapping import (
    ChannelMappingConfig,
    validate_channel_mapping,
    detect_speaker_by_channel,
    get_recommended_channel_setup
)
from whisper_transcription_tool.module3_phone.transcript_processing import (
    merge_transcripts_by_channel_mapping,
    merge_transcripts_with_timestamps
)
from whisper_transcription_tool.core.logging_setup import get_logger

logger = get_logger(__name__)


def cmd_list_devices():
    """List available audio devices."""
    print("🎵 AVAILABLE AUDIO DEVICES")
    print("=" * 40)

    try:
        import sounddevice as sd
        devices = sd.query_devices()

        for i, device in enumerate(devices):
            device_type = []
            if device['max_input_channels'] > 0:
                device_type.append("INPUT")
            if device['max_output_channels'] > 0:
                device_type.append("OUTPUT")

            type_str = "/".join(device_type) if device_type else "NONE"
            channels_in = device['max_input_channels']
            channels_out = device['max_output_channels']
            sample_rate = device['default_samplerate']

            print(f"[{i:2d}] {device['name']}")
            print(f"     Type: {type_str}")
            print(f"     Channels: IN={channels_in}, OUT={channels_out}")
            print(f"     Sample Rate: {sample_rate} Hz")

            # Highlight BlackHole devices
            if 'BlackHole' in device['name']:
                print("     🔊 BLACKHOLE DEVICE - Good for system audio capture!")

            print()

    except ImportError:
        print("❌ sounddevice not available. Install with: pip install sounddevice")
    except Exception as e:
        print(f"❌ Error listing devices: {e}")


def cmd_validate_setup(mic_device_id: str, sys_device_id: str, user_name: str, contact_name: str):
    """Validate a channel mapping setup."""
    print("🔍 CHANNEL MAPPING VALIDATION")
    print("=" * 40)

    config = ChannelMappingConfig(
        microphone_device_id=mic_device_id,
        system_audio_device_id=sys_device_id,
        user_name=user_name,
        contact_name=contact_name
    )

    print(f"Configuration:")
    print(f"  - Microphone Device ID: {config.microphone_device_id}")
    print(f"  - System Audio Device ID: {config.system_audio_device_id}")
    print(f"  - User Name: {config.user_name}")
    print(f"  - Contact Name: {config.contact_name}")
    print()

    # Validate
    result = validate_channel_mapping(config)

    print("Validation Results:")
    print(f"  ✅ Overall Valid: {result.is_valid}")
    print(f"  🎤 Microphone Available: {result.microphone_available}")
    print(f"  🔊 System Audio Available: {result.system_audio_available}")

    if result.microphone_info:
        print(f"  📱 Microphone: {result.microphone_info['name']}")
    if result.system_audio_info:
        print(f"  🖥️  System Audio: {result.system_audio_info['name']}")

    if result.errors:
        print(f"  ❌ Errors:")
        for error in result.errors:
            print(f"     - {error}")

    if result.warnings:
        print(f"  ⚠️  Warnings:")
        for warning in result.warnings:
            print(f"     - {warning}")

    return result.is_valid


def cmd_get_recommendation():
    """Get recommended channel setup."""
    print("💡 RECOMMENDED CHANNEL SETUP")
    print("=" * 40)

    recommendation = get_recommended_channel_setup()

    print(f"Status: {recommendation.get('status', 'unknown')}")
    print(f"Confidence: {recommendation.get('confidence', 'unknown')}")
    print(f"Devices Found: {recommendation.get('devices_found', 0)}")
    print()

    if recommendation.get('blackhole_available'):
        print("✅ BlackHole is available for system audio capture")
    else:
        print("❌ BlackHole not found")
        if 'installation_guide' in recommendation:
            guide = recommendation['installation_guide']
            print(f"   Install from: {guide.get('BlackHole', 'N/A')}")

    if recommendation.get('microphone_available'):
        print("✅ Microphone device available")
    else:
        print("❌ No microphone device found")

    if 'recommended_config' in recommendation:
        config = recommendation['recommended_config']
        mic_device = config.get('microphone_device', {})
        sys_device = config.get('system_audio_device', {})

        print("\n🎯 Recommended Configuration:")
        print(f"  - Microphone: [{mic_device.get('id')}] {mic_device.get('name')}")
        print(f"  - System Audio: [{sys_device.get('id')}] {sys_device.get('name')}")
        print(f"  - Sample Rate: {config.get('sample_rate')} Hz")

    if 'message' in recommendation:
        print(f"\n💬 {recommendation['message']}")


def cmd_test_merge(mic_file: str, sys_file: str, user_name: str, contact_name: str, output_format: str = "txt"):
    """Test transcript merging with actual files."""
    print("🔄 TESTING TRANSCRIPT MERGE")
    print("=" * 40)

    # Validate files exist
    if not os.path.exists(mic_file):
        print(f"❌ Microphone transcript file not found: {mic_file}")
        return False

    if not os.path.exists(sys_file):
        print(f"❌ System audio transcript file not found: {sys_file}")
        return False

    print(f"Input Files:")
    print(f"  - Microphone: {mic_file}")
    print(f"  - System Audio: {sys_file}")
    print(f"  - Output Format: {output_format}")
    print()

    try:
        # Read transcript files
        with open(mic_file, 'r', encoding='utf-8') as f:
            mic_content = f.read()

        with open(sys_file, 'r', encoding='utf-8') as f:
            sys_content = f.read()

        # Merge transcripts
        result = merge_transcripts_by_channel_mapping(
            mic_transcript_json=mic_content,
            system_transcript_json=sys_content,
            user_name=user_name,
            contact_name=contact_name,
            output_format=output_format
        )

        print("✅ Merge successful!")
        print(f"Output length: {len(result)} characters")
        print()

        if output_format.lower() == "json":
            # Parse and show statistics
            try:
                data = json.loads(result)
                metadata = data.get('metadata', {})
                print(f"📊 Statistics:")
                print(f"  - Total segments: {metadata.get('total_segments', 0)}")
                print(f"  - Microphone segments: {metadata.get('microphone_segments', 0)}")
                print(f"  - System segments: {metadata.get('system_segments', 0)}")
            except:
                pass

        # Show first 500 characters of output
        print("📄 Output Preview:")
        print("-" * 40)
        print(result[:500])
        if len(result) > 500:
            print("... (truncated)")

        return True

    except Exception as e:
        print(f"❌ Error during merge: {e}")
        return False


def cmd_create_test_data(output_dir: str):
    """Create sample test transcript files."""
    print("📁 CREATING TEST TRANSCRIPT FILES")
    print("=" * 40)

    os.makedirs(output_dir, exist_ok=True)

    # Sample microphone transcript
    mic_transcript = {
        "segments": [
            {
                "text": "Hallo, hier ist Dennis vom Support.",
                "start": 0.0,
                "end": 3.5,
                "confidence": 0.95
            },
            {
                "text": "Wie kann ich Ihnen heute helfen?",
                "start": 4.0,
                "end": 6.5,
                "confidence": 0.92
            },
            {
                "text": "Verstehe, das schauen wir uns an.",
                "start": 12.0,
                "end": 15.0,
                "confidence": 0.88
            },
            {
                "text": "Können Sie bitte Ihren Bildschirm teilen?",
                "start": 20.0,
                "end": 23.0,
                "confidence": 0.90
            }
        ]
    }

    # Sample system audio transcript
    sys_transcript = {
        "segments": [
            {
                "text": "Guten Tag! Ich habe ein Problem mit der Anwendung.",
                "start": 7.0,
                "end": 11.0,
                "confidence": 0.93
            },
            {
                "text": "Die Synchronisation funktioniert nicht richtig.",
                "start": 16.0,
                "end": 19.5,
                "confidence": 0.85
            },
            {
                "text": "Ja, moment mal, wie mache ich das nochmal?",
                "start": 24.0,
                "end": 27.5,
                "confidence": 0.87
            }
        ]
    }

    # Write files
    mic_file = os.path.join(output_dir, "microphone_transcript.json")
    sys_file = os.path.join(output_dir, "system_audio_transcript.json")

    with open(mic_file, 'w', encoding='utf-8') as f:
        json.dump(mic_transcript, f, indent=2, ensure_ascii=False)

    with open(sys_file, 'w', encoding='utf-8') as f:
        json.dump(sys_transcript, f, indent=2, ensure_ascii=False)

    print(f"✅ Created test files:")
    print(f"  - {mic_file}")
    print(f"  - {sys_file}")
    print()
    print(f"💡 Test the merge with:")
    print(f"python {sys.argv[0]} merge --mic {mic_file} --sys {sys_file} --user 'Dennis' --contact 'Kunde'")


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="CLI Test Tool for Channel-Based Speaker Mapping",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available audio devices
  python cli_test_channel_mapping.py devices

  # Get recommended setup
  python cli_test_channel_mapping.py recommend

  # Validate a specific setup
  python cli_test_channel_mapping.py validate --mic 0 --sys 1 --user "Dennis" --contact "Kunde"

  # Create test data
  python cli_test_channel_mapping.py create-test --output ./test_data

  # Test merge with actual files
  python cli_test_channel_mapping.py merge --mic mic.json --sys sys.json --user "Dennis" --contact "Kunde"
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Devices command
    subparsers.add_parser('devices', help='List available audio devices')

    # Recommend command
    subparsers.add_parser('recommend', help='Get recommended channel setup')

    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate channel mapping setup')
    validate_parser.add_argument('--mic', required=True, help='Microphone device ID')
    validate_parser.add_argument('--sys', required=True, help='System audio device ID')
    validate_parser.add_argument('--user', default='Ich', help='User name (default: Ich)')
    validate_parser.add_argument('--contact', default='Gesprächspartner', help='Contact name')

    # Create test command
    create_parser = subparsers.add_parser('create-test', help='Create sample test transcript files')
    create_parser.add_argument('--output', default='./test_transcripts', help='Output directory')

    # Merge test command
    merge_parser = subparsers.add_parser('merge', help='Test transcript merging')
    merge_parser.add_argument('--mic', required=True, help='Microphone transcript file')
    merge_parser.add_argument('--sys', required=True, help='System audio transcript file')
    merge_parser.add_argument('--user', default='Ich', help='User name')
    merge_parser.add_argument('--contact', default='Gesprächspartner', help='Contact name')
    merge_parser.add_argument('--format', default='txt', choices=['txt', 'md', 'json'], help='Output format')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Execute commands
    if args.command == 'devices':
        cmd_list_devices()

    elif args.command == 'recommend':
        cmd_get_recommendation()

    elif args.command == 'validate':
        success = cmd_validate_setup(args.mic, args.sys, args.user, args.contact)
        sys.exit(0 if success else 1)

    elif args.command == 'create-test':
        cmd_create_test_data(args.output)

    elif args.command == 'merge':
        success = cmd_test_merge(args.mic, args.sys, args.user, args.contact, args.format)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()