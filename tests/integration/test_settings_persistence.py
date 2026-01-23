"""
Integration tests for settings persistence.

This test module covers:
- Settings file loading and saving
- Settings migration between versions
- Default value handling
- Corrupted settings recovery
- Settings change notifications
- Cross-session settings persistence

Run with: pytest tests/integration/test_settings_persistence.py -v
"""

import pytest
import os
import json
import tempfile
import shutil
import threading
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from faster_whisper_hotkey.settings import (
    Settings,
    load_settings,
    save_settings,
    get_settings_dir,
    get_settings_file,
    is_portable_mode,
    TextProcessingSettings,
)
from faster_whisper_hotkey.flet_gui.settings_service import SettingsService


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp(prefix="settings_persistence_test_")
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_settings_dir(temp_dir, monkeypatch):
    """Mock the settings directory to use temp directory."""
    def mock_get_settings_dir():
        return temp_dir

    monkeypatch.setattr("faster_whisper_hotkey.settings.get_settings_dir", mock_get_settings_dir)
    monkeypatch.setattr("faster_whisper_hotkey.flet_gui.settings_service.get_settings_dir", mock_get_settings_dir)

    return temp_dir


# ============================================================================
# Test: Settings File Loading
# ============================================================================

@pytest.mark.integration
def test_load_settings_from_file(temp_dir, monkeypatch):
    """Test loading settings from a JSON file."""
    # Create test settings file
    settings_file = os.path.join(temp_dir, "transcriber_settings.json")
    test_data = {
        "device_name": "test_device",
        "model_type": "whisper",
        "model_name": "medium",
        "compute_type": "int8",
        "device": "cuda",
        "language": "es",
        "hotkey": "ctrl+f1",
        "history_hotkey": "ctrl+shift+h",
        "activation_mode": "toggle",
        "history_max_items": 100,
        "privacy_mode": True,
        "onboarding_completed": True,
        "text_processing": {
            "remove_filler_words": True,
            "auto_capitalize": False,
        },
        "enable_streaming": True,
        "auto_copy_on_release": False,
        "confidence_threshold": 0.7,
        "stream_chunk_duration": 2.0,
        "voice_commands": {
            "enabled": True,
            "command_prefixes": ["!", "/"],
        },
        "theme_mode": "dark",
        "update_check_frequency": "daily",
        "update_include_prereleases": True,
        "update_auto_download": True,
        "telemetry_enabled": True,
    }

    with open(settings_file, 'w') as f:
        json.dump(test_data, f)

    # Patch get_settings_file
    monkeypatch.setattr("faster_whisper_hotkey.settings.get_settings_file", lambda: settings_file)

    # Load settings
    settings = load_settings()

    assert settings is not None
    assert settings.model_name == "medium"
    assert settings.device == "cuda"
    assert settings.language == "es"
    assert settings.hotkey == "ctrl+f1"
    assert settings.activation_mode == "toggle"
    assert settings.history_max_items == 100
    assert settings.privacy_mode is True
    assert settings.onboarding_completed is True
    assert settings.text_processing["remove_filler_words"] is True
    assert settings.enable_streaming is True
    assert settings.confidence_threshold == 0.7
    assert settings.theme_mode == "dark"
    assert settings.update_check_frequency == "daily"


@pytest.mark.integration
def test_load_settings_with_defaults(temp_dir, monkeypatch):
    """Test loading settings applies defaults for missing values."""
    settings_file = os.path.join(temp_dir, "transcriber_settings.json")
    # Minimal settings file
    test_data = {
        "device_name": "test",
        "model_type": "whisper",
        "model_name": "tiny",
        "compute_type": "int8",
        "device": "cpu",
        "language": "en",
    }

    with open(settings_file, 'w') as f:
        json.dump(test_data, f)

    monkeypatch.setattr("faster_whisper_hotkey.settings.get_settings_file", lambda: settings_file)

    settings = load_settings()

    assert settings is not None
    # Check defaults applied
    assert settings.hotkey == "pause"  # Default
    assert settings.history_hotkey == "ctrl+shift+h"  # Default
    assert settings.activation_mode == "hold"  # Default
    assert settings.history_max_items == 50  # Default
    assert settings.privacy_mode is False  # Default
    assert settings.onboarding_completed is False  # Default
    assert settings.enable_streaming is False  # Default
    assert settings.confidence_threshold == 0.5  # Default
    assert settings.theme_mode == "system"  # Default


