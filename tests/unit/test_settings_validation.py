"""
Unit tests for settings validation functionality.

This test module covers:
- Settings validation with type checking
- Range validation for numeric values
- Choice validation for enum-like fields
- Corrupted settings recovery
- Settings backup/restore

Run with: pytest tests/unit/test_settings_validation.py -v
"""

import pytest
import os
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, Mock

from faster_whisper_hotkey.settings import (
    Settings,
    validate_settings,
    create_default_settings,
    backup_settings_file,
    restore_settings_backup,
    SettingsBackup,
    SettingsValidationError,
    SettingsCorruptedError,
    load_settings,
    save_settings,
    _validate_type,
    _validate_range,
    _validate_choice,
    _VALID_ACTIVATION_MODES,
    _VALID_THEME_MODES,
    _VALID_UPDATE_FREQUENCIES,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def temp_settings_dir():
    """Create a temporary directory for settings files."""
    temp_dir = tempfile.mkdtemp(prefix="settings_validation_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_settings_dir(temp_settings_dir, monkeypatch):
    """Mock the settings directory to use temp directory."""
    monkeypatch.setattr("faster_whisper_hotkey.settings.get_settings_dir", lambda: temp_settings_dir)
    monkeypatch.setattr("faster_whisper_hotkey.settings.get_settings_file",
                        lambda: os.path.join(temp_settings_dir, "transcriber_settings.json"))
    return temp_settings_dir


# ============================================================================
# Test: Type Validation
# ============================================================================

@pytest.mark.unit
def test_validate_type_string():
    """Test string type validation."""
    assert _validate_type("hello", str, "test_field") == "hello"
    assert _validate_type(123, str, "test_field") == "123"
    assert _validate_type(True, str, "test_field") == "True"


@pytest.mark.unit
def test_validate_type_int():
    """Test integer type validation."""
    assert _validate_type(42, int, "test_field") == 42
    assert _validate_type("42", int, "test_field") == 42
    assert _validate_type(42.5, int, "test_field") == 42


@pytest.mark.unit
def test_validate_type_float():
    """Test float type validation."""
    assert _validate_type(3.14, float, "test_field") == 3.14
    assert _validate_type("3.14", float, "test_field") == 3.14
    assert _validate_type(42, float, "test_field") == 42.0


@pytest.mark.unit
def test_validate_type_bool():
    """Test boolean type validation with various representations."""
    assert _validate_type(True, bool, "test_field") is True
    assert _validate_type(False, bool, "test_field") is False
    # String to bool conversion
    assert _validate_type("true", bool, "test_field") is True
    assert _validate_type("True", bool, "test_field") is True
    assert _validate_type("false", bool, "test_field") is False
    assert _validate_type("1", bool, "test_field") is True
    assert _validate_type("0", bool, "test_field") is False
    assert _validate_type("yes", bool, "test_field") is True
    assert _validate_type("no", bool, "test_field") is False


@pytest.mark.unit
def test_validate_type_invalid():
    """Test that invalid types raise SettingsValidationError."""
    with pytest.raises(SettingsValidationError):
        _validate_type(object(), str, "test_field")


@pytest.mark.unit
def test_validate_type_none():
    """Test that None values are handled correctly."""
    assert _validate_type(None, str, "test_field") is None


# ============================================================================
# Test: Range Validation
# ============================================================================

@pytest.mark.unit
def test_validate_range_in_bounds():
    """Test range validation with values within bounds."""
    assert _validate_range(50, 0, 100, "test_field") == 50
    assert _validate_range(0, 0, 100, "test_field") == 0
    assert _validate_range(100, 0, 100, "test_field") == 100


@pytest.mark.unit
def test_validate_range_below_minimum():
    """Test range validation with value below minimum."""
    assert _validate_range(-10, 0, 100, "test_field") == 0


@pytest.mark.unit
def test_validate_range_above_maximum():
    """Test range validation with value above maximum."""
    assert _validate_range(150, 0, 100, "test_field") == 100


@pytest.mark.unit
def test_validate_range_no_minimum():
    """Test range validation with no minimum."""
    assert _validate_range(50, None, 100, "test_field") == 50


@pytest.mark.unit
def test_validate_range_no_maximum():
    """Test range validation with no maximum."""
    assert _validate_range(50, 0, None, "test_field") == 50


@pytest.mark.unit
def test_validate_range_string_conversion():
    """Test range validation with string to number conversion."""
    assert _validate_range("50", 0, 100, "test_field") == 50


@pytest.mark.unit
def test_validate_range_invalid():
    """Test range validation with invalid value."""
    with pytest.raises(SettingsValidationError):
        _validate_range("invalid", 0, 100, "test_field")


# ============================================================================
# Test: Choice Validation
# ============================================================================

@pytest.mark.unit
def test_validate_choice_valid():
    """Test choice validation with valid values."""
    assert _validate_choice("hold", _VALID_ACTIVATION_MODES, "test_field", "hold") == "hold"
    assert _validate_choice("toggle", _VALID_ACTIVATION_MODES, "test_field", "hold") == "toggle"


@pytest.mark.unit
def test_validate_choice_case_insensitive():
    """Test choice validation is case-insensitive."""
    assert _validate_choice("HOLD", _VALID_ACTIVATION_MODES, "test_field", "hold") == "hold"
    assert _validate_choice("Toggle", _VALID_ACTIVATION_MODES, "test_field", "hold") == "toggle"


@pytest.mark.unit
def test_validate_choice_invalid():
    """Test choice validation with invalid value returns default."""
    assert _validate_choice("invalid", _VALID_ACTIVATION_MODES, "test_field", "hold") == "hold"


@pytest.mark.unit
def test_validate_choice_none():
    """Test choice validation with None returns default."""
    assert _validate_choice(None, _VALID_ACTIVATION_MODES, "test_field", "hold") == "hold"


# ============================================================================
# Test: Full Settings Validation
# ============================================================================

@pytest.mark.unit
def test_validate_settings_complete():
    """Test validating a complete settings dictionary."""
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
        "history_max_items": 100,
        "privacy_mode": True,
        "enable_streaming": False,
        "confidence_threshold": 0.7,
        "theme_mode": "dark",
        "update_check_frequency": "daily",
        "telemetry_enabled": True,
    }

    validated = validate_settings(data)

    assert validated["device_name"] == "test_device"
    assert validated["model_name"] == "large-v3"
    assert validated["hotkey"] == "pause"
    assert validated["activation_mode"] == "hold"
    assert validated["history_max_items"] == 100
    assert validated["privacy_mode"] is True
    assert validated["confidence_threshold"] == 0.7
    assert validated["theme_mode"] == "dark"
    assert validated["update_check_frequency"] == "daily"
    assert validated["telemetry_enabled"] is True


@pytest.mark.unit
def test_validate_settings_defaults_applied():
    """Test that defaults are applied for missing fields."""
    data = {
        "device_name": "test_device",
        "model_type": "whisper",
        "model_name": "base",
        "compute_type": "int8",
        "device": "cuda",
        "language": "es",
    }

    validated = validate_settings(data)

    # Check defaults applied
    assert validated["hotkey"] == "pause"
    assert validated["history_hotkey"] == "ctrl+shift+h"
    assert validated["activation_mode"] == "hold"
    assert validated["history_max_items"] == 50
    assert validated["privacy_mode"] is False
    assert validated["enable_streaming"] is False
    assert validated["confidence_threshold"] == 0.5
    assert validated["theme_mode"] == "system"
    assert validated["update_check_frequency"] == "weekly"
    assert validated["telemetry_enabled"] is False


@pytest.mark.unit
def test_validate_settings_range_clamping():
    """Test that out-of-range values are clamped."""
    data = {
        "device_name": "test",
        "model_type": "whisper",
        "model_name": "tiny",
        "compute_type": "int8",
        "device": "cpu",
        "language": "en",
        "history_max_items": -1,  # Below minimum
        "confidence_threshold": 1.5,  # Above maximum
        "stream_chunk_duration": 100.0,  # Above maximum
    }

    validated = validate_settings(data)

    assert validated["history_max_items"] == 1  # Clamped to minimum
    assert validated["confidence_threshold"] == 1.0  # Clamped to maximum
    assert validated["stream_chunk_duration"] == 30.0  # Clamped to maximum


@pytest.mark.unit
def test_validate_settings_choice_correction():
    """Test that invalid choice values are corrected to defaults."""
    data = {
        "device_name": "test",
        "model_type": "whisper",
        "model_name": "tiny",
        "compute_type": "int8",
        "device": "cpu",
        "language": "en",
        "activation_mode": "invalid_mode",
        "theme_mode": "invalid_theme",
        "update_check_frequency": "invalid_frequency",
    }

    validated = validate_settings(data)

    assert validated["activation_mode"] == "hold"  # Default
    assert validated["theme_mode"] == "system"  # Default
    assert validated["update_check_frequency"] == "weekly"  # Default


@pytest.mark.unit
def test_validate_settings_type_conversion():
    """Test that type conversion works correctly."""
    data = {
        "device_name": "test",
        "model_type": "whisper",
        "model_name": "tiny",
        "compute_type": "int8",
        "device": "cpu",
        "language": "en",
        "history_max_items": "100",  # String that should be int
        "privacy_mode": "true",  # String that should be bool
        "confidence_threshold": "0.75",  # String that should be float
    }

    validated = validate_settings(data)

    assert isinstance(validated["history_max_items"], int)
    assert validated["history_max_items"] == 100
    assert isinstance(validated["privacy_mode"], bool)
    assert validated["privacy_mode"] is True
    assert isinstance(validated["confidence_threshold"], float)
    assert validated["confidence_threshold"] == 0.75


@pytest.mark.unit
def test_validate_settings_nested_text_processing():
    """Test validation of nested text processing settings."""
    data = {
        "device_name": "test",
        "model_type": "whisper",
        "model_name": "tiny",
        "compute_type": "int8",
        "device": "cpu",
        "language": "en",
        "text_processing": {
            "remove_filler_words": "true",  # String bool
            "filler_aggressiveness": "0.8",  # String float
            "capitalization_style": "TITLE",  # Case should be fixed
            "custom_filler_words": ["um", "uh", "like"],
        }
    }

    validated = validate_settings(data)

    tp = validated["text_processing"]
    assert isinstance(tp["remove_filler_words"], bool)
    assert tp["remove_filler_words"] is True
    assert isinstance(tp["filler_aggressiveness"], float)
    assert tp["filler_aggressiveness"] == 0.8
    assert tp["capitalization_style"] == "title"  # Lowercased
    assert tp["custom_filler_words"] == ["um", "uh", "like"]


@pytest.mark.unit
def test_validate_settings_nested_voice_commands():
    """Test validation of nested voice command settings."""
    data = {
        "device_name": "test",
        "model_type": "whisper",
        "model_name": "tiny",
        "compute_type": "int8",
        "device": "cpu",
        "language": "en",
        "voice_commands": {
            "enabled": "1",  # String bool
            "confidence_threshold": "0.9",
            "key_press_delay": 50,  # Should be float
        }
    }

    validated = validate_settings(data)

    vc = validated["voice_commands"]
    assert isinstance(vc["enabled"], bool)
    assert vc["enabled"] is True
    assert isinstance(vc["confidence_threshold"], float)
    assert vc["confidence_threshold"] == 0.9
    assert isinstance(vc["key_press_delay"], float)
    assert vc["key_press_delay"] == 50.0


@pytest.mark.unit
def test_validate_settings_invalid_nested_data():
    """Test handling of invalid nested data types."""
    data = {
        "device_name": "test",
        "model_type": "whisper",
        "model_name": "tiny",
        "compute_type": "int8",
        "device": "cpu",
        "language": "en",
        "text_processing": "not a dict",  # Invalid
        "voice_commands": None,  # Valid, should default to {}
    }

    validated = validate_settings(data)

    assert isinstance(validated["text_processing"], dict)
    assert validated["text_processing"] == {}
    assert isinstance(validated["voice_commands"], dict)


# ============================================================================
# Test: Default Settings Creation
# ============================================================================

@pytest.mark.unit
def test_create_default_settings():
    """Test creating default settings."""
    settings = create_default_settings()

    assert isinstance(settings, Settings)
    assert settings.device_name == "default_device"
    assert settings.model_name == "large-v3"
    assert settings.device == "cpu"
    assert settings.language == "en"
    assert settings.hotkey == "pause"
    assert settings.activation_mode == "hold"
    assert settings.privacy_mode is False


@pytest.mark.unit
def test_create_default_settings_with_overrides():
    """Test creating default settings with overrides."""
    settings = create_default_settings(
        model_name="tiny",
        device="cuda",
        language="es",
        hotkey="ctrl+f1"
    )

    assert settings.model_name == "tiny"
    assert settings.device == "cuda"
    assert settings.language == "es"
    assert settings.hotkey == "ctrl+f1"
    # Other defaults still apply
    assert settings.activation_mode == "hold"


# ============================================================================
# Test: Settings Backup/Restore
# ============================================================================

@pytest.mark.unit
def test_backup_settings_file(mock_settings_dir):
    """Test creating a settings backup."""
    # Create initial settings file
    settings_file = os.path.join(mock_settings_dir, "transcriber_settings.json")
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

    # Create backup
    backup_path = backup_settings_file()

    assert backup_path is not None
    assert os.path.exists(backup_path)
    assert "backup" in backup_path

    # Verify backup content
    with open(backup_path, 'r') as f:
        backup_data = json.load(f)
    assert backup_data["device_name"] == "test"


@pytest.mark.unit
def test_backup_settings_file_no_existing(mock_settings_dir):
    """Test backup when no settings file exists."""
    # Don't create settings file
    backup_path = backup_settings_file()
    assert backup_path is None


@pytest.mark.unit
def test_restore_settings_backup(mock_settings_dir):
    """Test restoring settings from backup."""
    settings_file = os.path.join(mock_settings_dir, "transcriber_settings.json")

    # Create a backup file
    backup_data = {
        "device_name": "restored",
        "model_type": "whisper",
        "model_name": "medium",
        "compute_type": "float16",
        "device": "cuda",
        "language": "fr",
    }
    backup_path = os.path.join(mock_settings_dir, "backup.json")
    with open(backup_path, 'w') as f:
        json.dump(backup_data, f)

    # Restore
    result = restore_settings_backup(backup_path)
    assert result is True

    # Verify restoration
    with open(settings_file, 'r') as f:
        restored_data = json.load(f)
    assert restored_data["device_name"] == "restored"
    assert restored_data["model_name"] == "medium"


@pytest.mark.unit
def test_restore_settings_invalid_backup(mock_settings_dir):
    """Test restoring from an invalid backup file."""
    # Create invalid backup
    backup_path = os.path.join(mock_settings_dir, "invalid_backup.json")
    with open(backup_path, 'w') as f:
        f.write("{ invalid json }")

    result = restore_settings_backup(backup_path)
    assert result is False


@pytest.mark.unit
def test_settings_backup_context_manager(mock_settings_dir):
    """Test the SettingsBackup context manager."""
    settings_file = os.path.join(mock_settings_dir, "transcriber_settings.json")

    # Create initial settings
    test_data = {
        "device_name": "original",
        "model_type": "whisper",
        "model_name": "tiny",
        "compute_type": "int8",
        "device": "cpu",
        "language": "en",
    }
    with open(settings_file, 'w') as f:
        json.dump(test_data, f)

    # Test normal operation (no exception)
    with SettingsBackup(restore_on_error=True) as backup:
        # Modify settings
        modified_data = test_data.copy()
        modified_data["device_name"] = "modified"
        save_settings(modified_data, create_backup=False)

    # Settings should be modified
    with open(settings_file, 'r') as f:
        data = json.load(f)
    assert data["device_name"] == "modified"

    # Test with exception (should restore)
    with SettingsBackup(restore_on_error=True):
        # Modify settings
        modified_data = test_data.copy()
        modified_data["device_name"] = "will_be_restored"
        save_settings(modified_data, create_backup=False)
        raise ValueError("Simulated error")

    # Settings should be restored
    with open(settings_file, 'r') as f:
        data = json.load(f)
    assert data["device_name"] == "modified"


# ============================================================================
# Test: Corrupted Settings Handling
# ============================================================================

@pytest.mark.unit
def test_load_settings_corrupted_json(mock_settings_dir):
    """Test loading corrupted JSON settings file."""
    settings_file = os.path.join(mock_settings_dir, "transcriber_settings.json")

    # Write invalid JSON
    with open(settings_file, 'w') as f:
        f.write("{ corrupted json }")

    # Should return None and create backup
    settings = load_settings()
    assert settings is None

    # Check that backup was created
    backup_files = [f for f in os.listdir(mock_settings_dir) if "backup" in f]
    assert len(backup_files) > 0


@pytest.mark.unit
def test_load_settings_corrupted_with_raise(mock_settings_dir):
    """Test loading corrupted JSON with raise_on_error=True."""
    settings_file = os.path.join(mock_settings_dir, "transcriber_settings.json")

    # Write invalid JSON
    with open(settings_file, 'w') as f:
        f.write("{ corrupted json }")

    # Should raise SettingsCorruptedError
    with pytest.raises(SettingsCorruptedError):
        load_settings(raise_on_error=True)


@pytest.mark.unit
def test_load_settings_missing_field(mock_settings_dir):
    """Test loading settings with missing required fields."""
    settings_file = os.path.join(mock_settings_dir, "transcriber_settings.json")

    # Write incomplete settings
    incomplete_data = {
        "device_name": "test",
        # Missing required fields
    }
    with open(settings_file, 'w') as f:
        json.dump(incomplete_data, f)

    # Should validate and apply defaults
    settings = load_settings()
    assert settings is not None
    assert settings.device_name == "test"
    # Defaults applied
    assert settings.model_name == "large-v3"
    assert settings.device == "cpu"
    assert settings.language == "en"


# ============================================================================
# Test: Settings Save with Validation
# ============================================================================

@pytest.mark.unit
def test_save_settings_validates(mock_settings_dir):
    """Test that save_settings validates before saving."""
    settings_file = os.path.join(mock_settings_dir, "transcriber_settings.json")

    # Save settings with some invalid values
    invalid_settings = {
        "device_name": "test",
        "model_type": "whisper",
        "model_name": "tiny",
        "compute_type": "int8",
        "device": "cpu",
        "language": "en",
        "history_max_items": -100,  # Invalid, should be clamped
        "confidence_threshold": 2.0,  # Invalid, should be clamped
    }

    result = save_settings(invalid_settings)
    assert result is True

    # Load and verify values were corrected
    with open(settings_file, 'r') as f:
        saved_data = json.load(f)

    assert saved_data["history_max_items"] == 1  # Clamped to min
    assert saved_data["confidence_threshold"] == 1.0  # Clamped to max


@pytest.mark.unit
def test_save_settings_creates_backup(mock_settings_dir):
    """Test that save_settings creates backup by default."""
    settings_file = os.path.join(mock_settings_dir, "transcriber_settings.json")

    # Create initial settings
    initial_data = {
        "device_name": "initial",
        "model_type": "whisper",
        "model_name": "tiny",
        "compute_type": "int8",
        "device": "cpu",
        "language": "en",
    }
    save_settings(initial_data)

    # Save again (should create backup)
    new_data = initial_data.copy()
    new_data["device_name"] = "new"
    save_settings(new_data)

    # Check backup was created
    backup_files = [f for f in os.listdir(mock_settings_dir) if "backup" in f and "transcriber_settings" in f]
    assert len(backup_files) > 0


@pytest.mark.unit
def test_save_settings_no_backup_option(mock_settings_dir):
    """Test saving without creating backup."""
    settings_file = os.path.join(mock_settings_dir, "transcriber_settings.json")

    # Create initial settings
    initial_data = {
        "device_name": "initial",
        "model_type": "whisper",
        "model_name": "tiny",
        "compute_type": "int8",
        "device": "cpu",
        "language": "en",
    }
    save_settings(initial_data)

    # Save again without backup
    new_data = initial_data.copy()
    new_data["device_name"] = "new"
    save_settings(new_data, create_backup=False)

    # Check no backup was created
    backup_files = [f for f in os.listdir(mock_settings_dir) if "backup" in f and "transcriber_settings" in f]
    assert len(backup_files) == 0


# ============================================================================
# Test: Settings Migration
# ============================================================================

@pytest.mark.unit
def test_settings_migration_from_old_version(mock_settings_dir):
    """Test that old settings files are migrated correctly."""
    settings_file = os.path.join(mock_settings_dir, "transcriber_settings.json")

    # Simulate old version settings (minimal fields)
    old_settings = {
        "device_name": "old_device",
        "model_type": "whisper",
        "model_name": "base",
        "compute_type": "int8",
        "device": "cpu",
        "language": "en",
    }

    with open(settings_file, 'w') as f:
        json.dump(old_settings, f)

    # Load settings (should migrate)
    settings = load_settings()
    assert settings is not None
    assert settings.device_name == "old_device"
    assert settings.model_name == "base"

    # New fields should have defaults
    assert settings.history_hotkey == "ctrl+shift+h"
    assert settings.activation_mode == "hold"
    assert settings.theme_mode == "system"
    assert settings.telemetry_enabled is False


@pytest.mark.unit
def test_settings_migration_with_extra_fields(mock_settings_dir):
    """Test that extra fields in settings are handled gracefully."""
    settings_file = os.path.join(mock_settings_dir, "transcriber_settings.json")

    # Settings with unknown fields (from future version perhaps)
    settings_with_extras = {
        "device_name": "test",
        "model_type": "whisper",
        "model_name": "tiny",
        "compute_type": "int8",
        "device": "cpu",
        "language": "en",
        "unknown_future_field": "some_value",
        "another_unknown_field": 123,
    }

    with open(settings_file, 'w') as f:
        json.dump(settings_with_extras, f)

    # Should load successfully, ignoring unknown fields
    settings = load_settings()
    assert settings is not None
    assert settings.device_name == "test"
