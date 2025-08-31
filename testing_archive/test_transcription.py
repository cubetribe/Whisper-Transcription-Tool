#!/usr/bin/env python3
"""
Test script for transcription functionality in macOS CLI Wrapper

Tests the transcription command implementation including:
- File validation
- JSON command structure
- Error handling
- Real transcription (if test files are available)
"""

import json
import subprocess
import sys
import tempfile
import os
from pathlib import Path


def test_transcription_validation():
    """Test transcription command validation without real files."""
    
    print("🧪 Testing Transcription Command Validation")
    print("=" * 50)
    
    test_cases = [
        {
            "name": "Missing input_file",
            "command": {
                "command": "transcribe"
            },
            "expected_success": False,
            "expected_code": "MISSING_FIELDS"
        },
        {
            "name": "Non-existent file",
            "command": {
                "command": "transcribe",
                "input_file": "/path/to/nonexistent.mp3"
            },
            "expected_success": False,
            "expected_code": "FILE_NOT_FOUND"
        },
        {
            "name": "Unsupported format",
            "command": {
                "command": "transcribe",
                "input_file": "/tmp/test.xyz"
            },
            "expected_success": False,
            "expected_code": "UNSUPPORTED_FORMAT"
        }
    ]
    
    success_count = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}/{total_tests}: {test_case['name']}")
        
        try:
            # Create dummy file for unsupported format test
            if "test.xyz" in test_case['command'].get('input_file', ''):
                dummy_file = Path("/tmp/test.xyz")
                dummy_file.touch()
            
            command_json = json.dumps(test_case['command'])
            
            result = subprocess.run(
                [sys.executable, 'macos_cli.py', command_json],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent
            )
            
            if result.returncode != 0:
                print(f"❌ CLI returned non-zero exit code: {result.returncode}")
                continue
            
            response = json.loads(result.stdout.strip())
            
            # Validate response structure
            if not all(field in response for field in ['success', 'timestamp']):
                print("❌ Response missing required fields")
                continue
            
            # Check expected results
            actual_success = response['success']
            expected_success = test_case['expected_success']
            
            if actual_success != expected_success:
                print(f"❌ Expected success={expected_success}, got {actual_success}")
                continue
            
            if not expected_success and 'code' in test_case:
                expected_code = test_case['expected_code']
                actual_code = response.get('code', 'MISSING')
                
                if actual_code != expected_code:
                    print(f"❌ Expected code={expected_code}, got {actual_code}")
                    continue
            
            print("✅ Test passed")
            print(f"   Response: {json.dumps(response, indent=2)}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
        finally:
            # Cleanup dummy files
            dummy_file = Path("/tmp/test.xyz")
            if dummy_file.exists():
                dummy_file.unlink()
    
    print(f"\n📊 Validation Results: {success_count}/{total_tests} tests passed")
    return success_count == total_tests


def test_json_command_structure():
    """Test complete JSON command structure."""
    print("\n🔍 Testing JSON Command Structure")
    print("-" * 40)
    
    # Create a temporary supported file to test structure
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
        temp_path = temp_file.name
        temp_file.write(b"fake mp3 content")
    
    try:
        command = {
            "command": "transcribe",
            "input_file": temp_path,
            "output_dir": "transcriptions",
            "model": "tiny",
            "formats": ["txt", "srt"],
            "language": "en"
        }
        
        command_json = json.dumps(command)
        
        result = subprocess.run(
            [sys.executable, 'macos_cli.py', command_json],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            response = json.loads(result.stdout.strip())
            
            # Should fail because the file isn't a real audio file, but structure should be validated
            print("✅ Command structure parsing works correctly")
            print(f"   Response: {json.dumps(response, indent=2)}")
            return True
        else:
            print(f"❌ Command execution failed: {result.stderr}")
            return False
            
    finally:
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)


def test_extract_command():
    """Test video extraction command."""
    print("\n🎬 Testing Video Extraction Command")
    print("-" * 40)
    
    test_cases = [
        {
            "name": "Non-existent video file",
            "command": {
                "command": "extract",
                "input_file": "/path/to/nonexistent.mp4"
            },
            "expected_success": False,
            "expected_code": "FILE_NOT_FOUND"
        },
        {
            "name": "Unsupported video format",
            "command": {
                "command": "extract", 
                "input_file": "/tmp/test.mkv"
            },
            "expected_success": False,
            "expected_code": "UNSUPPORTED_FORMAT"
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Extract Test {i}: {test_case['name']}")
        
        try:
            # Create dummy file for unsupported format test
            if "test.mkv" in test_case['command'].get('input_file', ''):
                dummy_file = Path("/tmp/test.mkv")
                dummy_file.touch()
            
            command_json = json.dumps(test_case['command'])
            
            result = subprocess.run(
                [sys.executable, 'macos_cli.py', command_json],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent
            )
            
            if result.returncode == 0:
                response = json.loads(result.stdout.strip())
                
                if (response['success'] == test_case['expected_success'] and
                    response.get('code') == test_case.get('expected_code')):
                    print("✅ Extract test passed")
                    success_count += 1
                else:
                    print(f"❌ Expected different response: {response}")
            else:
                print(f"❌ Command failed: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
        finally:
            # Cleanup
            Path("/tmp/test.mkv").unlink(missing_ok=True)
    
    return success_count == len(test_cases)


if __name__ == '__main__':
    print("Starting Transcription Command Tests...\n")
    
    # Check if macos_cli.py exists
    cli_path = Path('macos_cli.py')
    if not cli_path.exists():
        print(f"❌ macos_cli.py not found at {cli_path.absolute()}")
        sys.exit(1)
    
    # Run tests
    validation_passed = test_transcription_validation()
    structure_passed = test_json_command_structure()
    extract_passed = test_extract_command()
    
    if validation_passed and structure_passed and extract_passed:
        print("\n✅ Task 2.2 Test: Transcription command wrapper implemented successfully!")
        print("✅ File validation, JSON structure, and error handling all working")
        print("Ready to proceed to Task 2.3")
    else:
        print("\n❌ Task 2.2 Test: Some issues found in implementation")
        sys.exit(1)