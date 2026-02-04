"""
Download state management for model downloads.

Provides progress tracking, cancellation support, and download state management.
"""

import logging
import os
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional
import uuid

from huggingface_hub import scan_cache_dir

logger = logging.getLogger(__name__)


class DownloadStatus(str, Enum):
    """Status of a model download."""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass
class ModelDownloadProgress:
    """Progress information for a model download."""

    download_id: str
    model_name: str
    model_type: str
    downloaded_bytes: int = 0
    total_bytes: int = 0
    status: DownloadStatus = DownloadStatus.PENDING
    error_message: Optional[str] = None
    started_at: float = field(default_factory=time.time)
    last_update_at: float = field(default_factory=time.time)

    @property
    def progress_percent(self) -> float:
        """Calculate download progress as percentage (0-1)."""
        if self.total_bytes <= 0:
            return 0.0
        return min(self.downloaded_bytes / self.total_bytes, 1.0)

    @property
    def is_active(self) -> bool:
        """Check if download is currently active."""
        return self.status in (DownloadStatus.PENDING, DownloadStatus.DOWNLOADING)

    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time since download started."""
        return time.time() - self.started_at

    @property
    def bytes_per_second(self) -> float:
        """Calculate download speed in bytes per second."""
        elapsed = self.elapsed_seconds
        if elapsed <= 0 or self.downloaded_bytes <= 0:
            return 0.0
        return self.downloaded_bytes / elapsed

    @property
    def estimated_remaining_seconds(self) -> Optional[float]:
        """Estimate remaining download time in seconds."""
        if self.total_bytes <= 0 or self.downloaded_bytes <= 0:
            return None
        speed = self.bytes_per_second
        if speed <= 0:
            return None
        remaining_bytes = self.total_bytes - self.downloaded_bytes
        return remaining_bytes / speed

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "download_id": self.download_id,
            "model_name": self.model_name,
            "model_type": self.model_type,
            "downloaded_bytes": self.downloaded_bytes,
            "total_bytes": self.total_bytes,
            "progress_percent": self.progress_percent,
            "status": self.status.value,
            "error_message": self.error_message,
            "elapsed_seconds": self.elapsed_seconds,
            "bytes_per_second": self.bytes_per_second,
            "estimated_remaining_seconds": self.estimated_remaining_seconds,
        }


class DownloadStateManager:
    """
    Manages download state for model downloads.

    Thread-safe singleton that tracks the current download and provides
    cancellation support.
    """

    _instance: Optional["DownloadStateManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "DownloadStateManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self._current_download: Optional[ModelDownloadProgress] = None
        self._cancel_event = threading.Event()
        self._progress_callbacks: list[Callable[[ModelDownloadProgress], None]] = []
        self._state_lock = threading.Lock()

        # Stall detection
        self._stall_timeout_seconds = 30.0
        self._last_progress_bytes = 0
        self._last_progress_time = 0.0

    @property
    def current_download(self) -> Optional[ModelDownloadProgress]:
        """Get the current download progress."""
        with self._state_lock:
            return self._current_download

    @property
    def is_downloading(self) -> bool:
        """Check if a download is in progress."""
        with self._state_lock:
            return self._current_download is not None and self._current_download.is_active

    @property
    def cancel_requested(self) -> bool:
        """Check if cancellation has been requested."""
        return self._cancel_event.is_set()

    def start_download(self, model_type: str, model_name: str) -> ModelDownloadProgress:
        """
        Start tracking a new download.

        Args:
            model_type: Type of model being downloaded
            model_name: Name/path of model being downloaded

        Returns:
            ModelDownloadProgress object for the new download

        Raises:
            RuntimeError: If a download is already in progress
        """
        with self._state_lock:
            if self._current_download is not None and self._current_download.is_active:
                raise RuntimeError("A download is already in progress")

            self._cancel_event.clear()
            self._last_progress_bytes = 0
            self._last_progress_time = time.time()

            self._current_download = ModelDownloadProgress(
                download_id=str(uuid.uuid4()),
                model_type=model_type,
                model_name=model_name,
                status=DownloadStatus.DOWNLOADING,
            )

            logger.info(f"Started download tracking: {model_type}/{model_name}")
            return self._current_download

    def update_progress(
        self,
        downloaded_bytes: int,
        total_bytes: int,
    ) -> bool:
        """
        Update download progress.

        Args:
            downloaded_bytes: Bytes downloaded so far
            total_bytes: Total bytes to download

        Returns:
            True if should continue, False if cancelled or stalled
        """
        # Check for cancellation
        if self._cancel_event.is_set():
            self._set_status(DownloadStatus.CANCELLED)
            return False

        with self._state_lock:
            if self._current_download is None:
                return False

            now = time.time()

            # Check for stall (no progress for stall_timeout_seconds)
            if downloaded_bytes > self._last_progress_bytes:
                self._last_progress_bytes = downloaded_bytes
                self._last_progress_time = now
            elif now - self._last_progress_time > self._stall_timeout_seconds:
                self._current_download.status = DownloadStatus.ERROR
                self._current_download.error_message = (
                    f"Download stalled - no progress for {self._stall_timeout_seconds} seconds"
                )
                self._notify_callbacks()
                return False

            self._current_download.downloaded_bytes = downloaded_bytes
            self._current_download.total_bytes = total_bytes
            self._current_download.last_update_at = now

            self._notify_callbacks()
            return True

    def complete_download(self) -> None:
        """Mark the current download as completed."""
        self._set_status(DownloadStatus.COMPLETED)
        logger.info("Download completed")

    def fail_download(self, error_message: str) -> None:
        """Mark the current download as failed."""
        with self._state_lock:
            if self._current_download:
                self._current_download.status = DownloadStatus.ERROR
                self._current_download.error_message = error_message
                self._notify_callbacks()
        logger.error(f"Download failed: {error_message}")

    def cancel_download(self) -> bool:
        """
        Request cancellation of the current download.

        Returns:
            True if cancellation was requested, False if no active download
        """
        with self._state_lock:
            if self._current_download is None or not self._current_download.is_active:
                return False

            self._cancel_event.set()
            logger.info("Download cancellation requested")
            return True

    def clear_download(self) -> None:
        """Clear the current download state."""
        with self._state_lock:
            self._current_download = None
            self._cancel_event.clear()

    def add_progress_callback(self, callback: Callable[[ModelDownloadProgress], None]) -> None:
        """Add a callback to be notified of progress updates."""
        self._progress_callbacks.append(callback)

    def remove_progress_callback(self, callback: Callable[[ModelDownloadProgress], None]) -> None:
        """Remove a progress callback."""
        try:
            self._progress_callbacks.remove(callback)
        except ValueError:
            pass

    def _set_status(self, status: DownloadStatus) -> None:
        """Set the download status and notify callbacks."""
        with self._state_lock:
            if self._current_download:
                self._current_download.status = status
                self._notify_callbacks()

    def _notify_callbacks(self) -> None:
        """Notify all registered callbacks of progress update."""
        if self._current_download is None:
            return

        progress = self._current_download
        for callback in self._progress_callbacks:
            try:
                callback(progress)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")


# Global singleton instance
download_state_manager = DownloadStateManager()


def get_cached_models() -> list[dict]:
    """
    Get list of downloaded/cached models.

    Returns a list of cached models with their disk usage.
    Uses huggingface_hub's scan_cache_dir() API for cross-platform support.
    """
    cached_models = []

    try:
        # Scan HuggingFace cache using official API
        # This automatically detects platform-specific cache location
        hf_cache_info = scan_cache_dir()
        logger.info(f"Scanning HuggingFace cache: {len(hf_cache_info.repos)} repos found")

        # Iterate through all repos in cache
        for repo in hf_cache_info.repos:
            # Filter only model-type repos (ignore datasets, spaces)
            if repo.repo_type == "model":
                # Map to existing API response format for backward compatibility
                cached_models.append(
                    {
                        "model_name": repo.repo_id,
                        "path": str(repo.repo_path),
                        "size_bytes": repo.size_on_disk,
                        "size_human": repo.size_on_disk_str,
                        "source": "huggingface",
                    }
                )
                logger.info(f"Found cached model: {repo.repo_id} ({repo.size_on_disk_str})")

        # Log warnings about corrupted repos if any
        if hf_cache_info.warnings:
            for warning in hf_cache_info.warnings:
                logger.warning(f"Cache warning: {warning}")

        # Sort by size descending (largest first)
        cached_models.sort(key=lambda x: x["size_bytes"], reverse=True)
        logger.info(f"Total: {len(cached_models)} cached models")

        return cached_models

    except Exception as e:
        # Propagate errors to API layer for proper error response
        logger.error(f"Error scanning HuggingFace cache: {e}", exc_info=True)
        raise


def get_cache_info() -> dict:
    """Get information about the model cache."""
    cached_models = get_cached_models()
    total_size = sum(m["size_bytes"] for m in cached_models)

    # Get cache directory path
    hf_cache_dir = os.path.expanduser("~/.cache/huggingface/hub")

    return {
        "cache_dir": hf_cache_dir,
        "total_models": len(cached_models),
        "total_size_bytes": total_size,
        "total_size_human": _format_bytes(total_size),
        "models": cached_models,
    }


def clear_model_cache(model_name: Optional[str] = None) -> dict:
    """
    Clear model cache.

    Args:
        model_name: Specific model to clear, or None to clear all

    Returns:
        Result dict with cleared models and freed space
    """
    import shutil

    hf_cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
    cleared = []
    freed_bytes = 0

    if not os.path.exists(hf_cache_dir):
        return {"cleared": [], "freed_bytes": 0, "freed_human": "0 B"}

    try:
        for entry in os.scandir(hf_cache_dir):
            if entry.is_dir() and entry.name.startswith("models--"):
                # Check if this is the model to clear
                if model_name:
                    parts = entry.name.replace("models--", "").split("--")
                    dir_model_name = f"{parts[0]}/{parts[1]}" if len(parts) >= 2 else parts[0]
                    if dir_model_name != model_name:
                        continue

                size = _get_directory_size(entry.path)
                shutil.rmtree(entry.path)
                cleared.append(entry.name)
                freed_bytes += size
                logger.info(f"Cleared cache for: {entry.name}")

                if model_name:
                    break  # Only clearing specific model

    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise

    return {
        "cleared": cleared,
        "freed_bytes": freed_bytes,
        "freed_human": _format_bytes(freed_bytes),
    }


def _get_directory_size(path: str) -> int:
    """Calculate total size of a directory in bytes."""
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file(follow_symlinks=False):
                total += entry.stat().st_size
            elif entry.is_dir(follow_symlinks=False):
                total += _get_directory_size(entry.path)
    except (PermissionError, FileNotFoundError):
        pass
    return total


def _format_bytes(size_bytes: int) -> str:
    """Format bytes as human-readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"
