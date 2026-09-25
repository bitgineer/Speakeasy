"""Tests for utils.focused_app.detect_focused_app."""

from speakeasy.core.processing import FocusedApp
from speakeasy.utils import focused_app


def test_unknown_platform_returns_none(monkeypatch):
    monkeypatch.setattr(focused_app.sys, "platform", "sunos5")

    assert focused_app.detect_focused_app() is None


def test_a_raising_probe_returns_none(monkeypatch):
    def boom():
        raise OSError("no desktop session")

    monkeypatch.setattr(focused_app.sys, "platform", "win32")
    monkeypatch.setattr(focused_app, "_detect_windows", boom)

    assert focused_app.detect_focused_app() is None


def test_a_successful_probe_is_returned(monkeypatch):
    app = FocusedApp(key="slack", title="general")

    monkeypatch.setattr(focused_app.sys, "platform", "darwin")
    monkeypatch.setattr(focused_app, "_detect_macos", lambda: app)

    assert focused_app.detect_focused_app() == app


def test_linux_dispatches_to_the_linux_probe(monkeypatch):
    app = FocusedApp(key="code", title="file.py")

    monkeypatch.setattr(focused_app.sys, "platform", "linux")
    monkeypatch.setattr(focused_app, "_detect_linux", lambda: app)

    assert focused_app.detect_focused_app() == app
