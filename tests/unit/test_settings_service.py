"""
Unit tests for SettingsService.

This test module covers:
- Settings loading and persistence
- Settings validation
- Individual settings getters and setters
- Subscription notifications
- Thread-safe operations

Run with: pytest tests/unit/test_settings_service.py -v
"""

import pytest
import os
import json
import tempfile
import threading
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from faster_whisper_hotkey.flet_gui.settings_service import SettingsService


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def temp_settings_dir():
    """Create a temporary directory for settings files."""
    temp_dir = tempfile.mkdtemp(prefix="settings_test_")
    yield temp_dir

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_settings_file(temp_settings_dir):
    """Create a mock settings file path."""
    return os.path.join(temp_settings_dir, "test_settings.json")


@pytest.fixture
def sample_settings_data(temp_settings_dir):
    """Create sample settings data."""
    settings_file = os.path.join(temp_settings_dir, "transcriber_settings.json")
    data = {
        "device_name": "test_device",
        "model_type": "whisper",
        "model_name": "large-v3",
        "compute_type": "float16",
        "device": "cpu",
        "language": "en",
        "hotkey": "pause",
        "history_hotkey": "ctrl+shift+h",
        "activation_mode": "hold",
        "history_max_items": 50,
        "privacy_mode": False,
        "onboarding_completed": True,
        "text_processing": {},
        "enable_streaming": False,
        "auto_copy_on_release": True,
        "confidence_threshold": 0.5,
        "stream_chunk_duration": 3.0,
        "voice_commands": {},
        "theme_mode": "system",
        "update_check_frequency": "weekly",
        "update_include_prereleases": False,
        "update_auto_download": False,
    }

    with open(settings_file, 'w') as f:
        json.dump(data, f)

    # Patch the get_settings_file function to return our test file
    with patch('faster_whisper_hotkey.settings.get_settings_dir', return_value=temp_settings_dir):
        with patch('faster_whisper_hotkey.settings.get_settings_file', return_value=settings_file):
            yield data


@pytest.fixture
def settings_service():
    """Create a SettingsService instance."""
    return SettingsService()


# ============================================================================
# Test: Initialization
# ============================================================================

@pytest.mark.unit
def test_settings_service_initialization(settings_service):
    """Test that SettingsService initializes correctly."""
    assert settings_service._settings is None
    assert settings_service._listeners == set()
    assert settings_service.is_loaded is False


@pytest.mark.unit
def test_accepted_constants(settings_service):
    """Test that accepted model/language lists are available."""
    assert len(settings_service.ACCEPTED_MODELS) > 0
    assert len(settings_service.ACCEPTED_LANGUAGES) > 0
    assert "cpu" in settings_service.ACCEPTED_DEVICES
    assert "cuda" in settings_service.ACCEPTED_DEVICES
    assert "float16" in settings_service.ACCEPTED_COMPUTE_TYPES
    assert "int8" in settings_service.ACCEPTED_COMPUTE_TYPES
    assert "hold" in settings_service.ACTIVATION_MODES
    assert "toggle" in settings_service.ACTIVATION_MODES


# ============================================================================
# Test: Settings Loading
# ============================================================================

@pytest.mark.unit
def test_load_settings(settings_service, sample_settings_data):
    """Test loading settings from file."""
    with patch('faster_whisper_hotkey.flet_gui.settings_service.load_settings') as mock_load:
        from faster_whisper_hotkey.settings import Settings

        mock_settings = Settings(**sample_settings_data)
        mock_load.return_value = mock_settings

        result = settings_service.load()

        assert result is not None
        assert result.model_name == "large-v3"
        assert result.language == "en"
        assert settings_service.is_loaded is True


@pytest.mark.unit
def test_load_settings_failure(settings_service):
    """Test loading settings when file doesn't exist."""
    with patch('faster_whisper_hotkey.flet_gui.settings_service.load_settings') as mock_load:
        mock_load.return_value = None

        result = settings_service.load()

        assert result is None
        assert settings_service.is_loaded is False


