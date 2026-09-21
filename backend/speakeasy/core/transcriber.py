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
import gc
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

import numpy as np
import scipy.signal
import sounddevice as sd
import torch

from .models import ProgressCallback, TranscriptionResult

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from .models import ModelWrapper

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


class AudioRecorder:
    """
    Manages audio device selection, stream capture, and buffer management.

    Extracted from TranscriberService to isolate audio I/O concerns.
    Uses callbacks for state transitions to avoid coupling to TranscriberService.
    """

    def __init__(
        self,
        target_sample_rate: int = 16000,
        channels: int = 1,
        on_state_change: Callable[[TranscriberState], None] | None = None,
        is_model_loaded_check: Callable[[], bool] | None = None,
    ):
        self._target_sample_rate = target_sample_rate
        self._channels = channels
        self._on_state_change = on_state_change
        self._is_model_loaded = is_model_loaded_check or (lambda: False)

        # Audio buffer and stream
        self._buffer: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._recording_start_time: float | None = None
        self._lock = threading.Lock()

        # Device selection
        self._device_name: str | None = None
        self._device_id: int | None = None
        self._native_samplerate: int | None = None

    # -- Device management --

    def set_device(self, device_name: str | None = None) -> None:
        """Set the audio input device by name, or reset to default."""
        if device_name is None:
            self._device_name = None
            self._device_id = None
            return

        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            if device_name.lower() in dev["name"].lower() and dev["max_input_channels"] > 0:
                self._device_name = dev["name"]
                self._device_id = i
                logger.info(f"Audio device set to: {self._device_name}")
                return

        raise ValueError(f"Audio device not found: {device_name}")

    @property
    def target_sample_rate(self) -> int:
        return self._target_sample_rate

    # -- Callback for sounddevice stream --

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: dict,
        status: sd.CallbackFlags,
    ) -> None:
        """Callback for audio stream. Minimal copy for performance."""
        if status:
            logger.warning(f"Audio status: {status}")
        with self._lock:
            audio_chunk = indata.copy().flatten()
            self._buffer.append(audio_chunk)
            if len(self._buffer) <= 3:
                max_amp = np.abs(audio_chunk).max() if len(audio_chunk) > 0 else 0.0
                logger.info(
                    f"Audio callback #{len(self._buffer)}: received {len(audio_chunk)} samples, max amplitude: {max_amp:.4f}"
                )

    # -- Recording lifecycle --

    def _resolve_device(self) -> tuple[int | None, int]:
        """Resolve input device ID and its native sample rate."""
        native_sr = self._target_sample_rate
        device_info = None

        try:
            if self._device_id is not None:
                device_info = sd.query_devices(self._device_id)
                if device_info["max_input_channels"] > 0:
                    native_sr = int(device_info["default_samplerate"])
                else:
                    device_info = None

            if device_info is None:
                device_info = sd.query_devices(kind="input")
                self._device_id = sd.default.device[0]
                native_sr = int(device_info["default_samplerate"])

            hostapis = sd.query_hostapis()
            device_hostapi = hostapis[device_info["hostapi"]]
            logger.info(
                f"Using device: {device_info['name']} (ID: {self._device_id}, "
                f"rate: {native_sr}Hz, API: {device_hostapi['name']})"
            )
        except Exception as e:
            logger.warning(f"Could not query audio devices: {e}, using fallback")
            native_sr = self._target_sample_rate

        return self._device_id, native_sr

    def start(self) -> None:
        """Start recording from the selected microphone."""
        with self._lock:
            self._buffer = []

        device_id, native_sr = self._resolve_device()
        self._native_samplerate = native_sr

        try:
            logger.info(
                f"Creating audio stream: samplerate={native_sr}Hz, channels={self._channels}, device={device_id}"
            )
            self._stream = sd.InputStream(
                samplerate=native_sr,
                channels=self._channels,
                dtype=np.float32,
                device=device_id,
                callback=self._audio_callback,
            )
            logger.info("Starting audio stream...")
            self._stream.start()
            self._recording_start_time = time.time()
            logger.info("Recording started successfully.")
        except Exception as e:
            logger.error(f"Failed to start recording: {e}", exc_info=True)
            self.cleanup()
            raise

    def stop(self) -> "RecordingResult":
        """Stop recording, return concatenated + resampled audio data."""
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        duration = time.time() - self._recording_start_time if self._recording_start_time else 0

        with self._lock:
            if not self._buffer:
                raise RuntimeError("No audio recorded - microphone may not be working or is muted")

            audio_data = np.concatenate(self._buffer)
            native_sr = self._native_samplerate or self._target_sample_rate

            logger.info(
                f"Audio data: {len(audio_data)} samples at {native_sr}Hz "
                f"({len(audio_data) / native_sr:.2f}s), max amp: {np.abs(audio_data).max():.4f}"
            )

            # Resample if device rate differs from target
            if native_sr != self._target_sample_rate:
                logger.info(f"Resampling from {native_sr}Hz to {self._target_sample_rate}Hz")
                target_samples = round(
                    len(audio_data) * float(self._target_sample_rate) / native_sr
                )
                audio_data = scipy.signal.resample(audio_data, target_samples).astype(np.float32)

            self._buffer = []

        self._recording_start_time = None
        self._native_samplerate = None

        logger.info(f"Recording stopped, duration: {duration:.2f}s")
        return RecordingResult(
            audio_data=audio_data,
            sample_rate=self._target_sample_rate,
            duration_seconds=duration,
        )

    def cleanup(self) -> None:
        """Force-cleanup stream and buffer state (error/cancel path)."""
        with self._lock:
            if self._stream:
                try:
                    self._stream.stop()
                    self._stream.close()
                except Exception as e:
                    logger.warning(f"Error closing stream: {e}")
                finally:
                    self._stream = None
            self._buffer = []
            self._recording_start_time = None
            self._native_samplerate = None

    @property
    def is_active(self) -> bool:
        return self._stream is not None and self._stream.active


