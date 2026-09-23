"""Tests for the AppSettings processing-group uniqueness validator."""

import pytest
from pydantic import ValidationError

from speakeasy.services.settings import (
    AppSettings,
    HotkeyBinding,
    LlmProvider,
    ToneProfile,
)


def test_duplicate_provider_ids_are_rejected():
    with pytest.raises(ValidationError, match="Provider ids must be unique"):
        AppSettings(providers=[LlmProvider(id="p"), LlmProvider(id="p")])


def test_duplicate_tone_names_are_rejected():
    with pytest.raises(ValidationError, match="Tone profile names must be unique"):
        AppSettings(
            tone_profiles=[ToneProfile(name="Slack"), ToneProfile(name="Slack")]
        )


def test_duplicate_hotkey_accelerators_are_rejected():
    with pytest.raises(ValidationError, match="Hotkey accelerators must be unique"):
        AppSettings(
            hotkeys=[
                HotkeyBinding(accelerator="ctrl+shift+space"),
                HotkeyBinding(accelerator="ctrl+shift+space"),
            ]
        )


def test_dangling_active_provider_id_is_allowed():
    """A deleted provider must not reset the file through the load fallback."""
    settings = AppSettings(active_provider_id="deleted", providers=[])

    assert settings.active_provider_id == "deleted"


def test_distinct_groups_are_accepted():
    settings = AppSettings(
        providers=[LlmProvider(id="a"), LlmProvider(id="b")],
        tone_profiles=[ToneProfile(name="A"), ToneProfile(name="B")],
        hotkeys=[HotkeyBinding(accelerator="ctrl+shift+space")],
    )

    assert [provider.id for provider in settings.providers] == ["a", "b"]
