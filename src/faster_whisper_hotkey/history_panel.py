"""
Transcription history panel using tkinter.

This module provides a GUI window for viewing and managing transcription
history. It supports click-to-copy functionality, history clearing, and
privacy mode which disables all history storage.

Classes
-------
HistoryPanel
    A window showing transcription history with click-to-copy functionality.

Notes
-----
When privacy mode is enabled, no history is saved and any existing
history is cleared from memory. History is persisted to disk as JSON.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
import pyperclip

from .settings import load_history, save_history, load_settings


class HistoryPanel:
    """A window showing transcription history with click-to-copy."""

    def __init__(self, max_items: int = 50, on_close=None):
        self.max_items = max_items
        self.on_close = on_close
        self.history = load_history()
        self.privacy_mode = False
        self._load_privacy_mode()
        self.window = None

    def _load_privacy_mode(self):
        """Load privacy mode setting from settings."""
        settings = load_settings()
        if settings:
            self.privacy_mode = getattr(settings, 'privacy_mode', False)
            if self.privacy_mode:
                # Clear any loaded history when privacy mode is active
                self.history = []

    def update_privacy_mode(self, privacy_mode: bool):
        """Update privacy mode setting."""
        self.privacy_mode = privacy_mode
        if privacy_mode:
            # Clear in-memory history when enabling privacy mode
            self.history = []

    def add_transcription(self, text: str):
        """Add a new transcription to history."""
        # Skip saving history in privacy mode
        if self.privacy_mode:
            return

        entry = {
            "timestamp": datetime.now().isoformat(),
            "text": text,
        }
        self.history.append(entry)
        # Trim to max items
        if len(self.history) > self.max_items:
            self.history = self.history[-self.max_items:]
        save_history(self.history, self.max_items)
        # Update display if window is open
        if self.window and self.window.winfo_exists():
            self._refresh_list()

    def show(self):
        """Show the history panel window."""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()
            return

        self.window = tk.Toplevel()
        self.window.title("Transcription History")
        self.window.geometry("600x400")
        self.window.minsize(400, 200)

        # Configure grid
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)

        # Main frame
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # Privacy mode indicator
        if self.privacy_mode:
            privacy_frame = ttk.Frame(main_frame)
            privacy_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
            ttk.Label(
                privacy_frame,
                text=" Privacy Mode Active - No history is being saved ",
                foreground="#ffffff",
                background="#F44336",
                font=("", 10, "bold")
            ).pack()

        # Listbox with scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=("Consolas", 10),
            selectmode=tk.SINGLE,
        )
        self.listbox.grid(row=0, column=0, sticky="nsew")
        scrollbar.config(command=self.listbox.yview)

        # Bind double-click to copy
        self.listbox.bind("<Double-1>", self._on_item_click)
        self.listbox.bind("<Return>", self._on_item_click)

        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        copy_btn = ttk.Button(button_frame, text="Copy Selected", command=self._copy_selected)
        copy_btn.pack(side=tk.LEFT, padx=(0, 5))

        clear_btn = ttk.Button(button_frame, text="Clear History", command=self._clear_history)
        clear_btn.pack(side=tk.LEFT)

        # Status label
        self.status_label = ttk.Label(main_frame, text="Double-click or press Enter to copy")
        self.status_label.grid(row=3, column=0, sticky="w", pady=(5, 0))

        # Populate list
        self._refresh_list()

        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _refresh_list(self):
        """Refresh the listbox with current history."""
        if not self.listbox:
            return
        self.listbox.delete(0, tk.END)
        # Show newest first
        for entry in reversed(self.history):
            timestamp = entry.get("timestamp", "")
            text = entry.get("text", "")
            # Format timestamp
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%H:%M:%S")
            except (ValueError, TypeError):
                time_str = "??:??:??"
            # Truncate text for display
            preview = text[:80].replace("\n", " ")
            if len(text) > 80:
                preview += "..."
            display = f"[{time_str}] {preview}"
            self.listbox.insert(tk.END, display)

    def _on_item_click(self, event=None):
        """Handle item click/double-click."""
        self._copy_selected()

    def _copy_selected(self):
        """Copy the selected item's full text to clipboard."""
        selection = self.listbox.curselection()
        if not selection:
            self.status_label.config(text="No item selected")
            return
        # Index is reversed in display
        idx = len(self.history) - 1 - selection[0]
        if 0 <= idx < len(self.history):
            text = self.history[idx].get("text", "")
            pyperclip.copy(text)
            self.status_label.config(text="✓ Copied to clipboard!")
            # Reset status after 2 seconds
            self.window.after(2000, lambda: self.status_label.config(
                text="Double-click or press Enter to copy"
            ))

    def _clear_history(self):
        """Clear all history."""
        self.history = []
        save_history(self.history, self.max_items)
        self._refresh_list()
        self.status_label.config(text="History cleared")

    def _on_window_close(self):
        """Handle window close."""
        if self.on_close:
            self.on_close()
        self.window.destroy()
        self.window = None

    def close(self):
        """Close the window if open."""
        if self.window and self.window.winfo_exists():
            self.window.destroy()
            self.window = None
