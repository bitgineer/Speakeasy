# Phase 04: Testing Framework Setup

This phase establishes the testing infrastructure for both frontend and backend. A solid testing foundation enables confident refactoring, prevents regressions, and documents expected behavior. By the end of this phase, the project will have working test runners for both sides of the stack with example tests passing.

## Tasks

- [ ] Set up backend testing with pytest:
  - Add `pytest`, `pytest-asyncio`, `pytest-cov` to `backend/pyproject.toml` or `requirements-dev.txt`
  - Create `backend/tests/__init__.py`
  - Create `backend/tests/conftest.py` with shared fixtures
  - Add `pytest.ini` configuration file with test discovery settings
  - Add `--cov` options to coverage configuration
  - Create test script entry point in `backend/pyproject.toml`

- [ ] Create backend test fixtures in conftest.py:
  - `client` fixture: FastAPI TestClient for API endpoint testing
  - `test_settings` fixture: In-memory settings for testing
  - `test_history` fixture: In-memory or temporary SQLite database
  - `mock_model` fixture: Mock ModelWrapper that doesn't load actual models
  - `mock_audio` fixture: Sample audio data numpy array for transcription tests
  - `clean_tmp_dir` fixture: Temporary directory cleanup for file operations

- [ ] Set up frontend testing with Vitest:
  - Add `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event` to `gui/package.json`
  - Create `vitest.config.ts` configuration file
  - Update `tsconfig.json` to include test files
  - Add test scripts to `gui/package.json` (test, test:ui, test:coverage)
  - Set up global test utilities in `gui/src/test/setup.ts`
  - Configure jsdom environment for DOM testing

- [ ] Create frontend test utilities:
  - Create `gui/src/test/utils.tsx` with custom render functions
  - Add mock wrappers for providers (ToastProvider, etc.)
  - Create mock store factories for Zustand stores
  - Add `mockWebSocket` helper for WebSocket connection testing
  - Create `waitForState` utility for async store updates

- [ ] Create backend API integration tests (initial set):
  - Create `backend/tests/test_api_health.py` testing health endpoint
  - Create `backend/tests/test_api_settings.py` testing settings CRUD
  - Create `backend/tests/test_api_models.py` testing model listing
  - Create `backend/tests/test_api_transcribe.py` with mocked model
  - Verify all tests pass with `pytest -v`

- [ ] Create frontend component tests (initial set):
  - Create `gui/src/renderer/src/components/__tests__/ModelSelector.test.tsx`
  - Create `gui/src/renderer/src/components/__tests__/DeviceSelector.test.tsx`
  - Create `gui/src/renderer/src/components/__tests__/HotkeyInput.test.tsx`
  - Create `gui/src/renderer/src/pages/__tests__/Settings.test.tsx`
  - Verify all tests pass with `npm test`

- [ ] Add testing documentation:
  - Create `backend/tests/README.md` explaining backend testing approach
  - Create `gui/tests/README.md` explaining frontend testing approach
  - Document how to run tests, how to write new tests, and how to debug
  - Add example test templates for reference

- [ ] Set up pre-commit hooks for testing:
  - Add `pre-commit` configuration to `.pre-commit-config.yaml`
  - Add hook to run backend tests on changed Python files
  - Add hook to run frontend tests on changed TSX/TS files
  - Add hook to run type checking (mypy for Python, tsc for TypeScript)

- [ ] Configure CI/CD test pipeline (optional but recommended):
  - Create `.github/workflows/test.yml` for GitHub Actions
  - Set up Python environment and run backend tests
  - Set up Node environment and run frontend tests
  - Add coverage reporting to codecov or similar

- [ ] Verify test framework is working:
  - Run `pytest --cov` from backend directory and verify coverage report
  - Run `npm test -- --coverage` from gui directory and verify coverage
  - Confirm tests run in under 30 seconds total
  - Confirm adding a failing test causes CI to fail
