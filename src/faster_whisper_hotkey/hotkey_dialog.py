"""
Custom hotkey capture dialog using tkinter.

This module provides a GUI dialog for capturing keyboard shortcut combinations.
It supports complex hotkey combinations with modifiers (Ctrl, Alt, Shift, Win)
and allows selection between hold-to-talk and toggle activation modes.

Classes
-------
HotkeyDialog
    Dialog for capturing custom hotkey combinations.

Functions
---------
show_hotkey_dialog
    Convenience function to show the hotkey dialog.

Notes
-----
Uses pynput for keyboard listening and handles both modifier keys and
regular keys. The dialog validates key combinations and formats them
consistently (e.g., "ctrl+shift+f1").
"""

import tkinter as tk
from tkinter import ttk
from pynput import keyboard


class HotkeyDialog:
    """Dialog for capturing custom hotkey combinations."""

    # Map pynput keys to display names
    KEY_NAMES = {
        keyboard.Key.f1: "F1",
        keyboard.Key.f2: "F2",
        keyboard.Key.f3: "F3",
        keyboard.Key.f4: "F4",
        keyboard.Key.f5: "F5",
        keyboard.Key.f6: "F6",
        keyboard.Key.f7: "F7",
        keyboard.Key.f8: "F8",
        keyboard.Key.f9: "F9",
        keyboard.Key.f10: "F10",
        keyboard.Key.f11: "F11",
        keyboard.Key.f12: "F12",
        keyboard.Key.pause: "Pause",
        keyboard.Key.insert: "Insert",
        keyboard.Key.home: "Home",
        keyboard.Key.end: "End",
        keyboard.Key.page_up: "PageUp",
        keyboard.Key.page_down: "PageDown",
        keyboard.Key.space: "Space",
        keyboard.Key.enter: "Enter",
        keyboard.Key.tab: "Tab",
        keyboard.Key.backspace: "Backspace",
        keyboard.Key.delete: "Delete",
        keyboard.Key.up: "Up",
        keyboard.Key.down: "Down",
        keyboard.Key.left: "Left",
        keyboard.Key.right: "Right",
        keyboard.Key.ctrl_l: "Ctrl",
        keyboard.Key.ctrl_r: "Ctrl",
        keyboard.Key.alt_l: "Alt",
        keyboard.Key.alt_r: "Alt",
        keyboard.Key.shift_l: "Shift",
        keyboard.Key.shift_r: "Shift",
        keyboard.Key.cmd: "Win",
        keyboard.Key.cmd_l: "Win",
        keyboard.Key.cmd_r: "Win",
    }

    MODIFIER_KEYS = {
        keyboard.Key.ctrl_l, keyboard.Key.ctrl_r,
        keyboard.Key.alt_l, keyboard.Key.alt_r,
        keyboard.Key.shift_l, keyboard.Key.shift_r,
        keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r,
    }

    def __init__(self, parent, current_hotkey: str = "pause", current_mode: str = "hold"):
        self.parent = parent
        self.result_hotkey = None
        self.result_mode = None
        self.current_keys = set()
        self.captured_combo = None
        self.listener = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Hotkey Settings")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 400) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 300) // 2
        self.dialog.geometry(f"+{x}+{y}")

        self._build_ui(current_hotkey, current_mode)

    def _build_ui(self, current_hotkey: str, current_mode: str):
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Current hotkey display
        ttk.Label(main_frame, text="Current Hotkey:").pack(anchor=tk.W)
        self.current_label = ttk.Label(
            main_frame, 
            text=current_hotkey.upper(),
            font=("Consolas", 14, "bold")
        )
        self.current_label.pack(anchor=tk.W, pady=(0, 15))

        # Capture section
        ttk.Label(main_frame, text="New Hotkey:").pack(anchor=tk.W)
        
        capture_frame = ttk.Frame(main_frame)
        capture_frame.pack(fill=tk.X, pady=(0, 15))

        self.hotkey_display = ttk.Label(
            capture_frame,
            text="Click 'Capture' then press your hotkey",
            font=("Consolas", 12),
            foreground="gray"
        )
        self.hotkey_display.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.capture_btn = ttk.Button(
            capture_frame,
            text="Capture",
            command=self._start_capture
        )
        self.capture_btn.pack(side=tk.RIGHT, padx=(10, 0))

        # Activation mode
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        ttk.Label(main_frame, text="Activation Mode:").pack(anchor=tk.W)

        self.mode_var = tk.StringVar(value=current_mode)

        mode_frame = ttk.Frame(main_frame)
        mode_frame.pack(fill=tk.X, pady=(5, 15))

        ttk.Radiobutton(
            mode_frame,
            text="Hold-to-talk (hold key while speaking)",
            variable=self.mode_var,
            value="hold"
        ).pack(anchor=tk.W)

        ttk.Radiobutton(
            mode_frame,
            text="Toggle (press to start, press again to stop)",
            variable=self.mode_var,
            value="toggle"
        ).pack(anchor=tk.W)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            button_frame,
            text="Save",
            command=self._save
        ).pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel
        ).pack(side=tk.RIGHT)

        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self._cancel)

    def _start_capture(self):
        """Start capturing keyboard input."""
        self.captured_combo = None
        self.current_keys = set()
        self.hotkey_display.config(text="Press your hotkey combo...", foreground="blue")
        self.capture_btn.config(state=tk.DISABLED)

        # Start keyboard listener
        self.listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.listener.start()

    def _on_key_press(self, key):
        """Handle key press during capture."""
        self.current_keys.add(key)
        self._update_display()

    def _on_key_release(self, key):
        """Handle key release - finalize capture when non-modifier released."""
        if key not in self.MODIFIER_KEYS and self.current_keys:
            # Capture complete - store the combo
            self.captured_combo = self._keys_to_string(self.current_keys)
            self._stop_capture()
        elif key in self.current_keys:
            self.current_keys.discard(key)
            self._update_display()

    def _update_display(self):
        """Update the hotkey display with current keys."""
        if self.current_keys:
            display = self._keys_to_string(self.current_keys)
            self.hotkey_display.config(text=display, foreground="black")

    def _keys_to_string(self, keys: set) -> str:
        """Convert a set of keys to a string representation."""
        modifiers = []
        main_key = None

        for key in keys:
            if key in self.MODIFIER_KEYS:
                name = self.KEY_NAMES.get(key, str(key))
                if name not in modifiers:
                    modifiers.append(name)
            else:
                main_key = self.KEY_NAMES.get(key, None)
                if main_key is None:
                    # Handle regular character keys
                    try:
                        main_key = key.char.upper() if key.char else str(key)
                    except AttributeError:
                        main_key = str(key).replace("Key.", "")

        # Sort modifiers for consistent ordering
        modifier_order = ["Ctrl", "Alt", "Shift", "Win"]
        modifiers.sort(key=lambda m: modifier_order.index(m) if m in modifier_order else 99)

        parts = modifiers + ([main_key] if main_key else [])
        return "+".join(parts) if parts else ""

    def _stop_capture(self):
        """Stop capturing and update UI."""
        if self.listener:
            self.listener.stop()
            self.listener = None
        
        self.capture_btn.config(state=tk.NORMAL)
        
        if self.captured_combo:
            self.hotkey_display.config(
                text=self.captured_combo,
                foreground="green"
            )
        else:
            self.hotkey_display.config(
                text="Click 'Capture' then press your hotkey",
                foreground="gray"
            )

    def _save(self):
        """Save the settings and close."""
        if self.captured_combo:
            self.result_hotkey = self.captured_combo.lower()
        self.result_mode = self.mode_var.get()
        self._cleanup()
        self.dialog.destroy()

    def _cancel(self):
        """Cancel and close."""
        self._cleanup()
        self.dialog.destroy()

    def _cleanup(self):
        """Clean up resources."""
        if self.listener:
            self.listener.stop()
            self.listener = None

    def show(self):
        """Show dialog and return (hotkey, mode) or (None, None) if cancelled."""
        self.dialog.wait_window()
        return self.result_hotkey, self.result_mode


def show_hotkey_dialog(parent, current_hotkey: str = "pause", current_mode: str = "hold"):
    """Show the hotkey dialog and return (new_hotkey, new_mode) or (None, None)."""
    dialog = HotkeyDialog(parent, current_hotkey, current_mode)
    return dialog.show()
