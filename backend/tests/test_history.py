"""
Comprehensive tests for the HistoryService.

Tests cover:
- Database initialization and schema creation
- CRUD operations (add, get, list, delete, clear)
- Full-text search via FTS5
- Pagination and ordering
- Statistics aggregation
- Error handling for uninitialized state
"""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path

import pytest

from speakeasy.services.history import HistoryService, TranscriptionRecord


@pytest.fixture
async def history_service(tmp_path: Path):
    """
    Provide an initialized HistoryService with automatic cleanup.

    Uses tmp_path for test isolation - each test gets a fresh database.
    """
    db_path = tmp_path / "test_history.db"
    service = HistoryService(db_path)
    await service.initialize()
    yield service
    await service.close()


@pytest.fixture
def uninitialized_service(tmp_path: Path) -> HistoryService:
    """Provide an uninitialized HistoryService for error testing."""
    db_path = tmp_path / "uninitialized.db"
    return HistoryService(db_path)


class TestInitialization:
    """Tests for database initialization."""

    async def test_initialize_creates_tables(self, tmp_path: Path):
        """DB schema creation - tables and indexes are created."""
        db_path = tmp_path / "init_test.db"
        service = HistoryService(db_path)

        await service.initialize()

        # Verify database file was created
        assert db_path.exists()

        # Verify tables exist by querying them
        assert service._db is not None

        # Check main table
        cursor = await service._db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='transcriptions'"
        )
        assert await cursor.fetchone() is not None

        # Check FTS5 virtual table
        cursor = await service._db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='transcriptions_fts'"
        )
        assert await cursor.fetchone() is not None

        # Check index
        cursor = await service._db.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_transcriptions_created_at'"
        )
        assert await cursor.fetchone() is not None

        await service.close()

    async def test_initialize_creates_parent_directories(self, tmp_path: Path):
        """Initialize creates parent directories if they don't exist."""
        db_path = tmp_path / "nested" / "dirs" / "test.db"
        service = HistoryService(db_path)

        await service.initialize()

        assert db_path.parent.exists()
        assert db_path.exists()

        await service.close()


class TestAddTranscription:
    """Tests for adding transcriptions."""

    async def test_add_transcription(self, history_service: HistoryService):
        """Insert and return record with all fields populated."""
        record = await history_service.add(
            text="Hello, world!",
            duration_ms=1500,
            model_used="whisper-tiny",
            language="en",
        )

        assert record.text == "Hello, world!"
        assert record.duration_ms == 1500
        assert record.model_used == "whisper-tiny"
        assert record.language == "en"
        assert isinstance(record.created_at, datetime)
        assert record.id is not None

    async def test_add_generates_uuid(self, history_service: HistoryService):
        """UUID format validation - generated ID is valid UUID4."""
        record = await history_service.add(
            text="Test transcription",
            duration_ms=1000,
        )

        # Validate UUID format
        parsed_uuid = uuid.UUID(record.id)
        assert parsed_uuid.version == 4
        assert str(parsed_uuid) == record.id

    async def test_add_with_optional_fields_none(self, history_service: HistoryService):
        """Add transcription with optional fields as None."""
        record = await history_service.add(
            text="Minimal record",
            duration_ms=500,
            model_used=None,
            language=None,
        )

        assert record.model_used is None
        assert record.language is None


class TestGetTranscription:
    """Tests for retrieving transcriptions."""

    async def test_get_by_id(self, history_service: HistoryService):
        """Retrieve existing record by ID."""
        added = await history_service.add(
            text="Retrievable text",
            duration_ms=2000,
            model_used="parakeet",
            language="en",
        )

        retrieved = await history_service.get(added.id)

        assert retrieved is not None
        assert retrieved.id == added.id
        assert retrieved.text == "Retrievable text"
        assert retrieved.duration_ms == 2000
        assert retrieved.model_used == "parakeet"
        assert retrieved.language == "en"

    async def test_get_nonexistent_returns_none(self, history_service: HistoryService):
        """404 case - nonexistent ID returns None."""
        result = await history_service.get("nonexistent-uuid-12345")

        assert result is None


