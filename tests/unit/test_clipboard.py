"""
Unit tests for clipboard module.

This test module covers:
- Clipboard backup functionality
- Clipboard set functionality
- Clipboard restore functionality
- Error handling when pyperclip is unavailable
- Non-text clipboard content handling

Run with: pytest tests/unit/test_clipboard.py -v
"""

import pytest
from unittest.mock import patch, MagicMock, Mock

from faster_whisper_hotkey.clipboard import (
    backup_clipboard,
    set_clipboard,
    restore_clipboard,
)


# ============================================================================
# Test: With pyperclip Available
# ============================================================================

@pytest.mark.unit
class TestWithPyperclip:
    """Tests when pyperclip is available."""

    @pytest.fixture
    def mock_pyperclip(self):
        """Mock pyperclip module."""
        mock = MagicMock()
        mock.paste.return_value = "original content"
        sys_modules = {"pyperclip": mock}

        with patch.dict("sys.modules", sys_modules, clear=False):
            # Also patch the imported reference in clipboard module
            import faster_whisper_hotkey.clipboard as clipboard_module
            original_pyperclip = clipboard_module.pyperclip
            clipboard_module.pyperclip = mock

            yield mock

            clipboard_module.pyperclip = original_pyperclip


    @pytest.mark.unit
    def test_backup_clipboard_success(self, mock_pyperclip):
        """Test successful clipboard backup."""
        mock_pyperclip.paste.return_value = "test clipboard content"

        result = backup_clipboard()

        assert result == "test clipboard content"
        mock_pyperclip.paste.assert_called_once()


    @pytest.mark.unit
    def test_backup_clipboard_empty(self, mock_pyperclip):
        """Test backing up empty clipboard."""
        mock_pyperclip.paste.return_value = ""

        result = backup_clipboard()

        assert result == ""


    @pytest.mark.unit
    def test_backup_clipboard_unicode(self, mock_pyperclip):
        """Test backing up clipboard with Unicode content."""
        mock_pyperclip.paste.return_value = "Hello 世界 🌍"

        result = backup_clipboard()

        assert result == "Hello 世界 🌍"


    @pytest.mark.unit
    def test_backup_clipboard_exception(self, mock_pyperclip):
        """Test backup handles exceptions gracefully."""
        mock_pyperclip.paste.side_effect = Exception("Clipboard access denied")

        result = backup_clipboard()

        assert result is None


    @pytest.mark.unit
    def test_set_clipboard_success(self, mock_pyperclip):
        """Test successful clipboard set."""
        result = set_clipboard("new content")

        assert result is True
        mock_pyperclip.copy.assert_called_once_with("new content")


    @pytest.mark.unit
    def test_set_clipboard_unicode(self, mock_pyperclip):
        """Test setting clipboard with Unicode content."""
        result = set_clipboard("Hello 世界 🌍")

        assert result is True
        mock_pyperclip.copy.assert_called_once_with("Hello 世界 🌍")


    @pytest.mark.unit
    def test_set_clipboard_long_text(self, mock_pyperclip):
        """Test setting clipboard with long text."""
        long_text = "A" * 10000

        result = set_clipboard(long_text)

        assert result is True
        mock_pyperclip.copy.assert_called_once_with(long_text)


    @pytest.mark.unit
    def test_set_clipboard_exception(self, mock_pyperclip):
        """Test set handles exceptions gracefully."""
        mock_pyperclip.copy.side_effect = Exception("Clipboard access denied")

        result = set_clipboard("test content")

        assert result is False


    @pytest.mark.unit
    def test_restore_clipboard_success(self, mock_pyperclip):
        """Test successful clipboard restore."""
        result = restore_clipboard("restored content")

        # Should not raise
        mock_pyperclip.copy.assert_called_once_with("restored content")


    @pytest.mark.unit
    def test_restore_clipboard_none(self, mock_pyperclip):
        """Test restore with None does nothing."""
        restore_clipboard(None)

        mock_pyperclip.copy.assert_not_called()


    @pytest.mark.unit
    def test_restore_clipboard_empty_string(self, mock_pyperclip):
        """Test restore with empty string."""
        restore_clipboard("")

        mock_pyperclip.copy.assert_called_once_with("")


    @pytest.mark.unit
    def test_restore_clipboard_exception(self, mock_pyperclip):
        """Test restore handles exceptions gracefully."""
        mock_pyperclip.copy.side_effect = Exception("Restore failed")

        # Should not raise
        restore_clipboard("test content")


    @pytest.mark.unit
    def test_backup_set_restore_cycle(self, mock_pyperclip):
        """Test complete backup-set-restore cycle."""
        # Set original content
        mock_pyperclip.paste.return_value = "original"
        mock_pyperclip.copy.return_value = None

        # Backup
        backed_up = backup_clipboard()
        assert backed_up == "original"

        # Set new content
        result = set_clipboard("new content")
        assert result is True

        # Verify new content was set
        mock_pyperclip.copy.assert_called_with("new content")

        # Restore original
        restore_clipboard(backed_up)
        mock_pyperclip.copy.assert_called_with("original")


