"""
Personal dictionary system for faster-whisper-hotkey.

This module provides an auto-learning dictionary that remembers user-specific
words and corrections. It supports fuzzy matching, case-sensitive entries,
pronunciation hints, and tracks usage statistics.

Classes
-------
DictionaryEntry
    Dataclass representing a single dictionary entry.

PersonalDictionary
    Main dictionary manager with storage, fuzzy matching, and auto-learning.

Functions
---------
load_dictionary
    Load dictionary from disk.

save_dictionary
    Save dictionary to disk.

Notes
-----
Dictionary entries are stored in JSON format with metadata including
variants, context, and usage count for intelligent correction.
"""

import os
import json
import logging
import re
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)

# Dictionary file location
conf_dir = os.path.expanduser("~/.config")
settings_dir = os.path.join(conf_dir, "faster_whisper_hotkey")
os.makedirs(settings_dir, exist_ok=True)
DICTIONARY_FILE = os.path.join(settings_dir, "personal_dictionary.json")

# Minimum similarity ratio for fuzzy matching (0-1)
DEFAULT_FUZZY_THRESHOLD = 0.75


@dataclass
class DictionaryEntry:
    """A single entry in the personal dictionary."""

    # The incorrect word(s) this entry corrects
    incorrect: str

    # The correct replacement text
    correct: str

    # Whether this entry is case-sensitive
    case_sensitive: bool = False

    # Pronunciation hint (optional, for homophones)
    pronunciation_hint: Optional[str] = None

    # Context where this correction applies (e.g., "medical", "legal")
    # None means apply in all contexts
    context: Optional[str] = None

    # Alternative incorrect spellings/variants that map to same correction
    variants: List[str] = field(default_factory=list)

    # Language code for this entry (e.g., "en", "es", "fr")
    # None means applies to all languages
    language: Optional[str] = None

    # How many times this entry has been used
    usage_count: int = 0

    # When this entry was created
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # When this entry was last used
    last_used: Optional[str] = None

    # Notes about this entry
    notes: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'DictionaryEntry':
        """Create from dictionary."""
        return cls(**data)

    def mark_used(self):
        """Mark this entry as used."""
        self.usage_count += 1
        self.last_used = datetime.now().isoformat()


