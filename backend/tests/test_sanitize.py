"""Tests for core.processing.sanitize."""

from speakeasy.core.processing import sanitize


def test_strips_surrounding_whitespace():
    assert sanitize("  hello  \n") == "hello"


def test_unwraps_a_fenced_response():
    assert sanitize("```text\nHello there.\n```") == "Hello there."


def test_unwraps_a_bare_fence():
    assert sanitize("```\nHello there.\n```") == "Hello there."


def test_unwraps_a_fence_with_trailing_whitespace():
    assert sanitize("  ```json\n{}\n```  ") == "{}"


def test_keeps_text_that_merely_contains_backticks():
    assert sanitize("Use `code` here.") == "Use `code` here."


def test_keeps_a_fence_that_does_not_wrap_the_whole_response():
    assert sanitize("Intro\n```\nbody\n```") == "Intro\n```\nbody\n```"


def test_empty_string_stays_empty():
    assert sanitize("") == ""


def test_a_fenced_empty_response_becomes_empty():
    assert sanitize("```text\n\n```") == ""
