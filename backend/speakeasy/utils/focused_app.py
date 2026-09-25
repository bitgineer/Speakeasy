"""Best-effort detection of the focused application, per platform.

Every probe returns ``None`` on failure so the resolver can fall back to the default tone. The
parse step is split into pure functions so normalization is testable without a desktop session.
"""

import json
import logging
import os
import re
import subprocess
import sys
from pathlib import PureWindowsPath

from speakeasy.core.processing import FocusedApp

logger = logging.getLogger(__name__)

_WM_CLASS_QUOTED = re.compile(r'"([^"]*)"')
_MACOS_SCRIPT = """\
tell application "System Events"
    set frontApp to first application process whose frontmost is true
    set appId to ""
    try
        set appId to bundle identifier of frontApp
    end try
    if appId is missing value or appId is "" then set appId to name of frontApp
    set winTitle to ""
    try
        set winTitle to name of front window of frontApp
    end try
    return appId & linefeed & winTitle
end tell
"""


def _collapse(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _normalize_key(value: str) -> str:
    return _collapse(value).lower().removesuffix(".exe")


def _normalize_title(value: str) -> str:
    return _collapse(value)


def parse_windows(exe_path: str, title: str) -> FocusedApp:
    """The exe stem, lowercased, plus the window text."""
    stem = PureWindowsPath(exe_path).stem
    return FocusedApp(key=_normalize_key(stem or exe_path), title=_normalize_title(title))


def parse_macos(stdout: str) -> FocusedApp | None:
    """Parse the probe's two lines: bundle id (or process name), then window title."""
    lines = stdout.splitlines()
    identifier = lines[0] if lines else ""
    title = lines[1] if len(lines) > 1 else ""
    key = _normalize_key(identifier)
    if not key:
        return None
    return FocusedApp(key=key, title=_normalize_title(title))


def parse_linux_x11(wm_class_output: str, title: str) -> FocusedApp | None:
    """Parse ``xprop WM_CLASS`` output and take its instance name."""
    match = _WM_CLASS_QUOTED.search(wm_class_output)
    if match is None:
        return None
    key = _normalize_key(match.group(1))
    if not key:
        return None
    return FocusedApp(key=key, title=_normalize_title(title))


def parse_linux_wayland(tree_json: str) -> FocusedApp | None:
    """Walk a sway tree to the focused node and take its ``app_id`` and ``name``."""
    try:
        tree = json.loads(tree_json)
    except (TypeError, ValueError):
        return None
    node = _focused_node(tree)
    if node is None:
        return None
    key = _normalize_key(str(node.get("app_id") or ""))
    if not key:
        return None
    return FocusedApp(key=key, title=_normalize_title(str(node.get("name") or "")))


def _focused_node(node: object) -> dict | None:
    if not isinstance(node, dict):
        return None
    if node.get("focused") is True:
        return node
    children = node.get("nodes")
    floating = node.get("floating_nodes")
    for child in (children if isinstance(children, list) else []) + (
        floating if isinstance(floating, list) else []
    ):
        found = _focused_node(child)
        if found is not None:
            return found
    return None


def _run(command: list[str], timeout: float = 2.0) -> str | None:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _detect_windows() -> FocusedApp | None:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD),
    ]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None

    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if not pid.value:
        return None

    process_query_limited_information = 0x1000
    handle = kernel32.OpenProcess(process_query_limited_information, False, pid.value)
    if not handle:
        return None
    try:
        size = wintypes.DWORD(1024)
        path_buffer = ctypes.create_unicode_buffer(size.value)
        if not kernel32.QueryFullProcessImageNameW(handle, 0, path_buffer, ctypes.byref(size)):
            return None
        exe_path = path_buffer.value
    finally:
        kernel32.CloseHandle(handle)

    length = user32.GetWindowTextLengthW(hwnd)
    title_buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, title_buffer, length + 1)
    return parse_windows(exe_path, title_buffer.value)


def _detect_macos() -> FocusedApp | None:
    result = subprocess.run(
        ["osascript", "-e", _MACOS_SCRIPT],
        capture_output=True,
        text=True,
        timeout=3,
    )
    if result.returncode != 0:
        return None
    return parse_macos(result.stdout)


def _detect_linux_x11() -> FocusedApp | None:
    window_id = _run(["xdotool", "getactivewindow"])
    if not window_id:
        return None
    wm_class = _run(["xprop", "-id", window_id, "WM_CLASS"])
    if wm_class is None:
        return None
    title = _run(["xdotool", "getwindowname", window_id]) or ""
    return parse_linux_x11(wm_class, title)


def _detect_linux_wayland() -> FocusedApp | None:
    tree_json = _run(["swaymsg", "-t", "get_tree"])
    if tree_json is None:
        return None
    return parse_linux_wayland(tree_json)


def _detect_linux() -> FocusedApp | None:
    if os.environ.get("XDG_SESSION_TYPE") == "wayland":
        return _detect_linux_wayland()
    return _detect_linux_x11()


def detect_focused_app() -> FocusedApp | None:
    """The focused app, or None when the platform is unknown or the probe fails."""
    try:
        if sys.platform == "win32":
            return _detect_windows()
        if sys.platform == "darwin":
            return _detect_macos()
        if sys.platform.startswith("linux"):
            return _detect_linux()
    except Exception as exc:
        logger.debug(f"Focused app detection failed: {exc}")
    return None
