"""Performance benchmark tests for critical backend operations."""

import asyncio
import time
from datetime import datetime

import pytest


class TestHistoryPerformance:
    """Performance benchmarks for HistoryService operations."""

    @pytest.fixture
    async def history_service(self, tmp_path):
        """Provide an initialized HistoryService with temporary database."""
        from speakeasy.services.history import HistoryService

        db_path = tmp_path / "perf_test.db"
        service = HistoryService(db_path)
        await service.initialize()
        yield service
        await service.close()

    @pytest.mark.asyncio
    async def test_history_add_performance(self, history_service):
        """Add operation completes in under 50ms."""
        start = time.perf_counter()
        await history_service.add(
            text="Test transcription for performance measurement",
            duration_ms=1500,
            model_used="test-model",
            language="en",
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 50, f"Add took {elapsed_ms:.2f}ms, expected < 50ms"

    @pytest.mark.asyncio
    async def test_history_list_performance(self, history_service):
        """List 100 records completes in under 100ms."""
        for i in range(100):
            await history_service.add(
                text=f"Performance test transcription number {i}",
                duration_ms=1000 + i,
                model_used="test-model",
                language="en",
            )

        start = time.perf_counter()
        records, total = await history_service.list(limit=100)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert len(records) == 100
        assert total == 100
        assert elapsed_ms < 100, f"List took {elapsed_ms:.2f}ms, expected < 100ms"

    @pytest.mark.asyncio
    async def test_history_search_performance(self, history_service):
        """FTS5 search on 100 records completes in under 100ms."""
        for i in range(100):
            word = ["alpha", "beta", "gamma", "delta"][i % 4]
            await history_service.add(
                text=f"Searchable {word} text number {i}",
                duration_ms=1000,
                model_used="test-model",
                language="en",
            )

        start = time.perf_counter()
        records, total = await history_service.list(search="gamma")
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert len(records) > 0
        assert elapsed_ms < 100, f"Search took {elapsed_ms:.2f}ms, expected < 100ms"


class TestSettingsPerformance:
    """Performance benchmarks for SettingsService operations."""

    def test_settings_load_performance(self, tmp_path):
        """Settings load completes in under 20ms."""
        from speakeasy.services.settings import SettingsService

        settings_path = tmp_path / "settings.json"
        service = SettingsService(settings_path)

        start = time.perf_counter()
        service.load()
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 20, f"Load took {elapsed_ms:.2f}ms, expected < 20ms"

    def test_settings_save_performance(self, tmp_path):
        """Settings save completes in under 20ms."""
        from speakeasy.services.settings import SettingsService

        settings_path = tmp_path / "settings.json"
        service = SettingsService(settings_path)
        service.load()

        start = time.perf_counter()
        service.save()
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 20, f"Save took {elapsed_ms:.2f}ms, expected < 20ms"


class TestSerializationPerformance:
    """Performance benchmarks for data serialization."""

    def test_transcription_record_to_dict_performance(self):
        """TranscriptionRecord.to_dict() completes in under 1ms."""
        from speakeasy.services.history import TranscriptionRecord

        record = TranscriptionRecord(
            id="perf-test-id",
            text="This is a test transcription for performance measurement",
            duration_ms=2500,
            model_used="whisper-large-v3",
            language="en",
            created_at=datetime.utcnow(),
        )

        iterations = 1000
        start = time.perf_counter()
        for _ in range(iterations):
            record.to_dict()
        total_ms = (time.perf_counter() - start) * 1000
        per_call_ms = total_ms / iterations

        assert per_call_ms < 1, f"to_dict took {per_call_ms:.4f}ms avg, expected < 1ms"

    def test_app_settings_model_dump_performance(self):
        """AppSettings.model_dump() completes in under 1ms."""
        from speakeasy.services.settings import AppSettings

        settings = AppSettings()

        iterations = 1000
        start = time.perf_counter()
        for _ in range(iterations):
            settings.model_dump()
        total_ms = (time.perf_counter() - start) * 1000
        per_call_ms = total_ms / iterations

        assert per_call_ms < 1, f"model_dump took {per_call_ms:.4f}ms avg, expected < 1ms"


class TestConcurrencyPerformance:
    """Performance benchmarks for concurrent operations."""

    @pytest.fixture
    async def history_service(self, tmp_path):
        """Provide an initialized HistoryService with temporary database."""
        from speakeasy.services.history import HistoryService

        db_path = tmp_path / "concurrent_test.db"
        service = HistoryService(db_path)
        await service.initialize()
        yield service
        await service.close()

    @pytest.mark.asyncio
    async def test_concurrent_history_adds(self, history_service):
        """10 concurrent add operations complete in under 500ms."""

        async def add_record(index: int):
            await history_service.add(
                text=f"Concurrent test record {index}",
                duration_ms=1000,
                model_used="test-model",
                language="en",
            )

        start = time.perf_counter()
        await asyncio.gather(*[add_record(i) for i in range(10)])
        elapsed_ms = (time.perf_counter() - start) * 1000

        _, total = await history_service.list(limit=20)
        assert total == 10
        assert elapsed_ms < 500, f"Concurrent adds took {elapsed_ms:.2f}ms, expected < 500ms"
