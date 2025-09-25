"""
Prompt templates for text correction using LLM models.
"""

from typing import Dict, List
from enum import Enum
from .models import CorrectionLevel


class PromptTemplates:
    """Collection of prompt templates for text correction."""

    SYSTEM_PROMPTS = {
        "light": """Du bist ein Assistent für Rechtschreibkorrektur. Deine Aufgabe ist es, offensichtliche Rechtschreibfehler in deutschen Texten zu korrigieren, ohne dabei die ursprüngliche Bedeutung oder den Stil zu verändern.

Befolge diese Regeln:
- Korrigiere nur eindeutige Rechtschreibfehler
- Behalte die ursprüngliche Satzstruktur bei
- Verändere keine Umgangssprache oder regionalen Ausdrücke
- Behalte alle Satzzeichen bei
- Antworte nur mit dem korrigierten Text, ohne zusätzliche Erklärungen
- Falls der Text bereits korrekt ist, gib ihn unverändert zurück""",

        "standard": """Du bist ein Assistent für Grammatik- und Rechtschreibkorrektur. Deine Aufgabe ist es, deutsche Texte zu korrigieren und dabei sowohl Rechtschreibung als auch grundlegende Grammatikfehler zu beheben.

Befolge diese Regeln:
- Korrigiere Rechtschreibfehler und grundlegende Grammatikfehler
- Verbessere falsche Wortstellungen und Zeitformen
- Korrigiere falsche Artikel (der, die, das)
- Behalte den ursprünglichen Stil und Ton bei
- Verändere keine bewussten Stilmittel oder Wortwahl
- Behalte Umgangssprache bei, korrigiere aber deren Grammatik
- Antworte nur mit dem korrigierten Text, ohne zusätzliche Erklärungen
- Falls der Text bereits korrekt ist, gib ihn unverändert zurück""",

        "strict": """Du bist ein Assistent für umfassende Textkorrektur. Deine Aufgabe ist es, deutsche Texte vollständig zu korrigieren und zu optimieren, um höchste sprachliche Qualität zu erreichen.

Befolge diese Regeln:
- Korrigiere alle Rechtschreib- und Grammatikfehler
- Verbessere Satzbau und Wortstellung für bessere Lesbarkeit
- Optimiere Wortwahl und verwende präzisere Begriffe wo angebracht
- Korrigiere Zeichensetzung und Groß-/Kleinschreibung
- Wandle Umgangssprache in Standarddeutsch um
- Verbessere den Textfluss und die Kohärenz
- Behalte die ursprüngliche Bedeutung und Kernaussagen bei
- Antworte nur mit dem korrigierten Text, ohne zusätzliche Erklärungen
- Falls der Text bereits auf höchstem Niveau ist, gib ihn unverändert zurück"""
    }

    USER_PROMPTS = {
        "correction": """Korrigiere folgenden Text:

{text}""",

        "dialect_normalization": """Wandle den folgenden dialektalen oder umgangssprachlichen Text in korrektes Hochdeutsch um, behalte aber die ursprüngliche Bedeutung bei:

{text}""",

        "with_context": """Korrigiere folgenden Text. Beachte dabei den Kontext der vorherigen und nachfolgenden Textpassagen:

Vorheriger Kontext: {prev_context}

ZU KORRIGIERENDER TEXT:
{text}

Nachfolgender Kontext: {next_context}"""
    }

    CORRECTION_EXAMPLES = {
        "light": {
            "input": "Das ist ein Beisspiel mit vielen Felern.",
            "output": "Das ist ein Beispiel mit vielen Fehlern."
        },
        "standard": {
            "input": "Ich bin gestern in die Stadt gegangen und habe mir ein neue Jacke kauft.",
            "output": "Ich bin gestern in die Stadt gegangen und habe mir eine neue Jacke gekauft."
        },
        "strict": {
            "input": "Ey, das war voll krass, wie der Typ da so rumgemacht hat, weißt du?",
            "output": "Es war beeindruckend, wie sich diese Person verhalten hat."
        }
    }

    DIALECT_EXAMPLES = {
        "bavarian": {
            "input": "I mog des ned, des is scho wieder z'vui.",
            "output": "Ich mag das nicht, das ist schon wieder zu viel."
        },
        "swabian": {
            "input": "Des isch aber älleweil no net fertig, gell?",
            "output": "Das ist aber immer noch nicht fertig, nicht wahr?"
        },
        "north_german": {
            "input": "Dat mook wi alles platt, dat warrt schon.",
            "output": "Das machen wir alles kaputt, das wird schon."
        }
    }


