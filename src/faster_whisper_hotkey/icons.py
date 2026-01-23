"""
Modern icon library for faster-whisper-hotkey GUI.

This module provides a comprehensive set of modern icons drawn using
tkinter Canvas. Icons are based on Material Design and Lucide principles
with clean lines and consistent proportions.

All icons are drawn procedurally without external image dependencies,
making them lightweight and resolution-independent.

Classes
-------
Icon
    Base icon class with drawing primitives.

ModernIcons
    Collection of pre-configured modern icons.

IconFactory
    Factory for creating icon widgets with consistent styling.

Usage
-----
    # Get an icon widget
    icon_widget = ModernIcons.settings(canvas, size=24, color="#2196F3")

    # Or use the factory for themed icons
    factory = IconFactory(theme_manager)
    icon = factory.create(canvas, "settings", size=24)

Notes
-----
Icons use a 24x24 grid by default with 2px stroke width.
All paths are drawn using the provided color for theme consistency.
"""

import tkinter as tk
from typing import Optional, Tuple, List


class Icon:
    """Base icon class with drawing primitives.

    Provides helper methods for drawing common shapes on canvas:
    - Lines and paths
    - Rectangles and rounded rectangles
    - Circles and ellipses
    - Polygons
    """

    def __init__(self, canvas: tk.Canvas, x: int = 0, y: int = 0,
                 size: int = 24, color: str = "#000000", width: int = 2):
        """Initialize icon drawer.

        Args:
            canvas: Canvas to draw on
            x: X position of icon
            y: Y position of icon
            size: Icon size (square)
            color: Stroke color
            width: Stroke width
        """
        self.canvas = canvas
        self.x = x
        self.y = y
        self.size = size
        self.scale = size / 24  # Scale from 24x24 base
        self.color = color
        self.width = width * self.scale

    def _coord(self, *values: float) -> List[float]:
        """Scale coordinates from 24x24 grid to actual size."""
        result = []
        for v in values:
            result.append(self.x + v * self.scale)
        return result

    def line(self, x1: float, y1: float, x2: float, y2: float, width: Optional[int] = None):
        """Draw a line."""
        w = width if width is not None else self.width
        self.canvas.create_line(
            *self._coord(x1, y1, x2, y2),
            fill=self.color,
            width=w,
            capstyle=tk.ROUND,
            joinstyle=tk.ROUND
        )

    def path(self, points: List[Tuple[float, float]], closed: bool = False):
        """Draw a path from points."""
        coords = self._coord(*[c for p in points for c in p])
        if closed:
            self.canvas.create_polygon(
                coords,
                fill=self.color,
                outline=self.color,
                smooth=False
            )
        else:
            # Draw connected lines
            for i in range(0, len(coords) - 2, 2):
                self.canvas.create_line(
                    coords[i], coords[i + 1],
                    coords[i + 2], coords[i + 3],
                    fill=self.color,
                    width=self.width,
                    capstyle=tk.ROUND,
                    joinstyle=tk.ROUND
                )

    def rect(self, x: float, y: float, w: float, h: float, fill: bool = False):
        """Draw a rectangle."""
        coords = self._coord(x, y, x + w, y + h)
        if fill:
            self.canvas.create_rectangle(
                *coords,
                fill=self.color,
                outline=self.color
            )
        else:
            self.canvas.create_rectangle(
                *coords,
                outline=self.color,
                width=self.width
            )

    def rounded_rect(self, x: float, y: float, w: float, h: float, r: float, fill: bool = False):
        """Draw a rounded rectangle."""
        coords = self._coord(x, y, x + w, y + h)
        radius = r * self.scale
        if fill:
            self.canvas.create_rectangle(
                *coords,
                fill=self.color,
                outline=self.color,
                width=0
            )
        else:
            self.canvas.create_rectangle(
                *coords,
                outline=self.color,
                width=self.width,
                borderwidth=0
            )

    def circle(self, cx: float, cy: float, r: float, fill: bool = False):
        """Draw a circle."""
        coords = self._coord(cx - r, cy - r, cx + r, cy + r)
        if fill:
            self.canvas.create_oval(
                *coords,
                fill=self.color,
                outline=self.color
            )
        else:
            self.canvas.create_oval(
                *coords,
                outline=self.color,
                width=self.width
            )

    def arc(self, cx: float, cy: float, r: float, start: float, extent: float):
        """Draw an arc."""
        coords = self._coord(cx - r, cy - r, cx + r, cy + r)
        self.canvas.create_arc(
            *coords,
            start=start,
            extent=extent,
            style=tk.ARC,
            outline=self.color,
            width=self.width
        )


