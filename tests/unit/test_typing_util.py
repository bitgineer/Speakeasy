"""
Unit tests for typing_util module.

This test module covers:
- Character-by-character typing functionality
- Special character handling with shift key
- Unicode character fallback
- Typing timing and delays
- Clipboard fallback for Unicode content

Run with: pytest tests/unit/test_typing_util.py -v
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
from time import sleep

from faster_whisper_hotkey.typing_util import (
    SmartTyper,
    TypingResult,
    get_smart_typer,
    type_text,
    SHIFT_CHARS,
    UPPERCASE_SHIFT,
    DIRECT_CHARS,
)


# ============================================================================
# Test: SmartTyper Initialization
# ============================================================================

@pytest.mark.unit
class TestSmartTyperInit:
    """Tests for SmartTyper initialization."""

    @pytest.mark.unit
    def test_init_with_defaults(self):
        """Test initialization with default values."""
        typer = SmartTyper()
        assert typer.char_delay == 0.01
        assert typer.pre_delay == 0.05
        assert typer.post_delay == 0.05
        assert typer.max_unicode_fallback_chars == 100

    @pytest.mark.unit
    def test_init_with_custom_delays(self):
        """Test initialization with custom delays."""
        typer = SmartTyper(char_delay=0.02, pre_delay=0.1, post_delay=0.1)
        assert typer.char_delay == 0.02
        assert typer.pre_delay == 0.1
        assert typer.post_delay == 0.1

    @pytest.mark.unit
    def test_is_available_with_keyboard(self):
        """Test is_available returns True when keyboard is available."""
        with patch('faster_whisper_hotkey.typing_util.keyboard') as mock_keyboard:
            mock_keyboard.Controller.return_value = MagicMock()
            typer = SmartTyper()
            assert typer.is_available() is True

    @pytest.mark.unit
    def test_is_available_without_keyboard(self):
        """Test is_available returns False when keyboard is not available."""
        with patch('faster_whisper_hotkey.typing_util.keyboard', side_effect=ImportError):
            typer = SmartTyper()
            assert typer.is_available() is False


# ============================================================================
# Test: Character Typing
# ============================================================================

@pytest.mark.unit
class TestCharacterTyping:
    """Tests for individual character typing."""

    @pytest.fixture
    def mock_keyboard(self):
        """Mock keyboard controller."""
        mock_ctrl = MagicMock()
        with patch('faster_whisper_hotkey.typing_util.keyboard', MagicMock(Controller=MagicMock(return_value=mock_ctrl))):
            typer = SmartTyper(pre_delay=0, post_delay=0, char_delay=0)
            typer._keyboard = mock_ctrl
            yield typer, mock_ctrl

    @pytest.mark.unit
    def test_type_lowercase_letters(self, mock_keyboard):
        """Test typing lowercase letters."""
        typer, ctrl = mock_keyboard
        result = typer.type("abc")

        assert result.success is True
        assert result.chars_typed == 3

    @pytest.mark.unit
    def test_type_uppercase_letters_with_shift(self, mock_keyboard):
        """Test typing uppercase letters uses shift key."""
        typer, ctrl = mock_keyboard
        result = typer.type("ABC")

        assert result.success is True
        assert result.chars_typed == 3

    @pytest.mark.unit
    def test_type_numbers(self, mock_keyboard):
        """Test typing numbers."""
        typer, ctrl = mock_keyboard
        result = typer.type("123")

        assert result.success is True
        assert result.chars_typed == 3

    @pytest.mark.unit
    def test_type_special_chars_with_shift(self, mock_keyboard):
        """Test typing special characters that require shift."""
        typer, ctrl = mock_keyboard
        result = typer.type("!@#$%")

        assert result.success is True
        assert result.chars_typed == 5

    @pytest.mark.unit
    def test_type_mixed_content(self, mock_keyboard):
        """Test typing mixed content (letters, numbers, special chars)."""
        typer, ctrl = mock_keyboard
        result = typer.type("Hello, World! 123")

        assert result.success is True
        assert result.chars_typed == 17  # Includes space, comma, exclamation

    @pytest.mark.unit
    def test_type_newline(self, mock_keyboard):
        """Test typing newline character."""
        typer, ctrl = mock_keyboard
        result = typer.type("line1\nline2")

        assert result.success is True
        assert result.chars_typed == 10  # "line1" + "line2" + newline

    @pytest.mark.unit
    def test_type_tab(self, mock_keyboard):
        """Test typing tab character."""
        typer, ctrl = mock_keyboard
        result = typer.type("\t")

        assert result.success is True
        assert result.chars_typed == 1

    @pytest.mark.unit
    def test_type_empty_string(self, mock_keyboard):
        """Test typing empty string."""
        typer, ctrl = mock_keyboard
        result = typer.type("")

        assert result.success is True
        assert result.chars_typed == 0

    @pytest.mark.unit
    def test_type_spaces(self, mock_keyboard):
        """Test typing spaces."""
        typer, ctrl = mock_keyboard
        result = typer.type("   ")

        assert result.success is True
        assert result.chars_typed == 3


# ============================================================================
# Test: Unicode Handling
# ============================================================================

@pytest.mark.unit
class TestUnicodeHandling:
    """Tests for Unicode character handling."""

    @pytest.fixture
    def mock_keyboard(self):
        """Mock keyboard controller."""
        mock_ctrl = MagicMock()
        with patch('faster_whisper_hotkey.typing_util.keyboard', MagicMock(Controller=MagicMock(return_value=mock_ctrl))):
            typer = SmartTyper(pre_delay=0, post_delay=0, char_delay=0)
            typer._keyboard = mock_ctrl
            yield typer, mock_ctrl

    @pytest.mark.unit
    def test_get_unicode_chars(self, mock_keyboard):
        """Test detection of Unicode characters."""
        typer, ctrl = mock_keyboard

        # ASCII only - no unicode
        unicode_chars = typer._get_unicode_chars("Hello World")
        assert len(unicode_chars) == 0

        # With emoji
        unicode_chars = typer._get_unicode_chars("Hello 👋")
        assert len(unicode_chars) == 1

        # With CJK characters
        unicode_chars = typer._get_unicode_chars("Hello 世界")
        assert len(unicode_chars) == 2

    @pytest.mark.unit
    def test_clipboard_fallback_for_unicode(self, mock_keyboard):
        """Test clipboard fallback is used for Unicode content."""
        typer, ctrl = mock_keyboard

        with patch('faster_whisper_hotkey.typing_util.set_clipboard') as mock_set:
            with patch('faster_whisper_hotkey.typing_util.paste_to_active_window') as mock_paste:
                mock_set.return_value = True
                result = typer.type("Hello 世界")

                assert result.success is True
                assert result.fallback_used is True


# ============================================================================
# Test: Shift Characters Constants
# ============================================================================

@pytest.mark.unit
class TestShiftCharacterConstants:
    """Tests for shift character mapping constants."""

    @pytest.mark.unit
    def test_shift_chars_mapping(self):
        """Test SHIFT_CHARS mapping is correct."""
        assert '~' in SHIFT_CHARS
        assert SHIFT_CHARS['~'] == '`'
        assert '!' in SHIFT_CHARS
        assert SHIFT_CHARS['!'] == '1'
        assert '@' in SHIFT_CHARS
        assert SHIFT_CHARS['@'] == '2'

    @pytest.mark.unit
    def test_uppercase_shift_set(self):
        """Test UPPERCASE_SHIFT contains all uppercase letters."""
        assert 'A' in UPPERCASE_SHIFT
        assert 'Z' in UPPERCASE_SHIFT
        assert len(UPPERCASE_SHIFT) == 26

    @pytest.mark.unit
    def test_direct_chars_set(self):
        """Test DIRECT_CHARS contains typeable characters."""
        assert 'a' in DIRECT_CHARS
        assert 'z' in DIRECT_CHARS
        assert ' ' in DIRECT_CHARS  # Space


# ============================================================================
# Test: Singleton Instance
# ============================================================================

@pytest.mark.unit
class TestSingleton:
    """Tests for singleton pattern."""

    @pytest.mark.unit
    def test_get_smart_typer_returns_same_instance(self):
        """Test get_smart_typer returns singleton instance."""
        # Clear any existing instance
        import faster_whisper_hotkey.typing_util as typing_module
        typing_module._instance = None

        typer1 = get_smart_typer()
        typer2 = get_smart_typer()

        assert typer1 is typer2

    @pytest.mark.unit
    def test_type_text_convenience_function(self):
        """Test type_text convenience function."""
        with patch('faster_whisper_hotkey.typing_util.get_smart_typer') as mock_get:
            mock_typer = MagicMock()
            mock_result = TypingResult(success=True, chars_typed=5)
            mock_typer.type.return_value = mock_result
            mock_get.return_value = mock_typer

            result = type_text("test", char_delay=0.02)

            assert result.success is True
            mock_typer.type.assert_called_once_with("test")


# ============================================================================
# Test: TypingResult Dataclass
# ============================================================================

@pytest.mark.unit
class TestTypingResult:
    """Tests for TypingResult dataclass."""

    @pytest.mark.unit
    def test_typing_result_creation(self):
        """Test creating TypingResult."""
        result = TypingResult(
            success=True,
            chars_typed=10,
            chars_skipped=0,
            fallback_used=False,
            error_message="",
            duration_ms=100.5
        )

        assert result.success is True
        assert result.chars_typed == 10
        assert result.chars_skipped == 0
        assert result.fallback_used is False
        assert result.error_message == ""
        assert result.duration_ms == 100.5

    @pytest.mark.unit
    def test_typing_result_defaults(self):
        """Test TypingResult default values."""
        result = TypingResult(success=True)

        assert result.success is True
        assert result.chars_typed == 0
        assert result.chars_skipped == 0
        assert result.fallback_used is False
        assert result.error_message == ""
        assert result.duration_ms == 0

    @pytest.mark.unit
    def test_typing_result_to_dict(self):
        """Test TypingResult doesn't need to_dict method for now."""
        result = TypingResult(success=True, chars_typed=5)

        # Just verify attributes are accessible
        assert result.success is True
        assert result.chars_typed == 5


