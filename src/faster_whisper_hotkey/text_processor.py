"""
Configurable text processing pipeline for transcriptions.

This module provides a pipeline for automatically cleaning up transcriptions
with toggleable processors including filler word removal, capitalization,
punctuation, number formatting, acronym expansion, and personal dictionary.

Classes
-------
TextProcessor
    Main pipeline coordinator for text processing.

Processor
    Base class for individual text processors.

FillerWordProcessor
    Removes filler words (um, uh, like, you know, etc.)

CapitalizationProcessor
    Auto-capitalizes sentences and proper nouns.

PunctuationProcessor
    Adds automatic punctuation.

NumberFormattingProcessor
    Formats numbers (e.g., "5" -> "five", "1000" -> "1,000").

AcronymExpansionProcessor
    Expands common acronyms based on context.

DictionaryProcessor
    Applies personal dictionary corrections with fuzzy matching.

TextProcessorConfig
    Configuration dataclass for the pipeline.
"""

import re
import logging
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple, TYPE_CHECKING

logger = logging.getLogger(__name__)

# Type hints for optional imports
if TYPE_CHECKING:
    from .language_detector import LanguageDetector, MixedLanguageProcessor
    from .translation_shortcuts import TranslationShortcutsManager


@dataclass
class Correction:
    """A single correction made during text processing."""
    correction_type: str
    original: str
    corrected: str
    position: int = -1
    confidence: float = 0.0
    processor: str = "unknown"


@dataclass
class TextProcessorConfig:
    """Configuration for the text processing pipeline."""

    # Enable/disable individual processors
    remove_filler_words: bool = True
    auto_capitalize: bool = True
    auto_punctuate: bool = True
    format_numbers: bool = False
    expand_acronyms: bool = False
    use_dictionary: bool = True  # Enable personal dictionary corrections

    # Sensitivity settings (0.0 to 1.0)
    filler_aggressiveness: float = 0.5  # Higher = more removal
    capitalization_style: str = "sentence"  # "sentence" or "title"
    punctuation_style: str = "minimal"  # "minimal" or "full"

    # Custom word lists
    custom_filler_words: List[str] = field(default_factory=list)
    custom_acronyms: Dict[str, str] = field(default_factory=dict)

    # Number formatting style
    number_style: str = "commas"  # "commas", "words", or "both"

    # Dictionary settings
    dictionary_fuzzy_matching: bool = True  # Use fuzzy matching for dictionary

    # Tone style preset settings
    tone_preset: str = "neutral"  # "neutral", "professional", "casual", "technical", "concise", "creative"
    tone_preset_enabled: bool = False  # Enable tone style processing

    # Multi-language processing settings
    enable_mixed_language: bool = False  # Enable mixed-language processing
    enable_translation_shortcuts: bool = False  # Enable translation shortcuts
    default_language: str = "en"  # Default language for mixed-language processing


class Processor(ABC):
    """Base class for text processors."""

    def __init__(self, config: TextProcessorConfig):
        self.config = config
        self.enabled = True
        self.corrections: List[Correction] = []

    @abstractmethod
    def process(self, text: str) -> str:
        """Process the input text and return the result."""
        pass

    def process_with_tracking(self, text: str) -> Tuple[str, List[Correction]]:
        """
        Process text and track corrections made.

        Parameters
        ----------
        text : str
            The input text to process.

        Returns
        -------
        Tuple[str, List[Correction]]
            The processed text and list of corrections made.
        """
        self.corrections = []
        original = text
        result = self.process(text)
        return result, self.corrections

    def _add_correction(self, correction_type: str, original: str, corrected: str,
                       position: int = -1, confidence: float = 0.0):
        """
        Record a correction made by this processor.

        Parameters
        ----------
        correction_type : str
            Type of correction (e.g., 'dictionary', 'filler_removal', etc.)
        original : str
            The original text
        corrected : str
            The corrected text
        position : int, optional
            Position in the text
        confidence : float, optional
            Confidence score (0-1)
        """
        processor_name = self.__class__.__name__
        correction = Correction(
            correction_type=correction_type,
            original=original,
            corrected=corrected,
            position=position,
            confidence=confidence,
            processor=processor_name
        )
        self.corrections.append(correction)

    def _set_enabled(self, enabled: bool):
        """Enable or disable this processor."""
        self.enabled = enabled


