"""
Input field component with validation states and modern styling.

The InputField component provides a styled text input with support for
labels, hints, validation states, icons, and helper text.

Classes
-------
InputField
    A styled text input with validation states.
InputState
    Input validation states.
"""

from enum import Enum
from typing import Optional, Callable, List

import flet as ft

from ..theme import get_theme_manager, BORDER_RADIUS, SPACING


class InputState(Enum):
    """Input validation states."""

    DEFAULT = "default"
    VALID = "valid"
    INVALID = "invalid"
    DISABLED = "disabled"


class InputField(ft.Column):
    """
    A styled text input with validation states and helper text.

    The InputField wraps a Flet TextField with consistent styling,
    optional labels, validation states, and helper text.

    Parameters
    ----------
    label
        Input label text.
    value
        Initial value.
    placeholder
        Placeholder text when empty.
    hint
        Helper text displayed below the input.
    error
        Error message to display (sets invalid state).
    state
        Manual state override (DEFAULT, VALID, INVALID, DISABLED).
    password
        Whether to hide text (password field).
    multiline
        Whether to allow multiple lines.
    min_lines
        Minimum lines for multiline.
    max_lines
        Maximum lines for multiline.
    max_length
        Maximum character length.
    prefix_icon
        Icon to display before the text.
    suffix_icon
        Icon to display after the text.
    prefix_text
        Text to display before the input (e.g., currency symbol).
    suffix_text
        Text to display after the input (e.g., unit).
    keyboard_type
        Type of keyboard (for mobile).
    text_align
        Text alignment.
    read_only
        Whether the field is read-only.
    disabled
        Whether the field is disabled.
    on_change
        Callback when value changes.
    on_submit
        Callback when user submits (Enter key).
    validator
        Optional custom validator function.
    width
        Input width. None for full width.
    **kwargs
        Additional TextField properties.

    Examples
    --------
    >>> field = InputField("Username", placeholder="Enter username")
    >>> field = InputField("Email", validator=lambda x: "@" in x)
    >>> field = InputField("Password", password=True)
    """

    def __init__(
        self,
        label: str,
        value: str = "",
        placeholder: Optional[str] = None,
        hint: Optional[str] = None,
        error: Optional[str] = None,
        state: InputState = InputState.DEFAULT,
        password: bool = False,
        multiline: bool = False,
        min_lines: int = 1,
        max_lines: int = 1,
        max_length: Optional[int] = None,
        prefix_icon: Optional[str] = None,
        suffix_icon: Optional[str] = None,
        prefix_text: Optional[str] = None,
        suffix_text: Optional[str] = None,
        keyboard_type: Optional[ft.KeyboardType] = None,
        text_align: ft.TextAlign = ft.TextAlign.LEFT,
        read_only: bool = False,
        disabled: bool = False,
        on_change=None,
        on_submit=None,
        validator: Optional[Callable[[str], bool]] = None,
        width: Optional[int] = None,
        **kwargs,
    ):
        """
        Initialize the InputField component.

        Parameters
        ----------
        label
            Input label text.
        value
            Initial value.
        placeholder
            Placeholder text.
        hint
            Helper text.
        error
            Error message.
        state
            Manual state override.
        password
            Whether to hide text.
        multiline
            Whether to allow multiple lines.
        min_lines
            Minimum lines for multiline.
        max_lines
            Maximum lines.
        max_length
            Maximum character length.
        prefix_icon
            Icon before text.
        suffix_icon
            Icon after text.
        prefix_text
            Text before input.
        suffix_text
            Text after input.
        keyboard_type
            Keyboard type.
        text_align
            Text alignment.
        read_only
            Whether read-only.
        disabled
            Whether disabled.
        on_change
            Change callback.
        on_submit
            Submit callback.
        validator
            Custom validator function.
        width
            Input width.
        **kwargs
            Additional properties.
        """
        self._theme = get_theme_manager()
        self._validator = validator
        self._state = state
        self._error_message = error
        self._hint_message = hint
        self._on_change_callback = on_change
        self._on_submit_callback = on_submit

        # Create the text field
        self._field = ft.TextField(
            value=value,
            label=label,
            placeholder=placeholder,
            password=password,
            multiline=multiline,
            min_lines=min_lines,
            max_lines=max_lines,
            max_length=max_length,
            prefix_icon=prefix_icon,
            suffix_icon=suffix_icon,
            prefix_text=prefix_text,
            suffix_text=suffix_text,
            keyboard_type=keyboard_type,
            text_align=text_align,
            read_only=read_only,
            disabled=disabled or state == InputState.DISABLED,
            width=width,
            on_change=self._on_change,
            on_submit=self._on_submit,
            **kwargs,
        )

        # Apply initial styling
        self._apply_state_style()

        # Create helper/error text
        self._helper_text = ft.Text(
            self._get_helper_text(),
            size=12,
            color=self._get_helper_color(),
        )

        # Build the column
        controls = [self._field]
        if hint or error:
            controls.append(
                ft.Container(
                    content=self._helper_text,
                    padding=ft.padding.only(left=16, top=4),
                )
            )

        super().__init__(
            controls=controls,
            spacing=0,
            tight=True,
        )

    def _on_change(self, e):
        """Handle value change."""
        # Validate if validator is set
        if self._validator:
            is_valid = self._validator(self._field.value)
            self._state = InputState.VALID if is_valid else InputState.INVALID
            self._apply_state_style()
            self._update_helper_text()

        # Call external callback
        if self._on_change_callback:
            self._on_change_callback(e)

    def _on_submit(self, e):
        """Handle submit."""
        if self._on_submit_callback:
            self._on_submit_callback(e)

    def _apply_state_style(self):
        """Apply styling based on current state."""
        theme = self._theme
        field = self._field

        if self._state == InputState.INVALID or self._error_message:
            field.border_color = theme.colors.error
            field.focused_border_color = theme.colors.error
            field.filled = True
            field.bgcolor = theme.colors.error_container
        elif self._state == InputState.VALID:
            field.border_color = theme.colors.success
            field.focused_border_color = theme.colors.success
            field.filled = True
            field.bgcolor = ft.colors.TRANSPARENT
        else:
            field.border_color = theme.colors.outline
            field.focused_border_color = theme.colors.primary
            field.filled = True
            field.bgcolor = theme.colors.surface_container_low

        field.border_radius = theme.radius.md
        field.text_size = 14

    def _get_helper_text(self) -> Optional[str]:
        """Get the helper/error text to display."""
        if self._error_message:
            return self._error_message
        return self._hint_message

    def _get_helper_color(self) -> str:
        """Get the helper text color."""
        if self._error_message:
            return self._theme.colors.error
        return self._theme.colors.on_surface_variant

    def _update_helper_text(self):
        """Update the helper text display."""
        self._helper_text.text = self._get_helper_text()
        self._helper_text.color = self._get_helper_color()
        self._helper_text.update()

    def set_error(self, error: Optional[str]):
        """
        Set the error message and state.

        Parameters
        ----------
        error
            Error message, or None to clear.
        """
        self._error_message = error
        if error:
            self._state = InputState.INVALID
        else:
            self._state = InputState.DEFAULT
        self._apply_state_style()
        self._update_helper_text()

    def set_state(self, state: InputState):
        """
        Set the input state.

        Parameters
        ----------
        state
            The input state.
        """
        self._state = state
        self._apply_state_style()
        self._update_helper_text()

    def validate(self) -> bool:
        """
        Validate the input value.

        Returns
        -------
        bool
            True if valid.
        """
        if self._validator:
            return self._validator(self.value)
        return self._error_message is None

    @property
    def value(self) -> str:
        """Get the input value."""
        return self._field.value or ""

    @value.setter
    def value(self, val: str):
        """Set the input value."""
        self._field.value = val

    @property
    def state(self) -> InputState:
        """Get the current state."""
        return self._state

    @property
    def field(self) -> ft.TextField:
        """Get the underlying TextField."""
        return self._field
