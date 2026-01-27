# SpeakEasy Backend Tests

This directory contains the test suite for the SpeakEasy backend API.

## Quick Start

```bash
# Run all tests
cd backend
pytest

# Run with coverage
pytest --cov

# Run specific test file
pytest tests/test_api_health.py

# Run tests in verbose mode
pytest -v

# Run tests matching a pattern
pytest -k "test_health"
```

## Test Structure

```
tests/
├── __init__.py
├── conftest.py          # Shared fixtures
├── test_api_health.py   # Health endpoint tests
├── test_api_settings.py # Settings CRUD tests
├── test_api_models.py   # Model listing tests
└── test_api_transcribe.py # Transcription flow tests
```

## Fixtures

All fixtures are defined in `conftest.py`:

| Fixture | Description |
|---------|-------------|
| `client` | FastAPI TestClient with mocked services |
| `async_client` | Async HTTP client for async tests |
| `test_settings` | In-memory settings configuration |
| `mock_model` | Mocked ModelWrapper (no real model loading) |
| `mock_audio` | Sample audio data (numpy array) |
| `clean_tmp_dir` | Temporary directory with auto-cleanup |
| `mock_transcriber` | Mocked transcriber service |
| `mock_settings_service` | Mocked settings service |
| `mock_history_service` | Mocked history service |

## Writing New Tests

### Basic Test

```python
def test_something(client):
    """Test description."""
    response = client.get("/api/endpoint")
    assert response.status_code == 200
    assert response.json()["key"] == "expected_value"
```

### Async Test

```python
import pytest

@pytest.mark.asyncio
async def test_async_operation(async_client):
    """Test async endpoint."""
    response = await async_client.get("/api/endpoint")
    assert response.status_code == 200
```

### Using Mocks

```python
def test_with_mock(client, mock_transcriber):
    """Test with mocked service."""
    # Configure mock behavior
    mock_transcriber.is_recording = True
    
    response = client.get("/api/transcribe/status")
    assert response.json()["is_recording"] is True
```

## Coverage

Coverage is configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = [
    "--cov=speakeasy",
    "--cov-report=term-missing",
    "--cov-report=html:htmlcov",
]
```

After running tests with coverage, view the HTML report:

```bash
# Generate coverage report
pytest --cov

# Open HTML report (on macOS)
open htmlcov/index.html

# On Linux
xdg-open htmlcov/index.html

# On Windows
start htmlcov/index.html
```

## Best Practices

1. **Test isolation**: Each test should be independent
2. **Use fixtures**: Leverage shared fixtures for setup
3. **Mock external services**: Don't hit real APIs or load real models
4. **Clear assertions**: Use descriptive assertion messages
5. **Test edge cases**: Include error paths and boundary conditions

## Troubleshooting

### Import errors

Make sure you're running from the backend directory:

```bash
cd backend
pytest
```

### Fixture not found

Check that `conftest.py` is in the `tests/` directory.

### Async test hangs

Ensure you have `pytest-asyncio` installed and `asyncio_mode = "auto"` in config.
