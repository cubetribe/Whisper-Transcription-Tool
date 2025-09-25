"""
Comprehensive Unit Tests for Correction Prompts and Templates

Tests cover:
- All correction levels (light, standard, strict)
- Prompt template generation and validation
- Context-aware prompt generation
- Dialect normalization functionality
- Input validation and error handling
- Token estimation
- Examples and template consistency

Author: QualityMarshal Agent
Version: 1.0.0
"""

import pytest
import unittest
from unittest.mock import Mock, patch
from pathlib import Path

# Import the classes to test
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.whisper_transcription_tool.module5_text_correction.correction_prompts import (
    PromptTemplates,
    get_correction_prompt,
    get_available_levels,
    get_correction_examples,
    get_dialect_examples,
    validate_prompt_inputs,
    CorrectionPrompts
)

from src.whisper_transcription_tool.module5_text_correction.models import CorrectionLevel


class TestPromptTemplates:
    """Test suite for PromptTemplates class"""

    def test_system_prompts_exist(self):
        """Test that all required system prompts are defined"""
        expected_levels = ["light", "standard", "strict"]

        for level in expected_levels:
            assert level in PromptTemplates.SYSTEM_PROMPTS
            prompt = PromptTemplates.SYSTEM_PROMPTS[level]
            assert isinstance(prompt, str)
            assert len(prompt) > 0
            assert "Du bist" in prompt  # Should start with role definition
            assert "Antworte nur mit dem korrigierten Text" in prompt

    def test_user_prompts_exist(self):
        """Test that all required user prompts are defined"""
        expected_prompts = ["correction", "dialect_normalization", "with_context"]

        for prompt_type in expected_prompts:
            assert prompt_type in PromptTemplates.USER_PROMPTS
            prompt = PromptTemplates.USER_PROMPTS[prompt_type]
            assert isinstance(prompt, str)
            assert len(prompt) > 0
            assert "{text}" in prompt

    def test_system_prompts_hierarchy(self):
        """Test that system prompts have appropriate complexity hierarchy"""
        light_prompt = PromptTemplates.SYSTEM_PROMPTS["light"]
        standard_prompt = PromptTemplates.SYSTEM_PROMPTS["standard"]
        strict_prompt = PromptTemplates.SYSTEM_PROMPTS["strict"]

        # Light should be simplest, strict should be most comprehensive
        assert len(light_prompt) < len(standard_prompt) < len(strict_prompt)

        # Light should focus on spelling
        assert "Rechtschreibfehler" in light_prompt
        assert "Rechtschreibkorrektur" in light_prompt

        # Standard should include grammar
        assert "Grammatik" in standard_prompt
        assert "Artikel" in standard_prompt

        # Strict should be comprehensive
        assert "umfassende" in strict_prompt or "vollständig" in strict_prompt
        assert "Wortwahl" in strict_prompt

    def test_correction_examples_exist(self):
        """Test that correction examples exist for all levels"""
        expected_levels = ["light", "standard", "strict"]

        for level in expected_levels:
            assert level in PromptTemplates.CORRECTION_EXAMPLES
            example = PromptTemplates.CORRECTION_EXAMPLES[level]
            assert "input" in example
            assert "output" in example
            assert isinstance(example["input"], str)
            assert isinstance(example["output"], str)
            assert len(example["input"]) > 0
            assert len(example["output"]) > 0

    def test_correction_examples_quality(self):
        """Test that correction examples demonstrate appropriate corrections"""
        light_example = PromptTemplates.CORRECTION_EXAMPLES["light"]
        standard_example = PromptTemplates.CORRECTION_EXAMPLES["standard"]
        strict_example = PromptTemplates.CORRECTION_EXAMPLES["strict"]

        # Light: Should correct spelling only
        assert "Beisspiel" in light_example["input"] and "Beispiel" in light_example["output"]
        assert "Felern" in light_example["input"] and "Fehlern" in light_example["output"]

        # Standard: Should correct grammar
        assert "kauft" in standard_example["input"] and "gekauft" in standard_example["output"]
        assert "ein neue" in standard_example["input"] and "eine neue" in standard_example["output"]

        # Strict: Should normalize style
        assert "voll krass" in strict_example["input"]
        assert "beeindruckend" in strict_example["output"]
        assert "rumgemacht" in strict_example["input"]
        assert "verhalten" in strict_example["output"]

    def test_dialect_examples_exist(self):
        """Test that dialect examples exist for major German dialects"""
        expected_dialects = ["bavarian", "swabian", "north_german"]

        for dialect in expected_dialects:
            assert dialect in PromptTemplates.DIALECT_EXAMPLES
            example = PromptTemplates.DIALECT_EXAMPLES[dialect]
            assert "input" in example
            assert "output" in example
            assert isinstance(example["input"], str)
            assert isinstance(example["output"], str)

    def test_dialect_examples_normalization(self):
        """Test that dialect examples show proper normalization"""
        bavarian = PromptTemplates.DIALECT_EXAMPLES["bavarian"]
        swabian = PromptTemplates.DIALECT_EXAMPLES["swabian"]
        north_german = PromptTemplates.DIALECT_EXAMPLES["north_german"]

        # Bavarian normalization
        assert "I mog" in bavarian["input"] and "Ich mag" in bavarian["output"]
        assert "z'vui" in bavarian["input"] and "zu viel" in bavarian["output"]

        # Swabian normalization
        assert "isch" in swabian["input"] and "ist" in swabian["output"]
        assert "gell" in swabian["input"] and "nicht wahr" in swabian["output"]

        # North German normalization
        assert "Dat" in north_german["input"] and "Das" in north_german["output"]
        assert "mook wi" in north_german["input"] and "machen wir" in north_german["output"]

    def test_user_prompt_templates_formatting(self):
        """Test that user prompt templates have correct placeholders"""
        correction_prompt = PromptTemplates.USER_PROMPTS["correction"]
        dialect_prompt = PromptTemplates.USER_PROMPTS["dialect_normalization"]
        context_prompt = PromptTemplates.USER_PROMPTS["with_context"]

        # Basic correction should have text placeholder
        assert "{text}" in correction_prompt

        # Dialect normalization should explain the task
        assert "{text}" in dialect_prompt
        assert "dialektalen" in dialect_prompt or "umgangssprachlich" in dialect_prompt

        # Context-aware should have all context placeholders
        assert "{prev_context}" in context_prompt
        assert "{text}" in context_prompt
        assert "{next_context}" in context_prompt


