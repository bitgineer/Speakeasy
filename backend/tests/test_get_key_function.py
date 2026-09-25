"""Tests for services.secrets.get_key."""

from speakeasy.services import secrets


def test_get_key_missing_file_returns_none(tmp_path):
    assert secrets.get_key("openai", tmp_path / "secrets.json") is None


def test_get_key_round_trips_a_stored_key(tmp_path):
    path = tmp_path / "secrets.json"
    secrets.set_key("openai", "sk-test", path)

    assert secrets.get_key("openai", path) == "sk-test"


def test_get_key_unknown_provider_returns_none(tmp_path):
    path = tmp_path / "secrets.json"
    secrets.set_key("openai", "sk-test", path)

    assert secrets.get_key("groq", path) is None


def test_get_key_corrupt_file_returns_none(tmp_path):
    path = tmp_path / "secrets.json"
    path.write_text("{not json")

    assert secrets.get_key("openai", path) is None


def test_get_key_non_mapping_file_returns_none(tmp_path):
    path = tmp_path / "secrets.json"
    path.write_text('["not", "a", "map"]')

    assert secrets.get_key("openai", path) is None


def test_get_key_separates_providers(tmp_path):
    path = tmp_path / "secrets.json"
    secrets.set_key("openai", "sk-one", path)
    secrets.set_key("groq", "sk-two", path)

    assert secrets.get_key("openai", path) == "sk-one"
    assert secrets.get_key("groq", path) == "sk-two"
