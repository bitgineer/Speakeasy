"""
Test for BatchService.__init__
Comprehensive test suite for BatchService initialization.
"""

import pytest
import asyncio
from pathlib import Path
import sys
import tempfile
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.services.batch import (
    BatchService,
    BatchJob,
    BatchFile,
    BatchJobStatus,
    BatchFileStatus,
)


@pytest.fixture
def temp_db_path():
    """Create a temporary database path."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_batch.db"
    yield db_path
    # Cleanup
    if db_path.exists():
        db_path.unlink()
    if temp_dir:
        os.rmdir(temp_dir)


class TestBatchServiceInit:
    """Tests for BatchService.__init__"""

    def test_basic_initialization(self, temp_db_path):
        """Test basic initialization with a valid database path."""
        service = BatchService(db_path=temp_db_path)

        assert service.db_path == temp_db_path
        assert service._db is None
        assert service._jobs == {}
        assert service._cancel_flags == {}
        assert service._processing_locks == {}

    def test_initialization_with_nonexistent_path(self, temp_db_path):
        """Test that initialization works with non-existent path."""
        nonexistent_path = temp_db_path.parent / "does" / "not" / "exist" / "batch.db"
        service = BatchService(db_path=nonexistent_path)

        assert service.db_path == nonexistent_path
        assert not nonexistent_path.parent.exists()

    def test_multiple_services_same_path(self, temp_db_path):
        """Test creating multiple services pointing to the same database."""
        service1 = BatchService(db_path=temp_db_path)
        service2 = BatchService(db_path=temp_db_path)

        assert service1.db_path == service2.db_path
        assert service1._db is None
        assert service2._db is None
        assert service1._jobs is not service2._jobs  # Different dict objects

    def test_initialization_preserves_path_object(self, temp_db_path):
        """Test that the path object is preserved."""
        service = BatchService(db_path=temp_db_path)

        assert isinstance(service.db_path, Path)

    def test_initialization_with_relative_path(self):
        """Test initialization with a relative path."""
        rel_path = Path("relative") / "batch.db"
        service = BatchService(db_path=rel_path)

        assert service.db_path == rel_path

    def test_initialization_creates_empty_collections(self, temp_db_path):
        """Test that initialization creates empty collections."""
        service = BatchService(db_path=temp_db_path)

        assert service._jobs == {}
        assert service._cancel_flags == {}
        assert service._processing_locks == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
