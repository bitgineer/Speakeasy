"""
Comprehensive tests for the ExportService.

Tests cover:
- TXT export format
- JSON export with/without metadata
- CSV export with/without metadata
- SRT subtitle format and timestamps
- VTT subtitle format and timestamps
- Unified export method for all formats
- Timestamp formatting helpers
"""

import json
from datetime import datetime

import pytest

from speakeasy.services.export import (
    CONTENT_TYPES,
    FILE_EXTENSIONS,
    ExportFormat,
    ExportService,
    _format_timestamp,
)
from speakeasy.services.history import TranscriptionRecord


@pytest.fixture
def export_service() -> ExportService:
    """Provide an ExportService instance."""
    return ExportService()


@pytest.fixture
def single_record() -> TranscriptionRecord:
    """Provide a single TranscriptionRecord for testing."""
    return TranscriptionRecord(
        id="test-uuid-001",
        text="Hello, this is a test transcription.",
        duration_ms=5000,
        model_used="whisper-tiny",
        language="en",
        created_at=datetime(2024, 1, 15, 10, 30, 0),
    )


@pytest.fixture
def multiple_records() -> list[TranscriptionRecord]:
    """Provide multiple TranscriptionRecords for testing."""
    return [
        TranscriptionRecord(
            id="test-uuid-001",
            text="First transcription segment.",
            duration_ms=3000,
            model_used="whisper-tiny",
            language="en",
            created_at=datetime(2024, 1, 15, 10, 30, 0),
        ),
        TranscriptionRecord(
            id="test-uuid-002",
            text="Second transcription segment.",
            duration_ms=4500,
            model_used="whisper-tiny",
            language="en",
            created_at=datetime(2024, 1, 15, 10, 31, 0),
        ),
        TranscriptionRecord(
            id="test-uuid-003",
            text="Third transcription segment.",
            duration_ms=2000,
            model_used="parakeet",
            language="fr",
            created_at=datetime(2024, 1, 15, 10, 32, 0),
        ),
    ]


@pytest.fixture
def empty_records() -> list[TranscriptionRecord]:
    """Provide an empty list of records for edge case testing."""
    return []


class TestTxtExport:
    """Tests for TXT export format."""

    def test_to_txt_single_record(
        self, export_service: ExportService, single_record: TranscriptionRecord
    ):
        """Single record exports with timestamp header and text."""
        result = export_service.to_txt([single_record])

        assert "[2024-01-15 10:30:00]" in result
        assert "Hello, this is a test transcription." in result
        # Should not have trailing newlines
        assert not result.endswith("\n\n")

    def test_to_txt_multiple_records(
        self, export_service: ExportService, multiple_records: list[TranscriptionRecord]
    ):
        """Multiple records separated by blank lines with timestamps."""
        result = export_service.to_txt(multiple_records)

        # All timestamps present
        assert "[2024-01-15 10:30:00]" in result
        assert "[2024-01-15 10:31:00]" in result
        assert "[2024-01-15 10:32:00]" in result

        # All texts present
        assert "First transcription segment." in result
        assert "Second transcription segment." in result
        assert "Third transcription segment." in result

        # Records are separated (blank line between them)
        lines = result.split("\n")
        # Structure: [timestamp], text, blank, [timestamp], text, blank, ...
        assert len(lines) >= 8  # 3 records * 3 lines - 1 trailing blank

    def test_to_txt_empty_list(
        self, export_service: ExportService, empty_records: list[TranscriptionRecord]
    ):
        """Empty list returns empty string."""
        result = export_service.to_txt(empty_records)

        assert result == ""


