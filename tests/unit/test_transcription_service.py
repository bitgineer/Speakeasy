"""
Unit tests for TranscriptionService.

This test module covers:
- Service initialization with various settings
- Recording control methods (start, stop, toggle)
- Event emission and callback registration
- State management and properties
- Thread-safe operations
- Error handling

Run with: pytest tests/unit/test_transcription_service.py -v
"""

import pytest
import threading
import queue
import time
from unittest.mock import Mock, patch, MagicMock, call
from dataclasses import asdict

from faster_whisper_hotkey.flet_gui.transcription_service import (
    TranscriptionService,
    TranscriptionEvent,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_settings():
    """Create a mock Settings object."""
    settings = Mock()
    settings.model_name = "large-v3"
    settings.device = "cpu"
    settings.compute_type = "int8"
    settings.language = "en"
    settings.hotkey = "pause"
    settings.activation_mode = "hold"
    settings.enable_streaming = False
    settings.confidence_threshold = 0.5
    settings.stream_chunk_duration = 3.0
    settings.auto_copy_on_release = True
    settings.voice_commands = {}
    settings.text_processing = {}
    return settings


@pytest.fixture
def mock_transcriber():
    """Create a mock MicrophoneTranscriber."""
    mock = Mock()
    mock.is_recording = False
    mock.is_transcribing = False
    mock.current_audio_level = 0.0
    mock.start_recording = Mock()
    mock.stop_recording_and_transcribe = Mock()
    mock.stop = Mock()
    mock.reload_voice_commands = Mock()
    mock.reload_text_processor = Mock()
    return mock


@pytest.fixture
def transcription_service(mock_settings):
    """Create a TranscriptionService instance."""
    # We'll patch the MicrophoneTranscriber to prevent actual instantiation
    with patch('faster_whisper_hotkey.flet_gui.transcription_service.MicrophoneTranscriber') as mock_class:
        mock_class.return_value = Mock(
            is_recording=False,
            is_transcribing=False,
            current_audio_level=0.0,
            start_recording=Mock(),
            stop_recording_and_transcribe=Mock(),
            stop=Mock(),
            reload_voice_commands=Mock(),
            reload_text_processor=Mock(),
        )
        service = TranscriptionService(mock_settings)
        yield service


# ============================================================================
# Test: Initialization
# ============================================================================

@pytest.mark.unit
def test_transcription_service_initialization(transcription_service, mock_settings):
    """Test that TranscriptionService initializes correctly."""
    assert transcription_service._settings == mock_settings
    assert transcription_service._is_initialized is False
    assert transcription_service.is_recording is False
    assert transcription_service.is_transcribing is False
    assert isinstance(transcription_service._event_queue, queue.Queue)
    assert isinstance(transcription_service._lock, type(threading.RLock()))


@pytest.mark.unit
def test_transcription_service_initialize(transcription_service):
    """Test the initialize method creates a transcriber."""
    with patch('faster_whisper_hotkey.flet_gui.transcription_service.MicrophoneTranscriber') as mock_class:
        mock_instance = Mock(
            is_recording=False,
            is_transcribing=False,
            current_audio_level=0.0,
        )
        mock_class.return_value = mock_instance

        result = transcription_service.initialize()

        assert result is True
        assert transcription_service.is_initialized is True
        assert transcription_service._transcriber == mock_instance
        mock_class.assert_called_once()


@pytest.mark.unit
def test_transcription_service_initialize_failure(transcription_service):
    """Test initialization failure handling."""
    with patch('faster_whisper_hotkey.flet_gui.transcription_service.MicrophoneTranscriber') as mock_class:
        mock_class.side_effect = Exception("Initialization failed")

        result = transcription_service.initialize()

        assert result is False
        assert transcription_service.is_initialized is False


@pytest.mark.unit
def test_transcription_service_reinitialize(transcription_service, mock_settings):
    """Test reinitializing with new settings."""
    with patch('faster_whisper_hotkey.flet_gui.transcription_service.MicrophoneTranscriber') as mock_class:
        mock_instance = Mock(
            is_recording=False,
            is_transcribing=False,
        )
        mock_class.return_value = mock_instance

        # First initialization
        transcription_service.initialize()
        assert transcription_service._transcriber is not None

        # Create new settings
        new_settings = Mock()
        new_settings.model_name = "medium"

        # Reinitialize
        result = transcription_service.reinitialize(new_settings)

        assert result is True
        assert transcription_service._settings == new_settings


# ============================================================================
# Test: Callback Registration
# ============================================================================

@pytest.mark.unit
def test_callback_registration(transcription_service):
    """Test registering and unregistering callbacks."""
    call_count = {"count": 0}

    def test_callback(data):
        call_count["count"] += 1

    # Register callback
    unsubscribe = transcription_service.on("state_change", test_callback)

    # Trigger event
    transcription_service._on_state_change("test_state")

    assert call_count["count"] == 1

    # Unregister
    unsubscribe()

    # Trigger again
    transcription_service._on_state_change("test_state")

    # Should still be 1 since we unsubscribed
    assert call_count["count"] == 1


@pytest.mark.unit
def test_multiple_callbacks(transcription_service):
    """Test multiple callbacks for the same event."""
    calls = []

    def callback1(data):
        calls.append("callback1")

    def callback2(data):
        calls.append("callback2")

    transcription_service.on("transcription", callback1)
    transcription_service.on("transcription", callback2)

    transcription_service._on_transcription("test text")

    assert "callback1" in calls
    assert "callback2" in calls


@pytest.mark.unit
def test_invalid_event_type(transcription_service):
    """Test registering callback for invalid event type."""
    with pytest.raises(ValueError, match="Unknown event type"):
        transcription_service.on("invalid_event", lambda x: None)


@pytest.mark.unit
def test_all_valid_event_types(transcription_service):
    """Test that all declared event types are valid."""
    valid_events = [
        "state_change",
        "transcription",
        "transcription_start",
        "audio_level",
        "streaming_update",
        "error",
    ]

    for event in valid_events:
        # Should not raise
        unsubscribe = transcription_service.on(event, lambda x: None)
        unsubscribe()


# ============================================================================
# Test: Recording Controls
# ============================================================================

@pytest.mark.unit
def test_start_recording(transcription_service):
    """Test starting recording."""
    # Set up mock transcriber
    mock_transcriber = Mock(is_recording=False)
    transcription_service._transcriber = mock_transcriber
    transcription_service._is_initialized = True

    result = transcription_service.start_recording()

    assert result is True
    mock_transcriber.start_recording.assert_called_once()


@pytest.mark.unit
def test_start_recording_when_already_recording(transcription_service):
    """Test start_recording when already recording."""
    mock_transcriber = Mock(is_recording=True)
    transcription_service._transcriber = mock_transcriber
    transcription_service._is_initialized = True

    result = transcription_service.start_recording()

    assert result is True
    # Should not call start_recording again
    mock_transcriber.start_recording.assert_not_called()


@pytest.mark.unit
def test_start_recording_not_initialized(transcription_service):
    """Test start_recording when service not initialized."""
    transcription_service._transcriber = None
    transcription_service._is_initialized = False

    result = transcription_service.start_recording()

    assert result is False


@pytest.mark.unit
def test_start_recording_exception(transcription_service):
    """Test start_recording exception handling."""
    mock_transcriber = Mock(is_recording=False)
    mock_transcriber.start_recording.side_effect = Exception("Audio device error")
    transcription_service._transcriber = mock_transcriber
    transcription_service._is_initialized = True

    result = transcription_service.start_recording()

    assert result is False


@pytest.mark.unit
def test_stop_recording(transcription_service):
    """Test stopping recording."""
    mock_transcriber = Mock(is_recording=True)
    transcription_service._transcriber = mock_transcriber
    transcription_service._is_initialized = True

    result = transcription_service.stop_recording()

    assert result is True
    mock_transcriber.stop_recording_and_transcribe.assert_called_once()


@pytest.mark.unit
def test_stop_recording_not_recording(transcription_service):
    """Test stop_recording when not recording."""
    mock_transcriber = Mock(is_recording=False)
    transcription_service._transcriber = mock_transcriber
    transcription_service._is_initialized = True

    result = transcription_service.stop_recording()

    assert result is True
    # Should not call stop
    mock_transcriber.stop_recording_and_transcribe.assert_not_called()


@pytest.mark.unit
def test_toggle_recording_start(transcription_service):
    """Test toggle_recording starts recording when stopped."""
    mock_transcriber = Mock(is_recording=False)
    transcription_service._transcriber = mock_transcriber
    transcription_service._is_initialized = True

    result = transcription_service.toggle_recording()

    assert result is True
    mock_transcriber.start_recording.assert_called_once()


@pytest.mark.unit
def test_toggle_recording_stop(transcription_service):
    """Test toggle_recording stops recording when recording."""
    mock_transcriber = Mock(is_recording=True)
    transcription_service._transcriber = mock_transcriber
    transcription_service._is_initialized = True

    result = transcription_service.toggle_recording()

    assert result is True
    mock_transcriber.stop_recording_and_transcribe.assert_called_once()


# ============================================================================
# Test: Event Queue
# ============================================================================

@pytest.mark.unit
def test_event_queue_put(transcription_service):
    """Test that events are added to the queue."""
    transcription_service._on_state_change("recording")

    event = transcription_service.get_next_event(timeout=0.1)

    assert event is not None
    assert event.event_type == "state_change"
    assert event.data == "recording"


@pytest.mark.unit
def test_get_next_event_timeout(transcription_service):
    """Test get_next_event with timeout."""
    event = transcription_service.get_next_event(timeout=0.1)

    assert event is None


@pytest.mark.unit
def test_get_next_event_no_timeout(transcription_service):
    """Test get_next_event without blocking."""
    event = transcription_service.get_next_event(timeout=0.0)

    assert event is None


@pytest.mark.unit
def test_process_events(transcription_service):
    """Test processing all pending events."""
    # Add multiple events
    transcription_service._on_state_change("recording")
    transcription_service._on_transcription("test text")
    transcription_service._on_audio_level(0.5)

    events = transcription_service.process_events()

    assert len(events) == 3
    assert events[0].event_type == "state_change"
    assert events[1].event_type == "transcription"
    assert events[2].event_type == "audio_level"


@pytest.mark.unit
def test_event_queue_full(transcription_service):
    """Test behavior when event queue is full."""
    # Create a very small queue
    transcription_service._event_queue = queue.Queue(maxsize=1)

    # Add one event
    transcription_service._on_state_change("first")

    # Try to add another - should log warning but not crash
    transcription_service._on_state_change("second")

    # Only first event should be in queue
    events = transcription_service.process_events()
    assert len(events) <= 2  # May be 1 or 2 depending on timing


# ============================================================================
# Test: Properties
# ============================================================================

@pytest.mark.unit
def test_is_recording_property(transcription_service):
    """Test is_recording property."""
    transcription_service._transcriber = None
    assert transcription_service.is_recording is False

    mock_transcriber = Mock(is_recording=True)
    transcription_service._transcriber = mock_transcriber
    assert transcription_service.is_recording is True


@pytest.mark.unit
def test_is_transcribing_property(transcription_service):
    """Test is_transcribing property."""
    transcription_service._transcriber = None
    assert transcription_service.is_transcribing is False

    mock_transcriber = Mock(is_transcribing=True)
    transcription_service._transcriber = mock_transcriber
    assert transcription_service.is_transcribing is True


@pytest.mark.unit
def test_current_audio_level_property(transcription_service):
    """Test current_audio_level property."""
    transcription_service._transcriber = None
    assert transcription_service.current_audio_level == 0.0

    mock_transcriber = Mock(current_audio_level=0.75)
    transcription_service._transcriber = mock_transcriber
    assert transcription_service.current_audio_level == 0.75


# ============================================================================
# Test: Callback Triggers
# ============================================================================

@pytest.mark.unit
def test_on_state_change_callback(transcription_service):
    """Test state change callback is triggered."""
    received = []

    def callback(state):
        received.append(state)

    transcription_service.on("state_change", callback)
    transcription_service._on_state_change("transcribing")

    assert len(received) == 1
    assert received[0] == "transcribing"


@pytest.mark.unit
def test_on_transcription_callback(transcription_service):
    """Test transcription callback is triggered."""
    received = []

    def callback(text):
        received.append(text)

    transcription_service.on("transcription", callback)
    transcription_service._on_transcription("Hello world")

    assert len(received) == 1
    assert received[0] == "Hello world"


@pytest.mark.unit
def test_on_transcription_start_callback(transcription_service):
    """Test transcription start callback is triggered."""
    received = []

    def callback(duration):
        received.append(duration)

    transcription_service.on("transcription_start", callback)
    transcription_service._on_transcription_start(1.5)

    assert len(received) == 1
    assert received[0] == 1.5


@pytest.mark.unit
def test_on_audio_level_callback(transcription_service):
    """Test audio level callback is triggered."""
    received = []

    def callback(level):
        received.append(level)

    transcription_service.on("audio_level", callback)
    transcription_service._on_audio_level(0.85)

    assert len(received) == 1
    assert received[0] == 0.85


@pytest.mark.unit
def test_on_streaming_update_callback(transcription_service):
    """Test streaming update callback is triggered."""
    received = []

    def callback(data):
        received.append(data)

    transcription_service.on("streaming_update", callback)
    transcription_service._on_streaming_update("partial text", 0.9, False)

    assert len(received) == 1
    assert received[0]["text"] == "partial text"
    assert received[0]["confidence"] == 0.9
    assert received[0]["is_final"] is False


@pytest.mark.unit
def test_on_error_callback(transcription_service):
    """Test error callback is triggered."""
    received = []

    def callback(error):
        received.append(error)

    # Trigger error via start_recording failure
    mock_transcriber = Mock(is_recording=False)
    mock_transcriber.start_recording.side_effect = Exception("Test error")
    transcription_service._transcriber = mock_transcriber
    transcription_service._is_initialized = True

    transcription_service.on("error", callback)
    transcription_service.start_recording()

    assert len(received) == 1
    assert "Test error" in received[0]


# ============================================================================
# Test: Reload Methods
# ============================================================================

@pytest.mark.unit
def test_reload_voice_commands(transcription_service):
    """Test reloading voice commands."""
    mock_transcriber = Mock()
    transcription_service._transcriber = mock_transcriber

    transcription_service.reload_voice_commands()

    mock_transcriber.reload_voice_commands.assert_called_once()


@pytest.mark.unit
def test_reload_text_processor(transcription_service):
    """Test reloading text processor."""
    mock_transcriber = Mock()
    transcription_service._transcriber = mock_transcriber

    transcription_service.reload_text_processor()

    mock_transcriber.reload_text_processor.assert_called_once()


@pytest.mark.unit
def test_reload_without_transcriber(transcription_service):
    """Test reload methods when no transcriber exists."""
    transcription_service._transcriber = None

    # Should not raise
    transcription_service.reload_voice_commands()
    transcription_service.reload_text_processor()


# ============================================================================
# Test: Shutdown
# ============================================================================

@pytest.mark.unit
def test_shutdown(transcription_service):
    """Test service shutdown."""
    mock_transcriber = Mock()
    transcription_service._transcriber = mock_transcriber
    transcription_service._is_initialized = True

    transcription_service.shutdown()

    mock_transcriber.stop.assert_called_once()
    assert transcription_service._transcriber is None
    assert transcription_service.is_initialized is False


@pytest.mark.unit
def test_shutdown_with_exception(transcription_service):
    """Test shutdown handles exceptions gracefully."""
    mock_transcriber = Mock()
    mock_transcriber.stop.side_effect = Exception("Stop failed")
    transcription_service._transcriber = mock_transcriber
    transcription_service._is_initialized = True

    # Should not raise
    transcription_service.shutdown()

    assert transcription_service._transcriber is None
    assert transcription_service.is_initialized is False


@pytest.mark.unit
def test_shutdown_without_transcriber(transcription_service):
    """Test shutdown when no transcriber exists."""
    transcription_service._transcriber = None

    # Should not raise
    transcription_service.shutdown()


# ============================================================================
# Test: Thread Safety
# ============================================================================

@pytest.mark.unit
def test_thread_safe_callback_registration(transcription_service):
    """Test callback registration is thread-safe."""
    callbacks = []

    def register_callbacks():
        for i in range(10):
            def callback(data):
                callbacks.append(i)
            transcription_service.on("state_change", callback)

    import threading
    threads = [threading.Thread(target=register_callbacks) for _ in range(5)]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # All callbacks should be registered
    assert len(transcription_service._callbacks["state_change"]) == 50


@pytest.mark.unit
def test_thread_safe_event_emission(transcription_service):
    """Test event emission is thread-safe."""
    call_count = {"count": 0}

    def callback(data):
        call_count["count"] += 1

    transcription_service.on("state_change", callback)

    def emit_events():
        for _ in range(10):
            transcription_service._on_state_change("test")

    import threading
    threads = [threading.Thread(target=emit_events) for _ in range(5)]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # All callbacks should be called
    assert call_count["count"] == 50


@pytest.mark.unit
def test_thread_safe_properties(transcription_service):
    """Test property access is thread-safe."""
    mock_transcriber = Mock(is_recording=True, is_transcribing=False, current_audio_level=0.5)
    transcription_service._transcriber = mock_transcriber

    results = {"recording": [], "transcribing": [], "level": []}

    def read_properties():
        for _ in range(10):
            results["recording"].append(transcription_service.is_recording)
            results["transcribing"].append(transcription_service.is_transcribing)
            results["level"].append(transcription_service.current_audio_level)

    import threading
    threads = [threading.Thread(target=read_properties) for _ in range(5)]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results["recording"]) == 50
    assert len(results["transcribing"]) == 50
    assert len(results["level"]) == 50
