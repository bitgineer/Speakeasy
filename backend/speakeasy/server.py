"""
FastAPI server for SpeakEasy backend.

Provides HTTP and WebSocket APIs for the Electron frontend.
"""

import asyncio
import logging
import os
import re
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .core.config import (
    MODEL_INFO,
    get_available_models,
    get_compute_types,
    get_languages_for_model,
)
from .core.models import TranscriptionResult, get_gpu_info, recommend_model
from .core.text_cleanup import TextCleanupProcessor
from .core.transcriber import TranscriberService, TranscriberState, list_audio_devices
from .services.download_state import (
    DownloadStatus,
    ModelDownloadProgress,
    clear_model_cache,
    download_state_manager,
    get_cache_info,
    get_cached_models,
)
from .services.batch import BatchJob, BatchJobStatus, BatchService
from .services.export import ExportFormat, export_service
from .services.history import HistoryService, TranscriptionRecord
from .services.settings import (
    AppSettings,
    SettingsService,
    get_default_db_path,
    get_default_settings_path,
)
from .utils.paste import insert_text

logger = logging.getLogger(__name__)

# Global services
transcriber: Optional[TranscriberService] = None
history: Optional[HistoryService] = None
settings_service: Optional[SettingsService] = None
batch_service: Optional[BatchService] = None

# WebSocket connections for real-time updates
websocket_connections: list[WebSocket] = []


# --- Pydantic Models ---


class TranscribeStartResponse(BaseModel):
    status: str


class TranscribeStopRequest(BaseModel):
    auto_paste: bool = True
    language: Optional[str] = Field(None, max_length=10)
    instruction: Optional[str] = Field(None, max_length=1000)
    grammar_correction: bool = False


class TranscribeStopResponse(BaseModel):
    id: str
    text: str
    duration_ms: int
    model_used: Optional[str]
    language: Optional[str]


class HistoryListResponse(BaseModel):
    items: list[dict]
    total: int
    next_cursor: Optional[str] = None


class SettingsUpdateRequest(BaseModel):
    model_type: Optional[str] = Field(None, max_length=50)
    model_name: Optional[str] = Field(None, max_length=200)
    compute_type: Optional[str] = Field(None, max_length=20)
    device: Optional[str] = Field(None, pattern=r"^(cuda|cpu)$")
    language: Optional[str] = Field(None, max_length=10)
    device_name: Optional[str] = Field(None, max_length=200)
    hotkey: Optional[str] = Field(None, max_length=50)
    hotkey_mode: Optional[str] = Field(None, pattern=r"^(toggle|push-to-talk)$")
    auto_paste: Optional[bool] = None
    show_recording_indicator: Optional[bool] = None
    always_show_indicator: Optional[bool] = None
    theme: Optional[str] = Field(None, max_length=50)
    enable_text_cleanup: Optional[bool] = None
    custom_filler_words: Optional[list[str]] = Field(None, max_length=100)
    enable_grammar_correction: Optional[bool] = None
    grammar_model: Optional[str] = Field(None, max_length=200)
    grammar_device: Optional[str] = Field(None, pattern=r"^(cuda|cpu|auto)$")
    server_port: Optional[int] = Field(None, ge=1024, le=65535)

    @field_validator("hotkey")
    @classmethod
    def validate_hotkey_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not re.match(r"^[a-zA-Z0-9+]+$", v):
            raise ValueError("Hotkey must contain only alphanumeric characters and +")
        return v


class ModelLoadRequest(BaseModel):
    model_type: str = Field(..., max_length=50)
    model_name: str = Field(..., max_length=200)
    device: str = Field(default="cuda", pattern=r"^(cuda|cpu)$")
    compute_type: Optional[str] = Field(None, max_length=20)


class HealthResponse(BaseModel):
    status: str
    state: str
    model_loaded: bool
    model_name: Optional[str]
    gpu_available: bool
    gpu_name: Optional[str]
    gpu_vram_gb: Optional[float]


# --- WebSocket broadcast ---


