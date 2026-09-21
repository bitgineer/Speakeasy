"""
Model wrapper for ASR engines (Whisper, Parakeet, Canary, Voxtral).

Provides a unified interface for loading and running different model types.

Performance optimizations:
- Fast model-cache check (O(1) via hf_hub_download on config.json, not O(n) snapshot_download)
- Lazy imports at module level (avoid per-load import overhead)
- CUDA warmup via warmup_cuda() called during server startup
- Pickle serialization cache for Whisper/Parakeet models (fast reload)
"""

import atexit
import hashlib
import json
import logging
import os
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import torch  # Ensure torch is imported for serialization

if TYPE_CHECKING:
    from numpy.typing import NDArray

# Type alias for progress callback: (downloaded_bytes, total_bytes) -> should_continue
ProgressCallback = Callable[[int, int], bool]

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy module-level imports — resolved once, reused across all loads
# ---------------------------------------------------------------------------
_FASTER_WHISPER_AVAILABLE = False
_WhisperModel = None
_NEMO_ASR_AVAILABLE = False
_ASRModel = None
_EncDecMultiTaskModel = None
_DILL_AVAILABLE = False
_VOXTRAL_AVAILABLE = False
_VoxtralForConditionalGeneration = None
_AutoProcessor = None
_BitsAndBytesConfig = None


def _ensure_faster_whisper():
    """Lazy-import faster_whisper (CTranslate2-based Whisper)."""
    global _FASTER_WHISPER_AVAILABLE, _WhisperModel
    if not _FASTER_WHISPER_AVAILABLE:
        from faster_whisper import WhisperModel

        _WhisperModel = WhisperModel
        _FASTER_WHISPER_AVAILABLE = True


def _ensure_nemo_asr():
    """Lazy-import NeMo ASR classes (heavy import chain)."""
    global _NEMO_ASR_AVAILABLE, _ASRModel, _EncDecMultiTaskModel
    if not _NEMO_ASR_AVAILABLE:
        from nemo.collections.asr.models import ASRModel, EncDecMultiTaskModel

        _ASRModel = ASRModel
        _EncDecMultiTaskModel = EncDecMultiTaskModel
        _NEMO_ASR_AVAILABLE = True


def _ensure_dill():
    """Lazy-check for dill availability (faster pickle serialization)."""
    global _DILL_AVAILABLE
    if not _DILL_AVAILABLE:
        try:
            import dill  # noqa: F401

            _DILL_AVAILABLE = True
        except ImportError:
            pass  # stays False


def _ensure_voxtral():
    """Lazy-import Voxtral dependencies (heavy transformers imports)."""
    global _VOXTRAL_AVAILABLE, _VoxtralForConditionalGeneration, _AutoProcessor, _BitsAndBytesConfig
    if not _VOXTRAL_AVAILABLE:
        from transformers import AutoProcessor, BitsAndBytesConfig

        try:
            from transformers import VoxtralForConditionalGeneration
        except ImportError:
            logger.warning(
                "VoxtralForConditionalGeneration not found. Install with: "
                "pip install git+https://github.com/huggingface/transformers.git"
            )
            raise ImportError(
                "Voxtral model requires a newer version of 'transformers'. "
                "Please run: pip install git+https://github.com/huggingface/transformers.git"
            )

        _AutoProcessor = AutoProcessor
        _BitsAndBytesConfig = BitsAndBytesConfig
        _VoxtralForConditionalGeneration = VoxtralForConditionalGeneration
        _VOXTRAL_AVAILABLE = True


# ---------------------------------------------------------------------------
# Fast model-cache check — O(1) instead of O(n) snapshot_download
# ---------------------------------------------------------------------------
def _is_hf_model_cached(repo_id: str) -> bool:
    """
    Check if a HuggingFace model is fully cached using a single file probe.

    Probes multiple common file names because model formats differ:
    - PyTorch/Transformers: config.json
    - NeMo models: *.nemo (probed via repo directory listing)
    - CTranslate2: model.bin, config.json

    Uses local_files_only=True for O(1) check vs snapshot_download's O(n).
    """
    from huggingface_hub import hf_hub_download
    from huggingface_hub.utils import LocalEntryNotFoundError

    # Probe files in priority order — first match wins
    probe_files = [
        "config.json",  # Standard HF / Transformers / Whisper
        "model.bin",  # CTranslate2 fallback
        "pytorch_model.bin",  # PyTorch fallback
    ]
    for filename in probe_files:
        try:
            hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_files_only=True,
            )
            return True
        except (LocalEntryNotFoundError, FileNotFoundError, OSError, Exception):
            continue

    # NeMo (.nemo) models: check if HF cache dir exists locally
    # Format: ~/.cache/huggingface/hub/models--org--name/snapshots/
    try:
        cache_root = os.path.expanduser(os.path.join("~", ".cache", "huggingface", "hub"))
        dir_name = "models--" + repo_id.replace("/", "--")
        cache_dir = os.path.join(cache_root, dir_name, "snapshots")
        if os.path.isdir(cache_dir):
            for entry in os.listdir(cache_dir):
                snap_path = os.path.join(cache_dir, entry)
                if os.path.isdir(snap_path) and os.listdir(snap_path):
                    return True
    except Exception:
        pass

    return False


