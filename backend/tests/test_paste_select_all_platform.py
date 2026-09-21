"""
Regression tests for select_all_and_paste platform handling.

Bug: select_all_and_paste always sent Ctrl+A. macOS needs Cmd+A. Platform
detection follows paste_to_active_window: _is_windows()/_is_linux(), else macOS.
"""

import sys
from pathlib import Path

import pynput.keyboard as pynput_keyboard

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.utils import paste


class RecordingKeyboard:
    def __init__(self):
        self.events = []

    def pressed(self, key):
        recorder = self

        class _Context:
            def __enter__(self):
                recorder.events.append(("press", key))

            def __exit__(self, *exc):
                recorder.events.append(("release", key))
                return False

        return _Context()

    def press(self, key):
        self.events.append(("press", key))

    def release(self, key):
        self.events.append(("release", key))


def run_select_all(monkeypatch, *, windows, linux):
    keyboard = RecordingKeyboard()
    monkeypatch.setattr(pynput_keyboard, "Controller", lambda: keyboard)
    monkeypatch.setattr(paste, "_is_windows", lambda: windows)
    monkeypatch.setattr(paste, "_is_linux", lambda: linux)

    paste.select_all_and_paste()

    return [key for action, key in keyboard.events if action == "press"]


def test_macos_sends_cmd_a(monkeypatch):
    pressed = run_select_all(monkeypatch, windows=False, linux=False)

    assert pynput_keyboard.Key.cmd in pressed
    assert pynput_keyboard.Key.ctrl not in pressed
    assert "a" in pressed


def test_windows_sends_ctrl_a(monkeypatch):
    pressed = run_select_all(monkeypatch, windows=True, linux=False)

    assert pynput_keyboard.Key.ctrl in pressed
    assert pynput_keyboard.Key.cmd not in pressed
    assert "a" in pressed
