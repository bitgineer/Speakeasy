"""
Collapsible sidebar component for quick settings access.

This module provides a modern, collapsible sidebar that can be used
to display quick settings, model info, and other controls.

Classes
-------
SidebarItem
    A single sidebar item with icon and label.
CollapsibleSidebar
    A collapsible sidebar with multiple items.
"""

from enum import Enum
from typing import Optional, List, Callable

import flet as ft

from ..theme import get_theme_manager, SPACING, BORDER_RADIUS, ANIMATION_DURATION


class SidebarItem:
    """
    A single sidebar item.

    Parameters
    ----------
    icon
        Icon to display.
    label
        Text label for the item.
    on_click
        Click handler.
    value
        Optional value associated with the item.
    badge
        Optional badge text to display.
    """

    def __init__(
        self,
        icon: str,
        label: str,
        on_click: Optional[Callable] = None,
        value: Optional[str] = None,
        badge: Optional[str] = None,
    ):
        """
        Initialize the SidebarItem.

        Parameters
        ----------
        icon
            Icon name.
        label
            Item label.
        on_click
            Click handler.
        value
            Optional value.
        badge
            Optional badge text.
        """
        self.icon = icon
        self.label = label
        self.on_click = on_click
        self.value = value
        self.badge = badge


class SidebarPosition(Enum):
    """Sidebar position options."""

    LEFT = "left"
    RIGHT = "right"


