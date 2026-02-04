"""
History service for storing and retrieving transcription records.

Uses SQLite with FTS5 for full-text search.
Supports cursor-based pagination and field projection.
"""

import base64
import logging
import uuid
from dataclasses import dataclass, fields as dataclass_fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiosqlite

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionRecord:
    """A stored transcription record."""

    id: str
    text: str
    duration_ms: int
    model_used: Optional[str]
    language: Optional[str]
    created_at: datetime
    original_text: Optional[str] = None  # Original text before AI enhancement

    # All valid field names for projection
    VALID_FIELDS = {
        "id",
        "text",
        "duration_ms",
        "model_used",
        "language",
        "created_at",
        "original_text",
    }

    @property
    def is_ai_enhanced(self) -> bool:
        """Check if this transcription was AI-enhanced (grammar corrected)."""
        return self.original_text is not None and self.original_text != self.text

    def to_dict(self, fields: Optional[set[str]] = None) -> dict:
        """
        Convert to dictionary for JSON serialization.

        Args:
            fields: Optional set of field names to include. If None, include all fields.
        """
        all_data = {
            "id": self.id,
            "text": self.text,
            "duration_ms": self.duration_ms,
            "model_used": self.model_used,
            "language": self.language,
            "created_at": self.created_at.isoformat(),
            "original_text": self.original_text,
            "is_ai_enhanced": self.is_ai_enhanced,
        }
        if fields is None:
            return all_data
        return {k: v for k, v in all_data.items() if k in fields}


def encode_cursor(created_at: datetime, record_id: str) -> str:
    """Encode cursor from timestamp and ID."""
    cursor_str = f"{created_at.isoformat()}_{record_id}"
    return base64.urlsafe_b64encode(cursor_str.encode()).decode()


def decode_cursor(cursor: str) -> tuple[datetime, str]:
    """
    Decode cursor to timestamp and ID.

    Raises:
        ValueError: If cursor format is invalid.
    """
    try:
        decoded = base64.urlsafe_b64decode(cursor.encode()).decode()
        timestamp_str, record_id = decoded.rsplit("_", 1)
        created_at = datetime.fromisoformat(timestamp_str)
        return created_at, record_id
    except Exception as e:
        raise ValueError(f"Invalid cursor format: {e}")


