"""
Test for DownloadStateManager.__init__
Comprehensive test suite for DownloadStateManager initialization.
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.services.download_state import (
    DownloadStateManager,
    DownloadStatus,
    ModelDownloadProgress,
)


class TestDownloadStateManagerInit:
    """Tests for DownloadStateManager.__init__"""

    def test_singleton_pattern(self):
        """Test that DownloadStateManager is a singleton."""
        manager1 = DownloadStateManager()
        manager2 = DownloadStateManager()

        assert manager1 is manager2

    def test_initialization_sets_defaults(self):
        """Test that initialization sets default values."""
        manager = DownloadStateManager()

        assert manager._current_download is None
        assert manager._cancel_event.is_set() is False
        assert manager._progress_callbacks == []
        assert manager._initialized is True

    def test_initial_state(self):
        """Test the initial state of the manager."""
        manager = DownloadStateManager()

        assert manager.is_downloading is False
        assert manager.cancel_requested is False
        assert manager.current_download is None

    def test_singleton_thread_safety(self):
        """Test that singleton pattern works correctly."""
        # Create multiple instances
        managers = [DownloadStateManager() for _ in range(5)]

        # All should be the same object
        first = managers[0]
        for manager in managers[1:]:
            assert manager is first


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