def _resolve_hf_cache_path(repo_id: str) -> str | None:
    """
    Resolve the local cache path for a HuggingFace repo without scanning.

    Probes config.json first (fast, O(1)), falls back to snapshot directory
    check for .nemo models that lack a config.json.

    Returns the cache directory path if found, None otherwise.
    """
    from huggingface_hub import try_to_load_from_cache

    # Try standard config.json probe first
    try:
        result = try_to_load_from_cache(repo_id=repo_id, filename="config.json")
        if result:
            return str(Path(result).parent)
    except Exception:
        pass

    # Fall back to snapshot directory check (for .nemo models)
    try:
        cache_root = os.path.expanduser(os.path.join("~", ".cache", "huggingface", "hub"))
        dir_name = "models--" + repo_id.replace("/", "--")
        cache_dir = os.path.join(cache_root, dir_name, "snapshots")
        if os.path.isdir(cache_dir):
            for entry in os.listdir(cache_dir):
                snap_path = os.path.join(cache_dir, entry)
                if os.path.isdir(snap_path) and os.listdir(snap_path):
                    return snap_path
    except Exception:
        pass

    return None


def warmup_cuda():
    """
    Pre-warm CUDA to absorb first-touch overhead before any model loads.

    In WSL2 especially, the first CUDA call triggers driver IPC + context
    creation + JIT kernel compilation (5-10s). Call this during server startup
    so model loading doesn't pay this penalty.
    """
    try:
        if torch.cuda.is_available():
            logger.info("Warming up CUDA...")
            _start = time.time()
            _t = torch.zeros(1, device="cuda")
            _t = _t + 1
            del _t
            torch.cuda.synchronize()
            logger.info(f"CUDA warmup complete in {time.time() - _start:.2f}s")
            return True
    except Exception as e:
        logger.warning(f"CUDA warmup skipped: {e}")
    return False


# Track temp files for emergency cleanup at exit
_temp_files_to_cleanup: set[str] = set()


def safe_delete(path: str, max_retries: int = 5, base_delay: float = 0.1) -> None:
    """
    Safely delete a file with retries to handle transient Windows file locks.
    """
    if not path or not os.path.exists(path):
        return

    for i in range(max_retries):
        try:
            os.unlink(path)
            return
        except PermissionError:
            if i == max_retries - 1:
                logger.warning(f"Failed to delete temp file after {max_retries} retries: {path}")
            time.sleep(base_delay * (2**i))
        except Exception as e:
            logger.warning(f"Error deleting temp file {path}: {e}")
            return


def safe_write_manifest(manifest_data: list) -> str:
    """
    Write manifest data to a temp file safely for Windows.
    Closes the handle immediately so other processes can read it.
    """
    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8", suffix=".json") as f:
        for item in manifest_data:
            f.write(json.dumps(item) + "\n")
        temp_path = f.name

    return temp_path


def _cleanup_temp_files_at_exit():
    """Emergency cleanup of temp files at process exit."""
    for path in list(_temp_files_to_cleanup):
        safe_delete(path)


atexit.register(_cleanup_temp_files_at_exit)

logger = logging.getLogger(__name__)


class ModelType(str, Enum):
    """Supported ASR model types."""

    WHISPER = "whisper"
    PARAKEET = "parakeet"
    CANARY = "canary"
    VOXTRAL = "voxtral"


@dataclass
class TranscriptionResult:
    """Result from a transcription operation."""

    text: str
    duration_ms: int  # Audio recording duration in milliseconds
    language: str | None = None
    model_used: str | None = None
    processing_ms: int | None = None  # Time taken to transcribe (for debugging)


