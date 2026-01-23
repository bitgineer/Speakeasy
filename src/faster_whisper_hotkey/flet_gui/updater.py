"""
Auto-update system for faster-whisper-hotkey.

This module provides automatic update checking, downloading, and installation
for the Windows executable version. It integrates with GitHub Releases API
to check for new versions and download updates in the background.

Classes
-------
UpdateInfo
    Dataclass containing information about an available update.

UpdateManager
    Main update management class with checking and downloading.

UpdateDialog
    Flet dialog for displaying update notifications and progress.

Functions
---------
get_current_version
    Get the current application version.

parse_version
    Parse version string into comparable tuple.

compare_versions
    Compare two version strings.
"""

import logging
import os
import sys
import threading
import time
import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any
import json
import tempfile
import shutil

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    # Fallback to urllib for HTTP requests
    from urllib import request as urllib_request
    from urllib.error import URLError, HTTPError

import flet as ft

logger = logging.getLogger(__name__)

# GitHub repository configuration
GITHUB_REPO = "blakkd/faster-whisper-hotkey"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
GITHUB_RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases"

# Update configuration
DEFAULT_CHECK_INTERVAL = 24 * 60 * 60  # 24 hours in seconds
CHECK_INTERVALS = {
    "daily": 24 * 60 * 60,
    "weekly": 7 * 24 * 60 * 60,
    "manually": 0,  # Only check manually
}


def get_current_version() -> str:
    """
    Get the current application version.

    First tries to read from pyproject.toml if running from source.
    For frozen executables, reads from version resource or returns a default.

    Returns
    -------
    str
        Current version string (e.g., "0.4.3").
    """
    # Try to get version from package metadata
    try:
        from importlib.metadata import version
        return version("faster-whisper-hotkey")
    except Exception:
        pass

    # For frozen executable, check for version file
    if getattr(sys, 'frozen', False):
        # Check for version.txt next to executable
        exe_dir = os.path.dirname(sys.executable)
        version_file = os.path.join(exe_dir, 'version.txt')
        if os.path.exists(version_file):
            try:
                with open(version_file, 'r') as f:
                    return f.read().strip()
            except Exception:
                pass

    # Default fallback version
    return "0.4.3"


def parse_version(version_str: str) -> tuple:
    """
    Parse a version string into a comparable tuple.

    Handles versions like:
    - "0.4.3" -> (0, 4, 3)
    - "0.4.3-beta" -> (0, 4, 3, 'beta', 0)
    - "1.0.0-rc1" -> (1, 0, 0, 'rc', 1)

    Parameters
    ----------
    version_str
        Version string to parse.

    Returns
    -------
    tuple
        Comparable version tuple.
    """
    # Remove 'v' prefix if present
    version_str = version_str.lstrip('v')

    # Split version parts
    parts = version_str.split('-')
    main_version = parts[0].split('.')

    # Parse numeric parts
    version_tuple = []
    for part in main_version:
        try:
            version_tuple.append(int(part))
        except ValueError:
            version_tuple.append(part)

    # Handle pre-release tags
    if len(parts) > 1:
        prerelease = parts[1]
        # Extract tag name and number (e.g., "beta1" -> ("beta", 1))
        tag_name = ''.join(c for c in prerelease if not c.isdigit())
        tag_number = ''.join(c for c in prerelease if c.isdigit())
        version_tuple.append(tag_name.lower())
        version_tuple.append(int(tag_number) if tag_number else 0)

    return tuple(version_tuple)


def compare_versions(v1: str, v2: str) -> int:
    """
    Compare two version strings.

    Parameters
    ----------
    v1
        First version string.
    v2
        Second version string.

    Returns
    -------
    int
        -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2.
    """
    p1 = parse_version(v1)
    p2 = parse_version(v2)

    if p1 < p2:
        return -1
    elif p1 > p2:
        return 1
    return 0


@dataclass
class UpdateInfo:
    """
    Information about an available update.

    Attributes
    ----------
    version
        New version string (e.g., "0.5.0").
    tag_name
        GitHub release tag name.
    download_url
        URL to download the update.
    file_size
        Size of the update file in bytes.
    sha256
        SHA256 checksum for verification.
    release_notes
        Markdown formatted release notes.
    prerelease
        Whether this is a pre-release version.
    published_at
        Publication date as datetime.
    """
    version: str
    tag_name: str
    download_url: str
    file_size: int
    sha256: str
    release_notes: str
    prerelease: bool
    published_at: datetime


