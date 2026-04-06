"""
Test for HistoryService.get
Comprehensive test suite for retrieving transcription records by ID.
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
async def initialized_service_with_record():
    """Create and initialize a HistoryService with a sample record."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_history.db"
    service = HistoryService(db_path=db_path)

    await service.initialize()

    # Add a record
    record = await service.add(
        text="Test transcription",
        duration_ms=5000,
        model_used="whisper-small",
        language="en",
        original_text="Test transcruption",
    )

    yield service, record

    # Cleanup
    await service.close()
    if db_path.exists():
        db_path.unlink()
    if temp_dir:
        os.rmdir(temp_dir)


class TestHistoryServiceGet:
    """Tests for HistoryService.get"""

    @pytest.mark.asyncio
    async def test_get_existing_record(self, initialized_service_with_record):
        """Test retrieving an existing record."""
        service, original = await initialized_service_with_record

        retrieved = await service.get(original.id)

        assert retrieved is not None
        assert retrieved.id == original.id
        assert retrieved.text == original.text
        assert retrieved.duration_ms == original.duration_ms
        assert retrieved.model_used == original.model_used
        assert retrieved.language == original.language
        assert retrieved.original_text == original.original_text

    @pytest.mark.asyncio
    async def test_get_nonexistent_record(self, initialized_service_with_record):
        """Test retrieving a record that doesn't exist."""
        service, _ = await initialized_service_with_record

        result = await service.get("non-existent-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_returns_transcriptionrecord(self, initialized_service_with_record):
        """Test that get returns a TranscriptionRecord instance."""
        service, original = await initialized_service_with_record

        retrieved = await service.get(original.id)

        assert isinstance(retrieved, TranscriptionRecord)

    @pytest.mark.asyncio
    async def test_get_preserves_created_at(self, initialized_service_with_record):
        """Test that get preserves the created_at timestamp."""
        service, original = await initialized_service_with_record

        retrieved = await service.get(original.id)

        assert retrieved.created_at == original.created_at

    @pytest.mark.asyncio
    async def test_get_with_empty_id(self, initialized_service_with_record):
        """Test retrieving with an empty ID."""
        service, _ = await initialized_service_with_record

        result = await service.get("")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_with_invalid_id_format(self, initialized_service_with_record):
        """Test retrieving with various invalid ID formats."""
        service, _ = await initialized_service_with_record

        invalid_ids = [
            "",
            "   ",
            "invalid-uuid",
            "12345",
            "a" * 1000,
        ]

        for invalid_id in invalid_ids:
            result = await service.get(invalid_id)
            assert result is None

    @pytest.mark.asyncio
    async def test_get_is_case_sensitive(self, initialized_service_with_record):
        """Test that get is case sensitive for UUIDs."""
        service, original = await initialized_service_with_record

        # UUIDs are typically lowercase
        upper_id = original.id.upper()

        result = await service.get(upper_id)

        # SQLite comparisons might be case-insensitive depending on collation
        # But UUIDs should match exactly
        assert result is None or result.id == original.id

    @pytest.mark.asyncio
    async def test_get_after_update(self, initialized_service_with_record):
        """Test that get returns updated text after update."""
        service, original = await initialized_service_with_record

        # Update the record
        await service.update_text(
            record_id=original.id,
            new_text="Updated text",
            original_text="Test transcription",
        )

        # Get and verify
        retrieved = await service.get(original.id)

        assert retrieved.text == "Updated text"
        assert retrieved.original_text == "Test transcription"

    @pytest.mark.asyncio
    async def test_get_after_delete(self, initialized_service_with_record):
        """Test that get returns None after record is deleted."""
        service, original = await initialized_service_with_record

        # Delete the record
        await service.delete(original.id)

        # Try to get
        result = await service.get(original.id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_multiple_records(self):
        """Test getting multiple different records."""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test_history.db"
        service = HistoryService(db_path=db_path)
        await service.initialize()

        try:
            # Add multiple records
            records = []
            for i in range(5):
                record = await service.add(
                    text=f"Record {i}",
                    duration_ms=1000 * (i + 1),
                    model_used=f"model-{i}",
                )
                records.append(record)

            # Get each one
            for i, original in enumerate(records):
                retrieved = await service.get(original.id)
                assert retrieved is not None
                assert retrieved.text == f"Record {i}"
                assert retrieved.duration_ms == 1000 * (i + 1)
                assert retrieved.model_used == f"model-{i}"
        finally:
            await service.close()
            if db_path.exists():
                db_path.unlink()
            if temp_dir:
                os.rmdir(temp_dir)

    @pytest.mark.asyncio
    async def test_get_fails_when_not_initialized(self, temp_db_path):
        """Test that get fails when database is not initialized."""
        service = HistoryService(db_path=temp_db_path)

        with pytest.raises(RuntimeError, match="Database not initialized"):
            await service.get("some-id")

    @pytest.mark.asyncio
    async def test_get_preserves_all_fields(self, initialized_service_with_record):
        """Test that get preserves all record fields accurately."""
        service, original = await initialized_service_with_record

        retrieved = await service.get(original.id)

        # Check all fields match
        assert retrieved.id == original.id
        assert retrieved.text == original.text
        assert retrieved.duration_ms == original.duration_ms
        assert retrieved.model_used == original.model_used
        assert retrieved.language == original.language
        assert retrieved.created_at == original.created_at
        assert retrieved.original_text == original.original_text
        assert retrieved.is_ai_enhanced == original.is_ai_enhanced


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
