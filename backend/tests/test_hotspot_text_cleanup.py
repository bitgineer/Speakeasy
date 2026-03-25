"""
Hotspot tests for text_cleanup.py - CRITICAL (75 callers)

Tests the cleanup() method and TextCleanupProcessor class.
This is the MOST CALLED function in the codebase - changes here affect ALL transcriptions.

Blast Radius:
- 75 direct callers
- Used in every transcription pipeline
- Affects text output quality across entire application

Coverage Targets:
- Basic cleanup functionality
- Edge cases (empty, None, special characters)
- Filler word variations
- Capitalization preservation
- Spacing cleanup
- Custom fillers
"""

import pytest

from speakeasy.core.text_cleanup import TextCleanupProcessor


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def processor():
    """Create default text cleanup processor."""
    return TextCleanupProcessor()


@pytest.fixture
def processor_with_custom_fillers():
    """Create processor with custom filler words."""
    custom = ["dude", "bro", "man"]
    return TextCleanupProcessor(custom_fillers=custom)


# =============================================================================
# Basic Cleanup Tests
# =============================================================================


class TestBasicCleanup:
    """Basic cleanup functionality tests."""

    def test_cleanup_empty_string(self, processor):
        """Empty string returns empty string."""
        assert processor.cleanup("") == ""

    def test_cleanup_whitespace_only(self, processor):
        """Whitespace-only string returns stripped whitespace."""
        assert processor.cleanup("   ") == ""
        assert processor.cleanup("\t\n") == ""

    def test_cleanup_none_input(self, processor):
        """None input returns None."""
        assert processor.cleanup(None) is None

    def test_cleanup_no_fillers(self, processor):
        """Text without fillers returns unchanged."""
        text = "Hello world, this is a test."
        assert processor.cleanup(text) == text

    def test_cleanup_single_filler(self, processor):
        """Single filler word is removed."""
        assert processor.cleanup("um hello") == "Hello"
        assert processor.cleanup("hello uh world") == "Hello world"

    def test_cleanup_multiple_fillers(self, processor):
        """Multiple filler words are removed."""
        text = "um uh like you know hello"
        result = processor.cleanup(text)
        assert "um" not in result.lower()
        assert "uh" not in result.lower()
        assert "like" not in result.lower()
        assert "you know" not in result.lower()
        assert "hello" in result


# =============================================================================
# Filler Word Tests
# =============================================================================


class TestFillerWords:
    """Tests for various filler word patterns."""

    def test_vocal_hesitations(self, processor):
        """Vocal hesitation fillers are removed."""
        fillers = ["um", "uh", "uhh", "umm", "err", "ah", "ahh"]
        for filler in fillers:
            text = f"{filler} hello world"
            result = processor.cleanup(text)
            assert filler not in result.lower()

    def test_discourse_markers(self, processor):
        """Discourse marker fillers are removed."""
        markers = ["like", "you know", "i mean", "sort of", "kind of"]
        for marker in markers:
            text = f"{marker} this is a test"
            result = processor.cleanup(text)
            # Multi-word markers might have partial matches, check carefully
            if " " in marker:
                assert marker not in result.lower()
            else:
                assert marker not in result.lower()

    def test_intensifiers(self, processor):
        """Intensifier fillers are removed."""
        intensifiers = ["so", "well", "actually", "basically", "literally", "honestly"]
        for intensifier in intensifiers:
            text = f"{intensifier} I think this works"
            result = processor.cleanup(text)
            assert intensifier not in result.lower()

    def test_acknowledgments(self, processor):
        """Acknowledgment fillers are removed."""
        acknowledgments = ["right", "okay", "alright", "anyway"]
        for ack in acknowledgments:
            text = f"{ack} let's continue"
            result = processor.cleanup(text)
            assert ack not in result.lower()

    def test_case_insensitive_fillers(self, processor):
        """Fillers are matched case-insensitively."""
        test_cases = [
            "UM hello",
            "Um hello",
            "uM hello",
            "HELLO uh WORLD",
            "Like this is cool",
            "LIKE this is cool",
        ]
        for text in test_cases:
            result = processor.cleanup(text)
            assert "um" not in result.lower()
            assert "uh" not in result.lower()
            assert "like" not in result.lower()

    def test_consecutive_fillers(self, processor):
        """Consecutive fillers are all removed."""
        text = "um uh ah like you know I mean hello"
        result = processor.cleanup(text)
        assert result == "Hello"

    def test_filler_at_start(self, processor):
        """Filler at text start is removed with capitalization preserved."""
        assert processor.cleanup("um hello world") == "Hello world"
        assert processor.cleanup("like this is cool") == "This is cool"

    def test_filler_at_end(self, processor):
        """Filler at text end is removed."""
        assert processor.cleanup("hello world um") == "Hello world"
        assert processor.cleanup("test uh") == "Test"

    def test_filler_in_middle(self, processor):
        """Filler in middle is removed cleanly."""
        assert processor.cleanup("hello um world") == "Hello world"
        assert processor.cleanup("test like this works") == "Test this works"


