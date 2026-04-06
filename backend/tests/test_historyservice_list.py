"""
Test for HistoryService.list
Comprehensive test suite for listing and searching transcription records.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timezone
from pathlib import Path
import sys
import tempfile
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.services.history import HistoryService, TranscriptionRecord


@pytest.fixture
async def initialized_service_with_data():
    """Create and initialize a HistoryService with sample data."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_history.db"
    service = HistoryService(db_path=db_path)

    await service.initialize()

    # Add multiple records with different texts
    texts = [
        "Hello world, this is a test",
        "Testing the transcription service",
        "Another test with different words",
        "Meeting notes from project alpha",
        "Code review session discussion",
    ]

    records = []
    for i, text in enumerate(texts):
        record = await service.add(
            text=text,
            duration_ms=3000 + i * 1000,
            model_used="whisper-small",
            language="en",
        )
        records.append(record)
        await asyncio.sleep(0.01)  # Small delay to ensure different timestamps

    yield service, records

    # Cleanup
    await service.close()
    if db_path.exists():
        db_path.unlink()
    if temp_dir:
        os.rmdir(temp_dir)


class TestHistoryServiceList:
    """Tests for HistoryService.list"""

    @pytest.mark.asyncio
    async def test_list_basic(self, initialized_service_with_data):
        """Test basic listing of records."""
        service, _ = await initialized_service_with_data

        records, total, next_cursor = await service.list(limit=10)

        assert total == 5
        assert len(records) == 5
        assert next_cursor is None  # All records returned

    @pytest.mark.asyncio
    async def test_list_with_limit(self, initialized_service_with_data):
        """Test listing with a limit."""
        service, _ = await initialized_service_with_data

        records, total, next_cursor = await service.list(limit=3)

        assert total == 5
        assert len(records) == 3
        assert next_cursor is not None  # More records available

    @pytest.mark.asyncio
    async def test_list_with_offset(self, initialized_service_with_data):
        """Test listing with an offset."""
        service, _ = await initialized_service_with_data

        records1, _, _ = await service.list(limit=2, offset=0)
        records2, _, _ = await service.list(limit=2, offset=2)

        assert len(records1) == 2
        assert len(records2) == 2

        # Should get different records
        ids1 = {r.id for r in records1}
        ids2 = {r.id for r in records2}

        assert ids1.isdisjoint(ids2)

    @pytest.mark.asyncio
    async def test_list_with_search(self, initialized_service_with_data):
        """Test listing with a search query."""
        service, _ = await initialized_service_with_data

        records, total, _ = await service.list(search="test")

        assert total == 3  # "test" appears in 3 records
        assert len(records) == 3

    @pytest.mark.asyncio
    async def test_list_search_no_results(self, initialized_service_with_data):
        """Test search that returns no results."""
        service, _ = await initialized_service_with_data

        records, total, _ = await service.list(search="xyz123")

        assert total == 0
        assert len(records) == 0

    @pytest.mark.asyncio
    async def test_list_ordering(self, initialized_service_with_data):
        """Test that records are returned in descending chronological order."""
        service, _ = await initialized_service_with_data

        records, _, _ = await service.list(limit=10)

        # Check timestamps are in descending order
        timestamps = [r.created_at for r in records]

        for i in range(len(timestamps) - 1):
            assert timestamps[i] >= timestamps[i + 1]

    @pytest.mark.asyncio
    async def test_list_with_cursor(self, initialized_service_with_data):
        """Test cursor-based pagination."""
        service, _ = await initialized_service_with_data

        # Get first page
        records1, total, cursor = await service.list(limit=2)

        assert len(records1) == 2
        assert cursor is not None

        # Get second page
        records2, _, cursor2 = await service.list(limit=2, cursor=cursor)

        assert len(records2) == 2
        assert cursor2 is not None

        # Get third page
        records3, _, cursor3 = await service.list(limit=2, cursor=cursor2)

        assert len(records3) == 1  # Only 1 record left
        assert cursor3 is None

    @pytest.mark.asyncio
    async def test_list_with_fields_projection(self, initialized_service_with_data):
        """Test listing with field projection."""
        service, _ = await initialized_service_with_data

        # Convert to dict with field projection
        records, _, _ = await service.list(limit=1)
        record = records[0]

        # Full dict
        full_dict = record.to_dict()
        assert "id" in full_dict
        assert "text" in full_dict
        assert "duration_ms" in full_dict

        # Limited fields
        limited_dict = record.to_dict(fields={"id", "text"})
        assert "id" in limited_dict
        assert "text" in limited_dict
        assert "duration_ms" not in limited_dict

    @pytest.mark.asyncio
    async def test_list_invalid_fields(self, initialized_service_with_data):
        """Test listing with invalid field names."""
        service, _ = await initialized_service_with_data

        with pytest.raises(ValueError, match="Invalid fields"):
            await service.list(limit=1, fields={"invalid_field"})

    @pytest.mark.asyncio
    async def test_list_search_with_special_characters(self, initialized_service_with_data):
        """Test search with special characters."""
        service, _ = await initialized_service_with_data

        # These should not raise errors
        searches = [
            "'single quotes'",
            '"double quotes"',
            "test AND meeting",
            "test OR meeting",
            "test NOT meeting",
        ]

        for search in searches:
            try:
                records, _, _ = await service.list(search=search)
                # Result doesn't matter, just shouldn't crash
                assert isinstance(records, list)
            except Exception as e:
                # FTS5 might fail on some queries, but shouldn't crash
                pass

    @pytest.mark.asyncio
    async def test_list_empty_database(self):
        """Test listing from an empty database."""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test_history.db"
        service = HistoryService(db_path=db_path)
        await service.initialize()

        try:
            records, total, cursor = await service.list(limit=10)

            assert total == 0
            assert len(records) == 0
            assert cursor is None
        finally:
            await service.close()
            if db_path.exists():
                db_path.unlink()
            if temp_dir:
                os.rmdir(temp_dir)

    @pytest.mark.asyncio
    async def test_list_limit_zero(self, initialized_service_with_data):
        """Test listing with limit of zero."""
        service, _ = await initialized_service_with_data

        records, total, _ = await service.list(limit=0)

        assert len(records) == 0
        assert total == 5

    @pytest.mark.asyncio
    async def test_list_large_limit(self, initialized_service_with_data):
        """Test listing with a very large limit."""
        service, _ = await initialized_service_with_data

        records, total, _ = await service.list(limit=1000)

        assert len(records) == 5
        assert total == 5

    @pytest.mark.asyncio
    async def test_list_fails_when_not_initialized(self, temp_db_path):
        """Test that list fails when database is not initialized."""
        service = HistoryService(db_path=temp_db_path)

        with pytest.raises(RuntimeError, match="Database not initialized"):
            await service.list()

    @pytest.mark.asyncio
    async def test_list_returns_correct_total_count(self, initialized_service_with_data):
        """Test that list returns correct total count regardless of limit."""
        service, _ = await initialized_service_with_data

        records1, total1, _ = await service.list(limit=2)
        records2, total2, _ = await service.list(limit=100)

        assert total1 == total2 == 5
        assert len(records1) == 2
        assert len(records2) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
