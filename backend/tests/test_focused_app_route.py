"""Tests for GET /api/focused-app."""

import httpx
import pytest

from speakeasy import server
from speakeasy.core.processing import FocusedApp


@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=server.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as api:
        yield api


async def test_focused_app_returns_the_detected_app(client, monkeypatch):
    monkeypatch.setattr(
        server, "detect_focused_app", lambda: FocusedApp(key="code", title="main.py - editor")
    )

    response = await client.get("/api/focused-app")

    assert response.status_code == 200
    assert response.json() == {"key": "code", "title": "main.py - editor"}


async def test_focused_app_returns_null_when_detection_fails(client, monkeypatch):
    monkeypatch.setattr(server, "detect_focused_app", lambda: None)

    response = await client.get("/api/focused-app")

    assert response.status_code == 200
    assert response.json() is None