class PersonalDictionary:
    """
    Personal dictionary for managing user-specific word corrections.

    Supports fuzzy matching, auto-learning from corrections, and
    export/import functionality.
    """

    def __init__(self, fuzzy_threshold: float = DEFAULT_FUZZY_THRESHOLD):
        """
        Initialize the personal dictionary.

        Parameters
        ----------
        fuzzy_threshold : float
            Minimum similarity ratio for fuzzy matching (0-1).
            Higher values require closer matches.
        """
        self.fuzzy_threshold = fuzzy_threshold
        self.entries: List[DictionaryEntry] = []
        self._load()

    def _load(self):
        """Load dictionary from disk."""
        try:
            with open(DICTIONARY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.entries = [DictionaryEntry.from_dict(entry) for entry in data]
                logger.info(f"Loaded {len(self.entries)} dictionary entries")
        except (FileNotFoundError, json.JSONDecodeError):
            self.entries = []
            logger.info("No existing dictionary found, starting fresh")

    def save(self):
        """Save dictionary to disk."""
        try:
            data = [entry.to_dict() for entry in self.entries]
            with open(DICTIONARY_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.entries)} dictionary entries")
        except IOError as e:
            logger.error(f"Failed to save dictionary: {e}")

    def add_entry(
        self,
        incorrect: str,
        correct: str,
        case_sensitive: bool = False,
        pronunciation_hint: Optional[str] = None,
        context: Optional[str] = None,
        language: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> DictionaryEntry:
        """
        Add a new entry to the dictionary.

        Parameters
        ----------
        incorrect : str
            The incorrect word(s) to correct.
        correct : str
            The correct replacement text.
        case_sensitive : bool
            Whether this entry is case-sensitive.
        pronunciation_hint : str, optional
            Pronunciation hint for homophones.
        context : str, optional
            Context where this correction applies.
        language : str, optional
            Language code for this entry (e.g., "en", "es", "fr").
            None means applies to all languages.
        notes : str, optional
            User notes about this entry.

        Returns
        -------
        DictionaryEntry
            The created entry.
        """
        # Check if entry already exists (case-insensitive check)
        incorrect_lower = incorrect.lower()
        for entry in self.entries:
            if entry.incorrect.lower() == incorrect_lower and entry.correct.lower() == correct.lower():
                logger.info(f"Entry already exists: {incorrect} -> {correct}")
                return entry

        entry = DictionaryEntry(
            incorrect=incorrect,
            correct=correct,
            case_sensitive=case_sensitive,
            pronunciation_hint=pronunciation_hint,
            context=context,
            language=language,
            notes=notes,
        )
        self.entries.append(entry)
        self.save()
        logger.info(f"Added dictionary entry: {incorrect} -> {correct} (lang: {language or 'all'})")
        return entry

    def remove_entry(self, incorrect: str, correct: str) -> bool:
        """
        Remove an entry from the dictionary.

        Parameters
        ----------
        incorrect : str
            The incorrect word(s).
        correct : str
            The correct replacement text.

        Returns
        -------
        bool
            True if entry was removed, False if not found.
        """
        incorrect_lower = incorrect.lower()
        for i, entry in enumerate(self.entries):
            if entry.incorrect.lower() == incorrect_lower and entry.correct.lower() == correct.lower():
                removed = self.entries.pop(i)
                logger.info(f"Removed dictionary entry: {removed.incorrect} -> {removed.correct}")
                self.save()
                return True
        return False

    def get_entry(self, incorrect: str, correct: str) -> Optional[DictionaryEntry]:
        """
        Get a specific entry from the dictionary.

        Parameters
        ----------
        incorrect : str
            The incorrect word(s).
        correct : str
            The correct replacement text.

        Returns
        -------
        DictionaryEntry or None
            The entry if found, None otherwise.
        """
        incorrect_lower = incorrect.lower()
        for entry in self.entries:
            if entry.incorrect.lower() == incorrect_lower and entry.correct.lower() == correct.lower():
                return entry
        return None

    def _is_in_dictionary(self, word: str) -> bool:
        """
        Check if a word exists in the dictionary.

        Parameters
        ----------
        word : str
            The word to check.

        Returns
        -------
        bool
            True if the word exists in the dictionary, False otherwise.
        """
        word_lower = word.lower()
        for entry in self.entries:
            # Check main incorrect form
            if entry.incorrect.lower() == word_lower:
                return True
            # Check variants
            for variant in entry.variants:
                if variant.lower() == word_lower:
                    return True
        return False

    def find_correction(self, text: str, use_fuzzy: bool = True) -> Optional[tuple[str, DictionaryEntry]]:
        """
        Find a correction for the given text.

        First tries exact matching, then fuzzy matching if enabled.

        Parameters
        ----------
        text : str
            The text to find a correction for.
        use_fuzzy : bool
            Whether to use fuzzy matching for inexact matches.

        Returns
        -------
        tuple or None
            (corrected_text, entry) if a correction is found, None otherwise.
        """
        # Try exact match first (respecting case sensitivity setting)
        text_lower = text.lower()
        for entry in self.entries:
            # Check main incorrect form
            if entry.case_sensitive:
                if entry.incorrect == text:
                    entry.mark_used()
                    self.save()
                    return entry.correct, entry
            else:
                if entry.incorrect.lower() == text_lower:
                    entry.mark_used()
                    self.save()
                    return entry.correct, entry

            # Check variants
            for variant in entry.variants:
                if entry.case_sensitive:
                    if variant == text:
                        entry.mark_used()
                        self.save()
                        return entry.correct, entry
                else:
                    if variant.lower() == text_lower:
                        entry.mark_used()
                        self.save()
                        return entry.correct, entry

        # Try fuzzy matching if enabled
        if use_fuzzy:
            for entry in self.entries:
                similarity = self._similarity_ratio(text_lower, entry.incorrect.lower())
                if similarity >= self.fuzzy_threshold:
                    entry.mark_used()
                    self.save()
                    return entry.correct, entry

                # Check variants
                for variant in entry.variants:
                    similarity = self._similarity_ratio(text_lower, variant.lower())
                    if similarity >= self.fuzzy_threshold:
                        entry.mark_used()
                        self.save()
                        return entry.correct, entry

        return None

    def apply_corrections(self, text: str, use_fuzzy: bool = True) -> str:
        """
        Apply all known corrections to the given text.

        Processes the text word by word and phrase by phrase,
        replacing any matches with their corrections.

        Parameters
        ----------
        text : str
            The text to apply corrections to.
        use_fuzzy : bool
            Whether to use fuzzy matching.

        Returns
        -------
        str
            The corrected text.
        """
        if not text:
            return text

        # Sort entries by length (descending) to match longer phrases first
        sorted_entries = sorted(self.entries, key=lambda e: len(e.incorrect.split()), reverse=True)

        result = text
        corrections_made = []

        for entry in sorted_entries:
            # Build pattern for this entry (including variants)
            patterns_to_try = [entry.incorrect] + entry.variants

            for pattern in patterns_to_try:
                if entry.case_sensitive:
                    # Exact case matching
                    if pattern in result:
                        result = result.replace(pattern, entry.correct)
                        corrections_made.append(f"{pattern} -> {entry.correct}")
                        entry.mark_used()
                else:
                    # Case-insensitive matching using regex
                    try:
                        pattern_re = re.compile(
                            re.escape(pattern),
                            flags=re.IGNORECASE
                        )
                        matches = pattern_re.findall(result)
                        if matches:
                            result = pattern_re.sub(entry.correct, result)
                            corrections_made.append(f"{pattern} -> {entry.correct}")
                            entry.mark_used()
                    except re.error:
                        # Fallback to simple replace if regex fails
                        if pattern.lower() in result.lower():
                            # Find the actual text with original casing
                            idx = result.lower().find(pattern.lower())
                            if idx != -1:
                                actual = result[idx:idx + len(pattern)]
                                result = result.replace(actual, entry.correct)
                                corrections_made.append(f"{pattern} -> {entry.correct}")
                                entry.mark_used()

        if corrections_made:
            logger.debug(f"Applied corrections: {', '.join(corrections_made)}")
            self.save()

        return result

    def _similarity_ratio(self, s1: str, s2: str) -> float:
        """
        Calculate similarity ratio between two strings.

        Uses a simple character-based similarity metric.

        Parameters
        ----------
        s1 : str
            First string.
        s2 : str
            Second string.

        Returns
        -------
        float
            Similarity ratio from 0 to 1.
        """
        if not s1 or not s2:
            return 0.0

        # Use difflib's SequenceMatcher for fuzzy matching
        try:
            from difflib import SequenceMatcher
            return SequenceMatcher(None, s1, s2).ratio()
        except ImportError:
            # Fallback: simple Levenshtein-based ratio
            return self._levenshtein_ratio(s1, s2)

    def _levenshtein_ratio(self, s1: str, s2: str) -> float:
        """
        Calculate Levenshtein distance-based ratio.

        Parameters
        ----------
        s1 : str
            First string.
        s2 : str
            Second string.

        Returns
        -------
        float
            Similarity ratio from 0 to 1.
        """
        len1, len2 = len(s1), len(s2)
        if len1 == 0:
            return 1.0 if len2 == 0 else 0.0

        # Dynamic programming table
        dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]

        for i in range(len1 + 1):
            dp[i][0] = i
        for j in range(len2 + 1):
            dp[0][j] = j

        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                cost = 0 if s1[i - 1] == s2[j - 1] else 1
                dp[i][j] = min(
                    dp[i - 1][j] + 1,      # deletion
                    dp[i][j - 1] + 1,      # insertion
                    dp[i - 1][j - 1] + cost  # substitution
                )

        max_len = max(len1, len2)
        return 1.0 - dp[len1][len2] / max_len

    # ------------------------------------------------------------------
    # Language-specific dictionary methods
    # ------------------------------------------------------------------
    def get_entries_by_language(self, language: Optional[str] = None) -> List[DictionaryEntry]:
        """
        Get dictionary entries filtered by language.

        Parameters
        ----------
        language : str, optional
            Language code to filter by (e.g., "en", "es", "fr").
            None returns entries that apply to all languages.

        Returns
        -------
        List[DictionaryEntry]
            List of entries for the specified language.
        """
        if language is None:
            # Get entries that apply to all languages
            return [e for e in self.entries if e.language is None]
        return [e for e in self.entries if e.language == language]

    def get_all_languages(self) -> List[str]:
        """
        Get list of all language codes in the dictionary.

        Returns
        -------
        List[str]
            Sorted list of unique language codes.
        """
        languages = set(e.language for e in self.entries if e.language)
        return sorted(languages)

    def apply_corrections_for_language(
        self,
        text: str,
        language: Optional[str] = None,
        use_fuzzy: bool = True
    ) -> str:
        """
        Apply corrections for a specific language.

        This includes both language-specific entries and entries that
        apply to all languages.

        Parameters
        ----------
        text : str
            Text to correct.
        language : str, optional
            Language code. If None, applies only universal entries.
        use_fuzzy : bool
            Whether to use fuzzy matching.

        Returns
        -------
        str
            Corrected text.
        """
        if not text:
            return text

        # Get entries for this language plus universal entries
        if language:
            entries = [e for e in self.entries if e.language is None or e.language == language]
        else:
            entries = [e for e in self.entries if e.language is None]

        # Sort by length (longest first)
        entries = sorted(entries, key=lambda e: len(e.incorrect.split()), reverse=True)

        result = text
        for entry in entries:
            patterns_to_try = [entry.incorrect] + entry.variants

            for pattern in patterns_to_try:
                if entry.case_sensitive:
                    if pattern in result:
                        result = result.replace(pattern, entry.correct)
                        entry.mark_used()
                else:
                    try:
                        pattern_re = re.compile(
                            re.escape(pattern),
                            flags=re.IGNORECASE
                        )
                        if pattern_re.search(result):
                            result = pattern_re.sub(entry.correct, result)
                            entry.mark_used()
                    except re.error:
                        if pattern.lower() in result.lower():
                            idx = result.lower().find(pattern.lower())
                            if idx != -1:
                                actual = result[idx:idx + len(pattern)]
                                result = result.replace(actual, entry.correct)
                                entry.mark_used()

        if entries:
            self.save()

        return result

    def export_to_json(self, filepath: str) -> bool:
        """
        Export dictionary to a JSON file.

        Parameters
        ----------
        filepath : str
            Path to export file.

        Returns
        -------
        bool
            True if export succeeded, False otherwise.
        """
        try:
            data = {
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "entries": [entry.to_dict() for entry in self.entries],
            }
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Exported {len(self.entries)} entries to {filepath}")
            return True
        except (IOError, TypeError) as e:
            logger.error(f"Failed to export dictionary: {e}")
            return False

    def import_from_json(self, filepath: str, merge: bool = True) -> int:
        """
        Import dictionary entries from a JSON file.

        Parameters
        ----------
        filepath : str
            Path to import file.
        merge : bool
            If True, merge with existing entries. If False, replace all.

        Returns
        -------
        int
            Number of entries imported.
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not merge:
                # Replace entire dictionary
                self.entries = [DictionaryEntry.from_dict(entry) for entry in data.get("entries", [])]
            else:
                # Merge with existing, avoiding duplicates
                for entry_data in data.get("entries", []):
                    new_entry = DictionaryEntry.from_dict(entry_data)
                    # Check for duplicates
                    exists = any(
                        e.incorrect.lower() == new_entry.incorrect.lower()
                        and e.correct.lower() == new_entry.correct.lower()
                        for e in self.entries
                    )
                    if not exists:
                        self.entries.append(new_entry)

            self.save()
            logger.info(f"Imported dictionary from {filepath}")
            return len(self.entries)

        except (FileNotFoundError, json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to import dictionary: {e}")
            return 0

    def get_statistics(self) -> dict:
        """
        Get statistics about the dictionary.

        Returns
        -------
        dict
            Dictionary with statistics.
        """
        total_usage = sum(e.usage_count for e in self.entries)
        contexts = set(e.context for e in self.entries if e.context)

        return {
            "total_entries": len(self.entries),
            "total_corrections_applied": total_usage,
            "case_sensitive_entries": sum(1 for e in self.entries if e.case_sensitive),
            "entries_with_pronunciation": sum(1 for e in self.entries if e.pronunciation_hint),
            "unique_contexts": len(contexts),
            "contexts": sorted(contexts) if contexts else [],
            "most_used_entries": sorted(
                self.entries,
                key=lambda e: e.usage_count,
                reverse=True
            )[:10]
        }

    def clear(self) -> bool:
        """
        Clear all dictionary entries.

        Returns
        -------
        bool
            True if cleared successfully.
        """
        try:
            self.entries = []
            self.save()
            logger.info("Dictionary cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear dictionary: {e}")
            return False

    def learn_from_correction(self, original: str, corrected: str) -> Optional[DictionaryEntry]:
        """
        Learn from a manual correction made by the user.

        This is called when the user manually edits transcribed text,
        allowing the dictionary to auto-learn new corrections.

        Parameters
        ----------
        original : str
            The original (incorrect) text.
        corrected : str
            The user-corrected text.

        Returns
        -------
        DictionaryEntry or None
            The newly created entry if the correction was learned,
            None if the correction was already known or invalid.
        """
        if not original or not corrected:
            return None

        if original.lower() == corrected.lower():
            return None  # No actual correction

        # Check if this correction already exists
        existing = self.get_entry(original, corrected)
        if existing:
            existing.mark_used()
            self.save()
            return existing

        # Auto-learn the new correction
        # Use case-sensitive if the correction differs only in case
        case_sensitive = (original.lower() == corrected.lower())

        entry = self.add_entry(
            incorrect=original,
            correct=corrected,
            case_sensitive=case_sensitive,
            notes="Auto-learned from user correction"
        )
        return entry


def load_dictionary() -> PersonalDictionary:
    """
    Load the personal dictionary from disk.

    Returns
    -------
    PersonalDictionary
        The loaded dictionary.
    """
    return PersonalDictionary()


def save_dictionary(dictionary: PersonalDictionary) -> bool:
    """
    Save the personal dictionary to disk.

    Parameters
    ----------
    dictionary : PersonalDictionary
        The dictionary to save.

    Returns
    -------
    bool
        True if saved successfully.
    """
    try:
        dictionary.save()
        return True
    except Exception as e:
        logger.error(f"Failed to save dictionary: {e}")
        return False
