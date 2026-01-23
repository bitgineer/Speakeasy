"""
Accuracy tracking system for faster-whisper-hotkey.

This module provides a comprehensive system to track manual corrections
in transcription history, calculate accuracy metrics over time, identify
problematic words/phrases, and suggest dictionary additions.

Classes
-------
AccuracyEntry
    Dataclass representing a single accuracy tracking entry.

Correction
    Dataclass representing a single correction made.

AccuracyTracker
    Main tracker for managing accuracy data and calculating statistics.

ProblemWord
    Dataclass representing a problematic word/phrase.

Functions
---------
load_accuracy_tracker
    Load accuracy tracker from disk.

save_accuracy_tracker
    Save accuracy tracker to disk.

Notes
-----
Accuracy data is stored in ~/.config/faster_whisper_hotkey/accuracy_tracking.json
"""

import os
import json
import logging
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
from pathlib import Path
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)

# Accuracy file location
conf_dir = os.path.expanduser("~/.config")
settings_dir = os.path.join(conf_dir, "faster_whisper_hotkey")
os.makedirs(settings_dir, exist_ok=True)
ACCURACY_FILE = os.path.join(settings_dir, "accuracy_tracking.json")

# Minimum occurrences for a word to be considered "problematic"
MIN_PROBLEM_OCCURRENCES = 3


@dataclass
class Correction:
    """A single correction made during text processing or manual edit."""

    # Type of correction
    correction_type: str  # 'dictionary', 'auto_capitalize', 'filler_removal', 'punctuation', 'manual_edit', etc.

    # The original incorrect text
    original: str

    # The corrected text
    corrected: str

    # Position in text (optional, for context)
    position: int = -1

    # Confidence score (for model-based corrections)
    confidence: float = 0.0

    # Which processor made this correction
    processor: str = "unknown"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'Correction':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class AccuracyEntry:
    """A single accuracy tracking entry for a transcription."""

    # The raw transcribed text (before any processing)
    raw_text: str

    # The text after automatic processing (dictionary, capitalization, etc.)
    processed_text: str

    # The final text after any manual edits
    final_text: str

    # List of corrections made during automatic processing
    automatic_corrections: List[Correction] = field(default_factory=list)

    # Whether manual edits were made
    has_manual_edits: bool = False

    # Timestamp of this entry
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # Number of words in the transcription
    word_count: int = 0

    # Model confidence score (if available)
    model_confidence: float = 0.0

    # Audio duration in seconds (if available)
    audio_duration: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['automatic_corrections'] = [c.to_dict() for c in self.automatic_corrections]
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'AccuracyEntry':
        """Create from dictionary."""
        corrections = [Correction.from_dict(c) for c in data.pop('automatic_corrections', [])]
        return cls(automatic_corrections=corrections, **data)

    def calculate_accuracy(self) -> float:
        """Calculate accuracy percentage for this entry."""
        if not self.raw_text:
            return 100.0

        # Calculate word-level accuracy
        raw_words = self.raw_text.split()
        final_words = self.final_text.split()

        if not raw_words:
            return 100.0

        # Simple word count comparison
        # For more sophisticated accuracy, we could use edit distance
        raw_len = len(raw_words)
        final_len = len(final_words)

        if raw_len == 0:
            return 100.0

        # Calculate based on manual edits and automatic corrections
        total_corrections = len(self.automatic_corrections)
        if self.has_manual_edits:
            # Weight manual edits more heavily
            total_corrections += self._count_manual_edits()

        # Accuracy = (1 - corrections / total_words) * 100
        # But cap at 0 and 100
        accuracy = max(0, min(100, (1 - total_corrections / raw_len) * 100))
        return round(accuracy, 2)

    def _count_manual_edits(self) -> int:
        """Estimate number of manual edits based on text diff."""
        if self.processed_text == self.final_text:
            return 0

        # Simple word-level diff
        processed_words = set(self.processed_text.lower().split())
        final_words = set(self.final_text.lower().split())

        # Count added/removed words
        removed = len(processed_words - final_words)
        added = len(final_words - processed_words)

        return removed + added


@dataclass
class ProblemWord:
    """A problematic word/phrase that frequently needs correction."""

    # The problematic word/phrase
    word: str

    # How often it appears in transcriptions
    occurrence_count: int = 0

    # How often it gets corrected
    correction_count: int = 0

    # Suggested corrections (from actual corrections made)
    suggested_corrections: List[str] = field(default_factory=list)

    # Correction frequency (correction_count / occurrence_count)
    correction_frequency: float = 0.0

    # Whether this is already in the dictionary
    in_dictionary: bool = False

    # Timestamp of last occurrence
    last_seen: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'ProblemWord':
        """Create from dictionary."""
        return cls(**data)


