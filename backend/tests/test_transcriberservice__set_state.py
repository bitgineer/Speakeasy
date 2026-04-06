"""
Test for TranscriberService._set_state
Comprehensive test suite for state management.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.core.transcriber import TranscriberService, TranscriberState


class TestTranscriberServiceSetState:
    """Tests for TranscriberService._set_state"""

    def test_set_state_updates_internal_state(self):
        """Test that _set_state updates the internal state."""
        service = TranscriberService()

        service._set_state(TranscriberState.RECORDING)

        assert service._state == TranscriberState.RECORDING

    def test_set_state_calls_callback(self):
        """Test that _set_state calls the state change callback."""
        callback = Mock()
        service = TranscriberService(on_state_change=callback)

        service._set_state(TranscriberState.RECORDING)

        callback.assert_called_once_with(TranscriberState.RECORDING)

    def test_set_state_no_callback(self):
        """Test that _set_state works without a callback."""
        service = TranscriberService()  # No callback

        # Should not raise
        service._set_state(TranscriberState.RECORDING)
        assert service._state == TranscriberState.RECORDING

    def test_set_state_callback_error_handling(self):
        """Test that _set_state handles callback errors gracefully."""
        callback = Mock(side_effect=Exception("Callback error"))
        service = TranscriberService(on_state_change=callback)

        # Should not raise even if callback fails
        service._set_state(TranscriberState.RECORDING)
        assert service._state == TranscriberState.RECORDING

    def test_set_state_all_states(self):
        """Test setting all possible states."""
        service = TranscriberService()

        states = [
            TranscriberState.IDLE,
            TranscriberState.LOADING,
            TranscriberState.READY,
            TranscriberState.RECORDING,
            TranscriberState.TRANSCRIBING,
            TranscriberState.ERROR,
        ]

        for state in states:
            service._set_state(state)
            assert service._state == state


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
