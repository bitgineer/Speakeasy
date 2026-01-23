"""
History manager with SQLite storage for faster-whisper-hotkey.

This module provides a thread-safe, SQLite-based history storage system for
transcription history. It offers enhanced search performance, metadata tracking,
and migration from the existing JSON-based history system.

Classes
-------
HistoryItem
    Dataclass representing a single transcription history item with metadata.

HistoryManager
    Thread-safe manager for transcription history with SQLite storage.

Functions
---------
migrate_json_to_sqlite
    Migrate existing JSON history to SQLite format.

Notes
-----
When privacy mode is enabled, no history is saved and existing history
is not accessible. Database is stored in the user's config directory.
"""

import os
import sqlite3
import json
import logging
import threading
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Callable, Set
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)

# Config directory paths
conf_dir = os.path.expanduser("~/.config")
settings_dir = os.path.join(conf_dir, "faster_whisper_hotkey")
os.makedirs(settings_dir, exist_ok=True)

# Database and legacy file paths
HISTORY_DB = os.path.join(settings_dir, "transcription_history.db")
LEGACY_HISTORY_FILE = os.path.join(settings_dir, "transcription_history.json")


@dataclass
class HistoryItem:
    """
    A single transcription history item with full metadata.

    Attributes
    ----------
    id
        Unique database ID for this item.
    timestamp
        ISO format timestamp when transcription was created.
    text
        The transcribed text content.
    model
        Model name used for transcription (e.g., "large-v3", "parakeet").
    language
        Language code for transcription (e.g., "en", "es").
    device
        Device type used (e.g., "cpu", "cuda").
    app_context
        Application context info (window class, title) at time of transcription.
    confidence
        Transcription confidence score (0.0 to 1.0) if available.
    duration_ms
        Audio duration in milliseconds if available.
    tags
        List of user-assigned tags for organizing history.
    edited
        Whether the text has been manually edited by the user.
    """
    id: Optional[int] = None
    timestamp: str = ""
    text: str = ""
    model: str = ""
    language: str = ""
    device: str = ""
    app_context: Optional[Dict[str, str]] = None
    confidence: Optional[float] = None
    duration_ms: Optional[int] = None
    tags: List[str] = None
    edited: bool = False

    def __post_init__(self):
        if self.app_context is None:
            self.app_context = {}
        if self.tags is None:
            self.tags = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HistoryItem":
        """Create from dictionary."""
        return cls(**data)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "HistoryItem":
        """Create from a SQLite row."""
        app_context = {}
        if row["app_context"]:
            try:
                app_context = json.loads(row["app_context"])
            except json.JSONDecodeError:
                pass

        tags = []
        if row["tags"]:
            try:
                tags = json.loads(row["tags"])
            except json.JSONDecodeError:
                pass

        return cls(
            id=row["id"],
            timestamp=row["timestamp"],
            text=row["text"],
            model=row["model"] or "",
            language=row["language"] or "",
            device=row["device"] or "",
            app_context=app_context,
            confidence=row["confidence"],
            duration_ms=row["duration_ms"],
            tags=tags,
            edited=bool(row["edited"]),
        )


