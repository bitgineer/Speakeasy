"""
Test for TranscriberService.start_recording
Comprehensive test suite covering happy path, error handling, and edge cases.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.core.transcriber import TranscriberService, TranscriberState


class TestTranscriberStartRecording:
    """Tests for TranscriberService.start_recording"""

    @pytest.fixture
    def service(self):
        """Create a TranscriberService with no callback."""
        return TranscriberService(on_state_change=None)

    @pytest.fixture
    def service_with_loaded_model(self):
        """Create a TranscriberService with a loaded model."""
        service = TranscriberService(on_state_change=None)
        mock_model = Mock()
        mock_model.is_loaded = True
        service._model = mock_model
        service._state = TranscriberState.READY
        return service

    def test_start_recording_success(self, service_with_loaded_model):
        """Test successful recording start with loaded model."""
        service = service_with_loaded_model

        with patch("speakeasy.core.transcriber.sd") as mock_sd:
            mock_device_info = {
                "name": "Test Device",
                "max_input_channels": 2,
                "default_samplerate": 16000,
                "hostapi": 0,
            }
            mock_sd.query_devices.return_value = [mock_device_info]
            mock_sd.query_devices.return_value = mock_device_info
            mock_sd.default.device = [0, 0]

            mock_stream = Mock()
            mock_sd.InputStream.return_value = mock_stream

            service.start_recording()

            assert service.state == TranscriberState.RECORDING
            mock_stream.start.assert_called_once()

    def test_start_recording_no_model_raises_error(self, service):
        """Test that starting recording without a model raises RuntimeError."""
        with pytest.raises(RuntimeError, match="No model loaded"):
            service.start_recording()

    def test_start_recording_already_recording_warns(self, service_with_loaded_model):
        """Test that starting recording when already recording logs a warning."""
        service = service_with_loaded_model
        service._state = TranscriberState.RECORDING

        with patch("speakeasy.core.transcriber.logger") as mock_logger:
            service.start_recording()

            mock_logger.warning.assert_called_with("Already recording")

    def test_start_recording_state_transition(self, service_with_loaded_model):
        """Test that recording start transitions through proper states."""
        service = service_with_loaded_model
        states_recorded = []

        def state_callback(state):
            states_recorded.append(state)

        service._on_state_change = state_callback

        with patch("speakeasy.core.transcriber.sd") as mock_sd:
            mock_device_info = {
                "name": "Test Device",
                "max_input_channels": 2,
                "default_samplerate": 16000,
                "hostapi": 0,
            }
            mock_sd.query_devices.return_value = mock_device_info
            mock_sd.default.device = [0, 0]
            mock_hostapis = [{"name": "MME"}]
            mock_sd.query_hostapis.return_value = mock_hostapis

            mock_stream = Mock()
            mock_sd.InputStream.return_value = mock_stream

            service.start_recording()

            assert TranscriberState.RECORDING in states_recorded

    def test_start_recording_creates_stream_with_correct_params(self, service_with_loaded_model):
        """Test that audio stream is created with correct parameters."""
        service = service_with_loaded_model

        with patch("speakeasy.core.transcriber.sd") as mock_sd:
            mock_device_info = {
                "name": "Test Device",
                "max_input_channels": 2,
                "default_samplerate": 16000.0,
                "hostapi": 0,
            }
            mock_sd.query_devices.return_value = mock_device_info
            mock_sd.default.device = [0, 0]
            mock_sd.query_hostapis.return_value = [{"name": "MME"}]

            mock_stream = Mock()
            mock_sd.InputStream.return_value = mock_stream

            service.start_recording()

            # Verify InputStream was created with expected parameters
            call_kwargs = mock_sd.InputStream.call_args.kwargs
            assert "samplerate" in call_kwargs
            assert "channels" in call_kwargs
            assert "dtype" in call_kwargs
            assert call_kwargs["dtype"] == np.float32

    def test_start_recording_with_custom_device(self, service_with_loaded_model):
        """Test recording start with a custom audio device."""
        service = service_with_loaded_model
        service._device_name = "Custom Mic"
        service._device_id = 1

        with patch("speakeasy.core.transcriber.sd") as mock_sd:
            mock_device_info = {
                "name": "Custom Mic",
                "max_input_channels": 2,
                "default_samplerate": 44100.0,
                "hostapi": 0,
            }
            mock_sd.query_devices.return_value = [mock_device_info, mock_device_info]
            mock_sd.query_devices.return_value = mock_device_info
            mock_sd.default.device = [0, 0]
            mock_sd.query_hostapis.return_value = [{"name": "MME"}]

            mock_stream = Mock()
            mock_sd.InputStream.return_value = mock_stream

            service.start_recording()

            assert service._recording_samplerate == 44100

    def test_start_recording_handles_device_query_failure(self, service_with_loaded_model):
        """Test that device query failure is handled gracefully."""
        service = service_with_loaded_model

        with patch("speakeasy.core.transcriber.sd") as mock_sd:
            mock_sd.query_devices.side_effect = Exception("Device query failed")

            with patch("speakeasy.core.transcriber.logger") as mock_logger:
                mock_stream = Mock()
                mock_sd.InputStream.return_value = mock_stream

                service.start_recording()

                # Should log warning and use fallback
                mock_logger.warning.assert_called()
                assert service._recording_samplerate == 16000

    def test_start_recording_falls_back_to_default_device(self, service_with_loaded_model):
        """Test fallback to default device when selected device has no input."""
        service = service_with_loaded_model
        service._device_id = 5  # Non-existent device

        with patch("speakeasy.core.transcriber.sd") as mock_sd:
            # Device at index 5 has no input channels
            mock_devices = [
                {"name": "Default Device", "max_input_channels": 2, "default_samplerate": 16000.0},
            ]
            mock_sd.query_devices.return_value = mock_devices
            mock_sd.query_devices.return_value = {
                "name": "Default Device",
                "max_input_channels": 2,
                "default_samplerate": 16000.0,
                "hostapi": 0,
            }
            mock_sd.default.device = [0, 0]
            mock_sd.query_hostapis.return_value = [{"name": "MME"}]

            mock_stream = Mock()
            mock_sd.InputStream.return_value = mock_stream

            service.start_recording()

            # Should fall back to default device
            assert service._device_id == 0

    def test_start_recording_stream_creation_failure(self, service_with_loaded_model):
        """Test error handling when stream creation fails."""
        service = service_with_loaded_model

        with patch("speakeasy.core.transcriber.sd") as mock_sd:
            mock_device_info = {
                "name": "Test Device",
                "max_input_channels": 2,
                "default_samplerate": 16000.0,
                "hostapi": 0,
            }
            mock_sd.query_devices.return_value = mock_device_info
            mock_sd.default.device = [0, 0]
            mock_sd.query_hostapis.return_value = [{"name": "MME"}]

            mock_sd.InputStream.side_effect = Exception("Stream creation failed")

            with pytest.raises(Exception):
                service.start_recording()

            # State should be reset on failure
            assert service.state in [TranscriberState.IDLE, TranscriberState.READY]

    def test_start_recording_initializes_buffer(self, service_with_loaded_model):
        """Test that audio buffer is initialized on recording start."""
        service = service_with_loaded_model

        with patch("speakeasy.core.transcriber.sd") as mock_sd:
            mock_device_info = {
                "name": "Test Device",
                "max_input_channels": 2,
                "default_samplerate": 16000.0,
                "hostapi": 0,
            }
            mock_sd.query_devices.return_value = mock_device_info
            mock_sd.default.device = [0, 0]
            mock_sd.query_hostapis.return_value = [{"name": "MME"}]

            mock_stream = Mock()
            mock_sd.InputStream.return_value = mock_stream

            service._audio_buffer = [np.array([1.0, 2.0, 3.0])]

            service.start_recording()

            # Buffer should be cleared
            assert service._audio_buffer == []

    def test_start_recording_sets_start_time(self, service_with_loaded_model):
        """Test that recording start time is set."""
        service = service_with_loaded_model

        with patch("speakeasy.core.transcriber.sd") as mock_sd:
            mock_device_info = {
                "name": "Test Device",
                "max_input_channels": 2,
                "default_samplerate": 16000.0,
                "hostapi": 0,
            }
            mock_sd.query_devices.return_value = mock_device_info
            mock_sd.default.device = [0, 0]
            mock_sd.query_hostapis.return_value = [{"name": "MME"}]

            mock_stream = Mock()
            mock_sd.InputStream.return_value = mock_stream

            with patch("time.time") as mock_time:
                mock_time.return_value = 12345.0

                service.start_recording()

                assert service._recording_start_time == 12345.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
