"""Tests for core.providers.complete_openai_compatible."""

import json

import httpx
import pytest

from speakeasy.core.processing import LlmRequest, ProviderError
from speakeasy.core.providers import complete_openai_compatible
from speakeasy.services.settings import LlmProvider, ProviderKind

REQUEST = LlmRequest(system="Be natural.", user="hello")
PROVIDER = LlmProvider(id="p", kind=ProviderKind.CUSTOM, model="m", base_url="https://llm.test/v1")


def _client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://test")


def _ok(content: str) -> httpx.Response:
    return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})


async def test_success_returns_stripped_content():
    async with _client(lambda request: _ok("  Hello there.  ")) as client:
        response = await complete_openai_compatible(PROVIDER, REQUEST, None, client=client)

    assert response.text == "Hello there."


async def test_posts_the_expected_request():
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        seen["content_type"] = request.headers.get("content-type")
        return _ok("ok")

    async with _client(handler) as client:
        await complete_openai_compatible(PROVIDER, REQUEST, None, client=client)

    assert seen["url"] == "https://llm.test/v1/chat/completions"
    assert seen["content_type"] == "application/json"
    assert seen["body"] == {
        "model": "m",
        "messages": [
            {"role": "system", "content": "Be natural."},
            {"role": "user", "content": "hello"},
        ],
        "temperature": 0,
        "stream": False,
    }


async def test_bearer_header_is_sent_with_a_key():
    seen = {}

    def handler(request):
        seen["authorization"] = request.headers.get("authorization")
        return _ok("ok")

    async with _client(handler) as client:
        await complete_openai_compatible(PROVIDER, REQUEST, "sk-test", client=client)

    assert seen["authorization"] == "Bearer sk-test"


async def test_bearer_header_is_absent_without_a_key():
    seen = {}

    def handler(request):
        seen["authorization"] = request.headers.get("authorization")
        return _ok("ok")

    async with _client(handler) as client:
        await complete_openai_compatible(PROVIDER, REQUEST, None, client=client)

    assert seen["authorization"] is None


@pytest.mark.parametrize(
    ("status", "reason"),
    [
        (401, "auth"),
        (403, "auth"),
        (429, "rate_limit"),
        (500, "server"),
        (503, "server"),
        (404, "bad_response"),
        (302, "bad_response"),
    ],
)
async def test_status_codes_map_to_reasons(status, reason):
    def handler(request):
        return httpx.Response(status, json={"error": "nope"})

    async with _client(handler) as client:
        with pytest.raises(ProviderError) as excinfo:
            await complete_openai_compatible(PROVIDER, REQUEST, None, client=client)

    assert excinfo.value.reason == reason


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"choices": []},
        {"choices": [{"message": {}}]},
        {"choices": [{"message": {"content": None}}]},
    ],
)
async def test_malformed_shapes_map_to_bad_response(payload):
    def handler(request):
        return httpx.Response(200, json=payload)

    async with _client(handler) as client:
        with pytest.raises(ProviderError) as excinfo:
            await complete_openai_compatible(PROVIDER, REQUEST, None, client=client)

    assert excinfo.value.reason == "bad_response"


async def test_non_json_body_maps_to_bad_response():
    async with _client(lambda request: httpx.Response(200, content=b"not json")) as client:
        with pytest.raises(ProviderError) as excinfo:
            await complete_openai_compatible(PROVIDER, REQUEST, None, client=client)

    assert excinfo.value.reason == "bad_response"


async def test_blank_content_maps_to_bad_response():
    async with _client(lambda request: _ok("   ")) as client:
        with pytest.raises(ProviderError) as excinfo:
            await complete_openai_compatible(PROVIDER, REQUEST, None, client=client)

    assert excinfo.value.reason == "bad_response"


async def test_timeout_maps_to_timeout_reason():
    def handler(request):
        raise httpx.ReadTimeout("slow")

    async with _client(handler) as client:
        with pytest.raises(ProviderError) as excinfo:
            await complete_openai_compatible(PROVIDER, REQUEST, None, client=client)

    assert excinfo.value.reason == "timeout"


async def test_connection_error_maps_to_connection_reason():
    def handler(request):
        raise httpx.ConnectError("refused")

    async with _client(handler) as client:
        with pytest.raises(ProviderError) as excinfo:
            await complete_openai_compatible(PROVIDER, REQUEST, None, client=client)

    assert excinfo.value.reason == "connection"


async def test_invalid_base_url_maps_to_connection_reason():
    provider = LlmProvider(id="p", kind=ProviderKind.CUSTOM, model="m", base_url="http://[::1")

    async with _client(lambda request: _ok("ok")) as client:
        with pytest.raises(ProviderError) as excinfo:
            await complete_openai_compatible(provider, REQUEST, None, client=client)

    assert excinfo.value.reason == "connection"


async def test_detail_never_contains_the_key_the_prompt_or_the_body():
    secret = "sk-super-secret"

    def handler(request):
        return httpx.Response(401, json={"error": "BODY-MARKER"})

    request = LlmRequest(system="PROMPT-MARKER", user="PROMPT-MARKER")

    async with _client(handler) as client:
        with pytest.raises(ProviderError) as excinfo:
            await complete_openai_compatible(PROVIDER, request, secret, client=client)

    assert secret not in excinfo.value.detail
    assert "PROMPT-MARKER" not in excinfo.value.detail
    assert "BODY-MARKER" not in excinfo.value.detail