class TestJsonExport:
    """Tests for JSON export format."""

    def test_to_json_with_metadata(
        self, export_service: ExportService, multiple_records: list[TranscriptionRecord]
    ):
        """JSON with metadata includes all record fields."""
        result = export_service.to_json(multiple_records, include_metadata=True)
        data = json.loads(result)

        assert "exported_at" in data
        assert data["count"] == 3
        assert len(data["transcriptions"]) == 3

        # Check first transcription has all metadata fields
        first = data["transcriptions"][0]
        assert first["id"] == "test-uuid-001"
        assert first["text"] == "First transcription segment."
        assert first["duration_ms"] == 3000
        assert first["model_used"] == "whisper-tiny"
        assert first["language"] == "en"
        assert "created_at" in first

    def test_to_json_without_metadata(
        self, export_service: ExportService, multiple_records: list[TranscriptionRecord]
    ):
        """JSON without metadata includes only id, text, created_at."""
        result = export_service.to_json(multiple_records, include_metadata=False)
        data = json.loads(result)

        assert data["count"] == 3
        assert len(data["transcriptions"]) == 3

        # Check first transcription has limited fields
        first = data["transcriptions"][0]
        assert first["id"] == "test-uuid-001"
        assert first["text"] == "First transcription segment."
        assert "created_at" in first

        # Should NOT have metadata fields
        assert "duration_ms" not in first
        assert "model_used" not in first
        assert "language" not in first

    def test_to_json_empty_list(
        self, export_service: ExportService, empty_records: list[TranscriptionRecord]
    ):
        """Empty list produces valid JSON with count 0."""
        result = export_service.to_json(empty_records, include_metadata=True)
        data = json.loads(result)

        assert data["count"] == 0
        assert data["transcriptions"] == []


class TestCsvExport:
    """Tests for CSV export format."""

    def test_to_csv_with_metadata(
        self, export_service: ExportService, multiple_records: list[TranscriptionRecord]
    ):
        """CSV with metadata includes all columns."""
        result = export_service.to_csv(multiple_records, include_metadata=True)
        lines = result.strip().split("\n")

        # Check header
        header = lines[0]
        assert '"id"' in header
        assert '"text"' in header
        assert '"duration_ms"' in header
        assert '"model_used"' in header
        assert '"language"' in header
        assert '"created_at"' in header

        # Check data rows
        assert len(lines) == 4  # header + 3 records

        # First data row contains expected values
        assert '"test-uuid-001"' in lines[1]
        assert '"First transcription segment."' in lines[1]
        assert '"3000"' in lines[1]
        assert '"whisper-tiny"' in lines[1]
        assert '"en"' in lines[1]

    def test_to_csv_without_metadata(
        self, export_service: ExportService, multiple_records: list[TranscriptionRecord]
    ):
        """CSV without metadata includes only id, text, created_at."""
        result = export_service.to_csv(multiple_records, include_metadata=False)
        lines = result.strip().split("\n")

        # Check header has limited columns
        header = lines[0]
        assert '"id"' in header
        assert '"text"' in header
        assert '"created_at"' in header

        # Should NOT have metadata columns
        assert '"duration_ms"' not in header
        assert '"model_used"' not in header
        assert '"language"' not in header

        # Check data rows
        assert len(lines) == 4  # header + 3 records

    def test_to_csv_empty_list(
        self, export_service: ExportService, empty_records: list[TranscriptionRecord]
    ):
        """Empty list produces CSV with only header."""
        result = export_service.to_csv(empty_records, include_metadata=True)
        lines = result.strip().split("\n")

        # Only header row
        assert len(lines) == 1
        assert '"id"' in lines[0]