@pytest.mark.unit
def test_load_settings_notifies_listeners(settings_service):
    """Test that loading settings notifies listeners."""
    notified = []

    def listener(settings):
        notified.append(settings)

    settings_service.subscribe(listener)

    with patch('faster_whisper_hotkey.flet_gui.settings_service.load_settings') as mock_load:
        from faster_whisper_hotkey.settings import Settings

        mock_settings = Settings(
            device_name="test",
            model_type="whisper",
            model_name="large-v3",
            compute_type="float16",
            device="cpu",
            language="en",
        )
        mock_load.return_value = mock_settings

        settings_service.load()

        assert len(notified) == 1
        assert notified[0].model_name == "large-v3"


# ============================================================================
# Test: Settings Saving
# ============================================================================

@pytest.mark.unit
def test_save_settings(settings_service):
    """Test saving settings to file."""
    from faster_whisper_hotkey.settings import Settings

    mock_settings = Settings(
        device_name="test",
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
        update_check_frequency="weekly",
        update_include_prereleases=False,
        update_auto_download=False,
    )

    settings_service._settings = mock_settings

    with patch('faster_whisper_hotkey.flet_gui.settings_service.save_settings') as mock_save:
        result = settings_service.save()

        assert result is True
        mock_save.assert_called_once()


@pytest.mark.unit
def test_save_settings_without_loading(settings_service):
    """Test saving when no settings are loaded."""
    result = settings_service.save()

    assert result is False


@pytest.mark.unit
def test_save_settings_notifies_listeners(settings_service):
    """Test that saving settings notifies listeners."""
    from faster_whisper_hotkey.settings import Settings

    notified = []

    def listener(settings):
        notified.append(settings)

    mock_settings = Settings(
        device_name="test",
        model_type="whisper",
        model_name="large-v3",
        compute_type="float16",
        device="cpu",
        language="en",
    )

    settings_service._settings = mock_settings
    settings_service.subscribe(listener)

    with patch('faster_whisper_hotkey.flet_gui.settings_service.save_settings'):
        settings_service.save()

    assert len(notified) == 1


# ============================================================================
# Test: Subscription Notifications
# ============================================================================

@pytest.mark.unit
def test_subscribe(settings_service):
    """Test subscribing to settings changes."""
    call_count = {"count": 0}

    def listener(settings):
        call_count["count"] += 1

    unsubscribe = settings_service.subscribe(listener)

    # Trigger notification
    settings_service._notify()

    assert call_count["count"] == 1


@pytest.mark.unit
def test_unsubscribe(settings_service):
    """Test unsubscribing from settings changes."""
    call_count = {"count": 0}

    def listener(settings):
        call_count["count"] += 1

    unsubscribe = settings_service.subscribe(listener)

    # First notification
    settings_service._notify()
    assert call_count["count"] == 1

    # Unsubscribe
    unsubscribe()

    # Second notification should not trigger
    settings_service._notify()
    assert call_count["count"] == 1


@pytest.mark.unit
def test_multiple_subscribers(settings_service):
    """Test multiple subscribers receive notifications."""
    calls = []

    def listener1(settings):
        calls.append("listener1")

    def listener2(settings):
        calls.append("listener2")

    settings_service.subscribe(listener1)
    settings_service.subscribe(listener2)

    settings_service._notify()

    assert "listener1" in calls
    assert "listener2" in calls


@pytest.mark.unit
def test_listener_exception_handling(settings_service):
    """Test that exceptions in listeners don't affect other listeners."""
    calls = []

    def failing_listener(settings):
        calls.append("failing")
        raise Exception("Test exception")

    def working_listener(settings):
        calls.append("working")

    settings_service.subscribe(failing_listener)
    settings_service.subscribe(working_listener)

    # Should not raise despite exception
    settings_service._notify()

    assert "failing" in calls
    assert "working" in calls


# ============================================================================
# Test: Settings Getters
# ============================================================================

