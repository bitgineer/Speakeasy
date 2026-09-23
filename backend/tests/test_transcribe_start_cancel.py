"""Tests for the start route cancelling an in-flight processing run."""

import httpx
import pytest

from speakeasy import server
from speakeasy.core.transcriber import TranscriberState


@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=server.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as api:
        yield api


class FakeTranscriber:
    state = TranscriberState.IDLE
    is_model_loaded = True

    def __init__(self, order: list[str]) -> None:
        self._order = order

    def start_recording(self) -> None:
        self._order.append("start")


async def test_start_cancels_processing_before_starting_the_recorder(client, monkeypatch):
    order: list[str] = []
    monkeypatch.setattr(server, "cancel_processing", lambda: order.append("cancel"))
    monkeypatch.setattr(server, "transcriber", FakeTranscriber(order))

    response = await client.post("/api/transcribe/start")

    assert response.status_code == 200
    assert response.json() == {"status": "started"}
    assert order == ["cancel", "start"]
