"""
Text cleanup processor for removing filler words from transcriptions.

Handles common speech fillers (um, uh, like, you know, etc.) while preserving
sentence structure and capitalization context.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


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

    def __init__(self, custom_fillers: Optional[list[str]] = None):
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