@pytest.mark.integration
def test_load_settings_file_not_found(monkeypatch, temp_dir):
    """Test loading settings when file doesn't exist."""
    settings_file = os.path.join(temp_dir, "nonexistent_settings.json")
    monkeypatch.setattr("faster_whisper_hotkey.settings.get_settings_file", lambda: settings_file)

    settings = load_settings()

    assert settings is None


@pytest.mark.integration
def test_load_settings_corrupted_json(temp_dir, monkeypatch):
    """Test loading settings from corrupted JSON file."""
    settings_file = os.path.join(temp_dir, "transcriber_settings.json")

    # Write invalid JSON
    with open(settings_file, 'w') as f:
        f.write("{ invalid json }")

    monkeypatch.setattr("faster_whisper_hotkey.settings.get_settings_file", lambda: settings_file)

    settings = load_settings()

    assert settings is None


# ============================================================================
# Test: Settings File Saving
# ============================================================================

@pytest.mark.integration
def test_save_settings_to_file(temp_dir, monkeypatch):
    """Test saving settings to a JSON file."""
    settings_file = os.path.join(temp_dir, "transcriber_settings.json")
    monkeypatch.setattr("faster_whisper_hotkey.settings.get_settings_file", lambda: settings_file)

    settings_dict = {
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
        "update_auto_download": False",
    }

    save_settings(settings_dict)

    # Verify file was created
    assert os.path.exists(settings_file)

    # Verify content
    with open(settings_file, 'r') as f:
        loaded_data = json.load(f)

    assert loaded_data["model_name"] == "large-v3"
    assert loaded_data["language"] == "en"


@pytest.mark.integration
def test_save_and_load_roundtrip(temp_dir, monkeypatch):
    """Test that saving and loading preserves settings."""
    settings_file = os.path.join(temp_dir, "transcriber_settings.json")
    monkeypatch.setattr("faster_whisper_hotkey.settings.get_settings_file", lambda: settings_file)

    # Original settings
    original_dict = {
        "device_name": "my_device",
        "model_type": "whisper",
        "model_name": "medium",
        "compute_type": "int8",
        "device": "cuda",
        "language": "fr",
        "hotkey": "ctrl+shift+space",
        "history_hotkey": "ctrl+alt+h",
        "activation_mode": "toggle",
        "history_max_items": 200,
        "privacy_mode": True,
        "onboarding_completed": False,
        "text_processing": {
            "remove_filler_words": False,
            "auto_capitalize": True,
            "auto_punctuate": True,
        },
        "enable_streaming": True,
        "auto_copy_on_release": False,
        "confidence_threshold": 0.8,
        "stream_chunk_duration": 1.5,
        "voice_commands": {},
        "theme_mode": "light",
        "update_check_frequency": "manually",
        "update_include_prereleases": False,
        "update_auto_download": False,
    }

    # Save
    save_settings(original_dict)

    # Load
    loaded_settings = load_settings()

    # Verify all fields match
    assert loaded_settings.device_name == original_dict["device_name"]
    assert loaded_settings.model_name == original_dict["model_name"]
    assert loaded_settings.language == original_dict["language"]
    assert loaded_settings.hotkey == original_dict["hotkey"]
    assert loaded_settings.history_hotkey == original_dict["history_hotkey"]
    assert loaded_settings.activation_mode == original_dict["activation_mode"]
    assert loaded_settings.history_max_items == original_dict["history_max_items"]
    assert loaded_settings.privacy_mode == original_dict["privacy_mode"]
    assert loaded_settings.text_processing == original_dict["text_processing"]
    assert loaded_settings.enable_streaming == original_dict["enable_streaming"]
    assert loaded_settings.confidence_threshold == original_dict["confidence_threshold"]
    assert loaded_settings.theme_mode == original_dict["theme_mode"]


