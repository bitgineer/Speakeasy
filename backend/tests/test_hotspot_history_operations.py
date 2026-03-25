"""
Hotspot tests for history.py add() method - CRITICAL (24 callers)

Tests the HistoryService.add() method which is called for EVERY transcription save.
This is a critical persistence function - failures here mean lost transcriptions.

Blast Radius:
- 24 direct callers
- Used in every recording completion
- Affects data persistence across entire application
- Database operations with potential for data loss

Coverage Targets:
- Basic add functionality
- Field validation
- Database error handling
- Concurrent access
- Data integrity
- Edge cases (empty text, long text, special characters)
"""

import asyncio
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from speakeasy.services.history import HistoryService, TranscriptionRecord, encode_cursor


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_db_path():
    """Create temporary database file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_history.db"
        yield db_path


@pytest.fixture
async def history_service(temp_db_path):
    """Create history service with temp database."""
    service = HistoryService(db_path=str(temp_db_path))
    await service.initialize()
    yield service
    await service.cleanup()


@pytest.fixture
def mock_db_connection():
    """Create mock database connection for unit tests."""
    mock_conn = AsyncMock()
    mock_cursor = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=mock_cursor)
    mock_conn.commit = AsyncMock()
    mock_conn.close = AsyncMock()
    return mock_conn


# =============================================================================
# Basic Add Tests
# =============================================================================


class TestAddBasic:
    """Basic add() functionality tests."""

    @pytest.mark.asyncio
    async def test_add_minimal_fields(self, history_service):
        """Add with only required fields succeeds."""
        record = await history_service.add(
            text="Test transcription",
            duration_ms=1000,
        )

        assert isinstance(record, TranscriptionRecord)
        assert record.text == "Test transcription"
        assert record.duration_ms == 1000
        assert record.id is not None
        assert record.created_at is not None

    @pytest.mark.asyncio
    async def test_add_all_fields(self, history_service):
        """Add with all fields succeeds."""
        record = await history_service.add(
            text="Test transcription",
            duration_ms=1500,
            model_used="whisper-tiny",
            language="en",
            original_text="Original text",
        )

        assert record.text == "Test transcription"
        assert record.duration_ms == 1500
        assert record.model_used == "whisper-tiny"
        assert record.language == "en"
        assert record.original_text == "Original text"
        assert record.id is not None

    @pytest.mark.asyncio
    async def test_add_generates_unique_id(self, history_service):
        """Each add generates unique ID."""
        record1 = await history_service.add(text="Test 1", duration_ms=1000)
        record2 = await history_service.add(text="Test 2", duration_ms=1000)

        assert record1.id != record2.id

    @pytest.mark.asyncio
    async def test_add_sets_timestamp(self, history_service):
        """Add sets created_at timestamp."""
        before = datetime.now(timezone.utc)
        record = await history_service.add(text="Test", duration_ms=1000)
        after = datetime.now(timezone.utc)

        assert before <= record.created_at <= after
        assert record.created_at.tzinfo is not None  # Has timezone

    @pytest.mark.asyncio
    async def test_add_returns_record(self, history_service):
        """Add returns the created record."""
        record = await history_service.add(
            text="Test",
            duration_ms=1000,
            model_used="test-model",
        )

        # Verify we can retrieve it
        retrieved = await history_service.get(record.id)
        assert retrieved is not None
        assert retrieved.id == record.id
        assert retrieved.text == record.text


# =============================================================================
# Field Validation Tests
# =============================================================================


class TestAddValidation:
    """Field validation tests for add()."""

    @pytest.mark.asyncio
    async def test_add_empty_text(self, history_service):
        """Add with empty text succeeds (edge case)."""
        record = await history_service.add(text="", duration_ms=1000)
        assert record.text == ""

    @pytest.mark.asyncio
    async def test_add_whitespace_text(self, history_service):
        """Add with whitespace-only text succeeds."""
        record = await history_service.add(text="   ", duration_ms=1000)
        assert record.text == "   "

    @pytest.mark.asyncio
    async def test_add_very_long_text(self, history_service):
        """Add with very long text succeeds."""
        long_text = "test " * 10000  # 50k characters
        record = await history_service.add(text=long_text, duration_ms=1000)
        assert record.text == long_text
        assert len(record.text) == 50000

    @pytest.mark.asyncio
    async def test_add_unicode_text(self, history_service):
        """Add with unicode text succeeds."""
        text = "Hello 世界 مرحبا שלום"
        record = await history_service.add(text=text, duration_ms=1000)
        assert record.text == text

    @pytest.mark.asyncio
    async def test_add_emoji_text(self, history_service):
        """Add with emoji succeeds."""
        text = "Test 👍 transcription 🎉 with emoji ✅"
        record = await history_service.add(text=text, duration_ms=1000)
        assert record.text == text

    @pytest.mark.asyncio
    async def test_add_special_characters(self, history_service):
        """Add with special characters succeeds."""
        text = "Test @#$%^&*()_+-=[]{}|;':\",./<>? characters"
        record = await history_service.add(text=text, duration_ms=1000)
        assert record.text == text

    @pytest.mark.asyncio
    async def test_add_newlines_preserved(self, history_service):
        """Add with newlines preserves them."""
        text = "Line 1\nLine 2\nLine 3"
        record = await history_service.add(text=text, duration_ms=1000)
        assert record.text == text

    @pytest.mark.asyncio
    async def test_add_null_optional_fields(self, history_service):
        """Add with null optional fields succeeds."""
        record = await history_service.add(
            text="Test",
            duration_ms=1000,
            model_used=None,
            language=None,
            original_text=None,
        )

        assert record.model_used is None
        assert record.language is None
        assert record.original_text is None


# =============================================================================
# Database Error Handling Tests
# =============================================================================


class TestAddErrorHandling:
    """Database error handling tests for add()."""

    @pytest.mark.asyncio
    async def test_add_without_initialization(self, temp_db_path):
        """Add before initialization raises RuntimeError."""
        service = HistoryService(db_path=str(temp_db_path))
        # Don't initialize

        with pytest.raises(RuntimeError, match="Database not initialized"):
            await service.add(text="Test", duration_ms=1000)

    @pytest.mark.asyncio
    async def test_add_database_commit_failure(self, temp_db_path):
        """Handle database commit failure."""
        service = HistoryService(db_path=str(temp_db_path))
        await service.initialize()

        # Mock commit to fail
        with patch.object(service._db, "commit", side_effect=Exception("Commit failed")):
            with pytest.raises(Exception, match="Commit failed"):
                await service.add(text="Test", duration_ms=1000)

    @pytest.mark.asyncio
    async def test_add_database_insert_failure(self, temp_db_path):
        """Handle database insert failure."""
        service = HistoryService(db_path=str(temp_db_path))
        await service.initialize()

        # Mock execute to fail on INSERT
        original_execute = service._db.execute

        async def mock_execute(query, *args):
            if "INSERT" in query:
                raise sqlite3.Error("Insert failed")
            return await original_execute(query, *args)

        with patch.object(service._db, "execute", side_effect=mock_execute):
            with pytest.raises(sqlite3.Error):
                await service.add(text="Test", duration_ms=1000)

    @pytest.mark.asyncio
    async def test_add_rollback_on_failure(self, temp_db_path):
        """Verify rollback happens on failure."""
        service = HistoryService(db_path=str(temp_db_path))
        await service.initialize()

        # Count records before
        before_count = len(await service.get_entries())

        # Mock to fail after insert but before commit
        with patch.object(service._db, "commit", side_effect=Exception("Commit failed")):
            with pytest.raises(Exception):
                await service.add(text="Test", duration_ms=1000)

        # Count records after - should be same as before (rolled back)
        after_count = len(await service.get_entries())
        assert after_count == before_count


# =============================================================================
# Concurrent Access Tests
# =============================================================================


class TestAddConcurrency:
    """Concurrent access tests for add()."""

    @pytest.mark.asyncio
    async def test_add_concurrent_operations(self, history_service):
        """Multiple concurrent adds succeed."""

        async def add_task(i):
            return await history_service.add(
                text=f"Test {i}",
                duration_ms=1000,
                model_used="test",
            )

        # Run 10 concurrent adds
        tasks = [add_task(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert len(results) == 10
        assert all(isinstance(r, TranscriptionRecord) for r in results)

        # All should have unique IDs
        ids = [r.id for r in results]
        assert len(set(ids)) == 10

    @pytest.mark.asyncio
    async def test_add_rapid_sequential(self, history_service):
        """Rapid sequential adds succeed."""
        records = []
        for i in range(100):
            record = await history_service.add(
                text=f"Test {i}",
                duration_ms=1000,
            )
            records.append(record)

        assert len(records) == 100
        assert all(r.id is not None for r in records)

        # Verify all were saved
        entries = await history_service.get_entries()
        assert len(entries) == 100

    @pytest.mark.asyncio
    async def test_add_mixed_operations(self, history_service):
        """Mixed add/get/delete operations succeed."""
        # Add 5 records
        records = []
        for i in range(5):
            record = await history_service.add(
                text=f"Test {i}",
                duration_ms=1000,
            )
            records.append(record)

        # Get all
        entries = await history_service.get_entries()
        assert len(entries) == 5

        # Delete first
        await history_service.delete(records[0].id)

        # Add another
        new_record = await history_service.add(
            text="New test",
            duration_ms=1000,
        )

        # Verify final state
        entries = await history_service.get_entries()
        assert len(entries) == 5
        assert any(e.id == new_record.id for e in entries)


# =============================================================================
# Data Integrity Tests
# =============================================================================


class TestAddDataIntegrity:
    """Data integrity tests for add()."""

    @pytest.mark.asyncio
    async def test_add_preserves_exact_text(self, history_service):
        """Add preserves exact text without modification."""
        original = "Test with exact   spacing and CAPS and punctuation!"
        record = await history_service.add(text=original, duration_ms=1000)

        # Retrieve from database
        retrieved = await history_service.get(record.id)
        assert retrieved is not None
        assert retrieved.text == original

    @pytest.mark.asyncio
    async def test_add_preserves_duration_accuracy(self, history_service):
        """Add preserves duration accurately."""
        durations = [1, 100, 1000, 10000, 999999]
        for duration in durations:
            record = await history_service.add(
                text=f"Test {duration}",
                duration_ms=duration,
            )
            assert record.duration_ms == duration

    @pytest.mark.asyncio
    async def test_add_preserves_model_name(self, history_service):
        """Add preserves model name exactly."""
        model_names = [
            "whisper-tiny",
            "whisper-base",
            "nvidia/parakeet-tdt-0.6b-v3",
            "custom_model_v1.2.3",
            "Model With Spaces",
        ]

        for model_name in model_names:
            record = await history_service.add(
                text="Test",
                duration_ms=1000,
                model_used=model_name,
            )
            assert record.model_used == model_name

    @pytest.mark.asyncio
    async def test_add_preserves_language_code(self, history_service):
        """Add preserves language code exactly."""
        languages = ["en", "es", "fr", "de", "zh", "ja", "ar", "hi"]

        for lang in languages:
            record = await history_service.add(
                text="Test",
                duration_ms=1000,
                language=lang,
            )
            assert record.language == lang

    @pytest.mark.asyncio
    async def test_add_original_text_field(self, history_service):
        """Add preserves original_text for AI enhancement tracking."""
        original = "um like uh test"
        corrected = "Test"

        record = await history_service.add(
            text=corrected,
            duration_ms=1000,
            original_text=original,
        )

        assert record.original_text == original
        assert record.text == corrected
        assert record.is_ai_enhanced is True

    @pytest.mark.asyncio
    async def test_add_without_original_text(self, history_service):
        """Add without original_text marks as not enhanced."""
        record = await history_service.add(
            text="Test",
            duration_ms=1000,
        )

        assert record.original_text is None
        assert record.is_ai_enhanced is False


# =============================================================================
# Cursor Encoding Tests
# =============================================================================


class TestAddWithCursor:
    """Tests for cursor-based pagination with add()."""

    @pytest.mark.asyncio
    async def test_add_generates_cursor_compatible_record(self, history_service):
        """Added record can be used with cursor encoding."""
        record = await history_service.add(
            text="Test",
            duration_ms=1000,
        )

        # Should be able to encode cursor
        cursor = encode_cursor(record.created_at, record.id)
        assert cursor is not None
        assert len(cursor) > 0

    @pytest.mark.asyncio
    async def test_add_multiple_with_pagination(self, history_service):
        """Multiple adds work with pagination."""
        # Add 50 records
        for i in range(50):
            await history_service.add(
                text=f"Test {i}",
                duration_ms=1000,
            )

        # Get first page
        page1 = await history_service.get_entries(limit=10)
        assert len(page1) == 10

        # Get cursor for next page
        if page1:
            last_record = page1[-1]
            cursor = encode_cursor(last_record.created_at, last_record.id)

            # Get next page
            page2 = await history_service.get_entries(limit=10, after=cursor)
            assert len(page2) == 10

            # No overlap
            page1_ids = {r.id for r in page1}
            page2_ids = {r.id for r in page2}
            assert page1_ids.isdisjoint(page2_ids)


# =============================================================================
# Performance Tests
# =============================================================================


class TestAddPerformance:
    """Performance tests for add() (called 24 times in various flows)."""

    @pytest.mark.asyncio
    async def test_add_speed_single(self, history_service):
        """Single add is fast."""
        import time

        start = time.perf_counter()
        await history_service.add(text="Test", duration_ms=1000)
        elapsed = time.perf_counter() - start

        # Should complete in < 10ms
        assert elapsed < 0.01, f"Too slow: {elapsed:.3f}s"

    @pytest.mark.asyncio
    async def test_add_speed_batch(self, history_service):
        """Batch adds are reasonably fast."""
        import time

        start = time.perf_counter()
        for i in range(100):
            await history_service.add(
                text=f"Test {i}",
                duration_ms=1000,
            )
        elapsed = time.perf_counter() - start

        # 100 adds should complete in < 1 second
        assert elapsed < 1.0, f"Too slow: {elapsed:.3f}s for 100 adds"

    @pytest.mark.asyncio
    async def test_add_memory_efficiency(self, history_service):
        """Add doesn't leak memory."""
        import gc
        import tracemalloc

        tracemalloc.start()

        # Add 1000 records
        for i in range(1000):
            await history_service.add(
                text=f"Test {i}",
                duration_ms=1000,
            )

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Peak memory should be reasonable (< 50MB for this test)
        assert peak < 50 * 1024 * 1024, f"Too much memory: {peak / 1024 / 1024:.2f}MB"

        # Force cleanup
        gc.collect()


