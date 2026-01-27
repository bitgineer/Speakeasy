"""
Model configuration and available models/languages.

Loads model definitions from the bundled JSON file.
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Load configuration from JSON file
_DATA_DIR = Path(__file__).parent.parent / "data"
_CONFIG_FILE = _DATA_DIR / "available_models_languages.json"


def _load_config() -> dict:
    """Load the configuration from JSON file."""
    if not _CONFIG_FILE.exists():
        logger.warning(f"Config file not found: {_CONFIG_FILE}")
        return {}

    with open(_CONFIG_FILE, "r") as f:
        return json.load(f)


_config = _load_config()

# Whisper models from faster-whisper
WHISPER_MODELS: list[str] = _config.get(
    "accepted_models_whisper",
    [
        "tiny",
        "tiny.en",
        "base",
        "base.en",
        "small",
        "small.en",
        "medium",
        "medium.en",
        "large-v1",
        "large-v2",
        "large-v3",
        "large-v3-turbo",
        "turbo",
        "distil-large-v2",
        "distil-medium.en",
        "distil-small.en",
        "distil-large-v3",
    ],
)

# All supported languages for Whisper
WHISPER_LANGUAGES: list[str] = _config.get(
    "accepted_languages_whisper",
    [
        "auto",
        "en",
        "zh",
        "de",
        "es",
        "ru",
        "ko",
        "fr",
        "ja",
        "pt",
        "tr",
        "pl",
        "ca",
        "nl",
        "ar",
        "sv",
        "it",
        "id",
        "hi",
        "fi",
        "vi",
        "he",
        "uk",
        "el",
        "ms",
        "cs",
        "ro",
        "da",
        "hu",
        "ta",
        "no",
        "th",
        "ur",
        "hr",
        "bg",
        "lt",
        "la",
        "mi",
        "ml",
        "cy",
        "sk",
        "te",
        "fa",
        "lv",
        "bn",
        "sr",
        "az",
        "sl",
        "kn",
        "et",
        "mk",
        "br",
        "eu",
        "is",
        "hy",
        "ne",
        "mn",
        "bs",
        "kk",
        "sq",
        "sw",
        "gl",
        "mr",
        "pa",
        "si",
        "km",
        "sn",
        "yo",
        "so",
        "af",
        "oc",
        "ka",
        "be",
        "tg",
        "sd",
        "gu",
        "am",
        "yi",
        "lo",
        "uz",
        "fo",
        "ht",
        "ps",
        "tk",
        "nn",
        "mt",
        "sa",
        "lb",
        "my",
        "bo",
        "tl",
        "mg",
        "as",
        "tt",
        "haw",
        "ln",
        "ha",
        "ba",
        "jw",
        "su",
    ],
)

# English-only Whisper models
WHISPER_ENGLISH_ONLY: list[str] = _config.get(
    "english_only_models_whisper",
    [
        "tiny.en",
        "base.en",
        "small.en",
        "medium.en",
        "distil-medium.en",
        "distil-small.en",
    ],
)

# Canary source-target language pairs
CANARY_LANGUAGES: dict[str, list[str]] = _config.get(
    "canary_source_target_languages",
    {
        "en": ["en", "de", "es", "fr"],
        "de": ["de", "en"],
        "es": ["es", "en"],
        "fr": ["fr", "en"],
    },
)

# Allowed Canary language pairs
CANARY_LANGUAGE_PAIRS: list[str] = _config.get(
    "canary_allowed_language_pairs",
    [
        "en-en",
        "en-de",
        "en-es",
        "en-fr",
        "de-de",
        "de-en",
        "es-es",
        "es-en",
        "fr-fr",
        "fr-en",
    ],
)

# Parakeet supported languages (25 European languages)
PARAKEET_LANGUAGES: list[str] = [
    "auto",  # Auto-detection
    "bg",
    "hr",
    "cs",
    "da",
    "nl",
    "en",
    "et",
    "fi",
    "fr",
    "de",
    "el",
    "hu",
    "it",
    "lv",
    "lt",
    "mt",
    "pl",
    "pt",
    "ro",
    "sk",
    "sl",
    "es",
    "sv",
    "ru",
    "uk",
]

# Voxtral supported languages
VOXTRAL_LANGUAGES: list[str] = [
    "auto",
    "en",
    "es",
    "fr",
    "pt",
    "hi",
    "de",
    "nl",
    "it",
]


# Model metadata for UI display
MODEL_INFO = {
    "whisper": {
        "name": "Faster-Whisper",
        "description": "OpenAI Whisper via CTranslate2 - Wide language support",
        "models": {
            "tiny": {"vram_gb": 1, "speed": "fastest", "accuracy": "low"},
            "base": {"vram_gb": 1, "speed": "very fast", "accuracy": "fair"},
            "small": {"vram_gb": 2, "speed": "fast", "accuracy": "good"},
            "medium": {"vram_gb": 5, "speed": "medium", "accuracy": "very good"},
            "large-v3": {"vram_gb": 10, "speed": "slow", "accuracy": "excellent"},
            "large-v3-turbo": {"vram_gb": 6, "speed": "fast", "accuracy": "excellent"},
            "turbo": {"vram_gb": 6, "speed": "fast", "accuracy": "excellent"},
        },
        "languages": WHISPER_LANGUAGES,
    },
    "parakeet": {
        "name": "NVIDIA Parakeet-TDT",
        "description": "State-of-the-art accuracy with 25 European languages",
        "models": {
            "nvidia/parakeet-tdt-0.6b-v3": {
                "vram_gb": 4,
                "speed": "fastest",
                "accuracy": "excellent",
            },
        },
        "languages": PARAKEET_LANGUAGES,
    },
    "canary": {
        "name": "NVIDIA Canary",
        "description": "ASR + Speech Translation between supported languages",
        "models": {
            "nvidia/canary-1b-v2": {"vram_gb": 6, "speed": "fast", "accuracy": "excellent"},
        },
        "languages": list(CANARY_LANGUAGES)
        if isinstance(CANARY_LANGUAGES, list)
        else list(CANARY_LANGUAGES.keys()),
    },
    "voxtral": {
        "name": "Mistral Voxtral",
        "description": "Advanced ASR with Q&A and summarization capabilities",
        "models": {
            "mistralai/Voxtral-Mini-3B-2507": {
                "vram_gb": 10,
                "speed": "medium",
                "accuracy": "excellent",
            },
        },
        "languages": VOXTRAL_LANGUAGES,
    },
}


def get_languages_for_model(model_type: str, model_name: Optional[str] = None) -> list[str]:
    """Get supported languages for a model type."""
    if model_type == "whisper":
        if model_name and model_name in WHISPER_ENGLISH_ONLY:
            return ["en"]
        return WHISPER_LANGUAGES
    elif model_type == "parakeet":
        return PARAKEET_LANGUAGES
    elif model_type == "canary":
        return list(CANARY_LANGUAGES.keys())
    elif model_type == "voxtral":
        return VOXTRAL_LANGUAGES
    else:
        return ["auto", "en"]


def get_available_models(model_type: str) -> list[str]:
    """Get available model names for a model type."""
    if model_type == "whisper":
        return WHISPER_MODELS
    elif model_type == "parakeet":
        return list(MODEL_INFO["parakeet"]["models"].keys())
    elif model_type == "canary":
        return list(MODEL_INFO["canary"]["models"].keys())
    elif model_type == "voxtral":
        return list(MODEL_INFO["voxtral"]["models"].keys())
    else:
        return []


def get_compute_types(model_type: str) -> list[str]:
    """Get available compute types for a model type."""
    if model_type == "whisper":
        return ["float16", "int8", "int8_float16", "float32"]
    elif model_type in ("parakeet", "canary"):
        return ["float16", "float32"]
    elif model_type == "voxtral":
        return ["float16", "bfloat16", "int8", "int4"]
    else:
        return ["float16"]
