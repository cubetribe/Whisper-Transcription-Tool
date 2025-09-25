#!/usr/bin/env python3
"""
Basic test script to validate module5_text_correction core components.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_models():
    """Test core data models without external dependencies."""
    print("Testing data models...")

    try:
        from src.whisper_transcription_tool.module5_text_correction.models import (
            CorrectionLevel, CorrectionResult, CorrectionJob,
            ModelStatus, SystemResources, TextChunk, CorrectionConfig
        )
        print("✓ Models import successful")

        # Test CorrectionLevel enum
        levels = [CorrectionLevel.LIGHT, CorrectionLevel.STANDARD, CorrectionLevel.STRICT]
        print(f"✓ Correction levels: {[level.value for level in levels]}")

        # Test CorrectionResult
        result = CorrectionResult(
            original_text="Test text",
            corrected_text="Test text corrected",
            success=True,
            correction_level="standard",
            processing_time_seconds=1.5,
            chunks_processed=1,
            model_used="test-model"
        )
        result_dict = result.to_dict()
        print("✓ CorrectionResult created and serialized")

        # Test TextChunk
        chunk = TextChunk(
            text="Test chunk",
            index=0,
            start_pos=0,
            end_pos=10
        )
        chunk_dict = chunk.to_dict()
        print("✓ TextChunk created and serialized")

        # Test CorrectionConfig
        config = CorrectionConfig()
        config_dict = config.to_dict()
        print("✓ CorrectionConfig created and serialized")

        return True

    except Exception as e:
        print(f"✗ Models test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_prompts():
    """Test correction prompts."""
    print("\nTesting correction prompts...")

    try:
        from src.whisper_transcription_tool.module5_text_correction.correction_prompts import (
            CorrectionPrompts, PromptTemplates, get_correction_prompt, get_available_levels
        )
        from src.whisper_transcription_tool.module5_text_correction.models import CorrectionLevel

        print("✓ Correction prompts import successful")

        # Test available levels
        levels = get_available_levels()
        print(f"✓ Available levels: {levels}")

        # Test prompt generation
        prompt = get_correction_prompt("standard", "Das ist ein Test Text mit Felern.")
        print("✓ Basic prompt generation successful")
        print(f"  System prompt length: {len(prompt['system'])} chars")
        print(f"  User prompt length: {len(prompt['user'])} chars")

        # Test CorrectionPrompts class
        prompts = CorrectionPrompts()
        enum_levels = prompts.get_available_levels()
        print(f"✓ CorrectionPrompts class levels: {[level.value for level in enum_levels]}")

        # Test prompt with enum
        prompt_with_enum = prompts.get_prompt(CorrectionLevel.STANDARD, "Test text")
        print("✓ Prompt generation with enum successful")

        # Test dialect mode
        dialect_prompt = prompts.get_prompt(
            CorrectionLevel.STANDARD,
            "I mog des ned",
            dialect_mode=True
        )
        print("✓ Dialect mode prompt generation successful")

        # Test token estimation
        tokens = prompts.estimate_tokens("Das ist ein Test", CorrectionLevel.STANDARD)
        print(f"✓ Token estimation: {tokens} tokens")

        return True

    except Exception as e:
        print(f"✗ Prompts test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_optional_components():
    """Test which optional components are available."""
    print("\nTesting optional components...")

    components = {
        'batch_processor': 'BatchProcessor for text chunking',
        'llm_corrector': 'LLMCorrector for LLM-based correction',
        'resource_manager': 'ResourceManager for system resource management'
    }

    available = {}

    for component, description in components.items():
        try:
            module_path = f"src.whisper_transcription_tool.module5_text_correction.{component}"
            __import__(module_path)
            available[component] = True
            print(f"✓ {component}: {description}")
        except ImportError as e:
            available[component] = False
            print(f"✗ {component}: {description} (dependency missing: {e})")

    return available

def main():
    """Run all tests."""
    print("=" * 60)
    print("MODULE5_TEXT_CORRECTION BASIC COMPONENT TEST")
    print("=" * 60)

    # Test core models
    models_ok = test_models()

    # Test prompts
    prompts_ok = test_prompts()

    # Test optional components
    optional = test_optional_components()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Data models: {'✓ PASS' if models_ok else '✗ FAIL'}")
    print(f"Correction prompts: {'✓ PASS' if prompts_ok else '✗ FAIL'}")
    print(f"Optional components: {sum(optional.values())}/{len(optional)} available")

    basic_ok = models_ok and prompts_ok

    if basic_ok:
        print("\n🎉 Basic component test PASSED!")
        print("The core module5_text_correction architecture is functional.")

        if sum(optional.values()) < len(optional):
            print("\n⚠ Note: Some advanced features require additional dependencies.")
            print("To install all dependencies: pip install -r requirements.txt")

        if sum(optional.values()) == len(optional):
            print("\n✨ All components available! Full functionality enabled.")
    else:
        print("\n❌ Basic component test FAILED!")
        print("Check the errors above and fix any issues.")

    return basic_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)