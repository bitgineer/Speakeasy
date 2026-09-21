"""Regression tests: displayed live text must not rewrite beyond its newest tail."""

import sys
import threading
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.core.models import TranscriptionResult
from speakeasy.core.transcriber import (
    RecordingResult,
    TranscriberService,
    TranscriberState,
)

HOLD_WORDS = 6


def common_prefix_words(left: str, right: str) -> int:
    count = 0
    for a, b in zip(left.split(), right.split()):
        if a != b:
            break
        count += 1
    return count


class ScriptedModel:
    """Test double: returns one scripted text per call and ignores the audio."""

    is_loaded = True
    model_name = "scripted"

    def __init__(self, texts: list[str]):
        self._texts = texts
        self._index = 0
        self._lock = threading.Lock()
        self.final: str | None = None

    def unload(self) -> None:
        pass

    def transcribe(
        self, audio_data, sample_rate: int = 16000, language=None, instruction=None
    ) -> TranscriptionResult:
        if self.final is not None:
            return TranscriptionResult(text=self.final, duration_ms=1)
        with self._lock:
            index = min(self._index, len(self._texts) - 1)
            self._index += 1
        return TranscriptionResult(text=self._texts[index], duration_ms=1)


class MutableRecorder:
    """Append-only chunk list the test can extend; mirrors AudioRecorder's read surface."""

    def __init__(self, chunks: list[np.ndarray]):
        self._lock = threading.Lock()
        self._buffer = list(chunks)
        self._native_samplerate = 16000
        self._stream = None

    def start(self) -> None:
        pass

    def cleanup(self) -> None:
        pass

    def append(self, chunk: np.ndarray) -> None:
        with self._lock:
            self._buffer.append(chunk)

    def stop(self) -> RecordingResult:
        with self._lock:
            data = np.concatenate(self._buffer) if self._buffer else np.zeros(0, dtype=np.float32)
        return RecordingResult(data, 16000, len(data) / 16000)


def make_service(model, callback, chunks: list[np.ndarray]) -> TranscriberService:
    service = TranscriberService()
    service._model = model
    service._recorder = MutableRecorder(chunks)
    service.set_live_callback(callback)
    service.set_live_enabled(True, 0.1)
    return service


def wait_for_callbacks(callbacks: list[str], count: int, timeout: float = 3.0) -> None:
    deadline = time.time() + timeout
    while len(callbacks) < count and time.time() < deadline:
        time.sleep(0.02)


def test_live_callbacks_never_rewrite_displayed_words():
    words = [f"word{n:02d}" for n in range(1, 21)]
    revised = words[:4] + ["revised05"] + words[5:]
    model = ScriptedModel([" ".join(words), " ".join(words + ["extra"]), " ".join(revised)])
    service = make_service(model, lambda text: None, [np.ones(16000 * 4, dtype=np.float32)])

    callbacks: list[str] = []
    service.set_live_callback(callbacks.append)
    service.start_recording()
    recorder = service._recorder
    assert isinstance(recorder, MutableRecorder)
    try:
        wait_for_callbacks(callbacks, 1)
        assert callbacks, "live transcription never started"

        recorder.append(np.ones(8000, dtype=np.float32))
        wait_for_callbacks(callbacks, 2)
        assert len(callbacks) == 2, f"expected an appended callback, got {callbacks}"

        recorder.append(np.ones(8000, dtype=np.float32))
        time.sleep(0.4)
        settled = len(callbacks)
        time.sleep(0.3)
        assert len(callbacks) == settled, (
            "a decode that revised already-read words reached the callback:\n"
            + "\n".join(callbacks[settled:])
        )
    finally:
        if service.state == TranscriberState.RECORDING:
            service.stop_recording()
        if service._live_thread is not None:
            service._live_thread.join(2.0)
        service.unload_model()

    assert len(callbacks) >= 2, f"expected live callbacks, got {callbacks}"
    assert all("revised05" not in text for text in callbacks), (
        f"a decode that revised already-read words reached the callback: {callbacks}"
    )
    for previous, current in zip(callbacks, callbacks[1:]):
        kept = common_prefix_words(previous, current)
        assert kept >= len(previous.split()) - HOLD_WORDS, (
            f"displayed text rewrote more than the last {HOLD_WORDS} words:\n"
            f"  before: {previous}\n  after:  {current}"
        )


def test_live_callbacks_stop_when_no_new_speech():
    model = ScriptedModel([f"pass {index} " + "word " * (index + 1) for index in range(50)])
    service = make_service(model, lambda text: None, [np.ones(16000 * 4, dtype=np.float32)])

    callbacks: list[str] = []
    service.set_live_callback(callbacks.append)
    service.start_recording()
    deadline = time.time() + 5.0
    while not callbacks and time.time() < deadline:
        time.sleep(0.05)
    assert callbacks, "live transcription never started"

    recorder = service._recorder
    assert isinstance(recorder, MutableRecorder)
    recorder.append(np.zeros(16000 * 3, dtype=np.float32))

    try:
        time.sleep(0.4)
        settled = len(callbacks)
        time.sleep(0.6)
        assert len(callbacks) == settled, (
            "live transcription kept updating while no new speech arrived:\n"
            + "\n".join(callbacks[settled:])
        )
    finally:
        if service.state == TranscriberState.RECORDING:
            service.stop_recording()
        if service._live_thread is not None:
            service._live_thread.join(2.0)
        service.unload_model()


def test_stop_and_transcribe_returns_the_final_decode():
    model = ScriptedModel(["live text"])
    service = make_service(model, lambda text: None, [np.ones(16000 * 4, dtype=np.float32)])

    callbacks: list[str] = []
    service.set_live_callback(callbacks.append)
    service.start_recording()
    deadline = time.time() + 5.0
    while not callbacks and time.time() < deadline:
        time.sleep(0.05)

    model.final = "FINAL FULL DECODE"
    try:
        result = service.stop_and_transcribe()
    finally:
        if service._live_thread is not None:
            service._live_thread.join(2.0)
        service.unload_model()

    assert result.text == "FINAL FULL DECODE"
