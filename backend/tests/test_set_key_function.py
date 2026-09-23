"""Tests for services.secrets.set_key."""

import json
import logging

from speakeasy.services import secrets


def test_set_key_creates_parent_directories(tmp_path):
    path = tmp_path / "nested" / "secrets.json"

    secrets.set_key("openai", "sk-test", path)

    assert secrets.get_key("openai", path) == "sk-test"


def test_set_key_overwrites_an_existing_key(tmp_path):
    path = tmp_path / "secrets.json"
    secrets.set_key("openai", "sk-old", path)

    secrets.set_key("openai", "sk-new", path)

    assert secrets.get_key("openai", path) == "sk-new"


def test_set_key_empty_string_deletes_the_entry(tmp_path):
    path = tmp_path / "secrets.json"
    secrets.set_key("openai", "sk-test", path)

    secrets.set_key("openai", "", path)

    assert secrets.get_key("openai", path) is None


def test_set_key_delete_leaves_other_providers(tmp_path):
    path = tmp_path / "secrets.json"
    secrets.set_key("openai", "sk-one", path)
    secrets.set_key("groq", "sk-two", path)

    secrets.set_key("openai", "", path)

    assert secrets.get_key("openai", path) is None
    assert secrets.get_key("groq", path) == "sk-two"


def test_set_key_replaces_a_corrupt_file(tmp_path):
    path = tmp_path / "secrets.json"
    path.write_text("{not json")

    secrets.set_key("openai", "sk-test", path)

    assert json.loads(path.read_text()) == {"openai": "sk-test"}


def test_set_key_leaves_no_temp_file(tmp_path):
    path = tmp_path / "secrets.json"

    secrets.set_key("openai", "sk-test", path)

    assert list(tmp_path.glob("*.tmp")) == []
    assert sorted(entry.name for entry in tmp_path.iterdir()) == ["secrets.json"]


def test_set_key_never_logs_the_key(tmp_path, caplog):
    path = tmp_path / "secrets.json"

    with caplog.at_level(logging.DEBUG):
        secrets.set_key("openai", "sk-secret-value", path)
        secrets.get_key("openai", path)

    assert "sk-secret-value" not in caplog.text
