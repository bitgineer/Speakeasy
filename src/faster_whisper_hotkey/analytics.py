"""
Analytics and usage statistics module for faster-whisper-hotkey.

This module provides comprehensive usage tracking and statistics including:
- Words transcribed over time (today/week/month)
- Estimated time saved vs typing
- Most-used applications
- Peak usage hours
- Transcription accuracy based on manual corrections

Classes
-------
AnalyticsTracker
    Tracks and stores usage statistics for each transcription.

AnalyticsData
    Data class for analytics statistics.

UsageStatistics
    Calculates and provides various usage statistics.

Notes
-----
Analytics data is stored in ~/.config/faster_whisper_hotkey/analytics.json
"""

import os
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from collections import defaultdict
import re

logger = logging.getLogger(__name__)

# Analytics storage directory
conf_dir = os.path.expanduser("~/.config")
settings_dir = os.path.join(conf_dir, "faster_whisper_hotkey")
os.makedirs(settings_dir, exist_ok=True)
ANALYTICS_FILE = os.path.join(settings_dir, "analytics.json")

# Average typing speed: 40 words per minute (WPM)
# Average speaking rate: 150 words per minute
TYPING_SPEED_WPM = 40
SPEAKING_SPEED_WPM = 150


@dataclass
class TranscriptionRecord:
    """Single transcription record with analytics data."""
    timestamp: str  # ISO format timestamp
    text: str  # Transcribed text
    word_count: int  # Number of words in the transcription
    duration_seconds: float  # Audio duration in seconds
    app_name: str  # Application name (e.g., "chrome", "code", "terminal")
    app_window_class: str  # Window class for app identification
    app_window_title: str  # Window title
    model_used: str  # Model used for transcription
    language: str  # Language code
    original_text: str  # Original transcription before processing
    was_corrected: bool = False  # Whether user manually corrected the text
    correction_count: int = 0  # Number of manual corrections made


@dataclass
class DailyStats:
    """Statistics for a single day."""
    date: str  # YYYY-MM-DD format
    word_count: int
    transcription_count: int
    total_duration_seconds: float
    most_used_app: str
    peak_hour: int  # Hour (0-23) with most transcriptions


@dataclass
class AnalyticsData:
    """Complete analytics data container."""
    records: List[Dict[str, Any]] = field(default_factory=list)
    daily_stats: List[Dict[str, Any]] = field(default_factory=list)
    app_usage: Dict[str, int] = field(default_factory=dict)
    total_words_all_time: int = 0
    total_transcriptions: int = 0


