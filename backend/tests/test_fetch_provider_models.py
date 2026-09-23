"""Tests for core.providers.fetch_provider_models."""

import threading

import httpx
import pytest

from speakeasy.core.processing import ProviderError
from speakeasy.core.providers import ProviderModel, fetch_provider_models
from speakeasy.services.settings import LlmProvider, ProviderKind

PROVIDER = LlmProvider(id="p", kind=ProviderKind.CUSTOM, model="m", base_url="https://llm.test/v1")


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


async def test_parses_the_wrapped_shape():
    def handler(request):
        return httpx.Response(200, json={"data": [{"id": "z", "name": "Zed"}, {"id": "a"}]})

    with _client(handler) as client:
        models = await fetch_provider_models(PROVIDER, None, client=client)

    assert models == [ProviderModel(id="a"), ProviderModel(id="z", name="Zed")]


async def test_parses_a_bare_list():
    def handler(request):
        return httpx.Response(200, json=[{"id": "b"}, {"id": "a"}])

    with _client(handler) as client:
        models = await fetch_provider_models(PROVIDER, None, client=client)

    assert [model.id for model in models] == ["a", "b"]


async def test_duplicate_ids_collapse():
    def handler(request):
        return httpx.Response(200, json={"data": [{"id": "a"}, {"id": "b"}, {"id": "a"}]})

    with _client(handler) as client:
        models = await fetch_provider_models(PROVIDER, None, client=client)

    assert [model.id for model in models] == ["a", "b"]


async def test_requests_the_effective_models_url_with_auth():
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        seen["authorization"] = request.headers.get("authorization")
        return httpx.Response(200, json={"data": []})

    provider = LlmProvider(
        id="p",
        kind=ProviderKind.CUSTOM,
        model="m",
        base_url="https://openrouter.ai/api/v1/chat/completions/",
    )

    with _client(handler) as client:
        await fetch_provider_models(provider, "sk-test", client=client)

    assert seen["url"] == "https://openrouter.ai/api/v1/models"
    assert seen["authorization"] == "Bearer sk-test"


async def test_the_fetch_runs_off_the_event_loop():
    loop_thread = threading.get_ident()
    worker_thread: dict[str, int] = {}

    def handler(request):
        worker_thread["id"] = threading.get_ident()
        return httpx.Response(200, json={"data": []})

    with _client(handler) as client:
        await fetch_provider_models(PROVIDER, None, client=client)

    assert worker_thread["id"] != loop_thread


async def test_no_auth_header_without_a_key():
    seen = {}

    def handler(request):
        seen["authorization"] = request.headers.get("authorization")
        return httpx.Response(200, json={"data": []})

    with _client(handler) as client:
        await fetch_provider_models(PROVIDER, None, client=client)

    assert seen["authorization"] is None


async def test_status_error_maps_the_provider_message():
    def handler(request):
        return httpx.Response(404, json={"error": {"message": "model list not allowed"}})

    with _client(handler) as client:
        with pytest.raises(ProviderError) as excinfo:
            await fetch_provider_models(PROVIDER, None, client=client)

    assert excinfo.value.reason == "bad_response"
    assert excinfo.value.detail == "provider returned HTTP 404: model list not allowed"


async def test_timeout_maps_to_timeout_reason():
    def handler(request):
        raise httpx.ReadTimeout("slow")

    with _client(handler) as client:
        with pytest.raises(ProviderError) as excinfo:
            await fetch_provider_models(PROVIDER, None, client=client)

    assert excinfo.value.reason == "timeout"


async def test_connection_error_maps_to_connection_reason():
    def handler(request):
        raise httpx.ConnectError("refused")

    with _client(handler) as client:
        with pytest.raises(ProviderError) as excinfo:
            await fetch_provider_models(PROVIDER, None, client=client)

    assert excinfo.value.reason == "connection"


async def test_invalid_base_url_maps_to_connection_reason():
    provider = LlmProvider(id="p", kind=ProviderKind.CUSTOM, model="m", base_url="http://[::1")

    with _client(lambda request: httpx.Response(200, json={"data": []})) as client:
        with pytest.raises(ProviderError) as excinfo:
            await fetch_provider_models(provider, None, client=client)

    assert excinfo.value.reason == "connection"


async def test_unexpected_payload_maps_to_bad_response():
    def handler(request):
        return httpx.Response(200, json={"models": ["a"]})

    with _client(handler) as client:
        with pytest.raises(ProviderError) as excinfo:
            await fetch_provider_models(PROVIDER, None, client=client)

    assert excinfo.value.reason == "bad_response"