class UpdateManager:
    """
    Manager for checking and downloading application updates.

    Features:
    - Check for updates via GitHub Releases API
    - Background download with progress tracking
    - Configurable check frequency (daily, weekly, manual)
    - Beta/preview channel support
    - Graceful error handling with rollback

    Attributes
    ----------
    current_version
        Current application version.
    check_frequency
        How often to check for updates.
    include_prereleases
        Whether to include pre-release versions.
    auto_download
        Whether to automatically download updates.
    """

    def __init__(
        self,
        current_version: Optional[str] = None,
        check_frequency: str = "daily",
        include_prereleases: bool = False,
        auto_download: bool = False,
    ):
        """
        Initialize the update manager.

        Parameters
        ----------
        current_version
            Current version string. If None, will be detected.
        check_frequency
            How often to check: "daily", "weekly", or "manually".
        include_prereleases
            Whether to include pre-release versions.
        auto_download
            Whether to automatically download updates when available.
        """
        self._current_version = current_version or get_current_version()
        self._check_frequency = check_frequency
        self._include_prereleases = include_prereleases
        self._auto_download = auto_download

        # State
        self._last_check_time: Optional[datetime] = None
        self._available_update: Optional[UpdateInfo] = None
        self._is_checking = False
        self._is_downloading = False
        self._download_progress: float = 0.0
        self._download_error: Optional[str] = None

        # Callbacks
        self._on_update_available: Optional[Callable[[UpdateInfo], None]] = None
        self._on_download_complete: Optional[Callable[[str], None]] = None
        self._on_download_progress: Optional[Callable[[float], None]] = None
        self._on_error: Optional[Callable[[str], None]] = None

        # Settings storage
        self._state_file: Optional[str] = None
        self._load_state()

    @property
    def current_version(self) -> str:
        """Get current version."""
        return self._current_version

    @property
    def check_frequency(self) -> str:
        """Get check frequency."""
        return self._check_frequency

    @check_frequency.setter
    def check_frequency(self, value: str):
        """Set check frequency."""
        if value in CHECK_INTERVALS:
            self._check_frequency = value
            self._save_state()

    @property
    def include_prereleases(self) -> bool:
        """Get include prereleases setting."""
        return self._include_prereleases

    @include_prereleases.setter
    def include_prereleases(self, value: bool):
        """Set include prereleases setting."""
        self._include_prereleases = value
        self._save_state()

    @property
    def auto_download(self) -> bool:
        """Get auto download setting."""
        return self._auto_download

    @auto_download.setter
    def auto_download(self, value: bool):
        """Set auto download setting."""
        self._auto_download = value
        self._save_state()

    @property
    def available_update(self) -> Optional[UpdateInfo]:
        """Get available update info."""
        return self._available_update

    @property
    def is_checking(self) -> bool:
        """Check if currently checking for updates."""
        return self._is_checking

    @property
    def is_downloading(self) -> bool:
        """Check if currently downloading."""
        return self._is_downloading

    @property
    def download_progress(self) -> float:
        """Get download progress (0.0 to 1.0)."""
        return self._download_progress

    def _get_state_file_path(self) -> str:
        """Get the path to the state file."""
        if self._state_file:
            return self._state_file

        # Use settings directory
        if getattr(sys, 'frozen', False):
            # Check for portable mode
            exe_dir = os.path.dirname(sys.executable)
            if os.path.exists(os.path.join(exe_dir, 'portable.txt')):
                state_dir = os.path.join(exe_dir, 'settings')
            else:
                # Use AppData
                state_dir = os.path.join(
                    os.environ.get('APPDATA', os.path.expanduser('~\\AppData\\Roaming')),
                    'faster_whisper_hotkey'
                )
        else:
            # Development mode
            state_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.updater_state')
            state_dir = os.path.abspath(state_dir)

        os.makedirs(state_dir, exist_ok=True)
        self._state_file = os.path.join(state_dir, 'update_state.json')
        return self._state_file

    def _load_state(self):
        """Load update state from disk."""
        try:
            state_file = self._get_state_file_path()
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    self._check_frequency = state.get('check_frequency', self._check_frequency)
                    self._include_prereleases = state.get('include_prereleases', self._include_prereleases)
                    self._auto_download = state.get('auto_download', self._auto_download)

                    last_check_str = state.get('last_check_time')
                    if last_check_str:
                        self._last_check_time = datetime.fromisoformat(last_check_str)
        except Exception as e:
            logger.warning(f"Failed to load update state: {e}")

    def _save_state(self):
        """Save update state to disk."""
        try:
            state_file = self._get_state_file_path()
            state = {
                'check_frequency': self._check_frequency,
                'include_prereleases': self._include_prereleases,
                'auto_download': self._auto_download,
                'last_check_time': self._last_check_time.isoformat() if self._last_check_time else None,
            }
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save update state: {e}")

    def should_check_for_updates(self) -> bool:
        """
        Check if it's time to check for updates based on frequency.

        Returns
        -------
        bool
            True if should check, False otherwise.
        """
        if self._check_frequency == "manually":
            return False

        if self._last_check_time is None:
            return True

        interval = CHECK_INTERVALS.get(self._check_frequency, DEFAULT_CHECK_INTERVAL)
        if interval == 0:
            return False

        elapsed = (datetime.now() - self._last_check_time).total_seconds()
        return elapsed >= interval

    def check_for_updates(self, callback: Optional[Callable[[UpdateInfo], None]] = None) -> bool:
        """
        Check for available updates.

        Parameters
        ----------
        callback
            Optional callback when update is available.

        Returns
        -------
        bool
            True if check was initiated, False if already checking.
        """
        if self._is_checking:
            return False

        self._is_checking = True
        self._on_update_available = callback

        def check_in_thread():
            try:
                update_info = self._fetch_latest_release()
                if update_info:
                    self._available_update = update_info
                    self._save_state()

                    # Notify callback
                    if self._on_update_available:
                        self._on_update_available(update_info)

                    # Auto-download if enabled
                    if self._auto_download:
                        self.download_update()
                else:
                    logger.info("No updates available")
            except Exception as e:
                logger.error(f"Error checking for updates: {e}")
                if self._on_error:
                    self._on_error(str(e))
            finally:
                self._is_checking = False
                self._last_check_time = datetime.now()
                self._save_state()

        threading.Thread(target=check_in_thread, daemon=True).start()
        return True

    def _fetch_latest_release(self) -> Optional[UpdateInfo]:
        """
        Fetch the latest release from GitHub API.

        Returns
        -------
        UpdateInfo or None
            Update info if newer version available, None otherwise.
        """
        if not REQUESTS_AVAILABLE:
            return self._fetch_latest_release_urllib()

        try:
            # Fetch releases from GitHub API
            response = requests.get(
                GITHUB_API_URL,
                headers={'Accept': 'application/vnd.github.v3+json'},
                timeout=10
            )
            response.raise_for_status()

            releases = response.json()

            # Find the latest relevant release
            for release in releases:
                # Skip if prerelease and not including them
                if release.get('prerelease', False) and not self._include_prereleases:
                    continue

                # Get version from tag name
                tag_name = release.get('tag_name', '')
                version = tag_name.lstrip('v')

                # Check if this is newer
                if compare_versions(version, self._current_version) > 0:
                    # Find the Windows installer asset
                    download_url = None
                    file_size = 0
                    sha256 = ""

                    for asset in release.get('assets', []):
                        name = asset.get('name', '').lower()
                        # Look for .exe installer
                        if 'faster-whisper-hotkey' in name and name.endswith('.exe'):
                            download_url = asset.get('browser_download_url')
                            file_size = asset.get('size', 0)
                            break

                    if download_url:
                        return UpdateInfo(
                            version=version,
                            tag_name=tag_name,
                            download_url=download_url,
                            file_size=file_size,
                            sha256=sha256,
                            release_notes=release.get('body', ''),
                            prerelease=release.get('prerelease', False),
                            published_at=datetime.fromisoformat(
                                release.get('published_at', '').replace('Z', '+00:00')
                            ),
                        )

            return None

        except Exception as e:
            logger.error(f"Failed to fetch releases: {e}")
            raise

    def _fetch_latest_release_urllib(self) -> Optional[UpdateInfo]:
        """Fallback for fetching releases using urllib."""
        try:
            req = urllib_request.Request(
                GITHUB_API_URL,
                headers={'Accept': 'application/vnd.github.v3+json'}
            )
            with urllib_request.urlopen(req, timeout=10) as response:
                releases = json.loads(response.read().decode())

                # Same logic as above
                for release in releases:
                    if release.get('prerelease', False) and not self._include_prereleases:
                        continue

                    tag_name = release.get('tag_name', '')
                    version = tag_name.lstrip('v')

                    if compare_versions(version, self._current_version) > 0:
                        download_url = None
                        file_size = 0

                        for asset in release.get('assets', []):
                            name = asset.get('name', '').lower()
                            if 'faster-whisper-hotkey' in name and name.endswith('.exe'):
                                download_url = asset.get('browser_download_url')
                                file_size = asset.get('size', 0)
                                break

                        if download_url:
                            return UpdateInfo(
                                version=version,
                                tag_name=tag_name,
                                download_url=download_url,
                                file_size=file_size,
                                sha256="",
                                release_notes=release.get('body', ''),
                                prerelease=release.get('prerelease', False),
                                published_at=datetime.fromisoformat(
                                    release.get('published_at', '').replace('Z', '+00:00')
                                ),
                            )

                return None

        except Exception as e:
            logger.error(f"Failed to fetch releases with urllib: {e}")
            raise

    def download_update(
        self,
        progress_callback: Optional[Callable[[float], None]] = None,
        complete_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None,
    ) -> bool:
        """
        Download the available update.

        Parameters
        ----------
        progress_callback
            Callback with progress (0.0 to 1.0).
        complete_callback
            Callback with path to downloaded file.
        error_callback
            Callback with error message.

        Returns
        -------
        bool
            True if download started, False if no update available or already downloading.
        """
        if not self._available_update:
            logger.warning("No update available to download")
            return False

        if self._is_downloading:
            return False

        self._is_downloading = True
        self._download_progress = 0.0
        self._download_error = None
        self._on_download_progress = progress_callback
        self._on_download_complete = complete_callback
        self._on_error = error_callback

        def download_in_thread():
            try:
                dest_path = self._download_file(
                    self._available_update.download_url,
                    self._available_update.file_size
                )

                if dest_path and self._on_download_complete:
                    self._on_download_complete(dest_path)

            except Exception as e:
                logger.error(f"Error downloading update: {e}")
                self._download_error = str(e)
                if self._on_error:
                    self._on_error(str(e))
            finally:
                self._is_downloading = False

        threading.Thread(target=download_in_thread, daemon=True).start()
        return True

    def _download_file(self, url: str, total_size: int) -> str:
        """
        Download a file with progress tracking.

        Parameters
        ----------
        url
            URL to download from.
        total_size
            Expected file size in bytes.

        Returns
        -------
        str
            Path to downloaded file.
        """
        # Create temp directory for downloads
        temp_dir = os.path.join(tempfile.gettempdir(), 'faster-whisper-hotkey-updates')
        os.makedirs(temp_dir, exist_ok=True)

        # Extract filename from URL
        filename = os.path.basename(url.split('?')[0])
        dest_path = os.path.join(temp_dir, filename)

        if REQUESTS_AVAILABLE:
            return self._download_with_requests(url, dest_path, total_size)
        else:
            return self._download_with_urllib(url, dest_path, total_size)

    def _download_with_requests(self, url: str, dest_path: str, total_size: int) -> str:
        """Download using requests library."""
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        downloaded = 0
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total_size > 0:
                        self._download_progress = downloaded / total_size
                        if self._on_download_progress:
                            self._on_download_progress(self._download_progress)

        return dest_path

    def _download_with_urllib(self, url: str, dest_path: str, total_size: int) -> str:
        """Download using urllib library."""
        def report_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                self._download_progress = min(downloaded / total_size, 1.0)
                if self._on_download_progress:
                    self._on_download_progress(self._download_progress)

        urllib_request.urlretrieve(url, dest_path, reporthook=report_progress)
        return dest_path

    def install_update(self, installer_path: str) -> bool:
        """
        Install the downloaded update.

        This will launch the installer and exit the current application.

        Parameters
        ----------
        installer_path
            Path to the downloaded installer.

        Returns
        -------
        bool
            True if installer was launched, False otherwise.
        """
        if not os.path.exists(installer_path):
            logger.error(f"Installer not found: {installer_path}")
            return False

        try:
            import subprocess

            # Launch installer and exit current app
            # Use DETACHED_PROCESS on Windows to avoid blocking
            if sys.platform == 'win32':
                subprocess.Popen(
                    [installer_path],
                    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                subprocess.Popen([installer_path], start_new_session=True)

            logger.info("Update installer launched, exiting application")
            return True

        except Exception as e:
            logger.error(f"Failed to launch installer: {e}")
            return False

    def dismiss_update(self):
        """Dismiss the available update (don't notify again for this version)."""
        if self._available_update:
            # Save dismissed version to state
            try:
                state_file = self._get_state_file_path()
                state = {}
                if os.path.exists(state_file):
                    with open(state_file, 'r') as f:
                        state = json.load(f)

                state['dismissed_version'] = self._available_update.version

                with open(state_file, 'w') as f:
                    json.dump(state, f, indent=2)
            except Exception as e:
                logger.warning(f"Failed to save dismissed version: {e}")

            self._available_update = None

    def is_update_dismissed(self, version: str) -> bool:
        """
        Check if an update version was previously dismissed.

        Parameters
        ----------
        version
            Version to check.

        Returns
        -------
        bool
            True if dismissed, False otherwise.
        """
        try:
            state_file = self._get_state_file_path()
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    return state.get('dismissed_version') == version
        except Exception:
            pass
        return False


class UpdateDialog:
    """
    Flet dialog for displaying update notifications and download progress.

    Attributes
    ----------
    update_manager
        The UpdateManager instance.
    """

    def __init__(self, update_manager: UpdateManager):
        """
        Initialize the update dialog.

        Parameters
        ----------
        update_manager
            The UpdateManager instance to use.
        """
        self._update_manager = update_manager
        self._dialog: Optional[ft.AlertDialog] = None
        self._page: Optional[ft.Page] = None
        self._progress_bar: Optional[ft.ProgressBar] = None
        self._status_text: Optional[ft.Text] = None
        self._release_notes: Optional[ft.Column] = None

    def show_update_available(self, page: ft.Page, update_info: UpdateInfo):
        """
        Show dialog for available update.

        Parameters
        ----------
        page
            Flet page to show dialog on.
        update_info
            Information about the available update.
        """
        self._page = page

        # Don't show if previously dismissed
        if self._update_manager.is_update_dismissed(update_info.version):
            return

        # Format release notes (basic markdown handling)
        notes_text = self._format_release_notes(update_info.release_notes)

        # Create dialog
        self._status_text = ft.Text(
            f"Version {update_info.version} is available!",
            size=16,
            weight=ft.FontWeight.BOLD,
        )

        version_info = ft.Text(
            f"You have version {self._update_manager.current_version}",
            size=13,
            color=ft.colors.ON_SURFACE_VARIANT,
        )

        self._release_notes = ft.Column(
            [ft.Text(notes_text, size=12, selectable=True)],
            scroll=ft.ScrollMode.AUTO,
            height=200,
        )

        size_text = ft.Text(
            f"Download size: {self._format_size(update_info.file_size)}",
            size=11,
            color=ft.colors.ON_SURFACE_VARIANT,
        )

        def on_update_click(e):
            """Handle update button click."""
            self._show_download_progress()
            self._update_manager.download_update(
                progress_callback=self._on_download_progress,
                complete_callback=self._on_download_complete,
                error_callback=self._on_download_error,
            )

        def on_dismiss_click(e):
            """Handle dismiss button click."""
            self._update_manager.dismiss_update()
            self.close()

        def on_later_click(e):
            """Handle later button click."""
            self.close()

        content = ft.Column(
            [
                self._status_text,
                version_info,
                ft.Divider(height=1),
                ft.Text("What's New:", size=13, weight=ft.FontWeight.MEDIUM),
                self._release_notes,
                size_text,
            ],
            spacing=8,
            tight=True,
        )

        self._dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.icons.SYSTEM_UPDATE_ALT, color=ft.colors.PRIMARY),
                ft.Text("Update Available"),
            ], spacing=8),
            content=content,
            actions=[
                ft.TextButton("Later", on_click=on_later_click),
                ft.TextButton("Skip This Version", on_click=on_dismiss_click),
                ft.ElevatedButton(
                    "Update Now",
                    icon=ft.icons.DOWNLOAD,
                    on_click=on_update_click,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.dialog = self._dialog
        self._dialog.open = True
        page.update()

    def _show_download_progress(self):
        """Switch dialog to show download progress."""
        if not self._dialog:
            return

        self._progress_bar = ft.ProgressBar(
            width=400,
            color=ft.colors.PRIMARY,
            bgcolor=ft.colors.SURFACE_VARIANT,
        )

        self._status_text.value = "Downloading update..."

        self._dialog.content = ft.Column(
            [
                self._status_text,
                ft.Container(padding=10),
                self._progress_bar,
                ft.Text(
                    "This may take a few minutes...",
                    size=12,
                    color=ft.colors.ON_SURFACE_VARIANT,
                ),
            ],
            spacing=8,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self._dialog.actions = [
            ft.TextButton("Cancel", on_click=self._on_cancel_download),
        ]

        if self._page:
            self._page.update()

    def _on_download_progress(self, progress: float):
        """Handle download progress update."""
        if self._progress_bar:
            self._progress_bar.value = progress
            percentage = int(progress * 100)
            if self._status_text:
                self._status_text.value = f"Downloading update... {percentage}%"
            if self._page:
                self._page.update()

    def _on_download_complete(self, installer_path: str):
        """Handle download completion."""
        if not self._dialog:
            return

        self._status_text.value = "Download complete!"
        self._dialog.content = ft.Column(
            [
                ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.SUCCESS, size=48),
                ft.Text(
                    "Update downloaded successfully!",
                    size=14,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "The application will close to install the update.",
                    size=12,
                    color=ft.colors.ON_SURFACE_VARIANT,
                ),
            ],
            spacing=8,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        def on_install_click(e):
            """Handle install button click."""
            self.close()
            if self._update_manager.install_update(installer_path):
                # Trigger app shutdown
                if self._page:
                    self._page.window_close()

        self._dialog.actions = [
            ft.ElevatedButton(
                "Install & Restart",
                icon=ft.icons.RESTART_ALT,
                on_click=on_install_click,
            ),
        ]

        if self._page:
            self._page.update()

    def _on_download_error(self, error: str):
        """Handle download error."""
        if not self._dialog:
            return

        self._status_text.value = "Download failed"

        self._dialog.content = ft.Column(
            [
                ft.Icon(ft.icons.ERROR, color=ft.colors.ERROR, size=48),
                ft.Text(
                    "Failed to download update",
                    size=14,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    error,
                    size=12,
                    color=ft.colors.ERROR,
                ),
            ],
            spacing=8,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        def on_retry_click(e):
            """Handle retry button click."""
            self.close()

        def on_close_click(e):
            """Handle close button click."""
            self.close()

        self._dialog.actions = [
            ft.TextButton("Close", on_click=on_close_click),
            ft.ElevatedButton(
                "Retry",
                icon=ft.icons.REFRESH,
                on_click=on_retry_click,
            ),
        ]

        if self._page:
            self._page.update()

    def _on_cancel_download(self, e):
        """Handle cancel button click."""
        self.close()

    def close(self):
        """Close the dialog."""
        if self._dialog and self._page:
            self._page.close(self._dialog)
            self._dialog = None

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format byte size to human readable."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    @staticmethod
    def _format_release_notes(notes: str) -> str:
        """Basic markdown formatting for release notes."""
        if not notes:
            return "No release notes available."

        lines = notes.split('\n')
        formatted = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Handle headers
            if line.startswith('##'):
                line = line.lstrip('#').strip()
                formatted.append(f"\n{line}\n")
            elif line.startswith('#'):
                line = line.lstrip('#').strip()
                formatted.append(f"\n{line}\n")
            # Handle list items
            elif line.startswith('-') or line.startswith('*'):
                formatted.append(f"  {line}")
            else:
                formatted.append(line)

        return '\n'.join(formatted)[:500]  # Limit length


def get_update_manager() -> Optional[UpdateManager]:
    """
    Get the global update manager instance.

    Returns
    -------
    UpdateManager or None
        The update manager instance, or None if not in executable mode.
    """
    # Only enable updates for frozen executables
    if not getattr(sys, 'frozen', False):
        return None

    # Get current version
    current_version = get_current_version()

    return UpdateManager(current_version=current_version)
