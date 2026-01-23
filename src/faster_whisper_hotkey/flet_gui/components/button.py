"""
Button component with modern styles and variants.

The Button component provides consistent button styling with multiple
variants (primary, secondary, danger, text, icon-only) and support
for icons and loading states.

Classes
-------
Button
    A styled button with multiple variants.
ButtonVariant
    Button style variants.
"""

from enum import Enum
from typing import Optional, Union

import flet as ft

from ..theme import get_theme_manager, BORDER_RADIUS, SPACING


class ButtonVariant(Enum):
    """Button style variants."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    DANGER = "danger"
    TEXT = "text"
    OUTLINED = "outlined"
    GHOST = "ghost"


class Button(ft.ElevatedButton):
    """
    A modern button with multiple style variants.

    The Button component provides consistent styling with support for
    icons, loading states, and multiple visual variants.

    Parameters
    ----------
    text
        Button text label.
    variant
        Button style variant.
    icon
        Optional icon name (ft.Icon) or icon enum.
    icon_position
        Position of icon ('left' or 'right').
    disabled
        Whether the button is disabled.
    loading
        Whether to show loading state.
    width
        Button width. None for auto.
    height
        Button height. None for auto.
    on_click
        Click handler.
    tooltip
        Optional tooltip.
    **kwargs
        Additional ElevatedButton properties.

    Examples
    --------
    >>> btn = Button("Save", variant=ButtonVariant.PRIMARY)
    >>> btn = Button("Delete", variant=ButtonVariant.DANGER, icon=ft.icons.DELETE)
    >>> btn = Button("Cancel", variant=ButtonVariant.TEXT)
    """

    def __init__(
        self,
        text: str,
        variant: ButtonVariant = ButtonVariant.PRIMARY,
        icon: Optional[Union[str, ft.Icon]] = None,
        icon_position: str = "left",
        disabled: bool = False,
        loading: bool = False,
        width: Optional[int] = None,
        height: Optional[int] = None,
        on_click=None,
        tooltip: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the Button component.

        Parameters
        ----------
        text
            Button text label.
        variant
            Button style variant.
        icon
            Optional icon.
        icon_position
            Position of icon ('left' or 'right').
        disabled
            Whether the button is disabled.
        loading
            Whether to show loading state.
        width
            Button width.
        height
            Button height.
        on_click
            Click handler.
        tooltip
            Optional tooltip.
        **kwargs
            Additional properties.
        """
        self._theme = get_theme_manager()
        self._variant = variant
        self._base_text = text
        self._base_icon = icon
        self._icon_position = icon_position

        # Build content based on icon and text
        content = self._build_content(text, icon, icon_position, loading)

        # Get button style
        style = self._get_style(variant)

        # Determine width/height
        btn_width = width if width is not None else self._get_default_width(variant)
        btn_height = height if height is not None else self._get_default_height(variant)

        super().__init__(
            content=content,
            style=style,
            width=btn_width,
            height=btn_height,
            disabled=disabled,
            on_click=on_click,
            tooltip=tooltip,
            **kwargs,
        )

    def _build_content(
        self,
        text: str,
        icon: Optional[Union[str, ft.Icon]],
        icon_position: str,
        loading: bool,
    ) -> ft.Row:
        """Build the button content row."""
        controls = []

        # Handle loading state
        if loading:
            loading_icon = ft.ProgressRing(
                width=16,
                height=16,
                stroke_width=2,
                color=self._get_loading_color(),
            )
            if icon_position == "left":
                controls.append(loading_icon)
            else:
                controls.insert(0, loading_icon)
        elif icon:
            # Convert string icon to ft.Icon if needed
            if isinstance(icon, str):
                icon_ctrl = ft.Icon(icon, size=18)
            else:
                icon_ctrl = icon

            if icon_position == "left":
                controls.append(icon_ctrl)
            else:
                controls.insert(0, icon_ctrl)

        # Add text (if not loading-only)
        if text and not loading:
            controls.append(ft.Text(text, size=14))

        return ft.Row(
            controls,
            spacing=SPACING.sm,
            alignment=ft.MainAxisAlignment.CENTER,
        )

    def _get_style(self, variant: ButtonVariant) -> ft.ButtonStyle:
        """Get the button style for a variant."""
        theme = self._theme

        shape = ft.RoundedRectangleBorder(radius=theme.radius.md)

        if variant == ButtonVariant.PRIMARY:
            return ft.ButtonStyle(
                bgcolor=theme.colors.primary,
                color=theme.colors.on_primary,
                shape=shape,
                padding=ft.padding.symmetric(horizontal=24, vertical=12),
            )
        elif variant == ButtonVariant.SECONDARY:
            return ft.ButtonStyle(
                bgcolor=theme.colors.secondary_container,
                color=theme.colors.on_secondary,
                shape=shape,
                padding=ft.padding.symmetric(horizontal=24, vertical=12),
            )
        elif variant == ButtonVariant.DANGER:
            return ft.ButtonStyle(
                bgcolor=theme.colors.error,
                color=theme.colors.on_error,
                shape=shape,
                padding=ft.padding.symmetric(horizontal=24, vertical=12),
            )
        elif variant == ButtonVariant.TEXT:
            return ft.ButtonStyle(
                bgcolor=ft.colors.TRANSPARENT,
                color=theme.colors.primary,
                shape=shape,
                padding=ft.padding.symmetric(horizontal=16, vertical=8),
            )
        elif variant == ButtonVariant.OUTLINED:
            return ft.ButtonStyle(
                bgcolor=ft.colors.TRANSPARENT,
                color=theme.colors.primary,
                shape=shape,
                side=ft.BorderSide(1, theme.colors.outline),
                padding=ft.padding.symmetric(horizontal=24, vertical=12),
            )
        else:  # GHOST
            return ft.ButtonStyle(
                bgcolor=ft.colors.TRANSPARENT,
                color=theme.colors.on_surface_variant,
                shape=shape,
                padding=ft.padding.symmetric(horizontal=16, vertical=8),
            )

    def _get_loading_color(self) -> str:
        """Get the loading indicator color."""
        theme = self._theme
        if self._variant in (ButtonVariant.PRIMARY, ButtonVariant.TEXT, ButtonVariant.OUTLINED):
            return theme.colors.on_primary
        elif self._variant == ButtonVariant.DANGER:
            return theme.colors.on_error
        else:
            return theme.colors.on_secondary

    def _get_default_width(self, variant: ButtonVariant) -> Optional[int]:
        """Get default width for variant."""
        return None  # Auto width

    def _get_default_height(self, variant: ButtonVariant) -> Optional[int]:
        """Get default height for variant."""
        return 40  # Standard button height

    def set_loading(self, loading: bool):
        """
        Set the loading state of the button.

        Parameters
        ----------
        loading
            Whether to show loading state.
        """
        self.content = self._build_content(
            self._base_text if not loading else "",
            self._base_icon if not loading else None,
            self._icon_position,
            loading,
        )
        self.disabled = loading
        self.update()

    @property
    def variant(self) -> ButtonVariant:
        """Get the button variant."""
        return self._variant