# ============================================================================
# Test: Settings Service Persistence
# ============================================================================

@pytest.mark.integration
def test_settings_service_save_and_load(temp_dir, monkeypatch):
    """Test SettingsService save and load operations."""
    settings_file = os.path.join(temp_dir, "test_settings.json")
    monkeypatch.setattr("faster_whisper_hotkey.settings.get_settings_file", lambda: settings_file)
    monkeypatch.setattr("faster_whisper_hotkey.settings.get_settings_dir", lambda: temp_dir)

    service = SettingsService()

    # Create and save settings
    with patch('faster_whisper_hotkey.flet_gui.settings_service.load_settings') as mock_load:
        from faster_whisper_hotkey.settings import Settings

        mock_settings = Settings(
            device_name="test",
            model_type="whisper",
            model_name="small",
            compute_type="int8",
            device="cpu",
            language="en",
            hotkey="f1",
        )
        mock_load.return_value = mock_settings

        service.load()

        # Modify settings
        service.set_model_name("large-v3")
        service.set_language("es")
        service.set_hotkey("ctrl+f1")

        # Save
        with patch('faster_whisper_hotkey.flet_gui.settings_service.save_settings') as mock_save:
            service.save()
            mock_save.assert_called_once()


# ============================================================================
# Test: Settings Change Notifications
# ============================================================================

@pytest.mark.integration
def test_settings_change_notifications(temp_dir, monkeypatch):
    """Test that settings changes trigger notifications."""
    settings_file = os.path.join(temp_dir, "test_settings.json")
    monkeypatch.setattr("faster_whisper_hotkey.settings.get_settings_file", lambda: settings_file)
    monkeypatch.setattr("faster_whisper_hotkey.settings.get_settings_dir", lambda: temp_dir)

    service = SettingsService()

    notification_log = []

    def listener(settings):
        notification_log.append({
            "model": settings.model_name if settings else None,
            "language": settings.language if settings else None,
        })

    unsubscribe = service.subscribe(listener)

    # Load settings (should trigger notification)
    with patch('faster_whisper_hotkey.flet_gui.settings_service.load_settings') as mock_load:
        from faster_whisper_hotkey.settings import Settings

        mock_settings = Settings(
            device_name="test",
            model_type="whisper",
            model_name="tiny",
            compute_type="int8",
            device="cpu",
            language="en",
        )
        mock_load.return_value = mock_settings

        service.load()

        assert len(notification_log) >= 1
        assert notification_log[-1]["model"] == "tiny"

    # Change settings (should trigger notification)
    service.set_model_name("medium")

    assert len(notification_log) >= 2
    assert notification_log[-1]["model"] == "medium"

    # Unsubscribe and change again (should not trigger)
    unsubscribe()
    service.set_model_name("large-v3")

    # Notification count should not increase
    final_count = len(notification_log)
    service.set_model_name("small")
    assert len(notification_log) == final_count


# ============================================================================
# Test: Thread-Safe Settings Access
# ============================================================================

@pytest.mark.integration
def test_concurrent_settings_access(temp_dir, monkeypatch):
    """Test that settings access is thread-safe."""
    settings_file = os.path.join(temp_dir, "test_settings.json")
    monkeypatch.setattr("faster_whisper_hotkey.settings.get_settings_file", lambda: settings_file)
    monkeypatch.setattr("faster_whisper_hotkey.settings.get_settings_dir", lambda: temp_dir)

    service = SettingsService()

    # Load settings
    with patch('faster_whisper_hotkey.flet_gui.settings_service.load_settings') as mock_load:
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
        mock_load.return_value = mock_settings
        service.load()

    results = {"gets": 0, "sets": 0, "errors": []}

    def get_settings():
        try:
            for _ in range(100):
                service.get_model_name()
                service.get_language()
                service.get_device()
                results["gets"] += 1
        except Exception as e:
            results["errors"].append(("get", e))

    def set_settings():
        try:
            for i in range(100):
                service.set_model_name(f"model_{i % 5}", notify=False)
                service.set_language(f"lang_{i % 3}", notify=False)
                results["sets"] += 1
        except Exception as e:
            results["errors"].append(("set", e))

    # Run concurrent operations
    threads = []
    for _ in range(3):
        threads.append(threading.Thread(target=get_settings))
    for _ in range(2):
        threads.append(threading.Thread(target=set_settings))

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verify no errors
    assert len(results["errors"]) == 0
    assert results["gets"] > 0
    assert results["sets"] > 0


