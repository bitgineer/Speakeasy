"""Tests for core.processing.describe_readiness."""

import pytest

from speakeasy.core.processing import describe_readiness, resolve_processing
from speakeasy.services.settings import (
    AppSettings,
    LlmProvider,
    ProcessingMode,
    ProviderKind,
)

LLM_MODES = (ProcessingMode.WRITE, ProcessingMode.COMMAND)

_OPENAI = LlmProvider(id="p", kind=ProviderKind.OPENAI, model="m")
_GROQ = LlmProvider(id="p", kind=ProviderKind.GROQ, model="m")
_CUSTOM = LlmProvider(id="p", kind=ProviderKind.CUSTOM, model="m")


def _rows(settings: AppSettings, keyed: frozenset[str] = frozenset()):
    return {row.mode: row for row in describe_readiness(settings, keyed)}


def _provider_settings(provider: LlmProvider) -> AppSettings:
    return AppSettings(active_provider_id="p", providers=[provider])


def test_all_three_modes_are_described_in_enum_order():
    rows = describe_readiness(AppSettings(), frozenset())

    assert [row.mode for row in rows] == [
        ProcessingMode.WRITE,
        ProcessingMode.COMMAND,
        ProcessingMode.DICTATE,
    ]


def test_dictate_is_always_ready_without_reason():
    row = _rows(AppSettings())[ProcessingMode.DICTATE]

    assert row.ready is True
    assert row.reason is None


@pytest.mark.parametrize(
    ("settings", "reason"),
    [
        (AppSettings(), "no provider configured"),
        (
            AppSettings(active_provider_id="gone", providers=[LlmProvider(id="p", model="m")]),
            "provider not found",
        ),
        (_provider_settings(LlmProvider(id="p", model="")), "model missing"),
        (_provider_settings(_CUSTOM), "base url missing"),
        (_provider_settings(_OPENAI), "key missing"),
        (_provider_settings(_GROQ), "key missing"),
    ],
)
def test_write_and_command_report_the_failure_class(settings, reason):
    rows = _rows(settings)

    for mode in LLM_MODES:
        assert rows[mode].ready is False
        assert rows[mode].reason == reason


def test_local_provider_needs_no_key():
    row = _rows(_provider_settings(LlmProvider(id="p", model="m")))[ProcessingMode.WRITE]

    assert row.ready is True
    assert row.reason is None


def test_openai_provider_with_a_key_is_ready():
    row = _rows(_provider_settings(_OPENAI), frozenset({"p"}))[ProcessingMode.WRITE]

    assert row.ready is True
    assert row.reason is None


def test_groq_provider_with_a_key_is_ready():
    row = _rows(_provider_settings(_GROQ), frozenset({"p"}))[ProcessingMode.WRITE]

    assert row.ready is True
    assert row.reason is None


def test_custom_provider_with_a_base_url_needs_no_key():
    provider = LlmProvider(
        id="p", kind=ProviderKind.CUSTOM, model="m", base_url="https://example.test/v1"
    )

    row = _rows(_provider_settings(provider))[ProcessingMode.WRITE]

    assert row.ready is True
    assert row.reason is None


@pytest.mark.parametrize(
    ("settings", "keyed"),
    [
        (AppSettings(), frozenset()),
        (_provider_settings(LlmProvider(id="p", model="m")), frozenset()),
        (_provider_settings(_OPENAI), frozenset()),
        (_provider_settings(_OPENAI), frozenset({"p"})),
        (_provider_settings(_GROQ), frozenset({"p"})),
        (_provider_settings(LlmProvider(id="p", model="")), frozenset()),
        (_provider_settings(_CUSTOM), frozenset()),
    ],
)
def test_readiness_agrees_with_resolution(settings, keyed):
    plan = resolve_processing(settings, ProcessingMode.WRITE, None, keyed)
    rows = _rows(settings, keyed)

    assert (plan.rewrite is not None) is rows[ProcessingMode.WRITE].ready
