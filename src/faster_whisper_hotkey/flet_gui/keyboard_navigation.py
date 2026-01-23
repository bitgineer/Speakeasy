"""
Keyboard navigation support for faster-whisper-hotkey Flet GUI.

This module provides keyboard navigation enhancements including:
- Focus management with visual indicators
- Keyboard shortcuts for common actions
- Tab order management
- Arrow key navigation support

Classes
-------
FocusRing
    Visual focus indicator for keyboard navigation.

KeyboardNavigator
    Manages keyboard navigation and focus handling.
"""

import logging
from typing import Optional, List, Callable, Dict, Any

import flet as ft

from .accessibility import get_accessibility_manager, FocusStyle
from .theme import get_theme_manager, SPACING

logger = logging.getLogger(__name__)


class FocusRing(ft.Container):
    """
    Visual focus indicator wrapper for keyboard navigation.

    Wraps any control with a visible focus ring when focused.

    Parameters
    ----------
    content
        The control to wrap.
    focused
        Whether the ring is currently focused.
    focus_style
        Optional custom focus style.
    **kwargs
        Additional Container properties.
    """

    def __init__(
        self,
        content: ft.Control,
        focused: bool = False,
        focus_style: Optional[FocusStyle] = None,
        **kwargs
    ):
        self._content = content
        self._focused = focused
        self._a11y = get_accessibility_manager()
        self._focus_style = focus_style or self._a11y.get_focus_style()

        super().__init__(
            content=content,
            padding=SPACING.xs,
            border_radius=8,
            **kwargs
        )

        self._update_border()

    def _update_border(self):
        """Update border based on focus state."""
        if self._focused and self._focus_style.width > 0:
            self.border = ft.Border.all(
                self._focus_style.width,
                self._focus_style.color,
            )
        else:
            self.border = None

    def focus(self):
        """Set focused state."""
        self._focused = True
        self._update_border()
        self.update()

    def blur(self):
        """Remove focused state."""
        self._focused = False
        self._update_border()
        self.update()

    @property
    def is_focused(self) -> bool:
        """Check if currently focused."""
        return self._focused


class KeyboardNavigator:
    """
    Manages keyboard navigation and focus handling.

    Features:
    - Tab order management
    - Arrow key navigation
    - Enter/Space activation
    - Escape to cancel
    """

    def __init__(self):
        """Initialize the keyboard navigator."""
        self._focusable_elements: List[ft.Control] = []
        self._current_index = 0
        self._on_activate_callbacks: Dict[str, Callable] = {}
        self._a11y = get_accessibility_manager()

    def register_element(
        self,
        element: ft.Control,
        activate_callback: Optional[Callable] = None,
        element_id: Optional[str] = None
    ):
        """
        Register a focusable element.

        Parameters
        ----------
        element
            The control to register.
        activate_callback
            Optional callback for activation (Enter/Space).
        element_id
            Optional identifier for the element.
        """
        self._focusable_elements.append(element)
        if element_id and activate_callback:
            self._on_activate_callbacks[element_id] = activate_callback

        # Enable keyboard navigation on the element
        if hasattr(element, 'on_focus'):
            original_on_focus = element.on_focus

            def on_focus_handler(e):
                if original_on_focus:
                    original_on_focus(e)
                self._on_element_focused(element)

            element.on_focus = on_focus_handler

    def _on_element_focused(self, element: ft.Control):
        """Handle element focus."""
        try:
            idx = self._focusable_elements.index(element)
            self._current_index = idx
        except ValueError:
            pass

        # Announce focus for screen readers
        if hasattr(element, 'tooltip') and element.tooltip:
            self._a11y.announce(f"Focused: {element.tooltip}")
        elif hasattr(element, 'text') and element.text:
            self._a11y.announce(f"Focused: {element.text}")

    def focus_next(self):
        """Move focus to next element."""
        if not self._focusable_elements:
            return

        self._current_index = (self._current_index + 1) % len(self._focusable_elements)
        self._focus_current()

    def focus_previous(self):
        """Move focus to previous element."""
        if not self._focusable_elements:
            return

        self._current_index = (self._current_index - 1) % len(self._focusable_elements)
        self._focus_current()

    def focus_first(self):
        """Move focus to first element."""
        if not self._focusable_elements:
            return

        self._current_index = 0
        self._focus_current()

    def focus_last(self):
        """Move focus to last element."""
        if not self._focusable_elements:
            return

        self._current_index = len(self._focusable_elements) - 1
        self._focus_current()

    def _focus_current(self):
        """Focus the current element."""
        element = self._focusable_elements[self._current_index]
        if hasattr(element, 'focus'):
            try:
                element.focus()
            except Exception as e:
                logger.debug(f"Could not focus element: {e}")

    def activate_current(self):
        """Activate the current focused element."""
        if not self._focusable_elements:
            return

        element = self._focusable_elements[self._current_index]

        # Try to click the element
        if hasattr(element, 'on_click') and element.on_click:
            try:
                element.on_click(None)
            except Exception as e:
                logger.debug(f"Could not activate element: {e}")

    def handle_key_event(self, e: ft.KeyboardEvent) -> bool:
        """
        Handle a keyboard event.

        Parameters
        ----------
        e
            The keyboard event.

        Returns
        -------
        bool
            True if the event was handled.
        """
        key = e.key.lower()

        # Tab navigation - let Flet handle this
        if key == "tab":
            return False

        # Arrow navigation
        if key == "arrowdown":
            self.focus_next()
            return True
        elif key == "arrowup":
            self.focus_previous()
            return True

        # Home/End
        if key == "home":
            self.focus_first()
            return True
        elif key == "end":
            self.focus_last()
            return True

        # Activation
        if key in ("enter", " "):
            self.activate_current()
            return True

        # Escape
        if key == "escape":
            self._a11y.announce("Cancelled")
            return True

        return False


