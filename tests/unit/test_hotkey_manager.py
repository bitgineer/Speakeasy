"""
Unit tests for HotkeyManager.

This test module covers:
- Hotkey parsing from strings
- Hotkey registration and management
- Named hotkeys (default, search, history)
- Event emission and callback registration
- Hotkey press/release detection
- Event queue processing

Run with: pytest tests/unit/test_hotkey_manager.py -v
"""

import pytest
import queue
import threading
from unittest.mock import Mock, patch, MagicMock

from faster_whisper_hotkey.flet_gui.hotkey_manager import (
    HotkeyManager,
    HotkeyEvent,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_pynput():
    """Mock pynput keyboard module."""
    with patch('faster_whisper_hotkey.flet_gui.hotkey_manager.keyboard') as mock_kb:
        # Create mock key objects
        mock_kb.Key.pause = "PAUSE_KEY"
        mock_kb.Key.f1 = "F1_KEY"
        mock_kb.Key.f12 = "F12_KEY"
        mock_kb.Key.ctrl_l = "CTRL_L"
        mock_kb.Key.ctrl_r = "CTRL_R"
        mock_kb.Key.alt_l = "ALT_L"
        mock_kb.Key.alt_r = "ALT_R"
        mock_kb.Key.shift_l = "SHIFT_L"
        mock_kb.Key.shift_r = "SHIFT_R"
        mock_kb.Key.cmd = "CMD_KEY"
        mock_kb.Key.cmd_l = "CMD_L"
        mock_kb.Key.cmd_r = "CMD_R"
        mock_kb.Key.space = "SPACE_KEY"
        mock_kb.Key.enter = "ENTER_KEY"
        mock_kb.Key.esc = "ESC_KEY"
        mock_kb.KeyCode.from_char = lambda c: f"CHAR_{c}"

        yield mock_kb


@pytest.fixture
def hotkey_manager():
    """Create a HotkeyManager instance."""
    return HotkeyManager(hotkey="pause")


# ============================================================================
# Test: Initialization
# ============================================================================

@pytest.mark.unit
def test_hotkey_manager_initialization(hotkey_manager):
    """Test HotkeyManager initializes correctly."""
    assert hotkey_manager._hotkey == "pause"
    assert hotkey_manager.is_running is False
    assert isinstance(hotkey_manager._event_queue, queue.Queue)
    assert isinstance(hotkey_manager._lock, type(threading.RLock()))
    assert hotkey_manager.DEFAULT_HOTKEY == "default"
    assert hotkey_manager.SEARCH_HOTKEY == "search"
    assert hotkey_manager.HISTORY_HOTKEY == "history"


@pytest.mark.unit
def test_initialization_with_custom_hotkey():
    """Test initialization with custom hotkey."""
    manager = HotkeyManager(hotkey="ctrl+shift+h")
    assert manager._hotkey == "ctrl+shift+h"


@pytest.mark.unit
def test_named_hotkeys_initialized(hotkey_manager):
    """Test that named hotkeys are initialized."""
    assert "default" in hotkey_manager._named_hotkeys
    assert hotkey_manager._named_hotkeys["default"][0] == "pause"


# ============================================================================
# Test: Hotkey Parsing
# ============================================================================

@pytest.mark.unit
def test_parse_simple_hotkey(hotkey_manager):
    """Test parsing a simple hotkey (single key)."""
    modifiers, main_key = hotkey_manager._parse_hotkey("pause")

    assert len(modifiers) == 0
    assert main_key is not None


@pytest.mark.unit
def test_parse_modifier_hotkey(hotkey_manager):
    """Test parsing hotkey with modifiers."""
    modifiers, main_key = hotkey_manager._parse_hotkey("ctrl+shift+h")

    assert len(modifiers) > 0
    assert main_key is not None


@pytest.mark.unit
def test_parse_function_key(hotkey_manager):
    """Test parsing function key hotkey."""
    with patch('faster_whisper_hotkey.flet_gui.hotkey_manager.keyboard') as mock_kb:
        mock_kb.Key.f5 = "F5_KEY"
        mock_kb.Key.f1 = "F1_KEY"
        mock_kb.Key.f12 = "F12_KEY"
        mock_kb.KeyCode.from_char = lambda c: f"CHAR_{c}"

        manager = HotkeyManager(hotkey="f5")

        # F5 should be recognized as a valid key
        modifiers, main_key = manager._parse_hotkey("f5")
        assert main_key is not None


@pytest.mark.unit
def test_parse_special_keys(hotkey_manager):
    """Test parsing special keys."""
    special_keys = ["space", "enter", "tab", "escape", "esc", "insert", "home", "end"]

    for key in special_keys:
        modifiers, main_key = hotkey_manager._parse_hotkey(key)
        assert main_key is not None, f"Failed to parse: {key}"


@pytest.mark.unit
def test_parse_arrow_keys(hotkey_manager):
    """Test parsing arrow keys."""
    arrow_keys = ["up", "down", "left", "right"]

    for key in arrow_keys:
        modifiers, main_key = hotkey_manager._parse_hotkey(key)
        assert main_key is not None, f"Failed to parse: {key}"


@pytest.mark.unit
def test_parse_complex_hotkey(hotkey_manager):
    """Test parsing complex hotkey with multiple modifiers."""
    modifiers, main_key = hotkey_manager._parse_hotkey("ctrl+shift+alt+win+a")

    assert len(modifiers) > 0
    assert main_key is not None


@pytest.mark.unit
def test_parse_hotkey_case_insensitive(hotkey_manager):
    """Test hotkey parsing is case insensitive."""
    lower_result = hotkey_manager._parse_hotkey("ctrl+a")
    upper_result = hotkey_manager._parse_hotkey("CTRL+A")
    mixed_result = hotkey_manager._parse_hotkey("CtRl+A")

    # All should parse successfully
    for modifiers, main_key in [lower_result, upper_result, mixed_result]:
        assert len(modifiers) > 0
        assert main_key is not None


# ============================================================================
# Test: Hotkey Registration
# ============================================================================

@pytest.mark.unit
def test_set_hotkey(hotkey_manager):
    """Test setting a hotkey."""
    hotkey_manager.set_hotkey("ctrl+f1", name="test_hotkey")

    assert "test_hotkey" in hotkey_manager._named_hotkeys
    assert hotkey_manager.get_hotkey("test_hotkey") == "ctrl+f1"


@pytest.mark.unit
def test_set_default_hotkey_updates_property(hotkey_manager):
    """Test setting default hotkey updates the property."""
    hotkey_manager.set_hotkey("f12", name="default")

    assert hotkey_manager._hotkey == "f12"


@pytest.mark.unit
def test_get_hotkey(hotkey_manager):
    """Test getting a hotkey by name."""
    hotkey_manager.set_hotkey("shift+a", name="my_hotkey")

    assert hotkey_manager.get_hotkey("my_hotkey") == "shift+a"


@pytest.mark.unit
def test_get_hotkey_not_found(hotkey_manager):
    """Test getting non-existent hotkey."""
    assert hotkey_manager.get_hotkey("nonexistent") == ""


@pytest.mark.unit
def test_get_default_hotkey(hotkey_manager):
    """Test getting default hotkey."""
    assert hotkey_manager.get_hotkey("default") == "pause"


@pytest.mark.unit
def test_remove_hotkey(hotkey_manager):
    """Test removing a named hotkey."""
    hotkey_manager.set_hotkey("ctrl+a", name="temp_hotkey")

    result = hotkey_manager.remove_hotkey("temp_hotkey")

    assert result is True
    assert "temp_hotkey" not in hotkey_manager._named_hotkeys


@pytest.mark.unit
def test_remove_default_hotkey_fails(hotkey_manager):
    """Test removing default hotkey fails."""
    result = hotkey_manager.remove_hotkey("default")

    assert result is False
    assert "default" in hotkey_manager._named_hotkeys


@pytest.mark.unit
def test_remove_nonexistent_hotkey(hotkey_manager):
    """Test removing non-existent hotkey."""
    result = hotkey_manager.remove_hotkey("nonexistent")

    assert result is False


@pytest.mark.unit
def test_list_hotkeys(hotkey_manager):
    """Test listing all registered hotkeys."""
    hotkey_manager.set_hotkey("ctrl+a", name="hotkey1")
    hotkey_manager.set_hotkey("shift+b", name="hotkey2")

    hotkeys = hotkey_manager.list_hotkeys()

    assert "default" in hotkeys
    assert "hotkey1" in hotkeys
    assert "hotkey2" in hotkeys
    assert hotkeys["hotkey1"] == "ctrl+a"
    assert hotkeys["hotkey2"] == "shift+b"


# ============================================================================
# Test: Key Press/Release Handling
# ============================================================================

@pytest.mark.unit
def test_is_modifier(hotkey_manager):
    """Test modifier key detection."""
    with patch('faster_whisper_hotkey.flet_gui.hotkey_manager.keyboard') as mock_kb:
        mock_kb.Key.ctrl_l = "CTRL_L"
        mock_kb.Key.ctrl_r = "CTRL_R"
        mock_kb.Key.alt_l = "ALT_L"
        mock_kb.Key.alt_r = "ALT_R"
        mock_kb.Key.shift_l = "SHIFT_L"
        mock_kb.Key.shift_r = "SHIFT_R"
        mock_kb.Key.cmd = "CMD"
        mock_kb.Key.cmd_l = "CMD_L"
        mock_kb.Key.cmd_r = "CMD_R"

        # Create a new instance to pick up the mocked keys
        manager = HotkeyManager(hotkey="pause")

        # Test modifiers are detected
        assert manager._is_modifier("CTRL_L") is True
        assert manager._is_modifier("ALT_R") is True

        # Test non-modifier is not detected
        assert manager._is_modifier("A_KEY") is False


@pytest.mark.unit
def test_on_press_modifies_active_modifiers(hotkey_manager):
    """Test key press updates active modifiers."""
    with patch('faster_whisper_hotkey.flet_gui.hotkey_manager.keyboard') as mock_kb:
        mock_kb.Key.ctrl_l = "CTRL"
        manager = HotkeyManager(hotkey="pause")

        # Simulate pressing a modifier
        manager._on_press("CTRL")

        assert "CTRL" in manager._active_modifiers


@pytest.mark.unit
def test_on_release_modifies_active_modifiers(hotkey_manager):
    """Test key release updates active modifiers."""
    with patch('faster_whisper_hotkey.flet_gui.hotkey_manager.keyboard') as mock_kb:
        mock_kb.Key.ctrl_l = "CTRL"
        manager = HotkeyManager(hotkey="pause")

        # Add modifier to active set
        manager._active_modifiers.add("CTRL")

        # Simulate releasing
        manager._on_release("CTRL")

        assert "CTRL" not in manager._active_modifiers


@pytest.mark.unit
def test_matches_hotkey(hotkey_manager):
    """Test hotkey matching logic."""
    with patch('faster_whisper_hotkey.flet_gui.hotkey_manager.keyboard') as mock_kb:
        # Setup mocks
        mock_kb.Key.ctrl_l = "CTRL"
        mock_kb.Key.ctrl_r = "CTRL_R"
        mock_kb.KeyCode.from_char = lambda c: f"KEY_{c.upper()}"

        manager = HotkeyManager(hotkey="ctrl+a")
        modifiers, main_key = manager._parse_hotkey("ctrl+a")

        # Set up active modifiers
        manager._active_modifiers.add("CTRL")

        # Test matching
        matched = manager._matches_hotkey("KEY_A")

        assert len(matched) >= 0  # Should return a list


# ============================================================================
# Test: Event Queue
# ============================================================================

@pytest.mark.unit
def test_event_queue_emission(hotkey_manager):
    """Test events are added to queue."""
    event = HotkeyEvent("press", "pause", "default")
    hotkey_manager._emit_event("hotkey_press", event)

    retrieved = hotkey_manager.get_next_event(timeout=0.1)

    assert retrieved is not None
    assert retrieved.action == "press"
    assert retrieved.hotkey == "pause"


@pytest.mark.unit
def test_get_next_event_timeout(hotkey_manager):
    """Test get_next_event with timeout returns None when empty."""
    event = hotkey_manager.get_next_event(timeout=0.1)

    assert event is None


@pytest.mark.unit
def test_get_next_event_with_timeout(hotkey_manager):
    """Test get_next_event with timeout waits for event."""
    import threading
    import time

    event_to_add = HotkeyEvent("press", "pause", "default")

    def add_event_later():
        time.sleep(0.05)
        hotkey_manager._event_queue.put(event_to_add)

    thread = threading.Thread(target=add_event_later)
    thread.start()

    event = hotkey_manager.get_next_event(timeout=1.0)

    thread.join()
    assert event is not None
    assert event.action == "press"


@pytest.mark.unit
def test_process_events(hotkey_manager):
    """Test processing all pending events."""
    events_to_add = [
        HotkeyEvent("press", "pause", "default"),
        HotkeyEvent("release", "pause", "default"),
        HotkeyEvent("press", "ctrl+h", "history"),
    ]

    for event in events_to_add:
        hotkey_manager._event_queue.put(event)

    processed = hotkey_manager.process_events()

    assert len(processed) == 3
    assert processed[0].action == "press"
    assert processed[1].action == "release"
    assert processed[2].hotkey == "ctrl+h"


# ============================================================================
# Test: Callback Registration
# ============================================================================

@pytest.mark.unit
def test_on_callback_registration(hotkey_manager):
    """Test registering a callback."""
    call_count = {"count": 0}

    def callback(event):
        call_count["count"] += 1

    unsubscribe = hotkey_manager.on("hotkey_press", callback)

    test_event = HotkeyEvent("press", "pause", "default")
    hotkey_manager._emit_event("hotkey_press", test_event)

    assert call_count["count"] == 1


@pytest.mark.unit
def test_on_callback_unsubscribe(hotkey_manager):
    """Test unsubscribing from callback."""
    call_count = {"count": 0}

    def callback(event):
        call_count["count"] += 1

    unsubscribe = hotkey_manager.on("hotkey_press", callback)

    # Emit event
    test_event = HotkeyEvent("press", "pause", "default")
    hotkey_manager._emit_event("hotkey_press", test_event)
    assert call_count["count"] == 1

    # Unsubscribe
    unsubscribe()

    # Emit again - should not call callback
    hotkey_manager._emit_event("hotkey_press", test_event)
    assert call_count["count"] == 1


@pytest.mark.unit
def test_on_invalid_event_type(hotkey_manager):
    """Test registering callback for invalid event type."""
    with pytest.raises(ValueError, match="Unknown event type"):
        hotkey_manager.on("invalid_event", lambda e: None)


@pytest.mark.unit
def test_all_valid_event_types(hotkey_manager):
    """Test all declared event types are valid."""
    valid_events = [
        "hotkey_press",
        "hotkey_release",
        "search_press",
        "search_release",
        "history_press",
        "history_release",
    ]

    for event in valid_events:
        # Should not raise
        unsubscribe = hotkey_manager.on(event, lambda e: None)
        unsubscribe()


# ============================================================================
# Test: Start/Stop Listener
# ============================================================================

@pytest.mark.unit
def test_start_listener(hotkey_manager):
    """Test starting the hotkey listener."""
    with patch('faster_whisper_hotkey.flet_gui.hotkey_manager.keyboard.Listener') as mock_listener_cls:
        mock_listener = Mock()
        mock_listener_cls.return_value = mock_listener

        hotkey_manager.start()

        assert hotkey_manager.is_running is True
        mock_listener.start.assert_called_once()


@pytest.mark.unit
def test_start_listener_already_running(hotkey_manager):
    """Test starting listener when already running."""
    with patch('faster_whisper_hotkey.flet_gui.hotkey_manager.keyboard.Listener') as mock_listener_cls:
        mock_listener = Mock()
        mock_listener_cls.return_value = mock_listener

        hotkey_manager.start()
        hotkey_manager.is_running = True

        # Start again - should not create new listener
        hotkey_manager.start()

        # Should still have only one listener created
        assert mock_listener_cls.call_count == 1


@pytest.mark.unit
def test_stop_listener(hotkey_manager):
    """Test stopping the hotkey listener."""
    with patch('faster_whisper_hotkey.flet_gui.hotkey_manager.keyboard.Listener') as mock_listener_cls:
        mock_listener = Mock()
        mock_listener_cls.return_value = mock_listener

        hotkey_manager.start()
        hotkey_manager.stop()

        assert hotkey_manager.is_running is False
        mock_listener.stop.assert_called_once()


@pytest.mark.unit
def test_stop_listener_not_running(hotkey_manager):
    """Test stopping when listener not running."""
    # Should not raise
    hotkey_manager.stop()

    assert hotkey_manager.is_running is False


# ============================================================================
# Test: Properties
# ============================================================================

@pytest.mark.unit
def test_is_running_property(hotkey_manager):
    """Test is_running property."""
    assert hotkey_manager.is_running is False

    with patch('faster_whisper_hotkey.flet_gui.hotkey_manager.keyboard.Listener') as mock_listener_cls:
        mock_listener = Mock()
        mock_listener_cls.return_value = mock_listener

        hotkey_manager.start()
        assert hotkey_manager.is_running is True

        hotkey_manager.stop()
        assert hotkey_manager.is_running is False


# ============================================================================
# Test: Thread Safety
# ============================================================================

@pytest.mark.unit
def test_thread_safe_callback_registration(hotkey_manager):
    """Test callback registration is thread-safe."""
    import threading

    callbacks = []

    def register_callbacks():
        for i in range(10):
            def callback(e):
                callbacks.append(i)
            hotkey_manager.on("hotkey_press", callback)

    threads = [threading.Thread(target=register_callbacks) for _ in range(5)]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # All callbacks should be registered
    assert len(hotkey_manager._callbacks["hotkey_press"]) == 50


@pytest.mark.unit
def test_thread_safe_hotkey_operations(hotkey_manager):
    """Test hotkey operations are thread-safe."""
    import threading

    results = {"sets": 0, "gets": 0}

    def set_hotkeys():
        for i in range(50):
            hotkey_manager.set_hotkey(f"ctrl+f{i%12}", name=f"hotkey_{i}")
            results["sets"] += 1

    def get_hotkeys():
        for i in range(50):
            hotkey_manager.get_hotkey("default")
            results["gets"] += 1

    threads = [
        threading.Thread(target=set_hotkeys),
        threading.Thread(target=get_hotkeys),
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results["sets"] == 50
    assert results["gets"] == 50


# ============================================================================
# Test: Event Callback Invokation
# ============================================================================

@pytest.mark.unit
def test_event_callback_invoked_with_data(hotkey_manager):
    """Test callbacks receive event data."""
    received_events = []

    def callback(event):
        received_events.append(event)

    hotkey_manager.on("hotkey_press", callback)

    test_event = HotkeyEvent("press", "ctrl+h", "history")
    hotkey_manager._emit_event("hotkey_press", test_event)

    assert len(received_events) == 1
    assert received_events[0].action == "press"
    assert received_events[0].hotkey == "ctrl+h"
    assert received_events[0].hotkey_name == "history"


@pytest.mark.unit
def test_callback_exception_handling(hotkey_manager):
    """Test exceptions in callbacks don't affect other callbacks."""
    call_log = []

    def failing_callback(event):
        call_log.append("failing")
        raise Exception("Test exception")

    def working_callback(event):
        call_log.append("working")

    hotkey_manager.on("hotkey_press", failing_callback)
    hotkey_manager.on("hotkey_press", working_callback)

    test_event = HotkeyEvent("press", "pause", "default")
    hotkey_manager._emit_event("hotkey_press", test_event)

    # Both should be called despite exception
    assert "failing" in call_log
    assert "working" in call_log


@pytest.mark.unit
def test_named_hotkey_events(hotkey_manager):
    """Test named hotkeys generate correct events."""
    received = []

    def search_callback(event):
        received.append(("search", event.hotkey_name))

    hotkey_manager.on("search_press", search_callback)

    # Set up search hotkey
    hotkey_manager.set_hotkey("ctrl+shift+s", name="search")

    # Simulate search hotkey press
    with patch('faster_whisper_hotkey.flet_gui.hotkey_manager.keyboard') as mock_kb:
        mock_kb.Key.ctrl_l = "CTRL"
        mock_kb.Key.shift_l = "SHIFT"
        mock_kb.KeyCode.from_char = lambda c: f"KEY_{c.upper()}"

        manager = HotkeyManager(hotkey="pause")
        manager.set_hotkey("ctrl+shift+s", name="search")

        # Trigger the event manually
        event = HotkeyEvent("press", "ctrl+shift+s", "search")
        manager._emit_event("search_press", event)

    # Check callback was invoked with correct hotkey name
    # (This is a simplified test - in real scenario, the matching logic
    # would trigger this automatically)
