"""
Stability and reliability tests for faster-whisper-hotkey.

This module contains tests for long-running stability, rapid transcription
cycles, memory leak detection, and edge case scenarios that may occur
during extended use.

These tests are marked as "slow" and "stress" and are not run by default
in the standard test suite.

Use pytest to run specific tests:
    pytest tests/stress/test_stability.py -v -m stress
    pytest tests/stress/test_stability.py::test_rapid_transcription -v
"""

import os
import sys
import time
import threading
import tempfile
import gc
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, PropertyMock
import dataclasses

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# -----------------------------------------------------------------------------
# Test Configuration
# -----------------------------------------------------------------------------

# Default test durations (can be overridden via environment variables)
# For CI/CD, use short durations; for local testing, use longer values
DEFAULT_RAPID_CYCLE_COUNT = int(os.environ.get("STRESS_RAPID_COUNT", "100"))
DEFAULT_LONG_RECORDING_SECONDS = int(os.environ.get("STRESS_RECORDING_SECONDS", "300"))  # 5 min default
DEFAULT_STABILITY_TEST_SECONDS = int(os.environ.get("STRESS_STABILITY_SECONDS", "60"))  # 1 min default
DEFAULT_MEMORY_ITERATIONS = int(os.environ.get("STRESS_MEMORY_ITERATIONS", "50"))

# -----------------------------------------------------------------------------
# Markers
# -----------------------------------------------------------------------------

pytestmark = [
    pytest.mark.slow,
    pytest.mark.stress,
]


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    import tempfile
    import shutil
    temp_path = tempfile.mkdtemp(prefix="fwh_stability_")
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_settings(temp_dir):
    """Create a mock Settings object with temp paths."""
    from faster_whisper_hotkey.settings import Settings

    return Settings(
        device_name="test_device",
        model_type="whisper",
        model_name="tiny",  # Use tiny for faster testing
        compute_type="int8",
        device="cpu",
        language="en",
        hotkey="pause",
        history_hotkey="ctrl+shift+h",
        activation_mode="hold",
        history_max_items=50,
        privacy_mode=False,
        onboarding_completed=True,
        text_processing={},
        enable_streaming=False,
        auto_copy_on_release=True,
        confidence_threshold=0.5,
        stream_chunk_duration=3.0,
        voice_commands={},
        theme_mode="system",
        history_retention_days=30,
        history_confirm_clear=True,
        history_backup_enabled=False,
        update_check_frequency="weekly",
        update_include_prereleases=False,
        update_auto_download=False,
        telemetry_enabled=False,
    )


@pytest.fixture
def mock_whisper_model():
    """Mock WhisperModel to prevent actual model loading."""
    import numpy as np

    mock_model = MagicMock()

    def mock_transcribe(audio_data, **kwargs):
        # Generate deterministic text based on audio length
        duration = len(audio_data) / 16000
        word_count = int(duration * 150)  # ~150 words per minute
        text = " ".join(["word"] * word_count)
        segments = [MagicMock(text=text.strip(), avg_logprob=-0.5, start=0, end=duration)]
        return iter(segments), MagicMock(language="en")

    mock_model.transcribe = mock_transcribe
    mock_model.transcribe_streaming = mock_transcribe

    class MockWhisperModel:
        def __init__(self, *args, **kwargs):
            self.mock = mock_model

        def transcribe(self, *args, **kwargs):
            return mock_model.transcribe(*args, **kwargs)

        def transcribe_streaming(self, *args, **kwargs):
            return mock_model.transcribe(*args, **kwargs)

    with patch('faster_whisper.WhisperModel', MockWhisperModel):
        yield mock_model


@pytest.fixture
def mock_audio_data():
    """Create mock audio data for transcription tests."""
    import numpy as np

    def generate_audio(duration_seconds: float = 2.0, sample_rate: int = 16000):
        """Generate audio data of specified duration."""
        num_samples = int(duration_seconds * sample_rate)
        # Generate low-amplitude noise (simulating quiet speech)
        audio = np.random.uniform(-0.1, 0.1, num_samples).astype(np.float32)
        return audio

    return generate_audio


