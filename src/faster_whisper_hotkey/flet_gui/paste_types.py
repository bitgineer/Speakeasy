"""
Paste method types for auto-paste functionality.

This module defines the paste method enum to avoid circular imports
between auto_paste and app_paste_rules modules.

Classes
-------
PasteMethod
    Enum defining available paste methods.
"""

from enum import Enum


class PasteMethod(Enum):
    """Available paste methods."""
    CLIPBOARD = "clipboard"  # Use Ctrl+V / Ctrl+Shift+V
    TYPING = "typing"  # Character-by-character typing
    DIRECT = "direct"  # Direct clipboard paste (no restore)
