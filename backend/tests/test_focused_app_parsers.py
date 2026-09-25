"""Tests for the pure focused-app parsers in utils.focused_app."""

import json

import pytest

from speakeasy.core.processing import FocusedApp
from speakeasy.utils.focused_app import (
    parse_linux_wayland,
    parse_linux_x11,
    parse_macos,
    parse_windows,
)


def test_parse_windows_returns_the_lowercased_exe_stem():
    app = parse_windows(r"C:\Program Files\Slack\slack.exe", "general - Slack")

    assert app == FocusedApp(key="slack", title="general - Slack")


def test_parse_windows_strips_an_uppercase_exe_and_collapses_whitespace():
    app = parse_windows(r"C:\Apps\Slack.EXE", "  Team\t  Chat  ")

    assert app == FocusedApp(key="slack", title="Team Chat")


def test_parse_windows_keeps_a_multi_dot_stem():
    assert parse_windows(r"C:\Apps\App.v2.exe", "Notes").key == "app.v2"


def test_parse_windows_handles_a_bare_executable_name():
    assert parse_windows("Notepad.exe", "").key == "notepad"


def test_parse_macos_reads_the_bundle_id_and_title():
    app = parse_macos("com.apple.Safari\nMy Window")

    assert app == FocusedApp(key="com.apple.safari", title="My Window")


def test_parse_macos_falls_back_to_a_process_name():
    app = parse_macos("Safari\n")

    assert app == FocusedApp(key="safari", title="")


def test_parse_macos_without_a_title_line():
    app = parse_macos("Notes")

    assert app == FocusedApp(key="notes", title="")


@pytest.mark.parametrize("stdout", ["", "\n", "   \nWindow"])
def test_parse_macos_malformed_stdout_is_none(stdout):
    assert parse_macos(stdout) is None


def test_parse_linux_x11_reads_the_instance_name():
    app = parse_linux_x11('WM_CLASS(STRING) = "slack", "Slack"', "general - Slack")

    assert app == FocusedApp(key="slack", title="general - Slack")


def test_parse_linux_x11_tolerates_surrounding_lines():
    output = '\nWM_CLASS(STRING) = "code", "Code"\n'

    assert parse_linux_x11(output, "file.py") == FocusedApp(key="code", title="file.py")


@pytest.mark.parametrize("output", ["", "WM_CLASS:  not found.", 'WM_CLASS(STRING) = "", "Slack"'])
def test_parse_linux_x11_malformed_output_is_none(output):
    assert parse_linux_x11(output, "title") is None


def _tree(nodes):
    return json.dumps({"nodes": nodes})


def test_parse_linux_wayland_finds_the_focused_node():
    tree = _tree(
        [
            {"app_id": "waybar", "name": "bar"},
            {
                "nodes": [
                    {"app_id": "other", "name": "Other"},
                    {"app_id": "firefox", "name": "Mozilla Firefox", "focused": True},
                ]
            },
        ]
    )

    assert parse_linux_wayland(tree) == FocusedApp(key="firefox", title="Mozilla Firefox")


def test_parse_linux_wayland_reads_floating_nodes():
    tree = json.dumps({"floating_nodes": [{"app_id": "vlc", "name": "VLC", "focused": True}]})

    assert parse_linux_wayland(tree) == FocusedApp(key="vlc", title="VLC")


def test_parse_linux_wayland_normalizes_key_and_title():
    tree = _tree([{"app_id": "  Slack ", "name": "  general   chat  ", "focused": True}])

    assert parse_linux_wayland(tree) == FocusedApp(key="slack", title="general chat")


@pytest.mark.parametrize(
    "payload",
    [
        "not json",
        "[]",
        "{}",
        '{"nodes": [{"app_id": "x"}]}',
        '{"nodes": [{"app_id": "", "focused": true}]}',
        '{"nodes": "junk", "focused": false}',
    ],
)
def test_parse_linux_wayland_malformed_input_is_none(payload):
    assert parse_linux_wayland(payload) is None