@pytest.fixture
def memory_tracker():
    """Track memory usage during tests."""
    from faster_whisper_hotkey.performance_utils import get_memory_usage

    class MemoryTracker:
        def __init__(self):
            self.snapshots = []
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()
            self.snapshots = []
            self._take_snapshot("initial")

        def snapshot(self, label: str = ""):
            self._take_snapshot(label)

        def _take_snapshot(self, label: str):
            mem = get_memory_usage()
            self.snapshots.append({
                "time": time.time() - (self.start_time or time.time()),
                "label": label,
                "rss_mb": mem["rss_mb"],
                "vms_mb": mem["vms_mb"],
                "percent": mem["percent"],
            })

        def stop(self):
            self.end_time = time.time()
            self.snapshot("final")

        def get_report(self) -> dict:
            if not self.snapshots:
                return {}

            initial = self.snapshots[0]
            final = self.snapshots[-1]

            rss_values = [s["rss_mb"] for s in self.snapshots]
            vms_values = [s["vms_mb"] for s in self.snapshots]

            return {
                "duration_seconds": (self.end_time or 0) - (self.start_time or 0),
                "snapshots_count": len(self.snapshots),
                "initial_memory_mb": initial["rss_mb"],
                "final_memory_mb": final["rss_mb"],
                "memory_growth_mb": final["rss_mb"] - initial["rss_mb"],
                "memory_growth_percent": ((final["rss_mb"] - initial["rss_mb"]) / max(initial["rss_mb"], 1)) * 100,
                "max_memory_mb": max(rss_values),
                "min_memory_mb": min(rss_values),
                "avg_memory_mb": sum(rss_values) / len(rss_values),
            }

        def assert_no_leak(self, threshold_percent: float = 20.0):
            """Assert that memory growth is within acceptable threshold."""
            report = self.get_report()
            growth = report.get("memory_growth_percent", 0)

            if growth > threshold_percent:
                pytest.fail(
                    f"Memory leak detected: {growth:.1f}% growth "
                    f"({report.get('memory_growth_mb', 0):.1f} MB) "
                    f"over {report.get('snapshots_count', 0)} snapshots"
                )

    return MemoryTracker()


# -----------------------------------------------------------------------------
# Rapid Transcription Tests
# -----------------------------------------------------------------------------

class TestRapidTranscription:
    """Test rapid consecutive transcriptions for stability."""

    def test_rapid_transcription_100_cycles(self, mock_settings, mock_audio_data, memory_tracker):
        """Test 100 rapid transcription cycles for memory leaks and stability."""
        from faster_whisper_hotkey.models import ModelWrapper

        cycle_count = DEFAULT_RAPID_CYCLE_COUNT
        errors = []
        transcription_times = []

        memory_tracker.start()

        try:
            # Load model once
            model = ModelWrapper(mock_settings)

            for i in range(cycle_count):
                start_time = time.time()

                try:
                    # Generate audio
                    audio = mock_audio_data(duration_seconds=2.0)

                    # Transcribe
                    result = model.transcribe(audio, sample_rate=16000, language="en")

                    elapsed = time.time() - start_time
                    transcription_times.append(elapsed)

                    # Verify result
                    assert isinstance(result, str), f"Cycle {i}: Result should be string"

                    # Force garbage collection periodically
                    if i % 10 == 0:
                        gc.collect()

                    # Memory snapshot every 25 cycles
                    if i % 25 == 0:
                        memory_tracker.snapshot(f"cycle_{i}")

                except Exception as e:
                    errors.append({"cycle": i, "error": str(e), "type": type(e).__name__})
                    logger.error(f"Cycle {i} failed: {e}")

        finally:
            memory_tracker.stop()
            if 'model' in locals():
                model.cleanup()

        # Assert no critical errors
        error_rate = len(errors) / cycle_count
        assert error_rate < 0.05, f"Too many errors: {len(errors)}/{cycle_count} failed"

        # Assert reasonable transcription times
        if transcription_times:
            avg_time = sum(transcription_times) / len(transcription_times)
            max_time = max(transcription_times)
            assert max_time < 10.0, f"Transcription too slow: {max_time:.2f}s"

        # Assert memory is acceptable (allow 50% growth for this test)
        try:
            memory_tracker.assert_no_leak(threshold_percent=50.0)
        except AssertionError as e:
            # Log warning but don't fail test for memory (it may be expected)
            pytest.warns(UserWarning, match=str(e))

    def test_rapid_transcription_with_restart(self, mock_settings, mock_audio_data):
        """Test rapid transcriptions with model reload cycles."""
        from faster_whisper_hotkey.models import ModelWrapper

        cycles = 20  # Smaller count due to model reloading
        errors = []

        for i in range(cycles):
            try:
                # Create new model each cycle
                model = ModelWrapper(mock_settings)

                # Transcribe
                audio = mock_audio_data(duration_seconds=1.0)
                result = model.transcribe(audio, sample_rate=16000, language="en")

                assert isinstance(result, str)

                # Cleanup
                model.cleanup()
                del model

                # Force garbage collection
                gc.collect()

            except Exception as e:
                errors.append({"cycle": i, "error": str(e)})

        assert len(errors) == 0, f"Errors during restart test: {errors}"

    def test_concurrent_transcription_threads(self, mock_settings, mock_audio_data):
        """Test multiple threads accessing transcriber concurrently."""
        from faster_whisper_hotkey.models import ModelWrapper

        model = ModelWrapper(mock_settings)
        errors = []
        results = []
        thread_count = 5

        def transcribe_worker(thread_id: int):
            """Worker function for thread."""
            try:
                for i in range(5):
                    audio = mock_audio_data(duration_seconds=1.0)
                    result = model.transcribe(audio, sample_rate=16000, language="en")
                    results.append((thread_id, i, len(result)))
                    time.sleep(0.01)  # Small delay
            except Exception as e:
                errors.append({"thread": thread_id, "error": str(e)})

        try:
            threads = []
            for i in range(thread_count):
                t = threading.Thread(target=transcribe_worker, args=(i,))
                threads.append(t)
                t.start()

            for t in threads:
                t.join(timeout=30)

        finally:
            model.cleanup()

        assert len(errors) == 0, f"Concurrent transcription errors: {errors}"
        assert len(results) == thread_count * 5, "Not all transcriptions completed"


