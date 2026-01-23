"""
Integration tests for transcription workflow.

This test module covers:
- Full transcription workflow (hotkey → record → transcribe → paste)
- Settings changes and persistence
- History search and retrieval
- Integration between multiple services

Run with: pytest tests/integration/test_transcription_workflow.py -v
"""

import pytest
import os
import tempfile
import shutil
import json
import threading
import time
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, call

from faster_whisper_hotkey.flet_gui.transcription_service import TranscriptionService
from faster_whisper_hotkey.flet_gui.settings_service import SettingsService
from faster_whisper_hotkey.flet_gui.history_manager import HistoryManager, HistoryItem
from faster_whisper_hotkey.flet_gui.hotkey_manager import HotkeyManager
from faster_whisper_hotkey.settings import Settings


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp(prefix="integration_test_")
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def settings_file(temp_dir):
    """Create a temporary settings file."""
    return os.path.join(temp_dir, "test_settings.json")


@pytest.fixture
def history_db(temp_dir):
    """Create a temporary history database."""
    return os.path.join(temp_dir, "test_history.db")


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
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


# ============================================================================
# Test: Full Transcription Workflow
# ============================================================================

@pytest.mark.integration
def test_full_transcription_workflow(mock_settings, history_db):
    """
    Test complete transcription workflow:
    1. Initialize transcription service
    2. Start recording
    3. Stop recording (triggers transcription)
    4. Receive transcription result
    5. Add to history
    6. Search in history
    """
    # Setup mocks
    with patch('faster_whisper_hotkey.flet_gui.transcription_service.MicrophoneTranscriber') as mock_transcriber_cls:
        # Create mock transcriber instance
        mock_transcriber = MagicMock()
        mock_transcriber.is_recording = False
        mock_transcriber.is_transcribing = False
        mock_transcriber.current_audio_level = 0.5

        # Setup transcribe method to return result
        mock_transcriber.stop_recording_and_transcribe.return_value = "This is a test transcription"
        mock_transcriber_class = MagicMock(return_value=mock_transcriber)
        mock_transcriber_class.side_effect = lambda *args, **kwargs: mock_transcriber

        with patch('faster_whisper_hotkey.flet_gui.transcription_service.MicrophoneTranscriber', mock_transcriber_class):
            # Create services
            transcription_service = TranscriptionService(mock_settings)
            history_manager = HistoryManager(db_path=history_db, privacy_mode=False)

            # Track events
            events = []
            def on_transcription(text):
                events.append(("transcription", text))

            def on_state_change(state):
                events.append(("state", state))

            transcription_service.on("transcription", on_transcription)
            transcription_service.on("state_change", on_state_change)

            # Initialize
            assert transcription_service.initialize() is True
            assert transcription_service.is_initialized is True

            # Start recording
            assert transcription_service.start_recording() is True
            mock_transcriber.is_recording = True

            # Verify state changed to recording
            state_events = [e for e in events if e[0] == "state"]
            assert any(state == "recording" for _, state in state_events)

            # Stop recording and transcribe
            mock_transcriber.is_recording = False
            mock_transcriber.is_transcribing = True

            assert transcription_service.stop_recording() is True

            # Add to history
            history_item = HistoryItem(
                timestamp=datetime.now().isoformat(),
                text="This is a test transcription",
                model="large-v3",
                language="en",
                device="cpu",
                confidence=0.95,
            )
            item_id = history_manager.add_item(history_item)

            assert item_id is not None

            # Verify history
            all_items = history_manager.get_all()
            assert len(all_items) == 1
            assert all_items[0].text == "This is a test transcription"

            # Search in history
            results = history_manager.search_by_text("test")
            assert len(results) == 1

            # Cleanup
            transcription_service.shutdown()


