"""
Regression tests for number-word formatting in TextCleanupProcessor.

Bug: _format_numbers_and_lists digitized any number word followed by a comma,
"and"/"or", or a sentence boundary, corrupting ordinary prose. It must only
digitize number words inside enumeration runs.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.core.text_cleanup import TextCleanupProcessor

PROSE_PRESERVED = [
    ("No one.", "No one."),
    ("one and only", "One and only"),
    ("one or two apples", "One or two apples"),
    ("nine or ten points", "Nine or ten points"),
    ("That is the one.", "That is the one."),
    ("number one", "Number one"),
    ("one more thing", "One more thing"),
    ("the one", "The one"),
]


class TestNumberWordsInProse:
    @pytest.mark.parametrize("text,expected", PROSE_PRESERVED)
    def test_prose_is_preserved(self, text, expected):
        assert TextCleanupProcessor().cleanup(text) == expected


ENUMERATIONS_CONVERTED = [
    ("one, two, three", "1, 2, 3"),
    ("one and two", "1 and 2"),
    ("I have one, two, three items", "I have 1, 2, 3 items"),
    ("four, five, six apples", "4, 5, 6 apples"),
    ("nine, ten", "9, 10"),
    ("one, two and three", "1, 2 and 3"),
]


class TestNumberListEnumeration:
    @pytest.mark.parametrize("text,expected", ENUMERATIONS_CONVERTED)
    def test_lists_are_digitized(self, text, expected):
        assert TextCleanupProcessor().cleanup(text) == expected