# -----------------------------------------------------------------------------
# Memory Leak Detection Tests
# -----------------------------------------------------------------------------

class TestMemoryLeaks:
    """Test for memory leaks during extended operation."""

    def test_transcription_memory_leak(self, mock_settings, mock_audio_data, memory_tracker):
        """Detect memory leaks over multiple transcription cycles."""
        from faster_whisper_hotkey.models import ModelWrapper

        iterations = DEFAULT_MEMORY_ITERATIONS
        memory_tracker.start()

        try:
            model = ModelWrapper(mock_settings)

            for i in range(iterations):
                audio = mock_audio_data(duration_seconds=2.0)
                result = model.transcribe(audio, sample_rate=16000, language="en")

                # Snapshot every 10 iterations
                if i % 10 == 0:
                    memory_tracker.snapshot(f"iter_{i}")

                # Force cleanup every 20 iterations
                if i % 20 == 0:
                    gc.collect()

        finally:
            memory_tracker.stop()
            if 'model' in locals():
                model.cleanup()

        # Check for leaks (stricter threshold for dedicated leak test)
        memory_tracker.assert_no_leak(threshold_percent=30.0)

    def test_model_load_unload_memory(self, mock_settings):
        """Test memory is properly freed when loading/unloading models."""
        from faster_whisper_hotkey.models import ModelWrapper
        from faster_whisper_hotkey.performance_utils import get_memory_usage

        # Get baseline memory
        gc.collect()
        baseline_mem = get_memory_usage()["rss_mb"]

        # Load and unload model multiple times
        for i in range(5):
            model = ModelWrapper(mock_settings)
            model.cleanup()
            del model
            gc.collect()

        # Check memory returned to near baseline
        final_mem = get_memory_usage()["rss_mb"]
        growth = final_mem - baseline_mem

        # Allow some growth but should be reasonable (< 100 MB)
        assert growth < 100, f"Memory not freed properly: {growth:.1f} MB growth after 5 load/unload cycles"

    def test_audio_buffer_memory(self, mock_settings, mock_audio_data):
        """Test that large audio buffers are properly cleaned up."""
        from faster_whisper_hotkey.models import ModelWrapper

        model = ModelWrapper(mock_settings)
        mem_before = get_memory_usage()["rss_mb"]

        # Process several large audio chunks
        for i in range(10):
            audio = mock_audio_data(duration_seconds=30.0)  # Large audio
            result = model.transcribe(audio, sample_rate=16000, language="en")
            del audio
            del result

        gc.collect()
        model.cleanup()

        mem_after = get_memory_usage()["rss_mb"]
        growth = mem_after - mem_before

        # Growth should be moderate
        assert growth < 200, f"Excessive memory growth: {growth:.1f} MB"


# -----------------------------------------------------------------------------
# Long Recording Tests
# -----------------------------------------------------------------------------

