"""
Language detection and mixed-language handling for faster-whisper-hotkey.

This module provides automatic language detection from text segments,
supports language-specific dictionary processing, and handles mixed-language
text by splitting and processing each segment appropriately.

Classes
-------
LanguageDetector
    Detects language from text segments with confidence scoring.

MixedLanguageProcessor
    Splits mixed-language text and applies language-specific processing.

LanguageSegment
    Dataclass representing a text segment with its detected language.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
from enum import Enum

logger = logging.getLogger(__name__)


# ISO 639-1 language codes with names
LANGUAGE_NAMES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "pl": "Polish",
    "ru": "Russian",
    "ar": "Arabic",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "hi": "Hindi",
    "sv": "Swedish",
    "da": "Danish",
    "no": "Norwegian",
    "fi": "Finnish",
    "tr": "Turkish",
    "cs": "Czech",
    "el": "Greek",
    "he": "Hebrew",
    "th": "Thai",
    "vi": "Vietnamese",
    "id": "Indonesian",
    "uk": "Ukrainian",
    "ro": "Romanian",
    "hu": "Hungarian",
}


class LanguageCode(Enum):
    """Common language codes supported."""
    EN = "en"
    ES = "es"
    FR = "fr"
    DE = "de"
    IT = "it"
    PT = "pt"
    NL = "nl"
    PL = "pl"
    RU = "ru"
    AR = "ar"
    ZH = "zh"
    JA = "ja"
    KO = "ko"
    HI = "hi"
    AUTO = "auto"


@dataclass
class LanguageSegment:
    """A text segment with detected language information."""
    text: str
    language: str
    confidence: float = 1.0
    start_pos: int = 0
    end_pos: int = 0

    def __len__(self):
        return len(self.text)


class LanguageDetector:
    """
    Detects language from text segments using character-based heuristics.

    This is a lightweight language detector that doesn't require external
    dependencies. It uses character n-gram analysis and language-specific
    patterns to identify the most likely language.

    For more accurate detection, you can integrate langdetect or polyglot.
    """

    # Language-specific character patterns (simplified)
    LANGUAGE_PATTERNS = {
        "en": {
            "common_words": {"the", "be", "to", "of", "and", "a", "in", "that", "have", "i"},
            "char_ranges": [(0x0041, 0x007A)],  # Basic Latin
        },
        "es": {
            "common_words": {"el", "la", "de", "que", "y", "a", "en", "un", "ser", "se"},
            "char_ranges": [(0x0041, 0x007A), (0x00C0, 0x00FF)],  # Latin + accents
            "special_chars": {"ñ", "á", "é", "í", "ó", "ú", "ü", "¿", "¡"},
        },
        "fr": {
            "common_words": {"le", "de", "un", "être", "et", "à", "il", "avoir", "ne", "je"},
            "char_ranges": [(0x0041, 0x007A), (0x00C0, 0x00FF)],
            "special_chars": {"ç", "â", "ê", "î", "ô", "û", "à", "è", "é", "ù", "œ", "æ"},
        },
        "de": {
            "common_words": {"der", "die", "und", "in", "den", "von", "zu", "das", "mit", "sich"},
            "char_ranges": [(0x0041, 0x007A), (0x00C0, 0x00FF)],
            "special_chars": {"ä", "ö", "ü", "ß"},
        },
        "it": {
            "common_words": {"il", "di", "che", "e", "la", "un", "a", "per", "in", "è"},
            "char_ranges": [(0x0041, 0x007A), (0x00C0, 0x00FF)],
            "special_chars": {"à", "è", "é", "ì", "ò", "ù"},
        },
        "pt": {
            "common_words": {"o", "de", "a", "e", "do", "da", "em", "um", "para", "é"},
            "char_ranges": [(0x0041, 0x007A), (0x00C0, 0x00FF)],
            "special_chars": {"ã", "õ", "á", "é", "í", "ó", "ú", "ç", "â", "ê"},
        },
        "ru": {
            "common_words": {"и", "в", "не", "на", "я", "быть", "он", "с", "как", "что"},
            "char_ranges": [(0x0410, 0x044F)],  # Cyrillic
            "special_chars": {"ъ", "ь"},
        },
        "zh": {
            "common_words": {"的", "一", "是", "不", "在", "了", "有", "和", "人", "这"},
            "char_ranges": [(0x4E00, 0x9FFF)],  # CJK Unified Ideographs
        },
        "ja": {
            "common_words": {"の", "に", "は", "を", "た", "が", "で", "て", "だ", "です"},
            "char_ranges": [(0x4E00, 0x9FFF), (0x3040, 0x309F)],  # Kanji + Hiragana
            "special_chars": {"ァ", "ィ", "ゥ", "ェ", "ォ", "ッ", "ャ", "ュ", "ョ"},
        },
        "ko": {
            "common_words": {"의", "이", "가", "은", "는", "을", "를", "에", "와", "과"},
            "char_ranges": [(0xAC00, 0xD7AF), (0x1100, 0x11FF)],  # Hangul
        },
        "ar": {
            "common_words": {"في", "من", "على", "أن", "إلى", "هذا", "كان", "أن", "التي", "كما"},
            "char_ranges": [(0x0600, 0x06FF)],  # Arabic
            "special_chars": {"ا", "ب", "ت", "ث", "ج", "ح", "خ", "د", "ذ", "ر", "ز", "س", "ش", "ص"},
        },
    }

    # Default minimum confidence threshold
    DEFAULT_MIN_CONFIDENCE = 0.3

    def __init__(self, min_confidence: float = DEFAULT_MIN_CONFIDENCE):
        """
        Initialize the language detector.

        Parameters
        ----------
        min_confidence : float
            Minimum confidence threshold (0-1) for language detection.
            Results below this threshold return "auto".
        """
        self.min_confidence = min_confidence

    def detect(self, text: str) -> Tuple[str, float]:
        """
        Detect the language of the given text.

        Parameters
        ----------
        text : str
            Text to analyze.

        Returns
        -------
        Tuple[str, float]
            (language_code, confidence) where language_code is an ISO 639-1 code
            or "auto" if confidence is too low.
        """
        if not text or len(text.strip()) < 3:
            return "auto", 0.0

        text_clean = text.lower().strip()

        # Check for character range matches first (faster)
        lang_by_char = self._detect_by_characters(text_clean)

        # Check for common word matches
        lang_by_words = self._detect_by_words(text_clean)

        # Combine scores
        scores = {}
        for lang, score in lang_by_char.items():
            scores[lang] = scores.get(lang, 0.0) + score * 0.6

        for lang, score in lang_by_words.items():
            scores[lang] = scores.get(lang, 0.0) + score * 0.4

        if not scores:
            return "auto", 0.0

        # Get best match
        best_lang = max(scores.items(), key=lambda x: x[1])

        if best_lang[1] < self.min_confidence:
            return "auto", best_lang[1]

        return best_lang

    def detect_segments(
        self,
        text: str,
        segment_size: int = 100
    ) -> List[LanguageSegment]:
        """
        Detect language for text segments.

        Splits text into segments and detects language for each.

        Parameters
        ----------
        text : str
            Text to analyze.
        segment_size : int
            Target size for each segment in characters.

        Returns
        -------
        List[LanguageSegment]
            List of segments with detected languages.
        """
        if not text:
            return []

        segments = []
        sentences = self._split_sentences(text)

        current_segment = ""
        current_lang = None
        current_confidence = 0.0
        start_pos = 0

        for sentence in sentences:
            if not sentence.strip():
                continue

            # Detect language for this sentence
            lang, conf = self.detect(sentence)

            # If language changes significantly, start new segment
            if current_lang and lang != current_lang and current_segment:
                segments.append(LanguageSegment(
                    text=current_segment.strip(),
                    language=current_lang,
                    confidence=current_confidence,
                    start_pos=start_pos,
                    end_pos=start_pos + len(current_segment)
                ))
                start_pos += len(current_segment)
                current_segment = sentence
                current_lang = lang
                current_confidence = conf
            else:
                current_segment += " " + sentence if current_segment else sentence
                current_lang = lang
                current_confidence = max(current_confidence, conf)

        # Add final segment
        if current_segment.strip():
            segments.append(LanguageSegment(
                text=current_segment.strip(),
                language=current_lang or "auto",
                confidence=current_confidence,
                start_pos=start_pos,
                end_pos=start_pos + len(current_segment)
            ))

        return segments

    def _detect_by_characters(self, text: str) -> Dict[str, float]:
        """Detect language by character ranges and special characters."""
        scores = {}

        for char in text:
            for lang, patterns in self.LANGUAGE_PATTERNS.items():
                # Check special characters
                if "special_chars" in patterns:
                    if char in patterns["special_chars"]:
                        scores[lang] = scores.get(lang, 0.0) + 2.0

                # Check character ranges
                if "char_ranges" in patterns:
                    for start, end in patterns["char_ranges"]:
                        if start <= ord(char) <= end:
                            scores[lang] = scores.get(lang, 0.0) + 0.5

        # Normalize scores
        max_score = max(scores.values()) if scores else 1.0
        return {lang: min(1.0, score / max_score) for lang, score in scores.items()}

    def _detect_by_words(self, text: str) -> Dict[str, float]:
        """Detect language by matching common words."""
        scores = {}
        words = re.findall(r'\b\w+\b', text.lower())

        for word in words:
            for lang, patterns in self.LANGUAGE_PATTERNS.items():
                if "common_words" in patterns:
                    if word in patterns["common_words"]:
                        scores[lang] = scores.get(lang, 0.0) + 1.0

        # Normalize scores by number of words checked
        if words:
            max_score = max(scores.values()) if scores else 1.0
            return {lang: min(1.0, score / max_score) for lang, score in scores.items()}

        return scores

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting on periods, question marks, exclamation
        sentences = re.split(r'[.!?]+\s+', text.strip())

        # Handle the case where text doesn't end with punctuation
        if sentences and sentences[-1]:
            return sentences
        return sentences[:-1] if len(sentences) > 1 else sentences


class MixedLanguageProcessor:
    """
    Handles mixed-language text processing.

    Detects language changes within text and applies language-specific
    processing (like dictionary corrections) to each segment.
    """

    def __init__(self, detector: Optional[LanguageDetector] = None):
        """
        Initialize the mixed-language processor.

        Parameters
        ----------
        detector : LanguageDetector, optional
            Language detector to use. If None, creates default.
        """
        self.detector = detector or LanguageDetector()

    def split_by_language(self, text: str) -> List[LanguageSegment]:
        """
        Split text into segments by detected language.

        Parameters
        ----------
        text : str
            Text to split.

        Returns
        -------
        List[LanguageSegment]
            List of text segments with their detected languages.
        """
        return self.detector.detect_segments(text)

    def process_with_language_dictionary(
        self,
        text: str,
        dictionary_getter,
        default_language: str = "en"
    ) -> Tuple[str, List[LanguageSegment]]:
        """
        Process text applying language-specific dictionary corrections.

        Parameters
        ----------
        text : str
            Text to process.
        dictionary_getter : callable
            Function that takes a language code and returns the appropriate
            dictionary for that language.
        default_language : str
            Default language to use for segments with "auto" detection.

        Returns
        -------
        Tuple[str, List[LanguageSegment]]
            (processed_text, segments) tuple.
        """
        segments = self.split_by_language(text)

        processed_segments = []
        for segment in segments:
            # Get the appropriate dictionary for this segment's language
            lang = segment.language if segment.language != "auto" else default_language
            dictionary = dictionary_getter(lang)

            # Apply dictionary corrections if available
            if dictionary:
                try:
                    corrected_text = dictionary.apply_corrections(segment.text)
                    processed_segments.append(LanguageSegment(
                        text=corrected_text,
                        language=segment.language,
                        confidence=segment.confidence,
                        start_pos=segment.start_pos,
                        end_pos=segment.end_pos
                    ))
                except Exception as e:
                    logger.debug(f"Dictionary correction failed for {lang}: {e}")
                    processed_segments.append(segment)
            else:
                processed_segments.append(segment)

        # Rejoin segments
        result = " ".join(seg.text for seg in processed_segments)
        return result, segments

    def get_language_summary(self, text: str) -> Dict[str, float]:
        """
        Get a summary of languages present in the text.

        Parameters
        ----------
        text : str
            Text to analyze.

        Returns
        -------
        Dict[str, float]
            Dictionary mapping language codes to proportion of text.
        """
        segments = self.split_by_language(text)

        if not segments:
            return {}

        total_chars = sum(len(seg.text) for seg in segments)
        summary = {}

        for seg in segments:
            lang_name = LANGUAGE_NAMES.get(seg.language, seg.language)
            proportion = len(seg.text) / total_chars if total_chars > 0 else 0
            summary[lang_name] = summary.get(lang_name, 0.0) + proportion

        return summary


def get_language_name(code: str) -> str:
    """
    Get human-readable language name from code.

    Parameters
    ----------
    code : str
        ISO 639-1 language code.

    Returns
    -------
    str
        Language name or the code if not found.
    """
    return LANGUAGE_NAMES.get(code, code)


def is_supported_language(code: str) -> bool:
    """
    Check if a language code is supported.

    Parameters
    ----------
    code : str
        ISO 639-1 language code.

    Returns
    -------
    bool
        True if supported.
    """
    return code in LANGUAGE_NAMES or code == "auto"
