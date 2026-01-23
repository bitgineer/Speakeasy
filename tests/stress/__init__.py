"""
Stress and stability tests for faster-whisper-hotkey.

This package contains tests that verify the application's stability
under extended use, high load, and edge case scenarios.

These tests are NOT run by default in the standard test suite.
Run them explicitly with:
    pytest tests/stress/ -v -m stress
    python -m scripts.run_stability_tests
"""