@pytest.mark.unit
def test_settings_property(settings_service):
    """Test getting the settings property."""
    from faster_whisper_hotkey.settings import Settings

    mock_settings = Settings(
        device_name="test",
        model_type="whisper",
        model_name="large-v3",
        compute_type="float16",
        device="cpu",
        language="en",
    )

    settings_service._settings = mock_settings

    result = settings_service.settings

    assert result is mock_settings


@pytest.mark.unit
def test_is_loaded_property(settings_service):
    """Test is_loaded property."""
    assert settings_service.is_loaded is False

    from faster_whisper_hotkey.settings import Settings
    mock_settings = Settings(
        device_name="test",
        model_type="whisper",
        model_name="large-v3",
        compute_type="float16",
        device="cpu",
        language="en",
    )
    settings_service._settings = mock_settings

    assert settings_service.is_loaded is True


@pytest.mark.unit
def test_get_hotkey(settings_service):
    """Test getting hotkey."""
    from faster_whisper_hotkey.settings import Settings

    mock_settings = Settings(
        device_name="test",
        model_type="whisper",
        model_name="large-v3",
        compute_type="float16",
        device="cpu",
        language="en",
        hotkey="ctrl+shift+t",
    )
    settings_service._settings = mock_settings

    assert settings_service.get_hotkey() == "ctrl+shift+t"


@pytest.mark.unit
def test_get_hotkey_default(settings_service):
    """Test getting hotkey returns default when not loaded."""
    assert settings_service.get_hotkey() == "pause"


@pytest.mark.unit
def test_get_history_hotkey(settings_service):
    """Test getting history hotkey."""
    from faster_whisper_hotkey.settings import Settings

    mock_settings = Settings(
        device_name="test",
        model_type="whisper",
        model_name="large-v3",
        compute_type="float16",
        device="cpu",
        language="en",
        history_hotkey="ctrl+alt+h",
    )
    settings_service._settings = mock_settings

    assert settings_service.get_history_hotkey() == "ctrl+alt+h"


@pytest.mark.unit
def test_get_history_hotkey_default(settings_service):
    """Test getting history hotkey returns default when not loaded."""
    assert settings_service.get_history_hotkey() == "ctrl+shift+h"


@pytest.mark.unit
def test_get_model_name(settings_service):
    """Test getting model name."""
    from faster_whisper_hotkey.settings import Settings

    mock_settings = Settings(
        device_name="test",
        model_type="whisper",
        model_name="medium",
        compute_type="float16",
        device="cpu",
        language="en",
    )
    settings_service._settings = mock_settings

    assert settings_service.get_model_name() == "medium"


@pytest.mark.unit
def test_get_model_name_default(settings_service):
    """Test getting model name returns default when not loaded."""
    assert settings_service.get_model_name() == "large-v3"


@pytest.mark.unit
def test_get_language(settings_service):
    """Test getting language."""
    from faster_whisper_hotkey.settings import Settings

    mock_settings = Settings(
        device_name="test",
        model_type="whisper",
        model_name="large-v3",
        compute_type="float16",
        device="cpu",
        language="es",
    )
    settings_service._settings = mock_settings

    assert settings_service.get_language() == "es"


@pytest.mark.unit
def test_get_language_default(settings_service):
    """Test getting language returns default when not loaded."""
    assert settings_service.get_language() == "en"


@pytest.mark.unit
def test_get_device(settings_service):
    """Test getting device."""
    from faster_whisper_hotkey.settings import Settings

    mock_settings = Settings(
        device_name="test",
        model_type="whisper",
        model_name="large-v3",
        compute_type="float16",
        device="cuda",
        language="en",
    )
    settings_service._settings = mock_settings

    assert settings_service.get_device() == "cuda"


@pytest.mark.unit
def test_get_device_default(settings_service):
    """Test getting device returns default when not loaded."""
    assert settings_service.get_device() == "cpu"


