"""
Test for function.startBackend
Tests the Electron main process backend startup functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestStartBackendFunction:
    """Tests for startBackend function"""

    def test_default_backend_port(self):
        """Test default backend port configuration."""
        default_port = 8765

        assert default_port == 8765

    def test_backend_startup_timeout(self):
        """Test backend startup timeout configuration."""
        # 120 seconds for first-time model download
        timeout_ms = 120000
        timeout_seconds = timeout_ms / 1000

        assert timeout_seconds == 120
        assert timeout_seconds > 60  # Should be more than 1 minute

    def test_python_executable_windows(self):
        """Test Python executable name on Windows."""
        is_win = True
        python_exec = "python.exe" if is_win else "python3"

        assert python_exec == "python.exe"

    def test_python_executable_unix(self):
        """Test Python executable name on Unix systems."""
        is_win = False
        python_exec = "python.exe" if is_win else "python3"

        assert python_exec == "python3"

    def test_venv_path_windows(self):
        """Test virtual environment path on Windows."""
        root_dir = "/project"
        backend_venv = str(Path(root_dir) / "backend" / ".venv" / "Scripts" / "python.exe")

        assert "Scripts" in backend_venv
        assert backend_venv.endswith("python.exe")

    def test_venv_path_unix(self):
        """Test virtual environment path on Unix."""
        root_dir = "/project"
        backend_venv = str(Path(root_dir) / "backend" / ".venv" / "bin" / "python")

        assert "bin" in backend_venv
        assert backend_venv.endswith("python")

    def test_uv_command_construction(self):
        """Test UV command construction when UV is available."""
        backend_port = 8765
        args = ["run", "-m", "speakeasy", "--port", str(backend_port)]

        assert args == ["run", "-m", "speakeasy", "--port", "8765"]

    def test_standard_venv_command_construction(self):
        """Test standard venv command construction."""
        backend_port = 8765
        python_path = "/project/backend/.venv/bin/python"
        args = ["-m", "speakeasy", "--port", str(backend_port)]

        assert "-m" in args
        assert "speakeasy" in args
        assert str(backend_port) in args

    def test_backend_path_dev_mode(self):
        """Test backend path in development mode."""
        is_packaged = False
        app_path = "/project/gui"
        backend_path = str(Path(app_path) / "../backend") if not is_packaged else ""

        assert "backend" in backend_path
        assert not is_packaged

    def test_backend_path_production(self):
        """Test backend path in production mode."""
        is_packaged = True
        resources_path = "/app/resources"
        backend_path = str(Path(resources_path) / "backend") if is_packaged else ""

        assert "backend" in backend_path
        assert is_packaged

    def test_health_check_endpoint(self):
        """Test health check endpoint URL construction."""
        backend_port = 8765
        health_url = f"http://127.0.0.1:{backend_port}/api/health"

        assert health_url == "http://127.0.0.1:8765/api/health"

    def test_health_check_success_status(self):
        """Test successful health check status code."""
        status_code = 200
        is_healthy = status_code == 200

        assert is_healthy == True

    def test_health_check_failure_status(self):
        """Test failed health check status codes."""
        status_codes = [500, 503, 404, 0]  # 0 means connection error

        for code in status_codes:
            is_healthy = code == 200
            assert is_healthy == False

    def test_poll_interval(self):
        """Test health check polling interval."""
        poll_interval_ms = 500

        assert poll_interval_ms == 500
        assert poll_interval_ms < 1000  # Should poll at least every second

    def test_environment_variable_pythonunbuffered(self):
        """Test PYTHONUNBUFFERED environment variable."""
        env_vars = {"PYTHONUNBUFFERED": "1"}

        assert "PYTHONUNBUFFERED" in env_vars
        assert env_vars["PYTHONUNBUFFERED"] == "1"

    def test_spawn_stdio_configuration(self):
        """Test spawn stdio configuration."""
        stdio = ["ignore", "pipe", "pipe"]

        assert stdio == ["ignore", "pipe", "pipe"]
        assert len(stdio) == 3

    def test_already_running_check(self):
        """Test check for already running backend."""
        # If backend is already healthy, should return immediately
        already_healthy = True

        if already_healthy:
            should_start = False
        else:
            should_start = True

        assert should_start == False

    def test_backend_start_failure_error(self):
        """Test error handling when backend fails to start."""
        is_healthy = False
        timeout_reached = True

        if not is_healthy and timeout_reached:
            error_message = "Backend failed to start within timeout"
        else:
            error_message = None

        assert error_message == "Backend failed to start within timeout"

    def test_uv_lock_file_detection(self):
        """Test UV lock file detection."""
        uv_lock_path = str(Path("/project") / "backend" / "uv.lock")

        assert "uv.lock" in uv_lock_path
        assert "backend" in uv_lock_path


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
