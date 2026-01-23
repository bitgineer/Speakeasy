"""
Reusable UI component library for faster-whisper-hotkey Flet GUI.

This package provides modern, styled UI components that follow the
application's design system and theme.

Components
----------
Card
    Rounded card component with elevation.
Button
    Modern button styles (primary, secondary, danger, icon-only).
InputField
    Styled text input with validation states.
Dropdown
    Custom dropdown with search capability.
ToggleSwitch
    Modern toggle for boolean settings.
Slider
    Range slider for numeric settings.
StatusBadge
    Compact status indicator.
AudioVisualizer
    Animated audio level bar.
"""

from .card import Card
from .button import Button, ButtonVariant
from .input_field import InputField
from .toggle_switch import ToggleSwitch
from .status_badge import StatusBadge, StatusType
from .audio_visualizer import AudioVisualizer
from .collapsible_sidebar import CollapsibleSidebar, SidebarItem, SidebarPosition

__all__ = [
    "Card",
    "Button",
    "ButtonVariant",
    "InputField",
    "ToggleSwitch",
    "StatusBadge",
    "StatusType",
    "AudioVisualizer",
    "CollapsibleSidebar",
    "SidebarItem",
    "SidebarPosition",
]
