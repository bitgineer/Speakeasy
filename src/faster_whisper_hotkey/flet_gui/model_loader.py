"""
Model loading optimization for faster-whisper-hotkey.

This module provides optimized model loading with lazy loading,
background pre-loading, and memory management.

Classes
-------
ModelLoadConfig
    Configuration for model loading behavior.

ModelLoader
    Optimized model loading service with caching and pre-loading.
"""

import logging
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable, Dict, Any

logger = logging.getLogger(__name__)


class LoadState(Enum):
    """Model loading states."""
    NOT_LOADED = "not_loaded"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"
    UNLOADED = "unloaded"


@dataclass
class ModelLoadConfig:
    """
    Configuration for model loading behavior.

    Attributes
    ----------
    lazy_load
        If True, only load model when first used.
    preload_on_startup
        If True, load model in background during app startup.
    keep_loaded
        If True, keep model loaded after use.
    unload_after_idle_seconds
        Unload model after this many seconds of inactivity (0 = never).
    show_loading_indicator
        If True, show UI indication when model is loading.
    enable_cache
        If True, cache model for faster reload.
    """
    lazy_load: bool = True
    preload_on_startup: bool = False
    keep_loaded: bool = True
    unload_after_idle_seconds: float = 0
    show_loading_indicator: bool = True
    enable_cache: bool = True


@dataclass
class ModelLoadStatus:
    """
    Status of a model load operation.

    Attributes
    ----------
    state
        Current load state.
    progress
        Load progress (0-1) if loading.
    error_message
        Error message if in ERROR state.
    load_time_seconds
        Time taken to load model (if loaded).
    memory_usage_mb
        Estimated memory usage in MB (if loaded).
    """
    state: LoadState = LoadState.NOT_LOADED
    progress: float = 0.0
    error_message: Optional[str] = None
    load_time_seconds: Optional[float] = None
    memory_usage_mb: Optional[int] = None