# =============================================================================
# Custom Fillers Tests
# =============================================================================


class TestCustomFillers:
    """Tests for custom filler word functionality."""

    def test_custom_fillers_added(self, processor_with_custom_fillers):
        """Custom fillers are added to defaults."""
        processor = processor_with_custom_fillers
        text = "dude bro man um hello"
        result = processor.cleanup(text)
        assert "dude" not in result.lower()
        assert "bro" not in result.lower()
        assert "man" not in result.lower()
        assert "um" not in result.lower()
        assert "hello" in result

    def test_custom_fillers_case_insensitive(self, processor_with_custom_fillers):
        """Custom fillers are case-insensitive."""
        processor = processor_with_custom_fillers
        test_cases = ["DUDE hello", "Dude hello", "dude hello"]
        for text in test_cases:
            result = processor.cleanup(text)
            assert "dude" not in result.lower()


# =============================================================================
# Spacing Cleanup Tests
# =============================================================================


class TestSpacingCleanup:
    """Tests for spacing and punctuation cleanup."""

    def test_multiple_spaces_collapsed(self, processor):
        """Multiple spaces are collapsed to single space."""
        assert processor.cleanup("hello    world") == "Hello world"
        assert processor.cleanup("test    with    spaces") == "Test with spaces"

    def test_space_before_punctuation_removed(self, processor):
        """Spaces before punctuation are removed."""
        assert processor.cleanup("hello , world") == "Hello, world"
        assert processor.cleanup("test .") == "Test."
        assert processor.cleanup("what ?") == "What?"

    def test_orphaned_punctuation_cleaned(self, processor):
        """Orphaned punctuation is cleaned."""
        assert processor.cleanup(", , hello") == "Hello"
        assert processor.cleanup(". . test") == "Test."

    def test_leading_punctuation_removed(self, processor):
        """Leading punctuation is removed."""
        assert processor.cleanup(", hello world") == "Hello world"
        assert processor.cleanup(". test") == "Test"
        assert processor.cleanup("! what") == "What"

    def test_trailing_spaces_removed(self, processor):
        """Trailing spaces are removed."""
        assert processor.cleanup("hello world   ") == "Hello world"
        assert processor.cleanup("test\t") == "Test"


# =============================================================================
# Capitalization Tests
# =============================================================================


class TestCapitalization:
    """Tests for sentence capitalization preservation."""

    def test_first_letter_capitalized(self, processor):
        """First letter is capitalized."""
        assert processor.cleanup("hello world") == "Hello world"
        assert processor.cleanup("test this") == "Test this"

    def test_already_capitalized_preserved(self, processor):
        """Already capitalized text is preserved."""
        assert processor.cleanup("Hello world") == "Hello world"
        assert processor.cleanup("THIS IS A TEST") == "THIS IS A TEST"

    def test_capitalization_after_period(self, processor):
        """Letter after period is capitalized."""
        assert processor.cleanup("hello. world") == "Hello. World"
        assert processor.cleanup("test. another sentence") == "Test. Another sentence"

    def test_capitalization_after_exclamation(self, processor):
        """Letter after exclamation is capitalized."""
        assert processor.cleanup("wow! amazing") == "Wow! Amazing"
        assert processor.cleanup("great! now this") == "Great! Now this"

    def test_capitalization_after_question(self, processor):
        """Letter after question mark is capitalized."""
        assert processor.cleanup("what? i don't know") == "What? I don't know"
        assert processor.cleanup("really? yes") == "Really? Yes"

    def test_capitalization_with_fillers_removed(self, processor):
        """Capitalization preserved when fillers removed from start."""
        assert processor.cleanup("um hello world") == "Hello world"
        assert processor.cleanup("like this is cool") == "This is cool"
        assert processor.cleanup("well I think so") == "I think so"


# =============================================================================
# Complex Scenarios Tests
# =============================================================================


