"""
Model wrapper for ASR engines (Whisper, Parakeet, Canary, Voxtral).

Provides a unified interface for loading and running different model types.
"""

import atexit
import logging
import os
import tempfile
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Callable, Optional, Set

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

# Type alias for progress callback: (downloaded_bytes, total_bytes) -> should_continue
ProgressCallback = Callable[[int, int], bool]

logger = logging.getLogger(__name__)

# Track temp files for emergency cleanup at exit
_temp_files_to_cleanup: Set[str] = set()


def _cleanup_temp_files_at_exit():
    """Emergency cleanup of temp files at process exit."""
    for path in list(_temp_files_to_cleanup):
        try:
            if os.path.exists(path):
                os.unlink(path)
        except Exception:
            pass


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
    duration_ms: int
    language: Optional[str] = None
    model_used: Optional[str] = None


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
        compute_type: Optional[str] = None,
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
        progress_callback: Optional[ProgressCallback] = None,
    ) -> None:
        """
        Load the model into memory. Call this before transcribing.

        Args:
            progress_callback: Optional callback function that receives
                (downloaded_bytes, total_bytes) and returns True to continue
                or False to cancel the download.
        """
        if self._loaded:
            logger.info(f"Model {self.model_name} already loaded")
            return

        logger.info(f"Loading {self.model_type.value} model: {self.model_name}")

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
        logger.info(f"Model {self.model_name} loaded successfully")

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

    def _download_hf_model(
        self,
        model_name: str,
        progress_callback: ProgressCallback,
    ) -> str:
        """
        Pre-download a HuggingFace model with progress tracking.

        Args:
            model_name: HuggingFace model name or path
            progress_callback: Callback receiving (downloaded_bytes, total_bytes)
                returning True to continue or False to cancel

        Returns:
            Path to the downloaded model

        Raises:
            RuntimeError: If download is cancelled
            Exception: If download fails
        """
        from huggingface_hub import snapshot_download
        from huggingface_hub.utils import tqdm as hf_tqdm
        from tqdm import tqdm

        # Track cumulative progress across all files
        total_downloaded: int = 0
        total_size: int = 0
        last_callback_time: float = 0.0
        callback_interval: float = 0.5  # Call callback at most every 0.5 seconds

        class ProgressTqdm(tqdm):
            """Custom tqdm that reports progress to callback."""

            def __init__(self, *args, **kwargs):
                nonlocal total_size
                super().__init__(*args, **kwargs)
                if self.total is not None:
                    total_size += int(self.total)

            def update(self, n=1):
                nonlocal total_downloaded, last_callback_time
                super().update(n)
                total_downloaded += int(n) if n is not None else 0

                # Throttle callback calls
                import time

                now = time.time()
                if now - last_callback_time >= callback_interval:
                    last_callback_time = now
                    # Call the progress callback
                    should_continue = progress_callback(total_downloaded, total_size)
                    if not should_continue:
                        raise RuntimeError("Download cancelled by user")

        try:
            # For whisper models that are just size names (tiny, small, etc.),
            # convert to the full HuggingFace repo name
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
                # faster-whisper uses Systran models
                if model_name.startswith("distil-"):
                    hf_model_name = f"Systran/faster-{model_name}"
                else:
                    hf_model_name = f"Systran/faster-whisper-{model_name}"
            else:
                hf_model_name = model_name

            logger.info(f"Pre-downloading model: {hf_model_name}")

            # Download with progress tracking
            local_dir = snapshot_download(
                repo_id=hf_model_name,
                tqdm_class=ProgressTqdm,
            )

            # Final callback to report completion
            progress_callback(total_size, total_size)

            logger.info(f"Model downloaded to: {local_dir}")
            return local_dir

        except RuntimeError as e:
            if "cancelled" in str(e).lower():
                logger.info("Download cancelled by user")
                raise
            raise
        except Exception as e:
            logger.error(f"Failed to download model: {e}")
            raise

    def _load_whisper(
        self,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> None:
        """Load Faster-Whisper model with optional progress tracking."""
        from faster_whisper import WhisperModel

        # Pre-download the model with progress tracking if callback provided
        if progress_callback:
            self._download_hf_model(self.model_name, progress_callback)

        self._model = WhisperModel(
            model_size_or_path=self.model_name,
            device=self.device,
            compute_type=self.compute_type or "float16",
        )

    def _load_parakeet(
        self,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> None:
        """Load NVIDIA Parakeet model via NeMo with optional progress tracking."""
        from nemo.collections.asr.models import ASRModel

        # Pre-download the model with progress tracking if callback provided
        if progress_callback:
            self._download_hf_model(self.model_name, progress_callback)

        self._model = ASRModel.from_pretrained(
            model_name=self.model_name,
            map_location=self.device,
        ).eval()

    def _load_canary(
        self,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> None:
        """Load NVIDIA Canary model via NeMo with optional progress tracking."""
        from nemo.collections.asr.models import EncDecMultiTaskModel

        # Pre-download the model with progress tracking if callback provided
        if progress_callback:
            self._download_hf_model(self.model_name, progress_callback)

        self._model = EncDecMultiTaskModel.from_pretrained(
            self.model_name,
            map_location=self.device,
        ).eval()

    def _load_voxtral(
        self,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> None:
        """Load Mistral Voxtral model via Transformers with optional progress tracking."""
        import torch
        from transformers import AutoProcessor, BitsAndBytesConfig

        try:
            from transformers import VoxtralForConditionalGeneration
        except ImportError:
            logger.warning("VoxtralForConditionalGeneration not found. Using generic auto class.")
            # Fallback or re-raise with helpful message
            raise ImportError(
                "Voxtral model requires a newer version of 'transformers'. "
                "Please run: pip install git+https://github.com/huggingface/transformers.git"
            )

        # Pre-download the model with progress tracking if callback provided
        if progress_callback:
            self._download_hf_model(self.model_name, progress_callback)

        # Import for TranscriptionRequest
        from mistral_common.protocol.transcription.request import (
            TranscriptionRequest as _TR,
        )
        from pydantic_extra_types.language_code import LanguageAlpha2

        # Create extended TranscriptionRequest with optional language
        class TranscriptionRequest(_TR):
            language: Optional[LanguageAlpha2] = None

        self._transcription_request_cls = TranscriptionRequest
        self._processor = AutoProcessor.from_pretrained(self.model_name)

        if self.compute_type == "int8":
            quant_cfg = BitsAndBytesConfig(load_in_8bit=True)
            self._model = VoxtralForConditionalGeneration.from_pretrained(
                self.model_name,
                quantization_config=quant_cfg,
                device_map="cuda",
            ).eval()
        elif self.compute_type == "int4":
            quant_cfg = BitsAndBytesConfig(load_in_4bit=True)
            self._model = VoxtralForConditionalGeneration.from_pretrained(
                self.model_name,
                quantization_config=quant_cfg,
                device_map="cuda",
            ).eval()
        else:
            compute_dtype = {
                "float16": torch.float16,
                "bfloat16": torch.bfloat16,
            }.get(self.compute_type or "float16", torch.float16)

            self._model = VoxtralForConditionalGeneration.from_pretrained(
                self.model_name,
                dtype=compute_dtype,
                device_map="cuda",
            ).eval()

    def transcribe(
        self,
        audio_data: "NDArray[np.float32]",
        sample_rate: int = 16000,
        language: Optional[str] = None,
    ) -> TranscriptionResult:
        """
        Transcribe audio data and return result.

        Args:
            audio_data: Numpy array of audio samples (float32, mono)
            sample_rate: Sample rate in Hz (default 16000)
            language: Language code or 'auto' for auto-detection

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
                text = self._transcribe_parakeet(audio_data)
            elif self.model_type == ModelType.CANARY:
                text = self._transcribe_canary(audio_data, sample_rate, language)
            elif self.model_type == ModelType.VOXTRAL:
                text = self._transcribe_voxtral(audio_data, sample_rate, language)
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

    def _transcribe_whisper(
        self, audio_data: "NDArray[np.float32]", language: Optional[str]
    ) -> str:
        """Transcribe using Faster-Whisper."""
        segments, _ = self._model.transcribe(
            audio_data,
            beam_size=5,
            condition_on_previous_text=False,
            language=(language if language and language != "auto" else None),
        )
        return " ".join(segment.text.strip() for segment in segments)

    def _transcribe_parakeet(self, audio_data: "NDArray[np.float32]") -> str:
        """Transcribe using NVIDIA Parakeet."""
        import torch

        with torch.inference_mode():
            out = self._model.transcribe([audio_data])
        return out[0].text if out else ""

    def _transcribe_canary(
        self, audio_data: "NDArray[np.float32]", sample_rate: int, language: Optional[str]
    ) -> str:
        """Transcribe using NVIDIA Canary."""
        import soundfile as sf

        lang = language or "en-en"
        lang_parts = lang.split("-")
        if len(lang_parts) != 2:
            source_lang, target_lang = "en", "en"
        else:
            source_lang, target_lang = lang_parts

        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as f:
                temp_path = f.name
                sf.write(temp_path, audio_data, sample_rate)
                out = self._model.transcribe(
                    audio=[temp_path],
                    source_lang=source_lang,
                    target_lang=target_lang,
                )
                return out[0].text.strip() if out and len(out) > 0 else ""
        except Exception:
            raise

    def _transcribe_voxtral(
        self, audio_data: "NDArray[np.float32]", sample_rate: int, language: Optional[str]
    ) -> str:
        """Transcribe using Mistral Voxtral with chunking for long audio."""
        MAX_DURATION_SECONDS = 30
        max_samples = MAX_DURATION_SECONDS * sample_rate

        if len(audio_data) > max_samples:
            logger.warning(
                f"Audio length ({len(audio_data) / sample_rate:.2f}s) exceeds "
                f"Voxtral limit ({MAX_DURATION_SECONDS}s). Processing in chunks."
            )
            chunks = []
            for i in range(0, len(audio_data), max_samples):
                chunk = audio_data[i : i + max_samples]
                if len(chunk) >= 1000:  # Skip very short chunks
                    chunks.append(chunk)

            full_text = ""
            for i, chunk in enumerate(chunks):
                try:
                    result = self._transcribe_voxtral_chunk(chunk, sample_rate, language)
                    if result.strip():
                        full_text += result + " "
                except Exception as e:
                    logger.error(f"Failed to transcribe chunk {i}: {e}")
            return full_text.strip()
        else:
            return self._transcribe_voxtral_chunk(audio_data, sample_rate, language)

    def _transcribe_voxtral_chunk(
        self, audio_data: "NDArray[np.float32]", sample_rate: int, language: Optional[str]
    ) -> str:
        """Transcribe a single chunk using Voxtral."""
        import soundfile as sf
        import torch

        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp_audio:
                sf.write(tmp_audio.name, audio_data, sample_rate)
                audio_path = tmp_audio.name

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


def get_gpu_info() -> dict:
    """Get GPU information for model recommendations."""
    try:
        import torch

        if not torch.cuda.is_available():
            return {"available": False, "name": None, "vram_gb": 0}

        device = torch.cuda.current_device()
        props = torch.cuda.get_device_properties(device)
        vram_gb = props.total_memory / (1024**3)

        return {
            "available": True,
            "name": props.name,
            "vram_gb": round(vram_gb, 1),
            "cuda_version": torch.version.cuda,
        }
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
