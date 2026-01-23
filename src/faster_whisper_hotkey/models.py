"""
ASR model wrapper for faster-whisper-hotkey.

This module provides a unified interface for loading and running different
Automatic Speech Recognition (ASR) models. It supports Whisper, Parakeet,
Canary, and Voxtral models with model-specific optimizations.

Classes
-------
ModelWrapper
    Encapsulates loading and running different model types.

Notes
-----
- Voxtral has a 30-second audio limit and handles chunking automatically.
- Canary requires source-target language pair specification.
- Parakeet does not require language specification.
- Whisper supports the widest range of languages.
- Heavy model libraries are lazy-loaded for faster startup.
- GPU initialization failures automatically fall back to CPU with user notification.
"""

import os
import tempfile
import logging
import torch
import soundfile as sf

from typing import Optional

# Lazy-load heavy model libraries
_transformers_available = False
_nemo_available = False
_faster_whisper_available = False

# Cache for lazy-loaded modules
_VoxtralForConditionalGeneration = None
_AutoProcessor = None
_BitsAndBytesConfig = None
_ASRModel = None
_EncDecMultiTaskModel = None
_WhisperModel = None


def _ensure_transformers():
    """Lazy-load transformers library."""
    global _transformers_available, _VoxtralForConditionalGeneration, _AutoProcessor, _BitsAndBytesConfig
    if not _transformers_available:
        try:
            from transformers import (
                VoxtralForConditionalGeneration,
                AutoProcessor,
                BitsAndBytesConfig,
            )
            _VoxtralForConditionalGeneration = VoxtralForConditionalGeneration
            _AutoProcessor = AutoProcessor
            _BitsAndBytesConfig = BitsAndBytesConfig
            _transformers_available = True
        except ImportError:
            _transformers_available = False
    return _transformers_available


def _ensure_nemo():
    """Lazy-load nemo library."""
    global _nemo_available, _ASRModel, _EncDecMultiTaskModel
    if not _nemo_available:
        try:
            from nemo.collections.asr.models import ASRModel, EncDecMultiTaskModel
            _ASRModel = ASRModel
            _EncDecMultiTaskModel = EncDecMultiTaskModel
            _nemo_available = True
        except ImportError:
            _nemo_available = False
    return _nemo_available


def _ensure_faster_whisper():
    """Lazy-load faster_whisper library."""
    global _faster_whisper_available, _WhisperModel
    if not _faster_whisper_available:
        try:
            from faster_whisper import WhisperModel
            _WhisperModel = WhisperModel
            _faster_whisper_available = True
        except ImportError:
            _faster_whisper_available = False
    return _faster_whisper_available


logger = logging.getLogger(__name__)

# Import error handling for user-friendly messages
try:
    from .error_handling import (
        ErrorCategory,
        GPUInitializationError,
        get_error_recovery,
        get_error_reporter,
    )
except ImportError:
    # Fallback if error_handling module is not available
    ErrorCategory = None
    GPUInitializationError = None
    def get_error_recovery(): return None
    def get_error_reporter(): return None