class ModelWrapper:
    """
    Encapsulates loading and running different ASR model types.

    Supports:
    - whisper: Faster-Whisper (CTranslate2)
    - parakeet: NVIDIA Parakeet-TDT (NeMo)
    - canary: NVIDIA Canary (NeMo)
    - voxtral: Mistral Voxtral-Mini-3B (Transformers)
    """

    def __init__(
        self,
        model_type: str,
        model_name: str,
        device: str = "cuda",
        compute_type: str | None = None,
    ):
        """
        Initialize the model wrapper.

        Args:
            model_type: One of 'whisper', 'parakeet', 'canary', 'voxtral'
            model_name: Model name or HuggingFace repo ID
            device: Device to run on ('cuda' or 'cpu')
            compute_type: Compute precision ('float16', 'int8', etc.)
        """
        self.model_type = ModelType(model_type.lower())
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type

        self._model = None
        self._processor = None
        self._transcription_request_cls = None
        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        """Check if model is currently loaded."""
        return self._loaded

    def load(
        self,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        """
        Load the model into memory with optimizations for faster startup.

        Args:
            progress_callback: Optional callback function that receives
                (downloaded_bytes, total_bytes) and returns True to continue
                or False to cancel the download.
        """
        if self._loaded:
            logger.info(f"Model {self.model_name} already loaded")
            return

        import time

        self._load_start_time = time.time()

        logger.info(f"Loading {self.model_type.value} model: {self.model_name}")
        if self.model_type == ModelType.WHISPER:
            logger.info("Target: <10s for cached models, <60s for first download")
        elif self.model_type == ModelType.PARAKEET:
            logger.info("Target: ~30s (NeMo loads from .nemo format - this is normal)")
        elif self.model_type == ModelType.CANARY:
            logger.info("Target: ~30s (NeMo loads from .nemo format - this is normal)")
        elif self.model_type == ModelType.VOXTRAL:
            logger.info("Target: <15s for cached models, <60s for first download")

        if self.model_type == ModelType.WHISPER:
            self._load_whisper(progress_callback)
        elif self.model_type == ModelType.PARAKEET:
            self._load_parakeet(progress_callback)
        elif self.model_type == ModelType.CANARY:
            self._load_canary(progress_callback)
        elif self.model_type == ModelType.VOXTRAL:
            self._load_voxtral(progress_callback)
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

        self._loaded = True
        self._load_duration = time.time() - self._load_start_time
        logger.info(f"Model {self.model_name} loaded successfully in {self._load_duration:.2f}s")

        if self._load_duration > 20:
            logger.warning(
                f"Model loading took {self._load_duration:.2f}s (target: <15s for cached)"
            )
            logger.info(
                "Consider optimizations: 1) Ensure model is cached 2) Check disk I/O 3) Use faster storage"
            )

    def unload(self) -> None:
        """Unload the model from memory to free resources."""
        if not self._loaded:
            return

        import gc

        import torch

        self._model = None
        self._processor = None
        self._transcription_request_cls = None
        self._loaded = False

        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        logger.info(f"Model {self.model_name} unloaded")

    def _resolve_hf_name(self, model_name: str) -> str:
        """Resolve short whisper model names to full HF repo IDs."""
        if "/" not in model_name and model_name in [
            "tiny",
            "tiny.en",
            "base",
            "base.en",
            "small",
            "small.en",
            "medium",
            "medium.en",
            "large",
            "large-v1",
            "large-v2",
            "large-v3",
            "distil-large-v2",
            "distil-large-v3",
            "distil-medium.en",
            "distil-small.en",
        ]:
            if model_name.startswith("distil-"):
                return f"Systran/faster-distil-whisper-{model_name.removeprefix('distil-')}"
            return f"Systran/faster-whisper-{model_name}"
        return model_name

    def _download_hf_model(
        self,
        model_name: str,
        progress_callback: ProgressCallback,
    ) -> str:
        """
        Pre-download a HuggingFace model with progress tracking.

        OPTIMIZED: Uses O(1) _is_hf_model_cached() probe instead of the
        O(n) snapshot_download(local_files_only=True) full-tree walk.
        """
        from huggingface_hub import snapshot_download
        from tqdm import tqdm

        hf_model_name = self._resolve_hf_name(model_name)

        # --- Fast path: model already cached ---
        if _is_hf_model_cached(hf_model_name):
            cached_path = _resolve_hf_cache_path(hf_model_name)
            if cached_path:
                logger.info(f"Model found in cache (fast check): {cached_path}")
                progress_callback(1, 1)
                return cached_path
            # Fall through to snapshot_download for edge cases
            logger.debug(
                "Fast cache check passed but path resolution failed, using snapshot_download"
            )

        # --- Slow path: download needed ---
        total_downloaded: int = 0
        total_size: int = 0
        last_callback_time: float = 0.0
        callback_interval: float = 0.5

        class ProgressTqdm(tqdm):
            def __init__(self, *args, **kwargs):
                nonlocal total_size
                super().__init__(*args, **kwargs)
                if self.total is not None:
                    total_size += int(self.total)

            def update(self, n=1):
                nonlocal total_downloaded, last_callback_time
                super().update(n)
                total_downloaded += int(n) if n is not None else 0
                now = time.time()
                if now - last_callback_time >= callback_interval:
                    last_callback_time = now
                    if not progress_callback(total_downloaded, total_size):
                        raise RuntimeError("Download cancelled by user")

        try:
            logger.info(f"Pre-downloading model: {hf_model_name}")
            local_dir = snapshot_download(
                repo_id=hf_model_name,
                tqdm_class=ProgressTqdm,
            )
            progress_callback(total_size, total_size)
            logger.info(f"Model downloaded to: {local_dir}")
            return local_dir
        except RuntimeError:
            raise
        except Exception as e:
            logger.error(f"Failed to download model: {e}")
            raise

    def _load_whisper(
        self,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        """Load Faster-Whisper model with fast cache check and lazy imports."""
        _ensure_faster_whisper()

        hf_model_name = self._resolve_hf_name(self.model_name)

        # --- Fast path: model cached, skip download check entirely ---
        if _is_hf_model_cached(hf_model_name):
            logger.info(f"Whisper model cached (fast check): {hf_model_name}")
            # Resolve cache path so WhisperModel doesn't do its own lookup
            cached_path = _resolve_hf_cache_path(hf_model_name)
            model_arg = cached_path if cached_path else self.model_name
        elif progress_callback:
            # Model not cached — download with progress
            self._download_hf_model(self.model_name, progress_callback)
            model_arg = self.model_name
        else:
            model_arg = self.model_name

        logger.info(
            f"Initializing CTranslate2 WhisperModel (compute_type={self.compute_type or 'float16'})..."
        )
        _start = time.time()
        self._model = _WhisperModel(
            model_size_or_path=model_arg,
            device=self.device,
            compute_type=self.compute_type or "float16",
        )
        logger.info(f"CTranslate2 WhisperModel init took {time.time() - _start:.2f}s")

    def _try_load_pickle_cache(self, cache_key: str) -> bool:
        """
        Try to load a NeMo model from pickle/dill serialization cache.

        Returns True if loaded successfully, False if cache miss or corrupted.
        """
        import torch as _t

        cache_dir = Path.home() / ".speakeasy" / "model_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        model_hash = hashlib.md5(cache_key.encode()).hexdigest()
        cache_path = cache_dir / f"parakeet_{model_hash}.pkl"

        if not cache_path.exists():
            return False

        if cache_path.stat().st_size == 0:
            logger.warning(f"Found empty cache file: {cache_path}. Deleting.")
            try:
                os.unlink(cache_path)
            except Exception:
                pass
            return False

        logger.info(f"Found model in serialization cache: {cache_path}")
        try:
            pickle_start = time.time()
            if _DILL_AVAILABLE:
                import dill

                self._model = _t.load(cache_path, map_location=self.device, pickle_module=dill)
            else:
                self._model = _t.load(cache_path, map_location=self.device)
            logger.info(f"Loaded from cache in {time.time() - pickle_start:.2f}s")
            return True
        except Exception as e:
            logger.warning(f"Failed to load from cache: {e}. Falling back to standard load.")
            try:
                os.unlink(cache_path)
            except Exception:
                pass
            return False

    def _load_parakeet_from_nemo(self) -> None:
        """Load Parakeet model via NeMo's from_pretrained (unavoidable ~25s)."""
        cache_check_start = time.time()
        is_cached = _is_hf_model_cached(self.model_name)
        logger.info(
            f"Model cache check took {time.time() - cache_check_start:.2f}s (cached={is_cached})"
        )

        logger.info("Initializing NeMo model architecture...")
        nemo_start = time.time()
        self._model = _ASRModel.from_pretrained(
            model_name=self.model_name,
            map_location=self.device,
        ).eval()
        logger.info(f"NeMo model initialization took {time.time() - nemo_start:.2f}s")

    def _apply_cuda_optimizations(self) -> None:
        """Apply CUDA inference optimizations after model is loaded."""
        import torch as _t

        if self.device != "cuda" or not _t.cuda.is_available():
            return

        logger.info("Applying CUDA optimizations...")
        try:
            self._model = self._model.to(self.device)
            self._model.eval()
            _t.backends.cudnn.benchmark = True
            logger.info("CUDA optimizations applied")
        except Exception as e:
            logger.warning(f"Failed to apply some CUDA optimizations: {e}")

    def _load_parakeet(
        self,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        """Load NVIDIA Parakeet model via NeMo — orchestrated with cache + fallback."""
        _ensure_nemo_asr()
        _ensure_dill()

        logger.info("Starting Parakeet model load with optimizations...")
        load_start = time.time()

        # Pre-download if needed (uses fast O(1) cache check internally)
        if progress_callback and not _is_hf_model_cached(self.model_name):
            self._download_hf_model(self.model_name, progress_callback)

        # Try pickle cache first, fall back to NeMo from_pretrained
        if not self._try_load_pickle_cache(self.model_name):
            self._load_parakeet_from_nemo()

        self._apply_cuda_optimizations()

        total_duration = time.time() - load_start
        logger.info(f"Total Parakeet load time: {total_duration:.2f}s")

    def _load_canary(
        self,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        """Load NVIDIA Canary model via NeMo with fast cache + lazy imports."""
        _ensure_nemo_asr()
        import torch as _t

        logger.info("Starting Canary model load with optimizations...")
        load_start = time.time()

        # Pre-download if needed (uses fast O(1) cache check internally)
        if progress_callback and not _is_hf_model_cached(self.model_name):
            self._download_hf_model(self.model_name, progress_callback)

        logger.info("Initializing NeMo Canary model architecture...")
        nemo_start = time.time()
        self._model = _EncDecMultiTaskModel.from_pretrained(
            self.model_name,
            map_location=self.device,
        ).eval()
        nemo_duration = time.time() - nemo_start
        logger.info(f"NeMo Canary initialization took {nemo_duration:.2f}s")

        if self.device == "cuda" and _t.cuda.is_available():
            logger.info("Applying CUDA optimizations...")
            _t.backends.cudnn.benchmark = True
            self._model = self._model.to(self.device)

        total_duration = time.time() - load_start
        logger.info(f"Total Canary load time: {total_duration:.2f}s")

    def _load_voxtral(
        self,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        """Load Mistral Voxtral model via Transformers with fast cache + lazy imports."""
        _ensure_voxtral()

        # Pre-download if needed (uses fast O(1) cache check internally)
        if progress_callback and not _is_hf_model_cached(self.model_name):
            self._download_hf_model(self.model_name, progress_callback)

        # Import for TranscriptionRequest
        from mistral_common.protocol.transcription.request import (
            TranscriptionRequest as _BaseTranscriptionRequest,
        )
        from pydantic_extra_types.language_code import LanguageAlpha2

        class TranscriptionRequest(_BaseTranscriptionRequest):
            language: LanguageAlpha2 | None = None
            prompt: str | None = None

        self._transcription_request_cls = TranscriptionRequest
        self._processor = _AutoProcessor.from_pretrained(self.model_name)

        if self.compute_type == "int8":
            quant_cfg = _BitsAndBytesConfig(load_in_8bit=True)
            self._model = _VoxtralForConditionalGeneration.from_pretrained(
                self.model_name,
                quantization_config=quant_cfg,
                device_map="cuda",
            ).eval()
        elif self.compute_type == "int4":
            quant_cfg = _BitsAndBytesConfig(load_in_4bit=True)
            self._model = _VoxtralForConditionalGeneration.from_pretrained(
                self.model_name,
                quantization_config=quant_cfg,
                device_map="cuda",
            ).eval()
        else:
            compute_dtype = {
                "float16": torch.float16,
                "bfloat16": torch.bfloat16,
            }.get(self.compute_type or "float16", torch.float16)

            self._model = _VoxtralForConditionalGeneration.from_pretrained(
                self.model_name,
                dtype=compute_dtype,
                device_map="cuda",
            ).eval()

    def transcribe(
        self,
        audio_data: "NDArray[np.float32]",
        sample_rate: int = 16000,
        language: str | None = None,
        instruction: str | None = None,
    ) -> TranscriptionResult:
        """
        Transcribe audio data and return result.

        Args:
            audio_data: Numpy array of audio samples (float32, mono)
            sample_rate: Sample rate in Hz (default 16000)
            language: Language code or 'auto' for auto-detection
            instruction: Optional instruction or system prompt

        Returns:
            TranscriptionResult with transcribed text and metadata
        """
        if not self._loaded:
            raise RuntimeError("Model not loaded. Call load() first.")

        import time

        start_time = time.perf_counter()

        try:
            if self.model_type == ModelType.WHISPER:
                text = self._transcribe_whisper(audio_data, language)
            elif self.model_type == ModelType.PARAKEET:
                text = self._transcribe_parakeet(audio_data, sample_rate)
            elif self.model_type == ModelType.CANARY:
                text = self._transcribe_canary(audio_data, sample_rate, language)
            elif self.model_type == ModelType.VOXTRAL:
                text = self._transcribe_voxtral(audio_data, sample_rate, language, instruction)
            else:
                raise ValueError(f"Unknown model type: {self.model_type}")

            duration_ms = int((time.perf_counter() - start_time) * 1000)

            return TranscriptionResult(
                text=text.strip(),
                duration_ms=duration_ms,
                language=language,
                model_used=self.model_name,
            )

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise

    def _transcribe_whisper(self, audio_data: "NDArray[np.float32]", language: str | None) -> str:
        """Transcribe using Faster-Whisper."""
        segments, _ = self._model.transcribe(
            audio_data,
            beam_size=5,
            condition_on_previous_text=False,
            language=(language if language and language != "auto" else None),
        )
        return " ".join(segment.text.strip() for segment in segments)

    def _transcribe_parakeet(self, audio_data: "NDArray[np.float32]", sample_rate: int) -> str:
        """Transcribe using NVIDIA Parakeet."""
        import soundfile as sf
        import torch

        temp_wav_path = None
        temp_manifest_path = None

        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_wav_path = f.name
                sf.write(f.name, audio_data, sample_rate)

            duration = len(audio_data) / sample_rate
            manifest_data = [
                {
                    "audio_filepath": temp_wav_path,
                    "text": "",
                    "duration": duration,
                }
            ]
            temp_manifest_path = safe_write_manifest(manifest_data)

            with torch.inference_mode():
                out = self._model.transcribe(temp_manifest_path, verbose=False)
            return out[0].text if out else ""

        finally:
            safe_delete(temp_wav_path)
            safe_delete(temp_manifest_path)

    def _transcribe_canary(
        self,
        audio_data: "NDArray[np.float32]",
        sample_rate: int,
        language: str | None,
    ) -> str:
        """Transcribe using NVIDIA Canary."""
        import soundfile as sf

        lang = language or "en-en"
        lang_parts = lang.split("-")
        if len(lang_parts) != 2:
            source_lang, target_lang = "en", "en"
        else:
            source_lang, target_lang = lang_parts

        temp_wav_path = None
        temp_manifest_path = None
        try:
            # Windows-safe temp file handling
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_wav_path = f.name
                sf.write(f.name, audio_data, sample_rate)

            duration = len(audio_data) / sample_rate
            manifest_data = [
                {
                    "audio_filepath": temp_wav_path,
                    "text": "",
                    "duration": duration,
                }
            ]
            temp_manifest_path = safe_write_manifest(manifest_data)

            out = self._model.transcribe(
                audio=temp_manifest_path,
                source_lang=source_lang,
                target_lang=target_lang,
                verbose=False,
            )
            return out[0].text.strip() if out and len(out) > 0 else ""
        except Exception:
            raise
        finally:
            safe_delete(temp_wav_path)
            safe_delete(temp_manifest_path)

    def _transcribe_voxtral(
        self,
        audio_data: "NDArray[np.float32]",
        sample_rate: int,
        language: str | None,
        instruction: str | None = None,
    ) -> str:
        """Transcribe using Mistral Voxtral with chunking for long audio."""
        max_duration_seconds = 30
        max_samples = max_duration_seconds * sample_rate

        if len(audio_data) > max_samples:
            logger.warning(
                f"Audio length ({len(audio_data) / sample_rate:.2f}s) exceeds "
                f"Voxtral limit ({max_duration_seconds}s). Processing in chunks."
            )
            chunks = []
            for i in range(0, len(audio_data), max_samples):
                chunk = audio_data[i : i + max_samples]
                if len(chunk) >= 1000:  # Skip very short chunks
                    chunks.append(chunk)

            full_text = ""
            for i, chunk in enumerate(chunks):
                try:
                    # Pass instruction to each chunk? Or maybe only the first?
                    # For consistency, passing to all chunks ensures style/grammar correction applies to all.
                    result = self._transcribe_voxtral_chunk(
                        chunk, sample_rate, language, instruction
                    )
                    if result.strip():
                        full_text += result + " "
                except Exception as e:
                    logger.error(f"Failed to transcribe chunk {i}: {e}")
            return full_text.strip()
        else:
            return self._transcribe_voxtral_chunk(audio_data, sample_rate, language, instruction)

    def _transcribe_voxtral_chunk(
        self,
        audio_data: "NDArray[np.float32]",
        sample_rate: int,
        language: str | None,
        instruction: str | None = None,
    ) -> str:
        """Transcribe a single chunk using Voxtral."""
        import soundfile as sf
        import torch

        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio:
                temp_path = tmp_audio.name
                sf.write(tmp_audio.name, audio_data, sample_rate)

            audio_path = temp_path

            class FileWrapper:
                def __init__(self, file_obj):
                    self.file = file_obj

            with open(audio_path, "rb") as f:
                wrapped_file = FileWrapper(f)

                openai_req = {
                    "model": self.model_name,
                    "file": wrapped_file,
                }
                if language and language != "auto":
                    openai_req["language"] = language

                if instruction:
                    openai_req["prompt"] = instruction

                tr = self._transcription_request_cls.from_openai(openai_req)
                tok = self._processor.tokenizer.tokenizer.encode_transcription(tr)

                input_features = self._processor.feature_extractor(
                    audio_data,
                    sampling_rate=sample_rate,
                    return_tensors="pt",
                ).input_features.to(self._model.device)

                if hasattr(tok, "tokens") and tok.tokens is not None:
                    token_ids = torch.tensor([tok.tokens], device=self._model.device)
                else:
                    logger.warning("Token IDs might be invalid")
                    return ""

                with torch.no_grad():
                    ids = self._model.generate(
                        input_features=input_features,
                        input_ids=token_ids,
                        max_new_tokens=500,
                        num_beams=1,
                    )
                    return self._processor.batch_decode(ids, skip_special_tokens=True)[0]
        except Exception:
            raise
        finally:
            safe_delete(temp_path)


_gpu_info_cache = None
_gpu_info_last_check = 0
GPU_INFO_CACHE_TTL = 5.0  # seconds


def get_gpu_info() -> dict:
    """Get GPU information for model recommendations."""
    global _gpu_info_cache, _gpu_info_last_check
    import time

    # Return cached result if valid
    if _gpu_info_cache and (time.time() - _gpu_info_last_check < GPU_INFO_CACHE_TTL):
        return _gpu_info_cache

    try:
        import torch

        if not torch.cuda.is_available():
            result = {"available": False, "name": None, "vram_gb": 0}
        else:
            device = torch.cuda.current_device()
            props = torch.cuda.get_device_properties(device)
            vram_gb = props.total_memory / (1024**3)

            result = {
                "available": True,
                "name": props.name,
                "vram_gb": round(vram_gb, 1),
                "cuda_version": torch.version.cuda,
            }

        # Update cache
        _gpu_info_cache = result
        _gpu_info_last_check = time.time()
        return result

    except Exception as e:
        logger.error(f"Error getting GPU info: {e}")
        return {"available": False, "name": None, "vram_gb": 0}


def recommend_model(vram_gb: float, needs_translation: bool = False) -> tuple[str, str]:
    """
    Recommend a model based on available VRAM.

    Returns:
        Tuple of (model_type, model_name)
    """
    if vram_gb >= 10:
        return ("voxtral", "mistralai/Voxtral-Mini-3B-2507")
    elif vram_gb >= 6 and needs_translation:
        return ("canary", "nvidia/canary-1b-v2")
    elif vram_gb >= 4:
        return ("parakeet", "nvidia/parakeet-tdt-0.6b-v3")
    elif vram_gb >= 2:
        return ("whisper", "small")
    else:
        return ("whisper", "tiny")
