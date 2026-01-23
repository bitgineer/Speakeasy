"""
Translation shortcuts system for faster-whisper-hotkey.

This module provides voice-activated translation commands like
"translate to Spanish" or "traducir al inglés" with automatic
language detection and translation.

Classes
-------
TranslationShortcut
    Represents a translation command pattern.

TranslationShortcutsManager
    Manages translation shortcuts and executes translations.

TranslationResult
    Dataclass for translation results.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Callable, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


# Language name mappings (English -> ISO code)
LANGUAGE_NAME_TO_CODE = {
    "english": "en",
    "spanish": "es",
    "french": "fr",
    "german": "de",
    "italian": "it",
    "portuguese": "pt",
    "dutch": "nl",
    "polish": "pl",
    "russian": "ru",
    "arabic": "ar",
    "chinese": "zh",
    "japanese": "ja",
    "korean": "ko",
    "hindi": "hi",
    "swedish": "sv",
    "danish": "da",
    "norwegian": "no",
    "finnish": "fi",
    "turkish": "tr",
    "czech": "cs",
    "greek": "el",
    "hebrew": "he",
    "thai": "th",
    "vietnamese": "vi",
    "indonesian": "id",
    "ukrainian": "uk",
    "romanian": "ro",
    "hungarian": "hu",
    "catalan": "ca",
    "filipino": "tl",
    "ukrainian": "uk",
}

# Language name mappings in other languages
TRANSLATION_LANGUAGE_ALIASES = {
    # Spanish
    "español": "es", "espanol": "es", "castellano": "es",
    "inglés": "en", "ingles": "en",
    "francés": "fr", "frances": "fr",
    "alemán": "de", "aleman": "de",
    "italiano": "it",
    "portugués": "pt", "portugues": "pt",

    # French
    "anglais": "en",
    "espagnol": "es",
    "allemand": "de",
    "italien": "it",

    # German
    "englisch": "en",
    "spanisch": "es",
    "französisch": "fr",
    "italienisch": "it",

    # Italian
    "inglese": "en",
    "spagnolo": "es",
    "francese": "fr",
    "tedesco": "de",

    # Portuguese
    "inglês": "en", "ingles": "en",
    "espanhol": "es",
    "francês": "fr", "frances": "fr",
    "alemão": "de", "alemao": "de",
}


@dataclass
class TranslationResult:
    """Result of a translation operation."""
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    confidence: float = 1.0
    success: bool = True
    error: Optional[str] = None


@dataclass
class TranslationShortcut:
    """A translation command pattern."""
    # Regex pattern to match the command
    pattern: str

    # Target language code extracted from pattern
    target_language: str

    # Source language (None = auto-detect)
    source_language: Optional[str] = None

    # Priority for matching (higher = checked first)
    priority: int = 0

    # Whether this pattern is case-sensitive
    case_sensitive: bool = False

    # Example usage
    example: str = ""

    def matches(self, text: str) -> Optional[re.Match]:
        """Check if text matches this shortcut pattern."""
        flags = 0 if self.case_sensitive else re.IGNORECASE
        match = re.match(self.pattern, text.strip(), flags)
        return match

    def extract_text_to_translate(self, text: str, match: re.Match) -> str:
        """Extract the actual text to translate from the matched command."""
        # Default: get everything after the command pattern
        remaining = text[match.end():].strip()
        # Remove common separator words
        for sep in [":", "-", "–", "—", "is", "means", "say"]:
            if remaining.lower().startswith(sep):
                remaining = remaining[len(sep):].strip()
                break
        return remaining


class TranslationShortcutsManager:
    """
    Manages translation shortcuts and executes translations.

    Supports voice commands like:
    - "translate to Spanish: hello world"
    - "traducir al inglés: hola mundo"
    - "translate hello world to German"
    """

    # Default translation patterns
    DEFAULT_PATTERNS = [
        # English patterns
        (r'^translate\s+(.+?)\s+to\s+(\w+)(?:\s*:?\s*(.*))?$', 1, 2),
        (r'^translate\s+to\s+(\w+)\s*:?\s*(.*)$', 0, 1),
        (r'^translate\s*:?\s*(.*)\s+to\s+(\w+)$', 1, 2),
        (r'^(.+?)\s+translate\s+to\s+(\w+)$', 1, 2),

        # Spanish patterns
        (r'^traducir\s+(.+?)\s+a\s+(?:el\s+)?(\w+)(?:\s*:?\s*(.*))?$', 1, 2),
        (r'^traducir\s+a\s+(?:el\s+)?(\w+)\s*:?\s*(.*)$', 0, 1),

        # French patterns
        (r'^traduire\s+(.+?)\s+(?:en|au)\s+(\w+)(?:\s*:?\s*(.*))?$', 1, 2),
        (r'^traduire\s+(?:en|au)\s+(\w+)\s*:?\s*(.*)$', 0, 1),
    ]

    def __init__(
        self,
        translation_provider: Optional[Callable] = None,
        enabled: bool = True,
        confidence_threshold: float = 0.5
    ):
        """
        Initialize the translation shortcuts manager.

        Parameters
        ----------
        translation_provider : callable, optional
            Function that performs translation.
            Signature: (text: str, target_lang: str, source_lang: str = None) -> str
            If None, uses a simple mock translation.
        enabled : bool
            Whether translation shortcuts are enabled.
        confidence_threshold : float
            Minimum confidence for accepting a shortcut match.
        """
        self.enabled = enabled
        self.confidence_threshold = confidence_threshold
        self.translation_provider = translation_provider or self._default_translation
        self.shortcuts: List[TranslationShortcut] = []
        self._build_default_shortcuts()

    def _build_default_shortcuts(self):
        """Build the default translation shortcut patterns."""
        self.shortcuts = []

        # English patterns
        self.shortcuts.append(TranslationShortcut(
            pattern=r'^translate\s+to\s+([a-zA-ZáéíóúñÁÉÍÓÚÑ]+)\s*:?\s*(.*)$',
            target_language="",  # Will be extracted from group 1
            example="translate to Spanish: hello world"
        ))
        self.shortcuts.append(TranslationShortcut(
            pattern=r'^translate\s+(.+?)\s+to\s+([a-zA-ZáéíóúñÁÉÍÓÚÑ]+)(?:\s*:?\s*(.*))?$',
            target_language="",  # Will be extracted from group 2
            example="translate hello world to Spanish"
        ))

        # Spanish patterns
        self.shortcuts.append(TranslationShortcut(
            pattern=r'^traducir\s+(?:a\s+(?:el\s+)?|al\s+)([a-zA-ZáéíóúñÁÉÍÓÚÑ]+)\s*:?\s*(.*)$',
            target_language="",
            example="traducir al inglés: hola mundo"
        ))
        self.shortcuts.append(TranslationShortcut(
            pattern=r'^traducir\s+(.+?)\s+(?:a\s+(?:el\s+)?|al\s+)([a-zA-ZáéíóúñÁÉÍÓÚÑ]+)(?:\s*:?\s*(.*))?$',
            target_language="",
            example="traducir hola mundo al inglés"
        ))

        # French patterns
        self.shortcuts.append(TranslationShortcut(
            pattern=r'^traduire\s+(?:en|au)\s+([a-zA-ZàâäéèêëïîôùûüÿçÀÂÄÉÈÊËÏÎÔÙÛÜŸÇ]+)\s*:?\s*(.*)$',
            target_language="",
            example="traduire en anglais: bonjour le monde"
        ))

    def parse_translation_command(self, text: str) -> Optional[Tuple[str, str, str]]:
        """
        Parse a translation command from text.

        Parameters
        ----------
        text : str
            Text to parse.

        Returns
        -------
        Tuple[str, str, str] or None
            (text_to_translate, target_lang, source_lang) if a command is found,
            None otherwise.
        """
        if not self.enabled or not text:
            return None

        for shortcut in self.shortcuts:
            match = shortcut.matches(text)
            if match:
                # Extract target language
                target_lang_name = match.group(1).lower().strip()
                target_lang = self._resolve_language_code(target_lang_name)

                if not target_lang:
                    logger.debug(f"Could not resolve target language: {target_lang_name}")
                    continue

                # Extract text to translate
                if match.lastindex >= 2 and match.group(2):
                    text_to_translate = match.group(2).strip()
                else:
                    # No text in command, will need to be provided separately
                    text_to_translate = ""

                source_lang = shortcut.source_language or "auto"

                if text_to_translate:
                    return text_to_translate, target_lang, source_lang

        return None

    def is_translation_command(self, text: str) -> bool:
        """
        Check if text is a translation command.

        Parameters
        ----------
        text : str
            Text to check.

        Returns
        -------
        bool
            True if text matches a translation shortcut pattern.
        """
        return self.parse_translation_command(text) is not None

    def translate(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> TranslationResult:
        """
        Translate text to target language.

        Parameters
        ----------
        text : str
            Text to translate.
        target_language : str
            Target language code (e.g., "en", "es", "fr").
        source_language : str, optional
            Source language code. If None, auto-detects.

        Returns
        -------
        TranslationResult
            Translation result with original text, translation, and metadata.
        """
        if not text:
            return TranslationResult(
                original_text=text,
                translated_text="",
                source_language=source_language or "auto",
                target_language=target_language,
                success=False,
                error="No text to translate"
            )

        try:
            translated = self.translation_provider(
                text, target_language, source_language
            )

            return TranslationResult(
                original_text=text,
                translated_text=translated,
                source_language=source_language or "auto",
                target_language=target_language,
                success=True
            )

        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return TranslationResult(
                original_text=text,
                translated_text=text,  # Return original on failure
                source_language=source_language or "auto",
                target_language=target_language,
                success=False,
                error=str(e)
            )

    def process_text(self, text: str) -> Tuple[str, Optional[TranslationResult]]:
        """
        Process text, checking for translation commands.

        Parameters
        ----------
        text : str
            Text to process.

        Returns
        -------
        Tuple[str, TranslationResult or None]
            (processed_text, translation_result) tuple.
            If text is a translation command, returns the translation.
            Otherwise returns original text with None result.
        """
        parsed = self.parse_translation_command(text)

        if parsed:
            text_to_translate, target_lang, source_lang = parsed
            result = self.translate(text_to_translate, target_lang, source_lang)

            if result.success:
                logger.info(f"Translated '{text_to_translate}' to {target_lang}: {result.translated_text}")
                return result.translated_text, result
            else:
                logger.warning(f"Translation failed: {result.error}")
                return text, result

        return text, None

    def _resolve_language_code(self, name: str) -> Optional[str]:
        """
        Resolve language name to ISO code.

        Parameters
        ----------
        name : str
            Language name (in various languages).

        Returns
        -------
        str or None
            ISO language code or None if not found.
        """
        name_lower = name.lower()

        # Direct lookup
        if name_lower in LANGUAGE_NAME_TO_CODE:
            return LANGUAGE_NAME_TO_CODE[name_lower]

        # Check aliases
        if name_lower in TRANSLATION_LANGUAGE_ALIASES:
            return TRANSLATION_LANGUAGE_ALIASES[name_lower]

        # Check if already a code
        if len(name_lower) == 2 and name_lower in LANGUAGE_NAME_TO_CODE.values():
            return name_lower

        return None

    def _default_translation(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> str:
        """
        Default (mock) translation provider.

        In a real implementation, this would use an actual translation API.
        For now, it returns a placeholder indicating translation would occur.

        Parameters
        ----------
        text : str
            Text to translate.
        target_language : str
            Target language code.
        source_language : str, optional
            Source language code.

        Returns
        -------
        str
            "Translated" text (placeholder).
        """
        # Try to use a real translation library if available
        try:
            # Check for googletrans (common Python translation library)
            from googletrans import Translator
            translator = Translator()
            result = translator.translate(text, dest=target_language, src=source_language or "auto")
            return result.text
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Translation API unavailable: {e}")

        # Fallback: return text with translation indicator
        lang_name = self._get_language_name(target_language)
        return f"[Translated to {lang_name}: {text}]"

    def _get_language_name(self, code: str) -> str:
        """Get human-readable language name from code."""
        for name, c in LANGUAGE_NAME_TO_CODE.items():
            if c == code:
                return name.capitalize()
        return code.upper()

    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported target languages.

        Returns
        -------
        List[str]
            List of language names.
        """
        return sorted(set(LANGUAGE_NAME_TO_CODE.keys()) | set(TRANSLATION_LANGUAGE_ALIASES()))

    def get_supported_language_codes(self) -> List[str]:
        """
        Get list of supported language codes.

        Returns
        -------
        List[str]
            List of ISO language codes.
        """
        return sorted(set(LANGUAGE_NAME_TO_CODE.values()) | set(TRANSLATION_LANGUAGE_ALIASES.values()))


def get_translation_shortcuts_manager(
    translation_provider: Optional[Callable] = None,
    enabled: bool = True
) -> TranslationShortcutsManager:
    """
    Get the global translation shortcuts manager instance.

    Parameters
    ----------
    translation_provider : callable, optional
        Custom translation provider function.
    enabled : bool
        Whether shortcuts are enabled.

    Returns
    -------
    TranslationShortcutsManager
        The manager instance.
    """
    return TranslationShortcutsManager(
        translation_provider=translation_provider,
        enabled=enabled
    )


# Convenience function for one-off translations
def quick_translate(
    text: str,
    target_language: str,
    source_language: Optional[str] = None
) -> str:
    """
    Quick translation function.

    Parameters
    ----------
    text : str
        Text to translate.
    target_language : str
        Target language code or name.
    source_language : str, optional
        Source language code or name.

    Returns
    -------
    str
        Translated text.
    """
    manager = get_translation_shortcuts_manager()

    # Resolve language names to codes
    if len(target_language) > 2:
        target_language = manager._resolve_language_code(target_language) or target_language
    if source_language and len(source_language) > 2:
        source_language = manager._resolve_language_code(source_language) or source_language

    result = manager.translate(text, target_language, source_language)
    return result.translated_text if result.success else text