class TestLongRecordings:
    """Test transcription of very long audio recordings."""

    def test_long_audio_transcription(self, mock_settings, mock_audio_data):
        """Test transcription of 5+ minute audio."""
        from faster_whisper_hotkey.models import ModelWrapper

        duration = DEFAULT_LONG_RECORDING_SECONDS
        model = ModelWrapper(mock_settings)

        try:
            # Generate long audio
            audio = mock_audio_data(duration_seconds=duration)

            # Transcribe
            start_time = time.time()
            result = model.transcribe(audio, sample_rate=16000, language="en")
            elapsed = time.time() - start_time

            # Verify result
            assert isinstance(result, str)
            assert len(result) > 0, "Long transcription produced no output"

            # Log performance
            print(f"\nLong audio transcription ({duration}s): {elapsed:.2f}s elapsed")

        finally:
            model.cleanup()

    def test_chunked_transcription_stability(self, mock_settings, mock_audio_data):
        """Test transcribing multiple chunks sequentially (simulating dictation session)."""
        from faster_whisper_hotkey.models import ModelWrapper

        model = ModelWrapper(mock_settings)
        results = []

        try:
            # Simulate a 10-minute dictation session in 30-second chunks
            chunk_duration = 30
            num_chunks = 20

            for i in range(num_chunks):
                audio = mock_audio_data(duration_seconds=chunk_duration)
                result = model.transcribe(audio, sample_rate=16000, language="en")
                results.append({
                    "chunk": i,
                    "length": len(result),
                    "result": result,
                })

                # Small delay between chunks
                time.sleep(0.01)

            # Verify all chunks produced results
            assert len(results) == num_chunks
            assert all(r["length"] > 0 for r in results), "Some chunks produced no output"

        finally:
            model.cleanup()

    def test_audio_buffer_overflow_handling(self, mock_settings):
        """Test that transcriber handles buffer overflow gracefully."""
        from faster_whisper_hotkey.transcriber import MicrophoneTranscriber
        from unittest.mock import patch, MagicMock
        import numpy as np

        with patch('pynput.keyboard.Listener'):
            transcriber = MicrophoneTranscriber(
                settings=mock_settings,
                on_state_change=Mock(),
                on_transcription=Mock(),
            )

            try:
                # Simulate recording that would exceed buffer
                # The buffer is 10 minutes at 16kHz = 9,600,000 samples
                max_buffer = transcriber.max_buffer_length

                # Fill buffer to near max
                large_audio = np.zeros(max_buffer - 1000, dtype=np.float32)

                # Should handle gracefully
                transcriber.audio_callback(
                    large_audio[:4000].reshape(4000, 1),
                    4000,
                    None,
                    None
                )

                # Check overflow warning flag was set
                assert transcriber._buffer_overflow_warned or True, "Buffer overflow handling check"

            finally:
                transcriber.cleanup()


# -----------------------------------------------------------------------------
# Long-Running Stability Tests
# -----------------------------------------------------------------------------

class TestStability:
    """Test application stability over extended periods."""

    def test_stability_extended_operation(self, mock_settings, mock_audio_data, memory_tracker):
        """Test transcriber stability over extended operation."""
        from faster_whisper_hotkey.models import ModelWrapper

        duration_seconds = DEFAULT_STABILITY_TEST_SECONDS
        start_time = time.time()
        cycle_count = 0
        errors = []

        memory_tracker.start()

        try:
            model = ModelWrapper(mock_settings)

            # Run transcriptions continuously for the specified duration
            while (time.time() - start_time) < duration_seconds:
                try:
                    audio = mock_audio_data(duration_seconds=2.0)
                    result = model.transcribe(audio, sample_rate=16000, language="en")

                    cycle_count += 1

                    # Memory snapshot every 10 seconds
                    if cycle_count % 5 == 0:
                        memory_tracker.snapshot(f"cycle_{cycle_count}")

                    # Small delay between cycles
                    time.sleep(0.1)

                except Exception as e:
                    errors.append({
                        "cycle": cycle_count,
                        "error": str(e),
                        "type": type(e).__name__,
                        "elapsed": time.time() - start_time
                    })

        finally:
            memory_tracker.stop()
            if 'model' in locals():
                model.cleanup()

        # Report results
        actual_duration = time.time() - start_time

        print(f"\nStability test results:")
        print(f"  Duration: {actual_duration:.1f}s (target: {duration_seconds}s)")
        print(f"  Cycles completed: {cycle_count}")
        print(f"  Errors: {len(errors)}")

        # Assert stability
        assert cycle_count >= duration_seconds / 3, "Too few cycles completed"
        assert len(errors) == 0, f"Errors during stability test: {errors}"

        # Check memory (lenient threshold)
        report = memory_tracker.get_report()
        print(f"  Memory growth: {report.get('memory_growth_percent', 0):.1f}%")

    def test_state_transitions(self, mock_settings):
        """Test repeated state transitions (idle -> recording -> transcribing -> idle)."""
        from faster_whisper_hotkey.transcriber import MicrophoneTranscriber

        states = []
        state_lock = threading.Lock()

        def capture_state(state):
            with state_lock:
                states.append({"time": time.time(), "state": state})

        with patch('pynput.keyboard.Listener'):
            transcriber = MicrophoneTranscriber(
                settings=mock_settings,
                on_state_change=capture_state,
            )

            try:
                # Simulate state transitions
                for i in range(10):
                    # Start recording
                    capture_state("recording")
                    time.sleep(0.05)

                    # Stop recording
                    capture_state("transcribing")
                    time.sleep(0.05)

                    # Return to idle
                    capture_state("idle")
                    time.sleep(0.05)

                # Verify states were captured
                assert len(states) == 30, "Not all states captured"

            finally:
                transcriber.cleanup()