class ModelWrapper:
    """
    Encapsulates loading and running different model types (whisper, parakeet, canary, voxtral).
    """

    def __init__(self, settings):
        self.settings = settings
        self.model_type = settings.model_type.lower()
        self.model = None
        self.processor = None
        self.TranscriptionRequest = None
        self._model_ref = None
        self._load_model()

    def _load_model(self):
        mt = self.model_type
        device = self.settings.device
        compute_type = getattr(self.settings, "compute_type", None)

        logger.info(f"Loading model: type={mt}, name={self.settings.model_name}, device={device}, compute_type={compute_type}")

        # For Whisper, try GPU first, fall back to CPU on error
        if mt == "whisper":
            self._load_whisper_with_fallback(device, compute_type)
        elif mt == "parakeet":
            self._load_parakeet_model(device)
        elif mt == "canary":
            self._load_canary_model(device)
        elif mt == "voxtral":
            self._load_voxtral_model()
        else:
            error_msg = f"Unknown model type: {self.model_type}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def _load_whisper_with_fallback(self, device: str, compute_type: str):
        """
        Load Whisper model with automatic CPU fallback on GPU error.

        If GPU initialization fails, automatically falls back to CPU
        and notifies the user with a friendly message.

        Parameters
        ----------
        device
            Requested device ("cuda" or "cpu").
        compute_type
            Requested compute type (float16, int8, etc.).
        """
        if not _ensure_faster_whisper():
            raise ImportError("faster_whisper library not available")

        original_device = device
        cpu_fallback = False

        try:
            self.model = _WhisperModel(
                model_size_or_path=self.settings.model_name,
                device=device,
                compute_type=compute_type,
            )
            logger.info(f"Whisper model loaded successfully on {device}")

        except Exception as e:
            # Check if this is a GPU-related error
            is_gpu_error = self._is_gpu_error(e)

            if is_gpu_error and device == "cuda":
                logger.warning(f"GPU initialization failed: {e}. Falling back to CPU...")
                cpu_fallback = True

                # Try CPU fallback with appropriate compute type
                cpu_compute_type = "int8" if compute_type in ("float16", "int8") else compute_type

                try:
                    self.model = _WhisperModel(
                        model_size_or_path=self.settings.model_name,
                        device="cpu",
                        compute_type=cpu_compute_type,
                    )
                    logger.info(f"Whisper model loaded successfully on CPU (fallback from GPU)")

                    # Notify user about CPU fallback
                    self._notify_gpu_fallback(original_device, "cpu", e)

                except Exception as cpu_error:
                    # CPU fallback also failed
                    logger.error(f"CPU fallback also failed: {cpu_error}")
                    self._report_gpu_init_error(original_device, compute_type, cpu_error)
                    raise RuntimeError(
                        f"Failed to load model on both GPU and CPU. "
                        f"GPU error: {e}. CPU error: {cpu_error}"
                    ) from cpu_error
            else:
                # Not a GPU error or not using CUDA - report the error
                self._report_gpu_init_error(device, compute_type, e)
                raise

    def _is_gpu_error(self, exception: Exception) -> bool:
        """
        Check if an exception is related to GPU initialization.

        Parameters
        ----------
        exception
            The exception to check.

        Returns
        -------
        bool
            True if this is a GPU-related error.
        """
        error_message = str(exception).lower()
        error_type = type(exception).__name__.lower()

        gpu_error_indicators = [
            "cuda",
            "gpu",
            "device",
            "out of memory",
            "oom",
            "nvidia",
            "cublas",
            "cudnn",
            "runtime error",
            "driver",
        ]

        # Check for torch.cuda specific errors
        if "cuda" in error_type or "outofmemory" in error_type:
            return True

        # Check error message for GPU-related terms
        return any(indicator in error_message for indicator in gpu_error_indicators)

    def _notify_gpu_fallback(self, from_device: str, to_device: str, error: Exception):
        """
        Notify user about GPU to CPU fallback.

        Parameters
        ----------
        from_device
            Original device that failed.
        to_device
            Fallback device being used.
        error
            The error that triggered the fallback.
        """
        # Log warning
        logger.warning(
            f"GPU initialization failed ({from_device}): {error}. "
            f"Proceeding with CPU ({to_device}). Transcription will be slower."
        )

        # Create user-friendly error report if available
        reporter = get_error_reporter()
        if reporter and ErrorCategory:
            try:
                reporter.create_report(
                    exception=error,
                    category=ErrorCategory.GPU_INIT,
                    message="GPU acceleration is unavailable. Using CPU instead.",
                    suggestions=[
                        "Update your GPU drivers",
                        "Check if CUDA is properly installed",
                        "Ensure your GPU has enough available memory",
                        "Consider using a smaller model for better performance",
                    ],
                    recovery_attempted=True,
                    recovery_successful=True,
                )
            except Exception:
                pass  # Don't fail if error reporting fails

    def _report_gpu_init_error(self, device: str, compute_type: str, error: Exception):
        """
        Report GPU initialization error with user-friendly message.

        Parameters
        ----------
        device
            Device that failed.
        compute_type
            Compute type that was attempted.
        error
            The error that occurred.
        """
        # Log error
        logger.error(f"GPU initialization failed: device={device}, compute_type={compute_type}, error={error}")

        # Create user-friendly error report if available
        reporter = get_error_reporter()
        if reporter and ErrorCategory:
            try:
                reporter.create_report(
                    exception=error,
                    category=ErrorCategory.GPU_INIT,
                    message="Could not initialize GPU for transcription.",
                    suggestions=[
                        "Update your GPU drivers",
                        "Check if CUDA is properly installed",
                        "Ensure your GPU has enough available memory",
                        "Try using CPU mode instead",
                        "Consider using a smaller model",
                    ],
                    recovery_attempted=False,
                    recovery_successful=False,
                )
            except Exception:
                pass  # Don't fail if error reporting fails

    def _load_parakeet_model(self, device: str):
        """Load Parakeet model with error handling."""
        if not _ensure_nemo():
            raise ImportError("nemo library not available")
        logger.info(f"Loading Parakeet model from {self.settings.model_name}...")

        try:
            self.model = _ASRModel.from_pretrained(
                model_name=self.settings.model_name,
                map_location=self.settings.device,
            ).eval()
            self._model_ref = self.model
            logger.info(f"Parakeet model loaded successfully")
        except Exception as e:
            self._report_gpu_init_error(device, "N/A", e)
            raise

    def _load_canary_model(self, device: str):
        """Load Canary model with error handling."""
        if not _ensure_nemo():
            raise ImportError("nemo library not available")
        logger.info(f"Loading Canary model from {self.settings.model_name}...")

        try:
            self.model = _EncDecMultiTaskModel.from_pretrained(
                self.settings.model_name, map_location=self.settings.device
            ).eval()
            self._model_ref = self.model
            logger.info(f"Canary model loaded successfully")
        except Exception as e:
            self._report_gpu_init_error(device, "N/A", e)
            raise

    def _load_voxtral_model(self):
        """Load Voxtral model with error handling."""
        if not _ensure_transformers():
            raise ImportError("transformers library not available")
        from typing import Optional
        from mistral_common.protocol.transcription.request import (
            TranscriptionRequest as _TR,
        )
        from pydantic_extra_types.language_code import LanguageAlpha2

        class TranscriptionRequest(_TR):
            language: Optional[LanguageAlpha2] = None

        repo_id = self.settings.model_name
        logger.info(f"Loading Voxtral model from {repo_id}...")

        try:
            self.processor = _AutoProcessor.from_pretrained(repo_id)
        except Exception as e:
            logger.error(f"Failed to load Voxtral processor: {e}")
            raise RuntimeError(f"Voxtral processor loading failed: {e}")

        try:
            if self.settings.compute_type == "int8":
                quant_cfg = _BitsAndBytesConfig(load_in_8bit=True)
                self.model = _VoxtralForConditionalGeneration.from_pretrained(
                    repo_id,
                    quantization_config=quant_cfg,
                    device_map="cuda",
                ).eval()

            elif self.settings.compute_type == "int4":
                quant_cfg = _BitsAndBytesConfig(load_in_4bit=True)
                self.model = _VoxtralForConditionalGeneration.from_pretrained(
                    repo_id,
                    quantization_config=quant_cfg,
                    device_map="cuda",
                ).eval()

            else:
                compute_dtype = {
                    "float16": torch.float16,
                    "bfloat16": torch.bfloat16,
                }.get(self.settings.compute_type, torch.float16)

                self.model = _VoxtralForConditionalGeneration.from_pretrained(
                    repo_id,
                    dtype=compute_dtype,
                    device_map="cuda",
                ).eval()

            self.TranscriptionRequest = TranscriptionRequest
            logger.info(f"Voxtral model loaded successfully")

        except Exception as e:
            self._report_gpu_init_error("cuda", self.settings.compute_type, e)
            raise

    def transcribe(
        self, audio_data, sample_rate: int = 16000, language: Optional[str] = None
    ) -> str:
        """
        Transcribe a numpy array of audio samples and return transcribed text.
        For some models (canary, voxtral) we write to a temp file and call model utilities requiring a file.
        For Voxtral-Mini-3B-2507, handles potential input size limits by chunking.
        """
        mt = self.model_type

        # Validate audio input
        if audio_data is None or len(audio_data) == 0:
            logger.warning("Empty audio data provided to transcribe")
            return ""

        audio_duration = len(audio_data) / sample_rate
        if audio_duration < 0.1:
            logger.debug(f"Audio too short ({audio_duration:.3f}s), skipping transcription")
            return ""

        try:
            if mt == "whisper":
                segments, _ = self.model.transcribe(
                    audio_data,
                    beam_size=5,
                    condition_on_previous_text=False,
                    language=(language if language and language != "auto" else None),
                )
                return " ".join(segment.text.strip() for segment in segments)

            elif mt == "parakeet":
                with torch.inference_mode():
                    out = self.model.transcribe([audio_data])
                return out[0].text if out else ""

            elif mt == "canary":
                lang = language or "en-en"
                lang_parts = lang.split("-")
                if len(lang_parts) != 2:
                    source_lang, target_lang = "en", "en"
                else:
                    source_lang, target_lang = lang_parts

                temp_path = None
                try:
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                        temp_path = f.name
                    sf.write(temp_path, audio_data, sample_rate)
                    out = self.model.transcribe(
                        audio=[temp_path],
                        source_lang=source_lang,
                        target_lang=target_lang,
                    )
                    return out[0].text.strip() if out and len(out) > 0 else ""
                finally:
                    if temp_path and os.path.exists(temp_path):
                        os.remove(temp_path)

            elif mt == "voxtral":
                # --- Voxtral-Mini-3B-2507-specific transcription with chunking ---
                # Based on documentation and typical behavior, 30s is a safe limit for the encoder.
                MAX_DURATION_SECONDS = 30
                samples_per_second = sample_rate
                max_samples = MAX_DURATION_SECONDS * samples_per_second

                if len(audio_data) > max_samples:
                    logger.warning(
                        f"Audio length ({len(audio_data) / samples_per_second:.2f}s) exceeds Voxtral-Mini-3B-2507's recommended input limit ({MAX_DURATION_SECONDS}s). "
                        "Processing in chunks."
                    )
                    chunks = []
                    for i in range(0, len(audio_data), max_samples):
                        chunk = audio_data[i : i + max_samples]
                        if len(chunk) < 1000:  # Skip very short chunks (likely noise)
                            continue
                        chunks.append(chunk)

                    # Process each chunk and concatenate results
                    full_text = ""
                    for i, chunk in enumerate(chunks):
                        try:
                            result = self._transcribe_single_chunk_voxtral(
                                chunk, sample_rate, language
                            )
                            if result.strip():
                                full_text += result + " "
                        except Exception as e:
                            logger.error(f"Failed to transcribe chunk {i}: {e}")
                            # Optionally add a placeholder or skip
                            pass

                    return full_text.strip()
                else:
                    # If audio is within limits, process it directly
                    return self._transcribe_single_chunk_voxtral(
                        audio_data, sample_rate, language
                    )

            else:
                raise ValueError(f"Unknown model type: {mt}")

        except torch.cuda.OutOfMemoryError as e:
            logger.error(f"GPU out of memory during transcription: {e}")
            return ""
        except ValueError as e:
            logger.error(f"Invalid input or configuration during transcription: {e}")
            return ""
        except RuntimeError as e:
            logger.error(f"Runtime error during transcription: {e}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error during model.transcribe: {e}")
            return ""

    def _transcribe_single_chunk_voxtral(
        self, audio_data, sample_rate: int, language: Optional[str]
    ) -> str:
        """
        Internal helper to transcribe a single chunk of audio for Voxtral-Mini-3B-2507.
        This handles the file I/O and model call.
        """
        # Write chunk to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio:
            sf.write(tmp_audio.name, audio_data, sample_rate)
            audio_path = tmp_audio.name

        try:
            # Create a wrapper class to mimic what the processor expects
            class FileWrapper:
                def __init__(self, file_obj):
                    self.file = file_obj

            with open(audio_path, "rb") as f:
                wrapped_file = FileWrapper(f)

                # Prepare request similar to test_voxtral.py
                openai_req = {
                    "model": self.settings.model_name,
                    "file": wrapped_file,
                }
                if language and language != "auto":
                    openai_req["language"] = language

                tr = self.TranscriptionRequest.from_openai(openai_req)

                # Get tokens from the processor's tokenizer
                tok = self.processor.tokenizer.tokenizer.encode_transcription(tr)

                try:
                    input_features = self.processor.feature_extractor(
                        audio_data,
                        sampling_rate=sample_rate,
                        return_tensors="pt",
                    ).input_features.to(self.model.device)

                    # Get the tokens correctly (they should be in tok.tokens)
                    if hasattr(tok, "tokens") and tok.tokens is not None:
                        token_ids = torch.tensor([tok.tokens], device=self.model.device)
                    else:
                        logger.warning("Token IDs might be invalid")
                        return ""

                except Exception as e:
                    logger.error(f"Feature extraction failed: {e}")
                    raise

                # Generate using the model
                with torch.no_grad():
                    ids = self.model.generate(
                        input_features=input_features,
                        input_ids=token_ids,
                        max_new_tokens=500,
                        num_beams=1,
                    )
                decoded = self.processor.batch_decode(ids, skip_special_tokens=True)[0]
                return decoded

        except Exception as e:
            logger.error(f"Voxtral-Mini-3B-2507 transcription error in chunk: {e}")
            raise
        finally:
            try:
                os.unlink(audio_path)
            except Exception:
                pass

    def transcribe_streaming(
        self,
        audio_data,
        sample_rate: int = 16000,
        language: Optional[str] = None,
        callback=None,
    ):
        """
        Stream transcription results as they are generated.

        Yields tuples of (text, confidence) for each segment as it's transcribed.
        For Whisper model, uses internal chunking to provide real-time results.

        Args:
            audio_data: Numpy array of audio samples
            sample_rate: Audio sample rate (default: 16000)
            language: Language code for transcription
            callback: Optional callback function(segment_text, confidence, is_final)

        Returns:
            Generator yielding (text, confidence, is_final) tuples
        """
        mt = self.model_type
        try:
            if mt == "whisper":
                # Whisper supports streaming via its transcribe generator
                segments, info = self.model.transcribe(
                    audio_data,
                    beam_size=5,
                    condition_on_previous_text=False,
                    language=(language if language and language != "auto" else None),
                    word_timestamps=True,  # Enable word-level timestamps for better streaming
                )

                accumulated_text = ""
                for segment in segments:
                    segment_text = segment.text.strip()
                    if not segment_text:
                        continue

                    # Calculate average confidence for this segment
                    # Whisper provides probability scores via segment.avg_logprob
                    confidence = getattr(segment, 'avg_logprob', None)
                    if confidence is not None:
                        # Convert logprob to probability-like score (0-1)
                        # Typical logprob range is -2 to 0, normalize to 0-1
                        confidence = max(0, min(1, (confidence + 2) / 2))

                    accumulated_text += (" " if accumulated_text else "") + segment_text

                    if callback:
                        try:
                            callback(accumulated_text, confidence, False)
                        except Exception as e:
                            logger.debug(f"Streaming callback error: {e}")

                    yield (accumulated_text, confidence, False)

                # Final result with all segments combined
                if callback:
                    try:
                        callback(accumulated_text, 1.0, True)
                    except Exception:
                        pass

                yield (accumulated_text, 1.0, True)

            elif mt in ("parakeet", "canary", "voxtral"):
                # For non-Whisper models, fall back to non-streaming transcription
                # These models don't support chunked streaming
                result = self.transcribe(audio_data, sample_rate, language)
                if callback:
                    try:
                        callback(result, 1.0, True)
                    except Exception:
                        pass
                yield (result, 1.0, True)

            else:
                raise ValueError(f"Unknown model type: {mt}")

        except Exception as e:
            logger.error(f"Error during model.transcribe_streaming: {e}")
            if callback:
                try:
                    callback("", 0.0, True)
                except Exception:
                    pass
            yield ("", 0.0, True)

    def cleanup(self):
        """
        Clean up resources and free memory.

        Call this method to free GPU memory and other resources when the model
        is no longer needed (e.g., before exiting or switching models).
        """
        try:
            # Clear CUDA cache if using GPU
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                logger.debug("CUDA cache cleared")

            # For PyTorch models, explicitly delete references
            if self._model_ref is not None:
                del self._model_ref
                self._model_ref = None

            # The main model reference
            if self.model is not None:
                # For WhisperModel, there's no explicit cleanup needed
                # For PyTorch models, we'll delete the reference
                if hasattr(self.model, 'parameters'):
                    del self.model
                    self.model = None

            # Delete processor if it exists
            if self.processor is not None:
                del self.processor
                self.processor = None

            logger.debug("Model resources cleaned up")

        except Exception as e:
            logger.warning(f"Error during model cleanup: {e}")

    def __del__(self):
        """Destructor to ensure cleanup on object deletion."""
        try:
            self.cleanup()
        except Exception:
            pass  # Ignore errors during destruction
