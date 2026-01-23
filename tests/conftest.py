"""
Pytest configuration and shared fixtures for faster-whisper-hotkey tests.

This module provides common fixtures and test utilities used across
the test suite.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def temp_dir():
    """
    Create a temporary directory for test files.

    The directory is automatically cleaned up after the test.
    """
    temp_path = tempfile.mkdtemp(prefix="fwh_test_")
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_settings_file(temp_dir):
    """Create a temporary settings file."""
    return os.path.join(temp_dir, "test_settings.json")


@pytest.fixture
def temp_history_db(temp_dir):
    """Create a temporary history database file."""
    return os.path.join(temp_dir, "test_history.db")


@pytest.fixture
def mock_settings():
    """Create a mock Settings object with default values."""
    from faster_whisper_hotkey.settings import Settings

    return Settings(
        device_name="test_device",
        model_type="whisper",
        model_name="large-v3",
        compute_type="float16",
        device="cpu",
        language="en",
        hotkey="pause",
        history_hotkey="ctrl+shift+h",
        activation_mode="hold",
        history_max_items=50,
        privacy_mode=False,
        onboarding_completed=True,
        text_processing={},
        enable_streaming=False,
        auto_copy_on_release=True,
        confidence_threshold=0.5,
        stream_chunk_duration=3.0,
        voice_commands={},
        theme_mode="system",
        history_retention_days=30,
        history_confirm_clear=True,
        history_backup_enabled=False,
        update_check_frequency="weekly",
        update_include_prereleases=False,
        update_auto_download=False,
        telemetry_enabled=False,
    )


@pytest.fixture
def mock_transcriber():
    """Create a mock MicrophoneTranscriber."""
    mock = Mock()
    mock.is_recording = False
    mock.is_transcribing = False
    mock.current_audio_level = 0.0
    return mock


@pytest.fixture
def mock_whisper_model():
    """
    Mock WhisperModel to prevent actual model loading during tests.

    This fixture patches faster_whisper.WhisperModel to prevent
    actual model downloads and loading.
    """
    mock_model = MagicMock()

    # Mock the transcribe method
    mock_model.transcribe.return_value = iter([
        Mock(text="Test transcription", segments=[])
    ])

    # Create a mock WhisperModel class
    class MockWhisperModel:
        def __init__(self, *args, **kwargs):
            self.mock = mock_model

        def transcribe(self, *args, **kwargs):
            return mock_model.transcribe(*args, **kwargs)

    with patch('faster_whisper.WhisperModel', MockWhisperModel):
        yield mock_model


@pytest.fixture
def sample_history_items():
    """Create sample history items for testing."""
    from faster_whisper_hotkey.flet_gui.history_manager import HistoryItem

    return [
        HistoryItem(
            id=1,
            timestamp="2024-01-15T10:30:00",
            text="Meeting about project kickoff",
            model="large-v3",
            language="en",
            device="cpu",
            confidence=0.95,
            duration_ms=1500,
            tags=["meeting", "project"],
            edited=False,
        ),
        HistoryItem(
            id=2,
            timestamp="2024-01-15T14:00:00",
            text="Discussion regarding feature implementation",
            model="medium",
            language="en",
            device="cpu",
            confidence=0.88,
            duration_ms=2200,
            tags=["discussion", "feature"],
            edited=False,
        ),
        HistoryItem(
            id=3,
            timestamp="2024-01-16T09:00:00",
            text="Standup daily sync",
            model="small",
            language="en",
            device="cuda",
            confidence=0.92,
            duration_ms=800,
            tags=["standup"],
            edited=False,
        ),
    ]


@pytest.fixture
def disable_threading():
    """
    Disable actual threading in tests.

    This fixture patches threading to make tests deterministic
    by preventing actual thread creation.
    """
    with patch('threading.Thread') as mock_thread:
        # Make threads run immediately
        def instant_thread(target=None, args=(), kwargs=None, daemon=None):
            if target:
                if kwargs is None:
                    kwargs = {}
                target(*args, **kwargs)
            mock_instance = Mock()
            mock_instance.start = Mock()
            mock_instance.join = Mock()
            return mock_instance

        mock_thread.side_effect = instant_thread
        yield mock_thread


@pytest.fixture
def mock_audio_data():
    """Create mock audio data for transcription tests."""
    import numpy as np
    # Generate 1 second of silence at 16kHz
    return np.zeros(16000, dtype=np.float32)


@pytest.fixture
def mock_pynput():
    """Mock pynput keyboard to prevent actual keyboard hooking."""
    with patch('pynput.keyboard.Listener'):
        with patch('pynput.keyboard.Key'):
            with patch('pynput.keyboard.KeyCode'):
                yield


# Pytest markers configuration
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow-running tests")
    config.addinivalue_line("markers", "gpu: Tests requiring GPU")
    config.addinivalue_line("markers", "requires_network: Tests requiring network access")
    config.addinivalue_line("markers", "stress: Stress tests for stability and load testing")
    config.addinivalue_line("markers", "memory: Memory leak detection tests")
