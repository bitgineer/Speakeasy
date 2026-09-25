"""Tests for the AI processing seam in transcribe_stop.

One outcome feeds the response, the WebSocket event, history, and the paste; a
provider failure or a superseded run degrades to the fallback text instead.
"""

from types import SimpleNamespace

import httpx
import pytest

from speakeasy import server
from speakeasy.core.processing import LlmResponse, ProviderError
from speakeasy.services.history import HistoryService
from speakeasy.services.settings import AppSettings, LlmProvider

LOCAL_PROVIDER = LlmProvider(id="local", kind="local", model="llama3.1:8b")


def _settings(**overrides) -> AppSettings:
    values = {
        "enable_text_cleanup": False,
        "active_provider_id": LOCAL_PROVIDER.id,
        "providers": [LOCAL_PROVIDER],
    }
    values.update(overrides)
    return AppSettings(**values)


class FakeTranscriber:
    is_recording = True

    def __init__(self, text: str = "raw words") -> None:
        self._text = text

    def stop_and_transcribe(self, language=None, progress_callback=None, instruction=None):
        return SimpleNamespace(
            text=self._text, duration_ms=1500, model_used="whisper", language="en"
        )


@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=server.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as api:
        yield api


@pytest.fixture
def recorded_broadcasts(monkeypatch):
    events: list[tuple[str, dict]] = []

    async def record(event_type, data):
        events.append((event_type, data))

    monkeypatch.setattr(server, "broadcast", record)
    return events


@pytest.fixture
def pasted(monkeypatch):
    texts: list[str] = []
    monkeypatch.setattr(server, "insert_text", texts.append)
    return texts


@pytest.fixture
async def history_service(temp_db_path):
    service = HistoryService(temp_db_path)
    await service.initialize()
    yield service
    await service.close()


def _wire(monkeypatch, history_service, complete=None, settings=None):
    monkeypatch.setattr(server, "build_provider_client", lambda provider, key: complete)
    monkeypatch.setattr(server, "get_key", lambda provider_id: None)
    monkeypatch.setattr(server, "detect_focused_app", lambda: None)
    monkeypatch.setattr(server, "history", history_service)
    monkeypatch.setattr(server, "transcriber", FakeTranscriber())
    monkeypatch.setattr(
        server, "settings_service", SimpleNamespace(get=lambda: settings or _settings())
    )


def _transcription_events(recorded_broadcasts: list[tuple[str, dict]]) -> list[dict]:
    return [data for event_type, data in recorded_broadcasts if event_type == "transcription"]


async def test_write_mode_delivers_one_consistent_outcome(
    client, monkeypatch, recorded_broadcasts, pasted, history_service
):
    seen: dict = {}

    async def complete(request):
        seen["user"] = request.user
        return LlmResponse(text="Rewritten words.")

    _wire(monkeypatch, history_service, complete=complete)

    response = await client.post("/api/transcribe/stop", json={"auto_paste": True, "mode": "write"})

    assert response.status_code == 200
    body = response.json()
    assert seen["user"] == "raw words"
    assert body["text"] == "Rewritten words."
    assert body["mode"] == "write"
    assert body["original_text"] == "raw words"
    assert body["processing_error"] is None

    record = await history_service.get(body["id"])
    assert record.text == "Rewritten words."
    assert record.original_text == "raw words"
    assert record.is_ai_enhanced is True

    assert _transcription_events(recorded_broadcasts) == [
        {
            "id": body["id"],
            "text": "Rewritten words.",
            "duration_ms": 1500,
            "original_text": "raw words",
            "processing_error": None,
        }
    ]
    assert pasted == ["Rewritten words."]


async def test_provider_failure_returns_the_fallback_with_the_error(
    client, monkeypatch, recorded_broadcasts, pasted, history_service
):
    async def failing(request):
        raise ProviderError("connection", "could not reach the provider")

    _wire(monkeypatch, history_service, complete=failing)

    response = await client.post("/api/transcribe/stop", json={"auto_paste": True, "mode": "write"})

    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "raw words"
    assert body["mode"] == "write"
    assert body["original_text"] is None
    assert body["processing_error"] == "could not reach the provider"

    record = await history_service.get(body["id"])
    assert record.text == "raw words"
    assert record.original_text is None
    assert record.is_ai_enhanced is False

    assert _transcription_events(recorded_broadcasts)[0]["processing_error"] == (
        "could not reach the provider"
    )
    assert pasted == ["raw words"]


async def test_dictate_never_builds_a_provider_client(
    client, monkeypatch, recorded_broadcasts, pasted, history_service
):
    built: list[LlmProvider] = []

    async def complete(request):
        raise AssertionError("dictate must not call the provider")

    monkeypatch.setattr(
        server, "build_provider_client", lambda provider, key: built.append(provider) or complete
    )
    monkeypatch.setattr(server, "get_key", lambda provider_id: "key")
    monkeypatch.setattr(server, "detect_focused_app", lambda: None)
    monkeypatch.setattr(server, "history", history_service)
    monkeypatch.setattr(server, "transcriber", FakeTranscriber())
    monkeypatch.setattr(
        server,
        "settings_service",
        SimpleNamespace(get=lambda: _settings(active_mode="dictate")),
    )

    response = await client.post("/api/transcribe/stop", json={"auto_paste": False})

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "dictate"
    assert body["text"] == "raw words"
    assert body["processing_error"] is None
    assert built == []
    assert pasted == []


async def test_superseded_run_records_history_and_skips_the_paste(
    client, monkeypatch, recorded_broadcasts, pasted, history_service
):
    async def superseding(request):
        server.cancel_processing()
        return LlmResponse(text="stale text")

    _wire(monkeypatch, history_service, complete=superseding)

    response = await client.post("/api/transcribe/stop", json={"auto_paste": True, "mode": "write"})

    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "raw words"
    assert body["processing_error"] == "cancelled"

    record = await history_service.get(body["id"])
    assert record.text == "raw words"
    assert record.original_text is None
    assert pasted == []
