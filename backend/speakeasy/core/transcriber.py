"""
Transcriber service for audio recording and transcription.

This service manages the recording state and coordinates with the model wrapper
for transcription. Designed for use via the FastAPI server.

Performance optimizations:
- Minimal buffer copies in audio callback (only copy, no redundant astype)
- Pre-allocated buffer concatenation using np.concatenate
- Chunked transcription for long recordings (>5 min) with progress reporting
"""

import asyncio
import logging
import threading
import time
import gc
import torch
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Callable, Optional

import numpy as np
import sounddevice as sd

from .models import ModelWrapper, ProgressCallback, TranscriptionResult

if TYPE_CHECKING:
    from numpy.typing import NDArray

logger = logging.getLogger(__name__)

# Type alias for transcription progress callback: (current_chunk, total_chunks, chunk_text) -> None
TranscriptionProgressCallback = Callable[[int, int, str], None]


class TranscriberState(str, Enum):
    """State of the transcriber service."""

    IDLE = "idle"
    LOADING = "loading"
    READY = "ready"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"
    ERROR = "error"


@dataclass
class RecordingResult:
    """Result of a recording session."""

    audio_data: "NDArray[np.float32]"
    sample_rate: int
    duration_seconds: float


class TranscriberService:
    """
    Service for managing audio recording and transcription.

    This class handles:
    - Model loading and unloading
    - Audio recording from the microphone
    - Coordination of transcription
    - State management

    Designed for API-based control via the FastAPI server.
    """

    SAMPLE_RATE = 16000  # Required by most ASR models
    CHANNELS = 1  # Mono
    MAX_RECORDING_SECONDS = 600  # 10 minutes max

    def __init__(
        self,
        on_state_change: Optional[Callable[[TranscriberState], None]] = None,
    ):
        """
        Initialize the transcriber service.

        Args:
            on_state_change: Callback when state changes
        """
        self._state = TranscriberState.IDLE
        self._on_state_change = on_state_change

        # Model
        self._model: Optional[ModelWrapper] = None

        # Audio recording
        self._audio_buffer: list[np.ndarray] = []
        self._stream: Optional[sd.InputStream] = None
        self._recording_start_time: Optional[float] = None
        self._lock = threading.Lock()

        # Device
        self._device_name: Optional[str] = None
        self._device_id: Optional[int] = None

        # Asyncio loop for thread-safe callbacks
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = None

    @property
    def state(self) -> TranscriberState:
        """Get current state."""
        return self._state

    def _set_state(self, state: TranscriberState) -> None:
        """Set state and notify callback."""
        self._state = state
        if self._on_state_change:
            try:
                # Thread-safe callback dispatch
                if self._loop and self._loop.is_running():
                    self._loop.call_soon_threadsafe(self._on_state_change, state)
                else:
                    self._on_state_change(state)
            except Exception as e:
                logger.error(f"State change callback error: {e}")

    @property
    def is_model_loaded(self) -> bool:
        """Check if a model is loaded."""
        return self._model is not None and self._model.is_loaded

    @property
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._state == TranscriberState.RECORDING

    def load_model(
        self,
        model_type: str,
        model_name: str,
        device: str = "cuda",
        compute_type: Optional[str] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> None:
        """
        Load an ASR model.

        Args:
            model_type: Type of model (whisper, parakeet, canary, voxtral)
            model_name: Model name or HuggingFace repo ID
            device: Device to use (cuda or cpu)
            compute_type: Compute precision
            progress_callback: Optional callback for download progress tracking
                that receives (downloaded_bytes, total_bytes) and returns
                True to continue or False to cancel
        """
        # Save args for reload
        self._last_load_args = {
            "model_type": model_type,
            "model_name": model_name,
            "device": device,
            "compute_type": compute_type,
            "progress_callback": progress_callback,
        }

        self._set_state(TranscriberState.LOADING)

        try:
            # Unload existing model if any
            if self._model:
                self._model.unload()

            # Create and load new model
            self._model = ModelWrapper(
                model_type=model_type,
                model_name=model_name,
                device=device,
                compute_type=compute_type,
            )
            self._model.load(progress_callback=progress_callback)

            self._set_state(TranscriberState.READY)
            logger.info(f"Model loaded: {model_type}/{model_name}")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self._set_state(TranscriberState.ERROR)
            raise

    def reload_model(self) -> None:
        """
        Reload the current model to recover from errors (e.g. CUDA).
        """
        if not hasattr(self, "_last_load_args") or not self._last_load_args:
            logger.warning("Cannot reload model: no model loaded yet")
            return

        logger.info("Reloading model...")
        self.unload_model()

        # Force cleanup
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        # Re-load
        self.load_model(**self._last_load_args)

    def unload_model(self) -> None:
        """Unload the current model."""
        if self._model:
            self._model.unload()
            self._model = None
        self._set_state(TranscriberState.IDLE)

    def set_device(self, device_name: Optional[str] = None) -> None:
        """
        Set the audio input device.

        Args:
            device_name: Device name, or None for default
        """
        if device_name is None:
            self._device_name = None
            self._device_id = None
            return

        # Find device by name
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            if device_name.lower() in dev["name"].lower() and dev["max_input_channels"] > 0:
                self._device_name = dev["name"]
                self._device_id = i
                logger.info(f"Audio device set to: {self._device_name}")
                return

        raise ValueError(f"Audio device not found: {device_name}")

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: dict,
        status: sd.CallbackFlags,
    ) -> None:
        """
        Callback for audio stream.

        Performance: Since we specify dtype=np.float32 in InputStream,
        indata is already float32. We only need to copy (sounddevice reuses buffer)
        and flatten (mono channel extraction).
        """
        if status:
            logger.warning(f"Audio status: {status}")

        with self._lock:
            # Optimized: indata is already float32, just copy and flatten
            # copy() is required because sounddevice reuses the buffer
            self._audio_buffer.append(indata.copy().flatten())

    def _cleanup_recording_state(self) -> None:
        """Clean up recording state (stream, buffer, timing). Called on error or cancel."""
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception as e:
                logger.warning(f"Error closing stream: {e}")
            finally:
                self._stream = None

        with self._lock:
            self._audio_buffer = []

        self._recording_start_time = None

    def start_recording(self) -> None:
        """Start recording audio from the microphone."""
        if self._state == TranscriberState.RECORDING:
            logger.warning("Already recording")
            return

        if not self.is_model_loaded:
            raise RuntimeError("No model loaded")

        with self._lock:
            self._audio_buffer = []

        # Create and start stream with try-finally for cleanup on error
        try:
            self._stream = sd.InputStream(
                samplerate=self.SAMPLE_RATE,
                channels=self.CHANNELS,
                dtype=np.float32,
                device=self._device_id,
                callback=self._audio_callback,
            )
            self._stream.start()
            self._recording_start_time = time.time()

            self._set_state(TranscriberState.RECORDING)
            logger.info("Recording started")
        except Exception:
            # Ensure buffer is cleared on stream creation/start failure
            with self._lock:
                self._audio_buffer = []
            if self._stream:
                try:
                    self._stream.stop()
                    self._stream.close()
                except Exception as e:
                    logger.warning(f"Error closing stream: {e}")
                finally:
                    self._stream = None
            self._recording_start_time = None
            raise

    def stop_recording(self) -> RecordingResult:
        """
        Stop recording and return the audio data.

        Returns:
            RecordingResult with audio data
        """
        if self._state != TranscriberState.RECORDING:
            raise RuntimeError("Not recording")

        try:
            # Stop stream
            if self._stream:
                self._stream.stop()
                self._stream.close()
                self._stream = None

            # Calculate duration
            duration = time.time() - self._recording_start_time if self._recording_start_time else 0

            # Concatenate audio buffer
            with self._lock:
                if not self._audio_buffer:
                    raise RuntimeError("No audio recorded")

                audio_data = np.concatenate(self._audio_buffer)
                self._audio_buffer = []

            self._recording_start_time = None
            self._set_state(TranscriberState.READY)
            logger.info(f"Recording stopped, duration: {duration:.2f}s")

            return RecordingResult(
                audio_data=audio_data,
                sample_rate=self.SAMPLE_RATE,
                duration_seconds=duration,
            )
        except Exception:
            # Ensure complete cleanup on any error
            self._cleanup_recording_state()
            raise
        finally:
            # Always ensure buffer is cleared and timing reset
            with self._lock:
                self._audio_buffer = []
            self._recording_start_time = None

    # Threshold for chunked transcription: 5 minutes at 16kHz
    CHUNK_THRESHOLD_SAMPLES = 5 * 60 * SAMPLE_RATE  # 4,800,000 samples
    # Chunk size for long recordings: 2 minutes (balance between progress updates and efficiency)
    CHUNK_SIZE_SAMPLES = 2 * 60 * SAMPLE_RATE  # 1,920,000 samples

    def transcribe(
        self,
        audio_data: "NDArray[np.float32]",
        sample_rate: int = 16000,
        language: Optional[str] = None,
        progress_callback: Optional[TranscriptionProgressCallback] = None,
        instruction: Optional[str] = None,
    ) -> TranscriptionResult:
        """
        Transcribe audio data with optional chunked processing for long recordings.

        Args:
            audio_data: Audio samples as float32 numpy array
            sample_rate: Sample rate of the audio
            language: Language code or 'auto'
            progress_callback: Optional callback for progress updates during long transcriptions.
                Receives (current_chunk, total_chunks, chunk_text) for each completed chunk.
            instruction: Optional instruction or system prompt (e.g. for grammar correction)

        Returns:
            TranscriptionResult with transcribed text

        Performance:
            - For recordings >5 minutes, audio is processed in 2-minute chunks
            - Progress callback is invoked after each chunk completes
            - Chunks are processed sequentially to maintain text order
        """
        if not self.is_model_loaded:
            raise RuntimeError("No model loaded")

        self._set_state(TranscriberState.TRANSCRIBING)

        try:
            # Check if chunked processing is needed
            if len(audio_data) > self.CHUNK_THRESHOLD_SAMPLES:
                result = self._transcribe_chunked(
                    audio_data=audio_data,
                    sample_rate=sample_rate,
                    language=language,
                    progress_callback=progress_callback,
                    instruction=instruction,
                )
            else:
                # Standard single-pass transcription
                result = self._model.transcribe(
                    audio_data=audio_data,
                    sample_rate=sample_rate,
                    language=language,
                    instruction=instruction,
                )
                # Report completion for single-pass
                if progress_callback:
                    progress_callback(1, 1, result.text)

            self._set_state(TranscriberState.READY)
            return result

        except Exception as e:
            self._set_state(TranscriberState.ERROR)
            raise

    def _transcribe_chunked(
        self,
        audio_data: "NDArray[np.float32]",
        sample_rate: int,
        language: Optional[str],
        progress_callback: Optional[TranscriptionProgressCallback],
        instruction: Optional[str] = None,
    ) -> TranscriptionResult:
        """
        Transcribe long audio in chunks with progress reporting.

        Args:
            audio_data: Full audio data
            sample_rate: Sample rate
            language: Language code
            progress_callback: Progress callback
            instruction: Optional instruction

        Returns:
            Combined TranscriptionResult
        """
        import time

        start_time = time.perf_counter()
        total_samples = len(audio_data)
        chunk_size = self.CHUNK_SIZE_SAMPLES

        # Calculate number of chunks
        num_chunks = (total_samples + chunk_size - 1) // chunk_size

        logger.info(
            f"Chunked transcription: {total_samples / sample_rate:.1f}s audio "
            f"in {num_chunks} chunks of {chunk_size / sample_rate:.0f}s each"
        )

        texts = []
        for i in range(num_chunks):
            chunk_start = i * chunk_size
            chunk_end = min((i + 1) * chunk_size, total_samples)
            chunk_data = audio_data[chunk_start:chunk_end]

            # Skip very short final chunks (< 0.5 seconds)
            if len(chunk_data) < sample_rate // 2:
                logger.debug(f"Skipping short final chunk: {len(chunk_data)} samples")
                continue

            # Transcribe chunk
            chunk_result = self._model.transcribe(
                audio_data=chunk_data,
                sample_rate=sample_rate,
                language=language,
                instruction=instruction,
            )

            chunk_text = chunk_result.text.strip()
            if chunk_text:
                texts.append(chunk_text)

            # Report progress
            if progress_callback:
                progress_callback(i + 1, num_chunks, chunk_text)

            logger.debug(f"Chunk {i + 1}/{num_chunks} transcribed: {len(chunk_text)} chars")

        # Combine results
        combined_text = " ".join(texts)
        duration_ms = int((time.perf_counter() - start_time) * 1000)

        return TranscriptionResult(
            text=combined_text,
            duration_ms=duration_ms,
            language=language,
            model_used=self._model.model_name if self._model else None,
        )

    def transcribe_file(
        self,
        file_path: str,
        language: Optional[str] = None,
        progress_callback: Optional[TranscriptionProgressCallback] = None,
        instruction: Optional[str] = None,
    ) -> TranscriptionResult:
        """
        Transcribe an audio file.

        Args:
            file_path: Path to the audio file
            language: Language code or 'auto'
            progress_callback: Optional callback for progress updates
            instruction: Optional instruction

        Returns:
            TranscriptionResult with transcribed text
        """
        if not self.is_model_loaded:
            raise RuntimeError("No model loaded")

        try:
            # Use faster_whisper's robust audio decoding (handles ffmpeg, resampling to 16k)
            from faster_whisper.audio import decode_audio

            audio_data = decode_audio(file_path, sampling_rate=self.SAMPLE_RATE)
        except ImportError:
            # Fallback if faster_whisper is not importable (should be rare in prod)
            logger.warning("faster_whisper not found, falling back to soundfile")
            import soundfile as sf
            import scipy.signal

            audio, sr = sf.read(file_path, dtype="float32")
            if len(audio.shape) > 1:
                audio = audio.mean(axis=1)

            if sr != self.SAMPLE_RATE:
                # Resample using scipy
                number_of_samples = round(len(audio) * float(self.SAMPLE_RATE) / sr)
                audio_data = scipy.signal.resample(audio, number_of_samples)
            else:
                audio_data = audio

        except Exception as e:
            logger.error(f"Error reading audio file {file_path}: {e}")
            raise

        return self.transcribe(
            audio_data=audio_data,
            sample_rate=self.SAMPLE_RATE,
            language=language,
            progress_callback=progress_callback,
            instruction=instruction,
        )

    def stop_and_transcribe(
        self,
        language: Optional[str] = None,
        progress_callback: Optional[TranscriptionProgressCallback] = None,
        instruction: Optional[str] = None,
    ) -> TranscriptionResult:
        """
        Stop recording and transcribe immediately.

        This is a convenience method that combines stop_recording() and transcribe().

        Args:
            language: Language code or 'auto'
            progress_callback: Optional callback for progress updates during long transcriptions.
                Receives (current_chunk, total_chunks, chunk_text) for each completed chunk.
            instruction: Optional instruction

        Returns:
            TranscriptionResult with transcribed text
        """
        recording = self.stop_recording()

        # Get the actual audio recording duration in milliseconds
        audio_duration_ms = int(recording.duration_seconds * 1000)

        # Use the transcribe method which handles chunking automatically
        result = self.transcribe(
            audio_data=recording.audio_data,
            sample_rate=recording.sample_rate,
            language=language,
            progress_callback=progress_callback,
            instruction=instruction,
        )

        # Replace processing time with actual audio duration
        # Store processing time separately for debugging
        return TranscriptionResult(
            text=result.text,
            duration_ms=audio_duration_ms,  # Actual audio recording duration
            language=result.language,
            model_used=result.model_used,
            processing_ms=result.duration_ms,  # Keep the transcription processing time
        )

    def cancel_recording(self) -> None:
        """Cancel the current recording without transcribing."""
        if self._state != TranscriberState.RECORDING:
            return

        try:
            self._cleanup_recording_state()
        finally:
            # Always ensure buffer is cleared and timing reset
            with self._lock:
                self._audio_buffer = []
            self._recording_start_time = None
            self._set_state(
                TranscriberState.READY if self.is_model_loaded else TranscriberState.IDLE
            )
            logger.info("Recording cancelled")

    def cleanup(self) -> None:
        """Clean up all resources including model and recording state."""
        try:
            self._cleanup_recording_state()
        finally:
            # Always ensure buffer is cleared and timing reset
            with self._lock:
                self._audio_buffer = []
            self._recording_start_time = None
            self.unload_model()


def list_audio_devices() -> list[dict]:
    """
    List available audio input devices.

    Returns:
        List of device info dictionaries
    """
    devices = sd.query_devices()
    input_devices = []

    for i, dev in enumerate(devices):
        if dev["max_input_channels"] > 0:
            input_devices.append(
                {
                    "id": i,
                    "name": dev["name"],
                    "channels": dev["max_input_channels"],
                    "sample_rate": dev["default_samplerate"],
                    "is_default": i == sd.default.device[0],
                }
            )

    return input_devices