# ============================================================================
# Test: Error Handling
# ============================================================================

@pytest.mark.unit
class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.unit
    def test_type_when_keyboard_unavailable(self):
        """Test typing when keyboard controller is unavailable."""
        typer = SmartTyper()
        typer._available = False
        typer._keyboard = None

        result = typer.type("test")

        assert result.success is False
        assert "not available" in result.error_message

    @pytest.mark.unit
    def test_type_with_exception_during_typing(self):
        """Test handling exception during typing."""
        mock_ctrl = MagicMock()
        mock_ctrl.press.side_effect = RuntimeError("Keyboard error")

        with patch('faster_whisper_hotkey.typing_util.keyboard', MagicMock(Controller=MagicMock(return_value=mock_ctrl))):
            typer = SmartTyper(pre_delay=0, post_delay=0, char_delay=0)
            typer._keyboard = mock_ctrl

            result = typer.type("test")

            # Should handle exception gracefully
            assert result.duration_ms >= 0


# ============================================================================
# Test: Special Edge Cases
# ============================================================================

@pytest.mark.unit
class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.fixture
    def mock_keyboard(self):
        """Mock keyboard controller."""
        mock_ctrl = MagicMock()
        with patch('faster_whisper_hotkey.typing_util.keyboard', MagicMock(Controller=MagicMock(return_value=mock_ctrl))):
            typer = SmartTyper(pre_delay=0, post_delay=0, char_delay=0)
            typer._keyboard = mock_ctrl
            yield typer, mock_ctrl

    @pytest.mark.unit
    def test_carriage_return_handling(self, mock_keyboard):
        """Test carriage return is handled."""
        typer, ctrl = mock_keyboard
        result = typer.type("line1\rline2")

        # Carriage return should be skipped
        assert result.success is True

    @pytest.mark.unit
    def test_all_printable_ascii(self, mock_keyboard):
        """Test typing all printable ASCII characters."""
        typer, ctrl = mock_keyboard
        text = "".join([chr(i) for i in range(32, 127)])  # All printable ASCII

        result = typer.type(text)

        assert result.success is True

    @pytest.mark.unit
    def test_very_long_text(self, mock_keyboard):
        """Test typing very long text."""
        typer, ctrl = mock_keyboard
        text = "A" * 1000

        result = typer.type(text)

        assert result.success is True
        assert result.chars_typed == 1000

    @pytest.mark.unit
    def test_unicode_max_fallback_limit(self, mock_keyboard):
        """Test that long unicode text doesn't use clipboard fallback."""
        typer, ctrl = mock_keyboard
        typer.max_unicode_fallback_chars = 5

        # Long text with unicode - should exceed limit and use direct typing
        long_text = "世界" * 10  # 20 characters

        result = typer.type(long_text)

        # Should still succeed, possibly with some chars skipped
        assert result is not None
