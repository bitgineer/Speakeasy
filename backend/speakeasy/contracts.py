"""Wire-format models for the WebSocket events and shared HTTP payloads.

This module imports nothing else from the project, so no project module can
cycle back into it. Statuses are ``Literal`` unions here; the tests pin them
against the service enums.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ConnectedEvent(BaseModel):
    state: str
    model_loaded: bool


class StatusEvent(BaseModel):
    state: str
    recording: bool


class TranscriptionEvent(BaseModel):
    id: str
    text: str
    duration_ms: int


class TranscriptionProgressEvent(BaseModel):
    current_chunk: int
    total_chunks: int
    chunk_text: str
    progress_percent: int


class LiveTranscriptEvent(BaseModel):
    text: str


class ErrorEvent(BaseModel):
    message: str


class TranscriptionRecord(BaseModel):
    id: str
    text: str
    duration_ms: int
    model_used: str | None
    language: str | None
    created_at: datetime
    original_text: str | None
    is_ai_enhanced: bool


class BatchProgressEvent(BaseModel):
    job_id: str
    status: Literal["pending", "processing", "completed", "cancelled", "failed"]
    current_file: str | None
    current_index: int
    total_files: int
    completed: int
    failed: int
    file_status: Literal["pending", "processing", "completed", "failed", "skipped"] | None = None


class DownloadProgressEvent(BaseModel):
    download_id: str
    model_name: str
    model_type: str
    downloaded_bytes: int
    total_bytes: int
    progress_percent: float
    status: Literal["pending", "downloading", "completed", "cancelled", "error"]
    error_message: str | None
    elapsed_seconds: float
    bytes_per_second: float
    estimated_remaining_seconds: float | None


WS_EVENT_MODELS: dict[str, type[BaseModel]] = {
    "ConnectedEvent": ConnectedEvent,
    "StatusEvent": StatusEvent,
    "TranscriptionEvent": TranscriptionEvent,
    "TranscriptionProgressEvent": TranscriptionProgressEvent,
    "LiveTranscriptEvent": LiveTranscriptEvent,
    "ErrorEvent": ErrorEvent,
    "BatchProgressEvent": BatchProgressEvent,
    "DownloadProgressEvent": DownloadProgressEvent,
}
