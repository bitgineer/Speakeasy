"""
Regression tests for insert_text's direct-typing branch.

Bug: insert_text(text, use_clipboard=False) fell through silently instead of
calling type_text. The clipboard path must keep working unchanged.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.utils.paste import insert_text


def test_use_clipboard_false_types_directly(monkeypatch):
    typed = []
    monkeypatch.setattr(
        "speakeasy.utils.paste.type_text",
        lambda text, interval=0.01: typed.append(text),
    )

    insert_text("hello", use_clipboard=False)

    assert typed == ["hello"]


def test_use_clipboard_true_uses_clipboard_path(monkeypatch):
    events = []
    import speakeasy.utils.clipboard as clipboard

    def set_clipboard(text):
        events.append(("set", text))
        return True

    monkeypatch.setattr(clipboard, "backup_clipboard", lambda: events.append("backup"))
    monkeypatch.setattr(clipboard, "set_clipboard", set_clipboard)
    monkeypatch.setattr(clipboard, "restore_clipboard", lambda: events.append("restore"))
    monkeypatch.setattr(
        "speakeasy.utils.paste.paste_to_active_window",
        lambda: events.append("paste"),
    )
    monkeypatch.setattr(
        "speakeasy.utils.paste.type_text",
        lambda text, interval=0.01: events.append(("type", text)),
    )

    insert_text("hello", use_clipboard=True)

    assert events == ["backup", ("set", "hello"), "paste", "restore"]
