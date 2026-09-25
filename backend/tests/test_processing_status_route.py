"""Tests for GET /api/processing/status."""

from types import SimpleNamespace

import httpx
import pytest

from speakeasy import server
from speakeasy.services.settings import AppSettings, LlmProvider


@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=server.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as api:
        yield api


OPENAI_PROVIDER = LlmProvider(id="openai", kind="openai", model="gpt-4o-mini")


def _service():
    settings = AppSettings(active_provider_id="openai", providers=[OPENAI_PROVIDER])
    return SimpleNamespace(get=lambda: settings)


async def test_status_reports_every_mode_ready_with_the_active_provider(client, monkeypatch):
    monkeypatch.setattr(server, "get_key", lambda provider_id: "sk-secret")
    monkeypatch.setattr(server, "settings_service", _service())

    response = await client.get("/api/processing/status")

    assert response.status_code == 200
    assert response.json() == {
        "modes": [
            {"mode": "write", "ready": True, "reason": None},
            {"mode": "command", "ready": True, "reason": None},
            {"mode": "dictate", "ready": True, "reason": None},
        ],
        "provider_id": "openai",
    }


async def test_status_reports_the_reason_a_mode_is_not_ready(client, monkeypatch):
    monkeypatch.setattr(server, "get_key", lambda provider_id: None)
    monkeypatch.setattr(server, "settings_service", _service())

    response = await client.get("/api/processing/status")

    assert response.status_code == 200
    assert response.json() == {
        "modes": [
            {"mode": "write", "ready": False, "reason": "key missing"},
            {"mode": "command", "ready": False, "reason": "key missing"},
            {"mode": "dictate", "ready": True, "reason": None},
        ],
        "provider_id": "openai",
    }