class UsageStatistics:
    """Calculates various usage statistics from analytics data."""

    def __init__(self, analytics_data: AnalyticsData):
        """Initialize with analytics data.

        Args:
            analytics_data: AnalyticsData instance with records
        """
        self.analytics_data = analytics_data

    def _parse_date(self, timestamp: str) -> datetime:
        """Parse ISO timestamp to datetime."""
        try:
            return datetime.fromisoformat(timestamp)
        except (ValueError, TypeError):
            return datetime.now()

    def get_words_today(self) -> int:
        """Get total words transcribed today."""
        today = datetime.now().date()
        count = 0
        for record in self.analytics_data.records:
            try:
                record_date = self._parse_date(record["timestamp"]).date()
                if record_date == today:
                    count += record.get("word_count", 0)
            except Exception:
                continue
        return count

    def get_words_this_week(self) -> int:
        """Get total words transcribed this week."""
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        count = 0
        for record in self.analytics_data.records:
            try:
                record_date = self._parse_date(record["timestamp"]).date()
                if week_start <= record_date <= today:
                    count += record.get("word_count", 0)
            except Exception:
                continue
        return count

    def get_words_this_month(self) -> int:
        """Get total words transcribed this month."""
        today = datetime.now().date()
        month_start = today.replace(day=1)
        count = 0
        for record in self.analytics_data.records:
            try:
                record_date = self._parse_date(record["timestamp"]).date()
                if month_start <= record_date <= today:
                    count += record.get("word_count", 0)
            except Exception:
                continue
        return count

    def get_time_saved_minutes(self) -> float:
        """Get estimated time saved in minutes vs typing.

        Calculation:
        - Time to type = word_count / TYPING_SPEED_WPM
        - Time to speak = word_count / SPEAKING_SPEED_WPM
        - Time saved = time_to_type - time_to_speak - processing_time
        """
        total_words = sum(r.get("word_count", 0) for r in self.analytics_data.records)
        time_to_type_minutes = total_words / TYPING_SPEED_WPM
        time_to_speak_minutes = total_words / SPEAKING_SPEED_WPM

        # Account for processing time (5 seconds overhead per transcription)
        processing_overhead = len(self.analytics_data.records) * 5 / 60

        time_saved = time_to_type_minutes - time_to_speak_minutes - processing_overhead
        return max(0, time_saved)

    def get_most_used_apps(self, limit: int = 10) -> List[tuple[str, int]]:
        """Get list of most used applications sorted by usage count.

        Args:
            limit: Maximum number of apps to return

        Returns:
            List of (app_name, usage_count) tuples
        """
        app_counts = defaultdict(int)
        for record in self.analytics_data.records:
            app_name = record.get("app_name", "Unknown")
            app_counts[app_name] += 1

        # Sort by count descending
        sorted_apps = sorted(app_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_apps[:limit]

    def get_peak_usage_hours(self, limit: int = 5) -> List[tuple[int, int]]:
        """Get peak usage hours.

        Args:
            limit: Maximum number of hours to return

        Returns:
            List of (hour, transcription_count) tuples
        """
        hour_counts = defaultdict(int)
        for record in self.analytics_data.records:
            try:
                hour = self._parse_date(record["timestamp"]).hour
                hour_counts[hour] += 1
            except Exception:
                continue

        # Sort by count descending
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_hours[:limit]

    def get_words_per_day(self, days: int = 30) -> List[tuple[str, int]]:
        """Get word count per day for the last N days.

        Args:
            days: Number of days to include

        Returns:
            List of (date_str, word_count) tuples
        """
        daily_words = defaultdict(int)
        today = datetime.now().date()

        for record in self.analytics_data.records:
            try:
                record_date = self._parse_date(record["timestamp"]).date()
                days_ago = (today - record_date).days
                if 0 <= days_ago < days:
                    date_str = record_date.isoformat()
                    daily_words[date_str] += record.get("word_count", 0)
            except Exception:
                continue

        # Sort by date
        sorted_days = sorted(daily_words.items())
        return sorted_days

    def get_hourly_heatmap_data(self, days: int = 7) -> Dict[int, int]:
        """Get hourly usage data for heatmap visualization.

        Args:
            days: Number of days to include

        Returns:
            Dictionary mapping hour (0-23) to transcription count
        """
        hourly_counts = defaultdict(int)
        today = datetime.now().date()

        for record in self.analytics_data.records:
            try:
                record_date = self._parse_date(record["timestamp"]).date()
                days_ago = (today - record_date).days
                if 0 <= days_ago < days:
                    hour = self._parse_date(record["timestamp"]).hour
                    hourly_counts[hour] += 1
            except Exception:
                continue

        # Fill in missing hours with 0
        result = {hour: hourly_counts.get(hour, 0) for hour in range(24)}
        return result

    def get_accuracy_rate(self) -> float:
        """Calculate transcription accuracy based on corrections.

        Returns:
            Accuracy percentage (0-100), or None if insufficient data
        """
        corrected = sum(1 for r in self.analytics_data.records if r.get("was_corrected", False))
        total = len(self.analytics_data.records)

        if total == 0:
            return 100.0  # No data means perfect accuracy

        accuracy = ((total - corrected) / total) * 100
        return accuracy

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get a summary of all statistics.

        Returns:
            Dictionary with all key statistics
        """
        return {
            "words_today": self.get_words_today(),
            "words_this_week": self.get_words_this_week(),
            "words_this_month": self.get_words_this_month(),
            "words_all_time": self.analytics_data.total_words_all_time,
            "transcription_count": self.analytics_data.total_transcriptions,
            "time_saved_minutes": self.get_time_saved_minutes(),
            "time_saved_hours": self.get_time_saved_minutes() / 60,
            "accuracy_rate": self.get_accuracy_rate(),
            "most_used_apps": self.get_most_used_apps(5),
            "peak_hours": self.get_peak_usage_hours(3),
        }


class AnalyticsTracker:
    """Tracks and stores usage statistics."""

    def __init__(self, max_records: int = 10000):
        """Initialize analytics tracker.

        Args:
            max_records: Maximum number of transcription records to keep
        """
        self.max_records = max_records
        self.data = self._load_data()
        self._privacy_mode = False

    def _load_data(self) -> AnalyticsData:
        """Load analytics data from disk."""
        try:
            with open(ANALYTICS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return AnalyticsData(
                    records=data.get("records", []),
                    daily_stats=data.get("daily_stats", []),
                    app_usage=data.get("app_usage", {}),
                    total_words_all_time=data.get("total_words_all_time", 0),
                    total_transcriptions=data.get("total_transcriptions", 0),
                )
        except (FileNotFoundError, json.JSONDecodeError):
            return AnalyticsData()

    def _save_data(self):
        """Save analytics data to disk."""
        if self._privacy_mode:
            return  # Don't save in privacy mode

        try:
            # Trim records to max
            if len(self.data.records) > self.max_records:
                self.data.records = self.data.records[-self.max_records:]

            data_dict = {
                "records": self.data.records,
                "daily_stats": self.data.daily_stats,
                "app_usage": self.data.app_usage,
                "total_words_all_time": self.data.total_words_all_time,
                "total_transcriptions": self.data.total_transcriptions,
            }

            with open(ANALYTICS_FILE, "w", encoding="utf-8") as f:
                json.dump(data_dict, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save analytics data: {e}")

    def set_privacy_mode(self, enabled: bool):
        """Set privacy mode and clear data if enabled.

        Args:
            enabled: Whether privacy mode is enabled
        """
        self._privacy_mode = enabled
        if enabled:
            # Clear in-memory data
            self.data = AnalyticsData()
            # Also delete the analytics file
            try:
                if os.path.exists(ANALYTICS_FILE):
                    os.remove(ANALYTICS_FILE)
                    logger.info("Analytics data cleared due to privacy mode")
            except IOError as e:
                logger.error(f"Failed to remove analytics file: {e}")

    def _count_words(self, text: str) -> int:
        """Count words in text.

        Args:
            text: Text to count words in

        Returns:
            Number of words
        """
        if not text:
            return 0
        # Split by whitespace and filter empty strings
        words = re.findall(r'\S+', text)
        return len(words)

    def _normalize_app_name(self, window_class: str, window_title: str, process_name: str = "") -> str:
        """Normalize app name to a human-readable format.

        Args:
            window_class: Window class name
            window_title: Window title
            process_name: Process name (optional)

        Returns:
            Normalized app name
        """
        # Common app mappings
        app_mappings = {
            "google-chrome": "Chrome",
            "chrome": "Chrome",
            "firefox": "Firefox",
            "code": "VS Code",
            "code-oss": "VS Code",
            "vim": "Vim",
            "nvim": "Neovim",
            "emacs": "Emacs",
            "terminal": "Terminal",
            "gnome-terminal": "Terminal",
            "konsole": "Terminal",
            "alacritty": "Terminal",
            "slack": "Slack",
            "discord": "Discord",
            "zoom": "Zoom",
            "teams": "Teams",
            "spotify": "Spotify",
        }

        # Try window class first
        if window_class:
            class_lower = window_class.lower()
            if class_lower in app_mappings:
                return app_mappings[class_lower]
            # Capitalize first letter
            return window_class.title()

        # Try process name
        if process_name:
            proc_lower = process_name.lower()
            if proc_lower in app_mappings:
                return app_mappings[proc_lower]
            return process_name.title()

        # Fallback to extracting from title or generic
        if window_title:
            # Try to detect from title (e.g., "Document - Google Docs")
            if "chrome" in window_title.lower():
                return "Chrome"
            if "visual studio code" in window_title.lower():
                return "VS Code"

        return "Unknown"

    def record_transcription(
        self,
        text: str,
        original_text: str,
        duration_seconds: float,
        model_used: str,
        language: str,
        app_window_class: str = "",
        app_window_title: str = "",
        app_process_name: str = "",
    ) -> Optional[TranscriptionRecord]:
        """Record a transcription for analytics.

        Args:
            text: Final processed text
            original_text: Original transcription before processing
            duration_seconds: Audio duration in seconds
            model_used: Model used for transcription
            language: Language code
            app_window_class: Active window's class
            app_window_title: Active window's title
            app_process_name: Active process name

        Returns:
            TranscriptionRecord if saved, None if privacy mode is enabled
        """
        if self._privacy_mode:
            return None

        word_count = self._count_words(text)
        app_name = self._normalize_app_name(
            app_window_class, app_window_title, app_process_name
        )

        record = TranscriptionRecord(
            timestamp=datetime.now().isoformat(),
            text=text,
            word_count=word_count,
            duration_seconds=duration_seconds,
            app_name=app_name,
            app_window_class=app_window_class,
            app_window_title=app_window_title,
            model_used=model_used,
            language=language,
            original_text=original_text,
        )

        # Add to data
        self.data.records.append(asdict(record))
        self.data.total_words_all_time += word_count
        self.data.total_transcriptions += 1

        # Update app usage
        if app_name not in self.data.app_usage:
            self.data.app_usage[app_name] = 0
        self.data.app_usage[app_name] += 1

        # Save to disk
        self._save_data()

        return record

    def record_correction(self, timestamp: str):
        """Record that a transcription was manually corrected.

        Args:
            timestamp: ISO timestamp of the original transcription
        """
        if self._privacy_mode:
            return

        # Find the record and mark it as corrected
        for record in self.data.records:
            if record.get("timestamp") == timestamp:
                record["was_corrected"] = True
                record["correction_count"] = record.get("correction_count", 0) + 1
                self._save_data()
                return

    def get_statistics(self) -> UsageStatistics:
        """Get usage statistics calculator.

        Returns:
            UsageStatistics instance
        """
        return UsageStatistics(self.data)

    def clear_all_data(self):
        """Clear all analytics data."""
        self.data = AnalyticsData()
        try:
            if os.path.exists(ANALYTICS_FILE):
                os.remove(ANALYTICS_FILE)
                logger.info("All analytics data cleared")
        except IOError as e:
            logger.error(f"Failed to clear analytics data: {e}")


# Global analytics tracker instance
_analytics_tracker: Optional[AnalyticsTracker] = None


def get_analytics_tracker() -> AnalyticsTracker:
    """Get the global analytics tracker instance.

    Returns:
        AnalyticsTracker singleton instance
    """
    global _analytics_tracker
    if _analytics_tracker is None:
        _analytics_tracker = AnalyticsTracker()
    return _analytics_tracker
