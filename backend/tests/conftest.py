"""Shared fixtures for the Speakeasy backend test suite."""

import pytest


@pytest.fixture
def temp_db_path(tmp_path):
    """Path for a SQLite database under pytest's per-test temp directory."""
    return tmp_path / "test.db"


@pytest.fixture
def temp_settings_path(tmp_path):
    """Path for a settings JSON file under pytest's per-test temp directory."""
    return tmp_path / "settings.json"
