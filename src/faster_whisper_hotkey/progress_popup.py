"""
Progress popup window for faster-whisper-hotkey.

This module provides a visual progress indicator that appears during
audio processing to reassure users that transcription is in progress.

Classes
-------
ProgressPopup
    A popup window with spinner animation and status message.

Notes
-----
The popup appears centered on screen and automatically updates
with processing status and time estimates.
"""

import tkinter as tk
from tkinter import ttk
import math
import time
import threading


class ProgressPopup:
    """
    A popup window showing transcription progress with spinner animation.

    Parameters
    ----------
    parent : tk.Tk or tk.Toplevel
        The parent tkinter window.
    audio_duration : float, optional
        Audio duration in seconds for time estimation.
    """

    def __init__(self, parent, audio_duration=None):
        self.parent = parent
        self.audio_duration = audio_duration
        self.window = None
        self.is_visible = False
        self.spinner_angle = 0
        self.animation_running = False
        self.start_time = None
        self.status_message = "Processing audio..."

        # Processing time tracking (for better estimates)
        self.processing_history = []  # List of (audio_duration, processing_time)

    def show(self, message="Processing audio..."):
        """Show the progress popup with the given message."""
        if self.is_visible:
            # Update message if already visible
            self.status_message = message
            self._update_message()
            return

        self.status_message = message
        self.start_time = time.time()

        # Schedule the window creation on the main thread
        self.parent.after(0, self._create_window)

    def update_message(self, message):
        """Update the status message."""
        self.status_message = message
        if self.is_visible and self.window:
            self.parent.after(0, self._update_message)

    def hide(self):
        """Hide the progress popup."""
        if not self.is_visible:
            return

        self.animation_running = False
        self.is_visible = False

        if self.window:
            self.parent.after(0, self._destroy_window)

    def _create_window(self):
        """Create the progress popup window."""
        # Create a toplevel window
        self.window = tk.Toplevel(self.parent)
        self.window.title("Processing")
        self.window.resizable(False, False)

        # Make the window stay on top
        self.window.attributes("-topmost", True)

        # Remove window decorations (optional, keeps it cleaner)
        # self.window.overrideredirect(True)

        # Calculate position (center on screen)
        self.window.update_idletasks()
        width = 300
        height = 150
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.window.geometry(f"{width}x{height}+{x}+{y}")

        # Main frame with styling
        main_frame = ttk.Frame(self.window, padding=25)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Spinner canvas
        self.canvas = tk.Canvas(
            main_frame,
            width=60,
            height=60,
            bg="#f0f0f0",
            highlightthickness=0
        )
        self.canvas.pack(pady=(0, 15))

        # Status message
        self.message_label = ttk.Label(
            main_frame,
            text=self.status_message,
            font=("", 10),
            anchor=tk.CENTER
        )
        self.message_label.pack()

        # Time estimate label
        self.estimate_label = ttk.Label(
            main_frame,
            text=self._get_estimate_text(),
            font=("", 9),
            foreground="gray",
            anchor=tk.CENTER
        )
        self.estimate_label.pack(pady=(5, 0))

        self.is_visible = True
        self.animation_running = True
        self.spinner_angle = 0

        # Start the spinner animation
        self._animate_spinner()

    def _update_message(self):
        """Update the message label."""
        if self.message_label:
            self.message_label.config(text=self.status_message)

        if self.estimate_label:
            self.estimate_label.config(text=self._get_estimate_text())

    def _destroy_window(self):
        """Destroy the popup window."""
        if self.window:
            try:
                self.window.destroy()
            except:
                pass
            self.window = None

    def _animate_spinner(self):
        """Animate the spinner."""
        if not self.animation_running or not self.window:
            return

        # Clear canvas
        self.canvas.delete("all")

        # Draw spinner segments
        center_x, center_y = 30, 30
        radius = 20
        segments = 8

        for i in range(segments):
            # Calculate angle for this segment
            angle = (self.spinner_angle + i * (360 / segments)) % 360
            rad = math.radians(angle)

            # Calculate color intensity (fade out as it goes around)
            intensity = 1 - (i / segments)
            # Color from orange to gray
            gray_value = int(200 + (55 * intensity))
            color = f"#{gray_value:02x}{gray_value:02x}{gray_value:02x}"
            if i == 0:
                color = "#FF9800"  # Orange for the leading segment

            # Calculate segment position
            x1 = center_x + radius * math.cos(rad)
            y1 = center_y + radius * math.sin(rad)
            x2 = center_x + (radius - 4) * math.cos(rad)
            y2 = center_y + (radius - 4) * math.sin(rad)

            # Draw the segment
            self.canvas.create_line(
                x1, y1, x2, y2,
                fill=color,
                width=4,
                capstyle=tk.ROUND
            )

        # Draw center circle
        self.canvas.create_oval(
            center_x - 4, center_y - 4,
            center_x + 4, center_y + 4,
            fill="#FF9800",
            outline=""
        )

        # Increment angle for next frame
        self.spinner_angle = (self.spinner_angle + 20) % 360

        # Schedule next frame (30 FPS)
        if self.animation_running:
            self.canvas.after(33, self._animate_spinner)

    def _get_estimate_text(self):
        """Generate the time estimate text."""
        if self.audio_duration is None:
            return "Please wait..."

        # Calculate elapsed time if we have a start time
        if self.start_time:
            elapsed = time.time() - self.start_time
            if elapsed > 0.5:
                return f"Audio: {self.audio_duration:.1f}s | Elapsed: {elapsed:.1f}s"

        return f"Audio duration: {self.audio_duration:.1f} seconds"

    def record_processing_time(self, processing_time):
        """
        Record a processing time for better future estimates.

        Parameters
        ----------
        processing_time : float
            The time taken to process in seconds.
        """
        if self.audio_duration:
            self.processing_history.append((self.audio_duration, processing_time))
            # Keep only the last 10 entries
            if len(self.processing_history) > 10:
                self.processing_history = self.processing_history[-10:]

    def get_estimate_for_duration(self, audio_duration):
        """
        Get an estimated processing time for a given audio duration.

        Parameters
        ----------
        audio_duration : float
            Audio duration in seconds.

        Returns
        -------
        float or None
            Estimated processing time in seconds, or None if no history.
        """
        if not self.processing_history:
            return None

        # Calculate average ratio
        ratios = [pt / ad for ad, pt in self.processing_history]
        if ratios:
            avg_ratio = sum(ratios) / len(ratios)
            return audio_duration * avg_ratio

        return None