class ModernIcons:
    """Collection of modern icons drawn with canvas.

    Icons include:
    - Navigation: home, settings, shortcuts, history
    - Actions: play, pause, stop, record, copy, trash
    - Status: check, close, warning, info
    - Media: microphone, volume
    - Interface: menu, search, filter, refresh
    """

    @staticmethod
    def settings(canvas: tk.Canvas, x: int = 0, y: int = 0,
                 size: int = 24, color: str = "#000000"):
        """Draw a settings/gear icon."""
        icon = Icon(canvas, x, y, size, color)

        # Gear/circle with teeth
        cx, cy = 12, 12
        outer_r = 10
        inner_r = 4

        # Outer circle
        icon.circle(cx, cy, outer_r)

        # Inner circle (filled)
        icon.circle(cx, cy, inner_r, fill=True)

        # Teeth (6 points)
        for angle in range(0, 360, 60):
            import math
            rad = math.radians(angle)
            x1 = cx + math.cos(rad) * outer_r
            y1 = cy + math.sin(rad) * outer_r
            x2 = cx + math.cos(rad) * (outer_r + 2.5)
            y2 = cy + math.sin(rad) * (outer_r + 2.5)
            icon.line(x1, y1, x2, y2)

    @staticmethod
    def home(canvas: tk.Canvas, x: int = 0, y: int = 0,
              size: int = 24, color: str = "#000000"):
        """Draw a home icon."""
        icon = Icon(canvas, x, y, size, color)

        # House outline
        icon.path([
            (3, 20), (3, 10), (12, 3), (21, 10), (21, 20)
        ])
        icon.line(12, 3, 12, 20)  # Center vertical
        icon.line(8, 20, 8, 14)   # Door frame left
        icon.line(16, 20, 16, 14) # Door frame right

    @staticmethod
    def keyboard(canvas: tk.Canvas, x: int = 0, y: int = 0,
                 size: int = 24, color: str = "#000000"):
        """Draw a keyboard shortcut icon."""
        icon = Icon(canvas, x, y, size, color)

        # Keyboard outline
        icon.rounded_rect(2, 4, 20, 14, 2)

        # Keys
        key_positions = [
            (4, 7), (8, 7), (12, 7), (16, 7),
            (4, 11), (8, 11), (12, 11), (16, 11),
        ]
        for kx, ky in key_positions:
            icon.rect(kx, ky, 2, 2, fill=True)

        # Spacebar
        icon.rect(6, 15, 12, 2, fill=True)

    @staticmethod
    def history(canvas: tk.Canvas, x: int = 0, y: int = 0,
                size: int = 24, color: str = "#000000"):
        """Draw a history/clock icon."""
        icon = Icon(canvas, x, y, size, color)

        # Circle outline
        icon.circle(12, 12, 10)

        # Clock hands
        icon.line(12, 12, 12, 7)  # Hour hand (vertical)
        icon.line(12, 12, 16, 12)  # Minute hand (horizontal)

    @staticmethod
    def play(canvas: tk.Canvas, x: int = 0, y: int = 0,
             size: int = 24, color: str = "#000000"):
        """Draw a play icon."""
        icon = Icon(canvas, x, y, size, color)

        # Triangle pointing right
        points = [(8, 6), (8, 18), (18, 12)]
        icon.path(points, closed=True)

    @staticmethod
    def pause(canvas: tk.Canvas, x: int = 0, y: int = 0,
              size: int = 24, color: str = "#000000"):
        """Draw a pause icon."""
        icon = Icon(canvas, x, y, size, color)

        # Two vertical bars
        icon.rect(7, 6, 3, 12, fill=True)
        icon.rect(14, 6, 3, 12, fill=True)

    @staticmethod
    def stop(canvas: tk.Canvas, x: int = 0, y: int = 0,
             size: int = 24, color: str = "#000000"):
        """Draw a stop icon."""
        icon = Icon(canvas, x, y, size, color)
        icon.rect(6, 6, 12, 12, fill=True)

    @staticmethod
    def record(canvas: tk.Canvas, x: int = 0, y: int = 0,
               size: int = 24, color: str = "#F44336"):
        """Draw a record/mic icon."""
        icon = Icon(canvas, x, y, size, color)

        # Red circle (recording indicator)
        icon.circle(12, 12, 6, fill=True)

    @staticmethod
    def microphone(canvas: tk.Canvas, x: int = 0, y: int = 0,
                   size: int = 24, color: str = "#000000"):
        """Draw a microphone icon."""
        icon = Icon(canvas, x, y, size, color)

        # Mic body (rounded rectangle)
        icon.rounded_rect(8, 4, 8, 12, 4, fill=True)

        # Mic stand/base
        icon.line(12, 16, 12, 20)
        icon.line(8, 20, 16, 20)

    @staticmethod
    def copy(canvas: tk.Canvas, x: int = 0, y: int = 0,
             size: int = 24, color: str = "#000000"):
        """Draw a copy icon."""
        icon = Icon(canvas, x, y, size, color)

        # Two overlapping rectangles
        icon.rect(8, 8, 12, 12)
        icon.rect(4, 4, 12, 12)

    @staticmethod
    def trash(canvas: tk.Canvas, x: int = 0, y: int = 0,
              size: int = 24, color: str = "#000000"):
        """Draw a trash/delete icon."""
        icon = Icon(canvas, x, y, size, color)

        # Lid
        icon.line(6, 6, 18, 6)
        icon.line(8, 4, 16, 4)
        icon.line(10, 4, 10, 6)
        icon.line(14, 4, 14, 6)

        # Body
        icon.rect(7, 8, 10, 11)

        # Lines
        icon.line(9, 10, 9, 17)
        icon.line(12, 10, 12, 17)
        icon.line(15, 10, 15, 17)

    @staticmethod
    def check(canvas: tk.Canvas, x: int = 0, y: int = 0,
              size: int = 24, color: str = "#4CAF50"):
        """Draw a checkmark icon."""
        icon = Icon(canvas, x, y, size, color)
        icon.path([(5, 12), (10, 17), (19, 7)])

    @staticmethod
    def close(canvas: tk.Canvas, x: int = 0, y: int = 0,
              size: int = 24, color: str = "#000000"):
        """Draw a close X icon."""
        icon = Icon(canvas, x, y, size, color)
        icon.line(8, 8, 16, 16)
        icon.line(16, 8, 8, 16)

    @staticmethod
    def warning(canvas: tk.Canvas, x: int = 0, y: int = 0,
                size: int = 24, color: str = "#FF9800"):
        """Draw a warning triangle icon."""
        icon = Icon(canvas, x, y, size, color)

        # Triangle
        points = [(12, 4), (4, 20), (20, 20)]
        icon.path(points)

        # Exclamation mark
        icon.line(12, 8, 12, 14)
        icon.circle(12, 17, 1, fill=True)

    @staticmethod
    def info(canvas: tk.Canvas, x: int = 0, y: int = 0,
             size: int = 24, color: str = "#2196F3"):
        """Draw an info circle icon."""
        icon = Icon(canvas, x, y, size, color)
        icon.circle(12, 12, 10)
        icon.line(12, 10, 12, 16)
        icon.circle(12, 7, 1, fill=True)

    @staticmethod
    def menu(canvas: tk.Canvas, x: int = 0, y: int = 0,
             size: int = 24, color: str = "#000000"):
        """Draw a hamburger menu icon."""
        icon = Icon(canvas, x, y, size, color)
        icon.line(4, 7, 20, 7, width=2)
        icon.line(4, 12, 20, 12, width=2)
        icon.line(4, 17, 20, 17, width=2)

    @staticmethod
    def search(canvas: tk.Canvas, x: int = 0, y: int = 0,
               size: int = 24, color: str = "#000000"):
        """Draw a search/magnifying glass icon."""
        icon = Icon(canvas, x, y, size, color)
        icon.circle(10, 10, 7)
        icon.line(15, 15, 21, 21)

    @staticmethod
    def filter(canvas: tk.Canvas, x: int = 0, y: int = 0,
               size: int = 24, color: str = "#000000"):
        """Draw a filter funnel icon."""
        icon = Icon(canvas, x, y, size, color)
        icon.path([(4, 4), (20, 4), (14, 12), (14, 20), (10, 20), (10, 12), (4, 4)])

    @staticmethod
    def refresh(canvas: tk.Canvas, x: int = 0, y: int = 0,
                size: int = 24, color: str = "#000000"):
        """Draw a refresh/rotate icon."""
        icon = Icon(canvas, x, y, size, color)
        icon.arc(12, 12, 9, 0, 270)
        # Arrow head
        icon.path([(18, 6), (20, 3), (14, 3)], closed=True)

    @staticmethod
    def sun(canvas: tk.Canvas, x: int = 0, y: int = 0,
            size: int = 24, color: str = "#000000"):
        """Draw a sun icon (light mode)."""
        icon = Icon(canvas, x, y, size, color)
        icon.circle(12, 12, 5)
        # Rays
        for angle in range(0, 360, 45):
            import math
            rad = math.radians(angle)
            x1 = 12 + math.cos(rad) * 8
            y1 = 12 + math.sin(rad) * 8
            x2 = 12 + math.cos(rad) * 11
            y2 = 12 + math.sin(rad) * 11
            icon.line(x1, y1, x2, y2)

    @staticmethod
    def moon(canvas: tk.Canvas, x: int = 0, y: int = 0,
             size: int = 24, color: str = "#000000"):
        """Draw a moon icon (dark mode)."""
        icon = Icon(canvas, x, y, size, color)
        # Crescent shape
        icon.circle(12, 12, 8)
        # Use same color to create crescent
        icon.circle(8, 8, 6, fill=True)

    @staticmethod
    def edit(canvas: tk.Canvas, x: int = 0, y: int = 0,
             size: int = 24, color: str = "#000000"):
        """Draw a pencil/edit icon."""
        icon = Icon(canvas, x, y, size, color)

        # Pencil body (diagonal)
        icon.path([(3, 21), (17, 7)])
        # Pencil tip
        icon.path([(3, 21), (7, 21), (3, 17)], closed=True)
        # Eraser
        icon.path([(17, 7), (21, 3), (19, 1), (15, 5), (17, 7)], closed=True)

    @staticmethod
    def plus(canvas: tk.Canvas, x: int = 0, y: int = 0,
             size: int = 24, color: str = "#000000"):
        """Draw a plus/add icon."""
        icon = Icon(canvas, x, y, size, color)
        icon.line(12, 5, 12, 19, width=2)
        icon.line(5, 12, 19, 12, width=2)

    @staticmethod
    def minus(canvas: tk.Canvas, x: int = 0, y: int = 0,
              size: int = 24, color: str = "#000000"):
        """Draw a minus icon."""
        icon = Icon(canvas, x, y, size, color)
        icon.line(5, 12, 19, 12, width=2)

    @staticmethod
    def shield(canvas: tk.Canvas, x: int = 0, y: int = 0,
               size: int = 24, color: str = "#2196F3"):
        """Draw a shield/privacy icon."""
        icon = Icon(canvas, x, y, size, color)
        # Shield outline
        points = [
            (12, 21),
            (4, 17),
            (4, 9),
            (12, 4),
            (20, 9),
            (20, 17),
            (12, 21)
        ]
        icon.path(points)
        # Lock hole
        icon.circle(12, 13, 2)

    @staticmethod
    def lock(canvas: tk.Canvas, x: int = 0, y: int = 0,
             size: int = 24, color: str = "#000000"):
        """Draw a lock icon."""
        icon = Icon(canvas, x, y, size, color)
        # Lock body
        icon.rect(6, 11, 12, 9, fill=True)
        # Shackle
        icon.path([(8, 11), (8, 7), (16, 7), (16, 11)], closed=False)

    @staticmethod
    def unlock(canvas: tk.Canvas, x: int = 0, y: int = 0,
               size: int = 24, color: str = "#000000"):
        """Draw an unlock icon."""
        icon = Icon(canvas, x, y, size, color)
        # Lock body
        icon.rect(6, 11, 12, 9, fill=True)
        # Open shackle
        icon.path([(8, 11), (8, 7), (14, 7), (14, 9)], closed=False)

    @staticmethod
    def download(canvas: tk.Canvas, x: int = 0, y: int = 0,
                 size: int = 24, color: str = "#000000"):
        """Draw a download icon."""
        icon = Icon(canvas, x, y, size, color)
        # Arrow down
        icon.path([(12, 4), (12, 14)])
        icon.path([(8, 10), (12, 14), (16, 10)], closed=True)
        # Base line
        icon.line(4, 18, 20, 18)

    @staticmethod
    def upload(canvas: tk.Canvas, x: int = 0, y: int = 0,
               size: int = 24, color: str = "#000000"):
        """Draw an upload icon."""
        icon = Icon(canvas, x, y, size, color)
        # Arrow up
        icon.path([(12, 14), (12, 4)])
        icon.path([(8, 8), (12, 4), (16, 8)], closed=True)
        # Base line
        icon.line(4, 18, 20, 18)

    @staticmethod
    def file(canvas: tk.Canvas, x: int = 0, y: int = 0,
             size: int = 24, color: str = "#000000"):
        """Draw a file icon."""
        icon = Icon(canvas, x, y, size, color)
        # File shape
        icon.path([(6, 3), (14, 3), (18, 7), (18, 21), (6, 21), (6, 3)])
        # Fold
        icon.line(14, 3, 14, 7)
        icon.line(14, 7, 18, 7)
        # Lines
        icon.line(9, 11, 15, 11)
        icon.line(9, 14, 15, 14)
        icon.line(9, 17, 13, 17)

    @staticmethod
    def folder(canvas: tk.Canvas, x: int = 0, y: int = 0,
               size: int = 24, color: str = "#000000"):
        """Draw a folder icon."""
        icon = Icon(canvas, x, y, size, color)
        # Folder back
        icon.rect(3, 8, 18, 11)
        # Tab
        icon.rect(3, 5, 8, 3)

    @staticmethod
    def chevron_right(canvas: tk.Canvas, x: int = 0, y: int = 0,
                      size: int = 24, color: str = "#000000"):
        """Draw a chevron pointing right."""
        icon = Icon(canvas, x, y, size, color)
        icon.path([(9, 6), (15, 12), (9, 18)])

    @staticmethod
    def chevron_left(canvas: tk.Canvas, x: int = 0, y: int = 0,
                     size: int = 24, color: str = "#000000"):
        """Draw a chevron pointing left."""
        icon = Icon(canvas, x, y, size, color)
        icon.path([(15, 6), (9, 12), (15, 18)])

    @staticmethod
    def chevron_up(canvas: tk.Canvas, x: int = 0, y: int = 0,
                   size: int = 24, color: str = "#000000"):
        """Draw a chevron pointing up."""
        icon = Icon(canvas, x, y, size, color)
        icon.path([(6, 15), (12, 9), (18, 15)])

    @staticmethod
    def chevron_down(canvas: tk.Canvas, x: int = 0, y: int = 0,
                     size: int = 24, color: str = "#000000"):
        """Draw a chevron pointing down."""
        icon = Icon(canvas, x, y, size, color)
        icon.path([(6, 9), (12, 15), (18, 9)])


