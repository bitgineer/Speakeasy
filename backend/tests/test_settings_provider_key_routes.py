"""Tests for the provider key routes: write-only storage and presence listing."""

from types import SimpleNamespace

import httpx
import pytest

from speakeasy import server
from speakeasy.services import secrets
from speakeasy.services.settings import AppSettings, LlmProvider


@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=server.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as api:
        yield api


@pytest.fixture
def key_store(monkeypatch, tmp_path):
    path = tmp_path / "secrets.json"
    monkeypatch.setattr(
        server, "set_key", lambda provider_id, key: secrets.set_key(provider_id, key, path)
    )
    monkeypatch.setattr(server, "get_key", lambda provider_id: secrets.get_key(provider_id, path))
    monkeypatch.setattr(
        server,
        "settings_service",
        SimpleNamespace(
            get=lambda: AppSettings(
                providers=[LlmProvider(id="openai", kind="openai", model="gpt-4o-mini")]
            )
        ),
    )
    return path


async def test_key_round_trip_and_presence(client, key_store):
    response = await client.put("/api/settings/providers/openai/key", json={"key": "sk-secret"})

    assert response.status_code == 200
    assert response.json() == {"provider_id": "openai", "has_key": True}
    assert "sk-secret" not in response.text
    assert secrets.get_key("openai", key_store) == "sk-secret"

    listing = await client.get("/api/settings/provider-keys")

    assert listing.status_code == 200
    assert listing.json() == {"openai": True}
    assert "sk-secret" not in listing.text


async def test_empty_key_clears_presence(client, key_store):
    await client.put("/api/settings/providers/openai/key", json={"key": "sk-secret"})

    cleared = await client.put("/api/settings/providers/openai/key", json={"key": ""})

    assert cleared.json() == {"provider_id": "openai", "has_key": False}
    assert secrets.get_key("openai", key_store) is None
    listing = await client.get("/api/settings/provider-keys")
    assert listing.json() == {"openai": False}


async def test_oversized_key_is_not_echoed(client, key_store):
    oversized = "sk-" + "x" * 600

    response = await client.put("/api/settings/providers/openai/key", json={"key": oversized})

    assert response.status_code == 422
    assert oversized not in response.text


async def test_unknown_provider_returns_404_without_echoing_the_key(client, key_store):
    response = await client.put("/api/settings/providers/missing/key", json={"key": "sk-secret"})

    assert response.status_code == 404
    assert "sk-secret" not in response.text
    assert not key_store.exists()
