"""Tests for core.processing.resolve_processing."""

import pytest

from speakeasy.core.processing import (
    WRITE_SYSTEM,
    CleanupSpec,
    FocusedApp,
    ProcessingPlan,
    resolve_processing,
)
from speakeasy.services.settings import (
    AppMatch,
    AppSettings,
    LlmProvider,
    ProcessingMode,
    ProviderKind,
    ToneProfile,
)


def _settings(**overrides) -> AppSettings:
    defaults = {
        "active_mode": ProcessingMode.WRITE,
        "active_provider_id": "p",
        "providers": [LlmProvider(id="p", model="llama3.1:8b")],
        "enable_text_cleanup": True,
    }
    return AppSettings(**{**defaults, **overrides})


def _prompt(plan: ProcessingPlan) -> str:
    assert plan.rewrite is not None
    return plan.rewrite.system_prompt


def test_dictate_never_carries_a_rewrite():
    plan = resolve_processing(
        _settings(active_mode=ProcessingMode.DICTATE), None, None, frozenset()
    )

    assert plan.mode is ProcessingMode.DICTATE
    assert plan.rewrite is None


def test_dictate_ignores_a_broken_provider():
    settings = _settings(
        active_mode=ProcessingMode.DICTATE, active_provider_id="gone", providers=[]
    )

    plan = resolve_processing(settings, None, FocusedApp(key="slack"), frozenset())

    assert plan.rewrite is None
    assert plan.cleanup == CleanupSpec()


def test_explicit_write_beats_active_dictate():
    plan = resolve_processing(
        _settings(active_mode=ProcessingMode.DICTATE), ProcessingMode.WRITE, None, frozenset()
    )

    assert plan.mode is ProcessingMode.WRITE
    assert plan.rewrite is not None


def test_explicit_dictate_beats_active_write():
    plan = resolve_processing(
        _settings(active_mode=ProcessingMode.WRITE), ProcessingMode.DICTATE, None, frozenset()
    )

    assert plan.mode is ProcessingMode.DICTATE
    assert plan.rewrite is None


def test_none_mode_uses_active_mode():
    plan = resolve_processing(
        _settings(active_mode=ProcessingMode.COMMAND), None, None, frozenset()
    )

    assert plan.mode is ProcessingMode.COMMAND


def test_write_without_an_app_uses_default_tone():
    settings = _settings(default_tone=ToneProfile(name="Default", prompt="Short and friendly."))

    plan = resolve_processing(settings, None, None, frozenset())

    assert _prompt(plan) == f"{WRITE_SYSTEM}\n\nTone guidance: Short and friendly."


def test_write_without_a_matching_profile_uses_default_tone():
    settings = _settings(
        default_tone=ToneProfile(name="Default", prompt="Neutral."),
        tone_profiles=[
            ToneProfile(name="Slack", prompt="Casual.", matches=[AppMatch(field="app", pattern="slack")])
        ],
    )

    plan = resolve_processing(settings, None, FocusedApp(key="chrome", title="Docs"), frozenset())

    assert "Neutral." in _prompt(plan)


def test_write_uses_a_matching_app_rule():
    settings = _settings(
        default_tone=ToneProfile(name="Default", prompt="Neutral."),
        tone_profiles=[
            ToneProfile(name="Slack", prompt="Casual.", matches=[AppMatch(field="app", pattern="slack")])
        ],
    )

    plan = resolve_processing(settings, None, FocusedApp(key="SLACK"), frozenset())

    assert _prompt(plan) == f"{WRITE_SYSTEM}\n\nTone guidance: Casual."


def test_write_uses_a_matching_title_rule():
    settings = _settings(
        default_tone=ToneProfile(name="Default", prompt="Neutral."),
        tone_profiles=[
            ToneProfile(
                name="GitHub", prompt="Structured.", matches=[AppMatch(field="title", pattern="github")]
            )
        ],
    )

    plan = resolve_processing(
        settings, None, FocusedApp(key="chrome", title="PR #42 - GitHub"), frozenset()
    )

    assert "Structured." in _prompt(plan)


def test_first_matching_profile_in_list_order_wins():
    settings = _settings(
        tone_profiles=[
            ToneProfile(
                name="First", prompt="First tone.", matches=[AppMatch(field="app", pattern="slack")]
            ),
            ToneProfile(
                name="Second", prompt="Second tone.", matches=[AppMatch(field="app", pattern="slack")]
            ),
        ]
    )

    plan = resolve_processing(settings, None, FocusedApp(key="slack"), frozenset())

    assert _prompt(plan) == f"{WRITE_SYSTEM}\n\nTone guidance: First tone."


def test_whitespace_tone_prompt_leaves_the_base_instruction():
    settings = _settings(default_tone=ToneProfile(name="Default", prompt="   "))

    plan = resolve_processing(settings, None, None, frozenset())

    assert _prompt(plan) == WRITE_SYSTEM