def make_accessible_button(
    text: str,
    on_click: Callable,
    icon: Optional[str] = None,
    tooltip: Optional[str] = None,
    hotkey: Optional[str] = None,
    **kwargs
) -> ft.ElevatedButton:
    """
    Create an accessible button with proper keyboard support.

    Parameters
    ----------
    text
        Button text.
    on_click
        Click handler.
    icon
        Optional icon.
    tooltip
        Tooltip text (defaults to button text).
    hotkey
        Optional keyboard shortcut hint.
    **kwargs
        Additional button properties.

    Returns
    -------
    ft.ElevatedButton
        Accessible button control.
    """
    a11y = get_accessibility_manager()
    theme = get_theme_manager()

    # Build tooltip with hotkey hint
    tooltip_text = tooltip or text
    if hotkey:
        tooltip_text = f"{tooltip_text} ({hotkey.upper()})"

    # Create button with accessible styling
    button = ft.ElevatedButton(
        text=text,
        icon=icon,
        tooltip=tooltip_text,
        on_click=on_click,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=theme.radius.md),
            padding=ft.padding.symmetric(
                horizontal=theme.space.md,
                vertical=theme.space.sm,
            ),
        ),
        **kwargs
    )

    # Apply font size scaling
    if hasattr(button, 'text_style'):
        current_size = kwargs.get('style', {}).get('text_style', ft.TextStyle()).size or 14
        # Would need to scale the size here

    return button


def create_focusable_list_item(
    text: str,
    on_click: Callable,
    index: int,
    selected: bool = False,
    **kwargs
) -> ft.Container:
    """
    Create a focusable list item for keyboard navigation.

    Parameters
    ----------
    text
        Item text.
    on_click
        Click handler.
    index
        Item index (for keyboard navigation).
    selected
        Whether the item is selected.
    **kwargs
        Additional properties.

    Returns
    -------
    ft.Container
        Focusable list item.
    """
    theme = get_theme_manager()
    a11y = get_accessibility_manager()

    # Focus style
    focus_style = a11y.get_focus_style()

    def on_focus(e):
        a11y.announce(f"Item {index + 1}: {text}")

    content = ft.Container(
        content=ft.Row([
            ft.Text(
                text,
                size=theme.get_font_size(14),
                color=theme.colors.on_surface if not selected else theme.colors.primary,
                weight=ft.FontWeight.MEDIUM if selected else ft.FontWeight.NORMAL,
            ),
        ]),
        padding=ft.padding.symmetric(
            horizontal=theme.space.md,
            vertical=theme.space.sm,
        ),
        border_radius=theme.radius.sm,
        bgcolor=theme.colors.primary_container if selected else theme.colors.surface_container_low,
        on_click=on_click,
        on_focus=on_focus,
        **kwargs
    )

    return content


class AccessibleDropdown(ft.Dropdown):
    """
    Accessible dropdown with keyboard navigation and announcements.

    Extends Flet's Dropdown with accessibility enhancements.
    """

    def __init__(self, label: str = "", options: List = None, **kwargs):
        self._a11y = get_accessibility_manager()
        self._theme = get_theme_manager()

        # Add accessibility hints
        if label and not kwargs.get('tooltip'):
            kwargs['tooltip'] = f"{label}. Use arrow keys to navigate."

        super().__init__(label=label, options=options or [], **kwargs)

        # Scale font size
        self.label_style = ft.TextStyle(
            size=self._theme.get_font_size(14),
            color=self._theme.colors.on_surface,
        )
        self.text_style = ft.TextStyle(
            size=self._theme.get_font_size(14),
            color=self._theme.colors.on_surface,
        )

    def _on_change(self, e):
        """Handle value change with announcement."""
        super()._on_change(e)
        if self.value:
            self._a11y.announce(f"Selected: {self.value}")


class AccessibleSwitch(ft.Switch):
    """
    Accessible switch with screen reader announcements.
    """

    def __init__(self, label: str = "", **kwargs):
        self._a11y = get_accessibility_manager()
        self._theme = get_theme_manager()

        super().__init__(label=label, **kwargs)

        # Scale font size
        self.label_style = ft.TextStyle(
            size=self._theme.get_font_size(14),
            color=self._theme.colors.on_surface,
        )

    def _on_change(self, e):
        """Handle toggle change with announcement."""
        super()._on_change(e)
        state = "enabled" if self.value else "disabled"
        if self.label:
            self._a11y.announce(f"{self.label}: {state}")
        else:
            self._a11y.announce(f"Switch: {state}")


class AccessibleSlider(ft.Slider):
    """
    Accessible slider with value announcements.
    """

    def __init__(self, label: str = "", **kwargs):
        self._a11y = get_accessibility_manager()
        self._theme = get_theme_manager()

        super().__init__(label=label, **kwargs)

    def _on_change(self, e):
        """Handle slider change with announcement."""
        super()._on_change(e)
        value = int(self.value * 100) if self.value <= 1 else int(self.value)
        if self.label:
            self._a11y.announce(f"{self.label}: {value} percent")
        else:
            self._a11y.announce(f"Value: {value}")