class CollapsibleSidebar(ft.Container):
    """
    A collapsible sidebar component.

    The sidebar can be expanded/collapsed with animation and displays
    a list of items with icons and labels.

    Parameters
    ----------
    items
        List of SidebarItem objects to display.
    position
        Position of the sidebar ('left' or 'right').
    width
        Width of the expanded sidebar.
    collapsed_width
        Width when collapsed.
    initially_expanded
        Whether the sidebar starts expanded.
    on_toggle
        Callback when sidebar is toggled.
    **kwargs
        Additional Container properties.

    Examples
    --------
    >>> items = [
    ...     SidebarItem(ft.icons.SETTINGS, "Settings", on_click=lambda e: print("Settings")),
    ...     SidebarItem(ft.icons.HISTORY, "History", on_click=lambda e: print("History")),
    ... ]
    >>> sidebar = CollapsibleSidebar(items=items)
    >>> sidebar.toggle()
    """

    def __init__(
        self,
        items: List[SidebarItem],
        position: SidebarPosition = SidebarPosition.LEFT,
        width: float = 200,
        collapsed_width: float = 60,
        initially_expanded: bool = True,
        on_toggle: Optional[Callable[[bool], None]] = None,
        **kwargs,
    ):
        """
        Initialize the CollapsibleSidebar.

        Parameters
        ----------
        items
            List of sidebar items.
        position
            Sidebar position.
        width
            Expanded width.
        collapsed_width
            Collapsed width.
        initially_expanded
            Initial expanded state.
        on_toggle
            Toggle callback.
        **kwargs
            Additional properties.
        """
        self._theme = get_theme_manager()
        self._items = items
        self._position = position
        self._expanded_width = width
        self._collapsed_width = collapsed_width
        self._is_expanded = initially_expanded
        self._on_toggle = on_toggle

        # Build sidebar content
        self._content_column = self._build_content()
        self._toggle_button = self._build_toggle_button()

        # Main container
        super().__init__(
            content=ft.Column(
                [
                    self._content_column,
                    self._toggle_button,
                ],
                spacing=0,
            ),
            width=self._expanded_width if initially_expanded else self._collapsed_width,
            bgcolor=self._theme.colors.surface,
            border=ft.border.only(
                right=ft.BorderSide(1, self._theme.colors.outline_variant)
                if position == SidebarPosition.LEFT
                else None,
                left=ft.BorderSide(1, self._theme.colors.outline_variant)
                if position == SidebarPosition.RIGHT
                else None,
            ),
            padding=SPACING.sm,
            animate=ft.Animation(
                duration=ANIMATION_DURATION.normal,
                curve=ft.AnimationCurve.EASE_OUT_CUBIC,
            ),
            **kwargs,
        )

    def _build_content(self) -> ft.Column:
        """Build the sidebar content column."""
        items = []

        for item in self._items:
            item_row = self._build_item(item)
            items.append(item_row)

        return ft.Column(
            items,
            spacing=SPACING.xs,
        )

    def _build_item(self, item: SidebarItem) -> ft.Container:
        """Build a single sidebar item."""
        theme = self._theme

        # Icon
        icon = ft.Icon(
            item.icon,
            size=20,
            color=theme.colors.on_surface_variant,
        )

        # Label
        label = ft.Text(
            item.label,
            size=13,
            color=theme.colors.on_surface,
            overflow=ft.TextOverflow.ELLIPSIS,
            expand=True,
        )

        # Badge (optional)
        badge = None
        if item.badge:
            badge = ft.Container(
                content=ft.Text(
                    item.badge,
                    size=10,
                    weight=ft.FontWeight.MEDIUM,
                    color=theme.colors.on_primary,
                ),
                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                bgcolor=theme.colors.primary,
                border_radius=8,
            )

        # Build row
        controls = [icon, label]
        if badge:
            controls.append(badge)

        content = ft.Row(
            controls,
            spacing=SPACING.sm,
            alignment=ft.MainAxisAlignment.START,
            expand=True,
        )

        item_container = ft.Container(
            content=content,
            padding=ft.padding.symmetric(horizontal=SPACING.sm, vertical=SPACING.xs),
            border_radius=theme.radius.md,
            on_click=lambda e, i=item: self._on_item_click(e, i),
        )

        # Set cursor
        item_container.cursor = ft.MouseCursor.CLICKER

        return item_container

    def _build_toggle_button(self) -> ft.Container:
        """Build the toggle button."""
        theme = self._theme

        # Determine icon based on position and expanded state
        if self._position == SidebarPosition.LEFT:
            icon = ft.icons.CHEVRON_LEFT if self._is_expanded else ft.icons.CHEVRON_RIGHT
        else:
            icon = ft.icons.CHEVRON_RIGHT if self._is_expanded else ft.icons.CHEVRON_LEFT

        button = ft.Container(
            content=ft.Icon(
                icon,
                size=18,
                color=theme.colors.on_surface_variant,
            ),
            width=32,
            height=32,
            alignment=ft.alignment.center,
            border_radius=16,
            on_click=self._on_toggle_click,
        )

        # Set cursor
        button.cursor = ft.MouseCursor.CLICKER

        # Set alignment based on position
        if self._position == SidebarPosition.LEFT:
            if self._is_expanded:
                button.alignment = ft.alignment.center_right
            else:
                button.alignment = ft.alignment.center
        else:
            if self._is_expanded:
                button.alignment = ft.alignment.center_left
            else:
                button.alignment = ft.alignment.center

        return button

    def _on_item_click(self, e, item: SidebarItem):
        """Handle item click."""
        if item.on_click:
            item.on_click(e)

    def _on_toggle_click(self, e):
        """Handle toggle button click."""
        self.toggle()

    def toggle(self):
        """
        Toggle the sidebar expanded/collapsed state.

        Updates the width, item visibility, and toggle button icon.
        """
        self._is_expanded = not self._is_expanded

        # Update width
        self.width = self._expanded_width if self._is_expanded else self._collapsed_width

        # Update item label visibility
        for item_container in self._content_column.controls:
            if isinstance(item_container, ft.Container):
                if isinstance(item_container.content, ft.Row):
                    # Hide/show labels (index 1) and badges (index 2)
                    for i, control in enumerate(item_container.content.controls):
                        if i == 1:  # Label
                            control.visible = self._is_expanded
                        elif i == 2 and isinstance(control, ft.Container):  # Badge
                            control.visible = self._is_expanded

        # Update toggle button icon
        if self._position == SidebarPosition.LEFT:
            new_icon = ft.icons.CHEVRON_LEFT if self._is_expanded else ft.icons.CHEVRON_RIGHT
            if self._is_expanded:
                self._toggle_button.alignment = ft.alignment.center_right
            else:
                self._toggle_button.alignment = ft.alignment.center
        else:
            new_icon = ft.icons.CHEVRON_RIGHT if self._is_expanded else ft.icons.CHEVRON_LEFT
            if self._is_expanded:
                self._toggle_button.alignment = ft.alignment.center_left
            else:
                self._toggle_button.alignment = ft.alignment.center

        self._toggle_button.content.icon = new_icon

        # Update
        self.update()

        # Notify callback
        if self._on_toggle:
            self._on_toggle(self._is_expanded)

    def expand(self):
        """Expand the sidebar."""
        if not self._is_expanded:
            self.toggle()

    def collapse(self):
        """Collapse the sidebar."""
        if self._is_expanded:
            self.toggle()

    @property
    def is_expanded(self) -> bool:
        """Check if the sidebar is expanded."""
        return self._is_expanded

    @property
    def items(self) -> List[SidebarItem]:
        """Get the sidebar items."""
        return self._items
