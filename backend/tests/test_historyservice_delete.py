"""
Test for HistoryService.delete
Comprehensive test suite covering deletion of transcription records.
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
async def initialized_service_with_records():
    """Create and initialize a HistoryService with sample records."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_history.db"
    service = HistoryService(db_path=db_path)

    await service.initialize()

    # Add some records
    records = []
    for i in range(5):
        record = await service.add(
            text=f"Test record {i}",
            duration_ms=3000 + i * 1000,
            model_used="test-model",
        )
        records.append(record)

    yield service, records

    # Cleanup
    await service.close()
    if db_path.exists():
        db_path.unlink()
    if temp_dir:
        os.rmdir(temp_dir)


class TestHistoryServiceDelete:
    """Tests for HistoryService.delete"""

    @pytest.mark.asyncio
    async def test_delete_existing_record(self, initialized_service_with_records):
        """Test deleting an existing record."""
        service, records = await initialized_service_with_records

        target_id = records[0].id

        result = await service.delete(target_id)

        assert result is True

        # Verify record is gone
        retrieved = await service.get(target_id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_record(self, initialized_service_with_records):
        """Test deleting a record that doesn't exist."""
        service, _ = await initialized_service_with_records

        result = await service.delete("non-existent-id")

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_removes_from_database(self, initialized_service_with_records):
        """Test that deleted records are removed from database."""
        service, records = await initialized_service_with_records

        target_id = records[0].id
        await service.delete(target_id)

        # Verify count decreased
        all_records, total, _ = await service.list(limit=100)

        assert total == 4
        assert target_id not in [r.id for r in all_records]

    @pytest.mark.asyncio
    async def test_delete_updates_fts_index(self, initialized_service_with_records):
        """Test that deleted records are removed from FTS index."""
        service, records = await initialized_service_with_records

        target_id = records[0].id
        target_text = records[0].text

        await service.delete(target_id)

        # Search should no longer find deleted text
        search_results, search_total, _ = await service.list(search=target_text)

        # Note: FTS index may take time to update, but our triggers should handle it immediately
        assert search_total == 0

    @pytest.mark.asyncio
    async def test_delete_empty_id(self, initialized_service_with_records):
        """Test deleting with an empty ID."""
        service, _ = await initialized_service_with_records

        result = await service.delete("")

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_invalid_id_format(self, initialized_service_with_records):
        """Test deleting with various invalid ID formats."""
        service, _ = await initialized_service_with_records

        invalid_ids = [
            None,
            "",
            "   ",
            "invalid-uuid",
            "12345",
            "a" * 1000,
        ]

        for invalid_id in invalid_ids:
            if invalid_id is not None:  # None might cause different error
                result = await service.delete(invalid_id)
                assert result is False

    @pytest.mark.asyncio
    async def test_delete_all_records(self, initialized_service_with_records):
        """Test deleting all records one by one."""
        service, records = await initialized_service_with_records

        for record in records:
            result = await service.delete(record.id)
            assert result is True

        # Verify all are gone
        all_records, total, _ = await service.list(limit=100)

        assert total == 0
        assert len(all_records) == 0

    @pytest.mark.asyncio
    async def test_delete_does_not_affect_other_records(self, initialized_service_with_records):
        """Test that deleting one record doesn't affect others."""
        service, records = await initialized_service_with_records

        other_ids = [r.id for r in records[1:]]
        target_id = records[0].id

        await service.delete(target_id)

        # Verify others still exist
        for other_id in other_ids:
            retrieved = await service.get(other_id)
            assert retrieved is not None

    @pytest.mark.asyncio
    async def test_delete_same_record_twice(self, initialized_service_with_records):
        """Test deleting the same record twice."""
        service, records = await initialized_service_with_records

        target_id = records[0].id

        result1 = await service.delete(target_id)
        result2 = await service.delete(target_id)

        assert result1 is True
        assert result2 is False  # Already deleted

    @pytest.mark.asyncio
    async def test_delete_fails_when_not_initialized(self, temp_db_path):
        """Test that delete fails when database is not initialized."""
        service = HistoryService(db_path=temp_db_path)

        with pytest.raises(RuntimeError, match="Database not initialized"):
            await service.delete("some-id")

    @pytest.mark.asyncio
    async def test_delete_cascade_to_fts(self, initialized_service_with_records):
        """Test that delete cascades to FTS table properly."""
        service, records = await initialized_service_with_records

        # Search before delete
        target_text = records[0].text
        before_results, before_count, _ = await service.list(search=target_text)

        assert before_count == 1

        # Delete
        await service.delete(records[0].id)

        # Search after delete
        after_results, after_count, _ = await service.list(search=target_text)

        assert after_count == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