class TestListTranscriptions:
    """Tests for listing transcriptions."""

    async def test_list_empty(self, history_service: HistoryService):
        """Empty database returns empty list."""
        records, total = await history_service.list()

        assert records == []
        assert total == 0

    async def test_list_with_records(self, history_service: HistoryService):
        """Multiple records returned correctly."""
        # Add multiple records
        await history_service.add(text="First", duration_ms=100)
        await history_service.add(text="Second", duration_ms=200)
        await history_service.add(text="Third", duration_ms=300)

        records, total = await history_service.list()

        assert len(records) == 3
        assert total == 3

    async def test_list_pagination(self, history_service: HistoryService):
        """Limit and offset work correctly for pagination."""
        # Add 5 records
        for i in range(5):
            await history_service.add(text=f"Record {i}", duration_ms=i * 100)

        # Get first page (2 items)
        page1, total = await history_service.list(limit=2, offset=0)
        assert len(page1) == 2
        assert total == 5

        # Get second page (2 items)
        page2, total = await history_service.list(limit=2, offset=2)
        assert len(page2) == 2
        assert total == 5

        # Get third page (1 item)
        page3, total = await history_service.list(limit=2, offset=4)
        assert len(page3) == 1
        assert total == 5

        # Verify no overlap between pages
        page1_ids = {r.id for r in page1}
        page2_ids = {r.id for r in page2}
        page3_ids = {r.id for r in page3}
        assert page1_ids.isdisjoint(page2_ids)
        assert page2_ids.isdisjoint(page3_ids)

    async def test_list_ordering(self, history_service: HistoryService):
        """Records ordered by created_at DESC (newest first)."""
        # Add records with small delays to ensure different timestamps
        await history_service.add(text="Oldest", duration_ms=100)
        await asyncio.sleep(0.01)  # Small delay
        await history_service.add(text="Middle", duration_ms=200)
        await asyncio.sleep(0.01)
        await history_service.add(text="Newest", duration_ms=300)

        records, _ = await history_service.list()

        # Newest should be first
        assert records[0].text == "Newest"
        assert records[1].text == "Middle"
        assert records[2].text == "Oldest"

        # Verify timestamps are in descending order
        for i in range(len(records) - 1):
            assert records[i].created_at >= records[i + 1].created_at


class TestSearchTranscriptions:
    """Tests for full-text search."""

    async def test_search_fts5(self, history_service: HistoryService):
        """Full-text search matches relevant records."""
        await history_service.add(text="The quick brown fox jumps", duration_ms=100)
        await history_service.add(text="A lazy dog sleeps", duration_ms=200)
        await history_service.add(text="The fox is clever", duration_ms=300)

        # Search for "fox"
        records, total = await history_service.list(search="fox")

        assert total == 2
        assert len(records) == 2
        assert all("fox" in r.text.lower() for r in records)

    async def test_search_no_results(self, history_service: HistoryService):
        """Search with no matches returns empty list."""
        await history_service.add(text="Hello world", duration_ms=100)
        await history_service.add(text="Goodbye world", duration_ms=200)

        records, total = await history_service.list(search="nonexistent")

        assert records == []
        assert total == 0

    async def test_search_with_pagination(self, history_service: HistoryService):
        """Search results can be paginated."""
        # Add multiple matching records
        for i in range(5):
            await history_service.add(text=f"Python programming example {i}", duration_ms=i * 100)

        # Add non-matching records
        await history_service.add(text="JavaScript code", duration_ms=500)

        # Search with pagination
        page1, total = await history_service.list(search="Python", limit=2, offset=0)
        page2, total = await history_service.list(search="Python", limit=2, offset=2)

        assert total == 5
        assert len(page1) == 2
        assert len(page2) == 2


class TestDeleteTranscription:
    """Tests for deleting transcriptions."""

    async def test_delete_existing(self, history_service: HistoryService):
        """Delete returns True for existing record."""
        record = await history_service.add(text="To be deleted", duration_ms=100)

        result = await history_service.delete(record.id)

        assert result is True

        # Verify it's actually deleted
        retrieved = await history_service.get(record.id)
        assert retrieved is None

    async def test_delete_nonexistent(self, history_service: HistoryService):
        """Delete returns False for nonexistent record."""
        result = await history_service.delete("nonexistent-id-12345")

        assert result is False