@pytest.mark.unit
def test_get_activation_mode(settings_service):
    """Test getting activation mode."""
    from faster_whisper_hotkey.settings import Settings

    mock_settings = Settings(
        device_name="test",
        model_type="whisper",
        model_name="large-v3",
        compute_type="float16",
        device="cpu",
        language="en",
        activation_mode="toggle",
    )
    settings_service._settings = mock_settings

    assert settings_service.get_activation_mode() == "toggle"


@pytest.mark.unit
def test_get_activation_mode_default(settings_service):
    """Test getting activation mode returns default when not loaded."""
    assert settings_service.get_activation_mode() == "hold"


@pytest.mark.unit
def test_get_text_processing_settings(settings_service):
    """Test getting text processing settings."""
    from faster_whisper_hotkey.settings import Settings

    mock_settings = Settings(
        device_name="test",
        model_type="whisper",
        model_name="large-v3",
        compute_type="float16",
        device="cpu",
        language="en",
        text_processing={
            "remove_filler_words": True,
            "auto_capitalize": False,
        },
    )
    settings_service._settings = mock_settings

    result = settings_service.get_text_processing_settings()

    assert result.remove_filler_words is True
    assert result.auto_capitalize is False


@pytest.mark.unit
def test_get_text_processing_settings_default(settings_service):
    """Test getting text processing settings returns defaults."""
    result = settings_service.get_text_processing_settings()

    # Should return a TextProcessingSettings object with defaults
    assert hasattr(result, "remove_filler_words")
    assert hasattr(result, "auto_capitalize")


# ============================================================================
# Test: Settings Setters
# ============================================================================

@pytest.mark.unit
def test_set_hotkey(settings_service):
    """Test setting hotkey."""
    from faster_whisper_hotkey.settings import Settings

    mock_settings = Settings(
        device_name="test",
        model_type="whisper",
        model_name="large-v3",
        compute_type="float16",
        device="cpu",
        language="en",
        hotkey="pause",
    )
    settings_service._settings = mock_settings

    result = settings_service.set_hotkey("ctrl+f1")

    assert result is True
    assert mock_settings.hotkey == "ctrl+f1"


@pytest.mark.unit
def test_set_hotkey_without_loading(settings_service):
    """Test setting hotkey when settings not loaded."""
    result = settings_service.set_hotkey("ctrl+f1")

    assert result is False


@pytest.mark.unit
def test_set_hotkey_no_notify(settings_service):
    """Test setting hotkey without notification."""
    from faster_whisper_hotkey.settings import Settings

    notified = []

    def listener(settings):
        notified.append(settings)

    mock_settings = Settings(
        device_name="test",
        model_type="whisper",
        model_name="large-v3",
        compute_type="float16",
        device="cpu",
        language="en",
        hotkey="pause",
    )
    settings_service._settings = mock_settings
    settings_service.subscribe(listener)

    settings_service.set_hotkey("ctrl+f1", notify=False)

    assert mock_settings.hotkey == "ctrl+f1"
    assert len(notified) == 0


@pytest.mark.unit
def test_set_history_hotkey(settings_service):
    """Test setting history hotkey."""
    from faster_whisper_hotkey.settings import Settings

    mock_settings = Settings(
        device_name="test",
        model_type="whisper",
        model_name="large-v3",
        compute_type="float16",
        device="cpu",
        language="en",
        history_hotkey="ctrl+shift+h",
    )
    settings_service._settings = mock_settings

    result = settings_service.set_history_hotkey("ctrl+alt+h")

    assert result is True
    assert mock_settings.history_hotkey == "ctrl+alt+h"


@pytest.mark.unit
def test_set_model_name(settings_service):
    """Test setting model name."""
    from faster_whisper_hotkey.settings import Settings

    mock_settings = Settings(
        device_name="test",
        model_type="whisper",
        model_name="large-v3",
        compute_type="float16",
        device="cpu",
        language="en",
    )
    settings_service._settings = mock_settings

    result = settings_service.set_model_name("medium")

    assert result is True
    assert mock_settings.model_name == "medium"