class TestGetCorrectionPrompt:
    """Test suite for get_correction_prompt function"""

    def test_basic_correction_prompt(self):
        """Test basic correction prompt generation"""
        text = "Das ist ein Test text."

        for level in ["light", "standard", "strict"]:
            result = get_correction_prompt(level, text)

            assert isinstance(result, dict)
            assert "system" in result
            assert "user" in result
            assert isinstance(result["system"], str)
            assert isinstance(result["user"], str)
            assert text in result["user"]

    def test_dialect_mode_prompt(self):
        """Test dialect normalization prompt generation"""
        text = "I mog des ned."

        result = get_correction_prompt("standard", text, dialect_mode=True)

        assert "dialektalen" in result["user"] or "umgangssprachlichen" in result["user"]
        assert text in result["user"]

    def test_context_aware_prompt(self):
        """Test context-aware prompt generation"""
        text = "Das ist der mittlere Text."
        prev_context = "Das ist der vorherige Kontext."
        next_context = "Das ist der nachfolgende Kontext."

        result = get_correction_prompt(
            "standard",
            text,
            prev_context=prev_context,
            next_context=next_context
        )

        assert prev_context in result["user"]
        assert text in result["user"]
        assert next_context in result["user"]
        assert "Vorheriger Kontext" in result["user"]
        assert "Nachfolgender Kontext" in result["user"]

    def test_context_aware_prompt_partial(self):
        """Test context-aware prompt with only one context"""
        text = "Das ist der mittlere Text."
        prev_context = "Das ist der vorherige Kontext."

        result = get_correction_prompt(
            "standard",
            text,
            prev_context=prev_context
        )

        assert prev_context in result["user"]
        assert text in result["user"]
        assert "[Kein nachfolgender Kontext]" in result["user"]

    def test_invalid_correction_level(self):
        """Test error handling for invalid correction level"""
        with pytest.raises(ValueError, match="Invalid correction level"):
            get_correction_prompt("invalid_level", "Test text")

    def test_all_system_prompts_used(self):
        """Test that all system prompts are properly used"""
        text = "Test text"

        for level in ["light", "standard", "strict"]:
            result = get_correction_prompt(level, text)
            expected_system = PromptTemplates.SYSTEM_PROMPTS[level]
            assert result["system"] == expected_system