class IconFactory:
    """Factory for creating themed icon widgets.

    Provides a consistent way to create icons that match the current theme.
    Icons are drawn on canvas widgets with proper sizing and colors.
    """

    # Available icon names mapped to drawing methods
    ICON_MAP = {
        "settings": ModernIcons.settings,
        "home": ModernIcons.home,
        "keyboard": ModernIcons.keyboard,
        "shortcuts": ModernIcons.keyboard,
        "history": ModernIcons.history,
        "play": ModernIcons.play,
        "pause": ModernIcons.pause,
        "stop": ModernIcons.stop,
        "record": ModernIcons.record,
        "microphone": ModernIcons.microphone,
        "copy": ModernIcons.copy,
        "trash": ModernIcons.trash,
        "delete": ModernIcons.trash,
        "check": ModernIcons.check,
        "close": ModernIcons.close,
        "warning": ModernIcons.warning,
        "info": ModernIcons.info,
        "menu": ModernIcons.menu,
        "search": ModernIcons.search,
        "filter": ModernIcons.filter,
        "refresh": ModernIcons.refresh,
        "sun": ModernIcons.sun,
        "light": ModernIcons.sun,
        "moon": ModernIcons.moon,
        "dark": ModernIcons.moon,
        "edit": ModernIcons.edit,
        "plus": ModernIcons.plus,
        "add": ModernIcons.plus,
        "minus": ModernIcons.minus,
        "shield": ModernIcons.shield,
        "privacy": ModernIcons.shield,
        "lock": ModernIcons.lock,
        "unlock": ModernIcons.unlock,
        "download": ModernIcons.download,
        "upload": ModernIcons.upload,
        "file": ModernIcons.file,
        "folder": ModernIcons.folder,
        "chevron_right": ModernIcons.chevron_right,
        "chevron_left": ModernIcons.chevron_left,
        "chevron_up": ModernIcons.chevron_up,
        "chevron_down": ModernIcons.chevron_down,
    }

    def __init__(self, theme_manager):
        """Initialize icon factory.

        Args:
            theme_manager: ThemeManager instance for colors
        """
        from .theme import ThemeManager
        if not isinstance(theme_manager, ThemeManager):
            raise TypeError("theme_manager must be a ThemeManager instance")
        self.theme_manager = theme_manager

    def create(self, parent: tk.Widget, icon_name: str,
               size: int = 20, color: Optional[str] = None) -> tk.Canvas:
        """Create an icon canvas widget.

        Args:
            parent: Parent widget
            icon_name: Name of the icon to draw
            size: Size of the icon (square)
            color: Color override (uses theme color if None)

        Returns:
            Canvas widget with the icon drawn

        Raises:
            ValueError: If icon_name is not recognized
        """
        if icon_name not in self.ICON_MAP:
            raise ValueError(f"Unknown icon: {icon_name}. Available: {list(self.ICON_MAP.keys())}")

        # Get color - use primary color if not specified
        if color is None:
            color = self.theme_manager.get_color("primary")

        # Try to get parent background, safe for both Tk and Ttk widgets
        try:
            parent_bg = parent.cget("bg")
        except (tk.TclError, AttributeError):
            # Fallback for Ttk widgets that don't support cget("bg")
            parent_bg = self.theme_manager.get_color("bg_main")

        # Create canvas
        canvas = tk.Canvas(
            parent,
            width=size,
            height=size,
            highlightthickness=0,
            bg=parent_bg
        )

        # Draw the icon
        draw_func = self.ICON_MAP[icon_name]
        draw_func(canvas, 0, 0, size, color)

        return canvas

    def get_button_icon(self, parent: tk.Widget, icon_name: str,
                        size: int = 20, command=None) -> tk.Canvas:
        """Create a clickable icon button.

        Args:
            parent: Parent widget
            icon_name: Name of the icon to draw
            size: Size of the icon
            command: Callback function for click

        Returns:
            Canvas widget that acts as a button
        """
        canvas = self.create(parent, icon_name, size)

        if command:
            # Bind click events
            canvas.bind("<Button-1>", lambda e: command())
            canvas.bind("<Return>", lambda e: command())
            canvas.bind("<space>", lambda e: command())

            # Add hover effect
            def on_enter(e):
                canvas.config(cursor="hand2")

            def on_leave(e):
                canvas.config(cursor="")

            canvas.bind("<Enter>", on_enter)
            canvas.bind("<Leave>", on_leave)

        return canvas

    @classmethod
    def get_available_icons(cls) -> List[str]:
        """Get list of all available icon names."""
        return list(cls.ICON_MAP.keys())
