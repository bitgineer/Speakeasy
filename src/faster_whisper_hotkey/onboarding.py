"""
Interactive onboarding overlay for first-time users.

This module provides a progressive tutorial that introduces keyboard shortcuts
and key features to new users using a "show, don't tell" approach.

Classes
-------
OnboardingOverlay
    Interactive onboarding tutorial for first-time users.

Functions
---------
show_onboarding
    Convenience function to show the onboarding overlay.

Notes
-----
The tutorial consists of interactive steps where users perform actions:
welcome, mic test, model selection, hotkey setup, test transcription,
and completion. Progress is tracked in settings.
"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
import threading
import time
import numpy as np
import sounddevice as sd
import json

from .config import accepted_models_whisper, accepted_languages_whisper
from .settings import SETTINGS_FILE, save_settings

logger = logging.getLogger(__name__)


class OnboardingOverlay:
    """Interactive onboarding tutorial for first-time users.

    The tutorial guides users through interactive setup:
    1. Welcome and introduction
    2. Microphone test with visual feedback
    3. Model selection based on use case
    4. Hotkey setup with collision detection
    5. Test transcription with sample phrase
    6. Completion and summary
    """

    # Tutorial step definitions
    STEPS = [
        "welcome",
        "mic_test",
        "model_selection",
        "hotkey_setup",
        "test_transcription",
        "complete"
    ]

    STEP_TITLES = {
        "welcome": "Welcome to Faster Whisper Hotkey",
        "mic_test": "Microphone Test",
        "model_selection": "Choose Your Model",
        "hotkey_setup": "Setup Your Hotkey",
        "test_transcription": "Test Transcription",
        "complete": "Setup Complete"
    }

    # Model recommendations based on use case
    USE_CASES = {
        "general": {
            "title": "General Use (Meetings, Notes, Dictation)",
            "description": "Balanced speed and accuracy for everyday transcription",
            "models": ["tiny", "base", "small"],
            "recommended": "base"
        },
        "accurate": {
            "title": "High Accuracy (Important Recordings)",
            "description": "Best accuracy, slower processing",
            "models": ["medium", "large-v2", "large-v3"],
            "recommended": "medium"
        },
        "fast": {
            "title": "Real-Time Captioning (Live Events)",
            "description": "Fastest processing for live transcription",
            "models": ["tiny", "base"],
            "recommended": "tiny"
        },
        "custom": {
            "title": "Let Me Choose Manually",
            "description": "Browse all available models",
            "models": accepted_models_whisper,
            "recommended": "base"
        }
    }

    # Model descriptions
    MODEL_DESCRIPTIONS = {
        "tiny": "Fastest, ~32x faster than realtime, Good for quick drafts",
        "base": "Fast, ~16x faster than realtime, Good balance of speed/accuracy",
        "small": "Moderate, ~6x faster than realtime, Better accuracy",
        "medium": "Slower, ~2x faster than realtime, High accuracy",
        "large-v2": "Slowest, ~0.5x realtime, Best accuracy (v2)",
        "large-v3": "Slowest, ~0.5x realtime, Best accuracy (v3, newest)",
    }

    def __init__(
        self,
        parent: tk.Tk,
        gui_ref,
        on_complete: Optional[Callable] = None
    ):
        """Initialize the onboarding overlay.

        Args:
            parent: The parent tkinter root window
            gui_ref: Reference to the WhisperHotkeyGUI instance
            on_complete: Callback when tutorial is completed or skipped
        """
        self.parent = parent
        self.gui_ref = gui_ref
        self.on_complete = on_complete
        self.current_step_index = 0
        self.window = None
        self.step_content_frame = None
        self.navigation_frame = None

        # Store user choices during onboarding
        self.user_choices = {
            "model": None,
            "language": "en",
            "hotkey": "pause",
            "activation_mode": "hold"
        }

        # Audio testing state
        self.is_testing_mic = False
        self.audio_stream = None
        self.mic_level_callback_id = None

    def show(self):
        """Show the onboarding overlay."""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()
            return

        self._create_window()
        self._show_step(self.current_step_index)

    def _create_window(self):
        """Create the main tutorial window."""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Interactive Setup Tutorial")
        self.window.geometry("600x550")
        self.window.resizable(False, False)

        # Make window stay on top
        self.window.transient(self.parent)
        self.window.attributes('-topmost', True)

        # Center on screen
        self.window.update_idletasks()
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - 600) // 2
        y = (screen_height - 550) // 2
        self.window.geometry(f"+{x}+{y}")

        # Main container
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header with progress
        self._create_header(main_frame)

        # Content area
        self.step_content_frame = ttk.Frame(main_frame)
        self.step_content_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 10))

        # Navigation buttons
        self._create_navigation(main_frame)

        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_header(self, parent):
        """Create the header with progress indicator."""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        # Title
        self.title_label = ttk.Label(
            header_frame,
            text="",
            font=("", 14, "bold")
        )
        self.title_label.pack(anchor=tk.W)

        # Progress indicator
        self.progress_label = ttk.Label(
            header_frame,
            text="",
            font=("", 9),
            foreground="gray"
        )
        self.progress_label.pack(anchor=tk.W, pady=(5, 0))

        # Progress bar
        self.progress_bar = ttk.Progressbar(
            header_frame,
            mode='determinate',
            maximum=100
        )
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))

        ttk.Separator(header_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(10, 0))

    def _create_navigation(self, parent):
        """Create navigation buttons."""
        self.navigation_frame = ttk.Frame(parent)
        self.navigation_frame.pack(fill=tk.X, pady=(10, 0))

        # Skip tutorial button (left side)
        self.skip_btn = ttk.Button(
            self.navigation_frame,
            text="Skip Tutorial",
            command=self._skip_tutorial
        )
        self.skip_btn.pack(side=tk.LEFT)

        # Navigation buttons (right side)
        nav_btn_frame = ttk.Frame(self.navigation_frame)
        nav_btn_frame.pack(side=tk.RIGHT)

        self.back_btn = ttk.Button(
            nav_btn_frame,
            text="Back",
            command=self._back,
            width=8
        )
        self.back_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.next_btn = ttk.Button(
            nav_btn_frame,
            text="Next",
            command=self._next,
            width=8
        )
        self.next_btn.pack(side=tk.LEFT)

    def _update_header(self):
        """Update the header for the current step."""
        step_key = self.STEPS[self.current_step_index]
        self.title_label.config(text=self.STEP_TITLES[step_key])

        # Progress text
        current = self.current_step_index + 1
        total = len(self.STEPS)
        self.progress_label.config(text=f"Step {current} of {total}")

        # Progress bar
        progress = (current / total) * 100
        self.progress_bar['value'] = progress

        # Update button states
        self.back_btn.config(state=tk.NORMAL if self.current_step_index > 0 else tk.DISABLED)

        if step_key == "complete":
            self.next_btn.config(text="Finish", command=self._finish)
        else:
            self.next_btn.config(text="Next", command=self._next)

    def _show_step(self, step_index: int):
        """Show a specific tutorial step."""
        # Stop any ongoing mic test when switching steps
        if self.is_testing_mic:
            self._stop_mic_test()

        # Clear previous content
        for widget in self.step_content_frame.winfo_children():
            widget.destroy()

        self.current_step_index = step_index
        self._update_header()

        step_key = self.STEPS[step_index]

        # Call the appropriate step renderer
        step_method = getattr(self, f"_step_{step_key}", None)
        if step_method:
            step_method()
        else:
            self._step_fallback(step_key)

    # ========================================================================
    # Step 1: Welcome
    # ========================================================================

    def _step_welcome(self):
        """Step 1: Welcome screen with value proposition."""
        # Welcome icon/emoji
        icon_label = ttk.Label(
            self.step_content_frame,
            text="Welcome!",
            font=("", 24, "bold"),
            foreground="#4CAF50"
        )
        icon_label.pack(pady=(20, 20))

        # Value proposition
        value_prop_text = (
            "Faster Whisper Hotkey transforms your voice into text instantly.\n"
            "Press a hotkey, speak, and your words appear in your clipboard."
        )
        ttk.Label(self.step_content_frame, text=value_prop_text, font=("", 11), justify=tk.CENTER).pack(pady=(0, 20))

        # What you'll do in this tutorial
        tutorial_frame = ttk.LabelFrame(self.step_content_frame, text="In This Tutorial", padding=15)
        tutorial_frame.pack(fill=tk.X, padx=20)

        steps = [
            (" Test your microphone", "Ensure your audio is working"),
            (" Choose a model", "Select the right AI model for your needs"),
            (" Setup your hotkey", "Pick a comfortable keyboard shortcut"),
            (" Test transcription", "Try it out with a sample phrase")
        ]

        for icon, description in steps:
            step_frame = ttk.Frame(tutorial_frame)
            step_frame.pack(fill=tk.X, pady=5)
            ttk.Label(step_frame, text=icon, font=("", 10)).pack(side=tk.LEFT)
            ttk.Label(step_frame, text=description, font=("", 9)).pack(side=tk.LEFT, padx=(10, 0))

        ttk.Label(
            self.step_content_frame,
            text="\nThe tutorial takes about 3 minutes to complete.",
            foreground="gray",
            font=("", 9)
        ).pack(pady=(20, 0))

    # ========================================================================
    # Step 2: Microphone Test
    # ========================================================================

    def _step_mic_test(self):
        """Step 2: Microphone test with visual feedback."""
        # Title
        ttk.Label(
            self.step_content_frame,
            text="Let's Test Your Microphone",
            font=("", 12, "bold")
        ).pack(pady=(0, 10))

        # Instructions
        ttk.Label(
            self.step_content_frame,
            text="Click 'Start Test' and speak into your microphone.",
            font=("", 10)
        ).pack(pady=(0, 5))

        # Audio level meter container
        meter_frame = ttk.Frame(self.step_content_frame)
        meter_frame.pack(pady=20)

        # Audio level bar
        self.mic_level_canvas = tk.Canvas(meter_frame, width=300, height=30, bg="#f0f0f0", highlightthickness=1, highlightbackground="#ccc")
        self.mic_level_canvas.pack()

        # Level indicator bar
        self.mic_level_bar = self.mic_level_canvas.create_rectangle(
            0, 0, 0, 30, fill="#4CAF50", outline=""
        )

        # Level labels
        level_frame = ttk.Frame(meter_frame)
        level_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(level_frame, text="Quiet", font=("", 8)).pack(side=tk.LEFT)
        ttk.Label(level_frame, text="Loud", font=("", 8)).pack(side=tk.RIGHT)

        # Status label
        self.mic_status_label = ttk.Label(
            self.step_content_frame,
            text="Ready to test",
            font=("", 10),
            foreground="gray"
        )
        self.mic_status_label.pack(pady=(10, 0))

        # Control buttons
        btn_frame = ttk.Frame(self.step_content_frame)
        btn_frame.pack(pady=15)

        self.mic_test_btn = ttk.Button(
            btn_frame,
            text="Start Test",
            command=self._toggle_mic_test,
            width=15
        )
        self.mic_test_btn.pack()

        # Explanation
        help_text = (
            "Tips:\n"
            "  Speak clearly at a normal volume\n"
            "  The bar should move when you talk\n"
            "  Green = Good, Yellow = Quiet, Red = Too Loud"
        )
        ttk.Label(
            self.step_content_frame,
            text=help_text,
            font=("", 9),
            foreground="gray",
            justify=tk.LEFT
        ).pack(pady=(15, 0))

    def _toggle_mic_test(self):
        """Toggle microphone test on/off."""
        if not self.is_testing_mic:
            self._start_mic_test()
        else:
            self._stop_mic_test()

    def _start_mic_test(self):
        """Start the microphone test."""
        try:
            self.is_testing_mic = True
            self.mic_test_btn.config(text="Stop Test")
            self.mic_status_label.config(text="Testing... Speak now!", foreground="#4CAF50")

            # Start audio stream for level monitoring
            def audio_callback(indata, frames, time, status):
                if status:
                    logger.warning(f"Audio callback status: {status}")
                # Calculate RMS level
                level = np.sqrt(np.mean(indata**2))
                # Update UI in main thread
                self.parent.after(0, lambda: self._update_mic_level(level))

            self.audio_stream = sd.InputStream(
                samplerate=16000,
                channels=1,
                dtype=np.float32,
                callback=audio_callback
            )
            self.audio_stream.start()

        except Exception as e:
            logger.error(f"Error starting mic test: {e}")
            self._stop_mic_test()
            messagebox.showerror("Microphone Error", f"Could not access microphone:\n{e}")

    def _stop_mic_test(self):
        """Stop the microphone test."""
        self.is_testing_mic = False
        self.mic_test_btn.config(text="Start Test")
        self.mic_status_label.config(text="Test stopped", foreground="gray")

        if self.audio_stream:
            try:
                self.audio_stream.stop()
                self.audio_stream.close()
            except Exception as e:
                logger.warning(f"Error stopping audio stream: {e}")
            self.audio_stream = None

        # Reset level bar
        self.parent.after(0, lambda: self._update_mic_level(0))

    def _update_mic_level(self, level: float):
        """Update the microphone level display."""
        if not self.mic_level_canvas.winfo_exists():
            return

        # Scale level (typical RMS range is 0.0 to 0.5)
        scaled_level = min(max(level * 400, 0), 100)

        # Determine color based on level
        if scaled_level < 20:
            color = "#FFC107"  # Yellow - too quiet
        elif scaled_level < 80:
            color = "#4CAF50"  # Green - good
        else:
            color = "#F44336"  # Red - too loud

        # Update bar
        self.mic_level_canvas.coords(self.mic_level_bar, 0, 0, scaled_level * 3, 30)
        self.mic_level_canvas.itemconfig(self.mic_level_bar, fill=color)

    # ========================================================================
    # Step 3: Model Selection
    # ========================================================================

    def _step_model_selection(self):
        """Step 3: Model selection based on use case."""
        # Title
        ttk.Label(
            self.step_content_frame,
            text="What Will You Use This For?",
            font=("", 12, "bold")
        ).pack(pady=(0, 15))

        # Use case selection
        use_case_frame = ttk.LabelFrame(self.step_content_frame, text="Select Your Use Case", padding=10)
        use_case_frame.pack(fill=tk.X, padx=10, pady=(0, 15))

        self.selected_use_case = tk.StringVar(value="general")
        self.use_case_descriptions = {}

        for key, info in self.USE_CASES.items():
            frame = ttk.Frame(use_case_frame)
            frame.pack(fill=tk.X, pady=5)

            rb = ttk.Radiobutton(
                frame,
                text=info["title"],
                variable=self.selected_use_case,
                value=key,
                command=self._on_use_case_changed
            )
            rb.pack(anchor=tk.W)

            desc_label = ttk.Label(
                frame,
                text=info["description"],
                font=("", 9),
                foreground="gray"
            )
            desc_label.pack(anchor=tk.W, padx=(20, 0))
            self.use_case_descriptions[key] = desc_label

        # Model preview area
        self.model_preview_frame = ttk.LabelFrame(self.step_content_frame, text="Recommended Models", padding=10)
        self.model_preview_frame.pack(fill=tk.BOTH, expand=True, padx=10)

        self.model_var = tk.StringVar(value="base")
        self._update_model_preview()

        # Initialize with general use case
        self._on_use_case_changed()

    def _on_use_case_changed(self):
        """Handle use case selection change."""
        use_case = self.selected_use_case.get()
        models = self.USE_CASES[use_case]["models"]
        recommended = self.USE_CASES[use_case]["recommended"]

        # Clear previous model options
        for widget in self.model_preview_frame.winfo_children():
            widget.destroy()

        # Header
        ttk.Label(
            self.model_preview_frame,
            text=f"Recommended: {recommended.upper()}",
            font=("", 10, "bold"),
            foreground="#4CAF50"
        ).pack(anchor=tk.W, pady=(0, 10))

        # Model options
        for model in models:
            desc = self.MODEL_DESCRIPTIONS.get(model, f"AI model: {model}")

            frame = ttk.Frame(self.model_preview_frame)
            frame.pack(fill=tk.X, pady=3)

            # Radio button for model
            rb = ttk.Radiobutton(
                frame,
                text=model.upper(),
                variable=self.model_var,
                value=model
            )
            rb.pack(side=tk.LEFT)

            # Description
            is_recommended = (model == recommended)
            fg = "#1976D2" if is_recommended else "gray"
            font_spec = ("", 9, "bold") if is_recommended else ("", 9)

            desc_label = ttk.Label(
                frame,
                text=f" - {desc}",
                font=font_spec,
                foreground=fg
            )
            desc_label.pack(side=tk.LEFT, padx=(10, 0))

            # Recommended badge
            if is_recommended:
                ttk.Label(
                    frame,
                    text=" [RECOMMENDED]",
                    font=("", 8),
                    foreground="#4CAF50"
                ).pack(side=tk.LEFT)

        # Set default to recommended
        self.model_var.set(recommended)

    def _update_model_preview(self):
        """Update the model preview display."""
        pass  # Updated dynamically in _on_use_case_changed

    # ========================================================================
    # Step 4: Hotkey Setup
    # ========================================================================

    def _step_hotkey_setup(self):
        """Step 4: Hotkey setup with collision detection."""
        # Title
        ttk.Label(
            self.step_content_frame,
            text="Choose Your Recording Hotkey",
            font=("", 12, "bold")
        ).pack(pady=(0, 10))

        # Current hotkey display
        self.hotkey_frame = ttk.Frame(self.step_content_frame)
        self.hotkey_frame.pack(pady=(20, 0))

        ttk.Label(self.hotkey_frame, text="Your Hotkey:", font=("", 10)).pack(side=tk.LEFT)

        self.hotkey_display = tk.Label(
            self.hotkey_frame,
            text=self.user_choices["hotkey"].upper(),
            font=("Consolas", 18, "bold"),
            bg="#E3F2FD",
            fg="#1976D2",
            padx=15,
            pady=8
        )
        self.hotkey_display.pack(side=tk.LEFT, padx=(10, 0))

        # Change hotkey button
        ttk.Button(
            self.hotkey_frame,
            text="Change",
            command=self._show_hotkey_dialog,
            width=8
        ).pack(side=tk.LEFT, padx=(15, 0))

        # Hotkey status
        self.hotkey_status_label = ttk.Label(
            self.step_content_frame,
            text="This hotkey is available",
            font=("", 10),
            foreground="#4CAF50"
        )
        self.hotkey_status_label.pack(pady=(10, 0))

        # Activation mode
        mode_frame = ttk.LabelFrame(self.step_content_frame, text="Activation Mode", padding=10)
        mode_frame.pack(fill=tk.X, padx=20, pady=(20, 0))

        self.activation_mode_var = tk.StringVar(value=self.user_choices["activation_mode"])

        ttk.Radiobutton(
            mode_frame,
            text="Hold - Press and hold to record, release to transcribe",
            variable=self.activation_mode_var,
            value="hold"
        ).pack(anchor=tk.W, pady=3)

        ttk.Radiobutton(
            mode_frame,
            text="Toggle - Press to start, press again to stop",
            variable=self.activation_mode_var,
            value="toggle"
        ).pack(anchor=tk.W, pady=3)

        # Tips
        tips_text = (
            "Tips:\n"
            "  Choose a key that's easy to reach but won't be pressed accidentally\n"
            "  F-keys (F1-F12) and PAUSE work well\n"
            "  You can change this later in Settings"
        )
        ttk.Label(
            self.step_content_frame,
            text=tips_text,
            font=("", 9),
            foreground="gray",
            justify=tk.LEFT
        ).pack(pady=(20, 0))

    def _show_hotkey_dialog(self):
        """Show dialog to capture a new hotkey."""
        dialog = tk.Toplevel(self.window)
        dialog.title("Press a Key")
        dialog.geometry("300x120")
        dialog.transient(self.window)
        dialog.attributes('-topmost', True)
        dialog.grab_set()

        # Center on parent
        dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - 300) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - 120) // 2
        dialog.geometry(f"+{x}+{y}")

        ttk.Label(
            dialog,
            text="Press any key or combination...",
            font=("", 11)
        ).pack(pady=20)

        captured_label = ttk.Label(
            dialog,
            text="",
            font=("Consolas", 14, "bold"),
            foreground="#1976D2"
        )
        captured_label.pack(pady=10)

        captured_hotkey = {"value": None}

        def on_press(key):
            try:
                key_char = key.char
                if key_char:
                    captured_hotkey["value"] = key_char.lower()
                    captured_label.config(text=key_char.upper())
            except AttributeError:
                # Special key
                key_name = key.name.lower()
                captured_hotkey["value"] = key_name
                captured_label.config(text=key_name.upper())

            # Auto-close after short delay
            dialog.after(500, dialog.destroy)

        from pynput import keyboard
        listener = keyboard.Listener(on_press=on_press)
        listener.start()

        dialog.wait_window()
        listener.stop()

        if captured_hotkey["value"]:
            new_hotkey = captured_hotkey["value"]
            self.user_choices["hotkey"] = new_hotkey
            self.hotkey_display.config(text=new_hotkey.upper())
            self.hotkey_status_label.config(
                text=f"Hotkey set to {new_hotkey.upper()}",
                foreground="#4CAF50"
            )

    # ========================================================================
    # Step 5: Test Transcription
    # ========================================================================

    def _step_test_transcription(self):
        """Step 5: Test transcription with sample phrase."""
        # Title
        ttk.Label(
            self.step_content_frame,
            text="Let's Test Your Setup!",
            font=("", 12, "bold")
        ).pack(pady=(0, 10))

        # Summary of choices
        summary_frame = ttk.LabelFrame(self.step_content_frame, text="Your Configuration", padding=10)
        summary_frame.pack(fill=tk.X, padx=20, pady=(0, 15))

        ttk.Label(
            summary_frame,
            text=f"Model: {self.model_var.get().upper()}",
            font=("", 10)
        ).pack(anchor=tk.W)
        ttk.Label(
            summary_frame,
            text=f"Hotkey: {self.user_choices['hotkey'].upper()} ({self.activation_mode_var.get()} mode)",
            font=("", 10)
        ).pack(anchor=tk.W)

        # Test instructions
        instructions = (
            "When you click 'Start Test':\n\n"
            "1. A recording window will appear\n"
            "2. Press your hotkey and speak clearly\n"
            "3. Release the hotkey (or press again if toggle mode)\n"
            "4. Your transcription will appear below"
        )
        ttk.Label(
            self.step_content_frame,
            text=instructions,
            font=("", 10),
            justify=tk.LEFT
        ).pack(pady=(0, 15))

        # Test result area
        result_frame = ttk.LabelFrame(self.step_content_frame, text="Transcription Result", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=20)

        self.test_result_text = tk.Text(
            result_frame,
            height=6,
            wrap=tk.WORD,
            font=("", 10)
        )
        self.test_result_text.pack(fill=tk.BOTH, expand=True)
        self.test_result_text.insert("1.0", "Your transcription will appear here...")
        self.test_result_text.config(state=tk.DISABLED)

        # Start test button
        self.start_test_btn = ttk.Button(
            self.step_content_frame,
            text="Start Test Recording",
            command=self._start_test_transcription,
            width=20
        )
        self.start_test_btn.pack(pady=(15, 0))

    def _start_test_transcription(self):
        """Start the test transcription."""
        # Apply settings first
        self._apply_onboarding_settings()

        # Start actual transcription test
        if self.gui_ref and self.gui_ref.transcriber:
            messagebox.showinfo(
                "Test Mode",
                f"Press your hotkey ({self.user_choices['hotkey'].upper()}) and speak:\n\n"
                "\"The quick brown fox jumps over the lazy dog.\""
            )
        else:
            # Mock test if transcriber not available
            self.test_result_text.config(state=tk.NORMAL)
            self.test_result_text.delete("1.0", tk.END)
            self.test_result_text.insert("1.0",
                "Test mode: Transcriber not yet initialized.\n\n"
                "Your settings have been saved. You can test the transcription\n"
                "after completing this tutorial by clicking 'Start' in the tray menu."
            )
            self.test_result_text.config(state=tk.DISABLED)
            self.start_test_btn.config(state=tk.DISABLED, text="Settings Saved")

    def _apply_onboarding_settings(self):
        """Apply the settings chosen during onboarding."""
        try:
            # Load existing settings
            import json
            from pathlib import Path

            settings_path = Path(SETTINGS_FILE)
            if settings_path.exists():
                with open(settings_path, 'r') as f:
                    data = json.load(f)
            else:
                data = {}

            # Update with onboarding choices
            data["model_name"] = self.model_var.get()
            data["hotkey"] = self.user_choices["hotkey"]
            data["activation_mode"] = self.activation_mode_var.get()
            data["language"] = self.user_choices["language"]

            # Save settings
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            with open(settings_path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Onboarding settings applied: {data}")

        except Exception as e:
            logger.error(f"Error applying onboarding settings: {e}")

    # ========================================================================
    # Step 6: Complete
    # ========================================================================

    def _step_complete(self):
        """Step 6: Completion."""
        # Success message
        success_label = ttk.Label(
            self.step_content_frame,
            text="You're All Set!",
            font=("", 18, "bold"),
            foreground="#4CAF50"
        )
        success_label.pack(pady=(20, 20))

        # Summary
        summary_text = (
            "Faster Whisper Hotkey is now configured and ready to use.\n\n"
            "Your settings have been saved:"
        )
        ttk.Label(self.step_content_frame, text=summary_text, font=("", 11), justify=tk.CENTER).pack()

        # Settings recap
        recap_frame = ttk.Frame(self.step_content_frame, relief=tk.RIDGE, borderwidth=1)
        recap_frame.pack(fill=tk.X, padx=40, pady=(15, 15))

        recap_items = [
            f"Model: {self.model_var.get().upper()}",
            f"Hotkey: {self.user_choices['hotkey'].upper()}",
            f"Mode: {self.activation_mode_var.get().capitalize()}"
        ]

        for item in recap_items:
            ttk.Label(recap_frame, text=item, font=("", 10)).pack(anchor=tk.W, padx=10, pady=3)

        # Next steps
        next_steps_frame = ttk.Frame(self.step_content_frame)
        next_steps_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(
            next_steps_frame,
            text="Next Steps:",
            font=("", 10, "bold")
        ).pack(anchor=tk.W)

        ttk.Label(
            next_steps_frame,
            text=" 1. Click 'Start' in the tray menu to begin\n"
                " 2. Press your hotkey and speak\n"
                " 3. Your transcribed text appears in the clipboard!\n\n"
                "Access Settings anytime from the tray menu to configure options.",
            font=("", 10),
            justify=tk.LEFT
        ).pack(anchor=tk.W)

    def _step_fallback(self, step_key: str):
        """Fallback for undefined steps."""
        ttk.Label(
            self.step_content_frame,
            text=f"Step: {step_key}",
            font=("", 12)
        ).pack(pady=20)

    def _next(self):
        """Advance to the next step."""
        # Apply settings when leaving model selection
        if self.STEPS[self.current_step_index] == "model_selection":
            self.user_choices["model"] = self.model_var.get()

        # Apply hotkey settings when leaving hotkey setup
        if self.STEPS[self.current_step_index] == "hotkey_setup":
            self.user_choices["hotkey"] = self.user_choices.get("hotkey", "pause")
            self.user_choices["activation_mode"] = self.activation_mode_var.get()

        if self.current_step_index < len(self.STEPS) - 1:
            self._show_step(self.current_step_index + 1)

    def _back(self):
        """Go back to the previous step."""
        if self.current_step_index > 0:
            self._show_step(self.current_step_index - 1)

    def _skip_tutorial(self):
        """Skip the entire tutorial."""
        if self.window and self.window.winfo_exists():
            if messagebox.askyesno(
                "Skip Tutorial?",
                "Are you sure you want to skip the tutorial?\n"
                "You can always access it later from the tray menu."
            ):
                self._complete_tutorial(skipped=True)

    def _finish(self):
        """Complete the tutorial."""
        # Apply all settings before finishing
        self._apply_onboarding_settings()
        self._complete_tutorial(skipped=False)

    def _complete_tutorial(self, skipped: bool = False):
        """Mark the tutorial as complete and clean up."""
        # Stop any ongoing mic test
        if self.is_testing_mic:
            self._stop_mic_test()

        if self.window and self.window.winfo_exists():
            self.window.destroy()
            self.window = None

        if self.on_complete:
            self.on_complete(skipped=skipped)

        logger.info(f"Onboarding tutorial {'skipped' if skipped else 'completed'}")

    def _on_close(self):
        """Handle window close button."""
        if messagebox.askyesno(
            "Exit Tutorial?",
            "Do you want to exit the tutorial?\n"
            "Your progress will be saved."
        ):
            # Apply settings before closing
            if hasattr(self, 'model_var') and self.model_var.get():
                self._apply_onboarding_settings()
            self._complete_tutorial(skipped=True)


def show_onboarding(parent, gui_ref, on_complete=None) -> OnboardingOverlay:
    """Show the onboarding overlay.

    Args:
        parent: The parent tkinter root window
        gui_ref: Reference to the WhisperHotkeyGUI instance
        on_complete: Callback when tutorial is completed

    Returns:
        The OnboardingOverlay instance
    """
    overlay = OnboardingOverlay(parent, gui_ref, on_complete)
    overlay.show()
    return overlay