class TranscriberService:
    """
    Service for managing audio recording and transcription.

    Delegates audio I/O to AudioRecorder. Handles model lifecycle,
    transcription coordination, and state management.
    """

    SAMPLE_RATE = 16000
    CHANNELS = 1
    MIN_LIVE_AUDIO_SECONDS = 0.5
    MAX_RECORDING_SECONDS = 600

    def __init__(
        self,
        on_state_change: Callable[[TranscriberState], None] | None = None,
    ):
        self._state = TranscriberState.IDLE
        self._on_state_change = on_state_change
        self._model: ModelWrapper | None = None
        self._state_lock = threading.Lock()
        self._model_lock = threading.Lock()  # Serialize model access across live + final threads
        # Delegate audio I/O to AudioRecorder
        self._recorder = AudioRecorder(
            target_sample_rate=self.SAMPLE_RATE,
            channels=self.CHANNELS,
            is_model_loaded_check=lambda: self.is_model_loaded,
        )

        # Live transcription state
        self._live_enabled: bool = False
        self._live_chunk_seconds: float = 3.0
        self._live_callback: Callable[[str], None] | None = None
        self._live_thread: threading.Thread | None = None
        self._live_generation: int = 0
        self._live_cancel: threading.Event | None = None

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

    def set_live_callback(self, callback: Callable[[str], None] | None) -> None:
        """Set callback for live partial transcription results."""
        self._live_callback = callback

    def set_live_enabled(self, enabled: bool, chunk_seconds: float = 3.0) -> None:
        """Enable/disable live transcription mode with chunk interval."""
        self._live_enabled = enabled
        self._live_chunk_seconds = chunk_seconds

    def _cancel_live_thread(self) -> None:
        """Retire the current live generation so its thread stops at the next check."""
        self._live_generation += 1
        if self._live_cancel is not None:
            self._live_cancel.set()

    def _run_live_transcription(self, generation: int, cancel: threading.Event) -> None:
        """Background thread: transcribe full accumulated audio every N seconds."""
        last_text = ""
        next_pass = time.monotonic() + self._live_chunk_seconds
        while self._state == TranscriberState.RECORDING and generation == self._live_generation:
            delay = next_pass - time.monotonic()
            if delay > 0 and cancel.wait(delay):
                return
            next_pass = max(next_pass + self._live_chunk_seconds, time.monotonic())
            if cancel.is_set() or generation != self._live_generation:
                return
            if self._state != TranscriberState.RECORDING:
                return
            try:
                with self._recorder._lock:
                    if not self._recorder._buffer:
                        continue
                    full_audio = np.concatenate(self._recorder._buffer)
                # Check minimum duration using native sample rate
                native_sr = self._recorder._native_samplerate or self.SAMPLE_RATE
                if len(full_audio) < native_sr * self.MIN_LIVE_AUDIO_SECONDS:
                    continue

                # Resample from native rate to target 16kHz
                native_sr = self._recorder._native_samplerate or self.SAMPLE_RATE
                if native_sr != self.SAMPLE_RATE:
                    n_target = round(len(full_audio) * float(self.SAMPLE_RATE) / native_sr)
                    full_audio = scipy.signal.resample(full_audio, n_target).astype(np.float32)

                # Transcribe with tqdm suppressed
                import os as _os

                _old = _os.environ.get("TQDM_DISABLE")
                _os.environ["TQDM_DISABLE"] = "1"
                try:
                    with self._model_lock:
                        result = self._model.transcribe(full_audio, self.SAMPLE_RATE)
                finally:
                    if _old is not None:
                        _os.environ["TQDM_DISABLE"] = _old
                    else:
                        _os.environ.pop("TQDM_DISABLE", None)

                # A quick stop/start can be back to RECORDING before this pass
                # returns; the generation is what tells the sessions apart.
                if (
                    cancel.is_set()
                    or generation != self._live_generation
                    or self._state != TranscriberState.RECORDING
                ):
                    return

                text = result.text.strip()
                logger.info(f"[live] result: '{text}' ({len(full_audio)} samples)")
                if text and text != last_text:
                    last_text = text
                    # Debug file write (best-effort, don't crash)
                    try:
                        import os as _os2

                        _os2.makedirs(_os2.path.expanduser("~/.speakeasy"), exist_ok=True)
                        with open(_os2.path.expanduser("~/.speakeasy/live_debug.log"), "a") as _f:
                            _f.write(
                                f"{__import__('time').time()}: '{text}' ({len(full_audio)} samples)\n"
                            )
                    except Exception:
                        pass
                    if self._live_callback:
                        self._live_callback(text)
            except Exception as e:
                logger.warning(f"Live transcription chunk failed: {e}")

    def load_model(
        self,
        model_type: str,
        model_name: str,
        device: str = "cuda",
        compute_type: str | None = None,
        progress_callback: ProgressCallback | None = None,
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

            # Lazy import to speed up initial startup
            from .models import ModelWrapper

            # Create and load new model
            self._model = ModelWrapper(
                model_type=model_type,
                model_name=model_name,
                device=device,
                compute_type=compute_type,
            )
            self._model.load(progress_callback=progress_callback)

            # Absorb first-inference kernel setup so the first live pass is warm
            try:
                self._model.transcribe(
                    np.zeros(self.SAMPLE_RATE, dtype=np.float32), self.SAMPLE_RATE
                )
            except Exception as e:
                logger.warning(f"Model warmup inference failed: {e}")

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

    def set_device(self, device_name: str | None = None) -> None:
        """Set the audio input device."""
        self._recorder.set_device(device_name)

    def start_recording(self) -> None:
        """Start recording audio from the microphone."""
        with self._state_lock:
            if self._state == TranscriberState.RECORDING:
                logger.warning("Already recording")
                return
            if not self.is_model_loaded:
                raise RuntimeError("No model loaded")

        try:
            self._cancel_live_thread()
            self._recorder.start()
            with self._state_lock:
                self._set_state(TranscriberState.RECORDING)

            # Start live transcription thread if enabled
            if self._live_enabled and self._model is not None:
                logger.info("Starting live transcription background thread")
                self._live_cancel = threading.Event()
                self._live_thread = threading.Thread(
                    target=self._run_live_transcription,
                    args=(self._live_generation, self._live_cancel),
                    daemon=True,
                )
                self._live_thread.start()
            elif self._live_enabled:
                logger.warning("Live enabled but no model loaded — live thread skipped")

        except Exception as e:
            logger.error(f"Failed to start recording: {e}", exc_info=True)
            self._recorder.cleanup()
            with self._state_lock:
                if self.is_model_loaded:
                    self._set_state(TranscriberState.READY)
                else:
                    self._set_state(TranscriberState.IDLE)
            raise

    def stop_recording(self) -> RecordingResult:
        """Stop recording and return audio data."""
        with self._state_lock:
            if self._state != TranscriberState.RECORDING:
                raise RuntimeError("Not recording")

        self._cancel_live_thread()

        try:
            with self._state_lock:
                self._set_state(TranscriberState.TRANSCRIBING)
            return self._recorder.stop()
        except Exception:
            self._recorder.cleanup()
            with self._state_lock:
                if self.is_model_loaded:
                    self._set_state(TranscriberState.READY)
                else:
                    self._set_state(TranscriberState.IDLE)
            raise

    # Threshold for chunked transcription: 5 minutes at 16kHz
    CHUNK_THRESHOLD_SAMPLES = 5 * 60 * SAMPLE_RATE  # 4,800,000 samples
    # Chunk size for long recordings: 2 minutes (balance between progress updates and efficiency)
    CHUNK_SIZE_SAMPLES = 2 * 60 * SAMPLE_RATE  # 1,920,000 samples

    def transcribe(
        self,
        audio_data: "NDArray[np.float32]",
        sample_rate: int = 16000,
        language: str | None = None,
        progress_callback: TranscriptionProgressCallback | None = None,
        instruction: str | None = None,
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
                # Standard single-pass transcription (serialized with live thread)
                with self._model_lock:
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

        except Exception:
            self._set_state(TranscriberState.ERROR)
            raise

    def _transcribe_chunked(
        self,
        audio_data: "NDArray[np.float32]",
        sample_rate: int,
        language: str | None,
        progress_callback: TranscriptionProgressCallback | None,
        instruction: str | None = None,
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

            # Transcribe chunk (serialized with live thread)
            with self._model_lock:
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
        language: str | None = None,
        progress_callback: TranscriptionProgressCallback | None = None,
        instruction: str | None = None,
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
        language: str | None = None,
        progress_callback: TranscriptionProgressCallback | None = None,
        instruction: str | None = None,
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
        # Atomic state check
        with self._state_lock:
            if self._state != TranscriberState.RECORDING:
                return
            # Mark as cancelling to prevent race conditions
            self._set_state(TranscriberState.TRANSCRIBING)

        try:
            self._recorder.cleanup()
        finally:
            # Always ensure state is reset
            with self._state_lock:
                self._set_state(
                    TranscriberState.READY if self.is_model_loaded else TranscriberState.IDLE
                )
            logger.info("Recording cancelled")

    def cleanup(self) -> None:
        """Clean up all resources including model and recording state."""
        # Hold state lock during entire cleanup
        with self._state_lock:
            try:
                self._recorder.cleanup()
            finally:
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