async def broadcast(event_type: str, data: dict) -> None:
    """Broadcast an event to all connected WebSocket clients."""
    message = {"type": event_type, **data}

    disconnected = []
    for ws in websocket_connections:
        try:
            await ws.send_json(message)
        except Exception:
            disconnected.append(ws)

    for ws in disconnected:
        websocket_connections.remove(ws)


def on_state_change(state: TranscriberState) -> None:
    """Handle transcriber state changes."""
    asyncio.create_task(
        broadcast(
            "status",
            {
                "state": state.value,
                "recording": state == TranscriberState.RECORDING,
            },
        )
    )


# --- Lifespan ---


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    global transcriber, history, settings_service, batch_service

    logger.info("Starting SpeakEasy backend...")

    # Initialize settings
    settings_service = SettingsService(get_default_settings_path())
    settings = settings_service.load()

    # Initialize history database
    history = HistoryService(get_default_db_path())
    await history.initialize()

    # Initialize batch service (uses same db path with different file)
    batch_db_path = get_default_db_path().parent / "batch.db"
    batch_service = BatchService(batch_db_path)
    await batch_service.initialize()

    # Initialize transcriber
    transcriber = TranscriberService(on_state_change=on_state_change)

    # Auto-load model if configured
    if settings.model_name:
        try:
            logger.info(f"Auto-loading model: {settings.model_type}/{settings.model_name}")
            # Run in a separate thread to not block startup
            import threading
            threading.Thread(target=lambda: transcriber.load_model(
                model_type=settings.model_type,
                model_name=settings.model_name,
                device=settings.device,
                compute_type=settings.compute_type,
            )).start()
        except Exception as e:
            logger.warning(f"Failed to auto-load model: {e}")

    logger.info("SpeakEasy backend started")
    # Debug print to confirm server file version
    print("DEBUG: SpeakEasy server.py loaded. Endpoints registered: /api/models/cache")

    yield

    # Cleanup
    logger.info("Shutting down SpeakEasy backend...")

    if transcriber:
        transcriber.cleanup()

    if history:
        await history.close()

    if batch_service:
        await batch_service.close()

    logger.info("SpeakEasy backend stopped")


# --- FastAPI App ---

