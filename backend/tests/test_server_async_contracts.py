"""Contract tests for the HTTP surface: off-loop execution and payload handling."""

import asyncio
import threading
from datetime import datetime, timezone
from types import SimpleNamespace

import httpx
import pytest

from speakeasy import server
from speakeasy.services.history import HistoryService


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


async def test_stop_transcribes_off_the_event_loop(client, monkeypatch, recorded_broadcasts):
    loop_thread = threading.get_ident()
    worker_thread: dict[str, int] = {}

    class FakeTranscriber:
        is_recording = True

        def stop_and_transcribe(self, language=None, progress_callback=None, instruction=None):
            worker_thread["id"] = threading.get_ident()
            if progress_callback:
                progress_callback(1, 2, "half")
            return SimpleNamespace(
                text="hello", duration_ms=1200, model_used="whisper", language="en"
            )

    class FakeHistory:
        async def add(self, **kwargs):
            return SimpleNamespace(id="rec-1")

    settings = SimpleNamespace(language="en", enable_text_cleanup=False, custom_filler_words=None)
    monkeypatch.setattr(server, "transcriber", FakeTranscriber())
    monkeypatch.setattr(server, "history", FakeHistory())
    monkeypatch.setattr(server, "settings_service", SimpleNamespace(get=lambda: settings))

    response = await client.post("/api/transcribe/stop", json={"auto_paste": False})

    assert response.status_code == 200
    assert worker_thread["id"] != loop_thread
    await asyncio.sleep(0.05)
    assert any(event_type == "transcription_progress" for event_type, _ in recorded_broadcasts)


async def test_model_load_runs_off_the_event_loop(client, monkeypatch, recorded_broadcasts):
    loop_thread = threading.get_ident()
    worker_thread: dict[str, int] = {}

    class FakeTranscriber:
        def load_model(
            self, model_type, model_name, device="cuda", compute_type=None, progress_callback=None
        ):
            worker_thread["id"] = threading.get_ident()
            if progress_callback:
                progress_callback(50, 100)

        def set_live_callback(self, callback):
            pass

        def set_live_enabled(self, enabled, chunk_seconds=3.0):
            pass

    settings = SimpleNamespace(
        update=lambda **kwargs: None,
        get=lambda: SimpleNamespace(live_transcription=False),
    )
    monkeypatch.setattr(server, "transcriber", FakeTranscriber())
    monkeypatch.setattr(server, "settings_service", settings)
    server.download_state_manager.clear_download()

    try:
        response = await client.post(
            "/api/models/load", json={"model_type": "whisper", "model_name": "base"}
        )

        assert response.status_code == 200
        assert worker_thread["id"] != loop_thread
        await asyncio.sleep(0.05)
        progress = [
            data for event_type, data in recorded_broadcasts if event_type == "download_progress"
        ]
        assert any(data.get("downloaded_bytes") == 50 for data in progress)
    finally:
        server.download_state_manager.clear_download()


async def test_batch_retry_reads_file_ids_from_the_body(client, monkeypatch):
    captured: dict = {}

    class FakeBatchService:
        async def retry_failed(self, job_id, file_ids):
            captured["job_id"] = job_id
            captured["file_ids"] = file_ids
            return SimpleNamespace(id=job_id, to_dict=lambda: {"id": job_id})

        async def process_job(self, *args, **kwargs):
            return None

    monkeypatch.setattr(server, "batch_service", FakeBatchService())
    monkeypatch.setattr(server, "settings_service", None)

    with_ids = await client.post(
        "/api/transcribe/batch/job-1/retry", json={"file_ids": ["file-1", "file-2"]}
    )
    assert with_ids.status_code == 200
    assert captured["file_ids"] == ["file-1", "file-2"]

    captured.clear()
    without_ids = await client.post("/api/transcribe/batch/job-1/retry")
    assert without_ids.status_code == 200
    assert captured["file_ids"] is None


async def test_history_import_preserves_records_and_is_idempotent(
    client, monkeypatch, temp_db_path
):
    history = HistoryService(temp_db_path)
    await history.initialize()
    monkeypatch.setattr(server, "history", history)

    payload = {
        "data": {
            "transcriptions": [
                {
                    "id": "r-1",
                    "text": "hello world",
                    "duration_ms": 900,
                    "model_used": "whisper",
                    "language": "en",
                    "created_at": "2026-01-02T03:04:05+00:00",
                    "original_text": "helo wrld",
                }
            ]
        },
        "merge": True,
    }

    try:
        first = await client.post("/api/history/import", json=payload)
        second = await client.post("/api/history/import", json=payload)

        assert first.json() == {"status": "ok", "imported": 1, "skipped": 0}
        assert second.json() == {"status": "ok", "imported": 0, "skipped": 1}

        records, total, _ = await history.list()
        assert total == 1
        record = await history.get("r-1")
        assert record is not None
        assert record.created_at == datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
        assert record.original_text == "helo wrld"
    finally:
        await history.close()