class AccuracyTracker:
    """
    Main accuracy tracking system.

    Tracks corrections, calculates accuracy metrics over time,
    identifies problematic words, and suggests dictionary additions.
    """

    def __init__(self, max_entries: int = 1000):
        """
        Initialize the accuracy tracker.

        Parameters
        ----------
        max_entries : int
            Maximum number of entries to keep in memory.
        """
        self.max_entries = max_entries
        self.entries: List[AccuracyEntry] = []
        self._load()

    def _load(self):
        """Load accuracy data from disk."""
        try:
            with open(ACCURACY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.entries = [AccuracyEntry.from_dict(entry) for entry in data.get("entries", [])]
                logger.info(f"Loaded {len(self.entries)} accuracy entries")
        except (FileNotFoundError, json.JSONDecodeError):
            self.entries = []
            logger.info("No existing accuracy data found, starting fresh")

    def save(self):
        """Save accuracy data to disk."""
        try:
            # Keep only the most recent entries
            entries_to_save = self.entries[-self.max_entries:]

            data = {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "entries": [entry.to_dict() for entry in entries_to_save],
            }
            with open(ACCURACY_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(entries_to_save)} accuracy entries")
        except IOError as e:
            logger.error(f"Failed to save accuracy data: {e}")

    def add_entry(self, entry: AccuracyEntry):
        """
        Add a new accuracy tracking entry.

        Parameters
        ----------
        entry : AccuracyEntry
            The entry to add.
        """
        # Calculate word count if not set
        if entry.word_count == 0:
            entry.word_count = len(entry.raw_text.split())

        self.entries.append(entry)

        # Trim to max entries
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]

        self.save()

    def get_accuracy_over_time(self, days: int = 30) -> List[Dict]:
        """
        Get accuracy metrics over time.

        Parameters
        ----------
        days : int
            Number of days to look back.

        Returns
        -------
        List[Dict]
            List of daily accuracy metrics.
        """
        cutoff = datetime.now() - timedelta(days=days)

        # Group entries by day
        daily_data = defaultdict(lambda: {"total_words": 0, "total_corrections": 0, "entry_count": 0})

        for entry in self.entries:
            try:
                entry_date = datetime.fromisoformat(entry.timestamp)
            except (ValueError, TypeError):
                continue

            if entry_date < cutoff:
                continue

            day_key = entry_date.strftime("%Y-%m-%d")
            daily_data[day_key]["total_words"] += entry.word_count
            daily_data[day_key]["entry_count"] += 1

            # Count corrections
            daily_data[day_key]["total_corrections"] += len(entry.automatic_corrections)
            if entry.has_manual_edits:
                daily_data[day_key]["total_corrections"] += entry._count_manual_edits()

        # Calculate accuracy for each day
        result = []
        for date, data in sorted(daily_data.items()):
            if data["total_words"] > 0:
                accuracy = (1 - data["total_corrections"] / data["total_words"]) * 100
                accuracy = max(0, min(100, accuracy))
            else:
                accuracy = 100.0

            result.append({
                "date": date,
                "accuracy": round(accuracy, 2),
                "total_words": data["total_words"],
                "total_corrections": data["total_corrections"],
                "entry_count": data["entry_count"],
            })

        return result

    def get_overall_accuracy(self, days: int = 30) -> Dict:
        """
        Get overall accuracy statistics.

        Parameters
        ----------
        days : int
            Number of days to look back.

        Returns
        -------
        Dict
            Overall accuracy metrics.
        """
        cutoff = datetime.now() - timedelta(days=days)

        total_words = 0
        total_corrections = 0
        total_entries = 0
        with_manual_edits = 0

        for entry in self.entries:
            try:
                entry_date = datetime.fromisoformat(entry.timestamp)
            except (ValueError, TypeError):
                continue

            if entry_date < cutoff:
                continue

            total_words += entry.word_count
            total_corrections += len(entry.automatic_corrections)
            if entry.has_manual_edits:
                total_corrections += entry._count_manual_edits()
                with_manual_edits += 1
            total_entries += 1

        if total_entries == 0:
            return {
                "accuracy": 100.0,
                "total_words": 0,
                "total_corrections": 0,
                "total_entries": 0,
                "entries_with_manual_edits": 0,
                "manual_edit_rate": 0.0,
            }

        accuracy = (1 - total_corrections / total_words) * 100 if total_words > 0 else 100.0
        accuracy = max(0, min(100, accuracy))

        return {
            "accuracy": round(accuracy, 2),
            "total_words": total_words,
            "total_corrections": total_corrections,
            "total_entries": total_entries,
            "entries_with_manual_edits": with_manual_edits,
            "manual_edit_rate": round(with_manual_edits / total_entries * 100, 2) if total_entries > 0 else 0.0,
        }

    def get_problem_words(self, limit: int = 50) -> List[ProblemWord]:
        """
        Identify problematic words/phrases.

        Parameters
        ----------
        limit : int
            Maximum number of problem words to return.

        Returns
        -------
        List[ProblemWord]
            List of problematic words sorted by correction frequency.
        """
        # Track word occurrences and corrections
        word_occurrences = Counter()
        word_corrections = Counter()
        word_suggestions = defaultdict(set)

        for entry in self.entries:
            # Get words from raw text
            words = re.findall(r'\b\w+\b', entry.raw_text.lower())
            word_occurrences.update(words)

            # Track corrections
            for correction in entry.automatic_corrections:
                corrected_words = re.findall(r'\b\w+\b', correction.original.lower())
                for word in corrected_words:
                    word_corrections[word] += 1
                    if correction.corrected:
                        word_suggestions[word].add(correction.corrected)

            # Track manual edits by comparing processed vs final
            if entry.has_manual_edits:
                processed_words = set(re.findall(r'\b\w+\b', entry.processed_text.lower()))
                final_words = set(re.findall(r'\b\w+\b', entry.final_text.lower()))

                # Words that were removed or changed
                for word in processed_words - final_words:
                    word_corrections[word] += 1

                # Words that were added (the corrections)
                for word in final_words - processed_words:
                    word_suggestions[word.lower()].add(word)

        # Build problem words list
        problem_words = []

        for word, occurrence_count in word_occurrences.most_common(limit * 2):
            if occurrence_count < MIN_PROBLEM_OCCURRENCES:
                continue

            correction_count = word_corrections.get(word, 0)
            if correction_count == 0:
                continue

            correction_frequency = correction_count / occurrence_count

            problem_words.append(ProblemWord(
                word=word,
                occurrence_count=occurrence_count,
                correction_count=correction_count,
                correction_frequency=round(correction_frequency, 3),
                suggested_corrections=list(word_suggestions.get(word, set()))[:5],
                in_dictionary=False,  # Will be checked by UI
            ))

        # Sort by correction frequency, then by correction count
        problem_words.sort(key=lambda p: (p.correction_frequency, p.correction_count), reverse=True)

        return problem_words[:limit]

    def get_correction_statistics(self, days: int = 30) -> Dict:
        """
        Get statistics about corrections made.

        Parameters
        ----------
        days : int
            Number of days to look back.

        Returns
        -------
        Dict
            Correction statistics.
        """
        cutoff = datetime.now() - timedelta(days=days)

        corrections_by_type = Counter()
        corrections_by_processor = Counter()

        for entry in self.entries:
            try:
                entry_date = datetime.fromisoformat(entry.timestamp)
            except (ValueError, TypeError):
                continue

            if entry_date < cutoff:
                continue

            for correction in entry.automatic_corrections:
                corrections_by_type[correction.correction_type] += 1
                corrections_by_processor[correction.processor] += 1

        return {
            "by_type": dict(corrections_by_type),
            "by_processor": dict(corrections_by_processor),
        }

    def get_suggested_dictionary_additions(self, limit: int = 20) -> List[Dict]:
        """
        Get suggested dictionary additions based on common corrections.

        Parameters
        ----------
        limit : int
            Maximum number of suggestions.

        Returns
        -------
        List[Dict]
            Suggested dictionary entries.
        """
        problem_words = self.get_problem_words(limit * 2)

        suggestions = []

        for pw in problem_words[:limit]:
            # Only suggest words that are corrected often
            if pw.correction_frequency < 0.3:  # At least 30% of the time
                continue

            # Use the most common correction
            if pw.suggested_corrections:
                suggestions.append({
                    "incorrect": pw.word,
                    "correct": pw.suggested_corrections[0],
                    "confidence": pw.correction_frequency,
                    "occurrence_count": pw.occurrence_count,
                    "correction_count": pw.correction_count,
                })

        return suggestions

    def clear_old_entries(self, days: int = 90):
        """
        Clear entries older than specified days.

        Parameters
        ----------
        days : int
            Number of days to keep.
        """
        cutoff = datetime.now() - timedelta(days=days)

        original_count = len(self.entries)
        self.entries = [
            entry for entry in self.entries
            if datetime.fromisoformat(entry.timestamp) >= cutoff
        ]

        removed = original_count - len(self.entries)
        if removed > 0:
            logger.info(f"Cleared {removed} old accuracy entries")
            self.save()

    def clear_all(self):
        """Clear all accuracy data."""
        self.entries = []
        self.save()
        logger.info("Cleared all accuracy data")


def load_accuracy_tracker(max_entries: int = 1000) -> AccuracyTracker:
    """
    Load the accuracy tracker from disk.

    Parameters
    ----------
    max_entries : int
        Maximum number of entries to keep.

    Returns
    -------
    AccuracyTracker
        The loaded accuracy tracker.
    """
    return AccuracyTracker(max_entries=max_entries)


def save_accuracy_tracker(tracker: AccuracyTracker) -> bool:
    """
    Save the accuracy tracker to disk.

    Parameters
    ----------
    tracker : AccuracyTracker
        The accuracy tracker to save.

    Returns
    -------
    bool
        True if saved successfully.
    """
    try:
        tracker.save()
        return True
    except Exception as e:
        logger.error(f"Failed to save accuracy tracker: {e}")
        return False
