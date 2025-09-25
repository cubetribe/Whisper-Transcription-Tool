#!/usr/bin/env python3
"""
Test script to validate module5_text_correction imports and basic functionality.
"""

import sys
import traceback
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test all module imports."""
    print("Testing module5_text_correction imports...")

    try:
        # Test core models
        from src.whisper_transcription_tool.module5_text_correction.models import (
            CorrectionLevel, CorrectionResult, CorrectionJob,
            ModelStatus, SystemResources, TextChunk, CorrectionConfig
        )
        print("✓ Models import successful")

        # Test correction prompts
        from src.whisper_transcription_tool.module5_text_correction.correction_prompts import (
            CorrectionPrompts, PromptTemplates, get_correction_prompt, get_available_levels
        )
        print("✓ Correction prompts import successful")

        # Test batch processor (might have missing dependencies)
        try:
            from src.whisper_transcription_tool.module5_text_correction.batch_processor import (
                BatchProcessor, TextChunk as BP_TextChunk, TokenizerStrategy
            )
            print("✓ Batch processor import successful")
        except ImportError as e:
            print(f"⚠ Batch processor import warning: {e}")

        # Test resource manager (might have missing psutil)
        try:
            from src.whisper_transcription_tool.module5_text_correction.resource_manager import (
                ResourceManager, ModelType
            )
            print("✓ Resource manager import successful")
        except ImportError as e:
            print(f"⚠ Resource manager import warning: {e}")

        # Test LLM corrector (might have missing llama-cpp-python)
        try:
            from src.whisper_transcription_tool.module5_text_correction.llm_corrector import (
                LLMCorrector, correct_text_quick
            )
            print("✓ LLM corrector import successful")
        except ImportError as e:
            print(f"⚠ LLM corrector import warning: {e}")

        return True

    except Exception as e:
        print(f"✗ Import test failed: {e}")
        traceback.print_exc()
        return False

def test_basic_functionality():
    """Test basic functionality without external dependencies."""
    print("\nTesting basic functionality...")

    try:
        # Test correction prompts
        from src.whisper_transcription_tool.module5_text_correction.correction_prompts import CorrectionPrompts
        from src.whisper_transcription_tool.module5_text_correction.models import CorrectionLevel

        prompts = CorrectionPrompts()
        levels = prompts.get_available_levels()
        print(f"✓ Available correction levels: {[level.value for level in levels]}")

        # Test prompt generation
        prompt = prompts.get_prompt(CorrectionLevel.STANDARD, "Das ist ein Test Text mit Felern.")
        print("✓ Prompt generation successful")
        print(f"  System prompt length: {len(prompt['system'])} chars")
        print(f"  User prompt length: {len(prompt['user'])} chars")

        # Test data models
        from src.whisper_transcription_tool.module5_text_correction.models import (
            CorrectionResult, TextChunk, CorrectionConfig
        )

        result = CorrectionResult(
            original_text="Test text",
            corrected_text="Test text corrected",
            success=True,
            correction_level="standard",
            processing_time_seconds=1.5,
            chunks_processed=1,
            model_used="test-model"
        )
        print(f"✓ CorrectionResult created: {result.success}")

        chunk = TextChunk(
            text="Test chunk",
            index=0,
            start_pos=0,
            end_pos=10
        )
        print(f"✓ TextChunk created: length={len(chunk)}")

        config = CorrectionConfig()
        print(f"✓ CorrectionConfig created: enabled={config.enabled}")

        return True

    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        traceback.print_exc()
        return False

def test_optional_dependencies():
    """Test which optional dependencies are available."""
    print("\nTesting optional dependencies...")

    dependencies = {
        'psutil': 'System resource monitoring',
        'llama_cpp': 'Local LLM inference',
        'sentencepiece': 'Advanced tokenization',
        'nltk': 'Natural language processing',
        'transformers': 'Hugging Face tokenizers'
    }

    available = {}

    for dep, description in dependencies.items():
        try:
            __import__(dep)
            available[dep] = True
            print(f"✓ {dep}: {description}")
        except ImportError:
            available[dep] = False
            print(f"✗ {dep}: {description} (not installed)")

    print(f"\nDependency summary: {sum(available.values())}/{len(available)} available")
    return available

def main():
    """Run all tests."""
    print("=" * 60)
    print("MODULE5_TEXT_CORRECTION INTEGRATION TEST")
    print("=" * 60)

    # Test imports
    imports_ok = test_imports()

    # Test basic functionality
    basic_ok = test_basic_functionality()

    # Test optional dependencies
    deps = test_optional_dependencies()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Imports: {'✓ PASS' if imports_ok else '✗ FAIL'}")
    print(f"Basic functionality: {'✓ PASS' if basic_ok else '✗ FAIL'}")
    print(f"Optional dependencies: {sum(deps.values())}/{len(deps)} available")

    if imports_ok and basic_ok:
        print("\n🎉 Module5 integration test PASSED!")
        print("The core architecture is ready and functional.")
        if sum(deps.values()) < len(deps):
            print("\n⚠ Note: Some optional features may not work due to missing dependencies.")
            print("Run 'pip install -r requirements.txt' to install all dependencies.")
    else:
        print("\n❌ Module5 integration test FAILED!")
        print("Check the errors above and fix any issues.")

    return imports_ok and basic_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)