@pytest.mark.unit
def test_set_model_name_invalid(settings_service):
    """Test setting invalid model name."""
    from faster_whisper_hotkey.settings import Settings

    mock_settings = Settings(
        device_name="test",
        model_type="whisper",
        model_name="large-v3",
        compute_type="float16",
        device="cpu",
        language="en",
    )
    settings_service._settings = mock_settings

    result = settings_service.set_model_name("invalid_model")

    assert result is False
    assert mock_settings.model_name == "large-v3"


@pytest.mark.unit
def test_set_language(settings_service):
    """Test setting language."""
    from faster_whisper_hotkey.settings import Settings

    mock_settings = Settings(
        device_name="test",
        model_type="whisper",
        model_name="large-v3",
        compute_type="float16",
        device="cpu",
        language="en",
    )
    settings_service._settings = mock_settings

    result = settings_service.set_language("es")

    assert result is True
    assert mock_settings.language == "es"


@pytest.mark.unit
def test_set_language_invalid(settings_service):
    """Test setting invalid language."""
    from faster_whisper_hotkey.settings import Settings

    mock_settings = Settings(
        device_name="test",
        model_type="whisper",
        model_name="large-v3",
        compute_type="float16",
        device="cpu",
        language="en",
    )
    settings_service._settings = mock_settings

    result = settings_service.set_language("xx")

    assert result is False
    assert mock_settings.language == "en"


@pytest.mark.unit
def test_set_device(settings_service):
    """Test setting device."""
    from faster_whisper_hotkey.settings import Settings

    mock_settings = Settings(
        device_name="test",
        model_type="whisper",
        model_name="large-v3",
        compute_type="float16",
        device="cpu",
        language="en",
    )
    settings_service._settings = mock_settings

    result = settings_service.set_device("cuda")

    assert result is True
    assert mock_settings.device == "cuda"


@pytest.mark.unit
def test_set_device_invalid(settings_service):
    """Test setting invalid device."""
    from faster_whisper_hotkey.settings import Settings

    mock_settings = Settings(
        device_name="test",
        model_type="whisper",
        model_name="large-v3",
        compute_type="float16",
        device="cpu",
        language="en",
    )
    settings_service._settings = mock_settings

    result = settings_service.set_device("invalid")

    assert result is False
    assert mock_settings.device == "cpu"


@pytest.mark.unit
def test_set_activation_mode(settings_service):
    """Test setting activation mode."""
    from faster_whisper_hotkey.settings import Settings

    mock_settings = Settings(
        device_name="test",
        model_type="whisper",
        model_name="large-v3",
        compute_type="float16",
        device="cpu",
        language="en",
        activation_mode="hold",
    )
    settings_service._settings = mock_settings

    result = settings_service.set_activation_mode("toggle")

    assert result is True
    assert mock_settings.activation_mode == "toggle"


@pytest.mark.unit
def test_set_activation_mode_invalid(settings_service):
    """Test setting invalid activation mode."""
    from faster_whisper_hotkey.settings import Settings

    mock_settings = Settings(
        device_name="test",
        model_type="whisper",
        model_name="large-v3",
        compute_type="float16",
        device="cpu",
        language="en",
        activation_mode="hold",
    )
    settings_service._settings = mock_settings

    result = settings_service.set_activation_mode("invalid")

    assert result is False
    assert mock_settings.activation_mode == "hold"


# ============================================================================
# Test: Validation Methods
# ============================================================================

@pytest.mark.unit
def test_validate_hotkey_valid(settings_service):
    """Test validating valid hotkeys."""
    test_cases = [
        ("pause", (True, "")),
        ("ctrl+f1", (True, "")),
        ("shift+alt+h", (True, "")),
        ("ctrl+shift+win+space", (True, "")),
        ("f12", (True, "")),
        ("a", (True, "")),
    ]

    for hotkey, expected in test_cases:
        result = settings_service.validate_hotkey(hotkey)
        assert result[0] == expected[0], f"Failed for {hotkey}: got {result}"