# =============================================================================
# Integration-like Scenarios
# =============================================================================


class TestAddIntegrationScenarios:
    """Integration-like scenarios testing real usage patterns."""

    @pytest.mark.asyncio
    async def test_add_recording_completion_flow(self, history_service):
        """Simulate add being called when recording completes."""
        # Simulate a recording completion
        transcription_text = "This is the transcribed audio from the recording"
        duration_ms = 5432
        model_used = "whisper-base"
        language = "en"

        # This is what happens in the real flow
        record = await history_service.add(
            text=transcription_text,
            duration_ms=duration_ms,
            model_used=model_used,
            language=language,
        )

        # Verify record created
        assert record is not None
        assert record.text == transcription_text

        # Verify can be retrieved (simulating history page load)
        retrieved = await history_service.get(record.id)
        assert retrieved is not None
        assert retrieved.text == transcription_text

    @pytest.mark.asyncio
    async def test_add_batch_transcription_flow(self, history_service):
        """Simulate add being called for batch transcription."""
        # Simulate batch processing multiple files
        files = [
            ("file1.wav", "First file transcription", 3000),
            ("file2.wav", "Second file transcription", 4500),
            ("file3.wav", "Third file transcription", 2800),
        ]

        records = []
        for filename, text, duration in files:
            record = await history_service.add(
                text=text,
                duration_ms=duration,
                model_used="batch-model",
            )
            records.append(record)

        # All should be saved
        assert len(records) == 3
        entries = await history_service.get_entries()
        assert len(entries) == 3

    @pytest.mark.asyncio
    async def test_add_with_ai_enhancement_flow(self, history_service):
        """Simulate add with AI grammar correction."""
        original_text = "um like uh this is a test you know"
        corrected_text = "This is a test"

        # Add with both original and corrected
        record = await history_service.add(
            text=corrected_text,
            duration_ms=1000,
            original_text=original_text,
        )

        # Verify both preserved
        assert record.text == corrected_text
        assert record.original_text == original_text
        assert record.is_ai_enhanced is True

        # Verify can retrieve both
        retrieved = await history_service.get(record.id)
        assert retrieved is not None
        assert retrieved.text == corrected_text
        assert retrieved.original_text == original_text

    @pytest.mark.asyncio
    async def test_add_high_volume_scenario(self, history_service):
        """Simulate high-volume usage (power user)."""
        # Simulate a power user creating 500 transcriptions
        for i in range(500):
            await history_service.add(
                text=f"Transcription {i} with some text content",
                duration_ms=1000 + (i % 1000),
                model_used=["whisper-tiny", "whisper-base", "parakeet"][i % 3],
                language=["en", "es", "fr"][i % 3],
            )

        # Verify all saved
        entries = await history_service.get_entries()
        assert len(entries) == 500

        # Verify can paginate through all
        all_records = []
        cursor = None
        while True:
            page = await history_service.get_entries(limit=50, after=cursor)
            if not page:
                break
            all_records.extend(page)
            if page:
                last = page[-1]
                cursor = encode_cursor(last.created_at, last.id)

        assert len(all_records) == 500
