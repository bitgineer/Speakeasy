"""
Test for HistoryService.add
Comprehensive test suite covering adding transcriptions to history.
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
async def initialized_service():
    """Create and initialize a HistoryService for testing."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_history.db"
    service = HistoryService(db_path=db_path)

    await service.initialize()

    yield service

    # Cleanup
    await service.close()
    if db_path.exists():
        db_path.unlink()
    if temp_dir:
        os.rmdir(temp_dir)


class TestHistoryServiceAdd:
    """Tests for HistoryService.add"""

    @pytest.mark.asyncio
    async def test_add_basic_record(self, initialized_service):
        """Test adding a basic transcription record."""
        service = await initialized_service

        record = await service.add(
            text="Hello world",
            duration_ms=5000,
            model_used="whisper-small",
            language="en",
        )

        assert record.text == "Hello world"
        assert record.duration_ms == 5000
        assert record.model_used == "whisper-small"
        assert record.language == "en"
        assert record.id is not None
        assert record.created_at is not None

    @pytest.mark.asyncio
    async def test_add_with_original_text(self, initialized_service):
        """Test adding a record with original text (grammar corrected)."""
        service = await initialized_service

        record = await service.add(
            text="Hello world",
            duration_ms=5000,
            model_used="whisper-small",
            language="en",
            original_text="hello wrld",
        )

        assert record.original_text == "hello wrld"
        assert record.is_ai_enhanced is True

    @pytest.mark.asyncio
    async def test_add_without_optional_fields(self, initialized_service):
        """Test adding a record without optional fields."""
        service = await initialized_service

        record = await service.add(
            text="Test transcription",
            duration_ms=3000,
        )

        assert record.text == "Test transcription"
        assert record.duration_ms == 3000
        assert record.model_used is None
        assert record.language is None
        assert record.original_text is None
        assert record.is_ai_enhanced is False

    @pytest.mark.asyncio
    async def test_add_generates_unique_ids(self, initialized_service):
        """Test that adding multiple records generates unique IDs."""
        service = await initialized_service

        record1 = await service.add(text="First", duration_ms=1000)
        record2 = await service.add(text="Second", duration_ms=2000)

        assert record1.id != record2.id

    @pytest.mark.asyncio
    async def test_add_sets_timestamp(self, initialized_service):
        """Test that adding a record sets the created_at timestamp."""
        service = await initialized_service

        before = datetime.now(timezone.utc)
        record = await service.add(text="Test", duration_ms=1000)
        after = datetime.now(timezone.utc)

        assert before <= record.created_at <= after

    @pytest.mark.asyncio
    async def test_add_with_special_characters(self, initialized_service):
        """Test adding text with special characters and unicode."""
        service = await initialized_service

        special_text = "Hello! ¿Cómo estás? 你好世界 🎉 \\n \\t"

        record = await service.add(text=special_text, duration_ms=5000)

        assert record.text == special_text

    @pytest.mark.asyncio
    async def test_add_empty_text(self, initialized_service):
        """Test adding an empty transcription."""
        service = await initialized_service

        record = await service.add(text="", duration_ms=0)

        assert record.text == ""
        assert record.duration_ms == 0

    @pytest.mark.asyncio
    async def test_add_long_text(self, initialized_service):
        """Test adding a very long transcription."""
        service = await initialized_service

        long_text = "This is a test. " * 1000

        record = await service.add(text=long_text, duration_ms=60000)

        assert record.text == long_text
        assert len(record.text) > 10000

    @pytest.mark.asyncio
    async def test_add_negative_duration(self, initialized_service):
        """Test adding a record with negative duration."""
        service = await initialized_service

        record = await service.add(text="Test", duration_ms=-1000)

        assert record.duration_ms == -1000

    @pytest.mark.asyncio
    async def test_add_zero_duration(self, initialized_service):
        """Test adding a record with zero duration."""
        service = await initialized_service

        record = await service.add(text="Test", duration_ms=0)

        assert record.duration_ms == 0

    @pytest.mark.asyncio
    async def test_add_persists_to_database(self, initialized_service):
        """Test that added records are persisted to the database."""
        service = await initialized_service

        record = await service.add(
            text="Persisted record",
            duration_ms=3000,
            model_used="test-model",
        )

        # Retrieve the record from database
        retrieved = await service.get(record.id)

        assert retrieved is not None
        assert retrieved.text == "Persisted record"
        assert retrieved.duration_ms == 3000
        assert retrieved.model_used == "test-model"

    @pytest.mark.asyncio
    async def test_add_fails_when_not_initialized(self, temp_db_path):
        """Test that add fails when database is not initialized."""
        service = HistoryService(db_path=temp_db_path)

        with pytest.raises(RuntimeError, match="Database not initialized"):
            await service.add(text="Test", duration_ms=1000)

    @pytest.mark.asyncio
    async def test_add_large_batch(self, initialized_service):
        """Test adding multiple records efficiently."""
        service = await initialized_service

        records = []
        for i in range(50):
            record = await service.add(
                text=f"Record {i}",
                duration_ms=i * 1000,
                model_used="test-model",
            )
            records.append(record)

        # Verify all records exist
        all_records = await service.list(limit=100)

        assert len(all_records[0]) == 50

    @pytest.mark.asyncio
    async def test_add_multiline_text(self, initialized_service):
        """Test adding text with newlines."""
        service = await initialized_service

        multiline_text = """Line 1
Line 2
Line 3"""

        record = await service.add(text=multiline_text, duration_ms=5000)

        assert record.text == multiline_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