@pytest.mark.integration
def test_transcription_with_settings_change(mock_settings, history_db):
    """
    Test transcription workflow when settings change mid-operation.
    """
    with patch('faster_whisper_hotkey.flet_gui.transcription_service.MicrophoneTranscriber') as mock_transcriber_cls:
        mock_transcriber = MagicMock()
        mock_transcriber.is_recording = False
        mock_transcriber.is_transcribing = False

        with patch('faster_whisper_hotkey.flet_gui.transcription_service.MicrophoneTranscriber', return_value=mock_transcriber):
            transcription_service = TranscriptionService(mock_settings)
            history_manager = HistoryManager(db_path=history_db)

            # Initialize with original settings
            assert transcription_service.initialize() is True

            # Change settings
            new_settings = Settings(
                device_name="test_device",
                model_type="whisper",
                model_name="medium",  # Changed model
                compute_type="int8",  # Changed compute type
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

            # Reinitialize with new settings
            assert transcription_service.reinitialize(new_settings) is True
            assert transcription_service._settings == new_settings

            transcription_service.shutdown()


@pytest.mark.integration
def test_transcription_to_clipboard_workflow(mock_settings, history_db):
    """
    Test transcription to clipboard workflow.
    """
    with patch('faster_whisper_hotkey.flet_gui.transcription_service.MicrophoneTranscriber') as mock_transcriber_cls:
        mock_transcriber = MagicMock()
        mock_transcriber.is_recording = False
        mock_transcriber.is_transcribing = False
        mock_transcriber.current_audio_level = 0.5

        with patch('faster_whisper_hotkey.flet_gui.transcription_service.MicrophoneTranscriber', return_value=mock_transcriber):
            # Mock clipboard
            with patch('faster_whisper_hotkey.clipboard.pyperclip') as mock_pyperclip:
                mock_pyperclip.paste.return_value = ""
                mock_pyperclip.copy.return_value = None

                transcription_service = TranscriptionService(mock_settings)

                transcription_service.initialize()

                transcription_events = []
                def on_transcription(text):
                    transcription_events.append(text)
                    # Simulate copying to clipboard
                    from faster_whisper_hotkey.clipboard import set_clipboard
                    set_clipboard(text)

                transcription_service.on("transcription", on_transcription)

                # Simulate transcription
                transcription_service._on_transcription("Test transcription for clipboard")

                assert len(transcription_events) == 1
                assert transcription_events[0] == "Test transcription for clipboard"

                # Verify clipboard was set
                mock_pyperclip.copy.assert_called()

                transcription_service.shutdown()


# ============================================================================
# Test: Settings Persistence Integration
# ============================================================================

@pytest.mark.integration
def test_settings_load_save_workflow(temp_dir):
    """
    Test settings persistence workflow.
    """
    settings_file = os.path.join(temp_dir, "settings.json")

    # Create initial settings
    initial_data = {
        "device_name": "test_device",
        "model_type": "whisper",
        "model_name": "tiny",
        "compute_type": "int8",
        "device": "cpu",
        "language": "en",
        "hotkey": "pause",
        "history_hotkey": "ctrl+shift+h",
        "activation_mode": "hold",
        "history_max_items": 50,
        "privacy_mode": False,
        "onboarding_completed": False,
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
        "telemetry_enabled": False,
    }

    # Save initial settings
    with open(settings_file, 'w') as f:
        json.dump(initial_data, f)

    # Load settings using SettingsService
    with patch('faster_whisper_hotkey.settings.get_settings_file', return_value=settings_file):
        with patch('faster_whisper_hotkey.settings.get_settings_dir', return_value=temp_dir):
            settings_service = SettingsService()
            settings = settings_service.load()

            assert settings is not None
            assert settings.model_name == "tiny"
            assert settings.device == "cpu"

            # Modify settings
            settings_service.set_model_name("large-v3")
            settings_service.set_language("es")

            # Save settings
            with patch('faster_whisper_hotkey.flet_gui.settings_service.save_settings') as mock_save:
                settings_service.save()
                mock_save.assert_called_once()


@pytest.mark.integration
def test_settings_change_notifications():
    """
    Test that settings changes trigger notifications.
    """
    settings_service = SettingsService()

    notified = []

    def listener(settings):
        notified.append(settings)

    settings_service.subscribe(listener)

    # Load settings (should trigger notification)
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

        assert len(notified) >= 1


# ============================================================================
# Test: History Search Integration
# ============================================================================

@pytest.mark.integration
def test_history_search_workflow(history_db):
    """
    Test comprehensive history search workflow.
    """
    history_manager = HistoryManager(db_path=history_db, privacy_mode=False)

    # Add diverse history items
    test_items = [
        HistoryItem(
            timestamp=datetime.now().isoformat(),
            text="Meeting about project kickoff",
            model="large-v3",
            language="en",
            device="cpu",
            tags=["meeting", "project"],
        ),
        HistoryItem(
            timestamp=datetime.now().isoformat(),
            text="Discussion regarding feature implementation",
            model="medium",
            language="en",
            device="cuda",
            tags=["discussion", "feature"],
        ),
        HistoryItem(
            timestamp=datetime.now().isoformat(),
            text="Reunión sobre el proyecto",
            model="large-v3",
            language="es",
            device="cpu",
            tags=["reunión", "proyecto"],
        ),
        HistoryItem(
            timestamp=(datetime.now() - timedelta(days=5)).isoformat() if hasattr(datetime, 'now') else datetime.now().isoformat(),
            text="Daily standup sync",
            model="small",
            language="en",
            device="cpu",
            tags=["standup"],
        ),
    ]

    # Add timedelta import for older items
    from datetime import timedelta
    test_items[3].timestamp = (datetime.now() - timedelta(days=5)).isoformat()

    for item in test_items:
        history_manager.add_item(item, skip_notification=True)

    # Test text search
    results = history_manager.search_by_text("project")
    assert len(results) >= 1
    assert any("project" in item.text.lower() for item in results)

    # Test model search
    results = history_manager.search_by_model("large-v3")
    assert len(results) >= 1

    # Test language search
    results = history_manager.search_by_language("en")
    assert len(results) >= 1

    # Test advanced search
    results = history_manager.advanced_search(
        text_query="project",
        model="large-v3",
        language="en",
    )
    # Should find items matching all criteria


@pytest.mark.integration
def test_history_statistics_workflow(history_db):
    """
    Test history statistics generation.
    """
    history_manager = HistoryManager(db_path=history_db, privacy_mode=False)

    # Add items with known properties
    for i in range(10):
        item = HistoryItem(
            timestamp=datetime.now().isoformat(),
            text=f"Test item {i}",
            model="large-v3" if i % 2 == 0 else "medium",
            language="en" if i % 2 == 0 else "es",
            device="cpu",
        )
        history_manager.add_item(item, skip_notification=True)

    # Get statistics
    stats = history_manager.get_statistics()

    assert stats['total_items'] == 10
    assert stats['today_count'] >= 0
    assert stats['week_count'] == 10
    assert stats['most_used_model'] in ['large-v3', 'medium']
    assert stats['most_used_language'] in ['en', 'es']


# ============================================================================
# Test: Hotkey Integration
# ============================================================================

@pytest.mark.integration
def test_hotkey_transcription_integration(mock_settings):
    """
    Test hotkey manager integration with transcription service.
    """
    with patch('faster_whisper_hotkey.flet_gui.transcription_service.MicrophoneTranscriber') as mock_transcriber_cls:
        mock_transcriber = MagicMock()
        mock_transcriber.is_recording = False
        mock_transcriber.is_transcribing = False

        with patch('faster_whisper_hotkey.flet_gui.transcription_service.MicrophoneTranscriber', return_value=mock_transcriber):
            transcription_service = TranscriptionService(mock_settings)
            hotkey_manager = HotkeyManager(hotkey="pause")

            # Track recording state
            recording_started = False
            recording_stopped = False

            def on_hotkey_press(event):
                nonlocal recording_started, recording_stopped
                if event.hotkey_name == "default":
                    if not transcription_service.is_recording:
                        transcription_service.start_recording()
                        recording_started = True
                    else:
                        transcription_service.stop_recording()
                        recording_stopped = True

            # Register callback
            hotkey_manager.on("hotkey_press", on_hotkey_press)

            # Initialize service
            transcription_service.initialize()

            # Simulate hotkey press
            test_event = Mock()
            test_event.action = "press"
            test_event.hotkey = "pause"
            test_event.hotkey_name = "default"

            # Manually trigger the callback
            on_hotkey_press(test_event)

            assert recording_started is True

            # Simulate release
            on_hotkey_press(test_event)

            assert recording_stopped is True

            transcription_service.shutdown()


@pytest.mark.integration
def test_multiple_services_integration(mock_settings, history_db):
    """
    Test integration of multiple services working together.
    """
    with patch('faster_whisper_hotkey.flet_gui.transcription_service.MicrophoneTranscriber') as mock_transcriber_cls:
        mock_transcriber = MagicMock()
        mock_transcriber.is_recording = False
        mock_transcriber.is_transcribing = False
        mock_transcriber.current_audio_level = 0.5

        with patch('faster_whisper_hotkey.flet_gui.transcription_service.MicrophoneTranscriber', return_value=mock_transcriber):
            # Create all services
            transcription_service = TranscriptionService(mock_settings)
            settings_service = SettingsService()
            history_manager = HistoryManager(db_path=history_db, privacy_mode=False)

            # Initialize settings
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
                )
                mock_load.return_value = mock_settings
                settings_service.load()

            # Track workflow
            workflow_events = []

            # Connect services with callbacks
            def on_transcription(text):
                workflow_events.append(("transcription", text))
                # Add to history
                item = HistoryItem(
                    timestamp=datetime.now().isoformat(),
                    text=text,
                    model="large-v3",
                    language="en",
                    device="cpu",
                )
                history_manager.add_item(item, skip_notification=True)

            transcription_service.on("transcription", on_transcription)

            # Initialize
            transcription_service.initialize()

            # Simulate transcription
            transcription_service._on_transcription("Integration test transcription")

            # Verify workflow
            assert len(workflow_events) == 1
            assert workflow_events[0][1] == "Integration test transcription"

            # Verify history
            history_items = history_manager.get_all()
            assert len(history_items) == 1
            assert history_items[0].text == "Integration test transcription"

            # Search history
            results = history_manager.search_by_text("integration")
            assert len(results) == 1

            transcription_service.shutdown()


