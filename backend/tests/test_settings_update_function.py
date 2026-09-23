"""Tests for the PUT /api/settings handler."""

import httpx
import pytest

from speakeasy import server
from speakeasy.services.settings import SettingsService


@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=server.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as api:
        yield api


@pytest.fixture
def settings_service(monkeypatch, temp_settings_path):
    service = SettingsService(settings_path=temp_settings_path)
    service.load()
    monkeypatch.setattr(server, "settings_service", service)
    return service


async def test_invalid_values_return_400(client, settings_service):
    response = await client.put("/api/settings", json={"providers": [{"id": "p"}, {"id": "p"}]})

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Invalid settings")


async def test_other_routes_keep_the_standard_validation_detail(client, settings_service):
    """The key-route echo guard must not change validation responses elsewhere."""
    response = await client.put("/api/settings", json={"device": "invalid"})

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert isinstance(detail, list)
    assert detail[0]["loc"] == ["body", "device"]


async def test_empty_active_provider_id_clears(client, settings_service):
    settings_service.update(active_provider_id="ollama")

    response = await client.put("/api/settings", json={"active_provider_id": ""})

    assert response.status_code == 200
    assert response.json()["settings"]["active_provider_id"] == ""
    assert settings_service.get().active_provider_id == ""