class TestSrtExport:
    """Tests for SRT subtitle format."""

    def test_to_srt_format(
        self, export_service: ExportService, multiple_records: list[TranscriptionRecord]
    ):
        """SRT format has correct structure: index, timestamps, text."""
        result = export_service.to_srt(multiple_records)
        blocks = result.strip().split("\n\n")

        assert len(blocks) == 3

        # First block structure
        first_lines = blocks[0].split("\n")
        assert first_lines[0] == "1"  # Index
        assert "-->" in first_lines[1]  # Timestamp line
        assert first_lines[2] == "First transcription segment."  # Text

        # Second block
        second_lines = blocks[1].split("\n")
        assert second_lines[0] == "2"

        # Third block
        third_lines = blocks[2].split("\n")
        assert third_lines[0] == "3"

    def test_to_srt_timestamps(
        self, export_service: ExportService, multiple_records: list[TranscriptionRecord]
    ):
        """SRT timestamps use comma separator and sequential timing."""
        result = export_service.to_srt(multiple_records)
        blocks = result.strip().split("\n\n")

        # First record: 0ms to 3000ms
        first_timestamp = blocks[0].split("\n")[1]
        assert first_timestamp == "00:00:00,000 --> 00:00:03,000"

        # Second record: 3000ms to 7500ms (3000 + 4500)
        second_timestamp = blocks[1].split("\n")[1]
        assert second_timestamp == "00:00:03,000 --> 00:00:07,500"

        # Third record: 7500ms to 9500ms (7500 + 2000)
        third_timestamp = blocks[2].split("\n")[1]
        assert third_timestamp == "00:00:07,500 --> 00:00:09,500"

    def test_to_srt_empty_list(
        self, export_service: ExportService, empty_records: list[TranscriptionRecord]
    ):
        """Empty list returns empty string."""
        result = export_service.to_srt(empty_records)

        assert result == ""


class TestVttExport:
    """Tests for WebVTT subtitle format."""

    def test_to_vtt_format(
        self, export_service: ExportService, multiple_records: list[TranscriptionRecord]
    ):
        """VTT format has WEBVTT header and correct structure."""
        result = export_service.to_vtt(multiple_records)
        lines = result.split("\n")

        # Must start with WEBVTT header
        assert lines[0] == "WEBVTT"
        assert lines[1] == ""  # Blank line after header

        # Check cue structure (timestamp line, text, blank)
        assert "-->" in lines[2]
        assert lines[3] == "First transcription segment."

    def test_to_vtt_timestamps(
        self, export_service: ExportService, multiple_records: list[TranscriptionRecord]
    ):
        """VTT timestamps use period separator and may omit hours."""
        result = export_service.to_vtt(multiple_records)
        lines = result.split("\n")

        # First cue: 0ms to 3000ms (no hours needed)
        assert lines[2] == "00:00.000 --> 00:03.000"

        # Second cue: 3000ms to 7500ms
        assert lines[5] == "00:03.000 --> 00:07.500"

        # Third cue: 7500ms to 9500ms
        assert lines[8] == "00:07.500 --> 00:09.500"

    def test_to_vtt_empty_list(
        self, export_service: ExportService, empty_records: list[TranscriptionRecord]
    ):
        """Empty list returns only WEBVTT header."""
        result = export_service.to_vtt(empty_records)

        assert result == "WEBVTT"