class TestClearTranscriptions:
    """Tests for clearing all transcriptions."""

    async def test_clear_all(self, history_service: HistoryService):
        """Bulk delete removes all records and returns count."""
        # Add multiple records
        await history_service.add(text="Record 1", duration_ms=100)
        await history_service.add(text="Record 2", duration_ms=200)
        await history_service.add(text="Record 3", duration_ms=300)

        deleted_count = await history_service.clear()

        assert deleted_count == 3

        # Verify all records are gone
        records, total = await history_service.list()
        assert records == []
        assert total == 0

    async def test_clear_empty_database(self, history_service: HistoryService):
        """Clear on empty database returns 0."""
        deleted_count = await history_service.clear()

        assert deleted_count == 0


class TestGetStats:
    """Tests for statistics aggregation."""

    async def test_get_stats(self, history_service: HistoryService):
        """Aggregation values are correct."""
        await history_service.add(text="First", duration_ms=1000)
        await history_service.add(text="Second", duration_ms=2000)
        await history_service.add(text="Third", duration_ms=3000)

        stats = await history_service.get_stats()

        assert stats["total_count"] == 3
        assert stats["total_duration_ms"] == 6000
        assert stats["first_transcription"] is not None
        assert stats["last_transcription"] is not None

    async def test_get_stats_empty_database(self, history_service: HistoryService):
        """Stats on empty database return zeros/nulls."""
        stats = await history_service.get_stats()

        assert stats["total_count"] == 0
        assert stats["total_duration_ms"] == 0
        assert stats["first_transcription"] is None
        assert stats["last_transcription"] is None


class TestUninitializedService:
    """Tests for error handling when service is not initialized."""

    async def test_uninitialized_add_raises(self, uninitialized_service: HistoryService):
        """RuntimeError raised when add() called before initialize()."""
        with pytest.raises(RuntimeError, match="Database not initialized"):
            await uninitialized_service.add(text="Test", duration_ms=100)

    async def test_uninitialized_get_raises(self, uninitialized_service: HistoryService):
        """RuntimeError raised when get() called before initialize()."""
        with pytest.raises(RuntimeError, match="Database not initialized"):
            await uninitialized_service.get("some-id")

    async def test_uninitialized_list_raises(self, uninitialized_service: HistoryService):
        """RuntimeError raised when list() called before initialize()."""
        with pytest.raises(RuntimeError, match="Database not initialized"):
            await uninitialized_service.list()

    async def test_uninitialized_delete_raises(self, uninitialized_service: HistoryService):
        """RuntimeError raised when delete() called before initialize()."""
        with pytest.raises(RuntimeError, match="Database not initialized"):
            await uninitialized_service.delete("some-id")

    async def test_uninitialized_clear_raises(self, uninitialized_service: HistoryService):
        """RuntimeError raised when clear() called before initialize()."""
        with pytest.raises(RuntimeError, match="Database not initialized"):
            await uninitialized_service.clear()

    async def test_uninitialized_get_stats_raises(self, uninitialized_service: HistoryService):
        """RuntimeError raised when get_stats() called before initialize()."""
        with pytest.raises(RuntimeError, match="Database not initialized"):
            await uninitialized_service.get_stats()


class TestTranscriptionRecord:
    """Tests for TranscriptionRecord dataclass."""

    def test_to_dict_serialization(self):
        """TranscriptionRecord.to_dict() produces correct JSON-serializable dict."""
        created = datetime(2024, 1, 15, 10, 30, 0)
        record = TranscriptionRecord(
            id="test-uuid-123",
            text="Sample transcription text",
            duration_ms=2500,
            model_used="whisper-large",
            language="en",
            created_at=created,
        )

        result = record.to_dict()

        assert result == {
            "id": "test-uuid-123",
            "text": "Sample transcription text",
            "duration_ms": 2500,
            "model_used": "whisper-large",
            "language": "en",
            "created_at": "2024-01-15T10:30:00",
        }

    def test_to_dict_with_none_fields(self):
        """to_dict() handles None optional fields correctly."""
        record = TranscriptionRecord(
            id="test-uuid-456",
            text="Minimal record",
            duration_ms=1000,
            model_used=None,
            language=None,
            created_at=datetime(2024, 6, 1, 12, 0, 0),
        )

        result = record.to_dict()

        assert result["model_used"] is None
        assert result["language"] is None