class FillerWordProcessor(Processor):
    """Removes filler words from transcriptions."""

    # Common filler words by frequency
    DEFAULT_FILLERS = [
        "um", "uh", "er", "ah", "like",
        "you know", "you see", "i mean",
        "kind of", "kinda", "sort of", "sorta",
        "basically", "actually", "literally",
        "oh", "well", "so", "but", "and", "or"
    ]

    # Fillers to only remove at sentence start
    SENTENCE_START_FILLERS = ["so", "but", "and", "well", "oh"]

    def __init__(self, config: TextProcessorConfig):
        super().__init__(config)
        self.fillers = self.DEFAULT_FILLERS + config.custom_filler_words
        # Build regex pattern based on aggressiveness
        self._build_patterns()

    def _build_patterns(self):
        """Build regex patterns based on configuration."""
        # Aggressiveness affects matching:
        # - Low: only exact matches with spaces
        # - Medium: matches with some variations
        # - High: matches more variations including repeated filler words

        base_fillers = [f for f in self.fillers if f not in self.SENTENCE_START_FILLERS]
        start_fillers = [f for f in self.fillers if f in self.SENTENCE_START_FILLERS]

        # Pattern for fillers in middle of text
        mid_patterns = []
        for filler in base_fillers:
            # Match with surrounding spaces/punctuation
            mid_patterns.append(r'\b' + re.escape(filler) + r'\b')

        if mid_patterns:
            self.mid_pattern = re.compile(
                r'\s*(?:' + '|'.join(mid_patterns) + r')\s*',
                re.IGNORECASE
            )
        else:
            self.mid_pattern = None

        # Pattern for fillers at sentence start
        if start_fillers:
            start_patterns = []
            for filler in start_fillers:
                start_patterns.append(r'(?:^|[.!?]\s+)' + re.escape(filler) + r'\s*')
            self.start_pattern = re.compile(
                '(' + '|'.join(start_patterns) + ')',
                re.IGNORECASE
            )
        else:
            self.start_pattern = None

    def process(self, text: str) -> str:
        """Remove filler words from text."""
        if not self.enabled or not text:
            return text

        result = text

        # Remove mid-sentence fillers based on aggressiveness
        if self.mid_pattern:
            if self.config.filler_aggressiveness < 0.3:
                # Low: only remove when surrounded by spaces
                result = self._conservative_removal(result)
            elif self.config.filler_aggressiveness < 0.7:
                # Medium: standard removal
                result = self.mid_pattern.sub(' ', result)
            else:
                # High: aggressive removal of multiple consecutive fillers
                result = self._aggressive_removal(result)

        # Remove sentence-starting fillers
        if self.start_pattern:
            result = self.start_pattern.sub(lambda m: m.group(0)[:-(m.group(0).strip().split()[-1:].__len__() or 1)], result)

        # Clean up extra spaces
        result = re.sub(r'\s+', ' ', result).strip()

        return result

    def _conservative_removal(self, text: str) -> str:
        """More conservative filler removal."""
        result = text
        for filler in ["um", "uh", "er", "ah"]:
            result = re.sub(r'\b' + re.escape(filler) + r'\b', '', result, flags=re.IGNORECASE)
        return re.sub(r'\s+', ' ', result).strip()

    def _aggressive_removal(self, text: str) -> str:
        """Aggressive removal including consecutive fillers."""
        # Remove multiple consecutive filler words
        result = self.mid_pattern.sub(' ', text)
        # Clean up any remaining multiple spaces
        return re.sub(r'\s+', ' ', result).strip()


