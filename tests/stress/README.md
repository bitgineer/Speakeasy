# Stability and Reliability Tests

This directory contains stress tests and long-running stability tests for the faster-whisper-hotkey application. These tests are designed to verify the application's reliability under extended use, high load, and edge case scenarios.

## Test Categories

### 1. Rapid Transcription Tests (`TestRapidTranscription`)
- **test_rapid_transcription_100_cycles**: Runs 100 consecutive transcription cycles to detect memory leaks and stability issues
- **test_rapid_transcription_with_restart**: Tests model loading/unloading cycles
- **test_concurrent_transcription_threads**: Tests multiple threads accessing the transcriber concurrently

### 2. Memory Leak Tests (`TestMemoryLeaks`)
- **test_transcription_memory_leak**: Detects memory leaks over multiple transcription cycles
- **test_model_load_unload_memory**: Verifies memory is properly freed when loading/unloading models
- **test_audio_buffer_memory**: Tests that large audio buffers are properly cleaned up

### 3. Long Recording Tests (`TestLongRecordings`)
- **test_long_audio_transcription**: Tests transcription of 5+ minute audio recordings
- **test_chunked_transcription_stability**: Tests multiple chunks sequentially (simulating dictation sessions)
- **test_audio_buffer_overflow_handling**: Tests handling of audio buffer overflow

### 4. Stability Tests (`TestStability`)
- **test_stability_extended_operation**: Tests transcriber stability over extended periods
- **test_state_transitions**: Tests repeated state transitions (idle → recording → transcribing → idle)

### 5. System State Tests (`TestSystemState`)
- **test_suspend_resume_simulation**: Simulates suspend/resume scenarios
- **test_settings_reload_stability**: Tests that settings changes don't cause instability

### 6. Multi-User Tests (`TestMultiUser`)
- **test_settings_profile_switching**: Tests switching between different user settings profiles
- **test_concurrent_settings_access**: Tests concurrent access to settings from multiple threads

### 7. Error Recovery Tests (`TestErrorRecovery`)
- **test_recovery_from_transcription_error**: Tests recovery from transcription errors
- **test_recovery_from_invalid_input**: Tests handling of invalid audio input

### 8. Performance Regression Tests (`TestPerformanceRegression`)
- **test_transcription_time_consistency**: Verifies transcription times remain consistent

## Running the Tests

### Quick Smoke Test (~2 minutes)
```bash
python scripts/run_stability_tests.py --quick
# or
pytest tests/stress/test_stability.py -v -m stress -k "test_rapid_transcription_10_cycles or test_concurrent"
```

### Rapid Transcription Test (100 cycles)
```bash
python scripts/run_stability_tests.py --rapid 100
# or
STRESS_RAPID_COUNT=100 pytest tests/stress/test_stability.py::TestRapidTranscription::test_rapid_transcription_100_cycles -v -s
```

### Memory Leak Test
```bash
python scripts/run_stability_tests.py --memory-only
# or
python scripts/run_stability_tests.py --memory 100
# or
STRESS_MEMORY_ITERATIONS=100 pytest tests/stress/test_stability.py::TestMemoryLeaks -v -s
```

### Long Recording Test (5 minutes)
```bash
python scripts/run_stability_tests.py --long-recording 300
# or
STRESS_RECORDING_SECONDS=300 pytest tests/stress/test_stability.py::TestLongRecordings::test_long_audio_transcription -v -s
```

### Extended Stability Test (1 hour)
```bash
python scripts/run_stability_tests.py --duration 3600
# or
STRESS_STABILITY_SECONDS=3600 pytest tests/stress/test_stability.py::TestStability::test_stability_extended_operation -v -s
```

### Full Test Suite
```bash
python scripts/run_stability_tests.py --full
# or
pytest tests/stress/test_stability.py -v -m stress
```

## Environment Variables

You can customize test behavior using these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `STRESS_RAPID_COUNT` | 100 | Number of rapid transcription cycles |
| `STRESS_RECORDING_SECONDS` | 300 | Long recording duration in seconds |
| `STRESS_STABILITY_SECONDS` | 60 | Stability test duration in seconds |
| `STRESS_MEMORY_ITERATIONS` | 50 | Memory leak test iterations |

## Test Reports

The test runner generates a JSON report file with detailed results:

```bash
python scripts/run_stability_tests.py --full --output my_report.json
```

Example report structure:
```json
{
  "timestamp": "2024-01-15T10:30:00",
  "results": {
    "rapid_transcription": {
      "success": true,
      "elapsed_seconds": 45.2,
      "stats": {
        "passed": 5,
        "failed": 0
      }
    }
  },
  "summary": {
    "total_tests_run": 25,
    "total_passed": 25,
    "total_failed": 0,
    "all_passed": true
  }
}
```

## Notes

- These tests use mock audio data and models by default to avoid dependency on actual audio hardware
- Tests marked with `@pytest.mark.slow` and `@pytest.mark.stress` are not run in the standard test suite
- For CI/CD environments, use reduced cycle counts and durations
- For comprehensive local testing, use longer durations and higher cycle counts

## Interpreting Results

### Memory Leak Detection
- Tests track memory usage (RSS) across multiple iterations
- A "memory leak" is flagged if memory growth exceeds a threshold (default 20-50%)
- Some memory growth is expected due to Python's memory allocator

### Performance Regression
- Transcription time consistency is measured using coefficient of variation (CV)
- CV < 50% is considered acceptable
- Significantly higher CV may indicate performance issues

### Error Recovery
- Tests verify the application can recover from errors without crashing
- Error rate should be < 5% for rapid transcription tests
