#!/usr/bin/env python3
"""
Test script for model management functionality in macOS CLI Wrapper

Tests the model management commands including:
- list_models command
- download_model command (without actual download)
- Model validation and verification
- Error handling for model operations
"""

import json
import subprocess
import sys
import tempfile
import os
import shutil
from pathlib import Path


def test_list_models():
    """Test the list_models command."""
    
    print("🧪 Testing Model Listing Command")
    print("=" * 50)
    
    # Test basic list models command
    command = {
        "command": "list_models"
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
        
        # Validate response structure
        required_fields = ['success', 'data', 'timestamp']
        missing_fields = [field for field in required_fields if field not in response]
        
        if missing_fields:
            print(f"❌ Response missing fields: {missing_fields}")
            return False
        
        if not response['success']:
            print(f"❌ Command failed: {response.get('error', 'Unknown error')}")
            return False
        
        data = response['data']
        required_data_fields = ['models', 'models_directory', 'total_count', 'downloaded_count']
        missing_data_fields = [field for field in required_data_fields if field not in data]
        
        if missing_data_fields:
            print(f"❌ Data missing fields: {missing_data_fields}")
            return False
        
        models = data['models']
        if not isinstance(models, list):
            print("❌ Models should be a list")
            return False
        
        print(f"✅ Found {data['total_count']} supported models")
        print(f"✅ Downloaded models: {data['downloaded_count']}")
        print(f"✅ Models directory: {data['models_directory']}")
        
        # Check that we have expected models
        model_names = [model['name'] for model in models]
        expected_models = ['tiny', 'tiny.en', 'base', 'base.en', 'small', 'medium', 'large-v3-turbo']
        
        for expected in expected_models:
            if expected not in model_names:
                print(f"❌ Expected model {expected} not found")
                return False
        
        print(f"✅ All expected models found: {', '.join(expected_models)}")
        
        # Verify model structure
        sample_model = models[0]
        required_model_fields = ['name', 'size_mb', 'description', 'performance', 'is_downloaded']
        missing_model_fields = [field for field in required_model_fields if field not in sample_model]
        
        if missing_model_fields:
            print(f"❌ Sample model missing fields: {missing_model_fields}")
            return False
        
        print("✅ Model structure validation passed")
        return True
        
    else:
        print(f"❌ Command execution failed: {result.stderr}")
        return False


def test_download_model_validation():
    """Test download_model command validation."""
    
    print("\n🎯 Testing Model Download Validation")
    print("=" * 50)
    
    test_cases = [
        {
            "name": "Missing model_name",
            "command": {
                "command": "download_model"
            },
            "expected_success": False,
            "expected_code": "MISSING_FIELDS"
        },
        {
            "name": "Unsupported model",
            "command": {
                "command": "download_model",
                "model_name": "nonexistent_model"
            },
            "expected_success": False,
            "expected_code": "UNSUPPORTED_MODEL"
        },
        {
            "name": "Valid model (should detect existing or download)",
            "command": {
                "command": "download_model",
                "model_name": "tiny"
            },
            "expected_success": True,
            "check_status": True  # Special case - check for already_downloaded or downloaded status
        }
    ]
    
    success_count = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}/{total_tests}: {test_case['name']}")
        
        try:
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
            
            # Check expected results
            actual_success = response['success']
            expected_success = test_case['expected_success']
            
            if actual_success != expected_success:
                print(f"❌ Expected success={expected_success}, got {actual_success}")
                continue
            
            if not expected_success and 'expected_code' in test_case:
                expected_code = test_case['expected_code']
                actual_code = response.get('code', 'MISSING')
                
                if actual_code != expected_code:
                    print(f"❌ Expected code={expected_code}, got {actual_code}")
                    continue
            
            # Special handling for download test
            if test_case.get('check_status') and actual_success:
                data = response.get('data', {})
                status = data.get('status', 'unknown')
                
                if status in ['already_downloaded', 'downloaded']:
                    print(f"✅ Model status: {status}")
                else:
                    print(f"❌ Unexpected status: {status}")
                    continue
            
            print("✅ Test passed")
            print(f"   Error: {response.get('error', 'N/A')}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print(f"\n📊 Download Validation Results: {success_count}/{total_tests} tests passed")
    return success_count == total_tests


def test_model_info_structure():
    """Test that model information has correct structure."""
    
    print("\n📋 Testing Model Information Structure")
    print("=" * 40)
    
    command = {
        "command": "list_models"
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
        models = response['data']['models']
        
        # Test specific model details
        tiny_model = next((m for m in models if m['name'] == 'tiny'), None)
        if not tiny_model:
            print("❌ Tiny model not found")
            return False
        
        # Validate performance metrics
        performance = tiny_model.get('performance', {})
        required_perf_fields = ['speed_multiplier', 'accuracy', 'memory_usage', 'languages']
        
        for field in required_perf_fields:
            if field not in performance:
                print(f"❌ Performance missing field: {field}")
                return False
        
        # Validate reasonable values
        if tiny_model['size_mb'] <= 0:
            print(f"❌ Invalid size_mb: {tiny_model['size_mb']}")
            return False
        
        if performance['speed_multiplier'] <= 0:
            print(f"❌ Invalid speed_multiplier: {performance['speed_multiplier']}")
            return False
        
        print("✅ Model information structure is correct")
        print(f"   Tiny model: {tiny_model['size_mb']}MB, {performance['speed_multiplier']}x speed")
        print(f"   Description: {tiny_model['description']}")
        
        return True
        
    else:
        print(f"❌ Failed to get model list: {result.stderr}")
        return False


def test_models_directory_creation():
    """Test that models directory is created correctly."""
    
    print("\n📁 Testing Models Directory Creation")  
    print("=" * 40)
    
    # Use a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_models_dir = Path(temp_dir) / "test_models"
        
        command = {
            "command": "list_models",
            "models_dir": str(temp_models_dir)
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
            
            if response['success']:
                # Check if directory was created
                if temp_models_dir.exists():
                    print("✅ Models directory created successfully")
                    print(f"   Directory: {temp_models_dir}")
                    return True
                else:
                    print("❌ Models directory was not created")
                    return False
            else:
                print(f"❌ Command failed: {response.get('error')}")
                return False
        else:
            print(f"❌ Command execution failed: {result.stderr}")
            return False


if __name__ == '__main__':
    print("Starting Model Management Tests...\n")
    
    # Check if macos_cli.py exists
    cli_path = Path('macos_cli.py')
    if not cli_path.exists():
        print(f"❌ macos_cli.py not found at {cli_path.absolute()}")
        sys.exit(1)
    
    # Run tests
    list_test_passed = test_list_models()
    download_test_passed = test_download_model_validation()
    structure_test_passed = test_model_info_structure()
    directory_test_passed = test_models_directory_creation()
    
    if all([list_test_passed, download_test_passed, structure_test_passed, directory_test_passed]):
        print("\n✅ Task 2.3 Test: Model management implemented successfully!")
        print("✅ Model listing, download validation, and directory management all working")
        print("Ready to proceed to Task 2.4")
    else:
        print("\n❌ Task 2.3 Test: Some issues found in model management implementation")
        sys.exit(1)