class CapitalizationProcessor(Processor):
    """Auto-capitalizes sentences and proper nouns."""

    # Common proper nouns that should always be capitalized
    PROPER_NOUNS = {
        "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
        "january", "february", "march", "april", "may", "june", "july",
        "august", "september", "october", "november", "december",
        "english", "spanish", "french", "german", "italian", "chinese", "japanese",
        "american", "british", "canadian", "australian",
        "google", "microsoft", "apple", "amazon", "facebook", "meta",
        "python", "javascript", "github", "linux", "windows", "mac",
    }

    def __init__(self, config: TextProcessorConfig):
        super().__init__(config)
        # Build proper noun pattern
        self.proper_pattern = re.compile(
            r'\b(' + '|'.join(re.escape(n) for n in self.PROPER_NOUNS) + r')\b',
            re.IGNORECASE
        )

    def process(self, text: str) -> str:
        """Capitalize text appropriately."""
        if not self.enabled or not text:
            return text

        result = text.lower() if self.config.capitalization_style == "sentence" else text

        # Capitalize first letter of text
        if result:
            result = result[0].upper() + result[1:]

        # Capitalize after sentence endings
        result = re.sub(r'([.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), result)

        # Capitalize proper nouns
        result = self.proper_pattern.sub(lambda m: self._title_case(m.group(1)), result)

        # Capitalize "I"
        result = re.sub(r'\bi\b', 'I', result)

        return result

    def _title_case(self, word: str) -> str:
        """Convert word to title case."""
        return word.capitalize() if word else word


class PunctuationProcessor(Processor):
    """Adds automatic punctuation to unpunctuated text."""

    # Pausing words that likely indicate sentence boundaries
    PAUSE_INDICATORS = ["however", "therefore", "meanwhile", "furthermore", "anyway"]

    # Question indicators
    QUESTION_STARTERS = ["who", "what", "where", "when", "why", "how", "which", "whose", "whom"]

    def __init__(self, config: TextProcessorConfig):
        super().__init__(config)

    def process(self, text: str) -> str:
        """Add punctuation to text."""
        if not self.enabled or not text:
            return text

        result = text

        # Don't over-punctuate already punctuated text
        existing_punct = sum(1 for c in result if c in '.!?')
        word_count = len(result.split())
        if existing_punct > word_count / 5:  # Already well punctuated
            return result

        if self.config.punctuation_style == "minimal":
            result = self._add_minimal_punctuation(result)
        else:
            result = self._add_full_punctuation(result)

        return result

    def _add_minimal_punctuation(self, text: str) -> str:
        """Add minimal punctuation - just end periods."""
        result = text.rstrip()

        # Add period at end if missing
        if result and result[-1] not in '.!?':
            result += '.'

        return result

    def _add_full_punctuation(self, text: str) -> str:
        """Add more comprehensive punctuation."""
        result = text

        # Check for question patterns
        words = result.split()
        if words and words[0].lower() in self.QUESTION_STARTERS:
            if result[-1] not in '.!?':
                result += '?'
        elif result[-1] not in '.!?':
            result += '.'

        # Add commas after pause indicators
        for indicator in self.PAUSE_INDICATORS:
            result = re.sub(
                r'\b' + re.escape(indicator) + r'\s+',
                indicator + ', ',
                result,
                flags=re.IGNORECASE
            )

        return result


class NumberFormattingProcessor(Processor):
    """Formats numbers in various ways."""

    # Number words for small numbers
    NUMBER_WORDS = {
        0: "zero", 1: "one", 2: "two", 3: "three", 4: "four",
        5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
        10: "ten", 11: "eleven", 12: "twelve",
        # Could extend for larger numbers
    }

    def __init__(self, config: TextProcessorConfig):
        super().__init__(config)

    def process(self, text: str) -> str:
        """Format numbers in text."""
        if not self.enabled or not text:
            return text

        if self.config.number_style == "commas":
            return self._add_commas(text)
        elif self.config.number_style == "words":
            return self._to_words(text)
        elif self.config.number_style == "both":
            # Add comma format with words in parentheses
            return self._add_both(text)
        return text

    def _add_commas(self, text: str) -> str:
        """Add thousand separators to numbers."""
        def format_number(match):
            num = int(match.group(1))
            return f"{num:,}"

        # Match numbers 1000 and above
        return re.sub(r'\b(\d{4,})\b', format_number, text)

    def _to_words(self, text: str) -> str:
        """Convert small numbers to words."""
        def replace_small(match):
            num = int(match.group(1))
            if num in self.NUMBER_WORDS:
                return self.NUMBER_WORDS[num]
            return match.group(0)

        # Match numbers 0-12
        return re.sub(r'\b(\d+)\b', replace_small, text)

    def _add_both(self, text: str) -> str:
        """Add both comma format and word representation."""
        def format_with_words(match):
            num = int(match.group(1))
            if num in self.NUMBER_WORDS and num >= 1000:
                return f"{num:,} ({self.NUMBER_WORDS[num]})"
            elif num >= 1000:
                return f"{num:,}"
            return match.group(0)

        return re.sub(r'\b(\d{4,})\b', format_with_words, text)


class AcronymExpansionProcessor(Processor):
    """Expands common acronyms based on context."""

    # Default acronym mappings
    DEFAULT_ACRONYMS = {
        "AI": "Artificial Intelligence",
        "ML": "Machine Learning",
        "NLP": "Natural Language Processing",
        "API": "Application Programming Interface",
        "UI": "User Interface",
        "UX": "User Experience",
        "CEO": "Chief Executive Officer",
        "CTO": "Chief Technology Officer",
        "HR": "Human Resources",
        "PR": "Public Relations",
        "R&D": "Research and Development",
        "ROI": "Return on Investment",
        "SaaS": "Software as a Service",
        "APIs": "Application Programming Interfaces",
    }

    def __init__(self, config: TextProcessorConfig):
        super().__init__(config)
        # Combine default and custom acronyms
        self.acronyms = {**self.DEFAULT_ACRONYMS, **config.custom_acronyms}
        # Sort by length (longest first) to handle overlaps
        self.acronyms = dict(sorted(self.acronyms.items(), key=lambda x: -len(x[0])))
        # Build pattern
        if self.acronyms:
            pattern = r'\b(' + '|'.join(re.escape(a) for a in self.acronyms.keys()) + r')\b'
            self.pattern = re.compile(pattern)

    def process(self, text: str) -> str:
        """Expand acronyms in text (first occurrence only)."""
        if not self.enabled or not text or not self.acronyms:
            return text

        # Track which acronyms we've already expanded
        expanded = set()

        def replace_acronym(match):
            acronym = match.group(0)
            if acronym not in expanded:
                expanded.add(acronym)
                return self.acronyms.get(acronym, acronym)
            return acronym

        result = self.pattern.sub(replace_acronym, text)
        return result


class DictionaryProcessor(Processor):
    """
    Applies personal dictionary corrections to transcribed text.

    This processor loads the user's personal dictionary and applies
    corrections to commonly mis-transcribed words. Supports fuzzy
    matching for approximate corrections.
    """

    def __init__(self, config: TextProcessorConfig):
        super().__init__(config)
        self.dictionary = None
        self._load_dictionary()

    def _load_dictionary(self):
        """Load the personal dictionary (lazy loading)."""
        try:
            from .dictionary import load_dictionary
            self.dictionary = load_dictionary()
            logger.info("Personal dictionary loaded for text processing")
        except ImportError:
            logger.warning("Dictionary module not available, dictionary processor disabled")
            self.enabled = False
        except Exception as e:
            logger.warning(f"Failed to load dictionary: {e}")
            self.dictionary = None

    def reload_dictionary(self):
        """Reload the dictionary from disk."""
        self._load_dictionary()

    def process(self, text: str) -> str:
        """Apply dictionary corrections to text."""
        if not self.enabled or not text or not self.dictionary:
            return text

        try:
            use_fuzzy = getattr(self.config, 'dictionary_fuzzy_matching', True)
            result = self.dictionary.apply_corrections(text, use_fuzzy=use_fuzzy)
            return result
        except Exception as e:
            logger.warning(f"Dictionary processor error: {e}")
            return text


class ToneStyleProcessor(Processor):
    """
    Adjusts text to match specific writing style presets.

    Supports rule-based post-processing for different tones:
    - Professional: Formal language, complete sentences, business-appropriate
    - Casual: Conversational, emoticons permitted, abbreviations allowed
    - Technical: Preserves jargon, precise terminology, technical accuracy
    - Concise: Removes fluff, shortens expressions, gets to the point
    - Creative: Elaborate descriptions, varied vocabulary, engaging style
    - Neutral: No modifications (default)
    """

    # Tone preset definitions with transformations
    TONE_PRESETS = {
        "neutral": {
            "name": "Neutral",
            "description": "No modifications to tone or style",
        },
        "professional": {
            "name": "Professional",
            "description": "Formal language suitable for business communication",
            "contractions_remove": True,
            "informal_remove": True,
            "complete_sentences": True,
        },
        "casual": {
            "name": "Casual",
            "description": "Conversational style with relaxed language",
            "emoticons_add": True,
            "abbreviations_allow": True,
            "contractions_allow": True,
        },
        "technical": {
            "name": "Technical",
            "description": "Preserves technical jargon and precise terminology",
            "jargon_preserve": True,
            "precise_units": True,
            "abbreviations_allow": True,
        },
        "concise": {
            "name": "Concise",
            "description": "Removes unnecessary words and fluff",
            "fluff_remove": True,
            "repetitions_remove": True,
            "shorten_expressions": True,
        },
        "creative": {
            "name": "Creative",
            "description": "Elaborate and engaging style with varied vocabulary",
            "elaborate": True,
            "varied_vocabulary": True,
            "descriptive": True,
        },
    }

    # Informal words to remove for professional tone
    INFORMAL_WORDS = [
        "gonna", "wanna", "gotta", "kinda", "sorta", "lemme", "gimme",
        "dunno", "cuz", "tho", "ya", "hey", "hi", "hello",
    ]

    # Filler phrases to remove for concise tone
    FLUFF_PHRASES = [
        r"\bi think\b",
        r"\bi believe\b",
        r"\bit seems to me\b",
        r"\bas far as i'm concerned\b",
        r"\bfor all intents and purposes\b",
        r"\bat the end of the day\b",
        r"\bin order to\b",
        r"\bdue to the fact that\b",
        r"\bbasically\b",
        r"\bactually\b",
        r"\breally\b",
        r"\bjust\b",
        r"\bsome\s+(?:sort|kind)\s+of\b",
    ]

    # Repetitive patterns to remove
    REPETITION_PATTERNS = [
        r"\b(\w+)\s+\1\b",  # Repeated words
        r"(.{10,}?)\1+",    # Repeated phrases (10+ chars)
    ]

    # Word shortening for concise tone
    EXPRESSION_SHORTENINGS = {
        r"\bat this point in time\b": "now",
        r"\bin the event that\b": "if",
        r"\bfor the purpose of\b": "to",
        r"\bon a (?:daily|regular|weekly) basis\b": r"daily/weekly",
        r"\bduring the course of\b": "during",
        r"\bwith regard to\b": "about",
        r"\bin regards to\b": "about",
        r"\bwith respect to\b": "about",
        r"\bin the near future\b": "soon",
        r"\bat the present time\b": "now",
        r"\bhave a tendency to\b": "tend to",
        r"\bis able to\b": "can",
        r"\bare able to\b": "can",
    }

    # Contractions to expand for professional tone
    CONTRACTIONS_MAP = {
        "can't": "cannot",
        "won't": "will not",
        "don't": "do not",
        "doesn't": "does not",
        "didn't": "did not",
        "isn't": "is not",
        "aren't": "are not",
        "wasn't": "was not",
        "weren't": "were not",
        "haven't": "have not",
        "hasn't": "has not",
        "hadn't": "had not",
        "wouldn't": "would not",
        "couldn't": "could not",
        "shouldn't": "should not",
        "i'm": "I am",
        "i've": "I have",
        "i'll": "I will",
        "i'd": "I would",
        "you're": "you are",
        "you've": "you have",
        "you'll": "you will",
        "you'd": "you would",
        "he's": "he is",
        "she's": "she is",
        "it's": "it is",
        "we're": "we are",
        "we've": "we have",
        "we'll": "we will",
        "we'd": "we would",
        "they're": "they are",
        "they've": "they have",
        "they'll": "they will",
        "they'd": "they would",
        "that's": "that is",
        "there's": "there is",
        "here's": "here is",
        "what's": "what is",
        "let's": "let us",
        "who's": "who is",
        "how's": "how is",
        "why's": "why is",
        "when's": "when is",
        "where's": "where is",
    }

    def __init__(self, config: TextProcessorConfig):
        super().__init__(config)
        self.tone_preset = getattr(config, 'tone_preset', 'neutral')
        self._build_patterns()

    def _build_patterns(self):
        """Build regex patterns based on current tone preset."""
        preset = self.TONE_PRESETS.get(self.tone_preset, self.TONE_PRESETS["neutral"])

        # Build informal word pattern for professional tone
        if preset.get("informal_remove"):
            self.informal_pattern = re.compile(
                r'\b(' + '|'.join(re.escape(w) for w in self.INFORMAL_WORDS) + r')\b',
                re.IGNORECASE
            )
        else:
            self.informal_pattern = None

        # Build fluff removal pattern for concise tone
        if preset.get("fluff_remove"):
            self.fluff_patterns = [
                re.compile(p, re.IGNORECASE) for p in self.FLUFF_PHRASES
            ]
        else:
            self.fluff_patterns = None

        # Build repetition removal patterns
        if preset.get("repetitions_remove"):
            self.repetition_patterns = [
                re.compile(p, re.IGNORECASE) for p in self.REPETITION_PATTERNS
            ]
        else:
            self.repetition_patterns = None

        # Build contraction patterns
        if preset.get("contractions_remove"):
            # Pattern to match contractions
            contractions = sorted(self.CONTRACTIONS_MAP.keys(), key=len, reverse=True)
            self.contraction_pattern = re.compile(
                r'\b(' + '|'.join(re.escape(c) for c in contractions) + r')\b',
                re.IGNORECASE
            )
        else:
            self.contraction_pattern = None

        # Build expression shortening patterns
        if preset.get("shorten_expressions"):
            patterns = []
            for long_form, short_form in self.EXPRESSION_SHORTENINGS.items():
                pattern = re.compile(re.escape(long_form), re.IGNORECASE)
                patterns.append((pattern, short_form))
            self.shortening_patterns = patterns
        else:
            self.shortening_patterns = None

    def process(self, text: str) -> str:
        """Process text according to the tone preset."""
        if not self.enabled or not text:
            return text

        preset = self.TONE_PRESETS.get(self.tone_preset, self.TONE_PRESETS["neutral"])

        result = text

        # Apply transformations based on preset
        if preset.get("contractions_remove"):
            result = self._remove_contractions(result)

        if preset.get("informal_remove"):
            result = self._remove_informal(result)

        if preset.get("fluff_remove"):
            result = self._remove_fluff(result)

        if preset.get("repetitions_remove"):
            result = self._remove_repetitions(result)

        if preset.get("shorten_expressions"):
            result = self._shorten_expressions(result)

        if preset.get("complete_sentences"):
            result = self._ensure_complete_sentences(result)

        if preset.get("emoticons_add"):
            result = self._add_emoticons(result)

        # For creative tone, add descriptive elements
        if preset.get("elaborate"):
            result = self._elaborate(result)

        # Clean up extra spaces
        result = re.sub(r'\s+', ' ', result).strip()

        return result

    def _remove_contractions(self, text: str) -> str:
        """Expand contractions for formal tone."""
        if not self.contraction_pattern:
            return text

        def replace(match):
            contraction = match.group(0)
            # Preserve original case in replacement
            expanded = self.CONTRACTIONS_MAP.get(contraction.lower(), contraction)
            if contraction[0].isupper():
                return expanded[0].upper() + expanded[1:]
            return expanded

        return self.contraction_pattern.sub(replace, text)

    def _remove_informal(self, text: str) -> str:
        """Remove informal words and expressions."""
        if not self.informal_pattern:
            return text
        return self.informal_pattern.sub('', text)

    def _remove_fluff(self, text: str) -> str:
        """Remove filler phrases and unnecessary words."""
        if not self.fluff_patterns:
            return text

        result = text
        for pattern in self.fluff_patterns:
            result = pattern.sub('', result)
        return result

    def _remove_repetitions(self, text: str) -> str:
        """Remove repeated words and phrases."""
        if not self.repetition_patterns:
            return text

        result = text
        for pattern in self.repetition_patterns:
            result = pattern.sub(r'\1', result)
        return result

    def _shorten_expressions(self, text: str) -> str:
        """Replace wordy expressions with shorter alternatives."""
        if not self.shortening_patterns:
            return text

        result = text
        for pattern, replacement in self.shortening_patterns:
            result = pattern.sub(replacement, result)
        return result

    def _ensure_complete_sentences(self, text: str) -> str:
        """Ensure sentences are complete with proper endings."""
        result = text.rstrip()

        # Add proper ending if missing
        if result and result[-1] not in '.!?':
            result += '.'

        return result

    def _add_emoticons(self, text: str) -> str:
        """Add contextual emoticons for casual tone (placeholder for future enhancement)."""
        # This is a simple placeholder - future enhancement could use sentiment analysis
        # to add appropriate emoticons based on emotional content
        return text

    def _elaborate(self, text: str) -> str:
        """Add descriptive elements for creative tone (placeholder for future enhancement)."""
        # This is a placeholder - future LLM integration could provide true style transfer
        # For now, we maintain the text as-is since rule-based creative expansion
        # would likely produce poor results
        return text

    def set_tone_preset(self, preset: str):
        """Change the tone preset and rebuild patterns."""
        if preset not in self.TONE_PRESETS:
            logger.warning(f"Unknown tone preset: {preset}, using 'neutral'")
            preset = "neutral"

        self.tone_preset = preset
        self._build_patterns()


class MixedLanguageProcessor(Processor):
    """
    Processes mixed-language text using language detection.

    Detects language changes within text and applies language-specific
    processing (like dictionary corrections) to each segment.
    """

    def __init__(self, config: TextProcessorConfig):
        super().__init__(config)
        self.language_detector = None
        self.dictionary_getter = None
        self.default_language = "en"
        self._init_language_detector()

    def _init_language_detector(self):
        """Initialize the language detector."""
        try:
            from .language_detector import LanguageDetector
            self.language_detector = LanguageDetector()
            logger.info("Mixed language processor initialized with language detector")
        except ImportError:
            logger.warning("Language detector not available, mixed-language processing disabled")
            self.enabled = False

    def set_dictionary_getter(self, getter):
        """Set a function that returns a dictionary for a given language code."""
        self.dictionary_getter = getter

    def set_default_language(self, language: str):
        """Set the default language for segments with 'auto' detection."""
        self.default_language = language

    def process(self, text: str) -> str:
        """Process text with language-specific corrections."""
        if not self.enabled or not text or not self.language_detector:
            return text

        # Split text by language
        segments = self.language_detector.detect_segments(text)

        if not segments:
            return text

        # Process each segment with language-specific dictionary
        processed_segments = []
        for segment in segments:
            lang = segment.language if segment.language != "auto" else self.default_language
            segment_text = segment.text

            # Apply language-specific dictionary corrections if available
            if self.dictionary_getter:
                try:
                    dictionary = self.dictionary_getter(lang)
                    if dictionary and hasattr(dictionary, 'apply_corrections_for_language'):
                        segment_text = dictionary.apply_corrections_for_language(
                            segment_text, lang, use_fuzzy=True
                        )
                except Exception as e:
                    logger.debug(f"Language-specific correction failed for {lang}: {e}")

            processed_segments.append(segment_text)

        # Rejoin segments
        return " ".join(processed_segments)


class TranslationShortcutProcessor(Processor):
    """
    Processes translation shortcuts in text.

    Detects and executes translation commands like
    "translate to Spanish: hello world" or "traducir al inglés: hola mundo".
    """

    def __init__(self, config: TextProcessorConfig):
        super().__init__(config)
        self.translation_manager = None
        self._init_translation_manager()

    def _init_translation_manager(self):
        """Initialize the translation shortcuts manager."""
        try:
            from .translation_shortcuts import TranslationShortcutsManager
            self.translation_manager = TranslationShortcutsManager(enabled=True)
            logger.info("Translation shortcut processor initialized")
        except ImportError:
            logger.warning("Translation shortcuts not available")
            self.enabled = False

    def process(self, text: str) -> str:
        """Process text, executing translation commands."""
        if not self.enabled or not text or not self.translation_manager:
            return text

        # Check if this is a translation command
        processed, result = self.translation_manager.process_text(text)

        if result:
            # Record the translation as a correction
            self._add_correction(
                correction_type="translation",
                original=result.original_text,
                corrected=result.translated_text,
                confidence=result.confidence if result.success else 0.0
            )

            if not result.success:
                logger.warning(f"Translation failed: {result.error}")

        return processed

    def set_translation_provider(self, provider):
        """Set a custom translation provider function."""
        if self.translation_manager:
            self.translation_manager.translation_provider = provider


class TextProcessor:
    """
    Main text processing pipeline coordinator.

    Applies a series of processors to transcribed text based on configuration.
    Each processor can be toggled on/off and has its own sensitivity settings.

    Example
    -------
    >>> config = TextProcessorConfig(
    ...     remove_filler_words=True,
    ...     auto_capitalize=True,
    ...     filler_aggressiveness=0.7
    ... )
    >>> processor = TextProcessor(config)
    >>> result = processor.process("um hello world this is a test")
    >>> print(result)
    "Hello world. This is a test."
    """

    def __init__(self, config: Optional[TextProcessorConfig] = None):
        """
        Initialize the text processor with optional configuration.

        Parameters
        ----------
        config : TextProcessorConfig, optional
            Configuration for the pipeline. If None, uses defaults.
        """
        self.config = config or TextProcessorConfig()
        self._init_processors()

    def _init_processors(self):
        """Initialize processor instances based on config."""
        self.processors = []

        # Initialize processors in order
        self.filler_processor = FillerWordProcessor(self.config)
        self.filler_processor.enabled = self.config.remove_filler_words
        self.processors.append(self.filler_processor)

        self.capitalization_processor = CapitalizationProcessor(self.config)
        self.capitalization_processor.enabled = self.config.auto_capitalize
        self.processors.append(self.capitalization_processor)

        self.punctuation_processor = PunctuationProcessor(self.config)
        self.punctuation_processor.enabled = self.config.auto_punctuate
        self.processors.append(self.punctuation_processor)

        self.number_processor = NumberFormattingProcessor(self.config)
        self.number_processor.enabled = self.config.format_numbers
        self.processors.append(self.number_processor)

        self.acronym_processor = AcronymExpansionProcessor(self.config)
        self.acronym_processor.enabled = self.config.expand_acronyms
        self.processors.append(self.acronym_processor)

        # Tone style processor - runs before dictionary for style adjustments
        self.tone_style_processor = ToneStyleProcessor(self.config)
        self.tone_style_processor.enabled = getattr(self.config, 'tone_preset_enabled', False)
        self.processors.append(self.tone_style_processor)

        # Translation shortcuts processor - runs before dictionary
        self.translation_shortcuts_processor = TranslationShortcutProcessor(self.config)
        self.translation_shortcuts_processor.enabled = getattr(self.config, 'enable_translation_shortcuts', False)
        self.processors.append(self.translation_shortcuts_processor)

        # Mixed language processor - applies language-specific dictionary corrections
        self.mixed_language_processor = MixedLanguageProcessor(self.config)
        self.mixed_language_processor.enabled = getattr(self.config, 'enable_mixed_language', False)
        # Set default language from config
        self.mixed_language_processor.set_default_language(
            getattr(self.config, 'default_language', 'en')
        )
        self.processors.append(self.mixed_language_processor)

        # Dictionary processor - runs last to apply final corrections
        self.dictionary_processor = DictionaryProcessor(self.config)
        self.dictionary_processor.enabled = getattr(self.config, 'use_dictionary', True)
        self.processors.append(self.dictionary_processor)

    def process(self, text: str) -> str:
        """
        Process text through the enabled processors.

        Parameters
        ----------
        text : str
            The input text to process.

        Returns
        -------
        str
            The processed text.
        """
        if not text:
            return text

        result = text
        for processor in self.processors:
            if processor.enabled:
                try:
                    result = processor.process(result)
                except Exception as e:
                    logger.warning(f"Processor {processor.__class__.__name__} failed: {e}")

        return result

    def process_with_tracking(self, text: str) -> Tuple[str, List[Correction]]:
        """
        Process text through the enabled processors and track all corrections.

        Parameters
        ----------
        text : str
            The input text to process.

        Returns
        -------
        Tuple[str, List[Correction]]
            The processed text and list of all corrections made.
        """
        if not text:
            return text, []

        result = text
        all_corrections: List[Correction] = []

        for processor in self.processors:
            if processor.enabled:
                try:
                    processed, corrections = processor.process_with_tracking(result)
                    result = processed
                    all_corrections.extend(corrections)
                except Exception as e:
                    logger.warning(f"Processor {processor.__class__.__name__} failed: {e}")

        return result, all_corrections

    def preview(self, text: str) -> Dict[str, str]:
        """
        Show before/after for each processor.

        Returns a dictionary with the result after each processing step.

        Parameters
        ----------
        text : str
            The input text to preview.

        Returns
        -------
        Dict[str, str]
            Dictionary with 'original' and keys for each processor name.
        """
        result = {"original": text}
        current = text

        for processor in self.processors:
            if processor.enabled:
                try:
                    current = processor.process(current)
                    result[processor.__class__.__name__] = current
                except Exception as e:
                    logger.warning(f"Processor {processor.__class__.__name__} failed: {e}")
                    result[processor.__class__.__name__] = current + f" [Error: {e}]"

        result["final"] = current
        return result

    def update_config(self, **kwargs):
        """
        Update configuration and reinitialize processors.

        Parameters
        ----------
        **kwargs
            Configuration keys to update.
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self._init_processors()

    def get_config(self) -> TextProcessorConfig:
        """Get current configuration."""
        return self.config

    def set_processor_enabled(self, processor_name: str, enabled: bool):
        """
        Enable or disable a specific processor.

        Parameters
        ----------
        processor_name : str
            Name of the processor class (e.g., 'FillerWordProcessor')
        enabled : bool
            Whether to enable the processor
        """
        for processor in self.processors:
            if processor.__class__.__name__ == processor_name:
                processor.enabled = enabled
                return
        logger.warning(f"Processor {processor_name} not found")

    def reload_dictionary(self):
        """Reload the personal dictionary from disk."""
        if hasattr(self, 'dictionary_processor'):
            self.dictionary_processor.reload_dictionary()
            logger.info("Dictionary reloaded")