def get_correction_prompt(
    level: str,
    text: str,
    dialect_mode: bool = False,
    prev_context: str = None,
    next_context: str = None
) -> Dict[str, str]:
    """
    Generate system and user prompts for text correction.

    Args:
        level: Correction level (light, standard, strict)
        text: Text to be corrected
        dialect_mode: Whether to apply dialect normalization
        prev_context: Previous context for context-aware correction
        next_context: Next context for context-aware correction

    Returns:
        Dictionary with 'system' and 'user' prompts
    """
    # Validate correction level
    if level not in PromptTemplates.SYSTEM_PROMPTS:
        raise ValueError(f"Invalid correction level: {level}. Must be one of: {list(PromptTemplates.SYSTEM_PROMPTS.keys())}")

    # Get system prompt
    system_prompt = PromptTemplates.SYSTEM_PROMPTS[level]

    # Choose appropriate user prompt template
    if dialect_mode:
        user_template = PromptTemplates.USER_PROMPTS["dialect_normalization"]
        user_prompt = user_template.format(text=text)
    elif prev_context or next_context:
        user_template = PromptTemplates.USER_PROMPTS["with_context"]
        user_prompt = user_template.format(
            prev_context=prev_context or "[Kein vorheriger Kontext]",
            text=text,
            next_context=next_context or "[Kein nachfolgender Kontext]"
        )
    else:
        user_template = PromptTemplates.USER_PROMPTS["correction"]
        user_prompt = user_template.format(text=text)

    return {
        "system": system_prompt,
        "user": user_prompt
    }


def get_available_levels() -> List[str]:
    """
    Return list of available correction levels.

    Returns:
        List of available correction level names
    """
    return list(PromptTemplates.SYSTEM_PROMPTS.keys())


def get_correction_examples(level: str) -> Dict[str, str]:
    """
    Get correction examples for a specific level.

    Args:
        level: Correction level

    Returns:
        Dictionary with 'input' and 'output' examples

    Raises:
        ValueError: If level is invalid
    """
    if level not in PromptTemplates.CORRECTION_EXAMPLES:
        raise ValueError(f"Invalid correction level: {level}")

    return PromptTemplates.CORRECTION_EXAMPLES[level]


def get_dialect_examples() -> Dict[str, Dict[str, str]]:
    """
    Get dialect normalization examples.

    Returns:
        Dictionary with dialect examples
    """
    return PromptTemplates.DIALECT_EXAMPLES.copy()


def validate_prompt_inputs(level: str, text: str) -> None:
    """
    Validate inputs for prompt generation.

    Args:
        level: Correction level
        text: Text to be corrected

    Raises:
        ValueError: If inputs are invalid
    """
    if not isinstance(level, str):
        raise ValueError("Level must be a string")

    if level not in get_available_levels():
        raise ValueError(f"Invalid correction level: {level}. Available levels: {get_available_levels()}")

    if not isinstance(text, str):
        raise ValueError("Text must be a string")

    if not text.strip():
        raise ValueError("Text cannot be empty or only whitespace")

    if len(text) > 10000:  # Reasonable limit for single prompt
        raise ValueError("Text too long for single prompt (max 10,000 characters)")


class CorrectionPrompts:
    """
    High-level interface for generating correction prompts.
    """

    def __init__(self):
        """Initialize the CorrectionPrompts interface."""
        self.templates = PromptTemplates()

    def get_prompt(
        self,
        level: CorrectionLevel,
        text: str,
        dialect_mode: bool = False,
        prev_context: str = None,
        next_context: str = None
    ) -> Dict[str, str]:
        """
        Generate correction prompts with validation.

        Args:
            level: Correction level enum
            text: Text to be corrected
            dialect_mode: Whether to apply dialect normalization
            prev_context: Previous context for context-aware correction
            next_context: Next context for context-aware correction

        Returns:
            Dictionary with 'system' and 'user' prompts
        """
        level_str = level.value if isinstance(level, CorrectionLevel) else level
        validate_prompt_inputs(level_str, text)

        return get_correction_prompt(
            level=level_str,
            text=text,
            dialect_mode=dialect_mode,
            prev_context=prev_context,
            next_context=next_context
        )

    def get_available_levels(self) -> List[CorrectionLevel]:
        """
        Get available correction levels as enums.

        Returns:
            List of CorrectionLevel enums
        """
        return [CorrectionLevel(level) for level in get_available_levels()]

    def estimate_tokens(self, text: str, level: CorrectionLevel) -> int:
        """
        Estimate token count for a correction prompt.

        Args:
            text: Text to be corrected
            level: Correction level

        Returns:
            Estimated token count (rough approximation)
        """
        # Rough approximation: 1 token per 4 characters for German text
        # System prompt + user prompt + text
        system_prompt = self.templates.SYSTEM_PROMPTS[level.value]
        user_template = self.templates.USER_PROMPTS["correction"]

        total_chars = len(system_prompt) + len(user_template) + len(text)
        estimated_tokens = total_chars // 4

        # Add some buffer for formatting and special tokens
        return int(estimated_tokens * 1.2)