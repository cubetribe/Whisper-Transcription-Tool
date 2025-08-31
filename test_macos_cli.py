#!/usr/bin/env python3
"""
Test script for macOS CLI Wrapper

Tests the JSON input/output functionality of the macos_cli.py wrapper.
This ensures the communication layer works correctly before implementing
the actual transcription functionality.
"""

import json
import subprocess
import sys
from pathlib import Path


def test_cli_wrapper():
    """Test the CLI wrapper with various JSON commands."""
    
    print("🧪 Testing macOS CLI Wrapper JSON Communication")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        {
            "name": "Valid command (not implemented)",
            "command": {
                "command": "transcribe",
                "input_file": "/path/to/test.mp3",
                "model": "tiny"
            },
            "expected_success": False,
            "expected_code": "NOT_IMPLEMENTED"
        },
        {
            "name": "Unknown command",
            "command": {
                "command": "unknown_command"
            },
            "expected_success": False,
            "expected_code": "UNKNOWN_COMMAND"
        },
        {
            "name": "List models (not implemented)",
            "command": {
                "command": "list_models"
            },
            "expected_success": False,
            "expected_code": "NOT_IMPLEMENTED"
        },
        {
            "name": "Invalid JSON",
            "command": "{ invalid json",
            "expected_success": False,
            "expected_code": "JSON_DECODE_ERROR",
            "raw_json": True
        }
    ]
    
    success_count = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}/{total_tests}: {test_case['name']}")
        
        try:
            # Prepare command
            if test_case.get('raw_json'):
                command_json = test_case['command']
            else:
                command_json = json.dumps(test_case['command'])
            
            # Run CLI wrapper
            result = subprocess.run(
                [sys.executable, 'macos_cli.py', command_json],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent
            )
            
            if result.returncode != 0:
                print(f"❌ CLI returned non-zero exit code: {result.returncode}")
                if result.stderr:
                    print(f"   stderr: {result.stderr}")
                continue
            
            # Parse response
            try:
                response = json.loads(result.stdout.strip())
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON response: {e}")
                print(f"   stdout: {result.stdout}")
                continue
            
            # Validate response structure
            if not isinstance(response, dict):
                print("❌ Response is not a dictionary")
                continue
            
            if 'success' not in response:
                print("❌ Response missing 'success' field")
                continue
            
            if 'timestamp' not in response:
                print("❌ Response missing 'timestamp' field")
                continue
            
            # Check expected success status
            actual_success = response['success']
            expected_success = test_case['expected_success']
            
            if actual_success != expected_success:
                print(f"❌ Expected success={expected_success}, got {actual_success}")
                continue
            
            # Check error code if expecting failure
            if not expected_success:
                if 'code' not in response:
                    print("❌ Error response missing 'code' field")
                    continue
                
                expected_code = test_case['expected_code']
                actual_code = response['code']
                
                if actual_code != expected_code:
                    print(f"❌ Expected code={expected_code}, got {actual_code}")
                    continue
            
            print("✅ Test passed")
            print(f"   Response: {json.dumps(response, indent=2)}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print(f"\n📊 Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All tests passed! JSON communication is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Check the implementation.")
        return False


def test_json_formats():
    """Test specific JSON format requirements."""
    print("\n🔍 Testing JSON Format Requirements")
    print("-" * 40)
    
    # Test error response format
    command_json = json.dumps({"command": "unknown"})
    result = subprocess.run(
        [sys.executable, 'macos_cli.py', command_json],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent
    )
    
    if result.returncode == 0:
        response = json.loads(result.stdout.strip())
        
        # Check error response format
        required_error_fields = ['success', 'error', 'code', 'timestamp']
        missing_fields = [field for field in required_error_fields if field not in response]
        
        if missing_fields:
            print(f"❌ Error response missing fields: {missing_fields}")
        else:
            print("✅ Error response format is correct")
            print(f"   Fields: {list(response.keys())}")


if __name__ == '__main__':
    print("Starting macOS CLI Wrapper Tests...\n")
    
    # Check if macos_cli.py exists
    cli_path = Path('macos_cli.py')
    if not cli_path.exists():
        print(f"❌ macos_cli.py not found at {cli_path.absolute()}")
        sys.exit(1)
    
    # Make CLI executable
    import os
    os.chmod('macos_cli.py', 0o755)
    
    # Run tests
    basic_tests_passed = test_cli_wrapper()
    test_json_formats()
    
    if basic_tests_passed:
        print("\n✅ Task 2.1 Test: JSON communication verified successfully!")
        print("Ready to proceed to Task 2.2")
    else:
        print("\n❌ Task 2.1 Test: Some issues found, please review implementation")
        sys.exit(1)