class TestGetAvailableLevels:
    """Test suite for get_available_levels function"""

    def test_available_levels(self):
        """Test that available levels are returned correctly"""
        levels = get_available_levels()

        assert isinstance(levels, list)
        assert len(levels) > 0
        assert "light" in levels
        assert "standard" in levels
        assert "strict" in levels

    def test_levels_match_system_prompts(self):
        """Test that available levels match system prompts keys"""
        levels = get_available_levels()
        system_prompt_keys = list(PromptTemplates.SYSTEM_PROMPTS.keys())

        assert set(levels) == set(system_prompt_keys)


class TestGetCorrectionExamples:
    """Test suite for get_correction_examples function"""

    def test_get_examples_for_all_levels(self):
        """Test getting examples for all correction levels"""
        for level in ["light", "standard", "strict"]:
            example = get_correction_examples(level)

            assert isinstance(example, dict)
            assert "input" in example
            assert "output" in example
            assert isinstance(example["input"], str)
            assert isinstance(example["output"], str)

    def test_get_examples_invalid_level(self):
        """Test error handling for invalid level"""
        with pytest.raises(ValueError, match="Invalid correction level"):
            get_correction_examples("invalid_level")

    def test_examples_are_copies(self):
        """Test that returned examples are independent copies"""
        example1 = get_correction_examples("light")
        example2 = get_correction_examples("light")

        # Modify one example
        example1["input"] = "modified"

        # Other example should be unchanged
        assert example2["input"] != "modified"


class TestGetDialectExamples:
    """Test suite for get_dialect_examples function"""

    def test_get_dialect_examples(self):
        """Test getting dialect examples"""
        examples = get_dialect_examples()

        assert isinstance(examples, dict)
        assert len(examples) > 0

        for dialect, example in examples.items():
            assert isinstance(example, dict)
            assert "input" in example
            assert "output" in example
            assert isinstance(example["input"], str)
            assert isinstance(example["output"], str)

    def test_dialect_examples_are_copies(self):
        """Test that returned examples are independent copies"""
        examples1 = get_dialect_examples()
        examples2 = get_dialect_examples()

        # Modify one example
        if "bavarian" in examples1:
            examples1["bavarian"]["input"] = "modified"

            # Other example should be unchanged
            assert examples2["bavarian"]["input"] != "modified"


class TestValidatePromptInputs:
    """Test suite for validate_prompt_inputs function"""

    def test_valid_inputs(self):
        """Test validation with valid inputs"""
        # Should not raise any exceptions
        validate_prompt_inputs("light", "Das ist ein Test.")
        validate_prompt_inputs("standard", "Ein anderer Test.")
        validate_prompt_inputs("strict", "Noch ein Test.")

    def test_invalid_level_type(self):
        """Test validation with invalid level type"""
        with pytest.raises(ValueError, match="Level must be a string"):
            validate_prompt_inputs(123, "Test text")

    def test_invalid_level_value(self):
        """Test validation with invalid level value"""
        with pytest.raises(ValueError, match="Invalid correction level"):
            validate_prompt_inputs("invalid_level", "Test text")

    def test_invalid_text_type(self):
        """Test validation with invalid text type"""
        with pytest.raises(ValueError, match="Text must be a string"):
            validate_prompt_inputs("light", 123)

    def test_empty_text(self):
        """Test validation with empty text"""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            validate_prompt_inputs("light", "")

    def test_whitespace_only_text(self):
        """Test validation with whitespace-only text"""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            validate_prompt_inputs("light", "   \n\t   ")

    def test_text_too_long(self):
        """Test validation with text that's too long"""
        long_text = "A" * 10001  # Over 10,000 characters

        with pytest.raises(ValueError, match="Text too long"):
            validate_prompt_inputs("light", long_text)

    def test_text_max_length_boundary(self):
        """Test validation at maximum length boundary"""
        max_length_text = "A" * 10000  # Exactly 10,000 characters

        # Should not raise exception
        validate_prompt_inputs("light", max_length_text)


