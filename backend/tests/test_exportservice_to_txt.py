"""
Test for ExportService.to_txt
Comprehensive test suite for exporting to text format.
"""

import pytest
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.services.export import ExportService
from speakeasy.services.history import TranscriptionRecord


class TestExportServiceToTxt:
    """Tests for ExportService.to_txt"""

    @pytest.fixture
    def sample_records(self):
        """Create sample transcription records."""
        return [
            TranscriptionRecord(
                id="test-1",
                text="Hello world",
                duration_ms=5000,
                model_used="whisper-small",
                language="en",
                created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            ),
            TranscriptionRecord(
                id="test-2",
                text="This is another transcription",
                duration_ms=8000,
                model_used="parakeet",
                language="en",
                created_at=datetime(2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc),
            ),
        ]

    def test_to_txt_basic(self, sample_records):
        """Test basic text export."""
        service = ExportService()

        result = service.to_txt(sample_records)

        assert "Hello world" in result
        assert "This is another transcription" in result
        assert "[2024-01-15" in result  # Timestamp

    def test_to_txt_format(self, sample_records):
        """Test text export format."""
        service = ExportService()

        result = service.to_txt(sample_records)

        lines = result.split("\n")

        # Check format: [timestamp] followed by text
        assert any("[2024-01-15 10:30:00]" in line for line in lines)
        assert any("[2024-01-15 11:00:00]" in line for line in lines)

    def test_to_txt_empty_records(self):
        """Test export with empty records list."""
        service = ExportService()

        result = service.to_txt([])

        assert result == ""

    def test_to_txt_single_record(self, sample_records):
        """Test export with single record."""
        service = ExportService()

        result = service.to_txt([sample_records[0]])

        assert "Hello world" in result
        assert "[2024-01-15 10:30:00]" in result
        # No trailing newline
        assert not result.endswith("\n\n")

    def test_to_txt_multiline_text(self):
        """Test export with multiline text."""
        service = ExportService()

        record = TranscriptionRecord(
            id="test-1",
            text="Line 1\nLine 2\nLine 3",
            duration_ms=5000,
            model_used="whisper",
            language="en",
            created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        )

        result = service.to_txt([record])

        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result

    def test_to_txt_special_characters(self):
        """Test export with special characters."""
        service = ExportService()

        record = TranscriptionRecord(
            id="test-1",
            text="Hello! ¿Cómo estás? 你好 🎉",
            duration_ms=5000,
            model_used="whisper",
            language="en",
            created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        )

        result = service.to_txt([record])

        assert "Hello! ¿Cómo estás? 你好 🎉" in result

    def test_to_txt_long_text(self):
        """Test export with very long text."""
        service = ExportService()

        long_text = "This is a test. " * 1000

        record = TranscriptionRecord(
            id="test-1",
            text=long_text,
            duration_ms=60000,
            model_used="whisper",
            language="en",
            created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        )

        result = service.to_txt([record])

        assert long_text in result

    def test_to_txt_timezone_handling(self):
        """Test export with different timezones."""
        service = ExportService()

        from datetime import timedelta

        record = TranscriptionRecord(
            id="test-1",
            text="Test",
            duration_ms=5000,
            model_used="whisper",
            language="en",
            created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone(timedelta(hours=2))),
        )

        result = service.to_txt([record])

        # Should include timezone offset in timestamp
        assert "2024-01-15" in result

    def test_to_txt_record_separator(self, sample_records):
        """Test that records are separated by blank lines."""
        service = ExportService()

        result = service.to_txt(sample_records)

        # Should have blank lines between records
        assert "\n\n" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
