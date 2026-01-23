"""
Recording indicator overlay for faster-whisper-hotkey.

This module provides a floating, draggable overlay window that appears when
recording starts. It features a pulsing microphone animation, real-time audio
waveform visualization, duration counter, and auto-hides after transcription.

Classes
-------
RecordingOverlay
    Floating overlay window with recording indicator and visualization.

Notes
-----
The overlay is always-on-top and supports multi-monitor setups. It receives
real-time audio level updates for the waveform visualization.
"""

import logging
import time
import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
import threading
import math

logger = logging.getLogger(__name__)


class RecordingOverlay:
    """Floating overlay window with recording visualization.

    Features:
    - Pulsing microphone animation
    - Real-time audio waveform visualization
    - Duration counter
    - Draggable window
    - Always-on-top
    - Multi-monitor support
    - Auto-hide after transcription
    """

    # Colors
    COLOR_BG = "#1E1E1E"
    COLOR_FG = "#FFFFFF"
    COLOR_ACCENT = "#F44336"  # Red for recording
    COLOR_WAVEFORM = "#4CAF50"  # Green for waveform

    def __init__(
        self,
        parent: tk.Tk,
        on_close: Optional[Callable] = None
    ):
        """Initialize the recording overlay.

        Args:
            parent: The parent tkinter root window
            on_close: Callback when overlay is closed
        """
        self.parent = parent
        self.on_close = on_close
        self.window: Optional[tk.Toplevel] = None

        # Recording state
        self.is_recording = False
        self.recording_start_time: Optional[float] = None
        self.duration_update_job = None

        # Animation state
        self.pulse_phase = 0.0
        self.pulse_animation_job = None
        self.pulse_speed = 0.15  # Speed of pulse animation

        # Audio visualization state
        self.audio_level = 0.0  # Current audio level (0.0 to 1.0)
        self.waveform_bars = []
        self.num_bars = 20
        self.bar_max_height = 40
        self.bar_width = 6
        self.bar_spacing = 4

        # Dragging state
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_dragging = False

        # Position state (saved for persistence)
        self.position_x = None
        self.position_y = None

    def show(self):
        """Show the overlay window."""
        if self.window and self.window.winfo_exists():
            # Already visible, just update state
            self._start_recording()
            return

        self._create_window()
        self._start_recording()

    def hide(self):
        """Hide the overlay window."""
        self._stop_recording()

        if self.window and self.window.winfo_exists():
            # Save position before hiding
            self.position_x = self.window.winfo_x()
            self.position_y = self.window.winfo_y()
            self.window.destroy()
            self.window = None

        if self.duration_update_job:
            self.parent.after_cancel(self.duration_update_job)
            self.duration_update_job = None

        if self.pulse_animation_job:
            self.parent.after_cancel(self.pulse_animation_job)
            self.pulse_animation_job = None

        if self.on_close:
            self.on_close()

    def update_audio_level(self, level: float):
        """Update the audio level for visualization.

        Args:
            level: Audio level from 0.0 (silent) to 1.0 (max)
        """
        self.audio_level = max(0.0, min(1.0, level))
        if self.window and self.window.winfo_exists():
            self._update_waveform()

    def _create_window(self):
        """Create the overlay window."""
        self.window = tk.Toplevel(self.parent)

        # Remove window decorations
        self.window.overrideredirect(True)

        # Always on top
        self.window.attributes('-topmost', True)

        # Set background color
        self.window.configure(bg=self.COLOR_BG)

        # Make window click-through to some extent (except on the window itself)
        # Note: -disabled doesn't work on all platforms

        # Set window size
        window_width = 280
        window_height = 180
        self.window.geometry(f"{window_width}x{window_height}")

        # Position window (use saved position or default to bottom-right of primary screen)
        if self.position_x is not None and self.position_y is not None:
            self.window.geometry(f"+{self.position_x}+{self.position_y}")
        else:
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            x = screen_width - window_width - 50
            y = screen_height - window_height - 100
            self.window.geometry(f"+{x}+{y}")

        # Create main container with rounded border effect
        main_frame = tk.Frame(
            self.window,
            bg=self.COLOR_BG,
            highlightbackground=self.COLOR_ACCENT,
            highlightthickness=2,
            width=window_width,
            height=window_height
        )
        main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Header/drag handle
        header_frame = tk.Frame(
            main_frame,
            bg=self.COLOR_BG,
            cursor="fleur"
        )
        header_frame.pack(fill=tk.X, pady=(8, 5))

        # Make header draggable
        header_frame.bind("<ButtonPress-1>", self._on_drag_start)
        header_frame.bind("<ButtonRelease-1>", self._on_drag_stop)
        header_frame.bind("<B1-Motion>", self._on_drag_motion)

        # Status text
        status_label = tk.Label(
            header_frame,
            text="● REC",
            font=("Segoe UI", "10", "bold"),
            bg=self.COLOR_BG,
            fg=self.COLOR_ACCENT
        )
        status_label.pack(side=tk.LEFT, padx=10)

        # Close button
        close_btn = tk.Label(
            header_frame,
            text="✕",
            font=("Segoe UI", 12),
            bg=self.COLOR_BG,
            fg="#666666",
            cursor="hand2"
        )
        close_btn.pack(side=tk.RIGHT, padx=10)
        close_btn.bind("<Button-1>", lambda e: self.hide())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg="#FFFFFF"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg="#666666"))

        # Canvas for mic icon and pulse animation
        self.canvas = tk.Canvas(
            main_frame,
            width=100,
            height=100,
            bg=self.COLOR_BG,
            highlightthickness=0
        )
        self.canvas.pack(pady=5)

        # Duration label
        self.duration_label = tk.Label(
            main_frame,
            text="00:00",
            font=("Consolas", 14),
            bg=self.COLOR_BG,
            fg=self.COLOR_FG
        )
        self.duration_label.pack(pady=(0, 5))

        # Create waveform visualization bars
        waveform_frame = tk.Frame(main_frame, bg=self.COLOR_BG)
        waveform_frame.pack(pady=(5, 8))

        self.waveform_bars = []
        waveform_width = self.num_bars * (self.bar_width + self.bar_spacing) - self.bar_spacing
        self.waveform_canvas = tk.Canvas(
            waveform_frame,
            width=waveform_width + 10,
            height=self.bar_max_height + 10,
            bg=self.COLOR_BG,
            highlightthickness=0
        )
        self.waveform_canvas.pack()

        # Create bars
        for i in range(self.num_bars):
            x = 5 + i * (self.bar_width + self.bar_spacing)
            # Center the bars vertically
            y1 = (self.bar_max_height + 10) // 2
            y2 = y1
            bar = self.waveform_canvas.create_rectangle(
                x, y1, x + self.bar_width, y2,
                fill=self.COLOR_WAVEFORM,
                outline=""
            )
            self.waveform_bars.append(bar)

        # Bind click-through - make the window movable from anywhere
        main_frame.bind("<ButtonPress-1>", self._on_drag_start)
        main_frame.bind("<ButtonRelease-1>", self._on_drag_stop)
        main_frame.bind("<B1-Motion>", self._on_drag_motion)

        # Store the main canvas reference for the mic icon
        self._draw_mic_icon()

    def _start_recording(self):
        """Start recording state."""
        self.is_recording = True
        self.recording_start_time = time.time()
        self.audio_level = 0.0

        # Start animations
        self._animate_pulse()
        self._update_duration()

    def _stop_recording(self):
        """Stop recording state."""
        self.is_recording = False
        self.recording_start_time = None

    def _draw_mic_icon(self):
        """Draw the microphone icon on the canvas."""
        if not self.canvas or not self.canvas.winfo_exists():
            return

        self.canvas.delete("mic_icon")

        cx, cy = 50, 50  # Center of canvas

        # Draw mic body (rounded rectangle using standard rectangle with oval for rounded ends)
        mic_width = 20
        mic_height = 30
        mic_x1 = cx - mic_width // 2
        mic_y1 = cy - mic_height // 2 - 5
        mic_x2 = cx + mic_width // 2
        mic_y2 = cy + mic_height // 2 - 5

        # Draw the mic body as a rectangle with rounded ends using ovals
        # Main body rectangle
        self.canvas.create_rectangle(
            mic_x1, mic_y1 + 10,
            mic_x2, mic_y2 - 10,
            fill=self.COLOR_FG,
            outline="",
            tags="mic_icon"
        )
        # Top rounded cap
        self.canvas.create_oval(
            mic_x1, mic_y1,
            mic_x2, mic_y1 + 20,
            fill=self.COLOR_FG,
            outline="",
            tags="mic_icon"
        )
        # Bottom rounded cap
        self.canvas.create_oval(
            mic_x1, mic_y2 - 20,
            mic_x2, mic_y2,
            fill=self.COLOR_FG,
            outline="",
            tags="mic_icon"
        )

        # Draw mic stand
        self.canvas.create_line(
            cx, cy + mic_height // 2 - 5,
            cx, cy + mic_height // 2 + 10,
            fill=self.COLOR_FG,
            width=3,
            tags="mic_icon"
        )

        # Draw mic base
        self.canvas.create_line(
            cx - 10, cy + mic_height // 2 + 10,
            cx + 10, cy + mic_height // 2 + 10,
            fill=self.COLOR_FG,
            width=3,
            tags="mic_icon"
        )

        # Draw initial pulse circle
        self._draw_pulse_circle()

    def _draw_pulse_circle(self, radius: int = 35):
        """Draw the pulsing circle around the mic icon.

        Args:
            radius: Current radius of the pulse circle
        """
        self.canvas.delete("pulse")

        if not self.is_recording:
            return

        cx, cy = 50, 50

        # Calculate alpha based on pulse phase (simulated via stipple)
        # Since tkinter doesn't support alpha directly, we use stipple patterns
        stipple_pattern = ""
        if self.pulse_phase < 0.33:
            stipple_pattern = "gray75"  # More opaque
        elif self.pulse_phase < 0.66:
            stipple_pattern = "gray50"  # Semi-transparent
        else:
            stipple_pattern = "gray25"  # More transparent

        # Draw pulse circle
        try:
            self.canvas.create_oval(
                cx - radius, cy - radius,
                cx + radius, cy + radius,
                outline=self.COLOR_ACCENT,
                width=2,
                stipple=stipple_pattern,
                tags="pulse"
            )
        except Exception:
            # Fallback if stipple not supported
            self.canvas.create_oval(
                cx - radius, cy - radius,
                cx + radius, cy + radius,
                outline=self.COLOR_ACCENT,
                width=2,
                tags="pulse"
            )

    def _animate_pulse(self):
        """Animate the pulsing circle."""
        if not self.is_recording or not self.window or not self.window.winfo_exists():
            return

        # Update pulse phase
        self.pulse_phase = (self.pulse_phase + self.pulse_speed) % 1.0

        # Calculate radius based on sine wave
        base_radius = 35
        pulse_amount = math.sin(self.pulse_phase * 2 * math.pi)
        radius = base_radius + int(pulse_amount * 8)

        self._draw_pulse_circle(radius)

        # Schedule next animation frame (30 FPS)
        self.pulse_animation_job = self.parent.after(33, self._animate_pulse)

    def _update_duration(self):
        """Update the duration counter."""
        if not self.is_recording:
            return

        if self.recording_start_time is None:
            return

        elapsed = time.time() - self.recording_start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        duration_str = f"{minutes:02d}:{seconds:02d}"

        if self.window and self.window.winfo_exists():
            self.duration_label.config(text=duration_str)
            self.duration_update_job = self.parent.after(100, self._update_duration)

    def _update_waveform(self):
        """Update the waveform visualization based on current audio level."""
        if not self.waveform_bars or not self.waveform_canvas:
            return

        # Create a mirrored waveform effect where bars in the center are taller
        center = self.num_bars / 2

        for i, bar in enumerate(self.waveform_bars):
            # Calculate distance from center (0.0 to 1.0)
            distance = abs(i - center) / center

            # Apply Gaussian-like curve for smoother visualization
            curve_factor = math.exp(-2 * distance * distance)

            # Calculate bar height based on audio level and position
            # Add some randomness for more dynamic effect
            import random
            random_factor = 1.0 + (random.random() - 0.5) * 0.3
            height = int(self.bar_max_height * self.audio_level * curve_factor * random_factor)

            # Ensure minimum visibility when recording
            if self.is_recording and height < 2:
                height = 2

            # Update bar coordinates (centered)
            y_center = (self.bar_max_height + 10) // 2
            x1, y1, x2, y2 = self.waveform_canvas.coords(bar)
            self.waveform_canvas.coords(bar, x1, y_center - height // 2, x2, y_center + height // 2)

            # Update color based on level
            if self.audio_level > 0.7:
                color = "#FF5722"  # Orange-red for high levels
            elif self.audio_level > 0.4:
                color = self.COLOR_WAVEFORM  # Green for medium
            else:
                color = "#81C784"  # Light green for low
            self.waveform_canvas.itemconfig(bar, fill=color)

    def _on_drag_start(self, event):
        """Handle drag start."""
        self.drag_start_x = event.x_root - self.window.winfo_x()
        self.drag_start_y = event.y_root - self.window.winfo_y()
        self.is_dragging = True

    def _on_drag_stop(self, event):
        """Handle drag stop."""
        self.is_dragging = False

    def _on_drag_motion(self, event):
        """Handle drag motion."""
        if self.is_dragging and self.window:
            new_x = event.x_root - self.drag_start_x
            new_y = event.y_root - self.drag_start_y

            # Ensure window stays on screen
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            window_width = self.window.winfo_width()
            window_height = self.window.winfo_height()

            new_x = max(0, min(new_x, screen_width - window_width))
            new_y = max(0, min(new_y, screen_height - window_height))

            self.window.geometry(f"+{new_x}+{new_y}")


class RecordingOverlayManager:
    """Manager for the recording overlay lifecycle.

    This class handles showing, hiding, and updating the recording overlay
    based on transcription state changes.
    """

    def __init__(self, parent: tk.Tk):
        """Initialize the overlay manager.

        Args:
            parent: The parent tkinter root window
        """
        self.parent = parent
        self.overlay: Optional[RecordingOverlay] = None
        self.is_visible = False

    def show_recording(self):
        """Show the overlay when recording starts."""
        if not self.overlay:
            self.overlay = RecordingOverlay(
                self.parent,
                on_close=self._on_overlay_closed
            )
        self.overlay.show()
        self.is_visible = True

    def hide_transcribing(self):
        """Hide the overlay when transcription begins.

        The overlay auto-hides after recording stops and transcription begins.
        """
        if self.overlay:
            self.overlay.hide()
            self.is_visible = False

    def update_audio_level(self, level: float):
        """Update the audio level visualization.

        Args:
            level: Audio level from 0.0 (silent) to 1.0 (max)
        """
        if self.overlay and self.is_visible:
            self.overlay.update_audio_level(level)

    def _on_overlay_closed(self):
        """Handle overlay close."""
        self.is_visible = False


# Convenience function for creating and showing the overlay
def show_recording_overlay(parent: tk.Tk) -> RecordingOverlayManager:
    """Create and return a recording overlay manager.

    Args:
        parent: The parent tkinter root window

    Returns:
        RecordingOverlayManager instance
    """
    return RecordingOverlayManager(parent)
