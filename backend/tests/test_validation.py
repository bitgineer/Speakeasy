"""
Tests for Pydantic schema validation edge cases.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError


class TestTranscribeStopRequestValidation:
    """Test TranscribeStopRequest schema validation."""

    def test_transcribe_stop_defaults(self):
        """Default values are applied correctly."""
        from speakeasy.server import TranscribeStopRequest

        request = TranscribeStopRequest()
        assert request.auto_paste is True
        assert request.language is None

    def test_transcribe_stop_with_values(self):
        """Explicit values are accepted."""
        from speakeasy.server import TranscribeStopRequest

        request = TranscribeStopRequest(auto_paste=False, language="en")
        assert request.auto_paste is False
        assert request.language == "en"

    def test_transcribe_stop_language_max_length_valid(self):
        """Language within max_length is accepted."""
        from speakeasy.server import TranscribeStopRequest

        request = TranscribeStopRequest(language="en")  # 2 chars, under 10
        assert request.language == "en"

    def test_transcribe_stop_language_max_length_boundary(self):
        """Language at exactly max_length is accepted."""
        from speakeasy.server import TranscribeStopRequest

        request = TranscribeStopRequest(language="a" * 10)  # Exactly 10
        assert len(request.language) == 10

    def test_transcribe_stop_language_max_length_exceeded(self):
        """Language exceeding max_length is rejected."""
        from speakeasy.server import TranscribeStopRequest

        with pytest.raises(ValidationError):
            TranscribeStopRequest(language="a" * 11)


class TestSettingsUpdateRequestValidation:
    """Test SettingsUpdateRequest schema validation."""

    def test_settings_all_optional(self):
        """Empty request is valid (all fields optional)."""
        from speakeasy.server import SettingsUpdateRequest

        request = SettingsUpdateRequest()
        assert request.model_type is None
        assert request.model_name is None

    def test_settings_model_type_max_length_valid(self):
        """model_type within limit is accepted."""
        from speakeasy.server import SettingsUpdateRequest

        request = SettingsUpdateRequest(model_type="whisper")
        assert request.model_type == "whisper"

    def test_settings_model_type_max_length_exceeded(self):
        """model_type exceeding 50 chars is rejected."""
        from speakeasy.server import SettingsUpdateRequest

        with pytest.raises(ValidationError):
            SettingsUpdateRequest(model_type="a" * 51)

    def test_settings_model_name_max_length_valid(self):
        """model_name within limit is accepted."""
        from speakeasy.server import SettingsUpdateRequest

        request = SettingsUpdateRequest(model_name="openai/whisper-large-v3")
        assert request.model_name == "openai/whisper-large-v3"

    def test_settings_model_name_max_length_exceeded(self):
        """model_name exceeding 200 chars is rejected."""
        from speakeasy.server import SettingsUpdateRequest

        with pytest.raises(ValidationError):
            SettingsUpdateRequest(model_name="a" * 201)

    def test_settings_device_pattern_cuda_valid(self):
        """device='cuda' is accepted."""
        from speakeasy.server import SettingsUpdateRequest

        request = SettingsUpdateRequest(device="cuda")
        assert request.device == "cuda"

    def test_settings_device_pattern_cpu_valid(self):
        """device='cpu' is accepted."""
        from speakeasy.server import SettingsUpdateRequest

        request = SettingsUpdateRequest(device="cpu")
        assert request.device == "cpu"

    def test_settings_device_pattern_invalid(self):
        """device with invalid value is rejected."""
        from speakeasy.server import SettingsUpdateRequest

        with pytest.raises(ValidationError):
            SettingsUpdateRequest(device="gpu")

    def test_settings_device_pattern_invalid_cuda0(self):
        """device='cuda:0' is rejected (must be exactly 'cuda')."""
        from speakeasy.server import SettingsUpdateRequest

        with pytest.raises(ValidationError):
            SettingsUpdateRequest(device="cuda:0")

    def test_settings_hotkey_valid_simple(self):
        """Simple hotkey is accepted."""
        from speakeasy.server import SettingsUpdateRequest

        request = SettingsUpdateRequest(hotkey="ctrl+shift+a")
        assert request.hotkey == "ctrl+shift+a"

    def test_settings_hotkey_valid_alphanumeric(self):
        """Alphanumeric hotkey is accepted."""
        from speakeasy.server import SettingsUpdateRequest

        request = SettingsUpdateRequest(hotkey="F12")
        assert request.hotkey == "F12"

    def test_settings_hotkey_invalid_chars(self):
        """Hotkey with invalid chars (dash) is rejected."""
        from speakeasy.server import SettingsUpdateRequest

        with pytest.raises(ValidationError):
            SettingsUpdateRequest(hotkey="ctrl-shift-a")  # Dashes not allowed

    def test_settings_hotkey_invalid_spaces(self):
        """Hotkey with spaces is rejected."""
        from speakeasy.server import SettingsUpdateRequest

        with pytest.raises(ValidationError):
            SettingsUpdateRequest(hotkey="ctrl shift a")

    def test_settings_hotkey_max_length_exceeded(self):
        """Hotkey exceeding 50 chars is rejected."""
        from speakeasy.server import SettingsUpdateRequest

        with pytest.raises(ValidationError):
            SettingsUpdateRequest(hotkey="a" * 51)


class TestModelLoadRequestValidation:
    """Test ModelLoadRequest schema validation."""

    def test_model_load_required_fields(self):
        """model_type and model_name are required."""
        from speakeasy.server import ModelLoadRequest

        with pytest.raises(ValidationError):
            ModelLoadRequest()  # Missing required fields

    def test_model_load_with_required_only(self):
        """Request with only required fields is valid."""
        from speakeasy.server import ModelLoadRequest

        request = ModelLoadRequest(model_type="whisper", model_name="tiny")
        assert request.model_type == "whisper"
        assert request.model_name == "tiny"
        assert request.device == "cuda"  # Default

    def test_model_load_device_default(self):
        """device defaults to 'cuda'."""
        from speakeasy.server import ModelLoadRequest

        request = ModelLoadRequest(model_type="whisper", model_name="tiny")
        assert request.device == "cuda"

    def test_model_load_device_cpu(self):
        """device='cpu' is accepted."""
        from speakeasy.server import ModelLoadRequest

        request = ModelLoadRequest(model_type="whisper", model_name="tiny", device="cpu")
        assert request.device == "cpu"

    def test_model_load_device_pattern_invalid(self):
        """Invalid device value is rejected."""
        from speakeasy.server import ModelLoadRequest

        with pytest.raises(ValidationError):
            ModelLoadRequest(model_type="whisper", model_name="tiny", device="mps")


class TestAppSettingsValidation:
    """Test AppSettings schema validation."""

    def test_app_settings_defaults(self):
        """All default values are correct."""
        from speakeasy.services.settings import AppSettings

        settings = AppSettings()

        assert settings.model_type == "parakeet"
        assert settings.model_name == "nvidia/parakeet-tdt-0.6b-v3"
        assert settings.compute_type == "float16"
        assert settings.device == "cuda"
        assert settings.language == "auto"
        assert settings.device_name is None
        assert settings.hotkey == "ctrl+shift+space"
        assert settings.hotkey_mode == "toggle"
        assert settings.auto_paste is True
        assert settings.show_recording_indicator is True
        assert settings.server_port == 8765

    def test_app_settings_model_dump(self):
        """model_dump() serializes correctly."""
        from speakeasy.services.settings import AppSettings

        settings = AppSettings()
        data = settings.model_dump()

        assert isinstance(data, dict)
        assert data["model_type"] == "parakeet"
        assert data["auto_paste"] is True

    def test_app_settings_custom_values(self):
        """Custom values are accepted."""
        from speakeasy.services.settings import AppSettings

        settings = AppSettings(
            model_type="whisper",
            model_name="openai/whisper-small",
            device="cpu",
            auto_paste=False,
        )

        assert settings.model_type == "whisper"
        assert settings.model_name == "openai/whisper-small"
        assert settings.device == "cpu"
        assert settings.auto_paste is False


class TestTranscriptionRecordValidation:
    """Test TranscriptionRecord serialization."""

    def test_transcription_record_to_dict(self):
        """to_dict() serializes datetime to ISO format."""
        from speakeasy.services.history import TranscriptionRecord

        now = datetime.utcnow()
        record = TranscriptionRecord(
            id="test-id",
            text="Test transcription",
            duration_ms=1500,
            model_used="whisper-small",
            language="en",
            created_at=now,
        )

        data = record.to_dict()

        assert data["id"] == "test-id"
        assert data["text"] == "Test transcription"
        assert data["duration_ms"] == 1500
        assert data["model_used"] == "whisper-small"
        assert data["language"] == "en"
        assert isinstance(data["created_at"], str)
        assert "T" in data["created_at"]  # ISO format

    def test_transcription_record_fields(self):
        """All fields are accessible."""
        from speakeasy.services.history import TranscriptionRecord

        record = TranscriptionRecord(
            id="id-123",
            text="Hello world",
            duration_ms=1000,
            model_used="test-model",
            language="en",
            created_at=datetime.utcnow(),
        )

        assert record.id == "id-123"
        assert record.text == "Hello world"
        assert record.duration_ms == 1000
        assert record.model_used == "test-model"
        assert record.language == "en"
        assert isinstance(record.created_at, datetime)


class TestModelDownloadProgressValidation:
    """Test ModelDownloadProgress computed properties."""

    def test_download_progress_progress_percent_zero(self):
        """progress_percent is 0 when total_bytes is 0."""
        from speakeasy.services.download_state import ModelDownloadProgress, DownloadStatus

        progress = ModelDownloadProgress(
            download_id="test",
            model_name="test-model",
            model_type="whisper",
            downloaded_bytes=0,
            total_bytes=0,
            status=DownloadStatus.DOWNLOADING,
        )

        assert progress.progress_percent == 0.0

    def test_download_progress_progress_percent_half(self):
        """progress_percent calculates correctly."""
        from speakeasy.services.download_state import ModelDownloadProgress, DownloadStatus

        progress = ModelDownloadProgress(
            download_id="test",
            model_name="test-model",
            model_type="whisper",
            downloaded_bytes=500,
            total_bytes=1000,
            status=DownloadStatus.DOWNLOADING,
        )

        assert progress.progress_percent == 50.0

    def test_download_progress_is_active_downloading(self):
        """is_active is True when DOWNLOADING."""
        from speakeasy.services.download_state import ModelDownloadProgress, DownloadStatus

        progress = ModelDownloadProgress(
            download_id="test",
            model_name="test-model",
            model_type="whisper",
            downloaded_bytes=100,
            total_bytes=1000,
            status=DownloadStatus.DOWNLOADING,
        )

        assert progress.is_active is True

    def test_download_progress_is_active_pending(self):
        """is_active is True when PENDING."""
        from speakeasy.services.download_state import ModelDownloadProgress, DownloadStatus

        progress = ModelDownloadProgress(
            download_id="test",
            model_name="test-model",
            model_type="whisper",
            downloaded_bytes=0,
            total_bytes=1000,
            status=DownloadStatus.PENDING,
        )

        assert progress.is_active is True

    def test_download_progress_is_active_completed(self):
        """is_active is False when COMPLETED."""
        from speakeasy.services.download_state import ModelDownloadProgress, DownloadStatus

        progress = ModelDownloadProgress(
            download_id="test",
            model_name="test-model",
            model_type="whisper",
            downloaded_bytes=1000,
            total_bytes=1000,
            status=DownloadStatus.COMPLETED,
        )

        assert progress.is_active is False

    def test_download_progress_to_dict(self):
        """to_dict() returns all fields."""
        from speakeasy.services.download_state import ModelDownloadProgress, DownloadStatus

        progress = ModelDownloadProgress(
            download_id="test-id",
            model_name="test-model",
            model_type="whisper",
            downloaded_bytes=500,
            total_bytes=1000,
            status=DownloadStatus.DOWNLOADING,
        )

        data = progress.to_dict()

        assert isinstance(data, dict)
        assert data["download_id"] == "test-id"
        assert data["model_name"] == "test-model"
        assert data["progress_percent"] == 50.0
        assert data["is_active"] is True
