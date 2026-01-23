"""
Toast notification system for faster-whisper-hotkey.

This module provides non-intrusive toast notifications that appear
briefly and then disappear automatically.

Classes
-------
ToastNotification
    Creates and displays a toast notification window.

Notes
-----
Toast notifications appear at the bottom-right of the screen and
automatically dismiss after a short duration.
"""

import tkinter as tk
from tkinter import ttk
import threading
import time


class ToastNotification:
    """
    A non-intrusive toast notification that appears and auto-dismisses.

    Parameters
    ----------
    message : str
        The message text to display.
    title : str, optional
        Optional title for the toast (default: empty).
    duration : int, optional
        How long to show the toast in milliseconds (default: 3000).
    icon : str, optional
        Icon type: "info", "success", "warning", "error" (default: "success").
    """

    # Color scheme for different icons
    COLORS = {
        "info": {"bg": "#2196F3", "fg": "#FFFFFF"},      # Blue
        "success": {"bg": "#4CAF50", "fg": "#FFFFFF"},   # Green
        "warning": {"bg": "#FF9800", "fg": "#FFFFFF"},   # Orange
        "error": {"bg": "#F44336", "fg": "#FFFFFF"},     # Red
    }

    def __init__(self, message, title="", duration=3000, icon="success"):
        self.message = message
        self.title = title
        self.duration = duration
        self.icon = icon
        self.window = None
        self._dismissed = False

    def show(self):
        """Show the toast notification in a new window."""
        # Create and show in a separate thread to avoid blocking
        thread = threading.Thread(target=self._create_and_show, daemon=True)
        thread.start()

    def _create_and_show(self):
        """Create the toast window and run the tkinter event loop."""
        # Create a new tkinter window for the toast
        root = tk.Tk()
        self.window = root

        # Configure the window
        root.overrideredirect(True)  # Remove window decorations
        root.attributes("-topmost", True)  # Keep on top
        root.attributes("-alpha", 0.95)  # Slight transparency

        # Get screen dimensions
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        # Set toast size
        toast_width = 350
        toast_height = 80

        # Position at bottom-right with margin
        margin = 20
        x = screen_width - toast_width - margin
        y = screen_height - toast_height - margin

        root.geometry(f"{toast_width}x{toast_height}+{x}+{y}")

        # Get colors based on icon type
        colors = self.COLORS.get(self.icon, self.COLORS["success"])

        # Main frame with rounded corners effect
        main_frame = tk.Frame(
            root,
            bg=colors["bg"],
            highlightbackground=colors["bg"],
            highlightthickness=1,
            padx=15,
            pady=10
        )
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Content frame
        content_frame = tk.Frame(main_frame, bg=colors["bg"])
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Icon indicator (colored circle)
        icon_frame = tk.Frame(content_frame, bg=colors["bg"])
        icon_frame.pack(side=tk.LEFT, padx=(0, 12))

        # Draw a simple icon using canvas
        canvas = tk.Canvas(
            icon_frame,
            width=24,
            height=24,
            bg=colors["bg"],
            highlightthickness=0
        )
        canvas.pack()

        # Draw icon based on type
        self._draw_icon(canvas, colors["fg"])

        # Text frame
        text_frame = tk.Frame(content_frame, bg=colors["bg"])
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Title (if provided)
        if self.title:
            title_label = tk.Label(
                text_frame,
                text=self.title,
                bg=colors["bg"],
                fg=colors["fg"],
                font=("", 10, "bold"),
                anchor=tk.W
            )
            title_label.pack(fill=tk.X)

        # Message
        message_label = tk.Label(
            text_frame,
            text=self.message,
            bg=colors["bg"],
            fg=colors["fg"],
            font=("", 9),
            anchor=tk.W,
            wraplength=toast_width - 80
        )
        message_label.pack(fill=tk.BOTH, expand=True)

        # Animate in (fade in)
        for i in range(10):
            root.attributes("-alpha", 0.1 + (i * 0.085))
            root.update()
            time.sleep(0.015)

        # Wait for duration
        root.after(self.duration, self._dismiss)

        # Run the event loop
        root.mainloop()

    def _draw_icon(self, canvas, color):
        """Draw an icon on the canvas based on icon type."""
        w, h = 24, 24
        center_x, center_y = 12, 12

        if self.icon == "success":
            # Checkmark
            canvas.create_oval(1, 1, 23, 23, outline=color, width=2)
            canvas.create_line(7, 12, 10, 16, 17, 8, fill=color, width=2, capstyle=tk.ROUND)
        elif self.icon == "info":
            # Info circle
            canvas.create_oval(1, 1, 23, 23, outline=color, width=2)
            canvas.create_text(center_x, center_y - 3, text="i", fill=color, font=("", 14, "bold"))
        elif self.icon == "warning":
            # Warning triangle
            points = [center_x, 2, 22, 21, 2, 21]
            canvas.create_polygon(points, outline=color, fill="", width=2)
            canvas.create_text(center_x, 15, text="!", fill=color, font=("", 12, "bold"))
        elif self.icon == "error":
            # X mark
            canvas.create_oval(1, 1, 23, 23, outline=color, width=2)
            canvas.create_line(8, 8, 16, 16, fill=color, width=2, capstyle=tk.ROUND)
            canvas.create_line(16, 8, 8, 16, fill=color, width=2, capstyle=tk.ROUND)
        else:
            # Default circle
            canvas.create_oval(1, 1, 23, 23, outline=color, width=2)

    def _dismiss(self):
        """Animate out and close the toast."""
        if self._dismissed or not self.window:
            return

        self._dismissed = True

        # Animate out (fade out)
        for i in range(10):
            alpha = 0.95 - (i * 0.095)
            if alpha < 0:
                alpha = 0
            try:
                self.window.attributes("-alpha", alpha)
                self.window.update()
                time.sleep(0.015)
            except:
                break

        # Close the window
        try:
            self.window.destroy()
        except:
            pass


def show_toast(message, title="", duration=3000, icon="success"):
    """
    Convenience function to show a toast notification.

    Parameters
    ----------
    message : str
        The message text to display.
    title : str, optional
        Optional title for the toast.
    duration : int, optional
        How long to show the toast in milliseconds.
    icon : str, optional
        Icon type: "info", "success", "warning", "error".
    """
    toast = ToastNotification(message, title, duration, icon)
    toast.show()
