#!/usr/bin/env python3
"""
Test script for Channel-Based Speaker Mapping validation.

This script provides comprehensive tests for the channel mapping functionality
to ensure robust speaker detection and transcript merging.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, List

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from whisper_transcription_tool.module3_phone.channel_speaker_mapping import (
    ChannelMappingConfig,
    validate_channel_mapping,
    detect_speaker_by_channel,
    get_recommended_channel_setup,
    create_channel_mapping_from_session
)
from whisper_transcription_tool.module3_phone.transcript_processing import (
    merge_transcripts_by_channel_mapping,
    merge_transcripts_with_timestamps,
    ChannelMapping,
    SpeakerRole
)
from whisper_transcription_tool.module3_phone.models import RecordingConfig, RecordingSession
from whisper_transcription_tool.core.logging_setup import get_logger

logger = get_logger(__name__)


def create_test_transcript_data() -> Dict[str, Dict]:
    """Create test transcript data for validation."""

    # Microphone transcript (local user)
    mic_transcript = {
        "segments": [
            {
                "text": "Hallo, ich bin hier.",
                "start": 0.0,
                "end": 2.5,
                "confidence": 0.95
            },
            {
                "text": "Können Sie mich hören?",
                "start": 3.0,
                "end": 5.0,
                "confidence": 0.92
            },
            {
                "text": "Gut, dann können wir anfangen.",
                "start": 8.0,
                "end": 10.5,
                "confidence": 0.88
            }
        ]
    }

    # System audio transcript (remote user)
    sys_transcript = {
        "segments": [
            {
                "text": "Ja, hallo! Ich höre Sie gut.",
                "start": 5.5,
                "end": 7.5,
                "confidence": 0.93
            },
            {
                "text": "Perfekt, ich bin bereit.",
                "start": 11.0,
                "end": 13.0,
                "confidence": 0.90
            },
            {
                "text": "Haben Sie noch Fragen?",
                "start": 15.0,
                "end": 17.0,
                "confidence": 0.89
            }
        ]
    }

    return {
        "microphone": mic_transcript,
        "system": sys_transcript
    }


def create_test_files(test_data: Dict[str, Dict]) -> Dict[str, str]:
    """Create temporary test transcript files."""
    temp_dir = tempfile.mkdtemp(prefix="channel_mapping_test_")
    file_paths = {}

    for channel, transcript_data in test_data.items():
        file_path = os.path.join(temp_dir, f"{channel}_transcript.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(transcript_data, f, indent=2, ensure_ascii=False)
        file_paths[channel] = file_path

    logger.info(f"Created test files in: {temp_dir}")
    return file_paths


def test_channel_mapping_config():
    """Test channel mapping configuration validation."""
    print("\n" + "="*50)
    print("TEST: Channel Mapping Configuration")
    print("="*50)

    # Test valid configuration
    config = ChannelMappingConfig(
        microphone_device_id="0",
        system_audio_device_id="1",
        user_name="Dennis",
        contact_name="Test Partner"
    )

    print(f"✅ Valid config created: {config.user_name} <-> {config.contact_name}")

    # Test validation
    validation_result = validate_channel_mapping(config)

    print(f"📊 Validation Result:")
    print(f"   - Valid: {validation_result.is_valid}")
    print(f"   - Microphone available: {validation_result.microphone_available}")
    print(f"   - System audio available: {validation_result.system_audio_available}")

    if validation_result.errors:
        print(f"   - Errors: {validation_result.errors}")
    if validation_result.warnings:
        print(f"   - Warnings: {validation_result.warnings}")

    return validation_result.is_valid


def test_speaker_detection():
    """Test hardware-based speaker detection."""
    print("\n" + "="*50)
    print("TEST: Hardware-Based Speaker Detection")
    print("="*50)

    # Create test data and files
    test_data = create_test_transcript_data()
    test_files = create_test_files(test_data)

    try:
        config = ChannelMappingConfig(
            microphone_device_id="0",
            system_audio_device_id="1",
            user_name="Dennis",
            contact_name="Kunde A"
        )

        detection_result = detect_speaker_by_channel(test_files, config)

        print(f"📊 Detection Result:")
        print(f"   - Confidence: {detection_result.confidence:.1%}")
        print(f"   - Channel mapping used: {detection_result.channel_mapping_used}")
        print(f"   - Detection method: {detection_result.detection_method}")
        print(f"   - Speaker mapping: {detection_result.speaker_mapping}")

        if detection_result.metadata:
            print(f"   - Metadata keys: {list(detection_result.metadata.keys())}")

        return detection_result.confidence > 0.8

    finally:
        # Cleanup test files
        for file_path in test_files.values():
            try:
                os.remove(file_path)
            except:
                pass


def test_transcript_merging():
    """Test channel-based transcript merging."""
    print("\n" + "="*50)
    print("TEST: Channel-Based Transcript Merging")
    print("="*50)

    # Create test data
    test_data = create_test_transcript_data()

    try:
        # Test merging with channel mapping
        result = merge_transcripts_by_channel_mapping(
            mic_transcript_json=json.dumps(test_data["microphone"]),
            system_transcript_json=json.dumps(test_data["system"]),
            user_name="Dennis",
            contact_name="Kunde A",
            output_format="json"
        )

        # Parse result to validate
        result_data = json.loads(result)

        print(f"📊 Merge Result:")
        print(f"   - Total segments: {result_data['metadata']['total_segments']}")
        print(f"   - Microphone segments: {result_data['metadata']['microphone_segments']}")
        print(f"   - System segments: {result_data['metadata']['system_segments']}")

        # Validate segments have correct speaker assignments
        segments = result_data["segments"]
        mic_segments = [s for s in segments if s.get('channel') == ChannelMapping.MICROPHONE]
        sys_segments = [s for s in segments if s.get('channel') == ChannelMapping.SYSTEM_AUDIO]

        print(f"   - Mic segments speaker: {mic_segments[0]['speaker'] if mic_segments else 'None'}")
        print(f"   - Sys segments speaker: {sys_segments[0]['speaker'] if sys_segments else 'None'}")

        # Test different output formats
        txt_result = merge_transcripts_by_channel_mapping(
            mic_transcript_json=json.dumps(test_data["microphone"]),
            system_transcript_json=json.dumps(test_data["system"]),
            user_name="Dennis",
            contact_name="Kunde A",
            output_format="txt"
        )

        md_result = merge_transcripts_by_channel_mapping(
            mic_transcript_json=json.dumps(test_data["microphone"]),
            system_transcript_json=json.dumps(test_data["system"]),
            user_name="Dennis",
            contact_name="Kunde A",
            output_format="md"
        )

        print(f"   - TXT output length: {len(txt_result)} chars")
        print(f"   - MD output length: {len(md_result)} chars")

        return len(segments) > 0 and all(s.get('speaker') for s in segments)

    except Exception as e:
        print(f"❌ Error in transcript merging: {e}")
        return False


def test_enhanced_merge_function():
    """Test the enhanced merge_transcripts_with_timestamps function."""
    print("\n" + "="*50)
    print("TEST: Enhanced Merge Function")
    print("="*50)

    test_data = create_test_transcript_data()

    try:
        # Test with channel mapping
        channel_mapping = {
            "channel_a": ChannelMapping.MICROPHONE,
            "channel_b": ChannelMapping.SYSTEM_AUDIO
        }

        result = merge_transcripts_with_timestamps(
            transcript_a_json=json.dumps(test_data["microphone"]),
            transcript_b_json=json.dumps(test_data["system"]),
            speaker_a_name="Dennis",
            speaker_b_name="Kunde A",
            output_format="json",
            channel_mapping=channel_mapping,
            use_channel_based_detection=True,
            confidence_threshold=0.85
        )

        result_data = json.loads(result)

        print(f"📊 Enhanced Merge Result:")
        print(f"   - Total segments: {result_data['metadata']['total_segments']}")
        print(f"   - Channel mapping used: {result_data['metadata']['channel_mapping_used']}")

        if 'channel_mapping' in result_data['metadata']:
            print(f"   - Channel mapping: {result_data['metadata']['channel_mapping']}")

        # Validate channel confidence
        segments = result_data["segments"]
        channel_confidences = [s.get('channel_confidence', 0) for s in segments]
        avg_confidence = sum(channel_confidences) / len(channel_confidences) if channel_confidences else 0

        print(f"   - Average channel confidence: {avg_confidence:.1%}")

        return avg_confidence > 0.9  # Hardware-based should be high confidence

    except Exception as e:
        print(f"❌ Error in enhanced merge function: {e}")
        return False


def test_error_handling():
    """Test error handling capabilities."""
    print("\n" + "="*50)
    print("TEST: Error Handling")
    print("="*50)

    tests_passed = 0
    total_tests = 4

    # Test 1: Invalid JSON
    try:
        result = merge_transcripts_by_channel_mapping(
            mic_transcript_json="invalid json",
            system_transcript_json="{}",
            user_name="Test",
            contact_name="Test"
        )
        if "FEHLER" in result or "error" in result.lower():
            print("✅ Test 1: Invalid JSON handled correctly")
            tests_passed += 1
        else:
            print("❌ Test 1: Invalid JSON not handled properly")
    except Exception as e:
        print(f"✅ Test 1: Invalid JSON properly raises exception: {type(e).__name__}")
        tests_passed += 1

    # Test 2: Empty user name
    try:
        result = merge_transcripts_by_channel_mapping(
            mic_transcript_json="{}",
            system_transcript_json="{}",
            user_name="",
            contact_name="Test"
        )
        print("❌ Test 2: Empty user name should raise ValueError")
    except ValueError:
        print("✅ Test 2: Empty user name properly raises ValueError")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 2: Unexpected exception: {type(e).__name__}")

    # Test 3: Invalid confidence threshold
    try:
        result = merge_transcripts_by_channel_mapping(
            mic_transcript_json="{}",
            system_transcript_json="{}",
            user_name="Test",
            contact_name="Test",
            confidence_threshold=1.5  # Invalid: > 1.0
        )
        print("❌ Test 3: Invalid confidence threshold should raise ValueError")
    except ValueError:
        print("✅ Test 3: Invalid confidence threshold properly raises ValueError")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 3: Unexpected exception: {type(e).__name__}")

    # Test 4: Non-existent file path
    try:
        result = merge_transcripts_by_channel_mapping(
            mic_transcript_json="/non/existent/file.json",
            system_transcript_json="{}",
            user_name="Test",
            contact_name="Test"
        )
        if "FEHLER" in result or len(result) < 100:
            print("✅ Test 4: Non-existent file handled gracefully")
            tests_passed += 1
        else:
            print("❌ Test 4: Non-existent file not handled properly")
    except Exception:
        print("✅ Test 4: Non-existent file properly raises exception")
        tests_passed += 1

    print(f"📊 Error handling tests: {tests_passed}/{total_tests} passed")
    return tests_passed == total_tests


def test_recommended_setup():
    """Test recommended channel setup detection."""
    print("\n" + "="*50)
    print("TEST: Recommended Channel Setup")
    print("="*50)

    try:
        recommendation = get_recommended_channel_setup()

        print(f"📊 Recommendation Result:")
        print(f"   - Status: {recommendation.get('status', 'unknown')}")
        print(f"   - Confidence: {recommendation.get('confidence', 'unknown')}")
        print(f"   - Devices found: {recommendation.get('devices_found', 0)}")
        print(f"   - BlackHole available: {recommendation.get('blackhole_available', False)}")
        print(f"   - Microphone available: {recommendation.get('microphone_available', False)}")

        if 'message' in recommendation:
            print(f"   - Message: {recommendation['message']}")

        if 'recommended_config' in recommendation:
            config = recommendation['recommended_config']
            print(f"   - Recommended mic: {config.get('microphone_device', {}).get('name', 'Unknown')}")
            print(f"   - Recommended system: {config.get('system_audio_device', {}).get('name', 'Unknown')}")

        return recommendation.get('status') == 'success'

    except Exception as e:
        print(f"❌ Error getting recommended setup: {e}")
        return False


def run_all_tests():
    """Run all validation tests."""
    print("🚀 CHANNEL-BASED SPEAKER MAPPING VALIDATION")
    print("=" * 60)

    test_results = []

    # Run individual tests
    test_results.append(("Channel Config", test_channel_mapping_config()))
    test_results.append(("Speaker Detection", test_speaker_detection()))
    test_results.append(("Transcript Merging", test_transcript_merging()))
    test_results.append(("Enhanced Merge", test_enhanced_merge_function()))
    test_results.append(("Error Handling", test_error_handling()))
    test_results.append(("Recommended Setup", test_recommended_setup()))

    # Summary
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)

    passed_tests = 0
    total_tests = len(test_results)

    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:20} {status}")
        if result:
            passed_tests += 1

    print("-" * 60)
    print(f"TOTAL: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")

    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Channel-based speaker mapping is ready for production.")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} tests failed. Review the implementation before deployment.")

    return passed_tests == total_tests


if __name__ == "__main__":
    # Configure logging for tests
    import logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    # Run all validation tests
    success = run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if success else 1)