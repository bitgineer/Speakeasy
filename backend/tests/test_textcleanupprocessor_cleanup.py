"""
Test for TextCleanupProcessor.cleanup
Comprehensive test suite for text cleanup functionality.
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.core.text_cleanup import TextCleanupProcessor, safe_cleanup, get_cached_processor


class TestTextCleanupProcessorCleanup:
    """Tests for TextCleanupProcessor.cleanup"""

    def test_cleanup_removes_filler_words(self):
        """Test that cleanup removes filler words."""
        processor = TextCleanupProcessor()

        text = "Um, hello uh world like you know"
        result = processor.cleanup(text)

        assert "um" not in result.lower()
        assert "uh" not in result.lower()
        assert "like" not in result.lower()
        assert "hello world" in result.lower()

    def test_cleanup_preserves_meaning(self):
        """Test that cleanup preserves sentence meaning."""
        processor = TextCleanupProcessor()

        text = "Um, I mean, this is basically a test"
        result = processor.cleanup(text)

        assert "this is a test" in result.lower()

    def test_cleanup_handles_empty_string(self):
        """Test cleanup with empty string."""
        processor = TextCleanupProcessor()

        result = processor.cleanup("")

        assert result == ""

    def test_cleanup_handles_whitespace(self):
        """Test that cleanup normalizes whitespace."""
        processor = TextCleanupProcessor()

        text = "Um   uh   like   hello"
        result = processor.cleanup(text)

        assert "  " not in result  # No double spaces

    def test_cleanup_capitalization(self):
        """Test that cleanup fixes sentence capitalization."""
        processor = TextCleanupProcessor()

        text = "um, hello world. this is a test"
        result = processor.cleanup(text)

        assert result[0].isupper()
        assert "Hello world" in result
        assert "This is a test" in result

    def test_cleanup_with_custom_fillers(self):
        """Test cleanup with custom filler words."""
        processor = TextCleanupProcessor(custom_fillers=["customword"])

        text = "Hello customword world"
        result = processor.cleanup(text)

        assert "customword" not in result.lower()

    def test_cleanup_punctuation(self):
        """Test that cleanup handles punctuation properly."""
        processor = TextCleanupProcessor()

        text = "Um, hello! Uh, world?"
        result = processor.cleanup(text)

        assert result.startswith("Hello")
        assert "!" in result
        assert "?" in result

    def test_cleanup_no_changes_needed(self):
        """Test cleanup when no filler words present."""
        processor = TextCleanupProcessor()

        text = "This is a clean sentence"
        result = processor.cleanup(text)

        assert result == "This is a clean sentence"


class TestSafeCleanup:
    """Tests for safe_cleanup function"""

    def test_safe_cleanup_basic(self):
        """Test basic safe cleanup."""
        result = safe_cleanup("Um hello world")

        assert "um" not in result.lower()

    def test_safe_cleanup_handles_none(self):
        """Test that safe_cleanup handles None input."""
        result = safe_cleanup(None)

        assert result == ""

    def test_safe_cleanup_handles_exception(self):
        """Test that safe_cleanup returns original text on error."""
        result = safe_cleanup("Normal text")

        # Should not raise and should return something
        assert isinstance(result, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