class TestExportAllFormats:
    """Tests for the unified export method."""

    def test_export_all_formats(
        self, export_service: ExportService, single_record: TranscriptionRecord
    ):
        """Export method works for all supported formats."""
        records = [single_record]

        for fmt in ExportFormat:
            content, filename, content_type = export_service.export(records, fmt)

            # Content is non-empty
            assert len(content) > 0

            # Filename has correct extension
            assert filename.endswith(f".{FILE_EXTENSIONS[fmt]}")
            assert filename.startswith("speakeasy_export_")

            # Content type is correct
            assert content_type == CONTENT_TYPES[fmt]

    def test_export_txt_format(
        self, export_service: ExportService, single_record: TranscriptionRecord
    ):
        """Export with TXT format returns correct content type."""
        content, filename, content_type = export_service.export([single_record], ExportFormat.TXT)

        assert content_type == "text/plain"
        assert filename.endswith(".txt")
        assert "Hello, this is a test transcription." in content

    def test_export_json_format(
        self, export_service: ExportService, single_record: TranscriptionRecord
    ):
        """Export with JSON format returns valid JSON."""
        content, filename, content_type = export_service.export([single_record], ExportFormat.JSON)

        assert content_type == "application/json"
        assert filename.endswith(".json")

        # Verify valid JSON
        data = json.loads(content)
        assert data["count"] == 1

    def test_export_csv_format(
        self, export_service: ExportService, single_record: TranscriptionRecord
    ):
        """Export with CSV format returns correct content type."""
        content, filename, content_type = export_service.export([single_record], ExportFormat.CSV)

        assert content_type == "text/csv"
        assert filename.endswith(".csv")

    def test_export_srt_format(
        self, export_service: ExportService, single_record: TranscriptionRecord
    ):
        """Export with SRT format returns correct content type."""
        content, filename, content_type = export_service.export([single_record], ExportFormat.SRT)

        assert content_type == "application/x-subrip"
        assert filename.endswith(".srt")
        assert "-->" in content

    def test_export_vtt_format(
        self, export_service: ExportService, single_record: TranscriptionRecord
    ):
        """Export with VTT format returns correct content type."""
        content, filename, content_type = export_service.export([single_record], ExportFormat.VTT)

        assert content_type == "text/vtt"
        assert filename.endswith(".vtt")
        assert content.startswith("WEBVTT")


class TestFormatTimestamp:
    """Tests for the _format_timestamp helper function."""

    def test_format_timestamp_srt_style(self):
        """SRT style uses comma and always includes hours."""
        # 0 milliseconds
        assert _format_timestamp(0, use_comma=True, always_hours=True) == "00:00:00,000"

        # 1 hour, 23 minutes, 45 seconds, 678 milliseconds
        ms = (1 * 3600 + 23 * 60 + 45) * 1000 + 678
        assert _format_timestamp(ms, use_comma=True, always_hours=True) == "01:23:45,678"

        # Just seconds and milliseconds
        assert _format_timestamp(5123, use_comma=True, always_hours=True) == "00:00:05,123"

    def test_format_timestamp_vtt_style(self):
        """VTT style uses period and may omit hours."""
        # 0 milliseconds (no hours)
        assert _format_timestamp(0, use_comma=False, always_hours=False) == "00:00.000"

        # Under 1 hour - no hours shown
        ms = (23 * 60 + 45) * 1000 + 678
        assert _format_timestamp(ms, use_comma=False, always_hours=False) == "23:45.678"

        # Over 1 hour - hours shown
        ms = (1 * 3600 + 23 * 60 + 45) * 1000 + 678
        assert _format_timestamp(ms, use_comma=False, always_hours=False) == "01:23:45.678"

    def test_format_timestamp_negative_clamped(self):
        """Negative milliseconds are clamped to 0."""
        assert _format_timestamp(-1000, use_comma=True, always_hours=True) == "00:00:00,000"
        assert _format_timestamp(-1, use_comma=False, always_hours=False) == "00:00.000"

    def test_format_timestamp_large_values(self):
        """Large timestamp values are formatted correctly."""
        # 99 hours, 59 minutes, 59 seconds, 999 milliseconds
        ms = (99 * 3600 + 59 * 60 + 59) * 1000 + 999
        assert _format_timestamp(ms, use_comma=True, always_hours=True) == "99:59:59,999"


class TestExportConstants:
    """Tests for export constants."""

    def test_content_types_mapping(self):
        """All formats have content type mappings."""
        for fmt in ExportFormat:
            assert fmt in CONTENT_TYPES
            assert isinstance(CONTENT_TYPES[fmt], str)
            assert "/" in CONTENT_TYPES[fmt]  # Valid MIME type format

    def test_file_extensions_mapping(self):
        """All formats have file extension mappings."""
        for fmt in ExportFormat:
            assert fmt in FILE_EXTENSIONS
            assert isinstance(FILE_EXTENSIONS[fmt], str)
            assert FILE_EXTENSIONS[fmt] == fmt.value  # Extension matches enum value
