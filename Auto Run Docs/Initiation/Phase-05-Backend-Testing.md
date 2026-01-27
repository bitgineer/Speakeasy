# Phase 05: Backend Testing Suite

This phase expands the backend test coverage to ensure core functionality works correctly. Comprehensive backend tests catch regressions early, document expected behavior, and enable confident refactoring. Tests cover the transcription service, history management, settings, and API endpoints.

## Tasks

- [ ] Create transcriber service unit tests:
  - Create `backend/tests/test_transcriber.py`
  - Test state transitions: idle -> loading -> ready -> recording -> ready
  - Test recording start/stop/cancel flows
  - Test audio buffer accumulation and cleanup
  - Test error handling when no model is loaded
  - Test device selection and validation
  - Use mock audio device to avoid requiring actual hardware

- [ ] Create model wrapper tests:
  - Create `backend/tests/test_models.py`
  - Test model type detection and validation
  - Test GPU info retrieval
  - Test model recommendation logic based on VRAM
  - Test compute type validation per model type
  - Mock actual model loading (don't download real models in tests)

- [ ] Create history service tests:
  - Create `backend/tests/test_history.py`
  - Test adding transcription records
  - Test pagination (limit/offset)
  - Test search functionality with various queries
  - Test deletion of records
  - Test statistics calculation
  - Use in-memory SQLite database for fast, isolated tests

- [ ] Create settings service tests:
  - Create `backend/tests/test_settings_service.py`
  - Test loading default settings
  - Test updating individual settings
  - Test settings persistence (write and reload)
  - Test validation of setting values
  - Test hotkey format validation

- [ ] Create API endpoint tests (comprehensive):
  - Create `backend/tests/test_api_endpoints.py`
  - Test all `/api/health` endpoint variations
  - Test `/api/settings` GET/PUT with valid and invalid data
  - Test `/api/models/*` endpoints
  - Test `/api/devices/*` endpoints
  - Test `/api/transcribe/start` and `/api/transcribe/stop` with mocked transcriber
  - Test `/api/transcribe/cancel` flow
  - Test `/api/history/* CRUD operations
  - Verify proper HTTP status codes (200, 400, 404, 500)

- [ ] Create WebSocket tests:
  - Create `backend/tests/test_websocket.py`
  - Test WebSocket connection and initial state message
  - Test broadcast functionality to multiple clients
  - Test ping/pong heartbeat
  - Test client disconnect handling
  - Test state change notifications

- [ ] Create input validation tests:
  - Create `backend/tests/test_validation.py`
  - Test Pydantic model validation for all request bodies
  - Test string length limits are enforced
  - Test numeric ranges are enforced
  - Test invalid types are rejected
  - Test required fields are enforced

- [ ] Create performance tests:
  - Create `backend/tests/test_performance.py`
  - Test transcription completes within reasonable time (mocked model)
  - Test history search performance with large datasets
  - Test concurrent request handling
  - Measure and assert memory usage doesn't grow unbounded

- [ ] Add test coverage reporting:
  - Ensure pytest-cov is configured
  - Set minimum coverage threshold (aim for 80%)
  - Generate HTML coverage reports
  - Add coverage comments to identify uncovered lines
  - Create coverage badge for README

- [ ] Run full test suite and fix failures:
  - Run `pytest -v --cov` to execute all tests
  - Fix any failing tests
  - Address flaky tests (those that sometimes fail)
  - Ensure tests run in under 60 seconds total
  - Verify coverage meets threshold