class TestComplexScenarios:
    """Tests for complex real-world scenarios."""

    def test_realistic_speech_pattern(self, processor):
        """Realistic speech with multiple fillers."""
        text = "um so like you know i mean uh this is basically like a test"
        result = processor.cleanup(text)
        assert result == "This is test"

    def test_long_text_multiple_sentences(self, processor):
        """Long text with multiple sentences."""
        text = "um hello. uh how are you? like i hope well. basically great"
        result = processor.cleanup(text)
        assert result == "Hello. How are you? I hope well. Great"

    def test_text_with_numbers(self, processor):
        """Text with numbers is handled correctly."""
        text = "um test 123 like test 456"
        result = processor.cleanup(text)
        assert result == "Test 123 test 456"

    def test_text_with_special_characters(self, processor):
        """Text with special characters is preserved."""
        text = "um hello @world #test like this"
        result = processor.cleanup(text)
        assert result == "Hello @world #test this"

    def test_text_with_contractions(self, processor):
        """Text with contractions is preserved."""
        text = "um i'm like you're testing don't remove contractions"
        result = processor.cleanup(text)
        assert "i'm" in result.lower() or "I'm" in result
        assert "you're" in result.lower() or "You're" in result
        assert "don't" in result.lower() or "Don't" in result

    def test_technical_text_preserved(self, processor):
        """Technical text is preserved."""
        text = "um the API endpoint like returns JSON with uh status code 200"
        result = processor.cleanup(text)
        assert "API" in result
        assert "JSON" in result
        assert "200" in result


# =============================================================================
# Performance Tests
# =============================================================================


class TestPerformance:
    """Performance tests for cleanup (called 75 times per transcription)."""

    def test_cleanup_speed_short_text(self, processor):
        """Cleanup is fast for short text."""
        import time

        text = "um hello uh world"
        start = time.perf_counter()
        for _ in range(1000):
            processor.cleanup(text)
        elapsed = time.perf_counter() - start

        # Should process 1000 short texts in < 0.1 seconds
        assert elapsed < 0.1, f"Too slow: {elapsed:.3f}s for 1000 iterations"

    def test_cleanup_speed_long_text(self, processor):
        """Cleanup is fast for long text."""
        import time

        text = "um " * 100 + "hello" + " uh " * 100 + "world"
        start = time.perf_counter()
        for _ in range(100):
            processor.cleanup(text)
        elapsed = time.perf_counter() - start

        # Should process 100 long texts in < 0.5 seconds
        assert elapsed < 0.5, f"Too slow: {elapsed:.3f}s for 100 iterations"


# =============================================================================
# Edge Cases Tests
# =============================================================================


class TestEdgeCases:
    """Edge case tests."""

    def test_single_character(self, processor):
        """Single character text is handled."""
        assert processor.cleanup("a") == "A"
        assert processor.cleanup("A") == "A"

    def test_only_fillers(self, processor):
        """Text with only fillers returns empty."""
        assert processor.cleanup("um uh like") == ""
        assert processor.cleanup("you know i mean") == ""

    def test_unicode_characters(self, processor):
        """Unicode characters are preserved."""
        text = "um hello 世界 uh مرحبا like test"
        result = processor.cleanup(text)
        assert "世界" in result
        assert "مرحبا" in result

    def test_emoji_preserved(self, processor):
        """Emoji are preserved."""
        text = "um hello 👍 uh world 🎉 like test"
        result = processor.cleanup(text)
        assert "👍" in result
        assert "🎉" in result

    def test_mixed_languages(self, processor):
        """Mixed language text is handled."""
        text = "um hello uh bonjour like hola test"
        result = processor.cleanup(text)
        assert "hello" in result
        assert "bonjour" in result
        assert "hola" in result

    def test_newlines_preserved(self, processor):
        """Newlines are handled gracefully."""
        text = "um hello\nuh world\nlike test"
        result = processor.cleanup(text)
        assert "Hello" in result
        assert "world" in result
        assert "test" in result

    def test_tabs_handled(self, processor):
        """Tabs are handled gracefully."""
        text = "um\thello\tuh\tworld"
        result = processor.cleanup(text)
        assert "Hello" in result
        assert "world" in result


# =============================================================================
# Integration-like Tests
# =============================================================================


class TestIntegrationLike:
    """Integration-like tests simulating real usage."""

    def test_transcription_pipeline_simulation(self, processor):
        """Simulate cleanup in transcription pipeline."""
        # Simulate 10 transcriptions with typical filler patterns
        transcriptions = [
            "um so like this is transcription one",
            "uh you know the second one here",
            "like i mean basically test three",
            "well actually um fourth test",
            "right okay so fifth one",
        ]

        cleaned = [processor.cleanup(t) for t in transcriptions]

        # Verify all fillers removed
        for text in cleaned:
            assert "um" not in text.lower()
            assert "uh" not in text.lower()
            assert "like" not in text.lower()
            assert "you know" not in text.lower()

        # Verify text is still readable
        assert all(len(t) > 0 for t in cleaned)
        assert all(t[0].isupper() for t in cleaned if t)

    def test_batch_processing(self, processor):
        """Batch processing multiple texts."""
        texts = [f"um test {i} uh like filler" for i in range(100)]
        results = [processor.cleanup(t) for t in texts]

        # All should be cleaned
        assert len(results) == 100
        assert all("um" not in r.lower() for r in results)
        assert all("uh" not in r.lower() for r in results)
        assert all(f"Test {i}" in r for i, r in enumerate(results))