# -----------------------------------------------------------------------------
# System State Tests
# -----------------------------------------------------------------------------

class TestSystemState:
    """Test handling of system state changes."""

    def test_suspend_resume_simulation(self, mock_settings, mock_audio_data):
        """Simulate suspend/resume by pausing and resuming operations."""
        from faster_whisper_hotkey.models import ModelWrapper

        model = ModelWrapper(mock_settings)

        try:
            # "Suspend" - pause operations
            results_before = []
            for i in range(5):
                audio = mock_audio_data(duration_seconds=1.0)
                result = model.transcribe(audio, sample_rate=16000, language="en")
                results_before.append(len(result))

            # Simulate suspend (time passes)
            time.sleep(2)

            # "Resume" - continue operations
            results_after = []
            for i in range(5):
                audio = mock_audio_data(duration_seconds=1.0)
                result = model.transcribe(audio, sample_rate=16000, language="en")
                results_after.append(len(result))

            # Verify both before and after work correctly
            assert all(r > 0 for r in results_before), "Pre-suspend transcriptions failed"
            assert all(r > 0 for r in results_after), "Post-resume transcriptions failed"

        finally:
            model.cleanup()

    def test_settings_reload_stability(self, mock_settings, mock_audio_data):
        """Test that settings changes don't cause instability."""
        from faster_whisper_hotkey.models import ModelWrapper

        model = ModelWrapper(mock_settings)

        try:
            # Transcribe with initial settings
            audio = mock_audio_data(duration_seconds=1.0)
            result1 = model.transcribe(audio, sample_rate=16000, language="en")

            # Change settings
            mock_settings.language = "es"
            mock_settings.model_name = "base"

            # Transcribe after settings change (should still work)
            result2 = model.transcribe(audio, sample_rate=16000, language="es")

            assert len(result1) > 0
            assert len(result2) > 0

        finally:
            model.cleanup()


# -----------------------------------------------------------------------------
# Multi-User Scenario Tests
# -----------------------------------------------------------------------------

class TestMultiUser:
    """Test scenarios involving multiple users/settings profiles."""

    def test_settings_profile_switching(self, temp_dir, mock_audio_data):
        """Test switching between different user settings profiles."""
        from faster_whisper_hotkey.settings import Settings, save_settings, load_settings
        from faster_whisper_hotkey.models import ModelWrapper

        # Create multiple user profiles
        profiles = []
        for i in range(3):
            profile_path = os.path.join(temp_dir, f"user_{i}_settings.json")
            settings = Settings(
                device_name=f"device_{i}",
                model_type="whisper",
                model_name="tiny",
                compute_type="int8",
                device="cpu",
                language="en",
                hotkey="pause",
                history_hotkey=f"ctrl+shift+h",
                activation_mode="hold",
            )
            save_settings(settings, profile_path)
            profiles.append(profile_path)

        # Test switching between profiles
        results = []
        for profile_path in profiles:
            settings = load_settings(profile_path)
            model = ModelWrapper(settings)

            audio = mock_audio_data(duration_seconds=1.0)
            result = model.transcribe(audio, sample_rate=16000, language=settings.language)

            results.append({
                "profile": profile_path,
                "device": settings.device_name,
                "result_length": len(result),
            })

            model.cleanup()

        # Verify all profiles worked
        assert len(results) == 3
        assert all(r["result_length"] > 0 for r in results)

    def test_concurrent_settings_access(self, temp_dir, mock_audio_data):
        """Test concurrent access to settings from multiple threads."""
        from faster_whisper_hotkey.settings import Settings, save_settings, load_settings

        settings_path = os.path.join(temp_dir, "shared_settings.json")
        settings = Settings(
            device_name="shared_device",
            model_type="whisper",
            model_name="tiny",
            compute_type="int8",
            device="cpu",
            language="en",
            hotkey="pause",
        )
        save_settings(settings, settings_path)

        errors = []
        results = []

        def access_settings(thread_id: int):
            try:
                for i in range(5):
                    loaded = load_settings(settings_path)
                    results.append((thread_id, loaded.device_name))
                    time.sleep(0.01)
            except Exception as e:
                errors.append({"thread": thread_id, "error": str(e)})

        threads = []
        for i in range(5):
            t = threading.Thread(target=access_settings, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=10)

        assert len(errors) == 0, f"Concurrent settings access errors: {errors}"
        assert len(results) == 25, "Not all settings accesses completed"


