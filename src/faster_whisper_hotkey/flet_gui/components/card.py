"""
Card component for displaying content in elevated containers.

The Card component provides a consistent, styled container for grouping
related content with optional elevation, padding, and borders.

Classes
-------
Card
    A rounded container with elevation and optional visual effects.
CardVariant
    Predefined card style variants.
"""

from enum import Enum
from typing import Optional, Union

import flet as ft

from ..theme import get_theme_manager, SPACING, BORDER_RADIUS, ELEVATION


class CardVariant(Enum):
    """Predefined card style variants."""

    DEFAULT = "default"
    ELEVATED = "elevated"
    OUTLINED = "outlined"
    FILLED = "filled"


class Card(ft.Container):
    """
    A rounded card container with elevation and optional effects.

    The Card component wraps content in a styled container with consistent
    padding, border radius, and optional elevation/shadow effects.

    Parameters
    ----------
    content
        The content to display inside the card.
    variant
        The card style variant (default, elevated, outlined, filled).
    elevation
        Elevation level (0-4). If None, uses variant default.
    padding
        Padding inside the card. If None, uses theme default.
    border_radius
        Border radius. If None, uses theme default.
    bgcolor
        Background color. If None, uses theme color.
    animate
        Whether to animate size changes.
    on_click
        Optional click handler for interactive cards.
    tooltip
        Optional tooltip text.
    **kwargs
        Additional Container properties.

    Examples
    --------
    >>> card = Card(
    ...     content=ft.Text("Hello World"),
    ...     variant=CardVariant.ELEVATED,
    ... )
    >>> card = Card(
    ...     content=ft.Column([ft.Text("Title"), ft.Text("Content")]),
    ...     variant=CardVariant.OUTLINED,
    ...     padding=SPACING.md,
    ... )
    """

    def __init__(
        self,
        content: ft.Control,
        variant: CardVariant = CardVariant.DEFAULT,
        elevation: Optional[int] = None,
        padding: Optional[float] = None,
        border_radius: Optional[float] = None,
        bgcolor: Optional[str] = None,
        animate: bool = False,
        on_click=None,
        tooltip: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the Card component.

        Parameters
        ----------
        content
            The content to display inside the card.
        variant
            The card style variant.
        elevation
            Elevation level (0-4).
        padding
            Padding inside the card.
        border_radius
            Border radius.
        bgcolor
            Background color.
        animate
            Whether to animate size changes.
        on_click
            Optional click handler.
        tooltip
            Optional tooltip.
        **kwargs
            Additional Container properties.
        """
        theme = get_theme_manager()

        # Set default padding based on theme
        if padding is None:
            padding = theme.space.md

        # Set default border radius
        if border_radius is None:
            border_radius = theme.radius.lg

        # Determine elevation and style based on variant
        if elevation is None:
            elevation = self._get_variant_elevation(variant)

        # Determine background color
        if bgcolor is None:
            bgcolor = self._get_variant_bgcolor(theme, variant)

        # Determine border
        border = self._get_variant_border(theme, variant)

        # Build animation if requested
        animation = None
        if animate:
            animation = ft.Animation(
                duration=theme.duration.normal,
                curve=ft.AnimationCurve.EASE_OUT,
            )

        # Setup mouse cursor for interactive cards
        cursor = None
        if on_click is not None:
            cursor = ft.MouseCursor.CLICKER

        super().__init__(
            content=content,
            padding=padding,
            border_radius=border_radius,
            bgcolor=bgcolor,
            border=border,
            animate=animation,
            on_click=on_click,
            tooltip=tooltip,
            cursor=cursor,
            **kwargs,
        )

        self._variant = variant
        self._elevation_level = elevation

    def _get_variant_elevation(self, variant: CardVariant) -> int:
        """Get the default elevation for a variant."""
        elevation_map = {
            CardVariant.DEFAULT: 1,
            CardVariant.ELEVATED: 3,
            CardVariant.OUTLINED: 0,
            CardVariant.FILLED: 0,
        }
        return elevation_map.get(variant, 1)

    def _get_variant_bgcolor(self, theme, variant: CardVariant) -> str:
        """Get the default background color for a variant."""
        if variant == CardVariant.FILLED:
            return theme.colors.surface_container
        return theme.colors.surface

    def _get_variant_border(self, theme, variant: CardVariant) -> Optional[ft.Border]:
        """Get the border for a variant."""
        if variant == CardVariant.OUTLINED:
            return ft.border.all(1, theme.colors.outline_variant)
        return None

    def set_elevation(self, level: int):
        """
        Update the card's elevation level.

        Parameters
        ----------
        level
            New elevation level (0-4).
        """
        self._elevation_level = level
        # Note: Flet doesn't have built-in shadow support
        # Elevation is visual only through border/bgcolor in this implementation
        self.update()

    @property
    def variant(self) -> CardVariant:
        """Get the card's variant."""
        return self._variant

    @property
    def elevation_level(self) -> int:
        """Get the card's elevation level."""
        return self._elevation_level