class TestCorrectionPrompts:
    """Test suite for CorrectionPrompts class"""

    def setUp(self):
        """Set up test fixtures"""
        self.correction_prompts = CorrectionPrompts()

    def test_initialization(self):
        """Test CorrectionPrompts initialization"""
        cp = CorrectionPrompts()
        assert cp.templates is not None
        assert isinstance(cp.templates, PromptTemplates)

    def test_get_prompt_with_enum(self):
        """Test getting prompt with CorrectionLevel enum"""
        cp = CorrectionPrompts()
        text = "Das ist ein Test."

        for level_enum in [CorrectionLevel.LIGHT, CorrectionLevel.STANDARD, CorrectionLevel.STRICT]:
            result = cp.get_prompt(level_enum, text)

            assert isinstance(result, dict)
            assert "system" in result
            assert "user" in result
            assert text in result["user"]

    def test_get_prompt_with_string(self):
        """Test getting prompt with string level"""
        cp = CorrectionPrompts()
        text = "Das ist ein Test."

        result = cp.get_prompt("standard", text)

        assert isinstance(result, dict)
        assert "system" in result
        assert "user" in result
        assert text in result["user"]

    def test_get_prompt_with_dialect_mode(self):
        """Test getting prompt with dialect mode enabled"""
        cp = CorrectionPrompts()
        text = "I mog des ned."

        result = cp.get_prompt(
            CorrectionLevel.STANDARD,
            text,
            dialect_mode=True
        )

        assert "dialektalen" in result["user"] or "umgangssprachlichen" in result["user"]

    def test_get_prompt_with_context(self):
        """Test getting prompt with context"""
        cp = CorrectionPrompts()
        text = "Das ist der mittlere Text."
        prev_context = "Vorheriger Kontext."
        next_context = "Nachfolgender Kontext."

        result = cp.get_prompt(
            CorrectionLevel.STANDARD,
            text,
            prev_context=prev_context,
            next_context=next_context
        )

        assert prev_context in result["user"]
        assert next_context in result["user"]

    def test_get_prompt_validation(self):
        """Test that get_prompt validates inputs"""
        cp = CorrectionPrompts()

        with pytest.raises(ValueError):
            cp.get_prompt(CorrectionLevel.LIGHT, "")

    def test_get_available_levels_enum(self):
        """Test getting available levels as enums"""
        cp = CorrectionPrompts()
        levels = cp.get_available_levels()

        assert isinstance(levels, list)
        assert len(levels) > 0
        assert all(isinstance(level, CorrectionLevel) for level in levels)
        assert CorrectionLevel.LIGHT in levels
        assert CorrectionLevel.STANDARD in levels
        assert CorrectionLevel.STRICT in levels

    def test_estimate_tokens_basic(self):
        """Test basic token estimation"""
        cp = CorrectionPrompts()
        text = "Das ist ein Test text."

        for level in [CorrectionLevel.LIGHT, CorrectionLevel.STANDARD, CorrectionLevel.STRICT]:
            token_count = cp.estimate_tokens(text, level)

            assert isinstance(token_count, int)
            assert token_count > 0

    def test_estimate_tokens_hierarchy(self):
        """Test that token estimation reflects prompt complexity hierarchy"""
        cp = CorrectionPrompts()
        text = "Das ist ein Test text."

        light_tokens = cp.estimate_tokens(text, CorrectionLevel.LIGHT)
        standard_tokens = cp.estimate_tokens(text, CorrectionLevel.STANDARD)
        strict_tokens = cp.estimate_tokens(text, CorrectionLevel.STRICT)

        # More complex levels should require more tokens
        assert light_tokens <= standard_tokens <= strict_tokens

    def test_estimate_tokens_text_length(self):
        """Test that token estimation scales with text length"""
        cp = CorrectionPrompts()

        short_text = "Kurz."
        long_text = "Das ist ein viel längerer Text mit vielen Wörtern und Sätzen. " * 10

        short_tokens = cp.estimate_tokens(short_text, CorrectionLevel.STANDARD)
        long_tokens = cp.estimate_tokens(long_text, CorrectionLevel.STANDARD)

        assert long_tokens > short_tokens


class TestPromptConsistency:
    """Test suite for prompt consistency and quality checks"""

    def test_system_prompts_language_consistency(self):
        """Test that all system prompts are in German"""
        for level, prompt in PromptTemplates.SYSTEM_PROMPTS.items():
            # Check for German language indicators
            assert "Du bist" in prompt
            assert any(word in prompt for word in ["korrigiere", "Korrektur", "Text"])
            # Should not contain English instructions
            assert "correct" not in prompt.lower()
            assert "fix" not in prompt.lower()

    def test_user_prompts_language_consistency(self):
        """Test that all user prompts are in German"""
        for prompt_type, prompt in PromptTemplates.USER_PROMPTS.items():
            if prompt_type == "correction":
                assert "Korrigiere" in prompt
            elif prompt_type == "dialect_normalization":
                assert "Wandle" in prompt and "Hochdeutsch" in prompt

    def test_prompt_structure_consistency(self):
        """Test that prompts have consistent structure"""
        for level, prompt in PromptTemplates.SYSTEM_PROMPTS.items():
            # Should start with role definition
            assert prompt.startswith("Du bist")

            # Should contain rules section
            assert "Befolge diese Regeln:" in prompt or "Regeln:" in prompt

            # Should end with response instruction
            assert "Antworte nur mit dem korrigierten Text" in prompt

    def test_examples_input_output_consistency(self):
        """Test that examples demonstrate actual corrections"""
        for level, example in PromptTemplates.CORRECTION_EXAMPLES.items():
            input_text = example["input"]
            output_text = example["output"]

            # Output should be different from input (correction applied)
            assert input_text != output_text

            # Output should be longer or equal length (corrections, not deletions)
            # Allow some flexibility for style changes in strict mode
            if level != "strict":
                assert len(output_text) >= len(input_text) - 10

    def test_dialect_examples_normalization_quality(self):
        """Test that dialect examples show proper normalization"""
        for dialect, example in PromptTemplates.DIALECT_EXAMPLES.items():
            input_text = example["input"]
            output_text = example["output"]

            # Should be different
            assert input_text != output_text

            # Output should be in standard German (no dialect markers)
            dialect_markers = ["mog", "isch", "mook", "gell", "älleweil"]
            assert not any(marker in output_text for marker in dialect_markers)


