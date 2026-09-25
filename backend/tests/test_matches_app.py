"""Tests for core.processing.matches_app."""

from speakeasy.core.processing import FocusedApp, matches_app
from speakeasy.services.settings import AppMatch, ToneProfile


def _profile(*matches: AppMatch) -> ToneProfile:
    return ToneProfile(name="tone", matches=list(matches))


def test_empty_match_list_is_false():
    assert matches_app(_profile(), FocusedApp(key="slack", title="general - Slack")) is False


def test_app_rule_matches_key_case_insensitively():
    profile = _profile(AppMatch(field="app", pattern="SLACK"))

    assert matches_app(profile, FocusedApp(key="slack")) is True


def test_title_rule_matches_title_case_insensitively():
    profile = _profile(AppMatch(field="title", pattern="github"))

    assert matches_app(profile, FocusedApp(key="chrome", title="PR #42 - GitHub")) is True


def test_substring_match_is_not_whole_word():
    profile = _profile(AppMatch(field="title", pattern="git"))

    assert matches_app(profile, FocusedApp(key="chrome", title="GitHub - PR")) is True


def test_app_rule_does_not_read_title():
    profile = _profile(AppMatch(field="app", pattern="slack"))

    assert matches_app(profile, FocusedApp(key="chrome", title="Slack")) is False


def test_title_rule_does_not_read_key():
    profile = _profile(AppMatch(field="title", pattern="slack"))

    assert matches_app(profile, FocusedApp(key="slack", title="general")) is False


def test_any_rule_firing_is_true():
    profile = _profile(
        AppMatch(field="app", pattern="vscode"),
        AppMatch(field="title", pattern="speakeasy"),
    )

    assert matches_app(profile, FocusedApp(key="chrome", title="SpeakEasy - GitHub")) is True