# ============================================================================
# Test: Settings Validation on Load
# ============================================================================

@pytest.mark.integration
def test_settings_validation_on_load(temp_dir, monkeypatch):
    """Test that invalid settings are handled on load."""
    settings_file = os.path.join(temp_dir, "transcriber_settings.json")

    # Create settings with some invalid values
    test_data = {
        "device_name": "test",
        "model_type": "whisper",
        "model_name": "invalid_model",  # Invalid
        "compute_type": "int8",
        "device": "cpu",
        "language": "xx",  # Invalid
        "hotkey": "pause",
        "history_max_items": -1,  # Invalid (negative)
    }

    with open(settings_file, 'w') as f:
        json.dump(test_data, f)

    monkeypatch.setattr("faster_whisper_hotkey.settings.get_settings_file", lambda: settings_file)

    # SettingsService validation would catch this
    service = SettingsService()

    with patch('faster_whisper_hotkey.flet_gui.settings_service.load_settings') as mock_load:
        from faster_whisper_hotkey.settings import Settings

        # Even with invalid data, Settings object would be created
        # But validation methods should catch it
        mock_settings = Settings(**test_data)
        mock_load.return_value = mock_settings

        service.load()

        # Validate methods should work
        assert service.validate_model("invalid_model") is False
        assert service.validate_model("large-v3") is True
        assert service.validate_language("xx") is False
        assert service.validate_language("en") is True


# ============================================================================
# Test: Portable Mode Detection
# ============================================================================

@pytest.mark.integration
def test_portable_mode_detection(monkeypatch):
    """Test portable mode detection."""
    # Test with PORTABLE_MODE environment variable
    monkeypatch.setenv("PORTABLE_MODE", "1")

    assert is_portable_mode() is True

    # Clear environment variable
    monkeypatch.delenv("PORTABLE_MODE", raising=False)

    # Test without environment variable (should be False in normal test)
    with patch('sys.frozen', False):
        assert is_portable_mode() is False


# ============================================================================
# Test: Settings Migration
# ============================================================================

@pytest.mark.integration
def test_settings_migration_from_old_version(temp_dir, monkeypatch):
    """Test migrating settings from an old version."""
    settings_file = os.path.join(temp_dir, "transcriber_settings.json")

    # Simulate old settings file (v0.1) with fewer fields
    old_settings = {
        "device_name": "test_device",
        "model_name": "base",
        "compute_type": "int8",
        "device": "cpu",
        "language": "en",
        "hotkey": "pause",
        # Missing new fields like:
        # - history_hotkey
        # - activation_mode
        # - enable_streaming
        # - theme_mode
        # - update settings
        # - telemetry
    }

    with open(settings_file, 'w') as f:
        json.dump(old_settings, f)

    monkeypatch.setattr("faster_whisper_hotkey.settings.get_settings_file", lambda: settings_file)

    # Load should apply defaults for missing fields
    settings = load_settings()

    assert settings is not None
    assert settings.model_name == "base"
    # Check defaults applied
    assert settings.history_hotkey == "ctrl+shift+h"
    assert settings.activation_mode == "hold"
    assert settings.enable_streaming is False
    assert settings.theme_mode == "system"
    assert settings.update_check_frequency == "weekly"
    assert settings.telemetry_enabled is False


