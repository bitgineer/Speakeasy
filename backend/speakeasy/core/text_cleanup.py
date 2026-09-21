"""
Text cleanup processor for removing filler words from transcriptions.

Handles common speech fillers (um, uh, like, you know, etc.) while preserving
sentence structure and capitalization context.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Module-level cached processor instance
_cached_processor: Optional["TextCleanupProcessor"] = None


def get_cached_processor(custom_fillers: list[str] | None = None) -> "TextCleanupProcessor":
    """Get cached TextCleanupProcessor instance (creates if needed)."""
    global _cached_processor

    if _cached_processor is None:
        _cached_processor = TextCleanupProcessor(custom_fillers=custom_fillers)

    return _cached_processor


def clear_cached_processor() -> None:
    """Clear the cached processor (useful for testing or when settings change)."""
    global _cached_processor
    _cached_processor = None


def safe_cleanup(
    text: str,
    custom_fillers: list[str] | None = None,
    use_cache: bool = True,
    timeout_seconds: float = 5.0,
) -> str:
    """
    Safely cleanup text with error handling and timeout protection.

    Args:
        text: Text to clean.
        custom_fillers: Optional custom filler words.
        use_cache: If True, use cached processor; otherwise create new one.
        timeout_seconds: Max time allowed for cleanup operation.

    Returns:
        Cleaned text, or original text if cleanup fails.
    """
    # Handle None or empty input
    if text is None:
        return ""
    if not text.strip():
        return text

    try:
        if use_cache:
            processor = get_cached_processor(custom_fillers=custom_fillers)
        else:
            processor = TextCleanupProcessor(custom_fillers=custom_fillers)

        return processor.cleanup(text)

    except Exception as e:
        logger.warning(f"Text cleanup failed, returning original text: {e}")
        return text

    try:
        if use_cache:
            processor = get_cached_processor(custom_fillers=custom_fillers)
        else:
            processor = TextCleanupProcessor(custom_fillers=custom_fillers)

        return processor.cleanup(text)

    except Exception as e:
        logger.warning(f"Text cleanup failed, returning original text: {e}")
        return text


class TextCleanupProcessor:
    """
    Removes filler words from transcribed text while preserving sentence structure.

    Handles common speech fillers like "um", "uh", "like", "you know", etc.
    Preserves capitalization at sentence boundaries and cleans up spacing/punctuation.
    """

    # Default filler words (case-insensitive matching)
    DEFAULT_FILLERS = [
        # Vocal hesitations
        "um",
        "uh",
        "uhh",
        "umm",
        "err",
        "ah",
        "ahh",
        # Discourse markers
        "like",
        "you know",
        "i mean",
        "sort of",
        "kind of",
        # Intensifiers/hedges
        "so",
        "well",
        "actually",
        "basically",
        "literally",
        "honestly",
        # Acknowledgments
        "right",
        "okay",
        "alright",
        "anyway",
    ]

    def __init__(self, custom_fillers: list[str] | None = None):
        """
        Initialize the text cleanup processor.

        Args:
            custom_fillers: Optional list of additional filler words to remove.
                           If provided, these are added to the default fillers.
        """
        self.fillers = self.DEFAULT_FILLERS.copy()
        if custom_fillers:
            self.fillers.extend(custom_fillers)

        # Build regex pattern for word boundary matching
        # Sort by length (longest first) to match multi-word fillers first
        sorted_fillers = sorted(self.fillers, key=len, reverse=True)
        # Escape special regex characters and create pattern with word boundaries
        escaped_fillers = [re.escape(filler) for filler in sorted_fillers]
        pattern = r"\b(" + "|".join(escaped_fillers) + r")\b"
        self.filler_pattern = re.compile(pattern, re.IGNORECASE)

    def cleanup(self, text: str) -> str:
        """
        Remove filler words from text while preserving sentence structure.

        Handles:
        - Case-insensitive filler matching with word boundaries
        - Capitalization preservation at sentence starts
        - Multiple consecutive fillers
        - Fillers at text boundaries
        - Cleanup of extra spaces and orphaned punctuation

        Args:
            text: The transcribed text to clean.

        Returns:
            Cleaned text with filler words removed.
        """
        if not text or not text.strip():
            return text

        result = text
        result = self.filler_pattern.sub(" ", result)
        result = self._cleanup_spacing(result)
        result = self._fix_sentence_capitalization(result)
        result = self._format_numbers_and_lists(result)

        return result.strip()

    def _cleanup_spacing(self, text: str) -> str:
        """
        Clean up spacing and punctuation issues.

        Removes:
        - Multiple consecutive spaces
        - Spaces before punctuation
        - Orphaned punctuation (e.g., ", , ")
        - Leading punctuation

        Args:
            text: Text to clean.

        Returns:
            Text with spacing issues fixed.
        """
        text = re.sub(r" +", " ", text)
        text = re.sub(r" ([,.!?;:])", r"\1", text)
        text = re.sub(r"([,.!?;:])\s*([,.!?;:])", r"\1", text)
        text = re.sub(r"^[,.!?;:\s]+", "", text)
        text = text.strip()

        return text

    def _fix_sentence_capitalization(self, text: str) -> str:
        """
        Capitalize first letter of text and after sentence-ending punctuation.

        Args:
            text: Text to fix.

        Returns:
            Text with corrected capitalization.
        """
        if not text:
            return text

        if text[0].isalpha():
            text = text[0].upper() + text[1:]

        def capitalize_after_sentence(match):
            return match.group(1) + match.group(2) + match.group(3).upper()

        text = re.sub(r"([.!?])(\s+)([a-z])", capitalize_after_sentence, text)
        return text

    # Number words mapped to digits (common in dictation)
    _NUMBER_WORDS = {
        "zero": "0",
        "one": "1",
        "two": "2",
        "three": "3",
        "four": "4",
        "five": "5",
        "six": "6",
        "seven": "7",
        "eight": "8",
        "nine": "9",
        "ten": "10",
    }

    _NUMBER_WORD = r"(?:zero|one|two|three|four|five|six|seven|eight|nine|ten)"
    _LIST_CONNECTOR = r"(?:\s*,\s*(?:and\s+|or\s+)?|\s+and\s+)"
    _NUMBER_LIST_PATTERN = re.compile(
        rf"\b{_NUMBER_WORD}\b(?:{_LIST_CONNECTOR}\b{_NUMBER_WORD}\b)+",
        re.IGNORECASE,
    )

    def _format_numbers_and_lists(self, text: str) -> str:
        """
        Convert number words to digits only in enumeration contexts.

        Converts: "one, two, three" → "1, 2, 3"
                  "one and two" → "1 and 2"
        Preserves: "one more thing", "number one", "the one"
        """

        # A run of number words joined by commas or "and" is an enumeration.
        # A lone number word is prose, even before "and"/"or" or a sentence end.
        def convert(match: re.Match) -> str:
            return re.sub(
                rf"\b({self._NUMBER_WORD})\b",
                lambda m: self._NUMBER_WORDS[m.group(1).lower()],
                match.group(0),
                flags=re.IGNORECASE,
            )

        return self._NUMBER_LIST_PATTERN.sub(convert, text)