# ============================================================================
# Test: Privacy Mode Integration
# ============================================================================

@pytest.mark.integration
def test_privacy_mode_workflow(mock_settings, history_db):
    """
    Test that privacy mode prevents history storage.
    """
    with patch('faster_whisper_hotkey.flet_gui.transcription_service.MicrophoneTranscriber') as mock_transcriber_cls:
        mock_transcriber = MagicMock()
        mock_transcriber.is_recording = False
        mock_transcriber.is_transcribing = False

        with patch('faster_whisper_hotkey.flet_gui.transcription_service.MicrophoneTranscriber', return_value=mock_transcriber):
            # Create history manager with privacy mode enabled
            history_manager = HistoryManager(db_path=history_db, privacy_mode=True)

            # Try to add item
            item = HistoryItem(
                timestamp=datetime.now().isoformat(),
                text="This should not be saved",
                model="large-v3",
                language="en",
                device="cpu",
            )
            item_id = history_manager.add_item(item)

            # Should return None (not saved)
            assert item_id is None

            # Verify no items in history
            items = history_manager.get_all()
            assert len(items) == 0

            # Search should return empty
            results = history_manager.search_by_text("should not")
            assert len(results) == 0

            # Disable privacy mode
            history_manager.set_privacy_mode(False)

            # Now items should be saved
            item2 = HistoryItem(
                timestamp=datetime.now().isoformat(),
                text="This should be saved",
                model="large-v3",
                language="en",
                device="cpu",
            )
            item_id = history_manager.add_item(item2)

            assert item_id is not None

            items = history_manager.get_all()
            assert len(items) == 1


# Add timedelta import at top level for the tests that need it
from datetime import timedelta