class TestErrorHandling:
    """Test suite for error handling in prompt generation"""

    def test_get_correction_prompt_error_handling(self):
        """Test error handling in get_correction_prompt"""
        # Invalid level
        with pytest.raises(ValueError):
            get_correction_prompt("invalid", "Test")

        # Valid calls should work
        result = get_correction_prompt("light", "Test")
        assert result is not None

    def test_correction_prompts_error_handling(self):
        """Test error handling in CorrectionPrompts class"""
        cp = CorrectionPrompts()

        # Invalid text
        with pytest.raises(ValueError):
            cp.get_prompt(CorrectionLevel.LIGHT, "")

        # Valid call should work
        result = cp.get_prompt(CorrectionLevel.LIGHT, "Test")
        assert result is not None


class TestIntegration:
    """Integration tests for prompt generation workflow"""

    def test_full_correction_workflow(self):
        """Test full correction prompt generation workflow"""
        cp = CorrectionPrompts()

        # Test data
        test_cases = [
            {
                "level": CorrectionLevel.LIGHT,
                "text": "Das ist ein Beisspiel mit Felern.",
                "dialect_mode": False
            },
            {
                "level": CorrectionLevel.STANDARD,
                "text": "Ich bin gestern in die Stadt gegangen.",
                "dialect_mode": False
            },
            {
                "level": CorrectionLevel.STRICT,
                "text": "Ey, das war voll krass.",
                "dialect_mode": True
            }
        ]

        for case in test_cases:
            result = cp.get_prompt(
                case["level"],
                case["text"],
                dialect_mode=case["dialect_mode"]
            )

            # Verify structure
            assert "system" in result
            assert "user" in result
            assert case["text"] in result["user"]

            # Verify token estimation
            token_count = cp.estimate_tokens(case["text"], case["level"])
            assert token_count > 0

    def test_context_aware_correction_workflow(self):
        """Test context-aware correction workflow"""
        cp = CorrectionPrompts()

        # Simulate a multi-chunk correction scenario
        chunks = [
            "Das ist der erste Chunk mit Felern.",
            "Dieser Chunk hat auch einige Probleme.",
            "Der letzte Chunk schließt ab."
        ]

        results = []
        for i, chunk in enumerate(chunks):
            prev_context = chunks[i-1] if i > 0 else None
            next_context = chunks[i+1] if i < len(chunks) - 1 else None

            result = cp.get_prompt(
                CorrectionLevel.STANDARD,
                chunk,
                prev_context=prev_context,
                next_context=next_context
            )

            results.append(result)

            # Verify context is included when available
            if prev_context:
                assert prev_context in result["user"]
            if next_context:
                assert next_context in result["user"]

    def test_performance_with_various_text_lengths(self):
        """Test prompt generation performance with various text lengths"""
        cp = CorrectionPrompts()

        test_texts = [
            "Kurz.",  # Very short
            "Das ist ein mittellanger Text mit mehreren Sätzen und Wörtern.",  # Medium
            "Das ist ein sehr langer Text. " * 100  # Long
        ]

        for text in test_texts:
            import time
            start_time = time.time()

            result = cp.get_prompt(CorrectionLevel.STANDARD, text)
            token_count = cp.estimate_tokens(text, CorrectionLevel.STANDARD)

            processing_time = time.time() - start_time

            # Should be fast
            assert processing_time < 1.0
            assert result is not None
            assert token_count > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])