# ============================================================================
# Test: Without pyperclip
# ============================================================================

@pytest.mark.unit
class TestWithoutPyperclip:
    """Tests when pyperclip is not available."""

    @pytest.fixture
    def no_pyperclip(self):
        """Patch to simulate pyperclip not being available."""
        import faster_whisper_hotkey.clipboard as clipboard_module
        original_pyperclip = clipboard_module.pyperclip
        clipboard_module.pyperclip = None

        yield

        clipboard_module.pyperclip = original_pyperclip


    @pytest.mark.unit
    def test_backup_clipboard_no_pyperclip(self, no_pyperclip):
        """Test backup returns None when pyperclip unavailable."""
        result = backup_clipboard()

        assert result is None


    @pytest.mark.unit
    def test_set_clipboard_no_pyperclip(self, no_pyperclip):
        """Test set returns False when pyperclip unavailable."""
        result = set_clipboard("test content")

        assert result is False


    @pytest.mark.unit
    def test_restore_clipboard_no_pyperclip(self, no_pyperclip):
        """Test restore does nothing when pyperclip unavailable."""
        # Should not raise
        restore_clipboard("test content")


# ============================================================================
# Test: Special Cases
# ============================================================================

@pytest.mark.unit
class TestSpecialCases:
    """Tests for special clipboard scenarios."""

    @pytest.fixture
    def mock_pyperclip(self):
        """Mock pyperclip module."""
        mock = MagicMock()

        with patch.dict("sys.modules", {"pyperclip": mock}, clear=False):
            import faster_whisper_hotkey.clipboard as clipboard_module
            original_pyperclip = clipboard_module.pyperclip
            clipboard_module.pyperclip = mock

            yield mock

            clipboard_module.pyperclip = original_pyperclip


    @pytest.mark.unit
    def test_clipboard_with_newlines(self, mock_pyperclip):
        """Test clipboard content with newlines."""
        test_text = "Line 1\nLine 2\r\nLine 3\rLine 4"

        result = set_clipboard(test_text)

        assert result is True
        mock_pyperclip.copy.assert_called_once_with(test_text)


    @pytest.mark.unit
    def test_clipboard_with_tabs(self, mock_pyperclip):
        """Test clipboard content with tabs."""
        test_text = "Column 1\tColumn 2\tColumn 3"

        result = set_clipboard(test_text)

        assert result is True
        mock_pyperclip.copy.assert_called_once_with(test_text)


    @pytest.mark.unit
    def test_clipboard_with_special_characters(self, mock_pyperclip):
        """Test clipboard content with special characters."""
        test_text = "Special: <>\"'&\t\n\r"

        result = set_clipboard(test_text)

        assert result is True
        mock_pyperclip.copy.assert_called_once_with(test_text)


    @pytest.mark.unit
    def test_clipboard_with_emoji(self, mock_pyperclip):
        """Test clipboard content with emoji."""
        test_text = "Emoji test: 😀🎉❤️🚀⭐"

        result = set_clipboard(test_text)

        assert result is True
        mock_pyperclip.copy.assert_called_once_with(test_text)


    @pytest.mark.unit
    def test_clipboard_zero_width_characters(self, mock_pyperclip):
        """Test clipboard content with zero-width characters."""
        test_text = "Test\u200B\u200C\u200DContent"

        result = set_clipboard(test_text)

        assert result is True
        mock_pyperclip.copy.assert_called_once_with(test_text)


    @pytest.mark.unit
    def test_clipboard_very_long_content(self, mock_pyperclip):
        """Test clipboard with very long content (1MB)."""
        # Create 1MB of text
        test_text = "A" * (1024 * 1024)

        result = set_clipboard(test_text)

        assert result is True
        mock_pyperclip.copy.assert_called_once()


    @pytest.mark.unit
    def test_backup_after_set(self, mock_pyperclip):
        """Test that backup reflects set content."""
        mock_pyperclip.paste.return_value = "initial"

        backup_clipboard()

        mock_pyperclip.paste.return_value = "new content"
        set_clipboard("new content")

        mock_pyperclip.paste.return_value = "new content"
        backed_up = backup_clipboard()

        assert backed_up == "new content"


    @pytest.mark.unit
    def test_multiple_backups(self, mock_pyperclip):
        """Test multiple sequential backups."""
        contents = ["first", "second", "third"]

        for content in contents:
            mock_pyperclip.paste.return_value = content
            result = backup_clipboard()
            assert result == content


    @pytest.mark.unit
    def test_restore_to_different_content(self, mock_pyperclip):
        """Test restore changes clipboard content."""
        # Current clipboard has "current"
        mock_pyperclip.paste.return_value = "current"

        # Restore should set it to "restored"
        restore_clipboard("restored")

        mock_pyperclip.copy.assert_called_once_with("restored")


