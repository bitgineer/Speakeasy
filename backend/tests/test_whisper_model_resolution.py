"""Whisper short-name resolution and the display catalog stay consistent."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.core.config import MODEL_INFO, WHISPER_MODELS
from speakeasy.core.models import ModelWrapper


def resolve(name: str) -> str:
    wrapper = ModelWrapper(model_type="whisper", model_name=name)
    return wrapper._resolve_hf_name(name)


def test_every_catalog_entry_resolves_to_a_systran_repo():
    for name in WHISPER_MODELS:
        resolved = resolve(name)
        assert resolved.startswith("Systran/faster-"), f"{name} resolved to {resolved}"


def test_distil_entries_use_the_distil_whisper_repos():
    assert resolve("distil-large-v3") == "Systran/faster-distil-whisper-large-v3"
    assert resolve("distil-large-v2") == "Systran/faster-distil-whisper-large-v2"
    assert resolve("distil-medium.en") == "Systran/faster-distil-whisper-medium.en"
    assert resolve("distil-small.en") == "Systran/faster-distil-whisper-small.en"


def test_full_repo_ids_pass_through_unchanged():
    assert resolve("Systran/faster-whisper-large-v3") == "Systran/faster-whisper-large-v3"


def test_display_catalog_matches_the_served_catalog():
    assert set(MODEL_INFO["whisper"]["models"]) == set(WHISPER_MODELS)
