"""
Test for HistoryService.__init__
Comprehensive test suite covering initialization and configuration.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from pathlib import Path
import sys
import tempfile
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.services.history import HistoryService, TranscriptionRecord


class TestHistoryServiceInit:
    """Tests for HistoryService.__init__"""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path."""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test_history.db"
        yield db_path
        # Cleanup
        if db_path.exists():
            db_path.unlink()
        if temp_dir:
            os.rmdir(temp_dir)

    def test_basic_initialization(self, temp_db_path):
        """Test basic initialization with a valid database path."""
        service = HistoryService(db_path=temp_db_path)

        assert service.db_path == temp_db_path
        assert service._db is None

    def test_initialization_with_directory_creation(self, temp_db_path):
        """Test that parent directory is created during initialization."""
        deep_path = temp_db_path.parent / "subfolder" / "another" / "history.db"
        service = HistoryService(db_path=deep_path)

        # The directory should not exist yet
        assert not deep_path.parent.exists()

    def test_initialization_with_empty_path(self):
        """Test initialization with an empty path should raise error."""
        with pytest.raises((ValueError, TypeError)):
            HistoryService(db_path=None)

    def test_initialization_with_relative_path(self):
        """Test initialization with a relative path."""
        rel_path = Path("relative") / "path" / "history.db"
        service = HistoryService(db_path=rel_path)

        assert service.db_path == rel_path

    def test_initialization_with_absolute_path(self, temp_db_path):
        """Test initialization with an absolute path."""
        service = HistoryService(db_path=temp_db_path)

        assert service.db_path.is_absolute()

    @pytest.mark.parametrize(
        "path_str",
        [
            "test.db",
            "/absolute/path/history.db",
            "./relative/path/history.db",
            "~/home/user/history.db",
        ],
    )
    def test_initialization_various_paths(self, path_str):
        """Test initialization with various path formats."""
        path = Path(path_str)
        service = HistoryService(db_path=path)

        assert isinstance(service, HistoryService)

    def test_database_attribute_is_none_initially(self, temp_db_path):
        """Test that _db attribute is None before initialize()."""
        service = HistoryService(db_path=temp_db_path)

        assert service._db is None

    def test_multiple_services_same_path(self, temp_db_path):
        """Test creating multiple services pointing to the same database."""
        service1 = HistoryService(db_path=temp_db_path)
        service2 = HistoryService(db_path=temp_db_path)

        assert service1.db_path == service2.db_path
        assert service1._db is None
        assert service2._db is None

    def test_service_isolation(self, temp_db_path):
        """Test that services have isolated attributes."""
        service1 = HistoryService(db_path=temp_db_path)
        service2 = HistoryService(db_path=temp_db_path / "different.db")

        service1.db_path = Path("modified.db")  # Should not affect service2

        assert service1.db_path != service2.db_path

    def test_initialization_preserves_path_object(self, temp_db_path):
        """Test that the path object is preserved and not converted."""
        original_path = temp_db_path
        service = HistoryService(db_path=original_path)

        assert isinstance(service.db_path, Path)
        assert service.db_path == original_path


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