# ============================================================================
# Test: Non-Text Clipboard Content
# ============================================================================

@pytest.mark.unit
class TestNonTextContent:
    """Tests for non-text clipboard content handling."""

    @pytest.fixture
    def mock_pyperclip(self):
        """Mock pyperclip module."""
        mock = MagicMock()

        with patch.dict("sys.modules", {"pyperclip": mock}, clear=False):
            import faster_whisper_hotkey.clipboard as clipboard_module
            original_pyperclip = clipboard_module.pyperclip
            clipboard_module.pyperclip = mock

            yield mock

            clipboard_module.pyperclip = original_pyperclip


    @pytest.mark.unit
    def test_backup_with_non_text_content(self, mock_pyperclip):
        """Test backup when clipboard has non-text content."""
        # Simulate pyperclip returning non-string or error for non-text
        mock_pyperclip.paste.side_effect = Exception("Non-text content")

        result = backup_clipboard()

        # Should handle gracefully
        assert result is None


    @pytest.mark.unit
    def test_restore_over_non_text_content(self, mock_pyperclip):
        """Test restore overwrites non-text content."""
        # Even if current content is non-text, restore should work
        restore_clipboard("text to restore")

        mock_pyperclip.copy.assert_called_once_with("text to restore")


# ============================================================================
# Test: Thread Safety
# ============================================================================

@pytest.mark.unit
class TestThreadSafety:
    """Tests for thread-safe clipboard operations."""

    @pytest.fixture
    def mock_pyperclip(self):
        """Mock pyperclip module."""
        mock = MagicMock()

        with patch.dict("sys.modules", {"pyperclip": mock}, clear=False):
            import faster_whisper_hotkey.clipboard as clipboard_module
            original_pyperclip = clipboard_module.pyperclip
            clipboard_module.pyperclip = mock

            yield mock

            clipboard_module.pyperclip = original_pyperclip


    @pytest.mark.unit
    def test_concurrent_backups(self, mock_pyperclip):
        """Test multiple threads can backup clipboard."""
        import threading

        results = []
        lock = threading.Lock()

        def backup_thread(i):
            mock_pyperclip.paste.return_value = f"content {i}"
            result = backup_clipboard()
            with lock:
                results.append(result)

        threads = [threading.Thread(target=backup_thread, args=(i,)) for i in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 10


    @pytest.mark.unit
    def test_concurrent_sets(self, mock_pyperclip):
        """Test multiple threads can set clipboard."""
        import threading

        results = {"success": 0, "failure": 0}
        lock = threading.Lock()

        def set_thread(i):
            result = set_clipboard(f"content {i}")
            with lock:
                if result:
                    results["success"] += 1
                else:
                    results["failure"] += 1

        threads = [threading.Thread(target=set_thread, args=(i,)) for i in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert results["success"] == 10


# ============================================================================
# Test: Edge Cases
# ============================================================================

@pytest.mark.unit
class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.fixture
    def mock_pyperclip(self):
        """Mock pyperclip module."""
        mock = MagicMock()

        with patch.dict("sys.modules", {"pyperclip": mock}, clear=False):
            import faster_whisper_hotkey.clipboard as clipboard_module
            original_pyperclip = clipboard_module.pyperclip
            clipboard_module.pyperclip = mock

            yield mock

            clipboard_module.pyperclip = original_pyperclip


    @pytest.mark.unit
    def test_clipboard_with_only_whitespace(self, mock_pyperclip):
        """Test clipboard with only whitespace."""
        test_cases = [" ", "\t", "\n", "\r\n", "   \t\n  "]

        for test_text in test_cases:
            result = set_clipboard(test_text)
            assert result is True


    @pytest.mark.unit
    def test_clipboard_with_null_byte(self, mock_pyperclip):
        """Test clipboard with null byte."""
        # Null bytes might be problematic, but we should handle them
        test_text = "before\x00after"

        result = set_clipboard(test_text)

        # Should attempt to set
        mock_pyperclip.copy.assert_called_once_with(test_text)


    @pytest.mark.unit
    def test_restore_with_very_long_content(self, mock_pyperclip):
        """Test restore with very long content."""
        long_content = "A" * (10 * 1024 * 1024)  # 10MB

        restore_clipboard(long_content)

        mock_pyperclip.copy.assert_called_once_with(long_content)


    @pytest.mark.unit
    def test_backup_set_restore_unicode_roundtrip(self, mock_pyperclip):
        """Test Unicode content survives backup-set-restore cycle."""
        original = "Test 你好 🎉 Привет مرحبا"

        # Backup original (simulated)
        mock_pyperclip.paste.return_value = original

        backed_up = backup_clipboard()
        assert backed_up == original

        # Set new content
        set_clipboard("temporary")
        mock_pyperclip.copy.assert_called_with("temporary")

        # Restore original
        restore_clipboard(backed_up)
        mock_pyperclip.copy.assert_called_with(original)
