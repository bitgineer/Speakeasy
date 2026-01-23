"""
Modern transcription history panel using tkinter with theme support.

This module provides a modern GUI window for viewing and managing
transcription history. It features:
- Modern card-based design with rounded corners
- 8px grid spacing system
- Theme support (light/dark mode)
- Improved typography and iconography
- Smooth hover effects

Classes
-------
ModernHistoryPanel
    Modern history panel with theme support.

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
from .theme import ThemeManager, create_styled_frame, create_styled_label, create_styled_button
from .icons import IconFactory


class ModernHistoryPanel:
    """Modern history panel with click-to-copy functionality."""

    def __init__(self, theme_manager: ThemeManager, max_items: int = 50, on_close=None):
        """Initialize the modern history panel.

        Args:
            theme_manager: ThemeManager instance for styling
            max_items: Maximum number of history items to keep
            on_close: Callback when panel is closed
        """
        self.theme_manager = theme_manager
        self.max_items = max_items
        self.on_close = on_close
        self.history = load_history()
        self.privacy_mode = False
        self._load_privacy_mode()
        self.window = None
        self.icon_factory = IconFactory(theme_manager)

    def _load_privacy_mode(self):
        """Load privacy mode setting from settings."""
        settings = load_settings()
        if settings:
            self.privacy_mode = getattr(settings, 'privacy_mode', False)
            if self.privacy_mode:
                self.history = []

    def update_privacy_mode(self, privacy_mode: bool):
        """Update privacy mode setting."""
        self.privacy_mode = privacy_mode
        if privacy_mode:
            self.history = []

    def add_transcription(self, text: str):
        """Add a new transcription to history."""
        if self.privacy_mode:
            return

        entry = {
            "timestamp": datetime.now().isoformat(),
            "text": text,
        }
        self.history.append(entry)
        if len(self.history) > self.max_items:
            self.history = self.history[-self.max_items:]
        save_history(self.history, self.max_items)
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
        self.window.geometry("700x500")
        self.window.minsize(500, 300)

        # Apply theme to window
        self.theme_manager.style.apply_to_widget(self.window)

        # Configure grid with 8px padding
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)

        # Main container with card styling
        main_frame = create_styled_frame(
            self.window,
            self.theme_manager,
            card_style=False
        )
        main_frame.grid(row=0, column=0, sticky="nsew", padx=self.theme_manager.get_spacing("md"),
                       pady=self.theme_manager.get_spacing("md"))
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Header section
        self._create_header(main_frame)

        # Privacy mode indicator (shown when active)
        if self.privacy_mode:
            self._create_privacy_banner(main_frame)

        # Content section with listbox
        self._create_content(main_frame)

        # Footer with action buttons
        self._create_footer(main_frame)

        # Populate list
        self._refresh_list()

        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self._on_window_close)

        # Center on screen
        self._center_window()

    def _create_header(self, parent):
        """Create the header section."""
        header_frame = create_styled_frame(parent, self.theme_manager, card_style=False)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, self.theme_manager.get_spacing("sm")))
        header_frame.columnconfigure(1, weight=1)

        # Icon + title
        title_frame = ttk.Frame(header_frame)
        title_frame.grid(row=0, column=0, sticky="w")

        # History icon
        icon = self.icon_factory.create(title_frame, "history", size=28,
                                       color=self.theme_manager.get_color("primary"))
        icon.grid(row=0, column=0, padx=(0, self.theme_manager.get_spacing("sm")), pady="4")

        # Title
        title = create_styled_label(
            title_frame,
            self.theme_manager,
            variant="subtitle",
            text="History"
        )
        title.grid(row=0, column=1)

        # Item count badge
        self.count_label = create_styled_label(
            header_frame,
            self.theme_manager,
            variant="hint",
            text=f"{len(self.history)} items"
        )
        self.count_label.grid(row=0, column=1, sticky="e")

    def _create_privacy_banner(self, parent):
        """Create privacy mode warning banner."""
        banner_frame = tk.Frame(
            parent,
            bg=self.theme_manager.get_color("error"),
            highlightthickness=0
        )
        banner_frame.grid(row=1, column=0, sticky="ew", pady=(0, self.theme_manager.get_spacing("sm")))

        # Shield icon
        icon = self.icon_factory.create(banner_frame, "shield", size=20, color="#FFFFFF")
        icon.configure(bg=self.theme_manager.get_color("error"))
        icon.pack(side=tk.LEFT, padx=(self.theme_manager.get_spacing("sm"), self.theme_manager.get_spacing("xs")))

        # Warning text
        warning = tk.Label(
            banner_frame,
            text="Privacy Mode Active - No history is being saved",
            fg="#FFFFFF",
            bg=self.theme_manager.get_color("error"),
            font=self.theme_manager.get_font("sm", bold=True)
        )
        warning.pack(side=tk.LEFT, padx=self.theme_manager.get_spacing("xs"), pady=self.theme_manager.get_spacing("xs"))

    def _create_content(self, parent):
        """Create the main content area with listbox."""
        content_frame = create_styled_frame(parent, self.theme_manager, card_style=True)
        content_frame.grid(row=2, column=0, sticky="nsew", pady=(0, self.theme_manager.get_spacing("sm")))
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)

        # Inner container for listbox
        list_container = ttk.Frame(content_frame, padding=0)
        list_container.grid(row=0, column=0, sticky="nsew")
        list_container.columnconfigure(0, weight=1)
        list_container.rowconfigure(0, weight=1)

        # Custom styled listbox
        self.listbox = tk.Listbox(
            list_container,
            font=self.theme_manager.get_mono_font("base"),
            selectmode=tk.SINGLE,
            highlightthickness=1,
            borderwidth=0,
            relief="flat",
            bd=0,
        )
        # Apply theme colors to listbox
        c = self.theme_manager.colors
        self.listbox.configure(
            bg=c["bg_main"],
            fg=c["fg_primary"],
            selectbackground=c["primary_light"],
            selectforeground=c["fg_primary"],
            highlightbackground=c["border"],
            highlightcolor=c["border_focus"],
        )
        self.listbox.grid(row=0, column=0, sticky="nsew")

        # Bind events
        self.listbox.bind("<Double-1>", self._on_item_click)
        self.listbox.bind("<Return>", self._on_item_click)
        self.listbox.bind("<<ListboxSelect>>", self._on_selection_change)

        # Modern scrollbar
        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.listbox.configure(yscrollcommand=scrollbar.set)

    def _create_footer(self, parent):
        """Create the footer with action buttons and status."""
        footer_frame = create_styled_frame(parent, self.theme_manager, card_style=False)
        footer_frame.grid(row=3, column=0, sticky="ew")

        # Button row
        button_frame = ttk.Frame(footer_frame)
        button_frame.pack(fill=tk.X, pady=(0, self.theme_manager.get_spacing("xs")))

        # Copy button (primary)
        self.copy_btn = create_styled_button(
            button_frame,
            self.theme_manager,
            variant="primary",
            text="Copy Selected",
            command=self._copy_selected
        )
        self.copy_btn.pack(side=tk.LEFT, padx=(0, self.theme_manager.get_spacing("xs")))

        # Clear button (danger)
        clear_btn = create_styled_button(
            button_frame,
            self.theme_manager,
            variant="danger",
            text="Clear All",
            command=self._clear_history
        )
        clear_btn.pack(side=tk.LEFT)

        # Status label
        self.status_label = create_styled_label(
            footer_frame,
            self.theme_manager,
            variant="hint",
            text="Double-click or press Enter to copy"
        )
        self.status_label.pack(anchor=tk.W, pady=(self.theme_manager.get_spacing("xs"), 0))

    def _refresh_list(self):
        """Refresh the listbox with current history."""
        if not self.listbox:
            return

        self.listbox.delete(0, tk.END)
        for entry in reversed(self.history):
            timestamp = entry.get("timestamp", "")
            text = entry.get("text", "")
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%H:%M:%S")
            except (ValueError, TypeError):
                time_str = "??:??:??"
            preview = text[:80].replace("\n", " ")
            if len(text) > 80:
                preview += "..."
            display = f"[{time_str}] {preview}"
            self.listbox.insert(tk.END, display)

        # Update count
        if hasattr(self, 'count_label'):
            self.count_label.configure(text=f"{len(self.history)} items")

    def _on_selection_change(self, event=None):
        """Handle selection change."""
        selection = self.listbox.curselection()
        if selection:
            state = tk.NORMAL
        else:
            state = tk.DISABLED
        if hasattr(self, 'copy_btn'):
            self.copy_btn.configure(state=state)

    def _on_item_click(self, event=None):
        """Handle item click/double-click."""
        self._copy_selected()

    def _copy_selected(self):
        """Copy the selected item's full text to clipboard."""
        selection = self.listbox.curselection()
        if not selection:
            self._show_status("No item selected", "error")
            return

        idx = len(self.history) - 1 - selection[0]
        if 0 <= idx < len(self.history):
            text = self.history[idx].get("text", "")
            pyperclip.copy(text)
            self._show_status("Copied to clipboard!", "success")
            # Reset status after delay
            self.window.after(2000, lambda: self._show_status("Double-click or press Enter to copy", "hint"))

    def _clear_history(self):
        """Clear all history."""
        if not self.history:
            self._show_status("History is already empty", "hint")
            return

        # Confirm with user (using simple messagebox)
        from tkinter import messagebox
        if messagebox.askyesno("Clear History", "Are you sure you want to clear all history?"):
            self.history = []
            save_history(self.history, self.max_items)
            self._refresh_list()
            self._show_status("History cleared", "success")

    def _show_status(self, message: str, status_type: str = "hint"):
        """Show a status message.

        Args:
            message: Message text
            status_type: Type of status - "hint", "success", "error"
        """
        if not hasattr(self, 'status_label'):
            return

        color_map = {
            "hint": self.theme_manager.get_color("fg_hint"),
            "success": self.theme_manager.get_color("success"),
            "error": self.theme_manager.get_color("error"),
        }
        color = color_map.get(status_type, self.theme_manager.get_color("fg_hint"))

        self.status_label.configure(text=message, foreground=color)

    def _center_window(self):
        """Center the window on screen."""
        self.window.update_idletasks()
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - self.window.winfo_width()) // 2
        y = (screen_height - self.window.winfo_height()) // 2
        self.window.geometry(f"+{x}+{y}")

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
