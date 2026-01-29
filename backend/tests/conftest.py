"""
Shared pytest fixtures for SpeakEasy backend tests.
"""

import asyncio
import shutil
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def clean_tmp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory that is cleaned up after the test."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="speakeasy_test_"))
    yield tmp_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture
def test_settings(clean_tmp_dir: Path) -> dict:
    """Provide test settings with temporary file paths."""
    return {
        "model_size": "tiny",
        "language": "en",
        "device": "cpu",
        "compute_type": "int8",
        "input_device_id": None,
        "push_to_talk_key": "ctrl+shift+space",
        "auto_paste": False,
        "auto_copy": True,
        "output_format": "text",
        "settings_path": str(clean_tmp_dir / "settings.json"),
        "history_db_path": str(clean_tmp_dir / "history.db"),
    }


@pytest.fixture
def mock_audio() -> np.ndarray:
    """Provide sample audio data for transcription tests."""
    # 1 second of random audio at 16kHz sample rate
    return np.random.randn(16000).astype(np.float32)


@pytest.fixture
def mock_transcription_result():
    """Mock transcription result matching the expected format."""
    return MagicMock(
        text="Hello, this is a test transcription.",
        language="en",
        duration=1.0,
        segments=[
            MagicMock(
                text="Hello, this is a test transcription.",
                start=0.0,
                end=1.0,
                confidence=0.95,
            )
        ],
    )


@pytest.fixture
def mock_model(mock_transcription_result):
    """Mock ModelWrapper that doesn't load actual models."""
    mock = MagicMock()
    mock.transcribe = MagicMock(return_value=mock_transcription_result)
    mock.transcribe_async = AsyncMock(return_value=mock_transcription_result)
    mock.is_loaded = True
    mock.model_size = "tiny"
    mock.device = "cpu"
    mock.compute_type = "int8"
    return mock


@pytest.fixture
def mock_transcriber(mock_model):
    """Mock transcriber service."""
    mock = MagicMock()
    mock.model = mock_model
    mock.is_recording = False
    mock.start_recording = AsyncMock()
    mock.stop_recording = AsyncMock(return_value="Test transcription")
    mock.cancel_recording = AsyncMock()
    mock.get_model_info = MagicMock(
        return_value={
            "model_size": "tiny",
            "device": "cpu",
            "compute_type": "int8",
            "is_loaded": True,
        }
    )
    return mock


@pytest.fixture
def mock_settings_service(test_settings):
    """Mock settings service."""
    mock = MagicMock()
    mock.get_settings = MagicMock(return_value=test_settings)
    mock.update_settings = AsyncMock(return_value=test_settings)
    mock.reset_settings = AsyncMock(return_value=test_settings)
    return mock


@pytest.fixture
def mock_history_service():
    """Mock history service."""
    mock = MagicMock()
    mock.get_entries = AsyncMock(return_value=[])
    mock.add_entry = AsyncMock(
        return_value={"id": 1, "text": "Test", "timestamp": "2024-01-01T00:00:00"}
    )
    mock.delete_entry = AsyncMock(return_value=True)
    mock.clear_history = AsyncMock()
    return mock


@pytest.fixture
def app_with_mocks(mock_transcriber, mock_settings_service, mock_history_service):
    """Create FastAPI app with mocked services."""
    # Patch services before importing app
    with (
        patch("speakeasy.server.transcriber", mock_transcriber),
        patch("speakeasy.server.settings_service", mock_settings_service),
        patch("speakeasy.server.history", mock_history_service),
    ):
        from speakeasy.server import app

        yield app


@pytest.fixture
def client(app_with_mocks) -> Generator[TestClient, None, None]:
    """Provide a synchronous test client for API endpoint testing."""
    with TestClient(app_with_mocks) as c:
        yield c


@pytest.fixture
async def async_client(app_with_mocks) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async test client for async endpoint testing."""
    transport = ASGITransport(app=app_with_mocks)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_history_db(clean_tmp_dir: Path) -> Path:
    """Provide a temporary SQLite database path for history tests."""
    return clean_tmp_dir / "test_history.db"