@pytest.mark.unit
def test_validate_hotkey_invalid(settings_service):
    """Test validating invalid hotkeys."""
    test_cases = [
        ("", False),
        ("   ", False),
        ("ctrl+@#$", False),
    ]

    for hotkey, should_be_valid in test_cases:
        result = settings_service.validate_hotkey(hotkey)
        assert result[0] == should_be_valid, f"Failed for '{hotkey}': got {result}"


@pytest.mark.unit
def test_validate_model(settings_service):
    """Test validating model names."""
    # Valid models
    for model in ["tiny", "base", "small", "medium", "large-v3"]:
        assert settings_service.validate_model(model) is True

    # Invalid model
    assert settings_service.validate_model("invalid_model") is False


@pytest.mark.unit
def test_validate_language(settings_service):
    """Test validating language codes."""
    # Common valid languages
    for lang in ["en", "es", "fr", "de", "ja", "zh"]:
        assert settings_service.validate_language(lang) is True

    # Invalid language
    assert settings_service.validate_language("xx") is False


@pytest.mark.unit
def test_validate_device(settings_service):
    """Test validating device types."""
    assert settings_service.validate_device("cpu") is True
    assert settings_service.validate_device("cuda") is True
    assert settings_service.validate_device("invalid") is False


# ============================================================================
# Test: Helper Methods for UI
# ============================================================================

@pytest.mark.unit
def test_get_model_display_name(settings_service):
    """Test getting model display names."""
    assert "fastest" in settings_service.get_model_display_name("tiny").lower()
    assert "recommended" in settings_service.get_model_display_name("large-v3").lower()
    assert settings_service.get_model_display_name("unknown_model") == "unknown_model"


@pytest.mark.unit
def test_get_language_display_name(settings_service):
    """Test getting language display names."""
    assert settings_service.get_language_display_name("en") == "English"
    assert settings_service.get_language_display_name("es") == "Spanish"
    assert settings_service.get_language_display_name("xx") == "XX"


@pytest.mark.unit
def test_get_available_models(settings_service):
    """Test getting available models list."""
    models = settings_service.get_available_models()
    assert isinstance(models, list)
    assert "tiny" in models
    assert "large-v3" in models


@pytest.mark.unit
def test_get_available_languages(settings_service):
    """Test getting available languages list."""
    languages = settings_service.get_available_languages()
    assert isinstance(languages, list)
    assert "en" in languages
    assert "es" in languages


# ============================================================================
# Test: Thread Safety
# ============================================================================

@pytest.mark.unit
def test_thread_safe_subscription(settings_service):
    """Test subscription is thread-safe."""
    listeners = []

    def subscribe_from_thread(i):
        def listener(settings):
            listeners.append(i)
        settings_service.subscribe(listener)

    import threading
    threads = [threading.Thread(target=subscribe_from_thread, args=(i,)) for i in range(10)]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(settings_service._listeners) == 10


@pytest.mark.unit
def test_thread_safe_get_set(settings_service):
    """Test getting and setting settings is thread-safe."""
    from faster_whisper_hotkey.settings import Settings

    mock_settings = Settings(
        device_name="test",
        model_type="whisper",
        model_name="large-v3",
        compute_type="float16",
        device="cpu",
        language="en",
        hotkey="pause",
    )
    settings_service._settings = mock_settings

    results = {"gets": 0, "sets": 0}

    def get_hotkey():
        for _ in range(100):
            settings_service.get_hotkey()
            results["gets"] += 1

    def set_hotkey():
        for i in range(100):
            settings_service.set_hotkey(f"ctrl+f{i % 12}", notify=False)
            results["sets"] += 1

    import threading
    threads = [
        threading.Thread(target=get_hotkey),
        threading.Thread(target=get_hotkey),
        threading.Thread(target=set_hotkey),
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results["gets"] == 200
    assert results["sets"] == 100
