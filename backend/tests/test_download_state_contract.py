"""Contract tests for download progress payloads."""

from speakeasy import server
from speakeasy.services.download_state import DownloadStatus, ModelDownloadProgress


def test_to_dict_reports_percent_on_a_0_to_100_scale():
    progress = ModelDownloadProgress(
        download_id="d-1",
        model_name="base",
        model_type="whisper",
        downloaded_bytes=3,
        total_bytes=4,
        status=DownloadStatus.DOWNLOADING,
    )

    assert progress.to_dict()["progress_percent"] == 75.0


async def test_cancelled_download_broadcast_carries_the_full_payload(monkeypatch):
    events: list[tuple[str, dict]] = []

    async def record(event_type, data):
        events.append((event_type, data))

    monkeypatch.setattr(server, "broadcast", record)

    manager = server.download_state_manager
    manager.clear_download()
    try:
        manager.start_download("whisper", "base")
        await server._broadcast_model_load_error("base", "", cancelled=True)

        event_type, payload = events[-1]
        assert event_type == "download_progress"
        assert payload["status"] == "cancelled"
        required = {
            "download_id",
            "model_name",
            "model_type",
            "downloaded_bytes",
            "total_bytes",
            "progress_percent",
            "status",
            "error_message",
            "elapsed_seconds",
            "bytes_per_second",
            "estimated_remaining_seconds",
        }
        assert required <= set(payload)
    finally:
        manager.clear_download()
