"""
Test for TranscriberService.__init__
Comprehensive test suite for TranscriberService initialization.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.core.transcriber import TranscriberService, TranscriberState


class TestTranscriberServiceInit:
    """Tests for TranscriberService.__init__"""

    def test_basic_initialization(self):
        """Test basic initialization without callback."""
        service = TranscriberService()

        assert service._state == TranscriberState.IDLE
        assert service._model is None
        assert service._audio_buffer == []
        assert service._stream is None
        assert service._on_state_change is None

    def test_initialization_with_callback(self):
        """Test initialization with state change callback."""
        callback = Mock()
        service = TranscriberService(on_state_change=callback)

        assert service._on_state_change is callback

    def test_initialization_sets_default_device(self):
        """Test that initialization sets default device to None."""
        service = TranscriberService()

        assert service._device_name is None
        assert service._device_id is None

    def test_state_property_initial(self):
        """Test that state property returns initial state."""
        service = TranscriberService()

        assert service.state == TranscriberState.IDLE

    def test_is_model_loaded_initial(self):
        """Test is_model_loaded returns False initially."""
        service = TranscriberService()

        assert service.is_model_loaded is False

    def test_is_recording_initial(self):
        """Test is_recording returns False initially."""
        service = TranscriberService()

        assert service.is_recording is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