class HistoryManager:
    """
    Thread-safe manager for transcription history with SQLite storage.

    This class provides a comprehensive history management system with:
    - SQLite storage for efficient searching
    - Full metadata tracking (model, language, app context)
    - Privacy mode support
    - Automatic migration from JSON history
    - Thread-safe operations
    - Change notifications

    Parameters
    ----------
    db_path
        Path to the SQLite database file. Defaults to config dir.
    privacy_mode
        If True, disables all history operations and clears existing data.
    max_items
        Maximum number of history items to keep (soft limit for pruning).

    Attributes
    ----------
    db_path
        Path to the SQLite database file.
    privacy_mode
        Whether privacy mode is enabled (no history storage).
    max_items
        Maximum history items to retain.
    """

    # Schema version for future migrations
    SCHEMA_VERSION = 1

    def __init__(
        self,
        db_path: Optional[str] = None,
        privacy_mode: bool = False,
        max_items: int = 1000,
    ):
        """Initialize the history manager."""
        self.db_path = db_path or HISTORY_DB
        self.privacy_mode = privacy_mode
        self.max_items = max_items
        self._lock = threading.RLock()
        self._listeners: Set[Callable[[str], None]] = set()

        # Initialize database
        self._init_db()

        # Check for legacy JSON migration
        self._check_migration()

    def subscribe(self, callback: Callable[[str], None]) -> Callable[[], None]:
        """
        Subscribe to history change events.

        Parameters
        ----------
        callback
            Function to call when history changes. Receives event type:
            "added", "deleted", "cleared", "edited".

        Returns
        -------
        Callable[[], None]
            Unsubscribe function.
        """
        with self._lock:
            self._listeners.add(callback)

        def unsubscribe():
            with self._lock:
                self._listeners.discard(callback)

        return unsubscribe

    def _notify(self, event: str):
        """Notify all subscribers of a history change."""
        with self._lock:
            listeners = self._listeners.copy()

        for callback in listeners:
            try:
                callback(event)
            except Exception as e:
                logger.warning(f"Error in history change callback: {e}")

    @contextmanager
    def _get_connection(self):
        """Get a thread-local database connection."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """Initialize the database schema."""
        if self.privacy_mode:
            return

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Create history table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        text TEXT NOT NULL,
                        model TEXT,
                        language TEXT,
                        device TEXT,
                        app_context TEXT,
                        confidence REAL,
                        duration_ms INTEGER,
                        tags TEXT,
                        edited INTEGER DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Create indexes for efficient searching
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_timestamp
                    ON history(timestamp DESC)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_text
                    ON history(text COLLATE NOCASE)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_model
                    ON history(model)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_language
                    ON history(language)
                """)

                # Create metadata table for schema version
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS metadata (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )
                """)

                # Set schema version
                cursor.execute("""
                    INSERT OR IGNORE INTO metadata (key, value)
                    VALUES ('schema_version', ?)
                """, (str(self.SCHEMA_VERSION),))

        except Exception as e:
            logger.error(f"Failed to initialize history database: {e}")

    def _check_migration(self):
        """Check if legacy JSON history needs migration."""
        if self.privacy_mode:
            return

        if not os.path.exists(LEGACY_HISTORY_FILE):
            return

        # Check if we've already migrated
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT value FROM metadata WHERE key = 'json_migrated'"
                )
                if cursor.fetchone():
                    return  # Already migrated
        except Exception:
            pass

        # Attempt migration
        try:
            count = self.migrate_json_to_sqlite()
            if count > 0:
                logger.info(f"Migrated {count} items from JSON history to SQLite")
        except Exception as e:
            logger.error(f"Failed to migrate JSON history: {e}")

    def migrate_json_to_sqlite(self) -> int:
        """
        Migrate existing JSON history to SQLite database.

        Returns
        -------
        int
            Number of items migrated.

        Raises
        ------
        FileNotFoundError
            If legacy JSON file doesn't exist.
        """
        if self.privacy_mode:
            return 0

        if not os.path.exists(LEGACY_HISTORY_FILE):
            return 0

        try:
            with open(LEGACY_HISTORY_FILE, "r", encoding="utf-8") as f:
                json_history = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load JSON history for migration: {e}")
            return 0

        count = 0
        for entry in json_history:
            try:
                item = HistoryItem(
                    timestamp=entry.get("timestamp", datetime.now().isoformat()),
                    text=entry.get("text", ""),
                )
                self.add_item(item, skip_notification=True)
                count += 1
            except Exception as e:
                logger.warning(f"Failed to migrate history item: {e}")

        # Mark migration as complete
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO metadata (key, value) "
                    "VALUES ('json_migrated', ?)",
                    (datetime.now().isoformat(),)
                )

            # Backup the old file instead of deleting
            backup_path = LEGACY_HISTORY_FILE + ".backup"
            try:
                os.rename(LEGACY_HISTORY_FILE, backup_path)
                logger.info(f"JSON history backed up to {backup_path}")
            except Exception:
                pass

        except Exception as e:
            logger.warning(f"Failed to mark migration complete: {e}")

        if count > 0:
            self._notify("added")

        return count

    def set_privacy_mode(self, enabled: bool):
        """
        Update privacy mode setting.

        When enabled, clears all history and prevents new items from being saved.

        Parameters
        ----------
        enabled
            Whether to enable privacy mode.
        """
        with self._lock:
            self.privacy_mode = enabled

            if enabled:
                # Clear all history when enabling privacy mode
                try:
                    with self._get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM history")
                except Exception as e:
                    logger.error(f"Failed to clear history for privacy mode: {e}")

                self._notify("cleared")

    def add_item(
        self,
        item: HistoryItem,
        skip_notification: bool = False,
    ) -> Optional[int]:
        """
        Add a new transcription to history.

        Parameters
        ----------
        item
            The HistoryItem to add.
        skip_notification
            If True, don't send change notifications.

        Returns
        -------
        int or None
            The ID of the inserted item, or None if privacy mode is enabled.
        """
        if self.privacy_mode:
            return None

        if not item.text:
            return None

        # Ensure timestamp is set
        if not item.timestamp:
            item.timestamp = datetime.now().isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Serialize complex fields
                app_context_json = json.dumps(item.app_context) if item.app_context else None
                tags_json = json.dumps(item.tags) if item.tags else None

                cursor.execute("""
                    INSERT INTO history (
                        timestamp, text, model, language, device,
                        app_context, confidence, duration_ms, tags, edited
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.timestamp,
                    item.text,
                    item.model,
                    item.language,
                    item.device,
                    app_context_json,
                    item.confidence,
                    item.duration_ms,
                    tags_json,
                    int(item.edited),
                ))

                item_id = cursor.lastrowid

                # Prune old items if over limit
                self._prune_old_items(cursor)

                if not skip_notification:
                    self._notify("added")

                return item_id

        except Exception as e:
            logger.error(f"Failed to add history item: {e}")
            return None

    def get_all(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        descending: bool = True,
    ) -> List[HistoryItem]:
        """
        Get all history items.

        Parameters
        ----------
        limit
            Maximum number of items to return. None for all items.
        offset
            Number of items to skip from the start.
        descending
            If True, return newest items first.

        Returns
        -------
        list[HistoryItem]
            List of history items.
        """
        if self.privacy_mode:
            return []

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                order = "DESC" if descending else "ASC"
                sql = f"""
                    SELECT * FROM history
                    ORDER BY timestamp {order}
                    LIMIT ? OFFSET ?
                """

                cursor.execute(sql, (limit or -1, offset))
                return [HistoryItem.from_row(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Failed to get history items: {e}")
            return []

    def get_by_id(self, item_id: int) -> Optional[HistoryItem]:
        """
        Get a specific history item by ID.

        Parameters
        ----------
        item_id
            The database ID of the item.

        Returns
        -------
        HistoryItem or None
            The item if found, None otherwise.
        """
        if self.privacy_mode:
            return None

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM history WHERE id = ?", (item_id,))
                row = cursor.fetchone()

                if row:
                    return HistoryItem.from_row(row)

        except Exception as e:
            logger.error(f"Failed to get history item by ID: {e}")

        return None

    def search_by_text(
        self,
        query: str,
        limit: int = 100,
        fuzzy: bool = False,
    ) -> List[HistoryItem]:
        """
        Search history items by text content.

        Parameters
        ----------
        query
            The search query string.
        limit
            Maximum number of results to return.
        fuzzy
            If True, use pattern matching (SQLite GLOB).

        Returns
        -------
        list[HistoryItem]
            Matching history items, ordered by timestamp (newest first).
        """
        if self.privacy_mode:
            return []

        if not query:
            return []

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if fuzzy:
                    # Use LIKE with wildcards for fuzzy search
                    pattern = f"%{query}%"
                    cursor.execute("""
                        SELECT * FROM history
                        WHERE text LIKE ? COLLATE NOCASE
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (pattern, limit))
                else:
                    # Use FTS-style search if available, or basic LIKE
                    cursor.execute("""
                        SELECT * FROM history
                        WHERE text LIKE ? COLLATE NOCASE
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (f"%{query}%", limit))

                return [HistoryItem.from_row(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Failed to search history: {e}")
            return []

    def search_by_date(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[HistoryItem]:
        """
        Search history items by date range.

        Parameters
        ----------
        start_date
            Start of date range (inclusive). If None, searches from beginning.
        end_date
            End of date range (inclusive). If None, searches to present.

        Returns
        -------
        list[HistoryItem]
            Matching history items, ordered by timestamp (newest first).
        """
        if self.privacy_mode:
            return []

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                conditions = []
                params = []

                if start_date:
                    conditions.append("timestamp >= ?")
                    params.append(start_date.isoformat())

                if end_date:
                    conditions.append("timestamp <= ?")
                    params.append(end_date.isoformat())

                where_clause = " AND ".join(conditions) if conditions else "1=1"

                cursor.execute(f"""
                    SELECT * FROM history
                    WHERE {where_clause}
                    ORDER BY timestamp DESC
                """, params)

                return [HistoryItem.from_row(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Failed to search history by date: {e}")
            return []

    def search_by_model(self, model: str, limit: int = 100) -> List[HistoryItem]:
        """
        Search history items by model name.

        Parameters
        ----------
        model
            The model name to search for (exact match).
        limit
            Maximum number of results to return.

        Returns
        -------
        list[HistoryItem]
            Matching history items, ordered by timestamp (newest first).
        """
        if self.privacy_mode:
            return []

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM history
                    WHERE model = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (model, limit))

                return [HistoryItem.from_row(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Failed to search history by model: {e}")
            return []

    def search_by_language(self, language: str, limit: int = 100) -> List[HistoryItem]:
        """
        Search history items by language code.

        Parameters
        ----------
        language
            The language code to search for (exact match).
        limit
            Maximum number of results to return.

        Returns
        -------
        list[HistoryItem]
            Matching history items, ordered by timestamp (newest first).
        """
        if self.privacy_mode:
            return []

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM history
                    WHERE language = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (language, limit))

                return [HistoryItem.from_row(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Failed to search history by language: {e}")
            return []

    def advanced_search(
        self,
        text_query: Optional[str] = None,
        model: Optional[str] = None,
        language: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
    ) -> List[HistoryItem]:
        """
        Advanced search with multiple filters.

        Parameters
        ----------
        text_query
            Text content to search for (partial match).
        model
            Filter by model name.
        language
            Filter by language code.
        start_date
            Start of date range.
        end_date
            End of date range.
        tags
            Filter by tags (items must have at least one matching tag).
        limit
            Maximum number of results.

        Returns
        -------
        list[HistoryItem]
            Matching history items, ordered by timestamp (newest first).
        """
        if self.privacy_mode:
            return []

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                conditions = []
                params = []

                if text_query:
                    conditions.append("text LIKE ? COLLATE NOCASE")
                    params.append(f"%{text_query}%")

                if model:
                    conditions.append("model = ?")
                    params.append(model)

                if language:
                    conditions.append("language = ?")
                    params.append(language)

                if start_date:
                    conditions.append("timestamp >= ?")
                    params.append(start_date.isoformat())

                if end_date:
                    conditions.append("timestamp <= ?")
                    params.append(end_date.isoformat())

                if tags:
                    # Search for items with matching tags
                    tag_conditions = []
                    for tag in tags:
                        tag_conditions.append("tags LIKE ?")
                        params.append(f"%{tag}%")
                    conditions.append(f"({ ' OR '.join(tag_conditions) })")

                where_clause = " AND ".join(conditions) if conditions else "1=1"

                cursor.execute(f"""
                    SELECT * FROM history
                    WHERE {where_clause}
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, params + [limit])

                return [HistoryItem.from_row(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Failed to perform advanced search: {e}")
            return []

    def update_item(self, item_id: int, item: HistoryItem) -> bool:
        """
        Update an existing history item.

        Parameters
        ----------
        item_id
            The database ID of the item to update.
        item
            The updated HistoryItem data.

        Returns
        -------
        bool
            True if update was successful, False otherwise.
        """
        if self.privacy_mode:
            return False

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                app_context_json = json.dumps(item.app_context) if item.app_context else None
                tags_json = json.dumps(item.tags) if item.tags else None

                cursor.execute("""
                    UPDATE history SET
                        timestamp = ?,
                        text = ?,
                        model = ?,
                        language = ?,
                        device = ?,
                        app_context = ?,
                        confidence = ?,
                        duration_ms = ?,
                        tags = ?,
                        edited = ?
                    WHERE id = ?
                """, (
                    item.timestamp,
                    item.text,
                    item.model,
                    item.language,
                    item.device,
                    app_context_json,
                    item.confidence,
                    item.duration_ms,
                    tags_json,
                    int(item.edited),
                    item_id,
                ))

                if cursor.rowcount > 0:
                    self._notify("edited")
                    return True

        except Exception as e:
            logger.error(f"Failed to update history item: {e}")

        return False

    def delete_item(self, item_id: int) -> bool:
        """
        Delete a history item by ID.

        Parameters
        ----------
        item_id
            The database ID of the item to delete.

        Returns
        -------
        bool
            True if deletion was successful, False otherwise.
        """
        if self.privacy_mode:
            return False

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM history WHERE id = ?", (item_id,))

                if cursor.rowcount > 0:
                    self._notify("deleted")
                    return True

        except Exception as e:
            logger.error(f"Failed to delete history item: {e}")

        return False

    def clear_all(self) -> bool:
        """
        Delete all history items.

        Returns
        -------
        bool
            True if clear was successful, False otherwise.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM history")

            self._notify("cleared")
            return True

        except Exception as e:
            logger.error(f"Failed to clear history: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get history statistics.

        Returns
        -------
        dict
            Dictionary with statistics:
            - total_items: Total number of history items
            - today_count: Items from today
            - week_count: Items from the past 7 days
            - most_used_model: Most frequently used model
            - most_used_language: Most frequently used language
            - oldest_item: Timestamp of oldest item
            - newest_item: Timestamp of newest item
        """
        if self.privacy_mode:
            return {
                "total_items": 0,
                "today_count": 0,
                "week_count": 0,
                "most_used_model": None,
                "most_used_language": None,
                "oldest_item": None,
                "newest_item": None,
            }

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Total items
                cursor.execute("SELECT COUNT(*) FROM history")
                total_items = cursor.fetchone()[0]

                if total_items == 0:
                    return {
                        "total_items": 0,
                        "today_count": 0,
                        "week_count": 0,
                        "most_used_model": None,
                        "most_used_language": None,
                        "oldest_item": None,
                        "newest_item": None,
                    }

                # Today's count
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                cursor.execute(
                    "SELECT COUNT(*) FROM history WHERE timestamp >= ?",
                    (today.isoformat(),)
                )
                today_count = cursor.fetchone()[0]

                # Week count
                week_ago = (datetime.now() - timedelta(days=7)).isoformat()
                cursor.execute(
                    "SELECT COUNT(*) FROM history WHERE timestamp >= ?",
                    (week_ago,)
                )
                week_count = cursor.fetchone()[0]

                # Most used model
                cursor.execute("""
                    SELECT model, COUNT(*) as count
                    FROM history
                    WHERE model IS NOT NULL AND model != ''
                    GROUP BY model
                    ORDER BY count DESC
                    LIMIT 1
                """)
                model_row = cursor.fetchone()
                most_used_model = model_row[0] if model_row else None

                # Most used language
                cursor.execute("""
                    SELECT language, COUNT(*) as count
                    FROM history
                    WHERE language IS NOT NULL AND language != ''
                    GROUP BY language
                    ORDER BY count DESC
                    LIMIT 1
                """)
                lang_row = cursor.fetchone()
                most_used_language = lang_row[0] if lang_row else None

                # Date range
                cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM history")
                oldest, newest = cursor.fetchone()

                return {
                    "total_items": total_items,
                    "today_count": today_count,
                    "week_count": week_count,
                    "most_used_model": most_used_model,
                    "most_used_language": most_used_language,
                    "oldest_item": oldest,
                    "newest_item": newest,
                }

        except Exception as e:
            logger.error(f"Failed to get history statistics: {e}")
            return {}

    def export_to_json(self, file_path: Optional[str] = None) -> bool:
        """
        Export all history to JSON file.

        Parameters
        ----------
        file_path
            Path to export file. If None, uses legacy history file path.

        Returns
        -------
        bool
            True if export was successful, False otherwise.
        """
        if self.privacy_mode:
            return False

        export_path = file_path or LEGACY_HISTORY_FILE

        try:
            items = self.get_all()

            data = [item.to_dict() for item in items]

            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Exported {len(data)} items to {export_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export history: {e}")
            return False

    def export_to_txt(self, file_path: str) -> bool:
        """
        Export all history to plain text file.

        Parameters
        ----------
        file_path
            Path to export file.

        Returns
        -------
        bool
            True if export was successful, False otherwise.
        """
        if self.privacy_mode:
            return False

        try:
            items = self.get_all()

            with open(file_path, "w", encoding="utf-8") as f:
                for item in items:
                    # Format timestamp
                    try:
                        dt = datetime.fromisoformat(item.timestamp)
                        time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except (ValueError, TypeError):
                        time_str = item.timestamp

                    # Write entry
                    f.write(f"[{time_str}]")
                    if item.model:
                        f.write(f" [{item.model}]")
                    if item.language:
                        f.write(f" [{item.language.upper()}]")
                    f.write(f"\n{item.text}\n")
                    f.write("-" * 80 + "\n\n")

            logger.info(f"Exported {len(items)} items to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export history to text: {e}")
            return False

    def _prune_old_items(self, cursor: sqlite3.Cursor):
        """Prune old items if over the max_items limit."""
        try:
            cursor.execute("SELECT COUNT(*) FROM history")
            count = cursor.fetchone()[0]

            if count > self.max_items:
                # Delete oldest items beyond the limit
                cursor.execute("""
                    DELETE FROM history
                    WHERE id IN (
                        SELECT id FROM history
                        ORDER BY timestamp ASC
                        LIMIT ?
                    )
                """, (count - self.max_items,))

                logger.debug(f"Pruned {count - self.max_items} old history items")

        except Exception as e:
            logger.warning(f"Failed to prune old history items: {e}")

    def auto_delete_before_date(self, before_date: datetime) -> int:
        """
        Delete all history items before a specific date.

        Parameters
        ----------
        before_date
            Delete items older than this date.

        Returns
        -------
        int
            Number of items deleted.
        """
        if self.privacy_mode:
            return 0

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM history WHERE timestamp < ?",
                    (before_date.isoformat(),)
                )
                deleted_count = cursor.rowcount

                if deleted_count > 0:
                    self._notify("deleted")
                    logger.info(f"Auto-deleted {deleted_count} items before {before_date}")

                return deleted_count

        except Exception as e:
            logger.error(f"Failed to auto-delete old history: {e}")
            return 0


def migrate_json_to_sqlite(
    json_path: Optional[str] = None,
    db_path: Optional[str] = None,
) -> int:
    """
    Standalone function to migrate JSON history to SQLite.

    Parameters
    ----------
    json_path
        Path to JSON history file. Defaults to legacy path.
    db_path
        Path to SQLite database. Defaults to new history db path.

    Returns
    -------
    int
        Number of items migrated.
    """
    json_file = json_path or LEGACY_HISTORY_FILE

    if not os.path.exists(json_file):
        return 0

    # Create a temporary manager for migration
    manager = HistoryManager(db_path=db_path)

    return manager.migrate_json_to_sqlite()
