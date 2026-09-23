"""Regression tests for the live transcription lifecycle.

Covers the three verified defects:
- server._setup_live_transcription() called from the daemon auto-load thread
  raised RuntimeError("no running event loop")
- a live callback could fire after stop_recording() returned
- a live thread from one recording session kept transcribing into the next

Also covers the live start latency: results were withheld until 3 s of audio
even when the configured chunk interval was shorter.
"""

import sys
import threading
import time
from pathlib import Path
from unittest.mock import Mock

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.core.models import TranscriptionResult
from speakeasy.core.transcriber import (
    RecordingResult,
    TranscriberService,
    TranscriberState,
)


class FakeRecorder:
    """Recorder double holding a fixed 4 s buffer (live needs >= 3 s)."""

    def __init__(self):
        self._lock = threading.Lock()
        self._buffer = [np.ones(16000 * 4, dtype=np.float32)]
        self._native_samplerate = 16000

    def start(self):
        pass

    def stop(self):
        return RecordingResult(np.zeros(16000, dtype=np.float32), 16000, 1.0)

    def cleanup(self):
        pass


def make_service(model, callback=None, chunk_seconds=0.05):
    service = TranscriberService()
    service._model = model
    service._recorder = FakeRecorder()
    service.set_live_callback(callback)
    service.set_live_enabled(True, chunk_seconds)
    return service


class FakeSettings:
    live_transcription = True
    live_chunk_seconds = 0.5
    live_auto_paste = False
    enable_text_cleanup = False
    custom_filler_words = []


class FakeSettingsService:
    def get(self):
        return FakeSettings()


def test_setup_live_transcription_from_non_async_thread_with_explicit_loop(monkeypatch):
    from speakeasy import server

    transcriber = Mock()
    monkeypatch.setattr(server, "transcriber", transcriber)
    monkeypatch.setattr(server, "settings_service", FakeSettingsService())

    loop = Mock()
    errors = []

    def run():
        try:
            server._setup_live_transcription(loop)
        except Exception as e:
            errors.append(e)

    thread = threading.Thread(target=run)
    thread.start()
    thread.join(5)

    assert not thread.is_alive()
    assert errors == []
    transcriber.set_live_enabled.assert_called_once_with(True, 0.5)
    callback = transcriber.set_live_callback.call_args[0][0]
    assert callback is not None
    callback("hello")
    loop.call_soon_threadsafe.assert_called_once()


class BlockingModel:
    is_loaded = True
    model_name = "fake"

    def __init__(self):
        self.entered = threading.Event()
        self.release = threading.Event()

    def transcribe(self, audio_data, sample_rate=16000, language=None, instruction=None):
        self.entered.set()
        assert self.release.wait(5), "test never released the model"
        return TranscriptionResult(text="late-result", duration_ms=1)


def test_no_live_callback_after_stop_recording_returns():
    model = BlockingModel()
    events = []
    service = make_service(model, callback=events.append)

    service.start_recording()
    live_thread = service._live_thread
    assert live_thread is not None
    assert model.entered.wait(5), "live thread never reached the model"

    service.stop_recording()
    model.release.set()
    live_thread.join(5)

    assert not live_thread.is_alive()
    assert events == []


class GatedModel:
    """First transcribe blocks; every call records its thread ident."""

    is_loaded = True
    model_name = "fake"

    def __init__(self):
        self._lock = threading.Lock()
        self.calls = []
        self.first_call_started = threading.Event()
        self.release_first_call = threading.Event()
        self.later_call_seen = threading.Event()

    def transcribe(self, audio_data, sample_rate=16000, language=None, instruction=None):
        with self._lock:
            index = len(self.calls)
            self.calls.append(threading.get_ident())
        if index == 0:
            self.first_call_started.set()
            assert self.release_first_call.wait(5), "test never released the first call"
        else:
            self.later_call_seen.set()
        return TranscriptionResult(text=f"result-{index}", duration_ms=1)


def test_stale_live_thread_does_not_transcribe_in_next_session():
    model = GatedModel()
    service = make_service(model, callback=lambda text: None, chunk_seconds=0.1)
    l1 = l2 = None

    try:
        service.start_recording()
        l1 = service._live_thread
        assert l1 is not None
        assert model.first_call_started.wait(5), "session 1 live thread never called the model"

        service.stop_recording()
        service.start_recording()
        l2 = service._live_thread
        assert l2 is not None and l2 is not l1
        mark = len(model.calls)

        model.release_first_call.set()
        assert model.later_call_seen.wait(5), "session 2 live thread never called the model"
        l1.join(1.0)

        calls_from_l1 = [ident for ident in model.calls[mark:] if ident == l1.ident]
        assert not l1.is_alive(), "session 1 live thread survived the stop/start"
        assert calls_from_l1 == [], "session 1 live thread transcribed during session 2"
    finally:
        if service.state == TranscriberState.RECORDING:
            service.stop_recording()
        if l1 is not None:
            l1.join(2.0)
        if l2 is not None:
            l2.join(2.0)


class ShortBufferRecorder(FakeRecorder):
    """Recorder double holding a 1.2 s buffer."""

    def __init__(self, seconds: float = 1.2):
        super().__init__()
        self._buffer = [np.ones(int(16000 * seconds), dtype=np.float32)]


def test_live_transcription_starts_before_three_seconds_of_audio():
    model = Mock()
    model.transcribe.return_value = TranscriptionResult(
        text="early words prove that live captions start", duration_ms=1
    )
    events = []
    service = make_service(model, callback=events.append, chunk_seconds=0.1)
    service._recorder = ShortBufferRecorder()

    try:
        service.start_recording()
        deadline = time.time() + 5
        while not events and time.time() < deadline:
            time.sleep(0.05)
        assert events == ["early"], "live result withheld despite a buffer past the chunk interval"
    finally:
        if service.state == TranscriberState.RECORDING:
            service.stop_recording()
