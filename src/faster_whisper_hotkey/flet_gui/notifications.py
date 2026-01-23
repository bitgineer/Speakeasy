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
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
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
    """

    def __init__(
        self,
        page: ft.Page,
        max_toasts: int = 3,
        max_history: int = 50,
        position: str = "top_right",
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
        """
        self._page = page
        self._max_toasts = max_toasts
        self._max_history = max_history
        self._position = position
        self._lock = threading.Lock()

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

        return notification.id

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