class ModelLoader:
    """
    Optimized model loading service.

    Features:
    - Lazy loading (load on first use)
    - Background pre-loading
    - Loading state tracking
    - Memory management with auto-unload
    - Progress callbacks
    """

    # Memory estimates for different models (in MB)
    MODEL_MEMORY = {
        "large-v3": 10000,
        "large-v2": 10000,
        "large-v1": 10000,
        "medium": 5000,
        "medium.en": 5000,
        "small": 2000,
        "small.en": 2000,
        "base": 1000,
        "base.en": 1000,
        "tiny": 750,
        "tiny.en": 750,
        "distil-large-v3": 6000,
        "distil-large-v2": 6000,
        "distil-medium.en": 3000,
        "distil-small.en": 1500,
    }

    def __init__(self, config: Optional[ModelLoadConfig] = None):
        """
        Initialize the model loader.

        Parameters
        ----------
        config
            Loading configuration. If None, uses defaults.
        """
        self._config = config or ModelLoadConfig()
        self._models: Dict[str, Any] = {}
        self._status: Dict[str, ModelLoadStatus] = {}
        self._callbacks: Dict[str, List[Callable[[ModelLoadStatus], None]]] = {}
        self._lock = threading.RLock()
        self._last_activity: Dict[str, float] = {}
        self._unload_timer: Optional[threading.Timer] = None

    def get_status(self, model_name: str) -> ModelLoadStatus:
        """
        Get the current load status of a model.

        Parameters
        ----------
        model_name
            Model identifier.

        Returns
        -------
        ModelLoadStatus
            Current status of the model.
        """
        with self._lock:
            if model_name not in self._status:
                self._status[model_name] = ModelLoadStatus()
            return self._status[model_name]

    def load_model(
        self,
        model_name: str,
        device: str = "cpu",
        compute_type: str = "int8",
        callback: Optional[Callable[[ModelLoadStatus], None]] = None,
    ) -> ModelLoadStatus:
        """
        Load a model with optional progress callback.

        Parameters
        ----------
        model_name
            Model identifier.
        device
            Target device ("cpu" or "cuda").
        compute_type
            Compute type ("float16", "int8", etc.).
        callback
            Optional callback for status updates.

        Returns
        -------
        ModelLoadStatus
            Initial status of the load operation.
        """
        with self._lock:
            # Check if already loaded
            if model_name in self._models:
                status = self._status.get(model_name, ModelLoadStatus())
                status.state = LoadState.LOADED
                self._last_activity[model_name] = time.time()
                return status

            # Initialize status
            if model_name not in self._status:
                self._status[model_name] = ModelLoadStatus()
            self._status[model_name].state = LoadState.LOADING
            self._status[model_name].progress = 0.0

            # Register callback
            if callback:
                if model_name not in self._callbacks:
                    self._callbacks[model_name] = []
                self._callbacks[model_name].append(callback)

        # Start loading in background
        def load_worker():
            try:
                start_time = time.time()

                # Import here to avoid issues
                from faster_whisper import WhisperModel

                # Update progress
                with self._lock:
                    self._status[model_name].progress = 0.5
                    self._notify_status(model_name)

                # Load the model
                model = WhisperModel(
                    model_size_or_path=model_name,
                    device=device,
                    compute_type=compute_type,
                )

                load_time = time.time() - start_time

                # Update status
                with self._lock:
                    self._models[model_name] = model
                    self._status[model_name].state = LoadState.LOADED
                    self._status[model_name].progress = 1.0
                    self._status[model_name].load_time_seconds = load_time
                    self._status[model_name].memory_usage_mb = self.MODEL_MEMORY.get(model_name)
                    self._last_activity[model_name] = time.time()
                    self._notify_status(model_name)

                # Start auto-unload timer if configured
                if self._config.unload_after_idle_seconds > 0:
                    self._start_unload_timer(model_name)

            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {e}")
                with self._lock:
                    self._status[model_name].state = LoadState.ERROR
                    self._status[model_name].error_message = str(e)
                    self._notify_status(model_name)

        thread = threading.Thread(target=load_worker, daemon=True)
        thread.start()

        return self._status[model_name]

    def unload_model(self, model_name: str) -> bool:
        """
        Unload a model to free memory.

        Parameters
        ----------
        model_name
            Model identifier.

        Returns
        -------
        bool
            True if model was unloaded.
        """
        with self._lock:
            if model_name not in self._models:
                return False

            try:
                # Delete the model
                del self._models[model_name]

                # Update status
                self._status[model_name].state = LoadState.UNLOADED
                self._status[model_name].progress = 0.0

                # Notify callbacks
                self._notify_status(model_name)

                logger.info(f"Unloaded model {model_name}")
                return True

            except Exception as e:
                logger.error(f"Failed to unload model {model_name}: {e}")
                return False

    def get_model(self, model_name: str) -> Optional[Any]:
        """
        Get a loaded model instance.

        Parameters
        ----------
        model_name
            Model identifier.

        Returns
        -------
        The loaded model, or None if not loaded.
        """
        with self._lock:
            if model_name in self._models:
                self._last_activity[model_name] = time.time()
                return self._models[model_name]
        return None

    def preload_model(
        self,
        model_name: str,
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:
        """
        Preload a model in the background.

        Parameters
        ----------
        model_name
            Model identifier.
        device
            Target device.
        compute_type
            Compute type.
        """
        # Start loading without blocking
        self.load_model(model_name, device, compute_type)

    def is_loaded(self, model_name: str) -> bool:
        """
        Check if a model is loaded.

        Parameters
        ----------
        model_name
            Model identifier.

        Returns
        -------
        bool
            True if model is loaded.
        """
        with self._lock:
            return (
                model_name in self._models and
                self._status.get(model_name, ModelLoadStatus()).state == LoadState.LOADED
            )

    def register_callback(
        self,
        model_name: str,
        callback: Callable[[ModelLoadStatus], None]
    ) -> None:
        """
        Register a callback for status updates.

        Parameters
        ----------
        model_name
            Model identifier.
        callback
            Callback function.
        """
        with self._lock:
            if model_name not in self._callbacks:
                self._callbacks[model_name] = []
            self._callbacks[model_name].append(callback)

    def _notify_status(self, model_name: str) -> None:
        """Notify all registered callbacks of status change."""
        status = self._status.get(model_name)
        if not status:
            return

        callbacks = self._callbacks.get(model_name, []).copy()
        for callback in callbacks:
            try:
                callback(status)
            except Exception as e:
                logger.warning(f"Error in load callback: {e}")

    def _start_unload_timer(self, model_name: str) -> None:
        """Start auto-unload timer for a model."""
        if self._unload_timer:
            self._unload_timer.cancel()

        def check_and_unload():
            now = time.time()
            models_to_unload = []

            with self._lock:
                for name, last_activity in self._last_activity.items():
                    if now - last_activity > self._config.unload_after_idle_seconds:
                        models_to_unload.append(name)

            for name in models_to_unload:
                self.unload_model(name)

        self._unload_timer = threading.Timer(
            self._config.unload_after_idle_seconds,
            check_and_unload,
        )
        self._unload_timer.daemon = True
        self._unload_timer.start()

    def unload_all(self) -> int:
        """
        Unload all loaded models.

        Returns
        -------
        int
            Number of models unloaded.
        """
        with self._lock:
            model_names = list(self._models.keys())

        count = 0
        for name in model_names:
            if self.unload_model(name):
                count += 1

        return count

    def get_memory_usage_mb(self) -> int:
        """
        Get total memory usage of all loaded models.

        Returns
        -------
        int
            Total memory usage in MB.
        """
        with self._lock:
            total = 0
            for name, status in self._status.items():
                if status.state == LoadState.LOADED and status.memory_usage_mb:
                    total += status.memory_usage_mb
            return total


# Global model loader instance
_model_loader: Optional[ModelLoader] = None


def get_model_loader(config: Optional[ModelLoadConfig] = None) -> ModelLoader:
    """
    Get the global model loader instance.

    Parameters
    ----------
    config
        Optional configuration to use on first call.

    Returns
    -------
    ModelLoader
        The model loader instance.
    """
    global _model_loader
    if _model_loader is None:
        _model_loader = ModelLoader(config)
    return _model_loader
