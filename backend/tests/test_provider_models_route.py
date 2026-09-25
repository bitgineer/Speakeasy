"""Tests for GET /api/settings/providers/{provider_id}/models."""

from types import SimpleNamespace

import httpx
import pytest

from speakeasy import server
from speakeasy.core.processing import ProviderError
from speakeasy.core.providers import ProviderModel
from speakeasy.services.settings import AppSettings, LlmProvider


@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=server.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as api:
        yield api


@pytest.fixture
def configured(monkeypatch):
    settings = AppSettings(providers=[LlmProvider(id="openai", kind="openai", model="gpt-4o-mini")])
    monkeypatch.setattr(server, "settings_service", SimpleNamespace(get=lambda: settings))
    monkeypatch.setattr(server, "get_key", lambda provider_id: None)


async def test_lists_models_for_a_configured_provider(client, configured, monkeypatch):
    monkeypatch.setattr(server, "get_key", lambda provider_id: "sk-test")

    async def fake_fetch(provider, api_key):
        assert provider.id == "openai"
        assert api_key == "sk-test"
        return [ProviderModel(id="gpt-4o-mini", name="GPT-4o mini"), ProviderModel(id="gpt-4o")]

    monkeypatch.setattr(server, "fetch_provider_models", fake_fetch)

    response = await client.get("/api/settings/providers/openai/models")

    assert response.status_code == 200
    assert response.json() == {
        "models": [
            {"id": "gpt-4o-mini", "name": "GPT-4o mini"},
            {"id": "gpt-4o", "name": None},
        ]
    }


async def test_unknown_provider_is_404(client, configured, monkeypatch):
    async def explode(provider, api_key):
        raise AssertionError("fetch should not run for an unknown provider")

    monkeypatch.setattr(server, "fetch_provider_models", explode)

    response = await client.get("/api/settings/providers/missing/models")

    assert response.status_code == 404
    assert response.json()["detail"] == "Unknown provider: missing"


async def test_upstream_failure_is_502_with_the_safe_detail(client, configured, monkeypatch):
    async def fail(provider, api_key):
        raise ProviderError("bad_response", "provider returned HTTP 404: model not found")

    monkeypatch.setattr(server, "fetch_provider_models", fail)

    response = await client.get("/api/settings/providers/openai/models")

    assert response.status_code == 502
    assert response.json()["detail"] == "provider returned HTTP 404: model not found"
