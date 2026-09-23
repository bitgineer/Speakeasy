"""Tests for core.processing.effective_base_url."""

import pytest

from speakeasy.core.processing import effective_base_url
from speakeasy.services.settings import LlmProvider, ProviderKind


def _provider(kind: ProviderKind = ProviderKind.CUSTOM, base_url: str = "") -> LlmProvider:
    return LlmProvider(id="p", kind=kind, base_url=base_url)


@pytest.mark.parametrize(
    ("kind", "default"),
    [
        (ProviderKind.LOCAL, "http://127.0.0.1:11434/v1"),
        (ProviderKind.OPENAI, "https://api.openai.com/v1"),
        (ProviderKind.GROQ, "https://api.groq.com/openai/v1"),
    ],
)
def test_empty_base_url_uses_the_kind_default(kind, default):
    assert effective_base_url(_provider(kind=kind)) == default


def test_custom_empty_base_url_stays_empty():
    assert effective_base_url(_provider(kind=ProviderKind.CUSTOM)) == ""


def test_configured_base_url_beats_the_kind_default():
    provider = _provider(kind=ProviderKind.OPENAI, base_url="https://llm.test/v1")

    assert effective_base_url(provider) == "https://llm.test/v1"


def test_trailing_slashes_are_stripped():
    provider = _provider(base_url="https://llm.test/v1///")

    assert effective_base_url(provider) == "https://llm.test/v1"


@pytest.mark.parametrize("suffix", ["/chat/completions", "/completions"])
def test_endpoint_suffixes_are_stripped(suffix):
    provider = _provider(base_url=f"https://llm.test/v1{suffix}")

    assert effective_base_url(provider) == "https://llm.test/v1"


@pytest.mark.parametrize("suffix", ["/chat/completions", "/completions"])
def test_endpoint_suffixes_with_a_trailing_slash_are_stripped(suffix):
    provider = _provider(base_url=f"https://llm.test/v1{suffix}/")

    assert effective_base_url(provider) == "https://llm.test/v1"


def test_the_reported_openrouter_endpoint_is_normalized():
    provider = _provider(base_url="https://openrouter.ai/api/v1/chat/completions")

    assert effective_base_url(provider) == "https://openrouter.ai/api/v1"


def test_an_interior_completions_segment_is_kept():
    provider = _provider(base_url="https://llm.test/completions/v1")

    assert effective_base_url(provider) == "https://llm.test/completions/v1"
