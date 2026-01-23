"""
Notification and toast system for the Flet GUI.

This module provides a comprehensive notification system with toast messages,
notification queue management, and various notification types.

Classes
-------
NotificationType
    Types of notifications (info, success, warning, error).
Notification
    Single notification data.
Toast
    Toast notification UI component.
NotificationManager
    Manages notification queue and display.
"""

import logging
import platform
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Callable, List, Dict, Any

import flet as ft

from .theme import get_theme_manager, SPACING, BORDER_RADIUS, ANIMATION_DURATION

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Types of notifications."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"


@dataclass
class Notification:
    """
    Notification data.

    Attributes
    ----------
    id
        Unique notification ID.
    type
        Notification type.
    title
        Notification title.
    message
        Notification message/body.
    duration
        Display duration in milliseconds. 0 for no auto-dismiss.
    action_label
        Optional action button label.
    action_callback
        Optional action button callback.
    dismissable
        Whether user can dismiss manually.
    timestamp
        When the notification was created.
    """

    id: str
    type: NotificationType
    title: str
    message: str = ""
    duration: int = 4000
    action_label: Optional[str] = None
    action_callback: Optional[Callable] = None
    dismissable: bool = True
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Generate ID if not provided."""
        if not self.id:
            self.id = f"notif_{datetime.now().timestamp()}"


class Toast(ft.Container):
    """
    A toast notification UI component.

    Displays a notification with icon, title, message, optional action button,
    and dismiss button.

    Parameters
    ----------
    notification
        The notification to display.
    on_dismiss
        Callback when toast is dismissed.
    on_action
        Callback when action button is clicked.
    width
        Toast width.
    **kwargs
        Additional Container properties.

    Examples
    --------
    >>> notif = Notification(
    ...     id="1",
    ...     type=NotificationType.SUCCESS,
    ...     title="Saved!",
    ...     message="Settings saved successfully."
    ... )
    >>> toast = Toast(notif, on_dismiss=lambda: print("Dismissed"))
    """

    # Icon mapping for notification types
    ICONS = {
        NotificationType.INFO: ft.icons.INFO,
        NotificationType.SUCCESS: ft.icons.CHECK_CIRCLE,
        NotificationType.WARNING: ft.icons.WARNING,
        NotificationType.ERROR: ft.icons.ERROR,
        NotificationType.RECORDING: ft.icons.MIC,
        NotificationType.TRANSCRIBING: ft.icons.TRANSCRIBE,
    }

    def __init__(
        self,
        notification: Notification,
        on_dismiss: Optional[Callable] = None,
        on_action: Optional[Callable] = None,
        width: float = 350,
        **kwargs,
    ):
        """
        Initialize the Toast component.

        Parameters
        ----------
        notification
            The notification to display.
        on_dismiss
            Dismiss callback.
        on_action
            Action button callback.
        width
            Toast width.
        **kwargs
            Additional properties.
        """
        self._theme = get_theme_manager()
        self._notification = notification
        self._on_dismiss = on_dismiss
        self._on_action = on_action
        self._is_dismissing = False

        # Get colors based on type
        colors = self._get_colors(notification.type)

        # Build toast content
        content = self._build_content(notification, colors)

        super().__init__(
            content=content,
            width=width,
            bgcolor=colors["bg"],
            border_radius=BORDER_RADIUS.lg,
            border=ft.border.all(1, colors["border"]),
            padding=SPACING.md,
            shadow=ft.BoxShadow(
                blur_radius=20,
                spread_radius=0,
                color=ft.colors.with_opacity(0.15, ft.colors.BLACK),
                offset=ft.Offset(0, 4),
            ),
            animate=ft.Animation(
                duration=ANIMATION_DURATION.normal,
                curve=ft.AnimationCurve.EASE_OUT_CUBIC,
            ),
            **kwargs,
        )

    def _get_colors(self, notif_type: NotificationType) -> Dict[str, str]:
        """Get colors for notification type."""
        theme = self._theme

        color_map = {
            NotificationType.INFO: {
                "bg": theme.colors.info_container,
                "icon": theme.colors.info,
                "border": theme.colors.info,
            },
            NotificationType.SUCCESS: {
                "bg": theme.colors.success_container,
                "icon": theme.colors.success,
                "border": theme.colors.success,
            },
            NotificationType.WARNING: {
                "bg": theme.colors.warning_container,
                "icon": theme.colors.warning,
                "border": theme.colors.warning,
            },
            NotificationType.ERROR: {
                "bg": theme.colors.error_container,
                "icon": theme.colors.error,
                "border": theme.colors.error,
            },
            NotificationType.RECORDING: {
                "bg": theme.colors.error_container,
                "icon": theme.colors.recording,
                "border": theme.colors.recording,
            },
            NotificationType.TRANSCRIBING: {
                "bg": theme.colors.warning_container,
                "icon": theme.colors.transcribing,
                "border": theme.colors.transcribing,
            },
        }

        return color_map.get(notif_type, color_map[NotificationType.INFO])

    def _build_content(
        self,
        notification: Notification,
        colors: Dict[str, str],
    ) -> ft.Column:
        """Build the toast content."""
        controls = []

        # Top row: icon, title, dismiss button
        top_row = ft.Row(
            [
                ft.Icon(
                    self.ICONS.get(notification.type, ft.icons.INFO),
                    color=colors["icon"],
                    size=20,
                ),
                ft.Text(
                    notification.title,
                    size=14,
                    weight=ft.FontWeight.MEDIUM,
                    color=self._theme.colors.on_surface,
                    expand=True,
                ),
            ],
            spacing=SPACING.sm,
        )

        # Add dismiss button if dismissable
        if notification.dismissable:
            top_row.controls.append(
                ft.IconButton(
                    icon=ft.icons.CLOSE,
                    icon_size=16,
                    on_click=self._on_dismiss_click,
                    style=ft.ButtonStyle(
                        padding=0,
                    ),
                )
            )

        controls.append(top_row)

        # Add message if present
        if notification.message:
            controls.append(
                ft.Text(
                    notification.message,
                    size=13,
                    color=self._theme.colors.on_surface_variant,
                )
            )

        # Add action button if present
        if notification.action_label:
            action_btn = ft.TextButton(
                notification.action_label,
                on_click=self._on_action_click,
                style=ft.ButtonStyle(
                    color=colors["icon"],
                ),
            )
            controls.append(
                ft.Container(
                    content=action_btn,
                    alignment=ft.alignment.center_left,
                )
            )

        return ft.Column(controls, spacing=SPACING.xs, tight=True)

    def _on_dismiss_click(self, e):
        """Handle dismiss button click."""
        self.dismiss()

    def _on_action_click(self, e):
        """Handle action button click."""
        if self._on_action:
            self._on_action()
        if self._notification.action_callback:
            self._notification.action_callback()
        self.dismiss()

    def dismiss(self):
        """Dismiss the toast with animation."""
        if self._is_dismissing:
            return

        self._is_dismissing = True

        # Fade out
        self.opacity = 0
        self.offset = ft.transform.Offset(0, -0.1)
        self.update()

        # Schedule removal
        def remove():
            if self._on_dismiss:
                self._on_dismiss(self._notification.id)

        if self.page:
            self.page.run_thread(remove, delay=ANIMATION_DURATION.normal)

    @property
    def notification(self) -> Notification:
        """Get the notification data."""
        return self._notification


class NotificationManager:
    """
    Manages notification queue and display.

    Handles queuing, displaying, and dismissing notifications with
    position management and history tracking.

    Attributes
    ----------
    toasts
        Currently displayed toasts by ID.
    history
        Notification history.
    max_toasts
        Maximum visible toasts at once.
    max_history
        Maximum history entries to keep.
    tray_manager
        Optional tray manager for system tray notifications.
    enable_tray_notifications
        Whether to show tray notifications for important events.
    """

    def __init__(
        self,
        page: ft.Page,
        max_toasts: int = 3,
        max_history: int = 50,
        position: str = "top_right",
        tray_manager=None,
        enable_tray_notifications: bool = True,
    ):
        """
        Initialize the NotificationManager.

        Parameters
        ----------
        page
            The Flet page to display toasts on.
        max_toasts
            Maximum visible toasts.
        max_history
            Maximum history entries.
        position
            Toast position ('top_right', 'top_left', 'bottom_right', 'bottom_left').
        tray_manager
            Optional tray manager for system tray notifications.
        enable_tray_notifications
            Whether to show tray notifications for important events.
        """
        self._page = page
        self._max_toasts = max_toasts
        self._max_history = max_history
        self._position = position
        self._lock = threading.Lock()
        self._tray_manager = tray_manager
        self._enable_tray_notifications = enable_tray_notifications

        self.toasts: Dict[str, Toast] = {}
        self.history: List[Notification] = []
        self._toast_stack: Optional[ft.Stack] = None
        self._toast_container: Optional[ft.Container] = None

        # Initialize toast container
        self._initialize_container()

    def _initialize_container(self):
        """Initialize the toast container stack."""
        self._toast_stack = ft.Stack(
            [],
            width=400,
            spacing=SPACING.sm,
        )

        # Position container
        alignment_map = {
            "top_right": ft.alignment.top_right,
            "top_left": ft.alignment.top_left,
            "bottom_right": ft.alignment.bottom_right,
            "bottom_left": ft.alignment.bottom_left,
        }

        self._toast_container = ft.Container(
            content=self._toast_stack,
            padding=SPACING.md,
            alignment=alignment_map.get(self._position, ft.alignment.top_right),
            visible=False,
        )

        # Add to page overlay (if supported)
        # For now, we'll add to page content
        # The page needs to support overlay positioning

    def show(
        self,
        title: str,
        message: str = "",
        type: NotificationType = NotificationType.INFO,
        duration: int = 4000,
        action_label: Optional[str] = None,
        action_callback: Optional[Callable] = None,
    ) -> str:
        """
        Show a notification toast.

        Parameters
        ----------
        title
            Notification title.
        message
            Notification message.
        type
            Notification type.
        duration
            Display duration in ms. 0 for no auto-dismiss.
        action_label
            Action button label.
        action_callback
            Action button callback.

        Returns
        -------
        str
            Notification ID.
        """
        notification = Notification(
            id="",
            type=type,
            title=title,
            message=message,
            duration=duration,
            action_label=action_label,
            action_callback=action_callback,
        )

        return self._show_notification(notification)

    def _show_notification(self, notification: Notification) -> str:
        """Show a notification toast."""
        with self._lock:
            # Add to history
            self.history.append(notification)
            if len(self.history) > self._max_history:
                self.history.pop(0)

            # Remove oldest toast if at max
            if len(self.toasts) >= self._max_toasts:
                oldest_id = next(iter(self.toasts))
                self._remove_toast(oldest_id)

            # Create toast
            toast = Toast(
                notification=notification,
                on_dismiss=self._on_toast_dismiss,
                on_action=None,
            )

            self.toasts[notification.id] = toast

        # Add to UI
        if self._toast_stack:
            self._toast_stack.controls.append(toast)
            self._toast_container.visible = True
            self._update_toast_positions()

            if self._page:
                self._page.add(self._toast_container)
                self._page.update()

                # Schedule auto-dismiss
                if notification.duration > 0:
                    self._schedule_dismiss(notification.id, notification.duration)

        # Show tray notification for important events
        self._show_tray_notification(notification)

        return notification.id

    def _show_tray_notification(self, notification: Notification):
        """Show a system tray notification if enabled and available."""
        if not self._enable_tray_notifications or not self._tray_manager:
            return

        # Only show tray notifications for important notification types
        important_types = (
            NotificationType.SUCCESS,
            NotificationType.ERROR,
            NotificationType.WARNING,
        )

        if notification.type not in important_types:
            return

        # Build notification message
        title = notification.title
        message = notification.message if notification.message else ""

        # Show via tray manager
        try:
            self._tray_manager.notify(title, message)
        except Exception as e:
            logger.debug(f"Failed to show tray notification: {e}")

    def set_tray_manager(self, tray_manager):
        """
        Set or update the tray manager.

        Parameters
        ----------
        tray_manager
            The tray manager instance.
        """
        self._tray_manager = tray_manager

    def set_tray_notifications_enabled(self, enabled: bool):
        """
        Enable or disable tray notifications.

        Parameters
        ----------
        enabled
            Whether to enable tray notifications.
        """
        self._enable_tray_notifications = enabled

    def _remove_toast(self, notif_id: str):
        """Remove a toast from display."""
        if notif_id in self.toasts:
            toast = self.toasts.pop(notif_id)
            if self._toast_stack and toast in self._toast_stack.controls:
                self._toast_stack.controls.remove(toast)
                self._update_toast_positions()

            if not self.toasts and self._toast_container:
                self._toast_container.visible = False

    def _on_toast_dismiss(self, notif_id: str):
        """Handle toast dismissal."""
        self._remove_toast(notif_id)
        if self._page:
            self._page.update()

    def _schedule_dismiss(self, notif_id: str, duration: int):
        """Schedule auto-dismissal."""
        def dismiss():
            if notif_id in self.toasts:
                self.toasts[notif_id].dismiss()

        if self._page:
            self._page.run_thread(dismiss, delay=duration)

    def _update_toast_positions(self):
        """Update positions of all toasts for stacking."""
        offset_y = 0
        for toast in reversed(self._toast_stack.controls):
            toast.top = offset_y
            offset_y += toast.height + SPACING.sm

    def dismiss_all(self):
        """Dismiss all active toasts."""
        with self._lock:
            for notif_id in list(self.toasts.keys()):
                self.toasts[notif_id].dismiss()

    def get_history(self) -> List[Notification]:
        """Get notification history."""
        return self.history.copy()

    # Convenience methods
    def info(self, title: str, message: str = "", **kwargs) -> str:
        """Show info notification."""
        return self.show(title, message, NotificationType.INFO, **kwargs)

    def success(self, title: str, message: str = "", **kwargs) -> str:
        """Show success notification."""
        return self.show(title, message, NotificationType.SUCCESS, **kwargs)

    def warning(self, title: str, message: str = "", **kwargs) -> str:
        """Show warning notification."""
        return self.show(title, message, NotificationType.WARNING, **kwargs)

    def error(self, title: str, message: str = "", **kwargs) -> str:
        """Show error notification."""
        return self.show(title, message, NotificationType.ERROR, **kwargs)


# Global notification manager instance
_notification_manager: Optional[NotificationManager] = None


def get_notification_manager() -> Optional[NotificationManager]:
    """
    Get the global notification manager.

    Returns
    -------
    NotificationManager or None
        The global notification manager, or None if not initialized.
    """
    return _notification_manager


def init_notifications(page: ft.Page, **kwargs) -> NotificationManager:
    """
    Initialize the global notification manager.

    Parameters
    ----------
    page
        The Flet page.
    **kwargs
        Additional NotificationManager arguments.

    Returns
    -------
    NotificationManager
        The initialized notification manager.
    """
    global _notification_manager
    _notification_manager = NotificationManager(page, **kwargs)
    return _notification_manager


def show_notification(
    title: str,
    message: str = "",
    type: NotificationType = NotificationType.INFO,
    **kwargs,
) -> Optional[str]:
    """
    Show a notification using the global manager.

    Parameters
    ----------
    title
        Notification title.
    message
        Notification message.
    type
        Notification type.
    **kwargs
        Additional notification options.

    Returns
    -------
    str or None
        Notification ID, or None if manager not initialized.
    """
    manager = get_notification_manager()
    if manager:
        return manager.show(title, message, type, **kwargs)
    return None


class NotificationHistoryPanel(ft.Container):
    """
    A panel for viewing notification history.

    Displays past notifications with filtering options and the ability
    to clear history.

    Parameters
    ----------
    notification_manager
        The notification manager to get history from.
    on_close
        Callback when the panel is closed.
    width
        Panel width.
    height
        Panel height.
    **kwargs
        Additional Container properties.

    Examples
    --------
    >>> panel = NotificationHistoryPanel(
    ...     notification_manager=manager,
    ...     on_close=lambda: print("Closed"),
    ... )
    """

    def __init__(
        self,
        notification_manager: NotificationManager,
        on_close=None,
        width: float = 500,
        height: float = 600,
        **kwargs,
    ):
        """Initialize the NotificationHistoryPanel."""
        self._theme = get_theme_manager()
        self._manager = notification_manager
        self._on_close = on_close
        self._filter_type: Optional[NotificationType] = None
        self._history_list: Optional[ft.ListView] = None
        self._empty_state: Optional[ft.Container] = None
        self._count_text: Optional[ft.Text] = None

        super().__init__(
            content=self._build_content(),
            width=width,
            height=height,
            bgcolor=self._theme.colors.surface,
            border_radius=BORDER_RADIUS.xl,
            **kwargs,
        )

    def _build_content(self) -> ft.Column:
        """Build the panel content."""
        # Header with title and close button
        header = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(
                        ft.icons.NOTIFICATIONS,
                        color=self._theme.colors.primary,
                        size=24,
                    ),
                    ft.Text(
                        "Notification History",
                        size=18,
                        weight=ft.FontWeight.SEMIBOLD,
                        color=self._theme.colors.on_surface,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.icons.CLOSE,
                        icon_size=20,
                        on_click=self._on_close_click,
                        style=ft.ButtonStyle(
                            padding=0,
                        ),
                    ),
                ],
                spacing=SPACING.sm,
            ),
            padding=ft.padding.symmetric(horizontal=SPACING.md, vertical=SPACING.sm),
            border=ft.border.only(bottom=ft.BorderSide(1, self._theme.colors.outline_variant)),
        )

        # Filter chips row
        self._filter_chips = self._build_filter_chips()

        # Count and clear row
        self._count_text = ft.Text(
            "0 notifications",
            size=12,
            color=self._theme.colors.on_surface_variant,
        )

        actions_row = ft.Container(
            content=ft.Row(
                [
                    self._count_text,
                    ft.Container(expand=True),
                    ft.TextButton(
                        "Clear History",
                        icon=ft.icons.DELETE_OUTLINE,
                        on_click=self._on_clear_history,
                    ),
                ],
            ),
            padding=ft.padding.symmetric(horizontal=SPACING.md, vertical=SPACING.sm),
        )

        # History list (will be populated)
        self._history_list = ft.ListView(
            expand=True,
            spacing=0,
            padding=ft.padding.only(bottom=SPACING.md),
        )

        # Empty state
        self._empty_state = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(
                        ft.icons.NOTIFICATIONS_NONE_OUTLINED,
                        size=48,
                        color=self._theme.colors.on_surface_variant,
                    ),
                    ft.Text(
                        "No notifications yet",
                        size=14,
                        color=self._theme.colors.on_surface_variant,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=SPACING.sm,
            ),
            padding=SPACING.xxl,
            alignment=ft.alignment.center,
        )

        # Main content column
        content = ft.Column(
            [
                header,
                self._filter_chips,
                actions_row,
                ft.Container(
                    content=self._history_list,
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        )

        return content

    def _build_filter_chips(self) -> ft.Container:
        """Build filter type chips."""
        chips = []

        # All filter
        all_chip = ft.ChoiceChip(
            label="All",
            selected=True,
            on_click=lambda _: self._set_filter(None),
            label_style=ft.TextStyle(size=12),
        )
        chips.append(all_chip)

        # Type filters
        type_labels = {
            NotificationType.SUCCESS: "Success",
            NotificationType.ERROR: "Errors",
            NotificationType.WARNING: "Warnings",
            NotificationType.INFO: "Info",
            NotificationType.RECORDING: "Recording",
            NotificationType.TRANSCRIBING: "Transcribing",
        }

        for notif_type, label in type_labels.items():
            chip = ft.ChoiceChip(
                label=label,
                on_click=lambda _, t=notif_type: self._set_filter(t),
                label_style=ft.TextStyle(size=12),
            )
            chips.append(chip)

        self._filter_chip_group = ft.ChipGroup(
            chips=chips,
            wrap=True,
        )

        return ft.Container(
            content=self._filter_chip_group,
            padding=ft.padding.symmetric(horizontal=SPACING.md, vertical=SPACING.sm),
            border=ft.border.only(bottom=ft.BorderSide(1, self._theme.colors.outline_variant)),
        )

    def _set_filter(self, filter_type: Optional[NotificationType]):
        """Set the notification type filter."""
        self._filter_type = filter_type
        self._refresh_history()

    def _refresh_history(self):
        """Refresh the history list."""
        if not self._history_list:
            return

        # Get filtered history
        history = self._manager.get_history()

        if self._filter_type:
            history = [n for n in history if n.type == self._filter_type]

        # Update count
        if self._count_text:
            self._count_text.text = f"{len(history)} notification{'s' if len(history) != 1 else ''}"

        # Clear list
        self._history_list.controls.clear()

        if not history:
            # Show empty state
            self._history_list.controls.append(
                ft.Container(content=self._empty_state, expand=True)
            )
        else:
            # Add notification items (newest first)
            for notification in reversed(history):
                item = self._build_history_item(notification)
                self._history_list.controls.append(item)

        self.update()

    def _build_history_item(self, notification: Notification) -> ft.Container:
        """Build a single history item."""
        colors = self._get_colors(notification.type)
        icon = Toast.ICONS.get(notification.type, ft.icons.INFO)

        # Format timestamp
        time_str = notification.timestamp.strftime("%H:%M")
        date_str = notification.timestamp.strftime("%b %d")

        # Build item content
        content = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(
                        icon,
                        color=colors["icon"],
                        size=18,
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                notification.title,
                                size=13,
                                weight=ft.FontWeight.MEDIUM,
                                color=self._theme.colors.on_surface,
                            ),
                            ft.Text(
                                notification.message or "No message",
                                size=12,
                                color=self._theme.colors.on_surface_variant,
                                max_lines=2,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ) if notification.message else None,
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                time_str,
                                size=11,
                                color=self._theme.colors.on_surface_variant,
                            ),
                            ft.Text(
                                date_str,
                                size=10,
                                color=self._theme.colors.on_surface_variant,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                        spacing=0,
                    ),
                ],
                spacing=SPACING.sm,
            ),
            padding=ft.padding.symmetric(horizontal=SPACING.md, vertical=SPACING.sm),
            border=ft.border.only(
                bottom=ft.BorderSide(1, self._theme.colors.outline_variant)
            ),
        )

        return content

    def _get_colors(self, notif_type: NotificationType) -> dict:
        """Get colors for notification type."""
        theme = self._theme

        color_map = {
            NotificationType.INFO: {
                "bg": theme.colors.info_container,
                "icon": theme.colors.info,
                "border": theme.colors.info,
            },
            NotificationType.SUCCESS: {
                "bg": theme.colors.success_container,
                "icon": theme.colors.success,
                "border": theme.colors.success,
            },
            NotificationType.WARNING: {
                "bg": theme.colors.warning_container,
                "icon": theme.colors.warning,
                "border": theme.colors.warning,
            },
            NotificationType.ERROR: {
                "bg": theme.colors.error_container,
                "icon": theme.colors.error,
                "border": theme.colors.error,
            },
            NotificationType.RECORDING: {
                "bg": theme.colors.error_container,
                "icon": theme.colors.recording,
                "border": theme.colors.recording,
            },
            NotificationType.TRANSCRIBING: {
                "bg": theme.colors.warning_container,
                "icon": theme.colors.transcribing,
                "border": theme.colors.transcribing,
            },
        }

        return color_map.get(notif_type, color_map[NotificationType.INFO])

    def _on_close_click(self, e):
        """Handle close button click."""
        if self._on_close:
            self._on_close()

    def _on_clear_history(self, e):
        """Handle clear history button click."""
        self._manager.history.clear()
        self._refresh_history()

    def refresh(self):
        """Refresh the history display."""
        self._refresh_history()


class SoundNotificationManager:
    """
    Manages sound notifications with volume control.

    Provides optional audio feedback for various events with
    configurable volume and per-event sound settings.

    Attributes
    ----------
    enabled
        Whether sound notifications are enabled.
    volume
        Master volume level (0.0 to 1.0).
    sounds_enabled
        Dictionary mapping event types to sound enabled state.
    """

    # Sound event types
    EVENT_TRANSCRIPTION_COMPLETE = "transcription_complete"
    EVENT_ERROR = "error"
    EVENT_RECORDING_START = "recording_start"
    EVENT_MODEL_DOWNLOAD_COMPLETE = "model_download_complete"
    EVENT_SETTINGS_SAVED = "settings_saved"

    # Default sounds (using Windows system sounds where possible)
    DEFAULT_SOUNDS = {
        EVENT_TRANSCRIPTION_COMPLETE: "SystemAsterisk",
        EVENT_ERROR: "SystemHand",
        EVENT_RECORDING_START: "SystemExclamation",
        EVENT_MODEL_DOWNLOAD_COMPLETE: "SystemExclamation",
        EVENT_SETTINGS_SAVED: "SystemAsterisk",
    }

    def __init__(self):
        """Initialize the SoundNotificationManager."""
        self._enabled = True
        self._volume = 0.5
        self._sounds_enabled: dict = {
            self.EVENT_TRANSCRIPTION_COMPLETE: True,
            self.EVENT_ERROR: True,
            self.EVENT_RECORDING_START: False,
            self.EVENT_MODEL_DOWNLOAD_COMPLETE: True,
            EVENT_SETTINGS_SAVED: False,
        }
        self._config_path = self._get_config_path()
        self._platform = platform.system()

        # Load saved settings
        self._load_settings()

    def _get_config_path(self) -> Path:
        """Get the configuration file path."""
        from pathlib import Path
        config_dir = Path.home() / ".faster-whisper-hotkey"
        return config_dir / "sound_settings.json"

    def _load_settings(self):
        """Load sound settings from disk."""
        try:
            if self._config_path.exists():
                import json
                data = json.loads(self._config_path.read_text())
                self._enabled = data.get("enabled", True)
                self._volume = data.get("volume", 0.5)
                self._sounds_enabled = data.get("sounds_enabled", self._sounds_enabled)
        except Exception as e:
            logger.warning(f"Failed to load sound settings: {e}")

    def _save_settings(self):
        """Save sound settings to disk."""
        try:
            import json
            from pathlib import Path
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            self._config_path.write_text(
                json.dumps({
                    "enabled": self._enabled,
                    "volume": self._volume,
                    "sounds_enabled": self._sounds_enabled,
                })
            )
        except Exception as e:
            logger.warning(f"Failed to save sound settings: {e}")

    def play(self, event: str):
        """
        Play a sound for the given event.

        Parameters
        ----------
        event
            The event type key (e.g., EVENT_TRANSCRIPTION_COMPLETE).
        """
        if not self._enabled or not self._sounds_enabled.get(event, False):
            return

        try:
            if self._platform == "Windows":
                self._play_windows(event)
            elif self._platform == "Darwin":  # macOS
                self._play_macos(event)
            else:  # Linux and others
                self._play_linux(event)
        except Exception as e:
            logger.debug(f"Failed to play sound: {e}")

    def _play_windows(self, event: str):
        """Play sound on Windows using winsound."""
        try:
            import winsound
            sound_name = self.DEFAULT_SOUNDS.get(event, "SystemAsterisk")

            # Play system sound
            winsound.MessageBeep(
                getattr(winsound, sound_name.upper(), winsound.MB_ICONASTERISK)
            )
        except ImportError:
            # Fallback: simple beep
            try:
                import winsound
                winsound.Beep(800, 100)
            except Exception:
                pass

    def _play_macos(self, event: str):
        """Play sound on macOS using afplay."""
        try:
            import subprocess
            # Use default system sound
            subprocess.run(
                ["afplay", "/System/Library/Sounds/Glass.aiff"],
                capture_output=True,
                check=False,
            )
        except Exception:
            pass

    def _play_linux(self, event: str):
        """Play sound on Linux using paplay or aplay."""
        try:
            import subprocess
            # Try paplay (PulseAudio)
            subprocess.run(
                ["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"],
                capture_output=True,
                check=False,
            )
        except Exception:
            try:
                # Fallback to aplay (ALSA)
                subprocess.run(
                    ["aplay", "/usr/share/sounds/alsa/Front_Center.wav"],
                    capture_output=True,
                    check=False,
                )
            except Exception:
                pass

    @property
    def enabled(self) -> bool:
        """Check if sound notifications are enabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        """Set sound notifications enabled state."""
        self._enabled = value
        self._save_settings()

    @property
    def volume(self) -> float:
        """Get master volume level (0.0 to 1.0)."""
        return self._volume

    @volume.setter
    def volume(self, value: float):
        """Set master volume level."""
        self._volume = max(0.0, min(1.0, value))
        self._save_settings()

    def is_event_enabled(self, event: str) -> bool:
        """
        Check if sound is enabled for a specific event.

        Parameters
        ----------
        event
            The event type key.

        Returns
        -------
        bool
            True if sound is enabled for this event.
        """
        return self._sounds_enabled.get(event, False)

    def set_event_enabled(self, event: str, enabled: bool):
        """
        Set sound enabled state for a specific event.

        Parameters
        ----------
        event
            The event type key.
        enabled
            Whether to enable sound for this event.
        """
        self._sounds_enabled[event] = enabled
        self._save_settings()

    def toggle_event(self, event: str) -> bool:
        """
        Toggle sound for a specific event.

        Parameters
        ----------
        event
            The event type key.

        Returns
        -------
        bool
            The new enabled state.
        """
        new_state = not self._sounds_enabled.get(event, False)
        self._sounds_enabled[event] = new_state
        self._save_settings()
        return new_state


# Global sound notification manager instance
_sound_manager: Optional[SoundNotificationManager] = None


def get_sound_manager() -> SoundNotificationManager:
    """
    Get the global sound notification manager.

    Returns
    -------
    SoundNotificationManager
        The global sound manager.
    """
    global _sound_manager
    if _sound_manager is None:
        _sound_manager = SoundNotificationManager()
    return _sound_manager


def play_notification_sound(event: str):
    """
    Play a notification sound using the global sound manager.

    Parameters
    ----------
    event
        The event type key (e.g., SoundNotificationManager.EVENT_TRANSCRIPTION_COMPLETE).
    """
    manager = get_sound_manager()
    if manager.enabled:
        manager.play(event)
