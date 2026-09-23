"""Tests for core.providers.complete_openai_compatible."""

import json

import httpx
import pytest

from speakeasy.core.processing import LlmRequest, ProviderError
from speakeasy.core.providers import complete_openai_compatible
from speakeasy.services.settings import LlmProvider, ProviderKind

REQUEST = LlmRequest(system="Be natural.", user="hello")
PROVIDER = LlmProvider(id="p", kind=ProviderKind.CUSTOM, model="m", base_url="https://llm.test/v1")
OPENROUTER = LlmProvider(
    id="or",
    kind=ProviderKind.CUSTOM,
    model="xiaomi/mimo-v2.6-pro",
    base_url="https://openrouter.ai/api/v1/chat/completions",
)


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


async def test_a_full_endpoint_base_url_is_not_doubled():
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        return _ok("ok")

    async with _client(handler) as client:
        await complete_openai_compatible(OPENROUTER, REQUEST, None, client=client)

    assert seen["url"] == "https://openrouter.ai/api/v1/chat/completions"


async def test_status_error_includes_the_provider_message():
    def handler(request):
        return httpx.Response(404, json={"error": {"message": "model not found"}})

    async with _client(handler) as client:
        with pytest.raises(ProviderError) as excinfo:
            await complete_openai_compatible(PROVIDER, REQUEST, None, client=client)

    assert excinfo.value.reason == "bad_response"
    assert excinfo.value.detail == "provider returned HTTP 404: model not found"


async def test_auth_error_includes_the_provider_message():
    def handler(request):
        return httpx.Response(401, json={"error": {"message": "No auth credentials found"}})

    async with _client(handler) as client:
        with pytest.raises(ProviderError) as excinfo:
            await complete_openai_compatible(PROVIDER, REQUEST, None, client=client)

    assert excinfo.value.reason == "auth"
    assert excinfo.value.detail == "provider rejected the API key: No auth credentials found"


async def test_status_error_truncates_the_provider_message():
    def handler(request):
        return httpx.Response(500, json={"error": {"message": "x" * 300}})

    async with _client(handler) as client:
        with pytest.raises(ProviderError) as excinfo:
            await complete_openai_compatible(PROVIDER, REQUEST, None, client=client)

    assert excinfo.value.reason == "server"
    assert excinfo.value.detail == f"provider server error (500): {'x' * 200}"


async def test_status_error_ignores_the_rest_of_the_body():
    def handler(request):
        return httpx.Response(
            429,
            json={
                "error": {"message": "slow down", "code": "BODY-MARKER"},
                "detail": "BODY-MARKER",
            },
        )

    async with _client(handler) as client:
        with pytest.raises(ProviderError) as excinfo:
            await complete_openai_compatible(PROVIDER, REQUEST, None, client=client)

    assert excinfo.value.detail == "provider rate limit reached: slow down"
    assert "BODY-MARKER" not in excinfo.value.detail
