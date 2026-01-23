"""
Model maintenance and update features for faster-whisper-hotkey.

This module provides version checking, update notifications, model cleanup,
and repair functionality for downloaded models.

Classes
-------
ModelVersionInfo
    Information about a model's version and status.

ModelMaintenance
    Handles model maintenance operations.
"""

import hashlib
import logging
import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ModelVersionInfo:
    """
    Version and status information for a model.

    Attributes
    ----------
    model_name
        Model identifier.
    installed_version
        Version string of installed model (if available).
    latest_version
        Latest available version string.
    has_update
        Whether an update is available.
    is_corrupted
        Whether the installed model appears corrupted.
    disk_usage_mb
        Disk space used by this model.
    install_path
        Path to the installed model.
    last_checked
        Timestamp of last version check.
    """
    model_name: str
    installed_version: Optional[str] = None
    latest_version: Optional[str] = None
    has_update: bool = False
    is_corrupted: bool = False
    disk_usage_mb: Optional[int] = None
    install_path: Optional[str] = None
    last_checked: Optional[datetime] = None


class ModelMaintenance:
    """
    Model maintenance and update manager.

    Provides:
    - Version checking for installed models
    - Update notifications
    - Batch update functionality
    - Model cleanup to free disk space
    - Model repair/re-download
    - Disk space usage reporting
    """

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the maintenance manager.

        Parameters
        ----------
        cache_dir
            Model cache directory. If None, uses default.
        """
        self._cache_dir = cache_dir or self._get_default_cache_dir()
        self._model_info: Dict[str, ModelVersionInfo] = {}

    def _get_default_cache_dir(self) -> str:
        """Get the default model cache directory."""
        cache_home = os.environ.get(
            "XDG_CACHE_HOME",
            os.path.join(os.path.expanduser("~"), ".cache")
        )
        return str(Path(cache_home) / "huggingface" / "hub")

    def get_installed_models(self) -> List[str]:
        """
        Get list of installed model names.

        Returns
        -------
        List[str]
            List of installed model identifiers.
        """
        installed = []

        # Check huggingface cache for faster-whisper models
        cache_path = Path(self._cache_dir)

        if not cache_path.exists():
            return installed

        # Look for faster-whisper model directories
        for item in cache_path.iterdir():
            if item.is_dir() and "faster-whisper" in item.name.lower():
                # Extract model name from directory name
                # Format: models--guillaumekln--faster-whisper-{model_name}
                parts = item.name.split("--")
                if len(parts) >= 3:
                    model_name = parts[-1]
                    if model_name not in installed:
                        installed.append(model_name)

        # Also check for symlinked or cached models
        for model_name in [
            "tiny", "tiny.en", "base", "base.en", "small", "small.en",
            "medium", "medium.en", "large-v1", "large-v2", "large-v3",
            "distil-large-v3", "distil-large-v2", "distil-medium.en", "distil-small.en"
        ]:
            if self._is_model_installed(model_name) and model_name not in installed:
                installed.append(model_name)

        return installed

    def _is_model_installed(self, model_name: str) -> bool:
        """Check if a specific model is installed."""
        try:
            from faster_whisper import WhisperModel

            # Try to load the model - this will fail if not installed
            test = WhisperModel(
                model_size_or_path=model_name,
                device="cpu",
                compute_type="int8",
            )
            del test
            return True
        except Exception:
            return False

    def check_model_version(self, model_name: str) -> ModelVersionInfo:
        """
        Check version information for a model.

        Parameters
        ----------
        model_name
            Model identifier.

        Returns
        -------
        ModelVersionInfo
            Version and status information.
        """
        info = ModelVersionInfo(
            model_name=model_name,
            last_checked=datetime.now(),
        )

        # Check if installed
        if not self._is_model_installed(model_name):
            return info

        info.installed_version = self._get_installed_version(model_name)
        info.install_path = self._get_model_path(model_name)

        # Get disk usage
        if info.install_path:
            info.disk_usage_mb = self._get_disk_usage(info.install_path)

        # Check for corruption
        info.is_corrupted = self._check_corruption(model_name)

        # For faster-whisper models, we don't have a simple version check
        # Models are updated via new model names (e.g., large-v2 -> large-v3)
        info.has_update = False

        return info

    def _get_installed_version(self, model_name: str) -> str:
        """Get version string for installed model."""
        # For Whisper, version is in the model name
        if "v3" in model_name:
            return "v3"
        elif "v2" in model_name:
            return "v2"
        elif "v1" in model_name:
            return "v1"
        return "unknown"

    def _get_model_path(self, model_name: str) -> Optional[str]:
        """Get filesystem path for a model."""
        cache_path = Path(self._cache_dir)

        # Search in huggingface cache
        for item in cache_path.iterdir():
            if item.is_dir() and model_name in item.name.lower():
                return str(item)

        return None

    def _get_disk_usage(self, path: str) -> Optional[int]:
        """Get disk usage in MB for a path."""
        try:
            total = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total += os.path.getsize(filepath)
            return total // (1024 * 1024)
        except Exception as e:
            logger.warning(f"Could not calculate disk usage for {path}: {e}")
            return None

    def _check_corruption(self, model_name: str) -> bool:
        """
        Check if a model appears corrupted.

        Parameters
        ----------
        model_name
            Model to check.

        Returns
        -------
        bool
            True if model appears corrupted.
        """
        try:
            from faster_whisper import WhisperModel

            # Try to load and run a simple test
            model = WhisperModel(
                model_size_or_path=model_name,
                device="cpu",
                compute_type="int8",
            )
            # If we get here without exception, model is likely valid
            del model
            return False
        except Exception as e:
            logger.warning(f"Model {model_name} appears corrupted: {e}")
            return True

    def get_all_model_info(self) -> Dict[str, ModelVersionInfo]:
        """
        Get version info for all known models.

        Returns
        -------
        Dict[str, ModelVersionInfo]
            Map of model names to version info.
        """
        info = {}

        for model_name in [
            "tiny", "tiny.en", "base", "base.en", "small", "small.en",
            "medium", "medium.en", "large-v1", "large-v2", "large-v3",
            "distil-large-v3", "distil-large-v2", "distil-medium.en", "distil-small.en"
        ]:
            info[model_name] = self.check_model_version(model_name)

        return info

    def get_total_disk_usage(self) -> Tuple[int, int]:
        """
        Get total disk usage for all models.

        Returns
        -------
        Tuple[int, int]
            (used_mb, model_count)
        """
        total_mb = 0
        count = 0

        for model_name in self.get_installed_models():
            info = self.check_model_version(model_name)
            if info.disk_usage_mb:
                total_mb += info.disk_usage_mb
            count += 1

        return total_mb, count

    def remove_model(self, model_name: str) -> bool:
        """
        Remove a downloaded model to free disk space.

        Parameters
        ----------
        model_name
            Model to remove.

        Returns
        -------
        bool
            True if removal was successful.
        """
        model_path = self._get_model_path(model_name)
        if not model_path:
            logger.warning(f"Cannot find path for model {model_name}")
            return False

        try:
            shutil.rmtree(model_path)
            logger.info(f"Removed model {model_name} from {model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove model {model_name}: {e}")
            return False

    def repair_model(self, model_name: str, download_callback=None) -> bool:
        """
        Re-download a corrupted model.

        Parameters
        ----------
        model_name
            Model to repair.
        download_callback
            Optional callback for download progress.

        Returns
        -------
        bool
            True if repair was successful.
        """
        # Remove corrupted files first
        self.remove_model(model_name)

        # Re-download
        try:
            from faster_whisper import WhisperModel

            model = WhisperModel(
                model_size_or_path=model_name,
                device="cpu",
                compute_type="int8",
            )
            del model
            logger.info(f"Repaired model {model_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to repair model {model_name}: {e}")
            return False

    def cleanup_old_models(self, keep_models: List[str]) -> int:
        """
        Remove models not in the keep list.

        Parameters
        ----------
        keep_models
            List of model names to keep.

        Returns
        -------
        int
            Number of models removed.
        """
        removed = 0
        installed = self.get_installed_models()

        for model_name in installed:
            if model_name not in keep_models:
                if self.remove_model(model_name):
                    removed += 1

        return removed

    def get_model_checksum(self, model_name: str) -> Optional[str]:
        """
        Get checksum for a model file.

        Parameters
        ----------
        model_name
            Model identifier.

        Returns
        -------
        str or None
            SHA256 checksum, or None if not available.
        """
        model_path = self._get_model_path(model_name)
        if not model_path:
            return None

        # Find the main model file
        model_file = Path(model_path)
        for item in model_file.rglob("model.bin"):
            return self._calculate_checksum(item)

        return None

    def _calculate_checksum(self, filepath: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()

        try:
            with open(filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.warning(f"Could not calculate checksum for {filepath}: {e}")
            return ""

    def verify_model_integrity(self, model_name: str) -> bool:
        """
        Verify the integrity of a downloaded model.

        Parameters
        ----------
        model_name
            Model to verify.

        Returns
        -------
        bool
            True if model passes integrity check.
        """
        # Try to load the model
        if self._check_corruption(model_name):
            return False

        # Additional checks could go here (checksums, etc.)
        return True


def get_model_maintenance(cache_dir: Optional[str] = None) -> ModelMaintenance:
    """
    Get or create the singleton model maintenance instance.

    Parameters
    ----------
    cache_dir
        Optional cache directory.

    Returns
    -------
    ModelMaintenance
        The maintenance instance.
    """
    if not hasattr(get_model_maintenance, "_instance"):
        get_model_maintenance._instance = ModelMaintenance(cache_dir)
    return get_model_maintenance._instance
