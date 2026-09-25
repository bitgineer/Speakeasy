"""Contract tests binding the committed OpenAPI schema to the server models."""

from datetime import datetime, timezone
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


def component_schemas() -> dict:
    return openapi_export.build_schema()["components"]["schemas"]


def test_committed_schema_matches_render():
    assert openapi_export.committed_text() == openapi_export.render()


def test_schema_contains_every_contract_component():
    expected = set(WS_EVENT_MODELS) | {"TranscriptionRecord", "AppSettings"}
    assert expected <= set(component_schemas())


def test_schema_pins_route_fields():
    schemas = component_schemas()
    assert "instruction" in schemas["TranscribeStopRequest"]["properties"]
    assert "mode" in schemas["TranscribeStopRequest"]["properties"]
    assert {"original_text", "processing_error", "mode"} <= set(
        schemas["TranscribeStopResponse"]["properties"]
    )
    assert {"original_text", "processing_error"} <= set(schemas["TranscriptionEvent"]["properties"])
    assert "next_cursor" in schemas["HistoryListResponse"]["properties"]
    assert "server_port" in schemas["SettingsUpdateRequest"]["properties"]
    assert "TranscriptionProgressEvent" in schemas


def test_schema_contains_processing_components():
    expected = {
        "ProcessingMode",
        "ProviderKind",
        "AppMatch",
        "ToneProfile",
        "LlmProvider",
        "HotkeyBinding",
        "ProviderKeyRequest",
        "ProviderKeyResponse",
        "ModeStatusResponse",
        "ProcessingStatusResponse",
        "FocusedAppResponse",
    }
    assert expected <= set(component_schemas())


def test_schema_components_never_expose_api_keys():
    for name, schema in component_schemas().items():
        assert "api_key" not in schema.get("properties", {}), f"{name} exposes api_key"


def test_settings_update_request_carries_processing_fields():
    properties = component_schemas()["SettingsUpdateRequest"]["properties"]
    for field in (
        "active_mode",
        "active_provider_id",
        "default_tone",
        "tone_profiles",
        "command_prompt",
        "providers",
        "hotkeys",
    ):
        assert field in properties


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