app = FastAPI(
    title="SpeakEasy Backend",
    description="Local voice transcription API",
    version="0.1.0",
    lifespan=lifespan,
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- CORS Configuration ---


def get_allowed_origins() -> list[str]:
    """
    Get allowed CORS origins based on environment.

    Priority:
    1. SPEAKEASY_CORS_ORIGINS env var (comma-separated)
    2. Development defaults (localhost on common ports)
    3. Production defaults (app:// for Electron)
    """
    env_origins = os.environ.get("SPEAKEASY_CORS_ORIGINS")
    if env_origins:
        return [origin.strip() for origin in env_origins.split(",") if origin.strip()]

    is_dev = os.environ.get("SPEAKEASY_ENV", "development").lower() == "development"

    if is_dev:
        # Development: allow localhost on common ports
        return [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:8080",
            "app://.",  # Electron production
        ]
    else:
        # Production: only allow Electron app
        return ["app://."]


def validate_origin(origin: str, allowed_origins: list[str]) -> bool:
    """
    Validate if an origin is allowed.

    Supports:
    - Exact matches
    - app:// protocol for Electron
    - Dynamic localhost ports in development
    """
    if not origin:
        return False

    # Check exact matches
    if origin in allowed_origins:
        return True

    # Check app:// protocol (Electron)
    if origin.startswith("app://"):
        return any(allowed.startswith("app://") for allowed in allowed_origins)

    # Check localhost with dynamic ports in development
    is_dev = os.environ.get("SPEAKEASY_ENV", "development").lower() == "development"
    if is_dev:
        if origin.startswith("http://localhost:") or origin.startswith("http://127.0.0.1:"):
            return True

    return False


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.post("/api/transcribe/stop", response_model=TranscribeStopResponse)
@limiter.limit("10/minute")
async def transcribe_stop(request: Request, body: TranscribeStopRequest):
    """Stop recording and transcribe."""
    if not transcriber:
        raise HTTPException(status_code=503, detail="Transcriber not initialized")

    if not transcriber.is_recording:
        raise HTTPException(status_code=400, detail="Not recording")

    try:
        # Get language from request or settings
        settings = settings_service.get() if settings_service else None
        language = body.language or (settings.language if settings else "auto")

        # Construct instruction if grammar correction is requested
        instruction = body.instruction
        if body.grammar_correction and not instruction:
            # Default instruction for grammar correction if not provided
            instruction = "Transcribe the audio exactly as spoken, but correct any grammatical errors. Maintain the original language."

        # Create progress callback for long transcriptions
        def on_transcription_progress(
            current_chunk: int, total_chunks: int, chunk_text: str
        ) -> None:
            """Broadcast transcription progress via WebSocket."""
            asyncio.create_task(
                broadcast(
                    "transcription_progress",
                    {
                        "current_chunk": current_chunk,
                        "total_chunks": total_chunks,
                        "chunk_text": chunk_text,
                        "progress_percent": int((current_chunk / total_chunks) * 100),
                    },
                )
            )

        # Stop and transcribe with progress reporting
        result: TranscriptionResult = transcriber.stop_and_transcribe(
            language=language,
            progress_callback=on_transcription_progress,
            instruction=instruction,
        )

        # Apply text cleanup if enabled
        cleaned_text = result.text
        if settings and settings.enable_text_cleanup:
            processor = TextCleanupProcessor(custom_fillers=settings.custom_filler_words)
            cleaned_text = processor.cleanup(result.text)

        # Save to history
        record = await history.add(
            text=result.text,
            duration_ms=result.duration_ms,
            model_used=result.model_used,
            language=result.language,
        )

        # Broadcast transcription event
        await broadcast(
            "transcription",
            {
                "id": record.id,
                "text": cleaned_text,
                "duration_ms": result.duration_ms,
            },
        )

        # Auto-paste if requested
        if body.auto_paste:
            insert_text(cleaned_text)

        return TranscribeStopResponse(
            id=record.id,
            text=cleaned_text,
            duration_ms=result.duration_ms,
            model_used=result.model_used,
            language=result.language,
        )

    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/transcribe/cancel")
async def transcribe_cancel():
    """Cancel current recording without transcribing."""
    if not transcriber:
        raise HTTPException(status_code=503, detail="Transcriber not initialized")

    transcriber.cancel_recording()
    return {"status": "cancelled"}


# --- History ---


@app.get("/api/history", response_model=HistoryListResponse)
async def history_list(
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None,
    cursor: Optional[str] = None,
    fields: Optional[str] = None,
):
    """
    List transcription history.

    Args:
        limit: Maximum number of records to return
        offset: Number of records to skip (ignored if cursor is provided)
        search: Optional search query for full-text search
        cursor: Optional cursor for pagination (from previous response's next_cursor)
        fields: Optional comma-separated list of fields to include (e.g., "id,text,created_at")
    """
    if not history:
        raise HTTPException(status_code=503, detail="History not initialized")

    # Parse fields parameter
    fields_set: Optional[set[str]] = None
    if fields:
        fields_set = set(f.strip() for f in fields.split(","))

    try:
        records, total, next_cursor = await history.list(
            limit=limit, offset=offset, search=search, cursor=cursor, fields=fields_set
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return HistoryListResponse(
        items=[r.to_dict(fields_set) for r in records],
        total=total,
        next_cursor=next_cursor,
    )


@app.get("/api/history/stats")
async def history_stats():
    """Get history statistics."""
    if not history:
        raise HTTPException(status_code=503, detail="History not initialized")

    return await history.get_stats()


# --- Export ---


class ExportRequest(BaseModel):
    format: str = Field(..., pattern=r"^(txt|json|csv|srt|vtt)$")
    include_metadata: bool = True
    start_date: Optional[str] = None  # ISO format
    end_date: Optional[str] = None  # ISO format
    search: Optional[str] = None
    record_ids: Optional[list[str]] = None  # Export specific records


@app.get("/api/history/export")
async def history_export_get(
    format: str = "json",
    include_metadata: bool = True,
):
    """
    Export all transcription history.

    Args:
        format: Export format (txt, json, csv, srt, vtt)
        include_metadata: Include metadata for JSON/CSV formats
    """
    if not history:
        raise HTTPException(status_code=503, detail="History not initialized")

    try:
        export_format = ExportFormat(format.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid format: {format}")

    # Get all records
    records, _, _ = await history.list(limit=10000, offset=0)

    content, filename, content_type = export_service.export(
        records, export_format, include_metadata
    )

    from fastapi.responses import Response

    return Response(
        content=content.encode("utf-8"),
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@app.get("/api/history/{record_id}")
async def history_get(record_id: str):
    """Get a specific transcription record."""
    if not history:
        raise HTTPException(status_code=503, detail="History not initialized")

    record = await history.get(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    return record.to_dict()


@app.delete("/api/history/{record_id}")
async def history_delete(record_id: str):
    """Delete a transcription record."""
    if not history:
        raise HTTPException(status_code=503, detail="History not initialized")

    deleted = await history.delete(record_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Record not found")

    return {"deleted": True}


@app.post("/api/history/export")
async def history_export_post(body: ExportRequest):
    """
    Export transcription history with filtering options.

    Supports filtering by date range, search query, or specific record IDs.
    """
    if not history:
        raise HTTPException(status_code=503, detail="History not initialized")

    try:
        export_format = ExportFormat(body.format.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid format: {body.format}")

    # Get records based on filters
    if body.record_ids:
        # Export specific records
        records = []
        for record_id in body.record_ids:
            record = await history.get(record_id)
            if record:
                records.append(record)
    else:
        # Get all and filter
        all_records, _, _ = await history.list(limit=10000, offset=0, search=body.search)
        records = all_records

        # Filter by date range if specified
        if body.start_date or body.end_date:
            from datetime import datetime

            filtered = []
            for r in records:
                if body.start_date:
                    start = datetime.fromisoformat(body.start_date.replace("Z", "+00:00"))
                    if r.created_at < start:
                        continue
                if body.end_date:
                    end = datetime.fromisoformat(body.end_date.replace("Z", "+00:00"))
                    if r.created_at > end:
                        continue
                filtered.append(r)
            records = filtered

    content, filename, content_type = export_service.export(
        records, export_format, body.include_metadata
    )

    from fastapi.responses import Response

    return Response(
        content=content.encode("utf-8"),
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


# --- Import ---


class ImportRequest(BaseModel):
    data: dict  # The exported JSON data
    merge: bool = True  # True to merge, False to replace


@app.post("/api/history/import")
@limiter.limit("5/minute")
async def history_import(request: Request, body: ImportRequest):
    """
    Import transcriptions from a previously exported JSON file.

    Args:
        data: The exported JSON data structure
        merge: If True, merge with existing history. If False, clear and replace.
    """
    if not history:
        raise HTTPException(status_code=503, detail="History not initialized")

    # Validate structure
    if "transcriptions" not in body.data:
        raise HTTPException(
            status_code=400, detail="Invalid import format: missing 'transcriptions' key"
        )

    transcriptions = body.data["transcriptions"]
    if not isinstance(transcriptions, list):
        raise HTTPException(
            status_code=400, detail="Invalid import format: 'transcriptions' must be an array"
        )

    # Clear existing if not merging
    if not body.merge:
        await history.clear()

    imported_count = 0
    skipped_count = 0

    for t in transcriptions:
        try:
            # Validate required fields
            if "text" not in t:
                skipped_count += 1
                continue

            # Check if record already exists (by ID)
            if body.merge and "id" in t:
                existing = await history.get(t["id"])
                if existing:
                    skipped_count += 1
                    continue

            # Add record
            await history.add(
                text=t.get("text", ""),
                duration_ms=t.get("duration_ms", 0),
                model_used=t.get("model_used"),
                language=t.get("language"),
            )
            imported_count += 1

        except Exception as e:
            logger.warning(f"Failed to import record: {e}")
            skipped_count += 1

    return {
        "status": "ok",
        "imported": imported_count,
        "skipped": skipped_count,
    }


# --- Batch Transcription ---


class BatchCreateRequest(BaseModel):
    file_paths: list[str] = Field(..., min_length=1)


class BatchJobResponse(BaseModel):
    id: str
    status: str
    total_files: int
    completed: int
    failed: int
    skipped: int


@app.post("/api/transcribe/batch")
@limiter.limit("10/minute")
async def batch_create(request: Request, body: BatchCreateRequest):
    """
    Create a new batch transcription job.

    Args:
        file_paths: List of paths to audio files to transcribe
    """
    if not batch_service:
        raise HTTPException(status_code=503, detail="Batch service not initialized")

    # Validate files exist
    from pathlib import Path

    for fp in body.file_paths:
        if not Path(fp).exists():
            raise HTTPException(status_code=400, detail=f"File not found: {fp}")

    job = await batch_service.create_job(body.file_paths)

    # Start processing in background
    asyncio.create_task(
        batch_service.process_job(
            job.id,
            transcriber,
            history,
            broadcast,
            language=settings_service.get().language if settings_service else "auto",
        )
    )

    return {
        "job_id": job.id,
        "status": job.status.value,
        "total_files": len(job.files),
    }


@app.get("/api/transcribe/batch")
async def batch_list():
    """List all batch transcription jobs."""
    if not batch_service:
        raise HTTPException(status_code=503, detail="Batch service not initialized")

    jobs = await batch_service.list_jobs()
    return {"jobs": [j.to_dict() for j in jobs]}


@app.get("/api/transcribe/batch/{job_id}")
async def batch_get(job_id: str):
    """Get status of a batch transcription job."""
    if not batch_service:
        raise HTTPException(status_code=503, detail="Batch service not initialized")

    job = await batch_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job.to_dict()


@app.post("/api/transcribe/batch/{job_id}/cancel")
async def batch_cancel(job_id: str):
    """Cancel a batch transcription job."""
    if not batch_service:
        raise HTTPException(status_code=503, detail="Batch service not initialized")

    cancelled = await batch_service.cancel_job(job_id)
    if not cancelled:
        raise HTTPException(status_code=400, detail="Job cannot be cancelled")

    return {"status": "cancelled"}


@app.post("/api/transcribe/batch/{job_id}/retry")
async def batch_retry(job_id: str, file_ids: Optional[list[str]] = None):
    """
    Retry failed files in a batch job.

    Args:
        file_ids: Specific file IDs to retry, or None to retry all failed
    """
    if not batch_service:
        raise HTTPException(status_code=503, detail="Batch service not initialized")

    try:
        job = await batch_service.retry_failed(job_id, file_ids)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Start processing again
    asyncio.create_task(
        batch_service.process_job(
            job.id,
            transcriber,
            history,
            broadcast,
            language=settings_service.get().language if settings_service else "auto",
        )
    )

    return {"status": "retrying", "job": job.to_dict()}


@app.delete("/api/transcribe/batch/{job_id}")
async def batch_delete(job_id: str):
    """Delete a batch transcription job."""
    if not batch_service:
        raise HTTPException(status_code=503, detail="Batch service not initialized")

    deleted = await batch_service.delete_job(job_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Job not found")

    return {"deleted": True}


# --- Settings ---


@app.get("/api/settings")
async def settings_get():
    """Get current settings."""
    if not settings_service:
        raise HTTPException(status_code=503, detail="Settings not initialized")

    return settings_service.to_dict()


@app.put("/api/settings")
@limiter.limit("20/minute")
async def settings_update(request: Request, body: SettingsUpdateRequest):
    """Update settings."""
    if not settings_service:
        raise HTTPException(status_code=503, detail="Settings not initialized")

    # Filter out None values
    updates = {k: v for k, v in body.model_dump().items() if v is not None}

    if not updates:
        return {"status": "ok", "reload_required": False}

    old_settings = settings_service.get()
    new_settings = settings_service.update(**updates)

    # Check if model reload is required
    reload_required = (
        updates.get("model_type") != old_settings.model_type
        or updates.get("model_name") != old_settings.model_name
        or updates.get("device") != old_settings.device
        or updates.get("compute_type") != old_settings.compute_type
    ) and any(k in updates for k in ["model_type", "model_name", "device", "compute_type"])

    return {
        "status": "ok",
        "settings": new_settings.model_dump(),
        "reload_required": reload_required,
    }


# --- Models ---


@app.get("/api/models")
async def models_list():
    """List available models and their info."""
    current_model = None
    if transcriber and transcriber._model:
        current_model = {
            "type": transcriber._model.model_type.value,
            "name": transcriber._model.model_name,
        }

    return {
        "models": MODEL_INFO,
        "current": current_model,
    }


@app.get("/api/models/types")
async def models_types():
    """Get available model types."""
    return {
        "types": list(MODEL_INFO.keys()),
    }


@app.get("/api/models/recommend")
async def models_recommend(needs_translation: bool = False):
    """Get model recommendation based on hardware."""
    gpu_info = get_gpu_info()
    vram_gb = gpu_info.get("vram_gb", 0)

    model_type, model_name = recommend_model(vram_gb, needs_translation)

    return {
        "recommendation": {
            "model_type": model_type,
            "model_name": model_name,
        },
        "gpu": gpu_info,
        "reason": f"Based on {vram_gb}GB VRAM"
        if gpu_info["available"]
        else "No GPU detected, using CPU model",
    }




@app.post("/api/models/load")
@limiter.limit("5/minute")
async def models_load(request: Request, body: ModelLoadRequest):
    """Load a model with download progress tracking."""
    if not transcriber:
        raise HTTPException(status_code=503, detail="Transcriber not initialized")

    # Check if already downloading
    if download_state_manager.is_downloading:
        raise HTTPException(status_code=409, detail="A model download is already in progress")

    try:
        # Start download tracking
        download_progress = download_state_manager.start_download(
            model_type=body.model_type,
            model_name=body.model_name,
        )

        # Broadcast loading status
        await broadcast("status", {"state": "loading", "model": body.model_name})
        await broadcast("download_progress", download_progress.to_dict())

        # Create progress callback that broadcasts updates
        last_broadcast_time = [0.0]  # Use list for mutable closure

        def progress_callback(downloaded: int, total: int) -> bool:
            """Progress callback that broadcasts via WebSocket."""
            import time

            # Check for cancellation
            if download_state_manager.cancel_requested:
                return False

            # Update state
            should_continue = download_state_manager.update_progress(downloaded, total)

            # Throttle broadcasts to every 1 second
            now = time.time()
            if now - last_broadcast_time[0] >= 1.0:
                last_broadcast_time[0] = now
                current = download_state_manager.current_download
                if current:
                    # Use asyncio to broadcast from sync callback
                    asyncio.create_task(broadcast("download_progress", current.to_dict()))

            return should_continue

        # Load model with progress tracking
        transcriber.load_model(
            model_type=body.model_type,
            model_name=body.model_name,
            device=body.device,
            compute_type=body.compute_type,
            progress_callback=progress_callback,
        )

        # Mark download complete
        download_state_manager.complete_download()

        # Final broadcast
        current = download_state_manager.current_download
        if current:
            await broadcast("download_progress", current.to_dict())

        # Update settings
        if settings_service:
            settings_service.update(
                model_type=request.model_type,
                model_name=request.model_name,
                device=request.device,
                compute_type=request.compute_type,
            )

        return {"status": "loaded", "model": body.model_name}

    except RuntimeError as e:
        if "cancelled" in str(e).lower():
            # Download was cancelled
            await broadcast(
                "download_progress",
                {
                    "status": "cancelled",
                    "model_name": body.model_name,
                },
            )
            raise HTTPException(status_code=499, detail="Download cancelled")

        download_state_manager.fail_download(str(e))
        current = download_state_manager.current_download
        if current:
            await broadcast("download_progress", current.to_dict())
        await broadcast("error", {"message": str(e)})
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        download_state_manager.fail_download(str(e))
        current = download_state_manager.current_download
        if current:
            await broadcast("download_progress", current.to_dict())
        await broadcast("error", {"message": str(e)})
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Clear download state after a delay to allow UI to show final state
        await asyncio.sleep(2)
        download_state_manager.clear_download()


@app.post("/api/models/unload")
async def models_unload():
    """Unload the current model."""
    if not transcriber:
        raise HTTPException(status_code=503, detail="Transcriber not initialized")

    transcriber.unload_model()
    return {"status": "unloaded"}


@app.get("/api/models/recommend")
async def models_recommend(needs_translation: bool = False):
    """Get model recommendation based on hardware."""
    gpu_info = get_gpu_info()
    vram_gb = gpu_info.get("vram_gb", 0)

    model_type, model_name = recommend_model(vram_gb, needs_translation)

    return {
        "recommendation": {
            "model_type": model_type,
            "model_name": model_name,
        },
        "gpu": gpu_info,
        "reason": f"Based on {vram_gb}GB VRAM"
        if gpu_info["available"]
        else "No GPU detected, using CPU model",
    }


# --- Model Download Progress ---


@app.get("/api/models/download/status")
async def models_download_status():
    """Get current download progress or null if no active download."""
    current = download_state_manager.current_download
    if current is None:
        return {"download": None}
    return {"download": current.to_dict()}


@app.post("/api/models/download/cancel")
async def models_download_cancel():
    """Cancel the current model download."""
    cancelled = download_state_manager.cancel_download()
    if not cancelled:
        raise HTTPException(status_code=400, detail="No active download to cancel")
    return {"status": "cancelled"}


@app.get("/api/models/downloaded")
async def models_downloaded():
    """Get list of downloaded/cached models."""
    models = get_cached_models()
    return {"models": models, "count": len(models)}


@app.get("/api/models/cache")
async def models_cache_info():
    """Get model cache information including disk usage."""
    logger.info("Accessing model cache endpoint")
    return get_cache_info()



@app.delete("/api/models/cache")
@limiter.limit("5/minute")
async def models_cache_clear(request: Request, model_name: Optional[str] = None):
    """
    Clear model cache.

    Args:
        model_name: Specific model to clear, or None to clear all cached models
    """
    try:
        result = clear_model_cache(model_name)
        return {"status": "cleared", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models/{model_type}")
async def models_by_type(model_type: str):
    """Get models of a specific type."""
    if model_type not in MODEL_INFO:
        raise HTTPException(status_code=404, detail=f"Unknown model type: {model_type}")

    return {
        "models": get_available_models(model_type),
        "languages": get_languages_for_model(model_type),
        "compute_types": get_compute_types(model_type),
        "info": MODEL_INFO[model_type],
    }


# --- Audio Devices ---


@app.get("/api/devices")
async def devices_list():
    """List available audio input devices."""
    devices = list_audio_devices()
    current = settings_service.get().device_name if settings_service else None

    return {
        "devices": devices,
        "current": current,
    }


@app.put("/api/devices/{device_name}")
async def devices_set(device_name: str):
    """Set the audio input device."""
    if not transcriber:
        raise HTTPException(status_code=503, detail="Transcriber not initialized")

    try:
        transcriber.set_device(device_name if device_name != "default" else None)

        if settings_service:
            settings_service.update(device_name=device_name if device_name != "default" else None)

        return {"status": "ok", "device": device_name}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- WebSocket ---


@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    websocket_connections.append(websocket)

    # Send initial state
    await websocket.send_json(
        {
            "type": "connected",
            "state": transcriber.state.value if transcriber else "not_initialized",
            "model_loaded": transcriber.is_model_loaded if transcriber else False,
        }
    )

    try:
        while True:
            try:
                # Wait for message with 30s timeout
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Echo for ping/pong
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Send ping to check if client is alive
                try:
                    await websocket.send_text("ping")
                except Exception:
                    # Client disconnected
                    break

    except WebSocketDisconnect:
        pass
    finally:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)


# --- Run function ---


def run(host: str = "127.0.0.1", port: int = 8765):
    """Run the server."""
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run()
