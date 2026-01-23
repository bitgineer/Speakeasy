"""
Toggle switch component for boolean settings.

The ToggleSwitch component provides a modern toggle/switch control for
boolean settings with labels and descriptions.

Classes
-------
ToggleSwitch
    A modern toggle switch for boolean values.
"""

from typing import Optional, Callable

import flet as ft

from ..theme import get_theme_manager, SPACING


class ToggleSwitch(ft.Row):
    """
    A modern toggle switch for boolean settings.

    The ToggleSwitch combines a Flet Switch with an optional label
    and description for a complete toggle control.

    Parameters
    ----------
    label
        Main label text.
    description
        Optional secondary description text.
    value
        Initial toggle state.
    on_change
        Callback when toggle state changes.
    disabled
        Whether the toggle is disabled.
    active_color
        Color when active. None uses theme primary.
    **kwargs
        Additional Row properties.

    Examples
    --------
    >>> toggle = ToggleSwitch("Dark Mode", value=False)
    >>> toggle = ToggleSwitch(
    ...     "Enable notifications",
    ...     description="Receive push notifications",
    ...     value=True,
    ... )
    """

    def __init__(
        self,
        label: str,
        description: Optional[str] = None,
        value: bool = False,
        on_change: Optional[Callable[[bool], None]] = None,
        disabled: bool = False,
        active_color: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the ToggleSwitch component.

        Parameters
        ----------
        label
            Main label text.
        description
            Optional description text.
        value
            Initial toggle state.
        on_change
            Change callback.
        disabled
            Whether disabled.
        active_color
            Active color. None uses theme primary.
        **kwargs
            Additional Row properties.
        """
        self._theme = get_theme_manager()
        self._on_change_callback = on_change
        self._active_color_override = active_color

        # Create the switch
        self._switch = ft.Switch(
            value=value,
            active_color=active_color or self._theme.colors.primary,
            disabled=disabled,
            on_change=self._on_change,
        )

        # Create label column
        label_controls = [
            ft.Text(
                label,
                size=14,
                weight=ft.FontWeight.MEDIUM,
                color=self._theme.colors.on_surface,
            )
        ]

        if description:
            label_controls.append(
                ft.Text(
                    description,
                    size=12,
                    color=self._theme.colors.on_surface_variant,
                )
            )

        self._label_column = ft.Column(
            controls=label_controls,
            spacing=2,
            expand=True,
        )

        # Build the row
        super().__init__(
            controls=[
                self._label_column,
                self._switch,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            spacing=SPACING.md,
            **kwargs,
        )

    def _on_change(self, e):
        """Handle switch change."""
        if self._on_change_callback:
            self._on_change_callback(e.data == "true")

    @property
    def value(self) -> bool:
        """Get the toggle state."""
        return self._switch.value

    @value.setter
    def value(self, val: bool):
        """Set the toggle state."""
        self._switch.value = val
        self._switch.update()

    @property
    def switch(self) -> ft.Switch:
        """Get the underlying Switch control."""
        return self._switch