# ============================================================================
# Test: Text Processing Settings
# ============================================================================

@pytest.mark.integration
def test_text_processing_settings_defaults():
    """Test TextProcessingSettings default values."""
    settings = TextProcessingSettings()

    assert settings.remove_filler_words is True
    assert settings.auto_capitalize is True
    assert settings.auto_punctuate is True
    assert settings.format_numbers is False
    assert settings.expand_acronyms is False
    assert settings.use_dictionary is True
    assert settings.filler_aggressiveness == 0.5
    assert settings.capitalization_style == "sentence"
    assert settings.punctuation_style == "minimal"
    assert settings.number_style == "commas"
    assert settings.dictionary_fuzzy_matching is True
    assert settings.custom_filler_words == []
    assert settings.custom_acronyms == {}


@pytest.mark.integration
def test_text_processing_settings_custom_values():
    """Test TextProcessingSettings with custom values."""
    settings = TextProcessingSettings(
        remove_filler_words=False,
        auto_capitalize=False,
        auto_punctuate=False,
        format_numbers=True,
        filler_aggressiveness=0.8,
        capitalization_style="title",
        punctuation_style="full",
        number_style="words",
        custom_filler_words=["um", "uh"],
        custom_acronyms={"lol": "laugh out loud"},
    )

    assert settings.remove_filler_words is False
    assert settings.auto_capitalize is False
    assert settings.auto_punctuate is False
    assert settings.format_numbers is True
    assert settings.filler_aggressiveness == 0.8
    assert settings.capitalization_style == "title"
    assert settings.punctuation_style == "full"
    assert settings.number_style == "words"
    assert settings.custom_filler_words == ["um", "uh"]
    assert settings.custom_acronyms == {"lol": "laugh out loud"}


@pytest.mark.integration
def test_get_text_processing_settings_from_settings(temp_dir, monkeypatch):
    """Test getting TextProcessingSettings from Settings."""
    settings_file = os.path.join(temp_dir, "transcriber_settings.json")

    test_data = {
        "device_name": "test",
        "model_type": "whisper",
        "model_name": "tiny",
        "compute_type": "int8",
        "device": "cpu",
        "language": "en",
        "text_processing": {
            "remove_filler_words": False,
            "auto_capitalize": True,
            "auto_punctuate": True,
            "filler_aggressiveness": 0.7,
            "capitalization_style": "title",
            "custom_filler_words": ["like", "you know"],
        },
    }

    with open(settings_file, 'w') as f:
        json.dump(test_data, f)

    monkeypatch.setattr("faster_whisper_hotkey.settings.get_settings_file", lambda: settings_file)

    settings = load_settings()

    assert settings is not None

    text_proc = settings.get_text_processing_settings()

    assert text_proc.remove_filler_words is False
    assert text_proc.auto_capitalize is True
    assert text_proc.auto_punctuate is True
    assert text_proc.filler_aggressiveness == 0.7
    assert text_proc.capitalization_style == "title"
    assert text_proc.custom_filler_words == ["like", "you know"]


# ============================================================================
# Test: Settings Directory Creation
# ============================================================================

@pytest.mark.integration
def test_settings_directory_creation(temp_dir, monkeypatch):
    """Test that settings directory is created if it doesn't exist."""
    nonexistent_dir = os.path.join(temp_dir, "nonexistent", "settings")
    settings_file = os.path.join(nonexistent_dir, "settings.json")

    monkeypatch.setattr("faster_whisper_hotkey.settings.get_settings_file", lambda: settings_file)
    monkeypatch.setattr("faster_whisper_hotkey.settings.get_settings_dir", lambda: nonexistent_dir)

    # Save should create directory
    save_settings({
        "device_name": "test",
        "model_type": "whisper",
        "model_name": "tiny",
        "compute_type": "int8",
        "device": "cpu",
        "language": "en",
    })

    # Verify directory was created
    assert os.path.exists(nonexistent_dir)
    assert os.path.exists(settings_file)