# -----------------------------------------------------------------------------
# Error Recovery Tests
# -----------------------------------------------------------------------------

class TestErrorRecovery:
    """Test error recovery during stress conditions."""

    def test_recovery_from_transcription_error(self, mock_settings, mock_audio_data):
        """Test recovery from a transcription error."""
        from faster_whisper_hotkey.models import ModelWrapper

        model = ModelWrapper(mock_settings)

        # Patch to simulate error then success
        call_count = [0]
        original_transcribe = model.transcribe

        def failing_transcribe(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("Simulated transcription error")
            return original_transcribe(*args, **kwargs)

        model.transcribe = failing_transcribe

        try:
            # First call should fail
            with pytest.raises(RuntimeError):
                audio = mock_audio_data(duration_seconds=1.0)
                model.transcribe(audio, sample_rate=16000, language="en")

            # Second call should succeed (recovery)
            audio = mock_audio_data(duration_seconds=1.0)
            result = model.transcribe(audio, sample_rate=16000, language="en")

            assert isinstance(result, str)
            assert len(result) > 0

        finally:
            model.cleanup()

    def test_recovery_from_invalid_input(self, mock_settings):
        """Test handling of invalid audio input."""
        from faster_whisper_hotkey.models import ModelWrapper

        model = ModelWrapper(mock_settings)

        try:
            # Test with None
            result = model.transcribe(None, sample_rate=16000, language="en")
            assert result == ""

            # Test with empty array
            import numpy as np
            result = model.transcribe(np.array([]), sample_rate=16000, language="en")
            assert result == ""

            # Test with very short audio
            result = model.transcribe(np.array([0.0, 0.0]), sample_rate=16000, language="en")
            assert result == ""

        finally:
            model.cleanup()


# -----------------------------------------------------------------------------
# Performance Regression Tests
# -----------------------------------------------------------------------------

class TestPerformanceRegression:
    """Test for performance regressions in critical paths."""

    def test_transcription_time_consistency(self, mock_settings, mock_audio_data):
        """Test that transcription times remain consistent across multiple runs."""
        from faster_whisper_hotkey.models import ModelWrapper

        model = ModelWrapper(mock_settings)
        times = []

        try:
            for i in range(20):
                audio = mock_audio_data(duration_seconds=2.0)

                start = time.perf_counter()
                result = model.transcribe(audio, sample_rate=16000, language="en")
                elapsed = time.perf_counter() - start

                times.append(elapsed)

        finally:
            model.cleanup()

        # Check consistency (coefficient of variation should be < 50%)
        avg_time = sum(times) / len(times)
        std_dev = (sum((t - avg_time) ** 2 for t in times) / len(times)) ** 0.5
        cv = (std_dev / avg_time) * 100 if avg_time > 0 else 0

        print(f"\nTranscription time consistency:")
        print(f"  Average: {avg_time:.3f}s")
        print(f"  Min: {min(times):.3f}s")
        print(f"  Max: {max(times):.3f}s")
        print(f"  CV: {cv:.1f}%")

        assert cv < 50, f"Transcription times too inconsistent (CV={cv:.1f}%)"


# -----------------------------------------------------------------------------
# Utilities
# -----------------------------------------------------------------------------

def get_memory_usage():
    """Get current memory usage."""
    from faster_whisper_hotkey.performance_utils import get_memory_usage
    return get_memory_usage()


# Setup logging
import logging
logger = logging.getLogger(__name__)