def test_command_uses_command_prompt_without_tone():
    settings = _settings(
        active_mode=ProcessingMode.COMMAND,
        command_prompt="Carry out the instruction.",
        default_tone=ToneProfile(name="Default", prompt="Tone that must not appear."),
        tone_profiles=[
            ToneProfile(name="Slack", prompt="Casual.", matches=[AppMatch(field="app", pattern="slack")])
        ],
    )

    plan = resolve_processing(settings, None, FocusedApp(key="slack"), frozenset())

    assert plan.mode is ProcessingMode.COMMAND
    assert _prompt(plan) == "Carry out the instruction."


def test_write_without_an_active_provider_degrades():
    plan = resolve_processing(
        _settings(active_provider_id="", providers=[]), ProcessingMode.WRITE, None, frozenset()
    )

    assert plan.mode is ProcessingMode.WRITE
    assert plan.rewrite is None
    assert plan.cleanup == CleanupSpec()


def test_write_with_a_dangling_provider_id_degrades():
    settings = _settings(active_provider_id="gone", providers=[LlmProvider(id="p", model="m")])

    assert resolve_processing(settings, None, None, frozenset()).rewrite is None


def test_provider_without_a_model_degrades():
    settings = _settings(providers=[LlmProvider(id="p", model="")])

    assert resolve_processing(settings, None, None, frozenset()).rewrite is None


def test_custom_provider_without_a_base_url_degrades():
    settings = _settings(providers=[LlmProvider(id="p", kind=ProviderKind.CUSTOM, model="m")])

    assert resolve_processing(settings, None, None, frozenset()).rewrite is None


def test_openai_provider_without_a_key_degrades():
    settings = _settings(providers=[LlmProvider(id="p", kind=ProviderKind.OPENAI, model="m")])

    assert resolve_processing(settings, None, None, frozenset()).rewrite is None


def test_groq_provider_without_a_key_degrades():
    settings = _settings(providers=[LlmProvider(id="p", kind=ProviderKind.GROQ, model="m")])

    assert resolve_processing(settings, None, None, frozenset()).rewrite is None


def test_command_degrades_without_a_provider():
    settings = _settings(active_mode=ProcessingMode.COMMAND, active_provider_id="")

    plan = resolve_processing(settings, None, None, frozenset())

    assert plan.rewrite is None
    assert plan.cleanup is not None


def test_local_provider_needs_no_key():
    settings = _settings(
        providers=[LlmProvider(id="p", kind=ProviderKind.LOCAL, model="m", base_url="")]
    )

    plan = resolve_processing(settings, None, None, frozenset())

    assert plan.rewrite is not None
    assert plan.rewrite.provider.id == "p"


def test_openai_provider_with_a_key_resolves():
    settings = _settings(providers=[LlmProvider(id="p", kind=ProviderKind.OPENAI, model="m")])

    plan = resolve_processing(settings, None, None, frozenset({"p"}))

    assert plan.rewrite is not None
    assert plan.rewrite.provider.kind is ProviderKind.OPENAI


def test_groq_provider_with_a_key_resolves():
    settings = _settings(providers=[LlmProvider(id="p", kind=ProviderKind.GROQ, model="m")])

    plan = resolve_processing(settings, None, None, frozenset({"p"}))

    assert plan.rewrite is not None
    assert plan.rewrite.provider.kind is ProviderKind.GROQ


def test_custom_provider_with_a_base_url_resolves_without_a_key():
    provider = LlmProvider(
        id="p", kind=ProviderKind.CUSTOM, model="m", base_url="https://example.test/v1"
    )

    plan = resolve_processing(_settings(providers=[provider]), None, None, frozenset())

    assert plan.rewrite is not None


def test_cleanup_carries_custom_fillers_when_enabled():
    plan = resolve_processing(_settings(custom_filler_words=["uh", "hmm"]), None, None, frozenset())

    assert plan.cleanup == CleanupSpec(custom_fillers=["uh", "hmm"])


def test_none_custom_fillers_map_to_an_empty_list():
    plan = resolve_processing(_settings(custom_filler_words=None), None, None, frozenset())

    assert plan.cleanup is not None
    assert plan.cleanup.custom_fillers == []


@pytest.mark.parametrize("mode", list(ProcessingMode))
def test_cleanup_is_present_in_every_mode_when_enabled(mode):
    plan = resolve_processing(_settings(enable_text_cleanup=True), mode, None, frozenset())

    assert plan.cleanup == CleanupSpec()


@pytest.mark.parametrize("mode", list(ProcessingMode))
def test_cleanup_is_absent_in_every_mode_when_disabled(mode):
    plan = resolve_processing(_settings(enable_text_cleanup=False), mode, None, frozenset())

    assert plan.cleanup is None
