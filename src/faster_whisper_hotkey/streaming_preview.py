"""
Real-time streaming transcription preview window.

This module provides a floating preview window that shows transcription
results as they are being generated, with confidence highlighting and
editable text.

Classes
-------
StreamingPreviewWindow
    Floating window for real-time transcription preview.
"""

import logging
import tkinter as tk
from tkinter import ttk, font
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class StreamingPreviewWindow:
    """
    Floating preview window for real-time streaming transcription.

    Features:
    - Editable text widget that updates as transcription progresses
    - Confidence highlighting (low confidence in red)
    - Always on top during recording
    - Auto-close on completion
    """

    # Color scheme for confidence highlighting
    LOW_CONFIDENCE_COLOR = "#d32f2f"  # Red 700
    MEDIUM_CONFIDENCE_COLOR = "#f57c00"  # Orange 700
    HIGH_CONFIDENCE_COLOR = "#388e3c"  # Green 700

    def __init__(
        self,
        theme_manager,
        confidence_threshold: float = 0.5,
        on_edit: Optional[Callable[[str], None]] = None,
        on_close: Optional[Callable[[], None]] = None,
    ):
        """
        Initialize the streaming preview window.

        Args:
            theme_manager: ThemeManager instance for styling
            confidence_threshold: Threshold for low-confidence highlighting (0-1)
            on_edit: Callback when text is edited by user
            on_close: Callback when window is closed
        """
        self.theme_manager = theme_manager
        self.confidence_threshold = confidence_threshold
        self.on_edit = on_edit
        self.on_close = on_close

        self.window = None
        self.text_widget = None
        self.status_label = None
        self.current_text = ""
        self.current_confidence = 1.0
        self.is_visible = False
        self._last_edit_time = 0

    def show(self):
        """Show the preview window."""
        if self.is_visible:
            return

        # Create the window
        self.window = tk.Tk()
        self.window.title("Transcription Preview")
        self.window.withdraw()  # Hide initially, we'll show and position it

        # Make window always on top
        self.window.attributes("-topmost", True)
        self.window.attributes("-alpha", 0.95)

        # Set window size
        self.window.geometry("600x300")

        # Apply theme
        self._setup_theme()

        # Create UI
        self._create_widgets()

        # Center on screen
        self._center_window()

        # Show window
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()
        self.is_visible = True

        logger.debug("Streaming preview window shown")

    def hide(self):
        """Hide and destroy the preview window."""
        if self.window and self.is_visible:
            try:
                # Get final text content if user edited it
                if self.text_widget and self.on_edit:
                    final_text = self.text_widget.get("1.0", "end-1c")
                    if final_text != self.current_text:
                        self.on_edit(final_text)

                self.window.destroy()
            except Exception as e:
                logger.debug(f"Error closing preview window: {e}")
            finally:
                self.window = None
                self.text_widget = None
                self.is_visible = False

        if self.on_close:
            try:
                self.on_close()
            except Exception as e:
                logger.debug(f"On close callback error: {e}")

        logger.debug("Streaming preview window hidden")

    def update_text(self, text: str, confidence: float = 1.0, is_final: bool = False):
        """
        Update the preview text with confidence highlighting.

        Args:
            text: Transcription text to display
            confidence: Confidence score (0-1)
            is_final: Whether this is the final result
        """
        if not self.is_visible or not self.text_widget:
            return

        self.current_text = text
        self.current_confidence = confidence

        # Don't update if user is currently editing
        import time
        if time.time() - self._last_edit_time < 0.5:
            return

        try:
            # Clear current content
            self.text_widget.delete("1.0", "end")

            # Determine color based on confidence
            if confidence < self.confidence_threshold:
                text_color = self.LOW_CONFIDENCE_COLOR
                status_text = f"Low confidence ({confidence:.1%})"
            elif confidence < 0.75:
                text_color = self.MEDIUM_CONFIDENCE_COLOR
                status_text = f"Medium confidence ({confidence:.1%})"
            else:
                text_color = self.theme_manager.get_color("fg_primary")
                status_text = f"High confidence ({confidence:.1%})"

            # Insert text with appropriate color
            self.text_widget.insert("1.0", text)
            self.text_widget.configure(fg=text_color)

            # Update status label
            if self.status_label:
                if is_final:
                    self.status_label.configure(text="✓ Final result", fg=self.HIGH_CONFIDENCE_COLOR)
                else:
                    self.status_label.configure(text=status_text, fg=self.theme_manager.get_color("fg_secondary"))

        except Exception as e:
            logger.debug(f"Error updating preview text: {e}")

    def get_text(self) -> str:
        """Get the current text content."""
        if self.text_widget:
            return self.text_widget.get("1.0", "end-1c")
        return self.current_text

    def _setup_theme(self):
        """Apply the current theme to the window."""
        mode = self.theme_manager.current_mode
        bg_color = self.theme_manager.get_color("bg_primary")
        fg_color = self.theme_manager.get_color("fg_primary")

        self.window.configure(bg=bg_color)

        # Configure style
        style = ttk.Style()
        style.theme_use("clam")

        if mode == "dark":
            style.configure("TFrame", background=bg_color)
            style.configure("TLabel", background=bg_color, foreground=fg_color)
            style.configure("TButton", background="#424242", foreground="white", borderwidth=1)
        else:
            style.configure("TFrame", background=bg_color)
            style.configure("TLabel", background=bg_color, foreground=fg_color)
            style.configure("TButton", background="#e0e0e0", foreground="#333333", borderwidth=1)

    def _create_widgets(self):
        """Create the window widgets."""
        bg_color = self.theme_manager.get_color("bg_primary")
        fg_color = self.theme_manager.get_color("fg_primary")

        # Main frame
        main_frame = ttk.Frame(self.window, padding=16)
        main_frame.pack(fill="both", expand=True)

        # Header with status
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 8))

        title_label = ttk.Label(
            header_frame,
            text="🎙️ Live Transcription",
            font=("", 12, "bold")
        )
        title_label.pack(side="left")

        self.status_label = ttk.Label(
            header_frame,
            text="Initializing...",
            font=("", 9)
        )
        self.status_label.pack(side="right")

        # Text widget with custom styling
        text_frame = tk.Frame(main_frame, bg=bg_color)
        text_frame.pack(fill="both", expand=True)

        # Create styled text widget
        self.text_widget = tk.Text(
            text_frame,
            wrap="word",
            font=("Helvetica", 14),
            bg=bg_color,
            fg=fg_color,
            insertbackground=fg_color,
            relief="flat",
            padx=16,
            pady=16,
            highlightthickness=1,
            highlightbackground="#e0e0e0" if self.theme_manager.current_mode == "light" else "#424242"
        )
        self.text_widget.pack(fill="both", expand=True)

        # Bind edit event
        self.text_widget.bind("<<Modified>>", self._on_text_modified)
        self.text_widget.bind("Key", self._on_key_press)

        # Instructions label
        instructions = ttk.Label(
            main_frame,
            text="Edit text as needed. Window will close when transcription is complete.",
            font=("", 8),
            foreground=self.theme_manager.get_color("fg_secondary")
        )
        instructions.pack(pady=(8, 0))

    def _on_text_modified(self, event=None):
        """Handle text modification by user."""
        import time
        self._last_edit_time = time.time()

    def _on_key_press(self, event=None):
        """Track key presses to detect user editing."""
        import time
        self._last_edit_time = time.time()

    def _center_window(self):
        """Center the window on the screen."""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def run(self):
        """
        Run the window main loop.

        This is a blocking call. For non-blocking usage, the window
        operates independently and updates can be scheduled via
        the update_text method.
        """
        if self.window:
            self.window.mainloop()
