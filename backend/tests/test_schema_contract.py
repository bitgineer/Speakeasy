"""Contract tests binding the committed OpenAPI schema to the server models."""

from datetime import datetime, timezone
from pathlib import Path
from typing import get_args

from speakeasy import openapi_export
from speakeasy.contracts import (
    WS_EVENT_MODELS,
    BatchProgressEvent,
    DownloadProgressEvent,
    TranscriptionRecord,
)
from speakeasy.services.batch import BatchFileStatus, BatchJobStatus
from speakeasy.services.download_state import DownloadStatus, ModelDownloadProgress
from speakeasy.services.history import TranscriptionRecord as HistoryRecord

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "openapi.json"


def component_schemas() -> dict:
    return openapi_export.build_schema()["components"]["schemas"]


def test_committed_schema_matches_render():
    assert SCHEMA_PATH.read_bytes().decode("utf-8") == openapi_export.render()


def test_schema_contains_every_contract_component():
    expected = set(WS_EVENT_MODELS) | {"TranscriptionRecord", "AppSettings"}
    assert expected <= set(component_schemas())


def test_schema_pins_route_fields():
    schemas = component_schemas()
    assert "instruction" in schemas["TranscribeStopRequest"]["properties"]
    assert "next_cursor" in schemas["HistoryListResponse"]["properties"]
    assert "server_port" in schemas["SettingsUpdateRequest"]["properties"]
    assert "TranscriptionProgressEvent" in schemas


def test_download_event_matches_state_manager():
    progress = ModelDownloadProgress(
        download_id="d-1",
        model_name="base",
        model_type="whisper",
        downloaded_bytes=3,
        total_bytes=4,
    )
    assert set(DownloadProgressEvent.model_fields) == set(progress.to_dict())

    status_literals = get_args(DownloadProgressEvent.model_fields["status"].annotation)
    assert set(status_literals) == {status.value for status in DownloadStatus}


def test_batch_event_matches_service_enums():
    status_literals = get_args(BatchProgressEvent.model_fields["status"].annotation)
    assert set(status_literals) == {status.value for status in BatchJobStatus}

    file_status_annotation = BatchProgressEvent.model_fields["file_status"].annotation
    file_status_literal, none = get_args(file_status_annotation)
    assert none is type(None)
    assert set(get_args(file_status_literal)) == {status.value for status in BatchFileStatus}


def test_transcription_record_matches_history():
    record = HistoryRecord(
        id="r-1",
        text="hello",
        duration_ms=1200,
        model_used="whisper",
        language="en",
        created_at=datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
    )
    assert set(TranscriptionRecord.model_fields) == set(record.to_dict())
