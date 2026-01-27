"""
Export service for exporting transcription records in various formats.

Supports: TXT, JSON, CSV, SRT, VTT
"""

import csv
import io
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from .history import TranscriptionRecord


class ExportFormat(str, Enum):
    """Supported export formats."""

    TXT = "txt"
    JSON = "json"
    CSV = "csv"
    SRT = "srt"
    VTT = "vtt"


# Content type mappings
CONTENT_TYPES = {
    ExportFormat.TXT: "text/plain",
    ExportFormat.JSON: "application/json",
    ExportFormat.CSV: "text/csv",
    ExportFormat.SRT: "application/x-subrip",
    ExportFormat.VTT: "text/vtt",
}

# File extensions
FILE_EXTENSIONS = {
    ExportFormat.TXT: "txt",
    ExportFormat.JSON: "json",
    ExportFormat.CSV: "csv",
    ExportFormat.SRT: "srt",
    ExportFormat.VTT: "vtt",
}


def _format_timestamp(
    ms: int,
    use_comma: bool = False,
    always_hours: bool = True,
) -> str:
    """
    Format milliseconds as timestamp for SRT/VTT.

    Args:
        ms: Milliseconds to format
        use_comma: Use comma for decimal separator (SRT) vs period (VTT)
        always_hours: Always include hours (SRT) vs optional (VTT)

    Returns:
        Formatted timestamp string
    """
    if ms < 0:
        ms = 0

    hours = ms // 3600000
    ms %= 3600000
    minutes = ms // 60000
    ms %= 60000
    seconds = ms // 1000
    milliseconds = ms % 1000

    decimal_sep = "," if use_comma else "."

    if always_hours or hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}{decimal_sep}{milliseconds:03d}"
    else:
        return f"{minutes:02d}:{seconds:02d}{decimal_sep}{milliseconds:03d}"


class ExportService:
    """
    Service for exporting transcription records to various formats.
    """

    def to_txt(self, records: list[TranscriptionRecord]) -> str:
        """
        Export records to plain text format.

        Each record is separated by a blank line with timestamp header.
        """
        lines = []
        for record in records:
            timestamp = record.created_at.strftime("%Y-%m-%d %H:%M:%S")
            lines.append(f"[{timestamp}]")
            lines.append(record.text)
            lines.append("")  # Blank line separator

        return "\n".join(lines).rstrip()

    def to_json(
        self,
        records: list[TranscriptionRecord],
        include_metadata: bool = True,
    ) -> str:
        """
        Export records to JSON format.

        Args:
            records: List of transcription records
            include_metadata: Include full metadata or just text
        """
        if include_metadata:
            data = {
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "count": len(records),
                "transcriptions": [record.to_dict() for record in records],
            }
        else:
            data = {
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "count": len(records),
                "transcriptions": [
                    {
                        "id": record.id,
                        "text": record.text,
                        "created_at": record.created_at.isoformat(),
                    }
                    for record in records
                ],
            }

        return json.dumps(data, indent=2, ensure_ascii=False)

    def to_csv(
        self,
        records: list[TranscriptionRecord],
        include_metadata: bool = True,
    ) -> str:
        """
        Export records to CSV format.

        Args:
            records: List of transcription records
            include_metadata: Include full metadata columns
        """
        output = io.StringIO()

        if include_metadata:
            fieldnames = ["id", "text", "duration_ms", "model_used", "language", "created_at"]
        else:
            fieldnames = ["id", "text", "created_at"]

        writer = csv.DictWriter(output, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()

        for record in records:
            if include_metadata:
                writer.writerow(
                    {
                        "id": record.id,
                        "text": record.text,
                        "duration_ms": record.duration_ms,
                        "model_used": record.model_used or "",
                        "language": record.language or "",
                        "created_at": record.created_at.isoformat(),
                    }
                )
            else:
                writer.writerow(
                    {
                        "id": record.id,
                        "text": record.text,
                        "created_at": record.created_at.isoformat(),
                    }
                )

        return output.getvalue()

    def to_srt(self, records: list[TranscriptionRecord]) -> str:
        """
        Export records to SRT (SubRip) subtitle format.

        Format:
        1
        00:00:00,000 --> 00:00:05,123
        First transcription text

        Uses sequential numbering and calculates timestamps from duration_ms.
        """
        lines = []
        current_time_ms = 0

        for index, record in enumerate(records, start=1):
            start_time = _format_timestamp(current_time_ms, use_comma=True, always_hours=True)
            end_time_ms = current_time_ms + record.duration_ms
            end_time = _format_timestamp(end_time_ms, use_comma=True, always_hours=True)

            lines.append(str(index))
            lines.append(f"{start_time} --> {end_time}")
            lines.append(record.text)
            lines.append("")  # Blank line separator

            current_time_ms = end_time_ms

        return "\n".join(lines).rstrip()

    def to_vtt(self, records: list[TranscriptionRecord]) -> str:
        """
        Export records to WebVTT subtitle format.

        Format:
        WEBVTT

        00:00.000 --> 00:05.123
        First transcription text
        """
        lines = ["WEBVTT", ""]  # Header and blank line
        current_time_ms = 0

        for record in records:
            start_time = _format_timestamp(current_time_ms, use_comma=False, always_hours=False)
            end_time_ms = current_time_ms + record.duration_ms
            end_time = _format_timestamp(end_time_ms, use_comma=False, always_hours=False)

            lines.append(f"{start_time} --> {end_time}")
            lines.append(record.text)
            lines.append("")  # Blank line separator

            current_time_ms = end_time_ms

        return "\n".join(lines).rstrip()

    def export(
        self,
        records: list[TranscriptionRecord],
        format: ExportFormat,
        include_metadata: bool = True,
    ) -> tuple[str, str, str]:
        """
        Export records to the specified format.

        Args:
            records: List of transcription records
            format: Export format
            include_metadata: Include metadata for JSON/CSV formats

        Returns:
            Tuple of (content, filename, content_type)
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"speakeasy_export_{timestamp}.{FILE_EXTENSIONS[format]}"
        content_type = CONTENT_TYPES[format]

        if format == ExportFormat.TXT:
            content = self.to_txt(records)
        elif format == ExportFormat.JSON:
            content = self.to_json(records, include_metadata)
        elif format == ExportFormat.CSV:
            content = self.to_csv(records, include_metadata)
        elif format == ExportFormat.SRT:
            content = self.to_srt(records)
        elif format == ExportFormat.VTT:
            content = self.to_vtt(records)
        else:
            raise ValueError(f"Unsupported export format: {format}")

        return content, filename, content_type


# Singleton instance
export_service = ExportService()