class HistoryService:
    """
    Manages transcription history storage using SQLite.

    Features:
    - Async database operations
    - Full-text search via FTS5
    - Automatic cleanup of old records
    """

    def __init__(self, db_path: Path):
        """
        Initialize the history service.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        """Initialize the database and create tables if needed."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row

        # Create main transcriptions table
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS transcriptions (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                duration_ms INTEGER,
                model_used TEXT,
                language TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                original_text TEXT
            )
        """)

        # Create index on created_at for fast sorting
        await self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_transcriptions_created_at 
            ON transcriptions(created_at DESC)
        """)

        # Create FTS5 virtual table for full-text search
        await self._db.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS transcriptions_fts 
            USING fts5(text, content=transcriptions, content_rowid=rowid)
        """)

        # Create triggers to keep FTS index in sync
        await self._db.execute("""
            CREATE TRIGGER IF NOT EXISTS transcriptions_ai AFTER INSERT ON transcriptions BEGIN
                INSERT INTO transcriptions_fts(rowid, text) VALUES (new.rowid, new.text);
            END
        """)

        await self._db.execute("""
            CREATE TRIGGER IF NOT EXISTS transcriptions_ad AFTER DELETE ON transcriptions BEGIN
                INSERT INTO transcriptions_fts(transcriptions_fts, rowid, text) 
                VALUES('delete', old.rowid, old.text);
            END
        """)

        await self._db.execute("""
            CREATE TRIGGER IF NOT EXISTS transcriptions_au AFTER UPDATE ON transcriptions BEGIN
                INSERT INTO transcriptions_fts(transcriptions_fts, rowid, text) 
                VALUES('delete', old.rowid, old.text);
                INSERT INTO transcriptions_fts(rowid, text) VALUES (new.rowid, new.text);
            END
        """)

        await self._db.commit()

        # Run migrations for existing databases
        await self._migrate_schema()

        logger.info(f"History database initialized at {self.db_path}")

    async def _migrate_schema(self) -> None:
        """Run schema migrations for existing databases."""
        if not self._db:
            return

        # Check if original_text column exists
        cursor = await self._db.execute("PRAGMA table_info(transcriptions)")
        columns = await cursor.fetchall()
        column_names = {col[1] for col in columns}

        if "original_text" not in column_names:
            logger.info("Migrating database: adding original_text column")
            await self._db.execute("""
                ALTER TABLE transcriptions ADD COLUMN original_text TEXT
            """)
            await self._db.commit()
            logger.info("Migration complete: original_text column added")

    async def close(self) -> None:
        """Close the database connection."""
        if self._db:
            await self._db.close()
            self._db = None

    async def update_text(
        self,
        record_id: str,
        new_text: str,
        original_text: str,
    ) -> None:
        """
        Update the text of an existing transcription (e.g. after grammar correction).

        Args:
            record_id: The ID of the record to update
            new_text: The corrected text
            original_text: The original text (to preserve it)
        """
        if not self._db:
            raise RuntimeError("Database not initialized")

        await self._db.execute(
            """
            UPDATE transcriptions 
            SET text = ?, original_text = ?
            WHERE id = ?
            """,
            (new_text, original_text, record_id),
        )
        await self._db.commit()
        logger.debug(f"Updated transcription {record_id} with corrected text")

    async def add(
        self,
        text: str,
        duration_ms: int,
        model_used: Optional[str] = None,
        language: Optional[str] = None,
        original_text: Optional[str] = None,
    ) -> TranscriptionRecord:
        """
        Add a new transcription to history.

        Args:
            text: The transcribed text (may be grammar-corrected)
            duration_ms: Duration of transcription in milliseconds
            model_used: Name of the model used
            language: Language of the transcription
            original_text: Original text before AI enhancement (if applicable)

        Returns:
            The created TranscriptionRecord
        """
        if not self._db:
            raise RuntimeError("Database not initialized")

        record_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc)

        await self._db.execute(
            """
            INSERT INTO transcriptions (id, text, duration_ms, model_used, language, created_at, original_text)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (record_id, text, duration_ms, model_used, language, created_at, original_text),
        )
        await self._db.commit()

        logger.debug(f"Added transcription {record_id}: {text[:50]}...")

        return TranscriptionRecord(
            id=record_id,
            text=text,
            duration_ms=duration_ms,
            model_used=model_used,
            language=language,
            created_at=created_at,
            original_text=original_text,
        )

    async def get(self, record_id: str) -> Optional[TranscriptionRecord]:
        """
        Get a transcription by ID.

        Args:
            record_id: The record ID

        Returns:
            The TranscriptionRecord or None if not found
        """
        if not self._db:
            raise RuntimeError("Database not initialized")

        cursor = await self._db.execute(
            "SELECT * FROM transcriptions WHERE id = ?",
            (record_id,),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return TranscriptionRecord(
            id=row["id"],
            text=row["text"],
            duration_ms=row["duration_ms"],
            model_used=row["model_used"],
            language=row["language"],
            created_at=datetime.fromisoformat(row["created_at"]),
            original_text=row["original_text"] if "original_text" in row.keys() else None,
        )

    async def list(
        self,
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None,
        cursor: Optional[str] = None,
        fields: Optional[set[str]] = None,
    ) -> tuple[list[TranscriptionRecord], int, Optional[str]]:
        """
        List transcriptions with optional search, cursor pagination, and field projection.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip (ignored if cursor is provided)
            search: Optional search query for full-text search
            cursor: Optional cursor for pagination (format: base64 encoded "timestamp_id")
            fields: Optional set of field names to include in response

        Returns:
            Tuple of (list of records, total count, next cursor or None)
        """
        if not self._db:
            raise RuntimeError("Database not initialized")

        # Validate fields if provided
        if fields:
            invalid_fields = fields - TranscriptionRecord.VALID_FIELDS
            if invalid_fields:
                raise ValueError(f"Invalid fields: {invalid_fields}")

        # Parse cursor if provided
        cursor_created_at: Optional[datetime] = None
        cursor_id: Optional[str] = None
        if cursor:
            cursor_created_at, cursor_id = decode_cursor(cursor)

        if search:
            # Sanitize search query for FTS5
            # Escape double quotes and wrap in double quotes to treat as a literal string/phrase
            # This prevents syntax errors with single quotes or FTS5 keywords
            sanitized = search.replace('"', '""')
            search_query = f'"{sanitized}"'

            # Use FTS5 for full-text search
            count_cursor_db = await self._db.execute(
                """
                SELECT COUNT(*) FROM transcriptions t
                INNER JOIN transcriptions_fts fts ON t.rowid = fts.rowid
                WHERE transcriptions_fts MATCH ?
                """,
                (search_query,),
            )
            total = (await count_cursor_db.fetchone())[0]

            if cursor_created_at and cursor_id:
                # Cursor-based pagination with search
                db_cursor = await self._db.execute(
                    """
                    SELECT t.* FROM transcriptions t
                    INNER JOIN transcriptions_fts fts ON t.rowid = fts.rowid
                    WHERE transcriptions_fts MATCH ?
                    AND (t.created_at < ? OR (t.created_at = ? AND t.id < ?))
                    ORDER BY t.created_at DESC, t.id DESC
                    LIMIT ?
                    """,
                    (search_query, cursor_created_at, cursor_created_at, cursor_id, limit),
                )
            else:
                # Offset-based pagination with search (backward compatible)
                db_cursor = await self._db.execute(
                    """
                    SELECT t.* FROM transcriptions t
                    INNER JOIN transcriptions_fts fts ON t.rowid = fts.rowid
                    WHERE transcriptions_fts MATCH ?
                    ORDER BY t.created_at DESC, t.id DESC
                    LIMIT ? OFFSET ?
                    """,
                    (search_query, limit, offset),
                )
        else:
            count_cursor_db = await self._db.execute("SELECT COUNT(*) FROM transcriptions")
            total = (await count_cursor_db.fetchone())[0]

            if cursor_created_at and cursor_id:
                # Cursor-based pagination
                db_cursor = await self._db.execute(
                    """
                    SELECT * FROM transcriptions 
                    WHERE created_at < ? OR (created_at = ? AND id < ?)
                    ORDER BY created_at DESC, id DESC
                    LIMIT ?
                    """,
                    (cursor_created_at, cursor_created_at, cursor_id, limit),
                )
            else:
                # Offset-based pagination (backward compatible)
                db_cursor = await self._db.execute(
                    """
                    SELECT * FROM transcriptions 
                    ORDER BY created_at DESC, id DESC
                    LIMIT ? OFFSET ?
                    """,
                    (limit, offset),
                )

        rows = await db_cursor.fetchall()
        records = [
            TranscriptionRecord(
                id=row["id"],
                text=row["text"],
                duration_ms=row["duration_ms"],
                model_used=row["model_used"],
                language=row["language"],
                created_at=datetime.fromisoformat(row["created_at"]),
                original_text=row["original_text"] if "original_text" in row.keys() else None,
            )
            for row in rows
        ]

        # Generate next cursor if there are more records
        next_cursor: Optional[str] = None
        if records and len(records) == limit:
            last_record = records[-1]
            next_cursor = encode_cursor(last_record.created_at, last_record.id)

        return records, total, next_cursor

    async def delete(self, record_id: str) -> bool:
        """
        Delete a transcription by ID.

        Args:
            record_id: The record ID to delete

        Returns:
            True if deleted, False if not found
        """
        if not self._db:
            raise RuntimeError("Database not initialized")

        cursor = await self._db.execute(
            "DELETE FROM transcriptions WHERE id = ?",
            (record_id,),
        )
        await self._db.commit()

        return cursor.rowcount > 0

    async def clear(self) -> int:
        """
        Delete all transcriptions.

        Returns:
            Number of records deleted
        """
        if not self._db:
            raise RuntimeError("Database not initialized")

        cursor = await self._db.execute("DELETE FROM transcriptions")
        await self._db.commit()

        return cursor.rowcount

    async def get_stats(self) -> dict:
        """
        Get statistics about the history.

        Returns:
            Dictionary with stats including activity counts by time period
        """
        if not self._db:
            raise RuntimeError("Database not initialized")

        # Basic stats
        cursor = await self._db.execute("""
            SELECT 
                COUNT(*) as total_count,
                SUM(duration_ms) as total_duration_ms,
                MIN(created_at) as first_transcription,
                MAX(created_at) as last_transcription
            FROM transcriptions
        """)
        row = await cursor.fetchone()

        # Activity counts by time period (using SQLite date functions)
        # Today: created_at >= start of today (00:00:00)
        cursor = await self._db.execute("""
            SELECT COUNT(*) as today_count
            FROM transcriptions
            WHERE date(created_at) = date('now', 'localtime')
        """)
        today_row = await cursor.fetchone()

        # This week: created_at >= start of this week (Sunday)
        cursor = await self._db.execute("""
            SELECT COUNT(*) as week_count
            FROM transcriptions
            WHERE date(created_at) >= date('now', 'localtime', 'weekday 0', '-7 days')
        """)
        week_row = await cursor.fetchone()

        # This month: created_at >= start of this month
        cursor = await self._db.execute("""
            SELECT COUNT(*) as month_count
            FROM transcriptions
            WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now', 'localtime')
        """)
        month_row = await cursor.fetchone()

        return {
            "total_count": row["total_count"] or 0,
            "total_duration_ms": row["total_duration_ms"] or 0,
            "first_transcription": row["first_transcription"],
            "last_transcription": row["last_transcription"],
            "today_count": today_row["today_count"] or 0,
            "this_week_count": week_row["week_count"] or 0,
            "this_month_count": month_row["month_count"] or 0,
        }
